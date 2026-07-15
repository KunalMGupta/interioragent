"""Shared core for IDSDL asset/scene tooling.

Logic extracted so BOTH the workbench CLI (thin print wrappers) and the MCP server
(content/image wrappers) call the same functions. Functions return plain Python objects and
never print. Owns the **warm singletons** — the 687MB embeddings + retrievers + router load
once per process here (the whole point of the MCP server), backed by the module-level
`_NPZ_CACHE`/`_JSON_CACHE` in IDSDL.datasets.retrievers.

Discovery (retrieve/inspect/browse) uses the router with ``seed=None`` so it never pollutes the
per-scene seeded retrieval cache (.cache/retrieval_seed_*.json). Scene builds keep their own
seeded retriever (IDSDL/scene.py) — do not route those through here.
"""
import glob
import json as _json
import os
import re
import subprocess
import sys
import threading

import numpy as np

# Repo root: IDSDL_ROOT env override > two levels above this file (IDSDL/service/core.py).
REPO_ROOT = os.environ.get("IDSDL_ROOT") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TMP = os.path.join(REPO_ROOT, "tmp")

# ---- warm singletons -------------------------------------------------------
_LOCK = threading.Lock()          # serialize the router (LLM client + any mutable state)
_base = None                      # FUTURE_HSSD_ASSET_RETRIEVERS[0] — full embeddings + metadata
_router = None                    # SceneProgAssetRetriever(seed=None) — routes + visual-picks
_planner = None                   # InteriorPlanner — RAG + image planner
_trace_retriever = None           # retriever_core.TraceRetriever — reasoning over the catalog


def get_base_retriever():
    """The base FutureHSSD retriever (full embeddings/metadata + _preview_path). Read-only."""
    global _base
    if _base is None:
        from IDSDL.datasets.retrievers import FUTURE_HSSD_ASSET_RETRIEVERS
        _base = FUTURE_HSSD_ASSET_RETRIEVERS[0]
    return _base


def get_router():
    """The top-level routing+resolving retriever (seed=None: no seeded-cache writes)."""
    global _router
    if _router is None:
        from IDSDL.datasets.retrievers import SceneProgAssetRetriever
        _router = SceneProgAssetRetriever(seed=None)
    return _router


def get_planner():
    global _planner
    if _planner is None:
        from planner_core.planner import InteriorPlanner
        _planner = InteriorPlanner()
    return _planner


def get_trace_retriever():
    global _trace_retriever
    if _trace_retriever is None:
        from retriever_core import TraceRetriever
        _trace_retriever = TraceRetriever()
    return _trace_retriever


def warm():
    """Eagerly load the heavy singletons (call at server startup so the first tool call is fast)."""
    get_base_retriever()
    get_router()
    return {"models": int(len(get_base_retriever().all_models))}


def reload_credentials(key=None):
    """Refresh OPENAI_API_KEY in the WARM server without a restart.

    The server process snapshots env at launch, so a rotated/stale key otherwise
    401s every LLM-backed tool until restart. Source order: explicit ``key`` arg >
    an ``OPENAI_API_KEY=...`` line in <repo>/.env > fail with instructions. Every
    singleton that captured an OpenAI client at construction (router, planner,
    trace retriever, the module retriever list) is rebuilt; the embedding arrays
    stay cached, so this is seconds, not a cold start. Subprocess tools
    (run_scene / generate_*) inherit os.environ and are fixed automatically."""
    source = "argument"
    if not key:
        env_file = os.path.join(REPO_ROOT, ".env")
        if os.path.isfile(env_file):
            for line in open(env_file):
                line = line.strip()
                if line.startswith("OPENAI_API_KEY=") and line.split("=", 1)[1]:
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    source = env_file
                    break
    if not key:
        return {"ok": False,
                "error": "no key found — pass key=..., or write OPENAI_API_KEY=... "
                         "to <repo>/.env and call reload_credentials() again"}
    os.environ["OPENAI_API_KEY"] = key
    global _base, _router, _planner, _trace_retriever
    with _LOCK:
        import IDSDL.datasets.retrievers as R
        # rebuild instances (they hold OpenAI clients); npz/json caches stay warm
        R.FUTURE_HSSD_ASSET_RETRIEVERS = [type(r)() for r in R.FUTURE_HSSD_ASSET_RETRIEVERS]
        _base = _router = _planner = _trace_retriever = None
        info = warm()
    return {"ok": True, "source": source, "key_tail": key[-6:], **info}


