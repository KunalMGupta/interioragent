"""
Batch scene generation + review — run many category scenes concurrently and get a
single self-contained HTML report you can open locally (the container has no port
forwarding, so the review is a downloadable HTML with images embedded as base64).

    python batchgen.py living_room meeting_room bedroom      # a subset (work ~5 at a time)
    python batchgen.py --all                                 # every scenes/*.py
    python batchgen.py --all --workers 3                     # concurrency (default 3)
    python batchgen.py --all --list                          # just list discovered scenes

Each scene is built in its own subprocess via `workbench.py run scenes/<name>.py`
(so retrieval + Blender are isolated per scene and a crash can't take down the batch).
Retrieval is network-bound and Blender is GPU-bound, so a few concurrent builds overlap
nicely. Results — status, retrieval picks, interior renders, and the discussion note —
are aggregated into `batch_review.html`.

This is the loop for working ~5 categories in parallel: run a subset, open the HTML,
note what works / what doesn't / asset gaps, edit the scene programs (and the notes in
skills/examples/logs/<name>.md), re-run. Re-runs hit the seeded retrieval cache so they're fast.
"""
import argparse
import base64
import glob
import html
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.abspath(__file__))
SCENES_DIR = os.path.join(ROOT, "scenes")
NOTES_DIR = os.path.join(ROOT, "skills", "examples", "logs")
PYTHON = sys.executable
RUN_DIR_RE = re.compile(r"run_dir\s*[:=]\s*(tmp/\S+)")


def discover():
    return sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(SCENES_DIR, "*.py"))
        if not os.path.basename(p).startswith("_")
    )


def build_one(name):
    """Run one scene program in a subprocess; return a result dict."""
    prog = os.path.join(SCENES_DIR, name + ".py")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [PYTHON, os.path.join(ROOT, "workbench.py"), "run", prog],
            cwd=ROOT, capture_output=True, text=True, timeout=2400,
            env={**os.environ, "PYTHONPATH": ROOT},
        )
        out = proc.stdout + "\n" + proc.stderr
        ok = proc.returncode == 0
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + "\n[batchgen] TIMEOUT"
        ok = False
    dt = time.time() - t0

    run_dir = None
    for m in RUN_DIR_RE.finditer(out):
        run_dir = m.group(1)
    report = None
    if run_dir:
        rp = os.path.join(ROOT, run_dir, "report.json")
        if os.path.isfile(rp):
            try:
                with open(rp) as f:
                    report = json.load(f)
            except Exception:
                pass
    # capture a short error tail when it failed
    err_tail = ""
    if not ok:
        lines = [l for l in out.splitlines() if l.strip()]
        err_tail = "\n".join(lines[-25:])
    return {"name": name, "ok": ok, "seconds": dt, "run_dir": run_dir,
            "report": report, "err_tail": err_tail}


def _camel_to_snake(name):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def collect_results():
    """Build results from existing tmp/*/report.json (latest run per scene) — no re-render.
    Lets you regenerate one combined review after batches have run."""
    known = set(discover())
    by_name = {}
    for rp in glob.glob(os.path.join(ROOT, "tmp", "*", "report.json")):
        try:
            with open(rp) as f:
                report = json.load(f)
        except Exception:
            continue
        run_dir = os.path.relpath(os.path.dirname(rp), ROOT)
        name = _camel_to_snake(report.get("scene", os.path.basename(os.path.dirname(rp))))
        if name not in known:   # skip probe/test scenes that aren't a scenes/<name>.py
            continue
        mtime = os.path.getmtime(rp)
        if name not in by_name or mtime > by_name[name][0]:
            by_name[name] = (mtime, {"name": name, "ok": True, "seconds": 0.0,
                                     "run_dir": run_dir, "report": report, "err_tail": ""})
    return [v[1] for v in by_name.values()]


