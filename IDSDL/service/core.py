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

_TMP = "/work/tmp"

# ---- warm singletons -------------------------------------------------------
_LOCK = threading.Lock()          # serialize the router (LLM client + any mutable state)
_base = None                      # FUTURE_HSSD_ASSET_RETRIEVERS[0] — full embeddings + metadata
_router = None                    # SceneProgAssetRetriever(seed=None) — routes + visual-picks
_planner = None                   # InteriorPlanner — RAG + image planner


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


def warm():
    """Eagerly load the heavy singletons (call at server startup so the first tool call is fast)."""
    get_base_retriever()
    get_router()
    return {"models": int(len(get_base_retriever().all_models))}


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
    return os.path.join(os.environ.get("WORKBENCH_OUT", "/work/tmp"), "browse")


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
    env = {**os.environ, "PYTHONPATH": "/work"}
    p = subprocess.run([sys.executable, "-m", "planner_core", prompt, "--out", out, "--top-k", str(top_k)],
                       cwd="/work", env=env, capture_output=True, text=True, timeout=900)
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
    env = {**os.environ, "PYTHONPATH": "/work"}
    p = subprocess.run(args, cwd="/work", env=env, capture_output=True, text=True, timeout=900)
    sp = os.path.join(out, "skill.txt"); rp = os.path.join(out, "retrieved.json")
    return {"prompt": prompt, "out_dir": out, "ok": p.returncode == 0,
            "refined_png": os.path.join(out, "refined_target.png"),
            "skill": open(sp).read() if os.path.exists(sp) else "",
            "retrieved": _json.load(open(rp)) if os.path.exists(rp) else [],
            "stderr_tail": "\n".join((p.stderr or "").splitlines()[-12:]) if p.returncode else ""}


def run_scene(program_path, timeout=2400):
    """Build+render a DSL scene program. Subprocess-isolated (a fresh scene/retriever + cold
    Blender, like batchgen). Returns the run's ``report`` dict + the room_views paths."""
    env = {**os.environ, "PYTHONPATH": "/work"}
    p = subprocess.run([sys.executable, "workbench.py", "run", program_path],
                       cwd="/work", env=env, capture_output=True, text=True, timeout=timeout)
    out = p.stdout + "\n" + p.stderr
    reps = sorted(glob.glob(os.path.join(_TMP, "*", "report.json")), key=os.path.getmtime)
    report = _json.load(open(reps[-1])) if reps else {}
    run_dir = report.get("run_dir")
    views = []
    if run_dir:
        rv = os.path.join("/work", run_dir, "room_views")
        views = sorted(glob.glob(os.path.join(rv, "*.png")))
    return {"program": program_path, "ok": p.returncode == 0, "run_dir": run_dir,
            "report": report, "room_views": views,
            "stderr_tail": "\n".join(out.splitlines()[-18:]) if p.returncode else ""}
