"""IDSDL MCP server (stdio) — warm, typed tools for the asset-discovery loop.

Run:  (from the repo root, in the project env)  PYTHONPATH=. python -m IDSDL.service.mcp_server
Registered via the repo's .mcp.json so Claude Code exposes the tools as mcp__interioragent__*.

The heavy state (687MB embeddings + retrievers + router) loads ONCE here and is reused across
all tool calls. Tools return a short text summary PLUS inline preview images, and the server
remembers the last candidate set so reselect/show/pin are instant (no re-retrieval).

IMPORTANT: the underlying retriever code print()s to stdout; on stdio MCP, stdout is the
JSON-RPC channel, so every tool body runs under _quiet() which redirects stdout->stderr.

CONCURRENCY MODEL: the LONG tools (run_scene, shop_run, shop_apply, ingest_glbs, plan,
plan_refine) are async and run their bodies in a worker thread, so the event loop stays
responsive during a minutes-long build — pings answered, status/browse tools usable,
cancellations noticed. A single _HEAVY semaphore keeps at most ONE long body running at a
time: the warm singletons, SESSION and the stdout guard were written under whole-server
serialization, and the semaphore preserves that assumption for the heavy paths while the
cheap tools stay interleavable.
"""
import contextlib
import io
import os
import sys
import threading
from dataclasses import dataclass, field

import anyio.to_thread
from mcp.server.fastmcp import FastMCP, Image

from IDSDL.service import core

mcp = FastMCP("interioragent")


# ---- stdout guard (library prints must NOT hit the stdio protocol channel) ----
# Refcounted and thread-safe: with heavy tools in worker threads, a cheap tool on the
# event loop can overlap a heavy one; the swap happens only on the 0<->1 transitions,
# so stdout stays redirected while ANY tool body is running.
_QUIET_LOCK = threading.Lock()
_QUIET_DEPTH = 0
_REAL_STDOUT = None


@contextlib.contextmanager
def _quiet():
    global _QUIET_DEPTH, _REAL_STDOUT
    with _QUIET_LOCK:
        if _QUIET_DEPTH == 0:
            _REAL_STDOUT = sys.stdout
            sys.stdout = sys.stderr
        _QUIET_DEPTH += 1
    try:
        yield
    finally:
        with _QUIET_LOCK:
            _QUIET_DEPTH -= 1
            if _QUIET_DEPTH == 0 and _REAL_STDOUT is not None:
                sys.stdout = _REAL_STDOUT


# ---- heavy-tool offload ---------------------------------------------------------
# One long-running body at a time, in a worker thread. See CONCURRENCY MODEL above.
_HEAVY = threading.Semaphore(1)


async def _offload(body):
    def guarded():
        with _HEAVY:
            return body()
    return await anyio.to_thread.run_sync(guarded)


def _llm_tool(body):
    """Run an LLM-backed tool body; turn a raw OpenAI 401 traceback into an
    actionable one-liner pointing at reload_credentials."""
    try:
        return body()
    except Exception as e:
        hint = core.stale_key_hint(e)
        if hint:
            return [hint]
        raise


# ---- session state for the discovery loop -------------------------------------
@dataclass
class Session:
    last_query: str | None = None
    last_candidates: list = field(default_factory=list)   # {model,path,scale,preview,desc,similarity,chosen}
    last_sheet: str | None = None
    pinned: dict = field(default_factory=dict)            # query -> model id

SESSION = Session()


# ---- helpers ------------------------------------------------------------------
def _img(path, max_px=1100, quality=72, brighten=1.4):
    """Downscaled JPEG Image content for inline display (keeps payloads small)."""
    if not path or not os.path.exists(path):
        return None
    try:
        from PIL import Image as PILImage, ImageEnhance
        im = PILImage.open(path).convert("RGB")
        if brighten and brighten != 1.0:
            im = ImageEnhance.Brightness(im).enhance(brighten)
        if max(im.size) > max_px:
            s = max_px / max(im.size)
            im = im.resize((int(im.width * s), int(im.height * s)))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        return Image(data=buf.getvalue(), format="jpeg")
    except Exception:
        return None


