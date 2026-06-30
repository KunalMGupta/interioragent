"""Localhost asset browser — scroll through dataset assets to diagnose orientation,
record per-asset front-offset corrections, and annotate placement zones.

    PYTHONPATH=/work python asset_browser.py [--port 8000] [--host 127.0.0.1]

Open http://localhost:8000/ , type a query (e.g. "desk"), scroll the previews, and click
0 / 90 / 180 / 270 on any card to record that asset's front correction — it writes
front_offsets.json via IDSDL.front_cache, so every future scene using that mesh is fixed.
Text search is offline (substring on descriptions); tick "semantic" for embedding ranking.

Each card also links to a 3D annotator (http://localhost:8000/annotate?id=<model>) where you
draw placement-zone boxes (top surface / shelf levels / interior) on the asset; boxes are
saved per asset via IDSDL.placement_zones for the placement primitives to consume later.
Use the "pool" filter (e.g. shelfs_or_cabinets) plus "needs zones" to drive batch coverage.

No third-party server deps (stdlib http.server). The 3D viewer loads three.js from the
vendored copy under IDSDL/vendor/three (served at /vendor/), so the annotator works offline.
Reuses the shared retriever embeddings + the dataset preview PNGs + the model GLB paths, so
startup is a couple of seconds.
"""
import argparse
import html
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from IDSDL.datasets.retrievers import FUTURE_HSSD_ASSET_RETRIEVERS
from IDSDL import front_cache, placement_zones

R = FUTURE_HSSD_ASSET_RETRIEVERS[0]   # base FutureHSSD: embeddings + metadata + _preview_path

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "IDSDL", "datasets", "assets")
_VENDOR_DIR = os.path.join(os.path.dirname(__file__), "IDSDL", "vendor")
# model id -> row index into R.all_embeddings, for ranking within a pool subset.
_MODEL_INDEX = {m: i for i, m in enumerate(R.all_models.tolist())}


def _pool_path(name):
    """Resolve a pool filter name to a pool JSON path under the assets dir, or None."""
    if not name:
        return None
    name = os.path.basename(name)
    if not name.endswith(".json"):
        name += ".json"
    p = os.path.join(_ASSETS_DIR, name)
    return p if os.path.exists(p) else None


def _available_pools():
    try:
        return sorted(f[:-5] for f in os.listdir(_ASSETS_DIR) if f.endswith(".json"))
    except OSError:
        return []


