"""Build a self-contained vanity TYPE-TAGGER HTML.

For each vanity in a pool, shows its preview + four type buttons
(floating / single / double / extra_wide) and an optional width(m) box.
"Download vanity_types.json" serializes {model_id: {type, width_m?}} for every tagged asset.

Reuses the retriever's `_preview_path` so hssd/future/custom previews resolve identically to the
gallery. Usage:  python tools/build_vanity_tagger.py [pool_name|json_path] [out.html]
"""
import base64, io, json, os, sys
from PIL import Image, ImageEnhance
from IDSDL.datasets import retrievers

POOL = sys.argv[1] if len(sys.argv) > 1 else "bathroom_vanity_unit"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "/work/tmp/vanity_tagger.html"

assets_dir = os.path.join(os.path.dirname(retrievers.__file__), "assets")
r = retrievers.FUTURE_HSSD_ASSET_RETRIEVERS[0]
path = POOL if os.path.exists(POOL) else os.path.join(assets_dir, POOL + ".json")
ids = json.load(open(path))

cards = []
for m in ids:
    prev = r._preview_path(m)
    b64 = ""
    if prev and os.path.exists(prev):
        im = Image.open(prev).convert("RGB")
        im = ImageEnhance.Brightness(im).enhance(1.4)
        im.thumbnail((220, 220))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=72)
        b64 = base64.b64encode(buf.getvalue()).decode()
    cards.append({"model": m,
                  "desc": (r.metadata.get(m, {}).get("description", "") or "")[:90],
                  "img": b64})

cards_json = json.dumps(cards).replace("</", "<\\/")

HTML = r"""<!doctype html><html><head><meta charset=utf-8><title>vanity tagger</title>
<style>
 body{margin:0;background:#111;color:#ddd;font-family:system-ui,sans-serif}
 #bar{position:sticky;top:0;background:#1c1c1cee;padding:10px 14px;border-bottom:1px solid #333;z-index:9;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
 #grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;padding:12px}
 .card{border:1px solid #333;border-radius:6px;padding:8px;background:#1e1e1e}
 .card img{width:100%;height:200px;object-fit:contain;background:#000;border-radius:4px}
 .desc{font-size:11px;color:#9aa;margin:4px 0;height:28px;overflow:hidden}
 .mono{font-family:monospace;font-size:10px;color:#789;word-break:break-all}
 .btns{display:flex;gap:4px;flex-wrap:wrap;margin-top:5px}
 .btns button{flex:1 1 46%;padding:5px 4px;font-size:11px;background:#333;color:#ccc;border:1px solid #555;border-radius:4px;cursor:pointer}
 .btns button.on{color:#111;font-weight:700}
 button[data-t=floating].on{background:#5ab0ff}button[data-t=single].on{background:#9aa0a8}
 button[data-t=double].on{background:#7dd17d}button[data-t=extra_wide].on{background:#ffb057}
 .w{width:64px;margin-top:5px;background:#333;color:#eee;border:1px solid #555;border-radius:3px;padding:3px}
 #dl{background:#0a64c0;color:#fff;border:0;padding:8px 14px;border-radius:5px;cursor:pointer;font-weight:700}
 #count{font-size:13px;color:#7a7}
 .filt button{padding:4px 8px;background:#2a2a2a;border:1px solid #555;color:#ccc;border-radius:4px;cursor:pointer;font-size:11px}
</style></head><body>
<div id=bar>
 <b>Vanity type tagger</b>
 <span class=mono>floating · single · double · extra_wide&nbsp; (+ optional width m)</span>
 <span class=filt>show: <button onclick="filt('')">all</button> <button onclick="filt('untagged')">untagged</button></span>
 <span id=count></span>
 <button id=dl onclick=dl()>Download vanity_types.json</button>
</div>
<div id=grid></div>
<script>
const CARDS=__CARDS__;
const tags={};
const TYPES=['floating','single','double','extra_wide'];
const grid=document.getElementById('grid');
function render(filter){
 grid.innerHTML='';
 for(const c of CARDS){
  if(filter==='untagged' && tags[c.model] && tags[c.model].type) continue;
  const t=tags[c.model]||{};
  const d=document.createElement('div');d.className='card';
  d.innerHTML=`<img src="data:image/jpeg;base64,${c.img}">
   <div class=desc>${c.desc}</div><div class=mono>${c.model}</div>
   <div class=btns>${TYPES.map(x=>`<button data-t="${x}" class="${t.type===x?'on':''}">${x}</button>`).join('')}</div>
   <input class=w type=number step=0.05 placeholder="w m" value="${t.width_m??''}">`;
  d.querySelectorAll('.btns button').forEach(b=>b.onclick=()=>{
    tags[c.model]=tags[c.model]||{}; tags[c.model].type=b.dataset.t;
    d.querySelectorAll('.btns button').forEach(x=>x.classList.toggle('on',x.dataset.t===b.dataset.t));
    upd();});
  d.querySelector('.w').onchange=e=>{tags[c.model]=tags[c.model]||{};
    const v=parseFloat(e.target.value); if(isNaN(v))delete tags[c.model].width_m; else tags[c.model].width_m=v; upd();};
  grid.appendChild(d);
 }
}
function upd(){document.getElementById('count').textContent=
  Object.values(tags).filter(t=>t.type).length+' / '+CARDS.length+' tagged';}
function filt(f){render(f);}
function dl(){
 const out={};for(const m in tags){if(tags[m].type)out[m]=tags[m];}
 const blob=new Blob([JSON.stringify(out,null,1)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='vanity_types.json';a.click();}
render('');upd();
</script></body></html>"""

open(OUT, "w").write(HTML.replace("__CARDS__", cards_json))
print("wrote", OUT, f"({len(cards)} vanities, {os.path.getsize(OUT)/1e6:.1f} MB)")
