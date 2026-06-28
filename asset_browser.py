"""Localhost asset browser — scroll through dataset assets to diagnose orientation
and record per-asset front-offset corrections.

    PYTHONPATH=/work python asset_browser.py [--port 8000] [--host 127.0.0.1]

Open http://localhost:8000/ , type a query (e.g. "desk"), scroll the previews, and click
0 / 90 / 180 / 270 on any card to record that asset's front correction — it writes
front_offsets.json via IDSDL.front_cache, so every future scene using that mesh is fixed.
Text search is offline (substring on descriptions); tick "semantic" for embedding ranking.

No third-party deps (stdlib http.server). Reuses the shared retriever embeddings + the
dataset preview PNGs, so startup is a couple of seconds.
"""
import argparse
import html
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from IDSDL.datasets.retrievers import FUTURE_HSSD_ASSET_RETRIEVERS
from IDSDL import front_cache

R = FUTURE_HSSD_ASSET_RETRIEVERS[0]   # base FutureHSSD: embeddings + metadata + _preview_path


def rank(query, n, semantic):
    """Return [(model, similarity_or_None), ...] for a query."""
    if not query:
        return [(m, None) for m in R.all_models.tolist()[:n]]
    if semantic:
        embd = np.array(R.encoder.embed_query(query))
        s = np.dot(R.all_embeddings, embd)
        idx = np.argsort(s)[-n:][::-1]
        return [(R.all_models[i], float(s[i])) for i in idx]
    ql = query.lower()
    out = []
    for m in R.all_models.tolist():
        if ql in (R.metadata.get(m, {}).get("description", "").lower()):
            out.append((m, None))
            if len(out) >= n:
                break
    return out


def _desc(m):
    return R.metadata.get(m, {}).get("description", "") or ""


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>asset browser</title>
<style>
 body{{font-family:system-ui,sans-serif;margin:0;background:#1e1e1e;color:#ddd}}
 header{{position:sticky;top:0;background:#252526;padding:12px 16px;border-bottom:1px solid #333;z-index:10}}
 input[type=text]{{width:340px;padding:6px 8px;background:#333;color:#eee;border:1px solid #555;border-radius:4px}}
 button.go{{padding:6px 12px;background:#0a64c0;color:#fff;border:0;border-radius:4px;cursor:pointer}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;padding:16px}}
 .card{{background:#2a2a2b;border:1px solid #3a3a3a;border-radius:6px;padding:8px;font-size:12px}}
 .card img{{width:100%;background:#111;border-radius:4px;display:block;filter:brightness(1.4)}}
 .id{{font-family:monospace;font-size:11px;color:#9cc;word-break:break-all;margin:6px 0 2px;cursor:pointer}}
 .desc{{color:#bbb;min-height:30px}}
 .off{{margin-top:4px}}
 .off b{{color:#ffae57}}
 .btns button{{margin:2px 2px 0 0;padding:3px 7px;background:#3a3a3a;color:#ddd;border:1px solid #555;border-radius:3px;cursor:pointer}}
 .btns button.cur{{background:#ffae57;color:#222;border-color:#ffae57}}
 .count{{color:#888;margin-left:10px}}
</style></head><body>
<header>
 <form method="get" action="/" style="display:inline">
  <input type="text" name="q" value="{q}" placeholder="search assets, e.g. desk" autofocus>
  <label style="margin:0 6px"><input type="checkbox" name="sem" {sem_checked}> semantic</label>
  <input type="hidden" name="n" value="{n}">
  <button class="go" type="submit">browse</button>
  <span class="count">{count} assets</span>
 </form>
</header>
<div class="grid">{cards}</div>
<script>
 function copyId(t){{navigator.clipboard.writeText(t.dataset.id);t.textContent='copied!';setTimeout(()=>t.textContent=t.dataset.id,700);}}
 async function setOff(model, deg, el){{
   const r = await fetch('/set?id='+encodeURIComponent(model)+'&deg='+deg);
   const j = await r.json();
   const card = el.closest('.card');
   card.querySelector('.off b').textContent = j.offset+'°';
   card.querySelectorAll('.btns button').forEach(b=>b.classList.toggle('cur', parseFloat(b.dataset.deg)===j.offset));
 }}
</script>
</body></html>"""

CARD = """<div class="card">
 <img loading="lazy" src="/img?id={qid}" alt="no preview">
 <div class="id" data-id="{model}" onclick="copyId(this)">{model}</div>
 <div class="desc">{desc}{sim}</div>
 <div class="off">front offset: <b>{off}°</b></div>
 <div class="btns">{btns}</div>
</div>"""


def render_page(q, n, semantic):
    results = rank(q, n, semantic)
    cards = []
    for m, sim in results:
        aid = front_cache.asset_id(m)
        off = float(front_cache._load().get(aid, 0.0))
        btns = "".join(
            f'<button class="{"cur" if off==d else ""}" data-deg="{d}" '
            f'onclick="setOff(\'{m}\',{d},this)">{d}</button>'
            for d in (0, 90, 180, 270)
        )
        simtxt = f' · <span style="color:#7a7">{sim:.3f}</span>' if sim is not None else ""
        cards.append(CARD.format(qid=urllib.parse.quote(m), model=html.escape(m),
                                 desc=html.escape(_desc(m)[:90]), sim=simtxt,
                                 off=f"{off:g}", btns=btns))
    return PAGE.format(q=html.escape(q), n=n, sem_checked="checked" if semantic else "",
                       count=len(results), cards="".join(cards))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if u.path == "/":
            q = (qs.get("q", [""])[0]).strip()
            n = int(qs.get("n", ["60"])[0])
            semantic = "sem" in qs
            self._send(200, render_page(q, n, semantic))
        elif u.path == "/img":
            model = qs.get("id", [""])[0]
            path = R._preview_path(model)
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "image/png")
            else:
                self._send(404, b"no preview", "text/plain")
        elif u.path == "/set":
            model = qs.get("id", [""])[0]
            deg = float(qs.get("deg", ["0"])[0])
            front_cache.set_offset(model, deg)
            off = float(front_cache._load().get(front_cache.asset_id(model), 0.0))
            self._send(200, json.dumps({"ok": True, "offset": off}),
                       "application/json")
        else:
            self._send(404, b"not found", "text/plain")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"asset browser on http://{args.host}:{args.port}/  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