def rank(query, n, semantic, pool_ids=None):
    """Return [(model, similarity_or_None), ...] for a query, optionally restricted to a pool."""
    if pool_ids is not None:
        universe = [m for m in pool_ids if m in _MODEL_INDEX]
    else:
        universe = R.all_models.tolist()

    if not query:
        return [(m, None) for m in universe[:n]]

    if semantic:
        embd = np.array(R.encoder.embed_query(query))
        idxs = np.array([_MODEL_INDEX[m] for m in universe])
        s = R.all_embeddings[idxs] @ embd
        order = np.argsort(s)[-n:][::-1]
        return [(universe[i], float(s[i])) for i in order]

    ql = query.lower()
    out = []
    for m in universe:
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
 input[type=text]{{width:300px;padding:6px 8px;background:#333;color:#eee;border:1px solid #555;border-radius:4px}}
 input.pool{{width:180px}}
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
 .zone{{margin-top:6px;display:flex;align-items:center;gap:8px}}
 .zone a{{color:#fff;background:#2d6a2d;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px}}
 .badge{{font-size:11px;padding:2px 6px;border-radius:3px}}
 .badge.has{{background:#2d6a2d;color:#dfd}}
 .badge.no{{background:#444;color:#aaa}}
 label{{font-size:13px}}
</style></head><body>
<header>
 <form method="get" action="/" style="display:inline">
  <input type="text" name="q" value="{q}" placeholder="search assets, e.g. desk" autofocus>
  <input type="text" class="pool" name="pool" value="{pool}" placeholder="pool (optional)" list="pools">
  <datalist id="pools">{pool_opts}</datalist>
  <label style="margin:0 6px"><input type="checkbox" name="sem" {sem_checked}> semantic</label>
  <label style="margin:0 6px"><input type="checkbox" name="needs" {needs_checked}> needs zones</label>
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
 <div class="zone"><a href="/annotate?id={qid}" target="_blank">annotate</a>
   <span class="badge {zcls}">{zlabel}</span></div>
</div>"""


def render_page(q, n, semantic, pool, needs_only):
    pool_ids = None
    pp = _pool_path(pool)
    if pp:
        pool_ids = placement_zones._pool_ids(pp)
    results = rank(q, n, semantic, pool_ids)

    zone_cache = placement_zones._load()
    cards = []
    for m, sim in results:
        aid = front_cache.asset_id(m)
        nzones = len(zone_cache.get(aid, {}).get("zones", []))
        if needs_only and nzones:
            continue
        off = float(front_cache._load().get(aid, 0.0))
        btns = "".join(
            f'<button class="{"cur" if off==d else ""}" data-deg="{d}" '
            f'onclick="setOff(\'{m}\',{d},this)">{d}</button>'
            for d in (0, 90, 180, 270)
        )
        simtxt = f' · <span style="color:#7a7">{sim:.3f}</span>' if sim is not None else ""
        zcls, zlabel = ("has", f"✓ {nzones} zone(s)") if nzones else ("no", "needs zones")
        cards.append(CARD.format(qid=urllib.parse.quote(m), model=html.escape(m),
                                 desc=html.escape(_desc(m)[:90]), sim=simtxt,
                                 off=f"{off:g}", btns=btns, zcls=zcls, zlabel=zlabel))
    pool_opts = "".join(f'<option value="{html.escape(p)}">' for p in _available_pools())
    return PAGE.format(q=html.escape(q), n=n, pool=html.escape(pool or ""),
                       pool_opts=pool_opts, sem_checked="checked" if semantic else "",
                       needs_checked="checked" if needs_only else "",
                       count=len(cards), cards="".join(cards))


# --- 3D placement-zone annotator -------------------------------------------------------
# Boxes are saved in raw GLB mesh-local coordinates (the same frame as the trimesh
# force="mesh" baked vertices): the GLB is added to the scene at identity, so a box's
# world AABB (Box3.setFromObject) equals its coordinates in that frame. Boxes are never
# rotated, keeping them axis-aligned so min/max are exact.
ANNOTATE_PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>annotate %%MODEL%%</title>
<style>
 html,body{margin:0;height:100%;font-family:system-ui,sans-serif;background:#111;color:#ddd;overflow:hidden}
 #view{position:absolute;inset:0}
 #side{position:absolute;top:0;right:0;width:300px;height:100%;background:#1e1e1ecc;
   border-left:1px solid #333;padding:12px;box-sizing:border-box;overflow:auto}
 h3{margin:4px 0 8px;font-size:14px}
 .mono{font-family:monospace;font-size:11px;color:#9cc;word-break:break-all}
 button{padding:5px 9px;margin:2px 0;background:#3a3a3a;color:#ddd;border:1px solid #555;
   border-radius:4px;cursor:pointer;font-size:12px}
 button.save{background:#0a64c0;color:#fff;border:0}
 button.add{background:#2d6a2d;color:#fff;border:0}
 .row{border:1px solid #3a3a3a;border-radius:4px;padding:6px;margin:6px 0;background:#2a2a2b}
 .row.sel{border-color:#ffae57}
 .row input[type=text]{width:120px;background:#333;color:#eee;border:1px solid #555;border-radius:3px;padding:2px 4px}
 .row input[type=number]{width:46px;background:#333;color:#eee;border:1px solid #555;border-radius:3px;padding:2px 4px}
 .tag{font-size:10px;padding:1px 5px;border-radius:3px;margin-left:4px}
 .tag.surface{background:#2d6a2d}.tag.shelf{background:#24507e}.tag.interior{background:#8a5a1e}
 .hint{font-size:11px;color:#888;margin:8px 0}
 #status{font-size:12px;color:#7a7;min-height:16px}
</style>
<script type="importmap">{"imports":{
 "three":"/vendor/three/three.module.js",
 "three/addons/":"/vendor/three/addons/"}}
</script></head><body>
<div id="view"></div>
<div id="side">
 <h3>placement zones</h3>
 <div class="mono">%%MODEL%%</div>
 <div class="hint">Drag the gizmo to move a box; press <b>S</b> to scale, <b>T</b> to move.
   Boxes stay axis-aligned. Green=surface, blue=shelf, orange=interior.</div>
 <button class="add" onclick="addBox('surface')">+ surface</button>
 <button class="add" onclick="addBox('shelf')">+ shelf</button>
 <button class="add" onclick="addBox('interior')">+ interior</button>
 <div id="list"></div>
 <button class="save" onclick="save()">save zones</button>
 <div id="status"></div>
</div>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {TransformControls} from 'three/addons/controls/TransformControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const MODEL = "%%MODEL%%";
const KIND_COLOR = {surface:0x39c439, shelf:0x4a90e2, interior:0xe0902a};
const view = document.getElementById('view');
const status = document.getElementById('status');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111111);
const camera = new THREE.PerspectiveCamera(50, view.clientWidth/view.clientHeight, 0.01, 1000);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(view.clientWidth, view.clientHeight);
view.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xffffff, 0.8));
const dir = new THREE.DirectionalLight(0xffffff, 1.0); dir.position.set(1,2,1); scene.add(dir);
const grid = new THREE.GridHelper(4, 16, 0x444444, 0x282828); scene.add(grid);
scene.add(new THREE.AxesHelper(0.5));

const orbit = new OrbitControls(camera, renderer.domElement);
const tcontrols = new TransformControls(camera, renderer.domElement);
tcontrols.setMode('translate');
tcontrols.addEventListener('dragging-changed', e => orbit.enabled = !e.value);
scene.add(tcontrols);

let modelBox = new THREE.Box3(new THREE.Vector3(-0.5,0,-0.5), new THREE.Vector3(0.5,1,0.5));
let boxes = [];          // {kind,name,level,mesh}
let selected = null;
let counters = {surface:0, shelf:0, interior:0};

const loader = new GLTFLoader();
loader.load('/glb?id='+encodeURIComponent(MODEL), gltf => {
  scene.add(gltf.scene);                       // identity transform == raw mesh frame
  modelBox = new THREE.Box3().setFromObject(gltf.scene);
  const c = modelBox.getCenter(new THREE.Vector3());
  const sz = modelBox.getSize(new THREE.Vector3());
  const r = Math.max(sz.x, sz.y, sz.z) || 1;
  camera.position.set(c.x + r*1.4, c.y + r*1.0, c.z + r*1.6);
  orbit.target.copy(c); orbit.update();
  grid.position.y = modelBox.min.y;
  loadExisting();
}, undefined, err => { status.textContent = 'failed to load GLB: '+err; });

function defaultBox(kind){
  const c = modelBox.getCenter(new THREE.Vector3());
  const sz = modelBox.getSize(new THREE.Vector3());
  if(kind==='surface') return {center:[c.x, modelBox.max.y, c.z], size:[sz.x*0.9, sz.y*0.05, sz.z*0.9]};
  if(kind==='shelf')   return {center:[c.x, c.y, c.z],            size:[sz.x*0.85, sz.y*0.05, sz.z*0.8]};
  return {center:[c.x, c.y, c.z], size:[sz.x*0.8, sz.y*0.8, sz.z*0.8]};   // interior
}

function makeMesh(kind, center, size){
  const geo = new THREE.BoxGeometry(1,1,1);
  const mat = new THREE.MeshBasicMaterial({color:KIND_COLOR[kind], transparent:true,
    opacity:0.25, depthWrite:false});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(center[0], center[1], center[2]);
  mesh.scale.set(Math.max(size[0],1e-3), Math.max(size[1],1e-3), Math.max(size[2],1e-3));
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo),
    new THREE.LineBasicMaterial({color:KIND_COLOR[kind]}));
  mesh.add(edges);
  scene.add(mesh);
  return mesh;
}

function addBox(kind, name, level, center, size){
  const d = defaultBox(kind);
  center = center || d.center; size = size || d.size;
  const mesh = makeMesh(kind, center, size);
  const entry = {kind, name: name || (kind+'_'+(counters[kind]++)),
    level: (level==null? (kind==='shelf'?0:undefined): level), mesh};
  if(kind==='shelf' && level!=null) counters.shelf = Math.max(counters.shelf, level+1);
  boxes.push(entry); select(entry); renderList();
}

function select(entry){ selected = entry; tcontrols.attach(entry.mesh); renderList(); }
function remove(entry){
  if(selected===entry){ tcontrols.detach(); selected=null; }
  scene.remove(entry.mesh); boxes = boxes.filter(b=>b!==entry); renderList();
}

function renderList(){
  const el = document.getElementById('list');
  el.innerHTML = '';
  boxes.forEach((b, i) => {
    const row = document.createElement('div');
    row.className = 'row' + (b===selected?' sel':'');
    const lvl = b.kind==='shelf'
      ? ` level <input type="number" value="${b.level??0}" onchange="setLevel(${i}, this.value)">` : '';
    row.innerHTML = `<input type="text" value="${b.name}" onchange="setName(${i}, this.value)">
      <span class="tag ${b.kind}">${b.kind}</span>${lvl}<br>
      <button onclick="sel(${i})">select</button>
      <button onclick="del(${i})">delete</button>`;
    el.appendChild(row);
  });
}

window.addBox = addBox;
window.sel = i => select(boxes[i]);
window.del = i => remove(boxes[i]);
window.setName = (i,v) => { boxes[i].name = v; };
window.setLevel = (i,v) => { boxes[i].level = parseInt(v)||0; };

window.addEventListener('keydown', e => {
  if(e.target.tagName==='INPUT') return;
  if(e.key==='s'||e.key==='S') tcontrols.setMode('scale');
  if(e.key==='t'||e.key==='T') tcontrols.setMode('translate');
});

async function loadExisting(){
  try{
    const r = await fetch('/zones?id='+encodeURIComponent(MODEL));
    const zs = await r.json();
    zs.forEach(z => {
      const center = [(z.min[0]+z.max[0])/2, (z.min[1]+z.max[1])/2, (z.min[2]+z.max[2])/2];
      const size = [z.max[0]-z.min[0], z.max[1]-z.min[1], z.max[2]-z.min[2]];
      addBox(z.kind, z.name, z.level, center, size);
    });
    tcontrols.detach(); selected=null; renderList();
    if(zs.length) status.textContent = 'loaded '+zs.length+' existing zone(s)';
  }catch(e){ /* none yet */ }
}

async function save(){
  const zones = boxes.map(b => {
    const bb = new THREE.Box3().setFromObject(b.mesh);   // world AABB == raw mesh frame
    const z = {name: b.name, kind: b.kind,
      min:[bb.min.x, bb.min.y, bb.min.z], max:[bb.max.x, bb.max.y, bb.max.z]};
    if(b.kind==='shelf') z.level = b.level ?? 0;
    return z;
  });
  const r = await fetch('/zones', {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:MODEL, zones})});
  const j = await r.json();
  status.textContent = j.ok ? ('saved '+j.count+' zone(s)') : ('error: '+(j.error||'?'));
}
window.save = save;

window.addEventListener('resize', () => {
  camera.aspect = view.clientWidth/view.clientHeight; camera.updateProjectionMatrix();
  renderer.setSize(view.clientWidth, view.clientHeight);
});
(function loop(){ requestAnimationFrame(loop); orbit.update(); renderer.render(scene, camera); })();
</script></body></html>"""


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
            pool = (qs.get("pool", [""])[0]).strip()
            needs_only = "needs" in qs
            self._send(200, render_page(q, n, semantic, pool, needs_only))
        elif u.path == "/img":
            model = qs.get("id", [""])[0]
            path = R._preview_path(model)
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "image/png")
            else:
                self._send(404, b"no preview", "text/plain")
        elif u.path == "/glb":
            model = qs.get("id", [""])[0]
            try:
                path, _ = R.model_to_path_scale(model)
            except Exception:
                path = None
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "model/gltf-binary")
            else:
                self._send(404, b"no glb", "text/plain")
        elif u.path.startswith("/vendor/"):
            rel = urllib.parse.unquote(u.path[len("/vendor/"):])
            path = os.path.normpath(os.path.join(_VENDOR_DIR, rel))
            if not path.startswith(_VENDOR_DIR) or not os.path.isfile(path):
                self._send(404, b"not found", "text/plain")
                return
            ctype = "text/javascript" if path.endswith(".js") else "application/octet-stream"
            with open(path, "rb") as f:
                self._send(200, f.read(), ctype)
        elif u.path == "/annotate":
            model = qs.get("id", [""])[0]
            page = ANNOTATE_PAGE.replace("%%MODEL%%", html.escape(model))
            self._send(200, page)
        elif u.path == "/zones":
            model = qs.get("id", [""])[0]
            self._send(200, json.dumps(placement_zones.zones_for(model)),
                       "application/json")
        elif u.path == "/set":
            model = qs.get("id", [""])[0]
            deg = float(qs.get("deg", ["0"])[0])
            front_cache.set_offset(model, deg)
            off = float(front_cache._load().get(front_cache.asset_id(model), 0.0))
            self._send(200, json.dumps({"ok": True, "offset": off}),
                       "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/zones":
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            model = payload.get("id", "")
            saved = placement_zones.set_zones(model, payload.get("zones", []))
            self._send(200, json.dumps({"ok": True, "count": len(saved)}),
                       "application/json")
        except (ValueError, KeyError) as e:
            self._send(400, json.dumps({"ok": False, "error": str(e)}),
                       "application/json")


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
