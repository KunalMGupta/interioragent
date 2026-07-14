"""Ingest a zip of .glb files into the asset library as first-class retrieval assets.

For each .glb it generates everything the retrieval pipeline reads — a stable id, a preview
render, metadata (description / placement / freetop / on_top_or_inside / scale), and an
embedding — and registers them so the asset is routed, ranked, previewed, picked, and
AddAsset-loaded exactly like any dataset asset (no other code changes; see the `custom`
branches in IDSDL/datasets/retrievers.py).

    python -m IDSDL.ingest <zip> [--category NAME] [--manifest manifest.json]

Contract: **supply the .glb files correctly scaled and oriented** (Y up, front facing +Z,
width along X, real-world metres) — the tool does not re-orient or re-unit meshes. A VLM then
captions + classifies the preview and gives the scale (real-world width, m). A manifest.json
(`{"<file.glb>": {"description":..., "scale":..., "placement":..., ...}}`) overrides any field
per file. Re-ingesting the same bytes is idempotent (sha1 id). Rendering/captioning run in
parallel (--workers). Outputs live in IDSDL/datasets/custom/{models,images}/ plus custom.json
(metadata) and custom.npz (embeddings).
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from IDSDL.datasets import retrievers as R

CUSTOM_DIR = R._CUSTOM_DIR
MODELS_DIR = os.path.join(CUSTOM_DIR, "models")
IMAGES_DIR = os.path.join(CUSTOM_DIR, "images")
META_PATH = R._CUSTOM_JSON
NPZ_PATH = R._CUSTOM_NPZ
EMB_DIM = 3072

_CAPTION_SYS = """
You are cataloguing a 3D asset for an interior-design asset library, given a preview render of
one object. Produce JSON with:
- description: one concise sentence naming the object with style, material, colour and type,
  e.g. "Large green classroom chalkboard with an aluminium frame."