def _candidate_table(d):
    """One-line-per-candidate summary (1-based, matching the contact-sheet labels)."""
    lines = [f"query: {d['query']!r}  ->  retriever={d['retriever']}",
             f"chosen #{_chosen_index(d['candidates'])}: {d['chosen_model']}  (scale {d['scale']})"]
    if d.get("reasoning"):
        lines.append(f"reason: {d['reasoning']}")
    lines.append("candidates (use the # with reselect/show/pin):")
    for i, c in enumerate(d["candidates"], 1):
        sim = f"{c['similarity']:.2f}" if c.get("similarity") is not None else "  -  "
        star = "*" if c.get("chosen") else " "
        lines.append(f" {star}#{i} {sim} {c['model']}  {(c.get('desc') or '')[:54]}")
    return "\n".join(lines)


def _chosen_index(cands):
    for i, c in enumerate(cands, 1):
        if c.get("chosen"):
            return i
    return 1


def _remember(d):
    SESSION.last_query = d["query"]
    SESSION.last_candidates = d["candidates"]
    SESSION.last_sheet = d["sheet"]


# ---- Tier A: warm retrieval (the core loop) -----------------------------------
@mcp.tool()
def retrieve(query: str, pin: str | None = None) -> list:
    """Route + resolve an asset query against the warm dataset and return the visual picker's
    candidates as a contact sheet (inline) plus a numbered table. This is the primary tool for
    the asset-discovery loop. Pass `pin` (a model id) to force a specific asset. After this,
    use reselect/show/pin (they read the remembered candidate set — instant, no re-retrieval)."""
    def body():
        with _quiet():
            d = core.retrieve(query, pin)
        _remember(d)
        out = [_candidate_table(d)]
        img = _img(d["sheet"])
        if img:
            out.append(img)
        return out
    return _llm_tool(body)


@mcp.tool()
def inspect(query: str) -> list:
    """Alias of retrieve: show the visual picker's candidates (contact sheet + table) for a query."""
    return retrieve(query)


@mcp.tool()
def browse(query: str, n: int = 24, semantic: bool = True) -> list:
    """Eyeball many dataset assets matching a query as one labeled montage (inline) + a manifest.
    semantic=True ranks by embedding similarity; semantic=False does an offline substring match on
    descriptions. Use this to hunt by hand when retrieve's top pick isn't right; grab a model id to
    pin via retrieve(query, pin=<id>)."""
    with _quiet():
        b = core.browse(query, n=n, semantic=semantic)
    # make browse results pinnable: remember them as the session candidate set (1-based)
    SESSION.last_query = query
    SESSION.last_candidates = [{"model": m["model"], "preview": m.get("preview"),
                                "desc": m["desc"], "similarity": m["similarity"],
                                "scale": None, "path": None, "chosen": False}
                               for m in b["manifest"]]
    SESSION.last_sheet = b["montage_path"]
    lines = [f"browse {query!r} ({'semantic' if semantic else 'text'}): {len(b['manifest'])} assets"
             "  (use reselect/show/pin with the #)"]
    for m in b["manifest"]:
        sim = f"{m['similarity']:.2f}" if m["similarity"] is not None else "  -  "
        lines.append(f" #{m['idx']} {sim} {m['model']}  {(m['desc'] or '')[:50]}")
    out = ["\n".join(lines)]
    img = _img(b["montage_path"], max_px=1400)
    if img:
        out.append(img)
    return out


