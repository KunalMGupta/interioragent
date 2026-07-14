"""Build a fully self-contained placement-zone annotator HTML file.

three.js (core + OrbitControls + TransformControls + GLTFLoader) is inlined as base64
data-URL ES modules wired through an import map, so the result needs no server and no
internet — just open it in a browser, load a .glb from disk, draw boxes, download the
zones JSON, then merge it with:  python -m IDSDL.placement_zones import <file>.json

    python tools/build_annotator_html.py            # writes annotator.html
    python tools/build_annotator_html.py out.html
"""
import base64
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_VENDOR = os.path.join(_HERE, "..", "IDSDL", "vendor", "three")


def _data_url(path):
    raw = open(path, "rb").read()
    return "data:text/javascript;base64," + base64.b64encode(raw).decode("ascii")


def build():
    importmap = {"imports": {
        "three": _data_url(os.path.join(_VENDOR, "three.module.js")),
        "three/addons/controls/OrbitControls.js":
            _data_url(os.path.join(_VENDOR, "addons/controls/OrbitControls.js")),
        "three/addons/controls/TransformControls.js":
            _data_url(os.path.join(_VENDOR, "addons/controls/TransformControls.js")),
        "three/addons/loaders/GLTFLoader.js":
            _data_url(os.path.join(_VENDOR, "addons/loaders/GLTFLoader.js")),
    }}
    return HTML.replace("%%IMPORTMAP%%", json.dumps(importmap))


