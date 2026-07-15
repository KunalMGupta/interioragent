"""Recover provenance for custom-library assets ingested before the shop recorded it.

The bundled library (IDSDL/datasets/custom/) redistributes third-party models, and most of the
older entries carry no author/license record. For each such orphan this tool searches Sketchfab
by the asset's description, then shows the VLM our tracked preview render next to the candidate
thumbnails and asks whether any candidate is the SAME model (not merely the same category).

  - confident match, CC/redistributable license  -> provenance written into custom.json
  - confident match, restrictive license          -> flagged on the HELP board (human decision)
  - no confident match                            -> HELP board with the render + best guesses

Resumable: per-asset results persist in shops/attribution/state.json, so re-runs only touch
assets not yet settled. After a run it regenerates ATTRIBUTIONS.md and the HELP board.

Usage:
    python tools/attribution_recover.py [--limit N] [--min-conf 0.75] [--retry-errors]
Requires OPENAI_API_KEY (VLM compare). Sketchfab search is public, no token needed.
"""

import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CUSTOM_JSON = os.path.join(ROOT, "IDSDL/datasets/custom/custom.json")
IMAGES_DIR = os.path.join(ROOT, "IDSDL/datasets/custom/images")
WORK_DIR = os.path.join(ROOT, "shops/attribution")
STATE_PATH = os.path.join(WORK_DIR, "state.json")
HELP_PATH = os.path.join(WORK_DIR, "HELP.md")
SEARCH_API = "https://api.sketchfab.com/v3/search"
N_CANDIDATES = 8

# Licenses under which redistribution-with-attribution is allowed. Sketchfab's "Standard" and
# "Editorial" licenses do NOT permit redistribution — a match under those is a HUMAN decision.
_REDISTRIBUTABLE = re.compile(r"^(cc(0|\s|-|\b)|public domain|free standard)", re.I)


def _load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {}


def _save_state(state):
    os.makedirs(WORK_DIR, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=1)


_QUERY_SYS = """You turn a 3D-asset catalogue description into Sketchfab search queries.
Sketchfab search is literal and AND-like: long specific phrases return nothing. Give two short
queries naming the object itself: `query` (2-4 words, the most likely wording an uploader used)
and `alt_query` (a different 2-4 word phrasing or synonym)."""


def _make_query_llm():
    from sceneprogllm import LLM
    return LLM(system_desc=_QUERY_SYS, response_format="json",
               response_params={"query": "str", "alt_query": "str"})


def _queries_for(entry, query_llm):
    desc = entry.get("description", "").strip().rstrip(".")
    words = re.sub(r"[^\w\s-]", " ", desc).split()
    # deterministic head-noun guess: the tokens before the first qualifier preposition,
    # last two of them ("Three-panel green chalkboard with ..." -> "green chalkboard")
    head = []
    for w in words:
        if w.lower() in ("with", "on", "in", "featuring", "and", "atop"):
            break
        head.append(w)
    fallbacks = [" ".join(head[-2:]), " ".join(words[:4])]
    try:
        out = query_llm(desc)
        out = out if isinstance(out, dict) else getattr(out, "__dict__", {})
        qs = [out.get("query", ""), out.get("alt_query", "")] + fallbacks
    except Exception:
        qs = fallbacks
    return [q for q in dict.fromkeys(q.strip() for q in qs) if q]


def _search(query):
    r = requests.get(SEARCH_API, params={"type": "models", "q": query, "count": N_CANDIDATES},
                     timeout=30)
    r.raise_for_status()
    return r.json().get("results", [])


def _thumb_url(result, target=512):
    images = ((result.get("thumbnails") or {}).get("images")) or []
    if not images:
        return None
    return min(images, key=lambda im: abs(im.get("width", 0) - target)).get("url")


