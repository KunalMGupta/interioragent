"""
Scene workbench — run a DSL scene program and surface everything needed to
iterate on it in one place:

  * the per-run scratchpad directory (tmp/<run_id>/)
  * the VLM textual feedback collected during compile (otherwise write-only on
    scene.vlm_feedback and never seen)
  * an index of every render produced this run, with paths to open/inspect

Usage:
    python workbench.py run path/to/scene_program.py
    python workbench.py report                 # re-print the latest run's saved report

Run under the project env:
    PYTHONPATH=/work /opt/conda/envs/interioragent/bin/python workbench.py run scene.py

The program is executed as a normal script (its `scene.export(...)` etc. run as
written). Afterwards the workbench finds the SceneProgRoom in its namespace and
reports. It also writes feedback.txt and report.json into the run directory so
`report` can re-show the latest run without recomputing.
"""
import argparse
import glob
import html
import json
import os
import runpy
import sys

from IDSDL.service import core as _svc   # shared logic (browse/montage live here)


def latest_run_dir():
    dirs = sorted(glob.glob("tmp/2*"), key=os.path.getmtime)
    return dirs[-1] if dirs else None


def _find_scene(ns):
    from IDSDL.scene import SceneProgRoom
    scenes = [v for v in ns.values() if isinstance(v, SceneProgRoom)]
    return scenes[-1] if scenes else None


def _collect_assets(scene):
    """Retrieval provenance for every asset with a recorded query (chosen + candidates)."""
    out, seen = [], set()
    pools = [getattr(scene, "objects", []), getattr(scene, "wall_objects", []),
             getattr(scene, "ceiling_lights", [])]
    for pool in pools:
        for o in pool:
            q = getattr(o, "retrieval_query", None)
            if not q or id(o) in seen:
                continue
            seen.add(id(o))
            cands = getattr(o, "retrieval_candidates", []) or []
            out.append({
                "query": q,
                "chosen": getattr(o, "retrieval_model", None),
                "candidates": [
                    {"model": c.get("model"), "desc": c.get("desc", ""),
                     "preview": c.get("preview"), "chosen": c.get("chosen", False),
                     "similarity": c.get("similarity")}
                    for c in cands
                ],
            })
    return out


def _collect(scene):
    run_dir = getattr(scene, "run_dir", None)
    feedback = (getattr(scene, "vlm_feedback", "") or "").strip()
    renders = []
    if run_dir and os.path.isdir(run_dir):
        renders = sorted(
            glob.glob(os.path.join(run_dir, "**", "*.png"), recursive=True)
        )
    return {
        "scene": getattr(scene, "name", "?"),
        "run_dir": run_dir,
        "counts": {
            "objects": len(getattr(scene, "objects", [])),
            "walls": len(getattr(scene, "walls", [])),
            "wall_objects": len(getattr(scene, "wall_objects", [])),
            "ceiling_lights": len(getattr(scene, "ceiling_lights", [])),
        },
        "vlm_feedback": feedback,
        "assets": _collect_assets(scene),
        "renders": renders,
    }


