"""Repair two ingested glbs that violate the ingest contract (multi-mesh + off-center origin).

Run under Blender:  blender --background --python tmp/fix_lab_glbs.py

Both meshes came in with the operating-room hospital.zip and were never used by that scene, so
they never got its Blender repair pass:
  d0b407b0…  binocular microscope   — 5 meshes, origin offset +118% of height (sinks through
                                      any surface it is placed on)
  66cdc7ba…  gas delivery cart      — 32 meshes, origin offset -26% of height (floats 0.62 m)

Fix per skills/examples/operating_room.md: JOIN in Blender (preserves material slots — a trimesh
round-trip strips them and renders flat white), then origin_set(ORIGIN_GEOMETRY, BOUNDS) and zero
the location, which is the invariant IDSDL/ingest.py::_copy_centered is supposed to establish.
Written back UNDER THE SAME FILENAME so the asset id, its embedding and every pin stay valid.
"""
import bpy

TARGETS = [
    "/work/IDSDL/datasets/custom/models/d0b407b0d9f123f5b1b105f5980c910d3da4cabf.glb",
    "/work/IDSDL/datasets/custom/models/66cdc7bab8ad57951b4cf15df04fb367eb88ea03.glb",
]

for path in TARGETS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    print(f"\n=== {path.split('/')[-1][:12]}  imported {len(meshes)} mesh objects")
    if not meshes:
        print("   !! no meshes, skipped")
        continue

    # 1. JOIN into a single mesh — both loaders keep only imported_objs[0], so a multi-mesh
    #    asset renders DISASSEMBLED with the rest stranded at the origin.
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active

    # 2. RECENTER: origin to the bbox centre, then move that origin to the world origin.
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    dim = obj.dimensions
    print(f"   joined -> 1 mesh, {len(obj.material_slots)} material slots, "
          f"dims=({dim.x:.3f}, {dim.y:.3f}, {dim.z:.3f}), origin=BOUNDS centre")

    # 3. Export over the SAME filename (the id is the filename; keeping it preserves the
    #    registry entry, the embedding and every asset_id pin in the scene programs).
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    print(f"   wrote {path}")

print("\n=== done")
