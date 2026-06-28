"""IDSDL MCP server (stdio) — warm, typed tools for the asset-discovery loop.

Run:  PYTHONPATH=/work /opt/conda/envs/interioragent/bin/python -m IDSDL.service.mcp_server
Registered via /work/.mcp.json so Claude Code exposes the tools as mcp__idsdl__*.

The heavy state (687MB embeddings + retrievers + router) loads ONCE here and is reused across
all tool calls. Tools return a short text summary PLUS inline preview images, and the server
remembers the last candidate set so reselect/show/pin are instant (no re-retrieval).

IMPORTANT: the underlying retriever code print()s to stdout; on stdio MCP, stdout is the
JSON-RPC channel, so every tool body runs under _quiet() which redirects stdout->stderr.
"""
import contextlib
import io
import os
import sys
from dataclasses import dataclass, field

from mcp.server.fastmcp import FastMCP, Image

from IDSDL.service import core

mcp = FastMCP("idsdl")


# ---- stdout guard (library prints must NOT hit the stdio protocol channel) ----
@contextlib.contextmanager
def _quiet():
    with contextlib.redirect_stdout(sys.stderr):
        yield


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
    with _quiet():
        d = core.retrieve(query, pin)
    _remember(d)
    out = [_candidate_table(d)]
    img = _img(d["sheet"])
    if img:
        out.append(img)
    return out


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
def ingest_glbs(zip_path: str, category: str | None = None, manifest_path: str | None = None,
                workers: int = 4) -> str:
    """Ingest a zip of .glb files into the custom pool (render preview -> VLM caption -> embed),
    then re-warm so they're retrievable immediately. SLOW (cold Blender per asset). Supply glbs
    Y-up, front=+Z, real metres; a manifest.json overrides description/placement/scale per file."""
    with _quiet():
        d = core.ingest_glbs(zip_path, category=category, manifest_path=manifest_path, workers=workers)
    lines = [f"ingested {d['n_added']} asset(s); re-warmed."]
    for a in d["added"]:
        lines.append(f"  + {a['model']}  ({a['placement']}, {a['scale']}m)  {(a['description'] or '')[:50]}")
    return "\n".join(lines)


# ---- Tier C: long isolated jobs -----------------------------------------------
@mcp.tool()
def plan(prompt: str, top_k: int = 3) -> list:
    """Run the interior planner: a design brief (skill.txt) + a reference-collage (plan.png).
    Returns the brief text + the collage inline. ~tens of seconds (image generation)."""
    with _quiet():
        d = core.plan(prompt, top_k=top_k)
    if not d["ok"]:
        return [f"planner failed:\n{d['stderr_tail']}"]
    txt = f"PLAN out_dir: {d['out_dir']}\n\n{d['skill']}"
    out = [txt]
    img = _img(d["plan_png"], max_px=1600, brighten=1.0)
    if img:
        out.append(img)
    return out


@mcp.tool()
def run_scene(program_path: str) -> list:
    """Build + render a DSL scene program. SLOW (3-8 min, cold Blender). Returns the VLM feedback
    + asset picks + the interior room views inline (first few). Runs subprocess-isolated."""
    with _quiet():
        d = core.run_scene(program_path)
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


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("[idsdl-mcp] FATAL: OPENAI_API_KEY not set; retrieval/LLM calls will fail.",
              file=sys.stderr)
    with _quiet():
        info = core.warm()
    print(f"[idsdl-mcp] warm: {info['models']} models loaded; serving stdio.", file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