def _fetch_thumbs(mid, results):
    tdir = os.path.join(WORK_DIR, "thumbs", mid.split("/", 1)[-1])
    os.makedirs(tdir, exist_ok=True)
    paths = []
    for i, res in enumerate(results):
        url = _thumb_url(res)
        if not url:
            paths.append(None)
            continue
        p = os.path.join(tdir, f"{i + 1}.jpg")
        if not os.path.exists(p):
            try:
                rr = requests.get(url, timeout=30)
                rr.raise_for_status()
                with open(p, "wb") as f:
                    f.write(rr.content)
            except Exception:
                paths.append(None)
                continue
        paths.append(p)
    return paths


_VLM_SYS = """You compare 3D-model images. Image 1 is OUR render of an asset in a plain viewer.
The remaining images are numbered Sketchfab candidates (candidate 1 is image 2, and so on).
Answer which candidate, if any, is the EXACT SAME 3D model as image 1 — identical geometry and
textures. Ignore lighting, camera angle, background, and render style. The same object category
or a similar-looking model is NOT a match; when unsure, say no match.
match: the candidate number (0 for no match). confidence: 0..1 that your answer is right."""


def _make_vlm():
    from sceneprogllm import LLM
    return LLM(system_desc=_VLM_SYS, response_format="json",
               response_params={"match": "int", "confidence": "float", "why": "str"})


def _provenance_from(result):
    uid = result.get("uid", "")
    return {
        "source": "sketchfab",
        "uid": uid,
        "url": f"https://sketchfab.com/3d-models/{uid}",
        "license": (result.get("license") or {}).get("label", ""),
        "author": (result.get("user") or {}).get("username", ""),
        "name": result.get("name", ""),
    }