@mcp.tool()
def reselect(n: int) -> list:
    """Pick candidate #n from the LAST retrieve/inspect result (1-based, matching the contact
    sheet). Instant — reads the remembered candidates, no re-retrieval. Returns that asset's
    preview inline + the AddAsset(asset_id=…) snippet to pin it."""
    cands = SESSION.last_candidates
    if not cands:
        return ["No remembered candidates — run retrieve/inspect first."]
    if n < 1 or n > len(cands):
        return [f"n out of range; have #{1}..#{len(cands)}."]
    c = cands[n - 1]
    for i, cc in enumerate(cands):
        cc["chosen"] = (i == n - 1)
    txt = (f"selected #{n}: {c['model']}  (scale {c['scale']})\n  {(c.get('desc') or '')}\n"
           f"  {core.addasset_snippet(SESSION.last_query, c['model'])}")
    out = [txt]
    img = _img(c.get("preview"))
    if img:
        out.append(img)
    return out


@mcp.tool()
def show(n: int, big: bool = False) -> list:
    """Show candidate #n's preview image (1-based) from the last retrieve/inspect result, larger.
    Instant, session-only."""
    cands = SESSION.last_candidates
    if not cands or n < 1 or n > len(cands):
        return ["No such candidate — run retrieve/inspect first."]
    c = cands[n - 1]
    img = _img(c.get("preview"), max_px=1600 if big else 1100)
    return [f"#{n}: {c['model']}  {(c.get('desc') or '')[:60]}", img] if img else [f"#{n}: no preview."]


@mcp.tool()
def pin(n: int) -> str:
    """Pin candidate #n (1-based) from the last result as the choice for its query, and return the
    durable AddAsset(asset_id=…) snippet to paste into the scene/skill."""
    cands = SESSION.last_candidates
    if not cands or n < 1 or n > len(cands):
        return "No such candidate — run retrieve/inspect first."
    c = cands[n - 1]
    SESSION.pinned[SESSION.last_query] = c["model"]
    return core.addasset_snippet(SESSION.last_query, c["model"])


# ---- Tier B: curation / pools / ingest ----------------------------------------
@mcp.tool()
def candidates(category: str, topk: int = 10) -> str:
    """Over-generate a candidate id pool from a named prompt-set (e.g. 'hair_salon',
    'presentation') by searching the full dataset. Writes an id-list json (curate it with
    gallery). Returns the count + path + available prompt-sets."""
    with _quiet():
        d = core.candidates(category, topk=topk)
    if not d["ids"]:
        return f"no prompt-set {category!r}. available: {d['available']}"
    return (f"candidates[{category}]: {d['n_unique']} unique ids -> {d['out_path']}\n"
            f"curate next: gallery('{d['out_path']}')   available sets: {d['available']}")


@mcp.tool()
def gallery(source: str, n: int | None = None, hint: str | None = None) -> str:
    """Build the self-contained selection HTML for a pool name / id-list json path / 'all'
    (or 'list' to list pools). A human-in-loop artifact: the user opens it in a browser, keeps
    assets, downloads selection.json. Returns the html path."""
    with _quiet():
        d = core.gallery(source, n=n, hint=hint)
    if "pools" in d:
        return "pools: " + ", ".join(d["pools"])
    return f"gallery -> {d['html_path']}  ({d['size_mb']} MB) — open in a browser, curate, download selection.json"


@mcp.tool()
def pool_add(category: str, ids: list[str], create: bool = False) -> str:
    """Append asset ids to a curated pool json (IDSDL/datasets/assets/<category>.json).
    create=True to require it be new. Returns the pool path + total count."""
    with _quiet():
        d = core.pool_add(category, ids, create=create)
    if d.get("error"):
        return d["error"]
    return f"pool {category}: {d['n_total']} ids -> {d['pool_path']}"