def stale_key_hint(exc):
    """A friendly message when an exception is an OpenAI auth failure, else None.
    Tools return this instead of a raw 401 traceback."""
    s = f"{type(exc).__name__}: {exc}"
    markers = ("401", "AuthenticationError", "invalid_api_key", "Incorrect API key")
    if any(m in s for m in markers):
        return ("OPENAI_API_KEY is invalid or stale for this warm server (it snapshots "
                "env at launch). Fix WITHOUT restarting: call reload_credentials(key=...) "
                "— or write OPENAI_API_KEY=... to <repo>/.env and call reload_credentials().")
    return None


def refresh_retrievers():
    """Re-instantiate the warm singletons so freshly-ingested custom assets become visible in
    the SAME process. ingest clears the module npz/json caches, but the already-built retriever
    objects still hold the old in-memory arrays — so we drop and rebuild them."""
    global _base, _router
    import IDSDL.datasets.retrievers as R
    R._NPZ_CACHE.clear()
    R._JSON_CACHE.clear()
    # rebuild the module-level retriever list so every retriever picks up the new embeddings
    R.FUTURE_HSSD_ASSET_RETRIEVERS = [type(r)() for r in R.FUTURE_HSSD_ASSET_RETRIEVERS]
    _base = None
    _router = None
    return warm()


# ---- retrieval (the discovery loop) ----------------------------------------
def retrieve(query, pin=None):
    """Route + resolve a single query to the full result dict (warm, no seeded cache):
    ``{query, retriever, chosen_model, path, scale, reasoning, sheet, candidates:[...]}``.
    ``candidates`` items are ``{model, path, scale, preview, desc, similarity, chosen}``."""
    router = get_router()
    with _LOCK:
        d = router._resolve_query(query, pin)
    return {
        "query": query,
        "retriever": d.get("retriever"),
        "chosen_model": d.get("model"),
        "path": d.get("path"),
        "scale": d.get("scale"),
        "reasoning": d.get("reasoning"),
        "sheet": d.get("sheet"),
        "candidates": list(d.get("candidates") or []),
    }


# inspect is retrieve with the guarantee that a contact sheet was produced (visual pickers set it)
inspect = retrieve


