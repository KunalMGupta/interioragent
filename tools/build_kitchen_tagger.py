"""Build a self-contained kitchen-set COMPONENT-TAGGER HTML.

For each kitchen unit in the pool, shows its preview + multi-select component chips (what the set
already bundles), a single-select layout shape, and an optional real-world width(m). The point: a
complete fitted kitchen set bundles cabinets/cooktop/hood/sink/etc as ONE mesh, so labelling what's
inside tells the scene builder what's left to ADD (island, stools, fridge, dining nook...).

"Download kitchen_components.json" serializes, for every tagged unit:
    { model_id: {"components": [...], "shape": "straight|L|U|island", "width_m"?: float} }

Reuses the retriever's `_preview_path` so hssd/future/custom previews resolve identically to the
gallery. Usage:  python tools/build_kitchen_tagger.py [pool_name|json_path] [out.html]
"""
import base64, io, json, os, sys
from PIL import Image, ImageEnhance

# Self-contained: resolve previews + descriptions straight off disk (no retrievers/trimesh import,
# so this runs anywhere the dataset is mounted). Mirrors retrievers._preview_path id->png routing.
_DS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "IDSDL", "datasets")
_IMG = {"hssd":   os.path.join(_DS, "futurehssd", "HSSD-images"),
        "future": os.path.join(_DS, "futurehssd", "3D-FUTURE-images"),
        "custom": os.path.join(_DS, "custom", "images")}

def _preview_path(model):
    if "/" not in model:
        return None
    kind, mid = model.split("/", 1)
    p = os.path.join(_IMG.get(kind, ""), mid + ".png")
    return p if kind in _IMG and os.path.exists(p) else None

POOL = sys.argv[1] if len(sys.argv) > 1 else "kitchen_set"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "/work/tmp/kitchen_tagger.html"

# The components a fitted kitchen SET can bundle (multi-select). "Cabinets" is implicit on every
# set, so we tag the things that vary / that you'd otherwise have to add separately.
COMPONENTS = ["base_cabinets", "wall_cabinets", "countertop", "cooktop", "oven",
              "range_hood", "sink", "fridge", "island", "microwave", "dishwasher"]
SHAPES = ["straight", "L", "U", "island"]

assets_dir = os.path.join(_DS, "assets")
path = POOL if os.path.exists(POOL) else os.path.join(assets_dir, POOL + ".json")
ids = json.load(open(path))
metadata = json.load(open(os.path.join(assets_dir, "futurehssd.json")))

cards = []
for m in ids:
    prev = _preview_path(m)
    b64 = ""
    if prev:
        im = Image.open(prev).convert("RGB")
        im = ImageEnhance.Brightness(im).enhance(1.4)
        im.thumbnail((260, 260))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=74)
        b64 = base64.b64encode(buf.getvalue()).decode()
    cards.append({"model": m,
                  "desc": (metadata.get(m, {}).get("description", "") or "")[:100],
                  "img": b64})

payload = json.dumps({"cards": cards, "components": COMPONENTS, "shapes": SHAPES}).replace("</", "<\\/")