@mcp.tool()
async def ingest_glbs(zip_path: str, category: str | None = None, manifest_path: str | None = None,
                      workers: int = 4) -> str:
    """Ingest a zip of .glb files into the custom pool (render preview -> VLM caption -> embed),
    then re-warm so they're retrievable immediately. SLOW (cold Blender per asset). Supply glbs
    Y-up, front=+Z, real metres; a manifest.json overrides description/placement/scale per file."""
    def body():
        with _quiet():
            return core.ingest_glbs(zip_path, category=category, manifest_path=manifest_path,
                                    workers=workers)
    d = await _offload(body)
    lines = [f"ingested {d['n_added']} asset(s); re-warmed."]
    for a in d["added"]:
        lines.append(f"  + {a['model']}  ({a['placement']}, {a['scale']}m)  {(a['description'] or '')[:50]}")
    return "\n".join(lines)


@mcp.tool()
def shop_search(query: str, count: int = 12, license: str = "permissive") -> str:
    """Search Sketchfab for free downloadable assets WITHOUT ingesting anything. Use this when
    retrieve() has nothing good and you want to know whether the internet does. license:
    permissive (cc0+by, default) | commercial-ok | any."""
    with _quiet():
        d = core.shop_search(query, count=count, license=license)
    if not d["hits"]:
        return f"no downloadable hits for {query!r}. Try a broader query or license='any'."
    lines = [f"{d['n']} hit(s) for {query!r}:"]
    for h in d["hits"]:
        lines.append(f"  {h['name'][:44]:44s} {h['license'] or '?':22s} {h['faces'] or 0:>8,}f  {h['url']}")
    lines.append("ingest them with shop_run(query). "
                 + ("" if d["has_token"] else "NOTE: no SKETCHFAB_API_TOKEN — downloads will be "
                    "handed to the user as manual links."))
    return "\n".join(lines)


@mcp.tool()
async def shop_run(query: str, count: int = 6, source: str = "sketchfab", category: str | None = None,
                   manual: bool = False, dry_run: bool = False) -> str:
    """Search the web for an asset the library lacks, normalize it (single mesh, real metres,
    front=+Z, verified on a re-render) and ingest it — then re-warm so retrieve() can find it
    immediately. VERY SLOW (download + several Blender passes + VLM per candidate).

    Anything the pipeline cannot judge confidently is NOT guessed: it lands on <batch>/HELP.md
    for the user (`manual=True` is the same run, framed as a question). source='meshy' GENERATES
    the asset instead of searching — that spends the user's Meshy credits, so only use it when
    they have asked for it. dry_run=True normalizes but writes nothing to the library."""
    def body():
        with _quiet():
            return core.shop_run(query, count=count, source=source, category=category,
                                 manual=manual, dry_run=dry_run)
    d = await _offload(body)
    lines = [f"shop[{query!r}] {d['counts']}"]
    for a in d["ingested"]:
        lines.append(f"  + {a['asset_id']}  {a['object']}  ({a['width_m']} m wide)  [{a['license']}]")
    for a in d["needs_you"]:
        lines.append(f"  ? {a['key']}  {a['object']}  — {a['why']}")
    for a in d["skipped"]:
        lines.append(f"  - {a['key']} skipped: {a['why']}")
    if d["needs_you"]:
        lines.append(f"user must settle these in {d['help_md']}, then shop_apply(batch).")
    return "\n".join(lines)


@mcp.tool()
async def shop_apply(batch: str, category: str | None = None) -> str:
    """Act on the answers the user wrote into <batch>/HELP.md (and any file they hand-downloaded
    into <batch>/inbox/), ingest what they accepted, and re-warm."""
    def body():
        with _quiet():
            return core.shop_apply(batch, category=category)
    d = await _offload(body)
    lines = [f"shop apply[{batch}] {d['counts']}"]
    for a in d["ingested"]:
        lines.append(f"  + {a['asset_id']}  {a['object']}  ({a['width_m']} m wide)")
    for a in d["needs_you"]:
        lines.append(f"  ? still open: {a['key']} — {a['why']}")
    return "\n".join(lines)