- placement: "floor", "wall", "ceiling", or "NA" (a small object that sits on/in other furniture).
- freetop: true only if it has a flat usable TOP surface to place things on; else false.
- on_top_or_inside: true if it is typically placed ON TOP OF or INSIDE other furniture; else false.
- scale: the object's real-world WIDTH in metres.
Respond with only that JSON.
""".strip()


def _ensure_dirs():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(CUSTOM_DIR, exist_ok=True)


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_meta():
    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            return json.load(f)
    return {}


def _load_npz():
    if os.path.exists(NPZ_PATH):
        d = np.load(NPZ_PATH, allow_pickle=False)
        return list(d["all_models"]), list(d["all_embeddings"])
    return [], []


def _save(meta, models, embs):
    _ensure_dirs()
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=1)
    np.savez(NPZ_PATH,
             all_models=np.array(models, dtype=object).astype(str),
             all_embeddings=np.array(embs, dtype=np.float64).reshape(-1, EMB_DIM))


def _render_preview(scene, glb_path, out_png):
    """Render one head-on front (+Z) view of the glb via the Blender renderer; write it to out_png.
    Uses render_from_front (camera at ~half the object height, looking straight on) rather than
    the edge-midpoint views, whose camera sits at 3x the object height and looks steeply DOWN —
    that foreshortens flat wall objects (chalkboards, whiteboards, screens, maps) into thin
    strips the VLM then mis-captions ("slim shelf rail"). Assets are supplied correctly oriented
    (front = +Z), so a single head-on front view is the right preview. out_png is unique per
    asset (sha1), so concurrent renders never collide."""
    from IDSDL.renderer.renderer import SceneRenderer
    from PIL import Image
    obj = scene.add_asset(glb_path, 1.0, "ingest-preview")
    target = obj._build_blend()
    SceneRenderer(verbose=False).render_from_front(target, output_path=out_png)
    # The front camera sits back at ~3x the largest dimension, so the object lands small in a
    # big transparent frame; the VLM then guesses from a tiny silhouette. Tightly crop to the
    # rendered pixels (alpha bbox) and put them on white so the asset fills the preview.
    im = Image.open(out_png).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    pad = int(0.08 * max(im.size)) + 1
    canvas = Image.new("RGBA", (im.size[0] + 2 * pad, im.size[1] + 2 * pad), (255, 255, 255, 255))
    canvas.paste(im, (pad, pad), im)
    canvas.convert("RGB").save(out_png)
    return out_png


# Each worker thread gets its own render scene (shared scene state isn't thread-safe).
_tls = threading.local()


def _worker_scene():
    if not hasattr(_tls, "scene"):
        from IDSDL.scene import SceneProgRoom
        _tls.scene = SceneProgRoom(f"Ingest{threading.get_ident()}", seed=0)
    return _tls.scene


def _copy_centered(src, dst):
    """Copy a supplied .glb into the library VERBATIM — do NOT re-export through trimesh.

    Two round-trip hazards, both seen in practice, are why this is a byte copy:
      * `trimesh.load(src, force="mesh")` concatenates every primitive into one mesh and DROPS
        the materials of any multi-material asset — the stored glb comes out POSITION-only and
        renders as a flat WHITE object.
      * `trimesh.load(src).export(dst)` (a Scene round-trip, even keeping materials) EXPLODES a
        single authored multi-primitive glTF mesh into MANY separate meshes/nodes. The Blender
        loader in scene.py keeps only `imported_objs[0]`, so all but one primitive are dropped at
        the origin — the asset renders DISASSEMBLED (part placed, the rest stuck at 0,0,0).

    A verbatim copy keeps the authored single-mesh / multi-material structure, which Blender
    imports as ONE object carrying all material slots (textured AND whole). Centering on ingest is
    unnecessary: the loader re-centers every asset on import via
    `origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')`, and size queries (`get_whd`) are
    translation-invariant. The ingest contract already requires assets be supplied correctly
    oriented + metric, so no geometry processing is needed here."""
    shutil.copy(src, dst)


def _process_one(glb, fname, sha, vlm, encoder, manifest):
    """Full per-asset pipeline (render → caption → scale → embed). Pure w.r.t. shared state:
    returns a result tuple; the caller registers + saves under a lock. Runs in a worker."""
    mid = f"custom/{sha}"
    _copy_centered(glb, os.path.join(MODELS_DIR, sha + ".glb"))
    preview = os.path.join(IMAGES_DIR, sha + ".png")
    try:
        _render_preview(_worker_scene(), glb, preview)
    except Exception as e:
        return ("error", fname, f"preview render failed ({e})")
    try:
        cap = vlm("Catalogue this asset.", image_paths=[preview])
    except Exception as e:
        return ("error", fname, f"VLM caption failed ({e})")
    cap = cap if isinstance(cap, dict) else getattr(cap, "__dict__", {})

    entry = {
        "description": cap.get("description", fname),
        "placement": cap.get("placement", "floor"),
        "freetop": bool(cap.get("freetop", False)),
        "on_top_or_inside": bool(cap.get("on_top_or_inside", False)),
        "scale": float(cap.get("scale") or 1.0),   # VLM-given width (m); asset supplied correctly scaled
    }
    entry.update(manifest.get(fname, {}))   # manifest overrides win
    vec = np.array(encoder.embed_query(entry["description"]), dtype=np.float64)
    return ("ok", mid, fname, entry, vec)


def ingest_paths(glbs, category=None, manifest=None, manifest_path=None, workers=4):
    """Ingest an explicit list of .glb paths. The zip entry point is a thin wrapper over this, and
    IDSDL.shop calls it directly with the files it just normalized — a zip in between would only
    be a temp file neither side wants.

    `manifest` (a dict keyed by glb BASENAME) overrides any metadata field per file and wins over
    the VLM caption, which is how the shop pins the `scale` it measured in Blender rather than
    letting the captioner re-guess a width it already knows exactly."""
    from sceneprogllm import LLM

    _ensure_dirs()
    manifest = dict(manifest or {})
    if manifest_path and os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest.update(json.load(f))

    vlm = LLM(system_desc=_CAPTION_SYS, response_format="json",
              response_params={"description": "str", "placement": "str",
                               "freetop": "bool", "on_top_or_inside": "bool",
                               "scale": "float"})
    encoder = R.FUTURE_HSSD_ASSET_RETRIEVERS[0].encoder

    meta = _load_meta()
    models, embs = _load_npz()
    have = set(models)
    lock = threading.Lock()
    added = []

    todo = []
    for glb in glbs:
        fname, sha = os.path.basename(glb), _sha1(glb)
        if f"custom/{sha}" in have:
            print(f"  · {fname}: already ingested, skipping")
        else:
            # Claim the sha NOW, not just at registration: two inputs with identical bytes (the
            # same glb under two paths in a zip, or a duplicated file in a --from-dir) would
            # otherwise both pass this check and both register, putting the id and its embedding
            # into the npz TWICE — after which retrieval returns the same asset as two hits.
            have.add(f"custom/{sha}")
            todo.append((glb, fname, sha))
    print(f"[ingest] {len(glbs)} glb(s); processing {len(todo)} new with {workers} workers")

    def _register(mid, fname, entry, vec):
        # single-threaded section: append + SAVE INCREMENTALLY so a crash/kill keeps
        # everything done so far (idempotent re-runs then skip them).
        with lock:
            meta[mid] = entry
            models.append(mid)
            embs.append(vec)
            _save(meta, models, embs)
            added.append((mid, entry))
            print(f"  + {fname} -> {mid}\n      {entry['description'][:70]}\n"
                  f"      placement={entry['placement']} freetop={entry['freetop']} "
                  f"scale={entry['scale']:.2f}m")

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_process_one, glb, fname, sha, vlm, encoder, manifest)
                for glb, fname, sha in todo]
        for fut in as_completed(futs):
            res = fut.result()
            if res[0] == "ok":
                _register(res[1], res[2], res[3], res[4])
            else:
                print(f"  ! {res[1]}: {res[2]}")

    if added and category:
        _add_to_category(category, [mid for mid, _ in added])
    R._NPZ_CACHE.clear(); R._JSON_CACHE.clear()   # so a same-process reload sees new assets
    print(f"[ingest] added {len(added)} asset(s); library now has {len(models)} custom asset(s).")
    return added


def ingest_zip(zip_path, category=None, manifest_path=None, workers=4):
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp)
        glbs = sorted(p for p in _walk(tmp)
                      if p.lower().endswith(".glb")
                      and "__MACOSX" not in p
                      and not os.path.basename(p).startswith("._"))   # skip macOS junk
        return ingest_paths(glbs, category=category, manifest_path=manifest_path, workers=workers)


def _add_to_category(category, ids):
    path = os.path.join(os.path.dirname(R.__file__), "assets",
                        category if category.endswith(".json") else category + ".json")
    pool = []
    if os.path.exists(path):
        with open(path) as f:
            pool = json.load(f)
    pool = list(dict.fromkeys(pool + ids))   # dedupe, preserve order
    with open(path, "w") as f:
        json.dump(pool, f, indent=1)
    print(f"[ingest] added {len(ids)} id(s) to category pool {os.path.basename(path)}")


def _walk(root):
    for dp, _, fs in os.walk(root):
        for fn in fs:
            yield os.path.join(dp, fn)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ingest")
    ap.add_argument("zip", help="path to a .zip of .glb files")
    ap.add_argument("--category", default=None,
                    help="also append ingested ids to this category pool (e.g. presentation_fixtures)")
    ap.add_argument("--manifest", default=None,
                    help="json overriding metadata fields per glb filename")
    ap.add_argument("--workers", type=int, default=4,
                    help="parallel render/caption workers (default 4)")
    args = ap.parse_args(argv)
    if not os.path.exists(args.zip):
        print(f"[ingest] no such zip: {args.zip}", file=sys.stderr)
        return 1
    ingest_zip(args.zip, category=args.category, manifest_path=args.manifest, workers=args.workers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
