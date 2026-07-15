---
id: workflow:asset_ingest
kind: workflow
role: "GLB ingest invariants (single mesh, real metres, front +Z)"
---

# Ingesting custom GLB assets — the single-mesh invariant (and how ingest breaks it)

> **Getting the `.glb`s in the first place?** `python -m IDSDL.ingest` is the *low* level: it
> assumes — and never checks — that you hand it files already single-mesh, real-metre, front=+Z.
> To go from a text query to an asset that satisfies all of that automatically (search Sketchfab
> or generate with Meshy → normalize in Blender → VLM triage → verify → ingest), use the asset
> shop: **[../acquire-assets/SKILL.md](../acquire-assets/SKILL.md)**, `python -m IDSDL.shop run
> "<query>"`. This page is what the shop is protecting you from — read it when something you
> ingested renders white, disassembled, or at the wrong size.

When you add your own `.glb`s to the library (`python -m IDSDL.ingest <zip>`), the stored mesh
must stay a **single glTF mesh**. Multiple *primitives* and *materials* inside that one mesh are
fine — that's how a textured asset with many parts is represented (Blender imports it as **one
object with many material slots**). What must NOT happen is the file ending up as **many meshes /
nodes**, because the Blender loader keeps only the first one.

## Why single-mesh matters — the loader keeps `imported_objs[0]`
Both the room loader (`IDSDL/scene.py`) and the per-object loader (`IDSDL/object.py`) do:
```python
bpy.ops.import_scene.gltf(filepath=...)
imported_objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
mesh_obj = imported_objs[0]          # <- only the FIRST mesh is used as the asset
```
The other imported meshes are **not deleted** — they're left at the file's origin and render there.
So a multi-mesh glb renders **DISASSEMBLED**: one piece lands at the placed position, the rest sit
stranded at `(0,0,0)`. This is a deliberate design: the whole `futurehssd` dataset (~29k assets) is
pre-processed to a single mesh, so `[0]` is always the whole asset. **Do not "fix" this in the
loader** — see the bottom of this file.

## `_copy_centered` must be a VERBATIM copy — never round-trip through trimesh
`IDSDL/ingest.py::_copy_centered` copies each supplied glb into the library. It must be a byte copy
(`shutil.copy`). Two trimesh round-trips were tried and BOTH corrupted assets:

| approach | what breaks | symptom |
|---|---|---|
| `trimesh.load(src, force="mesh")` | concatenates primitives, **drops materials** of any multi-material asset → POSITION-only | renders **flat WHITE** |
| `trimesh.load(src).export()` (Scene round-trip) | **explodes** one authored multi-primitive mesh into many meshes/nodes (e.g. 1 → 76) | renders **disassembled**, pieces at origin |

Centering at ingest is **unnecessary** anyway: the loader re-centers every asset on import via
`bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')`, and size queries (`get_whd`)
are translation-invariant. The ingest contract already requires assets be supplied correctly
oriented + metric, so no geometry processing is needed. Just copy the file.

## Diagnosing a bad-looking ingested asset (fast, no render)
A textured **preview PNG is not proof** — `ingest.py` renders the preview from the *source* file, so
a good thumbnail can hide a stripped/exploded stored mesh. Parse the stored glb's JSON chunk instead:
```python
import json, struct
d = open(path, "rb").read(); jlen = struct.unpack("<I", d[12:16])[0]; j = json.loads(d[20:20+jlen])
attrs = {a for m in j.get("meshes", []) for p in m.get("primitives", []) for a in p["attributes"]}
# meshes=len(j["meshes"]); materials/images; attrs has TEXCOORD_0?
```
- `materials==0` / `images==0` / attrs is `{POSITION}` only → **stripped** (renders white).
- `meshes` far greater than 1 (many nodes) → **exploded** (renders disassembled).
- A healthy single asset looks like: `meshes==1`, `materials>0`, `images>0`, `TEXCOORD_0` present.

To repair, re-copy the **original source** glb verbatim over `custom/models/<sha>.glb` (the id is the
sha1 of the *source*, so it's unchanged; captions/embeddings/previews stay valid).

## Do NOT change the loader to join meshes (evaluated + rejected)
The tempting "general fix" is to `bpy.ops.object.join` all imported meshes in `scene.py` instead of
taking `[0]`. **Rejected as not worth it:** it's a **no-op for 100% of the current library** (every
asset is already single-mesh, nothing to join), yet it sits on the per-asset-per-render path with
real crash surface (join preconditions: object mode, valid active object, selection; plus interaction
with the existing `transform_apply`/`origin_set`) and can't be cheaply regression-tested. The
single-mesh invariant's correct home is **ingest**, not the shared loader. If a genuinely multi-mesh
*source* ever matters, do a **material-preserving merge at ingest** (touches only that one asset).

See the worked example `../examples/jewelry_shop.md` (the OLIVIA jewelry counter was the asset that
surfaced all of this) and the asset-first kickoff in `asset_selection.md`.