# ---- Tier C: long isolated jobs -----------------------------------------------
@mcp.tool()
async def plan(prompt: str, top_k: int = 3) -> list:
    """Run the interior planner: a design brief (skill.txt) + a reference-collage (plan.png).
    Returns the brief text + the collage inline. ~tens of seconds (image generation)."""
    def body():
        with _quiet():
            d = core.plan(prompt, top_k=top_k)
        if not d["ok"]:
            hint = core.stale_key_hint(RuntimeError(d["stderr_tail"]))
            return [hint or f"planner failed:\n{d['stderr_tail']}"]
        txt = f"PLAN out_dir: {d['out_dir']}\n\n{d['skill']}"
        out = [txt]
        img = _img(d["plan_png"], max_px=1600, brighten=1.0)
        if img:
            out.append(img)
        return out
    return await _offload(lambda: _llm_tool(body))


@mcp.tool()
async def plan_refine(prompt: str, renders: list, prior: list = None,
                      instruction: str = None, top_k: int = 3) -> list:
    """Planner REFINEMENT: generate an IMPROVED visual target from the current scene's renders
    (e.g. a render_collection collage in `renders`) plus the planner's prior target(s) in `prior`
    and the retrieved skills. The composer critiques the build against intent, then image-conditions
    a fresh 2x4 target exploring layout/styling improvements. Returns the revised brief + the new
    target collage inline. ~tens of seconds (image generation)."""
    def body():
        with _quiet():
            d = core.plan_refine(prompt, renders, prior=prior, instruction=instruction,
                                 top_k=top_k)
        if not d["ok"]:
            hint = core.stale_key_hint(RuntimeError(d["stderr_tail"]))
            return [hint or f"refine failed:\n{d['stderr_tail']}"]
        txt = f"REFINE out_dir: {d['out_dir']}\n\n{d['skill']}"
        out = [txt]
        img = _img(d["refined_png"], max_px=1600, brighten=1.0)
        if img:
            out.append(img)
        return out
    return await _offload(lambda: _llm_tool(body))


@mcp.tool()
def lint_program(program_path: str) -> str:
    """Static API lint of a scene program — validates every method call and keyword argument
    against the REAL DSL surface (unknown verbs like place_on_left_adjacent, invented kwargs
    like add_lighting(asset_id=...)) in milliseconds, without building. ALWAYS run this before
    run_scene; run_scene's build also refuses to start on lint errors."""
    d = core.lint_program(program_path=program_path)
    if d["ok"]:
        return f"lint clean: {program_path}"
    return f"{len(d['errors'])} lint error(s) in {program_path}:\n" + "\n".join(d["errors"])


@mcp.tool()
async def run_scene(program_path: str, phase: int | None = None) -> list:
    """Build + render a DSL scene program. SLOW (3-8 min, cold Blender). Lints first (see
    lint_program) and refuses to build on errors. Returns the VLM feedback
    + asset picks + the interior room views inline (first few). Runs subprocess-isolated.
    `phase` (1 anchors / 2 surfaces / 3 all) builds a phase-gated program only up to that
    phase — a phase-1 layout check takes ~1 min instead of ~8 (see IDSDL/phases.py)."""
    def body():
        with _quiet():
            return core.run_scene(program_path, phase=phase)
    d = await _offload(body)
    if not d["ok"] and not d["report"]:
        return [f"run failed:\n{d['stderr_tail']}"]
    rep = d["report"]
    lines = [f"run {program_path}  ok={d['ok']}  run_dir={d['run_dir']}"]
    fb = rep.get("vlm_feedback")
    if fb:
        lines.append("VLM feedback:\n" + (fb if isinstance(fb, str) else "\n".join(map(str, fb))))
    for a in (rep.get("assets") or [])[:12]:
        ch = ""
        for c in a.get("candidates", []):
            if c.get("chosen"):
                ch = (c.get("desc") or c.get("model", ""))[:46]
        lines.append(f"  {a.get('query','')[:38]:38s} -> {ch}")
    out = ["\n".join(lines)]
    for v in d["room_views"][:4]:
        img = _img(v, max_px=1100)
        if img:
            out.append(img)
    return out