def _img_b64(path, max_h=360, quality=72):
    """Downscaled JPEG data for embedding — keeps the combined HTML small enough to open
    (full-res PNGs would make a 52-scene report hundreds of MB)."""
    try:
        from PIL import Image
        import io
        im = Image.open(path).convert("RGB")
        if im.height > max_h:
            im = im.resize((int(im.width * max_h / im.height), max_h), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return None


def _scene_images(run_dir):
    """Pick the most informative interior renders for the review (walls + one corner)."""
    if not run_dir:
        return []
    base = os.path.join(ROOT, run_dir, "room_views")
    wanted = ["wall_front.png", "wall_back.png", "wall_left.png", "wall_right.png",
              "corner_0.png", "corner_2.png"]
    out = []
    for w in wanted:
        p = os.path.join(base, w)
        if os.path.isfile(p):
            out.append((w, p))
    return out


def _note_html(name):
    p = os.path.join(NOTES_DIR, name + ".md")
    if not os.path.isfile(p):
        return ""
    with open(p) as f:
        return "<pre class='note'>" + html.escape(f.read()) + "</pre>"


def _assets_html(report):
    if not report or "assets" not in report:
        return ""
    rows = []
    for a in report["assets"]:
        q = html.escape(str(a.get("query", "")))
        chosen = ""
        for c in a.get("candidates", []):
            if c.get("chosen"):
                chosen = html.escape(str(c.get("desc", c.get("model", ""))))
                break
        rows.append(f"<tr><td>{q}</td><td>{chosen}</td></tr>")
    if not rows:
        return ""
    return ("<table class='assets'><tr><th>query</th><th>picked</th></tr>"
            + "".join(rows) + "</table>")


def build_html(results, out_path):
    cards = []
    for r in sorted(results, key=lambda x: x["name"]):
        name = html.escape(r["name"])
        status = "OK" if r["ok"] else "FAIL"
        color = "#1a7f37" if r["ok"] else "#cf222e"
        imgs = ""
        for label, p in _scene_images(r["run_dir"]):
            b = _img_b64(p)
            if b:
                imgs += (f"<figure><img src='data:image/jpeg;base64,{b}'/>"
                         f"<figcaption>{html.escape(label)}</figcaption></figure>")
        body = imgs or "<p class='noimg'>(no interior renders found)</p>"
        if not r["ok"] and r["err_tail"]:
            body += "<pre class='err'>" + html.escape(r["err_tail"]) + "</pre>"
        cards.append(f"""
        <section class='card' id='{name}'>
          <h2>{name} <span style='color:{color}'>[{status}]</span>
              <small>{r['seconds']:.0f}s</small></h2>
          {_assets_html(r['report'])}
          <div class='imgs'>{body}</div>
          {_note_html(r['name'])}
        </section>""")

    n_ok = sum(1 for r in results if r["ok"])
    toc = " · ".join(
        f"<a href='#{html.escape(r['name'])}'>{html.escape(r['name'])}"
        f"{'' if r['ok'] else ' ✗'}</a>"
        for r in sorted(results, key=lambda x: x["name"])
    )
    doc = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>Scene batch review</title>
<style>
 body{{font:14px/1.5 system-ui,sans-serif;margin:24px;max-width:1200px}}
 .card{{border:1px solid #ddd;border-radius:10px;padding:16px;margin:18px 0}}
 h1 small,h2 small{{color:#888;font-weight:400}}
 .imgs{{display:flex;flex-wrap:wrap;gap:10px}}
 figure{{margin:0}} figure img{{height:200px;border:1px solid #ccc;border-radius:6px}}
 figcaption{{font-size:11px;color:#666;text-align:center}}
 table.assets{{border-collapse:collapse;font-size:12px;margin:6px 0}}
 table.assets td,table.assets th{{border:1px solid #e3e3e3;padding:2px 8px;text-align:left}}
 pre.err{{background:#fff5f5;color:#86181d;padding:8px;border-radius:6px;overflow:auto;font-size:11px}}
 pre.note{{background:#f6f8fa;padding:8px;border-radius:6px;white-space:pre-wrap;font-size:12px}}
 .noimg{{color:#999}} .toc{{line-height:2}}
</style></head><body>
<h1>Scene batch review <small>{n_ok}/{len(results)} ok · {time.strftime('%Y-%m-%d %H:%M')}</small></h1>
<p class='toc'>{toc}</p>
{''.join(cards)}
</body></html>"""
    with open(out_path, "w") as f:
        f.write(doc)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="batchgen")
    ap.add_argument("names", nargs="*", help="scene names (scenes/<name>.py); empty + --all = every scene")
    ap.add_argument("--all", action="store_true", help="run every scenes/*.py")
    ap.add_argument("--workers", type=int, default=3, help="concurrent scene builds (default 3)")
    ap.add_argument("--list", action="store_true", help="list discovered scenes and exit")
    ap.add_argument("--collect", action="store_true",
                    help="build one combined review from existing tmp/ renders (no re-run)")
    ap.add_argument("--out", default="batch_review.html", help="output HTML path")
    args = ap.parse_args(argv)

    available = discover()
    if args.list:
        print("\n".join(available))
        return 0

    if args.collect:
        results = collect_results()
        out = build_html(results, os.path.join(ROOT, args.out))
        print(f"[batchgen] collected {len(results)} scene(s) from tmp/ → {out}")
        return 0

    names = available if args.all else [n for n in args.names if n in available]
    missing = [n for n in args.names if n not in available]
    if missing:
        print(f"[batchgen] unknown scenes (skipped): {', '.join(missing)}", file=sys.stderr)
    if not names:
        print("[batchgen] nothing to run. Use --all or pass scene names; --list to see them.",
              file=sys.stderr)
        return 1

    print(f"[batchgen] building {len(names)} scene(s) with {args.workers} workers: {', '.join(names)}")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(build_one, n): n for n in names}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  {'✓' if r['ok'] else '✗'} {r['name']:<22} {r['seconds']:6.0f}s "
                  f"{r['run_dir'] or ''}")

    out = build_html(results, os.path.join(ROOT, args.out))
    n_ok = sum(1 for r in results if r["ok"])
    print(f"[batchgen] done: {n_ok}/{len(results)} ok → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