HTML = r"""<!doctype html><html><head><meta charset=utf-8><title>kitchen component tagger</title>
<style>
 body{margin:0;background:#111;color:#ddd;font-family:system-ui,sans-serif}
 #bar{position:sticky;top:0;background:#1c1c1cee;padding:10px 14px;border-bottom:1px solid #333;z-index:9;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
 #grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;padding:12px}
 .card{border:1px solid #333;border-radius:6px;padding:9px;background:#1e1e1e}
 .card img{width:100%;height:230px;object-fit:contain;background:#000;border-radius:4px}
 .desc{font-size:11px;color:#9aa;margin:4px 0;height:28px;overflow:hidden}
 .mono{font-family:monospace;font-size:10px;color:#789;word-break:break-all}
 .lbl{font-size:10px;color:#778;margin:6px 0 2px;text-transform:uppercase;letter-spacing:.04em}
 .chips{display:flex;gap:4px;flex-wrap:wrap}
 .chips button{padding:4px 7px;font-size:11px;background:#2c2c2c;color:#bbb;border:1px solid #555;border-radius:12px;cursor:pointer}
 .chips button.on{background:#7dd17d;color:#111;font-weight:700;border-color:#7dd17d}
 .shape button.on{background:#5ab0ff;color:#111;font-weight:700;border-color:#5ab0ff}
 .w{width:70px;margin-left:6px;background:#333;color:#eee;border:1px solid #555;border-radius:3px;padding:3px}
 #dl{background:#0a64c0;color:#fff;border:0;padding:8px 14px;border-radius:5px;cursor:pointer;font-weight:700}
 #count{font-size:13px;color:#7a7}
 .filt button{padding:4px 8px;background:#2a2a2a;border:1px solid #555;color:#ccc;border-radius:4px;cursor:pointer;font-size:11px}
</style></head><body>
<div id=bar>
 <b>Kitchen component tagger</b>
 <span class=mono>toggle every component the SET already bundles &middot; pick its layout shape &middot; (optional width m)</span>
 <span class=filt>show: <button onclick="filt('')">all</button> <button onclick="filt('untagged')">untagged</button></span>
 <span id=count></span>
 <button id=dl onclick=dl()>Download kitchen_components.json</button>
</div>
<div id=grid></div>
<script>
const DATA=__PAYLOAD__;
const CARDS=DATA.cards, COMPONENTS=DATA.components, SHAPES=DATA.shapes;
const tags={};
const grid=document.getElementById('grid');
function st(m){tags[m]=tags[m]||{components:[],shape:null};return tags[m];}
function render(filter){
 grid.innerHTML='';
 for(const c of CARDS){
  const t=tags[c.model];
  if(filter==='untagged' && t && (t.components.length||t.shape)) continue;
  const s=st(c.model);
  const d=document.createElement('div');d.className='card';
  d.innerHTML=`<img src="data:image/jpeg;base64,${c.img}">
   <div class=desc>${c.desc}</div><div class=mono>${c.model}</div>
   <div class=lbl>bundled components</div>
   <div class="chips comp">${COMPONENTS.map(x=>`<button data-c="${x}" class="${s.components.includes(x)?'on':''}">${x}</button>`).join('')}</div>
   <div class=lbl>layout shape</div>
   <div class="chips shape">${SHAPES.map(x=>`<button data-s="${x}" class="${s.shape===x?'on':''}">${x}</button>`).join('')}
     <input class=w type=number step=0.05 placeholder="w m" value="${s.width_m??''}"></div>`;
  d.querySelectorAll('.comp button').forEach(b=>b.onclick=()=>{
    const a=st(c.model).components, x=b.dataset.c, i=a.indexOf(x);
    if(i<0)a.push(x);else a.splice(i,1);
    b.classList.toggle('on'); upd();});
  d.querySelectorAll('.shape button').forEach(b=>b.onclick=()=>{
    st(c.model).shape=b.dataset.s;
    d.querySelectorAll('.shape button').forEach(x=>x.classList.toggle('on',x.dataset.s===b.dataset.s));
    upd();});
  d.querySelector('.w').onchange=e=>{const v=parseFloat(e.target.value);
    if(isNaN(v))delete st(c.model).width_m;else st(c.model).width_m=v;upd();};
  grid.appendChild(d);
 }
}
function upd(){document.getElementById('count').textContent=
  Object.values(tags).filter(t=>t.components.length||t.shape).length+' / '+CARDS.length+' tagged';}
function filt(f){render(f);}
function dl(){
 const out={};
 for(const m in tags){const t=tags[m];
   if(!t.components.length && !t.shape) continue;
   out[m]={components:t.components};
   if(t.shape)out[m].shape=t.shape;
   if(t.width_m!=null)out[m].width_m=t.width_m;}
 const blob=new Blob([JSON.stringify(out,null,1)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='kitchen_components.json';a.click();}
render('');upd();
</script></body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(HTML.replace("__PAYLOAD__", payload))
print("wrote", OUT, f"({len(cards)} kitchen units, {os.path.getsize(OUT)/1e6:.1f} MB)")