# ---- Tier D: knowledge retrieval + end-to-end generation -----------------------
@mcp.tool()
def catalog() -> str:
    """The organized knowledge catalog: every worked example recipe (indexed by LAYOUT PATTERN),
    workflow guide and atomic lesson available for scene generation. Offline/instant. Read this
    to see what tacit knowledge exists; use retrieve_context to have a reasoner select from it."""
    with _quiet():
        return core.catalog_listing()


@mcp.tool()
def retrieve_context(prompt: str, plan: str | None = None,
                     include_programs: bool = True) -> str:
    """Reasoning-based trace retrieval (no embeddings): an LLM reads the WHOLE knowledge catalog
    plus your prompt (and optional planner brief) and selects the procedurally-similar example
    recipes, workflow guides and atomic lessons a scene author must read. Writes the assembled
    context to bundle.md and returns its path + the procedural signature + the selection —
    READ the bundle file before writing the scene program (it is large; not inlined here)."""
    def body():
        with _quiet():
            d = core.retrieve_context(prompt, plan=plan, include_programs=include_programs)
        return (f"procedural signature:\n{d['procedural_signature']}\n\n"
                f"why: {d['reasoning']}\n\n"
                f"examples : {d['examples']}\n"
                f"workflow : {d['workflow_docs']}\n"
                f"lessons  : {len(d['lessons'])} selected\n"
                f"bundle   : {d['bundle_path']}  ({d['bytes']/1000:.0f} KB) — read this file.")
    out = _llm_tool(body)
    return out[0] if isinstance(out, list) else out


@mcp.tool()
def reload_credentials(key: str | None = None) -> str:
    """Fix a stale/rotated OPENAI_API_KEY WITHOUT restarting the server. The warm process
    snapshots env at launch, so a rotated key otherwise 401s every LLM-backed tool. Pass the
    fresh key directly, or write `OPENAI_API_KEY=...` to <repo>/.env and call with no args.
    Rebuilds the LLM-holding singletons in seconds (embedding arrays stay cached)."""
    with _quiet():
        d = core.reload_credentials(key)
    if not d.get("ok"):
        return d.get("error", "reload failed")
    return (f"credentials reloaded from {d['source']} (…{d['key_tail']}); "
            f"{d['models']} models warm. LLM-backed tools are live again.")


@mcp.tool()
def generate_scene_start(prompt: str, seed: int = 42, max_inner: int = 3,
                         max_outer: int = 2, threshold: float = 8.0,
                         skip_stress: bool = False, model: str = "gpt-5") -> str:
    """Launch the FULL text→scene pipeline (plan → retrieve traces → asset stress test → author
    program → build → VLM-critic loop → design-match judging) as a background job. Takes 15-45
    min. Returns the job_id — poll with generate_scene_status, collect with generate_scene_result."""
    with _quiet():
        d = core.generate_start(prompt, seed=seed, max_inner=max_inner,
                                max_outer=max_outer, threshold=threshold,
                                skip_stress=skip_stress, model=model)
    return (f"started {d['job_id']}\nout: {d['out_dir']}\nlog: {d['log_path']}\n"
            f"poll: generate_scene_status('{d['job_id']}')")


@mcp.tool()
def generate_scene_status(job_id: str) -> list:
    """Progress of a generation job: stage log tail, iteration count, design-judge scores so far,
    and the latest room strip inline."""
    with _quiet():
        d = core.generate_status(job_id)
    if d.get("error"):
        return [f"{d['error']}  (known jobs: {d.get('known')})"]
    scores = ", ".join(f"{j['score']:.1f}" for j in d["judgements"]) or "(none yet)"
    lines = [f"{d['job_id']}  running={d['running']}  returncode={d['returncode']}",
             f"iterations: {d['iterations']}   judge scores: {scores}",
             f"design plan: {d.get('plan_png') or '(not yet generated)'}",
             f"--- log tail ---\n{d['log_tail']}"]
    out = ["\n".join(lines)]
    img = _img(d.get("latest_strip"), max_px=1400)
    if img:
        out.append(img)
    return out