def browse(query, n=24, semantic=True, out=None):
    """Montage the dataset assets matching a query so they can be eyeballed by hand. Returns
    ``{query, semantic, montage_path, manifest:[{idx, model, similarity, desc}]}``."""
    r = get_base_retriever()
    if not semantic:
        ql = query.lower()
        models = [m for m in r.all_models.tolist()
                  if ql in (r.metadata.get(m, {}).get("description", "").lower())][:n]
        sims = [None] * len(models)
    else:
        embd = np.array(r.encoder.embed_query(query))
        sims_all = np.dot(r.all_embeddings, embd)
        idx = np.argsort(sims_all)[-n:][::-1]
        models = [r.all_models[i] for i in idx]
        sims = [float(sims_all[i]) for i in idx]

    items, manifest = [], []
    for i, m in enumerate(models):
        desc = r.metadata.get(m, {}).get("description", "")
        prev = r._preview_path(m)
        items.append((i + 1, prev, m, desc))   # 1-based labels (align with reselect/pin n)
        manifest.append({"idx": i + 1, "model": m, "similarity": sims[i], "desc": desc,
                         "preview": prev})

    out = out or os.path.join(_scratch_dir(), f"browse_{_safe(query)}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    montage(items, out)
    return {"query": query, "semantic": semantic, "montage_path": out, "manifest": manifest}


def candidate_preview(model):
    """The preview PNG path for a model id (or None)."""
    return get_base_retriever()._preview_path(model)


def addasset_snippet(query, model):
    """The durable AddAsset override the agent should paste into a scene/skill to pin a pick."""
    return f'scene.AddAsset("{query}", asset_id="{model}")'


# ---- montage helper (shared with workbench CLI) ----------------------------
def montage(items, out_path, cols=4, cell=260, pad=10, label_h=52):
    """Grid of (idx, preview, model, desc) tiles into one labeled PNG. Returns out_path."""
    import math
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    n = len(items)
    if n == 0:
        return None
    cols = min(cols, n)
    rows = math.ceil(n / cols)
    W = cols * cell + (cols + 1) * pad
    H = rows * (cell + label_h) + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), (250, 250, 250))
    draw = ImageDraw.Draw(sheet)
    try:
        f1 = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        f2 = ImageFont.truetype("DejaVuSans.ttf", 13)
    except Exception:
        f1 = f2 = ImageFont.load_default()
    for k, (idx, preview, model, desc) in enumerate(items):
        r, c = divmod(k, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell + label_h + pad)
        if preview:
            try:
                im = Image.open(preview).convert("RGB")
                im = ImageEnhance.Brightness(im).enhance(1.5)
                im.thumbnail((cell, cell))
                sheet.paste(im, (x + (cell - im.width) // 2, y + label_h + (cell - im.height) // 2))
            except Exception:
                draw.rectangle([x, y + label_h, x + cell, y + label_h + cell], outline=(200, 200, 200))
        stem = model.split("/")[-1][:14]
        draw.text((x + 4, y + 3), f"#{idx}  {stem}", fill=(170, 0, 0), font=f1)
        draw.text((x + 4, y + 24), (desc or "")[:40], fill=(60, 60, 60), font=f2)
    sheet.save(out_path)
    return out_path


def _safe(s):
    return "".join(ch if ch.isalnum() else "_" for ch in s)[:32]


def _scratch_dir():
    return os.path.join(os.environ.get("WORKBENCH_OUT", _TMP), "browse")


# ---- Tier B: curation / pools / ingest (warm, in-process) ------------------
# These call the existing workbench/ingest helpers IN-PROCESS, so they reuse the already-warm,
# module-cached retrievers (no 687MB reload) while keeping a single source of logic.
def candidates(category, topk=10, out=None):
    """Over-generate a candidate id pool from a named prompt-set (workbench CANDIDATE_PROMPTS).
    Returns ``{category, n_unique, ids, out_path}``."""
    import workbench
    out = out or os.path.join(_TMP, f"candidates_{_safe(category)}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rc = workbench.cmd_candidates(category, topk=topk, out=out)
    ids = _json.load(open(out)) if (rc == 0 and os.path.exists(out)) else []
    return {"category": category, "n_unique": len(ids), "ids": ids, "out_path": out,
            "available": list(workbench.CANDIDATE_PROMPTS)}


def gallery(source, n=None, page=0, out=None, hint=None):
    """Build the self-contained selection HTML for a pool / id-list / 'all'. Returns
    ``{source, html_path, size_mb}`` (a human-in-loop artifact the user curates in a browser)."""
    import workbench
    if source in ("list", "--list"):
        import IDSDL.datasets.retrievers as R
        adir = os.path.join(os.path.dirname(R.__file__), "assets")
        pools = sorted(f[:-5] for f in os.listdir(adir)
                       if f.endswith(".json") and f != "futurehssd.json")
        return {"pools": pools}
    out = out or os.path.join(_TMP, f"gallery_{_safe(str(source))}.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rc = workbench.cmd_gallery(source, n=n, page=page, out=out, hint=hint)
    size_mb = round(os.path.getsize(out) / 1e6, 1) if os.path.exists(out) else 0.0
    return {"source": source, "html_path": out, "size_mb": size_mb, "ok": rc == 0}


def pool_add(category, ids, create=False):
    """Append ids to a curated pool json (IDSDL/datasets/assets/<category>.json); create=True
    requires it not already exist. Returns ``{category, pool_path, n_total}``."""
    import IDSDL.datasets.retrievers as R
    from IDSDL.ingest import _add_to_category
    category = os.path.basename(category)  # pool name, never a path
    path = os.path.join(os.path.dirname(R.__file__), "assets",
                        category if category.endswith(".json") else category + ".json")
    if create and os.path.exists(path):
        return {"error": f"pool {category!r} already exists", "pool_path": path}
    _add_to_category(category, list(ids))
    return {"category": category, "pool_path": path, "n_total": len(_json.load(open(path)))}


def ingest_glbs(zip_path, category=None, manifest_path=None, workers=4):
    """Ingest a zip of .glb into the custom pool (render preview -> VLM caption -> embed), then
    RE-WARM so the new assets are retrievable in this same process. Returns ``{n_added, added}``."""
    from IDSDL.ingest import ingest_zip
    added = ingest_zip(zip_path, category=category, manifest_path=manifest_path, workers=workers)
    refresh_retrievers()
    return {"n_added": len(added),
            "added": [{"model": mid, "description": e.get("description"),
                       "placement": e.get("placement"), "scale": e.get("scale")}
                      for mid, e in added]}


# ---- Tier C: long isolated jobs (subprocess, render/image-gen bound) --------
def plan(prompt, top_k=3, out=None):
    """Run the planner (RAG + skill synthesis + collage). Subprocess-isolated. Returns
    ``{prompt, out_dir, plan_png, skill, retrieved}``."""
    out = out or os.path.join(_TMP, f"plan_{_safe(prompt)}")
    env = {**os.environ, "PYTHONPATH": REPO_ROOT}
    p = subprocess.run([sys.executable, "-m", "planner_core", prompt, "--out", out, "--top-k", str(top_k)],
                       cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=900)
    sp = os.path.join(out, "skill.txt"); rp = os.path.join(out, "retrieved.json")
    return {"prompt": prompt, "out_dir": out, "ok": p.returncode == 0,
            "plan_png": os.path.join(out, "plan.png"),
            "skill": open(sp).read() if os.path.exists(sp) else "",
            "retrieved": _json.load(open(rp)) if os.path.exists(rp) else [],
            "stderr_tail": "\n".join((p.stderr or "").splitlines()[-12:]) if p.returncode else ""}


def plan_refine(prompt, renders, prior=None, instruction=None, top_k=3, out=None):
    """Planner REFINEMENT — an improved target from current renders (+ prior target + skills).
    Subprocess-isolated. Returns ``{prompt, out_dir, ok, refined_png, skill, retrieved}``."""
    out = out or os.path.join(_TMP, f"refine_{_safe(prompt)}")
    renders = list(renders) if isinstance(renders, (list, tuple)) else [renders]
    args = [sys.executable, "-m", "planner_core", prompt, "--refine",
            "--out", out, "--top-k", str(top_k), "--renders", *renders]
    if prior:
        prior = list(prior) if isinstance(prior, (list, tuple)) else [prior]
        args += ["--prior", *prior]
    if instruction:
        args += ["--instruction", instruction]
    env = {**os.environ, "PYTHONPATH": REPO_ROOT}
    p = subprocess.run(args, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=900)
    sp = os.path.join(out, "skill.txt"); rp = os.path.join(out, "retrieved.json")
    return {"prompt": prompt, "out_dir": out, "ok": p.returncode == 0,
            "refined_png": os.path.join(out, "refined_target.png"),
            "skill": open(sp).read() if os.path.exists(sp) else "",
            "retrieved": _json.load(open(rp)) if os.path.exists(rp) else [],
            "stderr_tail": "\n".join((p.stderr or "").splitlines()[-12:]) if p.returncode else ""}


def run_scene(program_path, timeout=2400, phase=None):
    """Build+render a DSL scene program. Subprocess-isolated (a fresh scene/retriever + cold
    Blender, like batchgen). Returns the run's ``report`` dict + the room view paths.

    ``phase`` (1 anchors / 2 surfaces / 3 everything, default) builds a phase-gated
    program only up to that phase — see IDSDL/phases.py. A phase-1 build of a gated
    program takes ~a minute, so layout errors are caught before expensive dressing.

    Only accepts a report.json written AFTER this run started, so a build that errors
    before reporting can never surface a different scene's renders (the old mtime-fallback
    gotcha). Under the minimal render policy room_views/ is not produced; the VLM strip(s)
    in vlm_views/ are returned instead."""
    import time as _time
    start = _time.time()
    env = {**os.environ, "PYTHONPATH": REPO_ROOT}
    cmd = [sys.executable, "workbench.py", "run", program_path]
    if phase is not None:
        cmd += ["--phase", str(int(phase))]
    p = subprocess.run(cmd,
                       cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    out = p.stdout + "\n" + p.stderr
    report, run_dir = {}, None
    for rp in sorted(glob.glob(os.path.join(_TMP, "*", "report.json")),
                     key=os.path.getmtime, reverse=True):
        if os.path.getmtime(rp) >= start:
            report = _json.load(open(rp))
            run_dir = report.get("run_dir")
            break
    views = []
    if run_dir:
        views = sorted(glob.glob(os.path.join(REPO_ROOT, run_dir, "room_views", "*.png")))
        if not views:   # minimal render policy: only the VLM strip exists
            views = sorted(glob.glob(os.path.join(REPO_ROOT, run_dir, "vlm_views", "combined_*.png")),
                           key=os.path.getmtime)
    return {"program": program_path, "ok": p.returncode == 0 and bool(report), "run_dir": run_dir,
            "report": report, "room_views": views,
            "stderr_tail": "\n".join(out.splitlines()[-18:]) if (p.returncode or not report) else ""}


def lint_program(program_path=None, source=None):
    """Static API lint of a scene program (IDSDL/lints.py) — unknown methods /
    keywords vs the real DSL surface, in milliseconds, no build. Pass a path or
    raw source. Returns {ok, errors}. `workbench run` also runs this and refuses
    to build on errors."""
    from IDSDL.lints import lint_program as _lint, lint_program_file as _lint_file
    if source is not None:
        errors = _lint(source)
    elif program_path is not None:
        errors = _lint_file(program_path)
    else:
        return {"ok": False, "errors": ["pass program_path or source"]}
    return {"ok": not errors, "errors": errors}


# ---- reasoning-based trace retrieval (retriever_core) -----------------------
def catalog_listing():
    """The organized knowledge-catalog listing (offline; no LLM call)."""
    return get_trace_retriever().catalog.listing()


def retrieve_context(prompt, plan=None, out=None, include_programs=True):
    """Reasoning-based retrieval over the knowledge catalog: the selector LLM reads the whole
    catalog + the prompt (and optional planner brief) and picks the procedurally-relevant
    recipes/lessons. Writes bundle.md + selection.json to `out` and returns
    ``{procedural_signature, reasoning, examples, workflow_docs, lessons, bundle_path, bytes}``.
    The bundle itself is large — read it from bundle_path rather than inlining it."""
    out = out or os.path.join(_TMP, f"context_{_safe(prompt)}")
    with _LOCK:
        bundle = get_trace_retriever().retrieve(prompt, plan=plan,
                                                include_programs=include_programs)
    bundle_path = str(bundle.save(out))
    return {"procedural_signature": bundle.procedural_signature,
            "reasoning": bundle.reasoning,
            "examples": bundle.examples,
            "workflow_docs": bundle.workflow_docs,
            "lessons": bundle.lessons,
            "bundle_path": bundle_path,
            "bytes": len(bundle.markdown)}


# ---- end-to-end generation jobs (main.py in a subprocess) --------------------
_JOBS = {}   # job_id -> {proc, out_dir, log_path, prompt}


def generate_start(prompt, seed=42, max_inner=3, max_outer=2, threshold=8.0,
                   skip_stress=False, model="gpt-5", out=None):
    """Launch the full text→scene pipeline (main.py) as a background subprocess.
    Returns ``{job_id, out_dir, log_path}``; poll with generate_status()."""
    import time as _time
    job_id = f"gen_{int(_time.time())}_{_safe(prompt)[:16]}"
    out_dir = out or os.path.join(REPO_ROOT, "results", job_id)
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "generate.log")
    args = [sys.executable, "main.py", prompt, "--out", out_dir, "--seed", str(seed),
            "--max-inner", str(max_inner), "--max-outer", str(max_outer),
            "--threshold", str(threshold), "--model", model]
    if skip_stress:
        args.append("--skip-stress")
    env = {**os.environ, "PYTHONPATH": REPO_ROOT}
    logf = open(log_path, "w")
    proc = subprocess.Popen(args, cwd=REPO_ROOT, env=env, stdout=logf,
                            stderr=subprocess.STDOUT)
    _JOBS[job_id] = {"proc": proc, "out_dir": out_dir, "log_path": log_path,
                     "prompt": prompt}
    return {"job_id": job_id, "out_dir": out_dir, "log_path": log_path}


def _job_trace(out_dir):
    tp = os.path.join(out_dir, "trace.json")
    return _json.load(open(tp)) if os.path.exists(tp) else {}


def generate_status(job_id):
    """Progress of a generation job: ``{running, returncode, log_tail, trace_summary,
    latest_strip}``. The strip is the newest room VLM strip produced so far."""
    job = _JOBS.get(job_id)
    if not job:
        return {"error": f"unknown job {job_id!r}", "known": list(_JOBS)}
    rc = job["proc"].poll()
    log_tail = ""
    if os.path.exists(job["log_path"]):
        log_tail = "\n".join(open(job["log_path"]).read().splitlines()[-15:])
    trace = _job_trace(job["out_dir"])
    iters = trace.get("iterations", [])
    strips = [i.get("strip") for i in iters if i.get("strip")]
    plan_png = os.path.join(job["out_dir"], "plan.png")
    return {"job_id": job_id, "running": rc is None, "returncode": rc,
            "out_dir": job["out_dir"], "prompt": job["prompt"],
            "iterations": len(iters),
            "judgements": trace.get("judgements", []),
            "latest_strip": strips[-1] if strips else None,
            "plan_png": plan_png if os.path.exists(plan_png) else None,
            "log_tail": log_tail}


def generate_result(job_id):
    """Final artifacts of a finished generation job: the trace, program, blend and strip."""
    job = _JOBS.get(job_id)
    if not job:
        return {"error": f"unknown job {job_id!r}", "known": list(_JOBS)}
    if job["proc"].poll() is None:
        return {"error": "still running — use generate_status", "job_id": job_id}
    trace = _job_trace(job["out_dir"])
    out_dir = job["out_dir"]
    return {"job_id": job_id, "out_dir": out_dir, "trace": trace,
            "program": os.path.join(out_dir, "program.py"),
            "blend": os.path.join(out_dir, "scene.blend"),
            "plan_png": os.path.join(out_dir, "plan.png"),
            "final_strip": os.path.join(out_dir, "final_strip.png"),
            "score": trace.get("final", {}).get("score")}


# ---- Tier B: the asset shop (search the web -> normalize -> ingest) ---------
# The library is no longer a closed set: when a scene needs a thing that does not exist in it,
# these fetch one and make it a first-class asset. Everything runs through IDSDL.shop, so the
# same triage/verify guarantees apply here as on the command line.

def shop_search(query, count=15, license="permissive"):
    """Look, don't touch: what a query WOULD bring in from Sketchfab."""
    from IDSDL.shop.sources import SketchfabSource
    s = SketchfabSource()
    hits = s.search(query, count=count, license=license)
    return {"query": query, "n": len(hits), "has_token": bool(s.token),
            "hits": [{"name": c.name, "license": c.license, "author": c.author,
                      "faces": c.faces, "url": c.url} for c in hits]}


def shop_run(query, batch=None, count=6, source="sketchfab", category=None, manual=False,
             dry_run=False, from_dir=None, license="permissive"):
    """Full pipeline. Re-warms the retrievers so anything ingested is retrievable IMMEDIATELY —
    the point being that a scene program can ask for an asset the library did not have a minute
    ago."""
    import time as _t

    from IDSDL.shop.pipeline import run as _run
    from IDSDL.shop.sources import slugify
    batch = batch or os.path.join(REPO_ROOT, "shops",
                                  f"{_t.strftime('%Y-%m-%d')}-{slugify(query or 'local')}")
    metas = _run(query, batch, source=source, count=count,
                 mode="manual" if manual else "auto", category=category,
                 license=license, from_dir=from_dir, dry_run=dry_run)
    if not dry_run:
        refresh_retrievers()
    return _shop_summary(metas, batch)


def shop_apply(batch, category=None):
    """Act on the answers written into <batch>/HELP.md, then re-warm."""
    from IDSDL.shop import board as _board
    from IDSDL.shop.pipeline import apply as _apply
    from pathlib import Path as _P
    _apply(batch, category=category)
    refresh_retrievers()
    metas = [_board.load(d) for d in _board.asset_dirs(_P(batch))]
    return _shop_summary(metas, batch)


def _shop_summary(metas, batch):
    by = {}
    for m in metas or []:
        by.setdefault(m["status"], []).append(m)
    return {"batch": str(batch),
            "counts": {k: len(v) for k, v in by.items()},
            "ingested": [{"asset_id": m.get("asset_id"),
                          "object": (m.get("judgment") or {}).get("object"),
                          "width_m": (m.get("final") or {}).get("dims", {}).get("w_x"),
                          "license": (m.get("provenance") or {}).get("license")}
                         for m in by.get("ingested", [])],
            "needs_you": [{"key": m["key"], "why": m.get("reason"),
                           "object": (m.get("judgment") or {}).get("object")}
                          for m in by.get("ask", []) + by.get("failed", [])],
            "skipped": [{"key": m["key"], "why": m.get("reason")} for m in by.get("skip", [])],
            "help_md": os.path.join(str(batch), "HELP.md")}