def _persist(report):
    run_dir = report["run_dir"]
    if not run_dir or not os.path.isdir(run_dir):
        return
    with open(os.path.join(run_dir, "feedback.txt"), "w") as f:
        f.write(report["vlm_feedback"] + "\n")
    with open(os.path.join(run_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)


def _print(report):
    bar = "=" * 70
    print(f"\n{bar}\n WORKBENCH REPORT — scene '{report['scene']}'\n{bar}")
    print(f" run_dir : {report['run_dir']}")
    c = report["counts"]
    print(f" scene   : {c['objects']} objects, {c['walls']} walls, "
          f"{c['wall_objects']} wall-objects, {c['ceiling_lights']} ceiling-lights")

    print("\n--- VLM FEEDBACK (collected this compile) ---")
    if report["vlm_feedback"]:
        print(report["vlm_feedback"])
    else:
        print("(none — no VLM constraint produced feedback, or no group with VLM "
              "constraints compiled)")

    print("\n--- ASSETS (retrieval: * = chosen; #N=sheet label, idx N-1 for reselect_asset) ---")
    assets = report.get("assets", [])
    if not assets:
        print("(no retrieval provenance recorded)")
    for a in assets:
        print(f"  query: {a['query']!r}")
        for i, c in enumerate(a["candidates"]):
            mark = "*" if c["chosen"] else " "
            sim = f"{c['similarity']:.3f}" if c.get("similarity") is not None else "  -  "
            print(f"    {mark}#{i+1} (idx {i}) {sim} {c['model']}  {c['desc'][:42]}")
            if c["chosen"] or not c.get("preview"):
                print(f"         preview: {c.get('preview') or '(none)'}")

    print("\n--- RENDERS ---")
    if report["renders"]:
        for p in report["renders"]:
            print(f"  {p}")
    else:
        print("(none found under run_dir)")
    print(bar + "\n")


def cmd_run(program_path):
    program_path = os.path.abspath(program_path)
    if not os.path.isfile(program_path):
        print(f"[workbench] no such program: {program_path}", file=sys.stderr)
        return 1
    print(f"[workbench] running {program_path} ...")
    ns = runpy.run_path(program_path, run_name="__main__")
    scene = _find_scene(ns)
    if scene is None:
        print("[workbench] no SceneProgRoom instance found in program namespace.",
              file=sys.stderr)
        return 1
    report = _collect(scene)
    _persist(report)
    _print(report)
    return 0


def cmd_report():
    run_dir = latest_run_dir()
    if not run_dir:
        print("[workbench] no runs under tmp/.", file=sys.stderr)
        return 1
    path = os.path.join(run_dir, "report.json")
    if not os.path.isfile(path):
        print(f"[workbench] latest run {run_dir} has no report.json "
              f"(was it produced by `workbench run`?).", file=sys.stderr)
        return 1
    with open(path) as f:
        _print(json.load(f))
    return 0


def cmd_inspect(query, render=False):
    """Run retrieval for a query and surface the candidate set (the agentic picker's view).

    Prints the contact sheet + each candidate's preview path. With --render, loads the top
    two finalists into a bare object and renders each (opt-in higher-fidelity look).
    """
    from IDSDL.datasets.retrievers import SceneProgAssetRetriever
    r = SceneProgAssetRetriever(seed=None)
    r(query)
    cands = r.last_candidates
    print(f"\nquery: {query!r}")
    if r.last_sheet:
        print(f"contact sheet: {r.last_sheet}")
    if getattr(r, "last_reasoning", None):
        print(f"VLM decision : {r.last_reasoning}")
    print("(#N matches the contact-sheet label / the VLM's choice; idx N-1 for reselect_asset)")
    for i, c in enumerate(cands):
        mark = "*" if c.get("chosen") else " "
        sim = f"{c['similarity']:.3f}" if c.get("similarity") is not None else "  -  "
        print(f"  {mark}#{i+1} (idx {i}) {sim} {c['model']}  {c.get('desc','')[:46]}")
        print(f"        preview: {c.get('preview')}")

    if render:
        from IDSDL.scene import SceneProgRoom
        scene = SceneProgRoom("Inspect", seed=None)
        finalists = ([c for c in cands if c.get("chosen")] +
                     [c for c in cands if not c.get("chosen")])[:2]
        print("\n--- finalist renders ---")
        for c in finalists:
            try:
                obj = scene.add_asset(c["path"], c["scale"], query)
                print(f"  {c['model']}: {obj.render()}")
            except Exception as e:
                print(f"  {c['model']} render failed: {e}")
    return 0


def cmd_browse(query, n=24, text=False, out=None):
    """Montage the dataset assets matching a query so you can eyeball them by hand. Thin wrapper
    over the shared IDSDL.service.core.browse (single source of the browse/montage logic)."""
    d = _svc.browse(query, n=n, semantic=not text, out=out)
    print(f"\nbrowse {query!r} ({'semantic' if d['semantic'] else 'text'}): {len(d['manifest'])} assets")
    print(f"montage: {d['montage_path']}")
    print("(use the model id with AddAsset(..., asset_id=...) ; for selection use `gallery`)")
    for m in d["manifest"]:
        sm = f"{m['similarity']:.3f}" if m["similarity"] is not None else "  -  "
        print(f"  #{m['idx']:<2} {sm} {m['model']}  {(m['desc'] or '')[:50]}")
    return 0


_SELECT_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>{title} — select</title>
<style>
 body{{font-family:system-ui,sans-serif;margin:0;background:#1e1e1e;color:#ddd}}
 header{{position:sticky;top:0;background:#252526;padding:12px 16px;border-bottom:1px solid #333;z-index:10;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
 header h2{{margin:0;font-size:16px}}
 .hint{{color:#9a9;font-size:12px;max-width:620px}}
 button{{padding:7px 12px;background:#3a3a3a;color:#eee;border:1px solid #555;border-radius:5px;cursor:pointer;font-size:13px}}
 button.dl{{background:#0a8a3a;color:#fff;border:0;font-size:14px}}
 input[type=text]{{padding:6px 8px;background:#333;color:#eee;border:1px solid #555;border-radius:4px;width:220px}}
 .count{{color:#6fd06f;font-weight:bold}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;padding:14px}}
 .card{{background:#2a2a2b;border:2px solid #3a3a3a;border-radius:6px;padding:7px;font-size:12px;cursor:pointer;user-select:none}}
 .card.keep{{border-color:#3ad06f;background:#22302a}}
 .card img{{width:100%;background:#111;border-radius:4px;display:block;pointer-events:none}}
 .id{{font-family:monospace;font-size:10px;color:#9cc;word-break:break-all;margin:5px 0 2px}}
 .desc{{color:#bbb;min-height:28px}}
 .mark{{margin-top:3px;font-weight:bold;color:#888}}
 .card.keep .mark{{color:#3ad06f}}
</style></head><body>
<header>
 <h2>{title}</h2>
 <button class="dl" onclick="dl()">⬇ Download selection.json (<span class="count" id="k">0</span> kept)</button>
 <button onclick="setAll(true)">keep all</button>
 <button onclick="setAll(false)">clear</button>
 <input type="text" id="filter" placeholder="filter by text… (Enter)" onkeydown="if(event.key==='Enter')applyFilter()">
 <span class="hint">{hint}</span>
</header>
<div class="grid" id="grid"></div>
<script>
const CARDS = {cards_json};
const keep = {{}};
function cardHTML(c){{
 const k = keep[c.model];
 return `<div class="card ${{k?'keep':''}}" id="c_${{c.idx}}" onclick="tog(${{c.idx}})">
   <img loading="lazy" src="data:image/jpeg;base64,${{c.img}}" alt="no preview">
   <div class="id">${{c.model}}</div>
   <div class="desc">${{c.desc}}</div>
   <div class="mark">${{k?'✓ keep':'click to keep'}}</div></div>`;
}}
let VIEW = CARDS;
function render(){{ document.getElementById('grid').innerHTML = VIEW.map(cardHTML).join(''); upd(); }}
function tog(i){{ const c=CARDS[i]; keep[c.model]=!keep[c.model];
 const el=document.getElementById('c_'+i); el.outerHTML=cardHTML(c); upd(); }}
function setAll(v){{ VIEW.forEach(c=> keep[c.model]=v); render(); }}
function upd(){{ document.getElementById('k').textContent = Object.values(keep).filter(Boolean).length; }}
function applyFilter(){{ const q=document.getElementById('filter').value.toLowerCase();
 VIEW = q ? CARDS.filter(c=> (c.model+' '+c.desc).toLowerCase().includes(q)) : CARDS; render(); }}
function dl(){{
 const sel = CARDS.filter(c=>keep[c.model]).map(c=>c.model);
 const blob=new Blob([JSON.stringify(sel,null,1)],{{type:'application/json'}});
 const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
 a.download='selection.json'; a.click();
}}
render();
</script></body></html>"""


_SELECT_HINT = ("Click an asset to KEEP it (turns green); click again to drop it. Keep the "
                "ones that belong in this category; ignore the rest. Use the filter box to "
                "narrow (then 'keep all'/'clear' act on the filtered view). Then Download "
                "selection.json and send it back.")


def _safe_name(s):
    return "".join(c if c.isalnum() else "_" for c in s)[:40]


def _emit_select_html(models, title, out, hint=None):
    """Write a self-contained SELECTION HTML for a list of model ids: base64 previews, click
    to keep/drop, Download selection.json (the kept ids). Reusable by gallery/candidates."""
    import base64
    import io
    import json as _json
    from PIL import Image, ImageEnhance
    from IDSDL.datasets.retrievers import FUTURE_HSSD_ASSET_RETRIEVERS
    r = FUTURE_HSSD_ASSET_RETRIEVERS[0]

    cards = []
    for i, m in enumerate(models):
        prev = r._preview_path(m)
        b64 = ""
        if prev and os.path.exists(prev):
            im = Image.open(prev).convert("RGB")
            im = ImageEnhance.Brightness(im).enhance(1.4)
            im.thumbnail((200, 200))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=70)
            b64 = base64.b64encode(buf.getvalue()).decode()
        cards.append({"idx": i, "model": m,
                      "desc": (r.metadata.get(m, {}).get("description", "") or "")[:80],
                      "img": b64})

    cards_json = _json.dumps(cards).replace("</", "<\\/")  # safe inside <script>
    page = _SELECT_HTML.format(cards_json=cards_json, title=html.escape(title),
                               hint=html.escape(hint or _SELECT_HINT))
    with open(out, "w") as f:
        f.write(page)
    mb = os.path.getsize(out) / 1e6
    print(f"\nwrote {out}  ({len(cards)} assets, {mb:.1f} MB)")
    print("Download it, open in a browser, click assets to KEEP, then Download selection.json")
    print("and send it back (a JSON array of kept ids).")
    return 0


def cmd_gallery(source, n=None, page=0, out=None, hint=None):
    """Self-contained SELECTION HTML for a set of assets. `source` is one of:
      list                      -> print the available category pools
      <pool name or json path>  -> all ids in that pool / id-list json
      all                       -> the whole dataset, paginated (--n page size, --page index)
    """
    import json as _json
    from IDSDL.datasets import retrievers
    assets_dir = os.path.join(os.path.dirname(retrievers.__file__), "assets")
    r = retrievers.FUTURE_HSSD_ASSET_RETRIEVERS[0]

    if source in ("list", "--list"):
        print("available pools (IDSDL/datasets/assets/*.json):")
        for f in sorted(os.listdir(assets_dir)):
            if f.endswith(".json") and f != "futurehssd.json":
                print("  ", f[:-5])
        return 0

    if source == "all":
        allm = r.all_models.tolist()
        per = n or 500
        models = allm[page * per:(page + 1) * per]
        name = f"all_p{page}"
        title = f"full dataset — page {page} ({len(models)} of {len(allm)}; --page to advance)"
    else:
        path = (source if os.path.exists(source)
                else os.path.join(assets_dir, source if source.endswith(".json") else source + ".json"))
        if not os.path.exists(path):
            print(f"[gallery] no such pool/json: {path}  (try `workbench.py gallery list`)")
            return 1
        data = _json.load(open(path))
        models = data if isinstance(data, list) else list(data.keys())
        if n:
            models = models[:n]
        name = os.path.basename(path)[:-5]
        title = f"{name} — {len(models)} assets"

    out = out or os.path.join("/work", f"gallery_{_safe_name(name)}.html")
    return _emit_select_html(models, title, out, hint)


# Prompt sets used by `candidates` to over-generate a pool from the FULL dataset, which you
# then curate down in the selection gallery. Add categories here as we build more pools.
CANDIDATE_PROMPTS = {
    "hair_salon": [
        # --- styling chairs / barber seating (specific + generic, to surface what really exists) ---
        "a barber chair", "a salon styling chair", "a hydraulic barber chair", "a hairdressing chair",
        "a reclining barber chair", "a vintage barber chair", "a modern salon chair", "a beauty salon chair",
        "a black leather salon chair", "an upholstered swivel chair with a chrome base",
        "a swivel armchair on a star base", "a salon chair with a footrest",
        # --- stools / tool carts / trolleys ---
        "a rolling salon stool", "a hydraulic cutting stool", "a saddle stool on wheels",
        "a hairdresser's tool trolley", "a rolling utility cart with drawers", "a salon trolley cart",
        "a beauty trolley on wheels", "a small rolling cart with trays", "a tool cart on casters",
        # --- mirrors / styling stations ---
        "a large wall mirror", "a tall framed mirror", "a full-length floor mirror",
        "a salon styling station with a mirror", "a wall-mounted vanity mirror", "a rectangular wall mirror",
        "an ornate gold framed mirror", "a round wall mirror", "a styling station console with drawers",
        "a barber station cabinet with a mirror",
        # --- wash / shampoo area ---
        "a shampoo bowl basin", "a salon backwash unit", "a reclining shampoo chair with a basin",
        "a ceramic wash basin on a pedestal", "a hair washing sink station", "a beauty salon sink",
        # --- drying / processing equipment ---
        "a hooded hair dryer chair", "a standing hooded salon dryer", "a rollerball hair processor",
        "a salon hair dryer on a stand", "a bonnet hood dryer",
        # --- reception / checkout / retail display ---
        "a reception desk", "a salon reception counter", "a curved reception desk", "a modern front desk",
        "a retail checkout counter", "a glass display counter", "a freestanding retail shelf unit",
        "a wall-mounted display shelf", "a glass display cabinet", "a cosmetics product display shelf",
        "a tiered product display stand", "a tall open shelving unit", "a retail product cabinet",
        # --- waiting area ---
        "a waiting room bench", "a row of linked waiting chairs", "a small two-seat sofa",
        "a modern lounge armchair", "a magazine rack", "a small round coffee table", "a low side table",
        # --- storage / utility / plants ---
        "a tall storage cabinet", "a towel storage cabinet", "a low cabinet with drawers",
        "a mini refrigerator", "a coat rack stand", "a tall potted floor plant", "a medium potted plant",
        "a decorative floor vase", "a trash can", "a floor rug",
        # --- wall decor / lighting / signage ---
        "a framed wall art print", "a set of framed pictures", "a pendant ceiling light",
        "a modern chandelier", "a wall-mounted menu price board", "a neon wall sign", "a round wall clock",
    ],
    "desktop": [
        # --- monitors / screens / computers (the workstation hero surface item) ---
        "a computer monitor", "a flat screen computer monitor", "a widescreen desktop monitor",
        "a monitor on a stand", "a dual monitor setup", "an all-in-one desktop computer",
        "an iMac style computer", "a desktop PC tower", "a laptop computer", "an open laptop",
        "a small computer monitor", "a curved gaming monitor", "a computer display screen",
        # --- keyboard / mouse / input ---
        "a computer keyboard", "a keyboard and mouse", "a computer mouse", "a wireless keyboard",
        "a mechanical keyboard", "a mouse and mouse pad", "a keyboard on a desk",
        # --- desk / task lighting ---
        "a desk lamp", "a task desk lamp", "an articulated desk lamp", "a modern desk lamp",
        "a small table lamp", "a banker's desk lamp", "an LED desk lamp",
        # --- desk organizers / stationery ---
        "a pen holder", "a desk pen cup", "a desk organizer", "a desk organizer tray",
        "a pencil cup with pens", "a stack of papers", "a stack of books on a desk",
        "a stack of notebooks", "a stapler", "a desk file tray", "a paper tray organizer",
        "a small clock on a desk", "a desk calendar", "a sticky note pad",
        # --- desk decor / personal items ---
        "a small potted succulent", "a small desk plant", "a small potted plant for a desk",
        "a picture frame", "a small photo frame", "a coffee mug", "a pen cup with a plant",
        "a desk telephone", "an office telephone", "a small trophy", "a desk pencil sharpener",
        # --- office peripherals ---
        "a desktop printer", "a small office printer", "a desk speaker", "a webcam",
    ],
    "presentation": [
        # chalk / black boards
        "a large green chalkboard", "a black chalkboard with a wooden frame", "a classroom blackboard",
        "a green classroom chalkboard with an aluminum frame", "a rolling chalkboard on wheels",
        "a sliding chalkboard panel", "a vintage slate blackboard", "a small black chalkboard sign",
        "a framed green chalkboard", "a large wall-mounted blackboard", "a school chalkboard with a chalk tray",
        "a double-sided chalkboard", "a black writing board", "a green writing board for a classroom", "a tall blackboard",
        # whiteboards
        "a white dry-erase whiteboard", "a magnetic whiteboard", "a mobile whiteboard on a stand",
        "a large conference room whiteboard", "a framed whiteboard with a marker tray", "a glass whiteboard",
        "a wall-mounted whiteboard", "a small whiteboard", "a gridded whiteboard", "a double-sided rolling whiteboard",
        "a dry erase board with an aluminum frame", "a markerboard for an office", "a portable whiteboard easel",
        "a large white presentation board", "a whiteboard on casters",
        # bulletin / cork / notice
        "a cork bulletin board", "a notice board", "a fabric pin board", "a framed cork board",
        "a classroom notice board", "an office bulletin board", "a memo board", "a message board with cork",
        "a large cork board", "a felt notice board", "a combination cork and whiteboard", "a wall-mounted bulletin board",
        # easels / flip charts
        "a flip chart easel", "an art easel", "a wooden display easel", "a presentation easel stand",
        "a tripod easel", "a flip chart stand with a paper pad", "a metal easel", "a tabletop easel",
        "an adjustable studio easel", "a poster display easel",
        # projectors
        "a ceiling-mounted projector", "a portable projector", "an overhead projector", "a short-throw projector",
        "a classroom projector", "a conference room projector", "a projector on a stand", "a mini projector",
        "a data projector", "a video projector",
        # screens
        "a pull-down projection screen", "a tripod projection screen", "a motorized projection screen",
        "a wall-mounted projector screen", "a fixed-frame projection screen", "a portable projector screen",
        "a large presentation screen", "a retractable projection screen", "a white projection screen",
        "a classroom projection screen",
        # podiums / lecterns
        "a wooden podium", "an acrylic lectern", "a lectern with a microphone", "a presentation podium",
        "a conference lectern", "a church pulpit", "an adjustable height podium", "a modern podium",
        "a speaker's lectern", "a tabletop lectern",
        # displays / TVs / monitors
        "a wall-mounted flat screen TV", "a large LED television", "a conference room display screen",
        "an interactive touch display", "a digital signage display", "a wall-mounted monitor",
        "a large presentation monitor", "a flat panel display on the wall", "a smart board interactive whiteboard",
        "a meeting room television",
        # maps / globes / charts
        "a world map for a classroom wall", "a pull-down classroom map", "a globe on a stand", "a world globe",
        "an educational wall chart", "an alphabet poster for a classroom", "a periodic table chart", "a large wall map",
    ],
}


def cmd_candidates(category, topk=10, out=None):
    """Over-generate a candidate id pool by searching the FULL dataset with many prompts.

    For each prompt in CANDIDATE_PROMPTS[category], take the top-`topk` most similar assets;
    union + dedupe across all prompts. Writes a json id-list you then curate down with
    `workbench.py gallery <that json>`.
    """
    import json as _json
    import numpy as np
    from IDSDL.datasets.retrievers import FUTURE_HSSD_ASSET_RETRIEVERS
    r = FUTURE_HSSD_ASSET_RETRIEVERS[0]

    prompts = CANDIDATE_PROMPTS.get(category)
    if not prompts:
        print(f"[candidates] no prompt set '{category}'. available: {list(CANDIDATE_PROMPTS)}")
        return 1

    vecs = np.array(r.encoder.embed_documents(prompts))      # (P, D)
    sims = r.all_embeddings @ vecs.T                          # (N, P)
    picks = []
    for j in range(len(prompts)):
        top = np.argsort(sims[:, j])[-topk:][::-1]
        picks.extend(r.all_models[i] for i in top)
    uniq = sorted(set(picks))

    out = out or os.path.join("/work", f"candidates_{_safe_name(category)}.json")
    _json.dump(uniq, open(out, "w"), indent=1)
    print(f"{len(prompts)} prompts × top{topk} = {len(picks)} picks → {len(uniq)} unique")
    print(f"wrote {out}")
    print(f"Curate them:  python workbench.py gallery {out}")
    return 0


SCRATCH_BROWSE = os.path.join(
    os.environ.get("WORKBENCH_OUT",
                   "/tmp/claude-0/-work/747d828f-5d53-4053-8866-536f23c7a768/scratchpad"),
    "browse")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="workbench")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a scene program and report")
    r.add_argument("program", help="path to a scene .py program")
    sub.add_parser("report", help="re-print the latest run's saved report")
    ins = sub.add_parser("inspect", help="show retrieval candidates for a query")
    ins.add_argument("query", help="asset description to retrieve")
    ins.add_argument("--render", action="store_true",
                     help="also render the top-2 finalists (slow; opt-in)")
    br = sub.add_parser("browse", help="montage of dataset assets matching a query")
    br.add_argument("query", help="what to browse (e.g. 'a teachers desk')")
    br.add_argument("--n", type=int, default=24, help="how many assets (default 24)")
    br.add_argument("--text", action="store_true", help="substring match on descriptions (offline)")
    br.add_argument("--out", default=None, help="output PNG path")
    gl = sub.add_parser("gallery", help="self-contained SELECTION HTML for a pool / id-list / 'all'")
    gl.add_argument("source", help="pool name (e.g. presentation_fixtures), a json id-list path, 'all', or 'list'")
    gl.add_argument("--n", type=int, default=None, help="cap assets (page size for 'all')")
    gl.add_argument("--page", type=int, default=0, help="page index when source='all'")
    gl.add_argument("--out", default=None, help="output .html path")
    gl.add_argument("--hint", default=None, help="guidance text shown in the tool header")
    cd = sub.add_parser("candidates", help="over-generate a candidate id pool from many prompts (to curate)")
    cd.add_argument("category", help=f"prompt set: {list(CANDIDATE_PROMPTS)}")
    cd.add_argument("--topk", type=int, default=10, help="picks per prompt (default 10)")
    cd.add_argument("--out", default=None, help="output candidates .json path")
    args = ap.parse_args(argv)

    if args.cmd == "run":
        return cmd_run(args.program)
    if args.cmd == "report":
        return cmd_report()
    if args.cmd == "inspect":
        return cmd_inspect(args.query, render=args.render)
    if args.cmd == "browse":
        return cmd_browse(args.query, n=args.n, text=args.text, out=args.out)
    if args.cmd == "gallery":
        return cmd_gallery(args.source, n=args.n, page=args.page, out=args.out, hint=args.hint)
    if args.cmd == "candidates":
        return cmd_candidates(args.category, topk=args.topk, out=args.out)
    return 2


if __name__ == "__main__":
    sys.exit(main())