@mcp.tool()
def generate_scene_result(job_id: str) -> list:
    """Final artifacts of a finished generation job: score, program path, .blend path, the full
    provenance trace, and — inline — the design plan followed by the final room strip (compare
    them: the plan is the target the build was judged against)."""
    with _quiet():
        d = core.generate_result(job_id)
    if d.get("error"):
        return [d["error"]]
    t = d.get("trace", {})
    lines = [f"{d['job_id']}  score={d.get('score')}",
             f"program: {d['program']}",
             f"blend  : {d['blend']}",
             f"plan   : {d.get('plan_png')}",
             f"trace  : {os.path.join(d['out_dir'], 'trace.json')}"]
    sig = t.get("procedural_signature")
    if sig:
        lines.append(f"\nprocedural signature:\n{sig}")
    out = ["\n".join(lines)]
    for path in (d.get("plan_png"), d.get("final_strip")):
        img = _img(path, max_px=1400, brighten=1.0)
        if img:
            out.append(img)
    return out


# ---- Tier E: the guided 9-gate flow (IDSDL/service/flow.py) --------------------
@mcp.tool()
def howto() -> str:
    """START HERE if you are new to this server: what IDSDL is, the 9-gate scene-generation
    recipe distilled from the worked examples, and which tools to use at each gate."""
    from IDSDL.service import flow
    return flow.howto()


@mcp.tool()
def flow_start(prompt: str) -> str:
    """Begin a guided scene generation for a text prompt. Returns step 1's card: what to do,
    the exact commands, and the evidence to bring back. Each subsequent gate (flow_advance)
    validates your evidence mechanically before revealing the next step — this is how the
    best scenes were built. State is file-backed; flow_status resumes after a disconnect."""
    from IDSDL.service import flow
    with _quiet():
        return flow.flow_start(prompt)


@mcp.tool()
def flow_status(flow_id: str) -> str:
    """Where a guided flow stands: gates passed (with any overrides) + the current step card."""
    from IDSDL.service import flow
    with _quiet():
        return flow.flow_status(flow_id)


@mcp.tool()
def flow_advance(flow_id: str, evidence: str) -> str:
    """Submit the current gate's evidence (a JSON object — see the EVIDENCE line of the step
    card). Validated mechanically (files exist, program lints clean, fresh phase-N report, no
    unresolved [Lint]/WARNING lines). On pass: the next step card. On fail: exactly what to fix."""
    from IDSDL.service import flow
    with _quiet():
        return flow.flow_advance(flow_id, evidence)


@mcp.tool()
def flow_override(flow_id: str, reason: str) -> str:
    """Pass the current gate WITHOUT valid evidence, recording your reasoning in the flow's
    provenance. For deliberate deviations only — gates guide, they don't imprison."""
    from IDSDL.service import flow
    with _quiet():
        return flow.flow_override(flow_id, reason)


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("[interioragent-mcp] FATAL: OPENAI_API_KEY not set; retrieval/LLM calls will fail.",
              file=sys.stderr)
    try:
        with _quiet():
            info = core.warm()
    except FileNotFoundError as e:
        # The most common fresh-clone failure: datasets.zip was never installed. Say so
        # plainly on stderr — the MCP client only shows "server failed" otherwise.
        print(f"[interioragent-mcp] FATAL: {e}", file=sys.stderr)
        print("[interioragent-mcp] The asset datasets are not installed. Download datasets.zip and "
              "extract it into IDSDL/datasets/ (see README: Installation), then reconnect.",
              file=sys.stderr)
        sys.exit(1)
    mode = " (MINIMAL curated library)" if info.get("minimal") else ""
    print(f"[interioragent-mcp] warm: {info['models']} models loaded{mode}; serving stdio.",
          file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
