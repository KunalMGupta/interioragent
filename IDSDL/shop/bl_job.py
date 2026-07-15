"""Blender-side worker for the asset shop. Runs INSIDE Blender (via SceneProgExec), never here.

    blender --background --python bl_job.py -- <config.json>

Two modes, one file (kept self-contained on purpose: the runner copies this script into each
job's own directory so parallel jobs never share a log file or an import path):

  preview   import -> join -> measure -> render 4 straight-on ortho side views + a hero
  finalize  import -> join -> rotate -> uniform-scale -> centre -> export .glb -> re-render

The output contract, which is exactly what IDSDL.ingest already assumes and never checks:
ONE mesh, textures intact, AABB centred at the origin, uniformly scaled to real-world metres,
and the front facing -Y in Blender — which `export_yup=True` writes out as +Z in glTF.

FIVE LOAD-BEARING FIXES live in here (each one cost real debugging time; see
skills/ingest-assets/SKILL.md before you "simplify" any of them):

 1. Unit-scale overwritten by resize. The glTF importer parents meshes under empties carrying a
    unit-conversion scale (cm->m etc). Join, then unparent by ASSIGNING matrix_world (the
    parent_clear operator silently no-ops in --background), delete the empties, and
    transform_apply so the object starts from an IDENTITY transform in real units. Skip this and
    a later `obj.scale = f` REPLACES the baked unit scale instead of composing with it -> 72x
    blowups.
 2. Quaternion rotation mode. The importer leaves objects in QUATERNION mode, where assigning
    `rotation_euler` is silently IGNORED (location/scale are mode-independent, which is why only
    the rotation "vanishes"). Force rotation_mode = 'XYZ' first.
 3. The EEVEE enum name moves between Blender versions ('BLENDER_EEVEE' vs 'BLENDER_EEVEE_NEXT').
    Pick whichever the running build actually offers instead of hard-coding one.
 4. Camera clip planes cull large-unit models. A model authored in millimetres is thousands of
    units tall; with the default far clip it renders as a blank grey frame and the VLM dutifully
    calls it "empty". Widen clip_end relative to the object.
 5. UV-safe join. Blender's Join merges UV layers BY NAME off the ACTIVE object; if the active
    mesh has no UVs, textured UVs scramble and the textures vanish. Give every mesh a 'UVMap'
    active-render layer and anchor the join to a mesh that actually has UVs.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

# Panel k of the preview shows the side of the object FACING direction k. The host maps the
# VLM's chosen panel back to a rotation; keep these in lockstep with triage.PANELS.
VIEWS = [("p1", Vector((0, 1, 0))),    # camera on +Y  -> shows the +Y side
         ("p2", Vector((0, -1, 0))),   # camera on -Y  -> shows the -Y side  (the target front)
         ("p3", Vector((1, 0, 0))),    # camera on +X  -> shows the +X side
         ("p4", Vector((-1, 0, 0)))]   # camera on -X  -> shows the -X side


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def meshes():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def world_aabb(objs):
    mn = Vector((1e18,) * 3)
    mx = Vector((-1e18,) * 3)
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    return mn, mx


def join_single():
    """Fix 5 (UV-safe join) + fix 1 (unparent, drop empties, bake to identity)."""
    ms = meshes()
    if not ms:
        return None
    UVN = "UVMap"

    def has_uvs(o):
        me = o.data
        if UVN not in me.uv_layers or not len(me.loops):
            return False
        uvl = me.uv_layers[UVN]
        return any(uvl.data[i].uv[0] or uvl.data[i].uv[1]
                   for i in range(min(len(uvl.data), 300)))

    for o in ms:
        me = o.data
        if UVN not in me.uv_layers:
            me.uv_layers.new(name=UVN)
        uvl = me.uv_layers[UVN]
        uvl.active_render = True
        me.uv_layers.active = uvl

    textured = [o for o in ms if has_uvs(o)]
    anchor = max(textured or ms, key=lambda o: len(o.data.polygons))
    anchor.data.uv_layers[UVN].active_render = True

    bpy.ops.object.select_all(action="DESELECT")
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = anchor
    if len(ms) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active

    mw = obj.matrix_world.copy()          # fix 1: the operator no-ops in background
    obj.parent = None
    obj.matrix_world = mw
    bpy.context.view_layer.update()
    for e in [o for o in bpy.context.scene.objects if o.type == "EMPTY"]:
        bpy.data.objects.remove(e, do_unlink=True)
    bpy.context.view_layer.update()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def setup_render(res):
    """FIX 6 — the lighting must not pick a favourite side.

    A single fixed sun lights (say) +X and leaves -X in shadow, and the VLM then reliably calls
    the BRIGHT side the front: a wall shelf whose flat back was lit and whose shelved front was
    black got its front called 180 degrees wrong, with high confidence. The render, not the
    model, was lying. So there is no fixed key light here: `render_views` re-aims the sun along
    each view direction, giving every panel an identical headlight, and the world provides a
    strong even ambient so nothing important sits in the dark. Symmetric lighting for a question
    about symmetry."""
    sc = bpy.context.scene
    engines = {i.identifier for i in                                    # fix 3
               bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    for e in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        if e in engines:
            sc.render.engine = e
            break
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.70, 0.70, 0.73, 1.0)   # neutral grey: white assets on a
        bg.inputs[1].default_value = 1.6                       # white bg vanish for the VLM
    ld = bpy.data.lights.new("Key", "SUN")
    ld.energy = 2.5
    sun = bpy.data.objects.new("Key", ld)
    bpy.context.collection.objects.link(sun)
    return sun


def render_views(center, dims, out_dir, tag, res, sun=None):
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    aim = bpy.data.objects.new("aim", None)
    bpy.context.collection.objects.link(aim)
    aim.location = center

    if sun is not None:                        # fix 6: the key light rides the camera
        sc_ = sun.constraints.new("TRACK_TO")
        sc_.target = aim
        sc_.track_axis = "TRACK_NEGATIVE_Z"
        sc_.up_axis = "UP_Y"

    cd = bpy.data.cameras.new("Cam")
    cd.type = "ORTHO"
    cd.ortho_scale = max(dims) * 1.06
    reach = max(dims) * 2.0 + 1.0
    cd.clip_start = 0.001
    cd.clip_end = max(1000.0, reach * 6.0)               # fix 4
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    con = cam.constraints.new("TRACK_TO")
    con.target = aim
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    paths = {}
    for name, d in VIEWS:
        cam.location = center + d * reach
        if sun is not None:                    # headlight, lifted for some modelling shadow
            sun.location = cam.location + Vector((0, 0, reach * 0.6))
        bpy.context.view_layer.update()
        p = os.path.join(out_dir, f"{tag}_{name}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths[name] = p

    cd.type = "PERSP"
    cd.lens = 50
    cam.location = center + Vector((reach * 0.8, -reach * 0.8, reach * 0.6))
    if sun is not None:
        sun.location = cam.location + Vector((0, 0, reach * 0.6))
    bpy.context.view_layer.update()
    p = os.path.join(out_dir, f"{tag}_hero.png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    paths["hero"] = p
    return paths


def measure(obj):
    mn, mx = world_aabb([obj])
    c = (mn + mx) / 2
    d = mx - mn
    return c, d


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    cfg = json.load(open(argv[0]))
    res = int(cfg.get("res", 420))
    tag = cfg.get("tag", "asset")
    out_dir = cfg["out_dir"]
    result = {"mode": cfg["mode"], "ok": False}

    clear()
    bpy.ops.import_scene.gltf(filepath=cfg["src"])
    n_meshes = len(meshes())
    result["meshes_before_join"] = n_meshes
    result["n_images"] = len(bpy.data.images)
    if not n_meshes:
        result["error"] = "no_mesh"
        json.dump(result, open(cfg["result"], "w"))
        return

    obj = join_single()
    result["n_polys"] = len(obj.data.polygons)

    if cfg["mode"] == "finalize":
        rot = cfg.get("rot_deg", [0, 0, 0])
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        obj.rotation_mode = "XYZ"                                     # fix 2
        obj.rotation_euler = tuple(math.radians(a) for a in rot)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        _, dims = measure(obj)
        axis = {"x": 0, "y": 1, "z": 2}[cfg.get("scale_axis", "z")]
        if dims[axis] <= 1e-9:
            result["error"] = "degenerate_axis"
            json.dump(result, open(cfg["result"], "w"))
            return
        f = float(cfg["scale_size"]) / dims[axis]        # UNIFORM: never distort proportions
        obj.scale = (f, f, f)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        c, _ = measure(obj)
        obj.location = -c
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

        out_glb = cfg["out_glb"]
        os.makedirs(os.path.dirname(out_glb), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        # export_yup: Blender's -Y (our front) becomes glTF's +Z — the library's front convention.
        bpy.ops.export_scene.gltf(filepath=out_glb, export_format="GLB",
                                  use_selection=True, export_yup=True)

        clear()                                          # verify by re-importing what we WROTE
        bpy.ops.import_scene.gltf(filepath=out_glb)
        vobj = meshes()
        result["final_mesh_count"] = len(vobj)
        result["n_images_final"] = len(bpy.data.images)
        obj = join_single()
        result["out_glb"] = out_glb
        result["out_size_mb"] = round(os.path.getsize(out_glb) / 1e6, 2)

    c, d = measure(obj)
    result["center"] = [round(v, 4) for v in c]
    result["dims"] = {"w_x": round(d.x, 4), "d_y": round(d.y, 4), "h_z": round(d.z, 4)}
    sun = setup_render(res)
    result["views"] = render_views(c, d, out_dir, tag, res, sun=sun)
    result["ok"] = True
    json.dump(result, open(cfg["result"], "w"))


main()