def _write_help(state, meta):
    lines = [
        "# Attribution HELP — assets that need a human",
        "",
        "Reverse-search could not settle these bundled assets. For each: open the preview,",
        "identify the source (Sketchfab search, your download history, the original zip), then",
        "add a `provenance` block to `IDSDL/datasets/custom/custom.json` and rerun",
        "`python -c \"from IDSDL.ingest import write_attributions; write_attributions()\"`.",
        "",
    ]
    restricted = {m: s for m, s in state.items() if s["status"] == "restricted"}
    unmatched = {m: s for m, s in state.items() if s["status"] in ("nomatch", "error")}
    if restricted:
        lines += ["## Matched, but the license forbids redistribution", "",
                  "These WERE identified — under Sketchfab licenses that don't allow bundling.",
                  "Options per asset: remove it from the library, or re-source a licensed copy.", ""]
        for mid, s in sorted(restricted.items()):
            p = s.get("provenance", {})
            lines.append(f"- `{mid}` -> **{p.get('name')}** by {p.get('author')} "
                         f"({p.get('license')}) {p.get('url')}")
        lines.append("")
    if unmatched:
        lines += ["## No confident match", ""]
        for mid, s in sorted(unmatched.items()):
            sha = mid.split("/", 1)[-1]
            desc = (meta.get(mid) or {}).get("description", "")[:80]
            lines.append(f"- `{mid}` — {desc}")
            lines.append(f"  preview: IDSDL/datasets/custom/images/{sha}.png")
            if s.get("best_guess"):
                lines.append(f"  closest search hit (NOT confirmed): {s['best_guess']}")
        lines.append("")
    os.makedirs(WORK_DIR, exist_ok=True)
    with open(HELP_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"[attr] HELP board: {HELP_PATH} — {len(restricted)} restricted, {len(unmatched)} unmatched")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="attribution_recover")
    ap.add_argument("--limit", type=int, default=0, help="process at most N orphans (0 = all)")
    ap.add_argument("--min-conf", type=float, default=0.75)
    ap.add_argument("--retry-errors", action="store_true",
                    help="re-attempt assets whose last run errored")
    ap.add_argument("--workers", type=int, default=4,
                    help="parallel per-asset workers (default 4; same pattern as ingest)")
    args = ap.parse_args(argv)

    with open(CUSTOM_JSON) as f:
        meta = json.load(f)
    state = _load_state()
    orphans = [m for m, e in meta.items() if not e.get("provenance")]
    todo = [m for m in orphans
            if m not in state or (args.retry_errors and state[m]["status"] == "error")]
    if args.limit:
        todo = todo[:args.limit]
    print(f"[attr] {len(orphans)} orphans; {len(todo)} to process this run")

    vlm = _make_vlm()
    query_llm = _make_query_llm()

    def _process(mid):
        """Everything for one asset; returns (result_dict, log_line). Never raises."""
        entry = meta[mid]
        sha = mid.split("/", 1)[-1]
        preview = os.path.join(IMAGES_DIR, sha + ".png")
        label = entry.get("description", "")[:56]
        try:
            if not os.path.exists(preview):
                return {"status": "error", "why": "no preview render on disk"}, f"ERROR  {label}: no preview"
            results, seen = [], set()
            for q in _queries_for(entry, query_llm):
                for r in _search(q):
                    if r.get("uid") not in seen:
                        seen.add(r.get("uid"))
                        results.append(r)
                time.sleep(0.4)  # stay polite to the public API
                if len(results) >= N_CANDIDATES:
                    break
            results = results[:N_CANDIDATES]
            if not results:
                return {"status": "nomatch", "why": "search returned nothing"}, f"no match  {label} (no search hits)"
            thumbs = _fetch_thumbs(mid, results)
            usable = [(i, r, t) for (i, r), t in zip(enumerate(results), thumbs) if t]
            if not usable:
                return {"status": "nomatch", "why": "no thumbnails"}, f"no match  {label} (no thumbnails)"
            verdict = vlm("Which candidate matches image 1?",
                          image_paths=[preview] + [t for _, _, t in usable])
            verdict = verdict if isinstance(verdict, dict) else getattr(verdict, "__dict__", {})
            match, conf = int(verdict.get("match") or 0), float(verdict.get("confidence") or 0.0)
            best = _provenance_from(usable[0][1])
            if match > 0 and match <= len(usable) and conf >= args.min_conf:
                prov = _provenance_from(usable[match - 1][1])
                if _REDISTRIBUTABLE.match(prov["license"] or ""):
                    return ({"status": "matched", "provenance": prov,
                             "confidence": conf, "why": verdict.get("why", "")},
                            f"MATCH  {label} -> {prov['name']} by {prov['author']} "
                            f"({prov['license']}, {conf:.2f})")
                return ({"status": "restricted", "provenance": prov,
                         "confidence": conf, "why": verdict.get("why", "")},
                        f"RESTRICTED  {label} -> {prov['name']} ({prov['license']})")
            return ({"status": "nomatch", "confidence": conf,
                     "best_guess": f"{best['name']} by {best['author']} {best['url']}"},
                    f"no match  {label} (conf {conf:.2f})")
        except Exception as e:
            return {"status": "error", "why": str(e)[:200]}, f"ERROR  {label}: {e}"

    lock = threading.Lock()
    done = [0]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_process, mid): mid for mid in todo}
        for fut in as_completed(futs):
            mid = futs[fut]
            result, line = fut.result()
            with lock:
                state[mid] = result
                done[0] += 1
                print(f"  [{done[0]}/{len(todo)}] {line}", flush=True)
                _save_state(state)  # resumable after every asset

    # Write confirmed provenance back into the library, then regenerate the public record.
    n_written = 0
    for mid, s in state.items():
        if s["status"] == "matched" and mid in meta and not meta[mid].get("provenance"):
            meta[mid]["provenance"] = s["provenance"]
            n_written += 1
    if n_written:
        with open(CUSTOM_JSON, "w") as f:
            json.dump(meta, f, indent=1)
    print(f"[attr] wrote provenance for {n_written} asset(s) into custom.json")

    from IDSDL.ingest import write_attributions
    write_attributions()
    _write_help(state, meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
