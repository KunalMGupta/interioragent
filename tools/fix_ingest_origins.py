"""Make glbs INGEST-READY: one mesh object, origin at the bbox centre, verified.

Run under Blender:
    blender --background --python tools/fix_ingest_origins.py -- <glb-or-dir> [<glb-or-dir> ...]
    blender --background --python tools/fix_ingest_origins.py            # legacy: the two lab meshes

The ingest contract (skills/examples/operating_room.md) that this establishes, and that
`IDSDL/ingest.py::_copy_centered` assumes:
  1. ONE mesh object per glb — both loaders keep only `imported_objs[0]`, so a multi-OBJECT glb
     renders DISASSEMBLED with the rest stranded at the origin.
  2. Origin == bbox centre — the runtime floor-aligns by AABB bottom, but room-level passes assume
     origin == bbox centre, so an off-centre origin lands the mesh FLOATING or SUNK.

TWO TRAPS THIS TOOL EXISTS TO AVOID (both cost a full pass on art_done.zip, 2026-07-13):

  (a) **The glTF importer PARENTS meshes to EMPTIES, so the naive fix silently NO-OPS.**
      `origin_set(BOUNDS)` + `obj.location = (0,0,0)` sets the object's *local* location; the parent
      empty's transform still offsets it in world space and the exporter writes the hierarchy out.
      The first version of this tool did exactly that, printed `joined N mesh(es)` for all 68 files,
      and changed NOTHING — every asset came out exactly as off-centre as it went in (the easels at
      1.35x their own bbox). => `parent_clear(CLEAR_KEEP_TRANSFORM)`, delete the non-mesh objects,
      and `transform_apply(location=True, ...)` BEFORE `origin_set`.

  (b) **A success message is not evidence.** This tool now measures the final WORLD AABB and refuses
      to claim victory: it prints `center_off` per file and a FAILED list at the end. Verify, don't
      trust. (And note `trimesh`'s geometry count is material PRIMITIVES, not objects — a correctly
      joined 6-material object still loads as `len(scene.geometry) == 6`, so a trimesh mesh-count
      audit reports MULTIMESH on a file that is already fine. Judge object count in Blender.)

Meshes are JOINed in Blender, never concatenated in trimesh (that strips material slots -> flat
white; a Scene round-trip explodes the mesh). Units are NOT touched — supply real-world metres.

Written back UNDER THE SAME FILENAME, so for an ALREADY-INGESTED asset the id, its embedding and
every `asset_id=` pin stay valid. (For a NOT-yet-ingested glb, recentring changes the bytes and
therefore the sha1 id ingest will assign — so fix first, ingest second, pin third.)
"""
import os
import sys

import bpy
from mathutils import Vector

LEGACY_TARGETS = [
    "/work/IDSDL/datasets/custom/models/d0b407b0d9f123f5b1b105f5980c910d3da4cabf.glb",
    "/work/IDSDL/datasets/custom/models/66cdc7bab8ad57951b4cf15df04fb367eb88ea03.glb",
]
CENTER_TOL = 0.02          # |bbox centre| / max(dim); above this the file is NOT centred


def _targets():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        return LEGACY_TARGETS
    out = []
    for a in argv:
        if os.path.isdir(a):
            out += [os.path.join(a, f) for f in sorted(os.listdir(a)) if f.endswith(".glb")]
        else:
            out.append(a)
    return out


def _world_bbox(obj):
    cs = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
    hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
    return lo, hi


def fix(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)

    # (a) drop the importer's EMPTY parent hierarchy, KEEPING world transforms. Without this the
    #     whole repair is a no-op -- see trap (a) in the module docstring.
    bpy.ops.object.select_all(action="SELECT")
    if bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")

    # ...then delete everything that is not a mesh (the empties themselves, cameras, lights)
    bpy.ops.object.select_all(action="DESELECT")
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            o.select_set(True)
    if bpy.context.selected_objects:
        bpy.ops.object.delete()

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        return None, "no mesh objects"

    # 1. JOIN into ONE object (preserves material slots)
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active

    # 2. bake the FULL world transform (location INCLUDED) into the mesh data, then recentre
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # (b) VERIFY against the world AABB -- a success message is not evidence
    lo, hi = _world_bbox(obj)
    ctr, dim = (lo + hi) / 2.0, (hi - lo)
    off = max(abs(ctr.x), abs(ctr.y), abs(ctr.z)) / max(max(dim), 1e-9)

    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    return {"objs": len(meshes), "slots": len(obj.material_slots),
            "dims": (dim.x, dim.y, dim.z), "off": off}, None


failed = []
paths = _targets()
print(f"=== fix_ingest_origins: {len(paths)} glb(s)\n")
for p in paths:
    name = os.path.basename(p)
    try:
        r, err = fix(p)
        if err:
            failed.append((name, err))
            print(f"SKIP {name:<52} {err}")
            continue
        bad = r["off"] > CENTER_TOL
        if bad:
            failed.append((name, f"center_off={r['off']:.3f} > {CENTER_TOL}"))
        print(f"{'FAIL' if bad else 'OK  '} {name:<52} joined={r['objs']:>2} slots={r['slots']:>2} "
              f"dims=({r['dims'][0]:.2f},{r['dims'][1]:.2f},{r['dims'][2]:.2f}) "
              f"center_off={r['off']:.3f}")
    except Exception as e:                                  # noqa: BLE001
        failed.append((name, f"{type(e).__name__}: {e}"))
        print(f"FAIL {name}: {e}")

print(f"\n=== {len(paths) - len(failed)}/{len(paths)} ingest-ready")
for n, e in failed:
    print(f"  FAILED {n}: {e}")