HTML = r"""<!doctype html><html><head><meta charset="utf-8">
<title>placement-zone annotator</title>
<style>
 html,body{margin:0;height:100%;font-family:system-ui,sans-serif;background:#111;color:#ddd;overflow:hidden}
 #view{position:absolute;inset:0}
 #side{position:absolute;top:0;right:0;width:320px;height:100%;background:#1e1e1eee;
   border-left:1px solid #333;padding:12px;box-sizing:border-box;overflow:auto}
 h3{margin:4px 0 8px;font-size:14px}
 .mono{font-family:monospace;font-size:11px;color:#9cc;word-break:break-all}
 button{padding:5px 9px;margin:2px 0;background:#3a3a3a;color:#ddd;border:1px solid #555;
   border-radius:4px;cursor:pointer;font-size:12px}
 button.save{background:#0a64c0;color:#fff;border:0}
 button.add{background:#2d6a2d;color:#fff;border:0}
 input[type=text]{background:#333;color:#eee;border:1px solid #555;border-radius:3px;padding:3px 5px}
 #assetId{width:220px}
 .row{border:1px solid #3a3a3a;border-radius:4px;padding:6px;margin:6px 0;background:#2a2a2b}
 .row.sel{border-color:#ffae57}
 .row input[type=text]{width:120px}
 .row input[type=number]{width:46px;background:#333;color:#eee;border:1px solid #555;border-radius:3px;padding:2px 4px}
 .tag{font-size:10px;padding:1px 5px;border-radius:3px;margin-left:4px}
 .tag.surface{background:#2d6a2d}.tag.shelf{background:#24507e}.tag.interior{background:#8a5a1e}
 .hint{font-size:11px;color:#888;margin:8px 0}
 #status{font-size:12px;color:#7a7;min-height:16px;margin-top:6px}
 hr{border:0;border-top:1px solid #333;margin:10px 0}
</style>
<script type="importmap">%%IMPORTMAP%%</script>
</head><body>
<div id="view"></div>
<div id="side">
 <h3>placement-zone annotator</h3>
 <div class="hint">Self-contained: no server, no internet. Load a dataset
   <b>.glb</b>, draw boxes, download the JSON, then run<br>
   <span class="mono">python -m IDSDL.placement_zones import file.json</span></div>
 <label>load .glb: <input type="file" id="glb" accept=".glb,.gltf"></label>
 <div style="margin:6px 0">asset id: <input type="text" id="assetId" placeholder="(from filename)"></div>
 <hr>
 <div class="hint">Drag the gizmo to move a box; press <b>S</b> to scale, <b>T</b> to move.
   Boxes stay axis-aligned. Green=surface, blue=shelf, orange=interior.</div>
 <button class="add" onclick="addBox('surface')">+ surface</button>
 <button class="add" onclick="addBox('shelf')">+ shelf</button>
 <button class="add" onclick="addBox('interior')">+ interior</button>
 <div id="list"></div>
 <hr>
 <button class="save" onclick="download_()">download zones JSON</button>
 <label style="font-size:12px">load JSON: <input type="file" id="loadzones" accept=".json"></label>
 <div id="status"></div>
</div>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {TransformControls} from 'three/addons/controls/TransformControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const KIND_COLOR = {surface:0x39c439, shelf:0x4a90e2, interior:0xe0902a};
const view = document.getElementById('view');
const status = document.getElementById('status');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111111);
const camera = new THREE.PerspectiveCamera(50, view.clientWidth/view.clientHeight, 0.001, 1000);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(view.clientWidth, view.clientHeight);
view.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xffffff, 0.85));
const dir = new THREE.DirectionalLight(0xffffff, 1.0); dir.position.set(1,2,1); scene.add(dir);
const grid = new THREE.GridHelper(4, 16, 0x444444, 0x282828); scene.add(grid);
scene.add(new THREE.AxesHelper(0.5));

const orbit = new OrbitControls(camera, renderer.domElement);
camera.position.set(1.4, 1.2, 1.8); orbit.update();
const tcontrols = new TransformControls(camera, renderer.domElement);
tcontrols.addEventListener('dragging-changed', e => orbit.enabled = !e.value);
scene.add(tcontrols);

let modelBox = new THREE.Box3(new THREE.Vector3(-0.5,0,-0.5), new THREE.Vector3(0.5,1,0.5));
let modelRoot = null;
let boxes = [];
let selected = null;
let counters = {surface:0, shelf:0, interior:0};
const loader = new GLTFLoader();

document.getElementById('glb').addEventListener('change', ev => {
  const file = ev.target.files[0];
  if(!file) return;
  const stem = file.name.replace(/\.(glb|gltf)$/i,'');
  const idEl = document.getElementById('assetId');
  if(!idEl.value) idEl.value = stem;
  file.arrayBuffer().then(buf => loader.parse(buf, '', gltf => {
    if(modelRoot) scene.remove(modelRoot);
    modelRoot = gltf.scene; scene.add(modelRoot);    // identity == raw mesh frame
    modelBox = new THREE.Box3().setFromObject(modelRoot);
    const c = modelBox.getCenter(new THREE.Vector3());
    const sz = modelBox.getSize(new THREE.Vector3());
    const r = Math.max(sz.x, sz.y, sz.z) || 1;
    camera.position.set(c.x + r*1.4, c.y + r*1.0, c.z + r*1.6);
    orbit.target.copy(c); orbit.update();
    grid.position.y = modelBox.min.y;
    status.textContent = 'loaded ' + file.name;
  }, err => status.textContent = 'GLB parse failed: ' + err));
});

function defaultBox(kind){
  const c = modelBox.getCenter(new THREE.Vector3());
  const sz = modelBox.getSize(new THREE.Vector3());
  if(kind==='surface') return {center:[c.x, modelBox.max.y, c.z], size:[sz.x*0.9, sz.y*0.05, sz.z*0.9]};
  if(kind==='shelf')   return {center:[c.x, c.y, c.z],            size:[sz.x*0.85, sz.y*0.05, sz.z*0.8]};
  return {center:[c.x, c.y, c.z], size:[sz.x*0.8, sz.y*0.8, sz.z*0.8]};
}
function makeMesh(kind, center, size){
  const geo = new THREE.BoxGeometry(1,1,1);
  const mat = new THREE.MeshBasicMaterial({color:KIND_COLOR[kind], transparent:true, opacity:0.25, depthWrite:false});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(center[0], center[1], center[2]);
  mesh.scale.set(Math.max(size[0],1e-3), Math.max(size[1],1e-3), Math.max(size[2],1e-3));
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({color:KIND_COLOR[kind]})));
  scene.add(mesh); return mesh;
}
function addBox(kind, name, level, center, size){
  const d = defaultBox(kind);
  const mesh = makeMesh(kind, center||d.center, size||d.size);
  const entry = {kind, name: name||(kind+'_'+(counters[kind]++)),
    level:(level==null?(kind==='shelf'?0:undefined):level), mesh};
  if(kind==='shelf' && level!=null) counters.shelf = Math.max(counters.shelf, level+1);
  boxes.push(entry); select(entry); renderList();
}
function select(entry){ selected=entry; tcontrols.attach(entry.mesh); renderList(); }
function remove(entry){ if(selected===entry){tcontrols.detach();selected=null;} scene.remove(entry.mesh); boxes=boxes.filter(b=>b!==entry); renderList(); }
function renderList(){
  const el = document.getElementById('list'); el.innerHTML='';
  boxes.forEach((b,i)=>{
    const row=document.createElement('div'); row.className='row'+(b===selected?' sel':'');
    const lvl=b.kind==='shelf'?` level <input type="number" value="${b.level??0}" onchange="setLevel(${i},this.value)">`:'';
    row.innerHTML=`<input type="text" value="${b.name}" onchange="setName(${i},this.value)">
      <span class="tag ${b.kind}">${b.kind}</span>${lvl}<br>
      <button onclick="sel(${i})">select</button> <button onclick="del(${i})">delete</button>`;
    el.appendChild(row);
  });
}
window.addBox=addBox; window.sel=i=>select(boxes[i]); window.del=i=>remove(boxes[i]);
window.setName=(i,v)=>{boxes[i].name=v;}; window.setLevel=(i,v)=>{boxes[i].level=parseInt(v)||0;};
window.addEventListener('keydown',e=>{ if(e.target.tagName==='INPUT')return;
  if(e.key==='s'||e.key==='S')tcontrols.setMode('scale'); if(e.key==='t'||e.key==='T')tcontrols.setMode('translate'); });

function zonesArray(){
  return boxes.map(b=>{
    const bb=new THREE.Box3().setFromObject(b.mesh);   // world AABB == raw mesh frame
    const z={name:b.name, kind:b.kind, min:[bb.min.x,bb.min.y,bb.min.z], max:[bb.max.x,bb.max.y,bb.max.z]};
    if(b.kind==='shelf') z.level=b.level??0; return z;
  });
}
function download_(){
  const id=document.getElementById('assetId').value.trim();
  if(!id){ status.textContent='set an asset id first'; return; }
  const obj={}; obj[id]={zones:zonesArray()};
  const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=id.replace(/[\/\\]/g,'_')+'.json'; a.click();
  status.textContent='downloaded '+a.download+' ('+boxes.length+' zone(s))';
}
window.download_=download_;

document.getElementById('loadzones').addEventListener('change', ev=>{
  const f=ev.target.files[0]; if(!f) return;
  f.text().then(t=>{
    const data=JSON.parse(t);
    const id=Object.keys(data)[0]; const zs=(data[id].zones||data[id]);
    document.getElementById('assetId').value=id;
    boxes.slice().forEach(remove);
    zs.forEach(z=>{ const center=[(z.min[0]+z.max[0])/2,(z.min[1]+z.max[1])/2,(z.min[2]+z.max[2])/2];
      const size=[z.max[0]-z.min[0],z.max[1]-z.min[1],z.max[2]-z.min[2]]; addBox(z.kind,z.name,z.level,center,size); });
    tcontrols.detach(); selected=null; renderList(); status.textContent='loaded '+zs.length+' zone(s) for '+id;
  });
});

window.addEventListener('resize',()=>{ camera.aspect=view.clientWidth/view.clientHeight; camera.updateProjectionMatrix();
  renderer.setSize(view.clientWidth, view.clientHeight); });
(function loop(){ requestAnimationFrame(loop); orbit.update(); renderer.render(scene,camera); })();
</script></body></html>"""


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.join(_HERE, "..", "annotator.html")
    html = build()
    with open(out, "w") as f:
        f.write(html)
    print(f"wrote {os.path.abspath(out)}  ({len(html)/1e6:.2f} MB)")


if __name__ == "__main__":
    main(sys.argv)
