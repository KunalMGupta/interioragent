"""Blender-side renderer for the cherry-blossom title demo (run by blossom.py).

    blender --background blossom_title.blend --python blossom_render.py -- <out_dir>

Renders a top-view still, then a walkthrough: a low dolly through the corridor
between text lines, followed by a crane up and back to reveal the whole title.
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT_DIR = argv[0]

RES = (1280, 720)
STILL_RES = (1600, 900)
SAMPLES = 32
FPS = 24
N_FRAMES = 384


def mesh_objects():
    return [o for o in bpy.context.scene.objects
            if o.type == "MESH" and not o.hide_render]


def world_bbox(objs):
    pts = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        ev = o.evaluated_get(dg)
        for c in ev.bound_box:
            pts.append(ev.matrix_world @ Vector(c))
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def setup_world():
    for o in list(bpy.context.scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.93, 0.96, 1.0, 1.0)   # pale sky
    bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = world
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.data.angle = math.radians(15)
    sun.rotation_euler = (math.radians(55), 0, math.radians(120))
    bpy.context.collection.objects.link(sun)


def add_ground(z, span):
    mat = bpy.data.materials.new("ground")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.82, 0.86, 0.78, 1.0)  # soft grass
    bsdf.inputs["Roughness"].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=span * 6, location=(0, 0, z - 0.002))
    floor = bpy.context.active_object
    floor.data.materials.append(mat)


def setup_render(res, animation):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "Medium Contrast"
    if animation:
        sc.render.image_settings.file_format = "FFMPEG"
        sc.render.ffmpeg.format = "MPEG4"
        sc.render.ffmpeg.codec = "H264"
        sc.render.ffmpeg.constant_rate_factor = "HIGH"
        sc.render.ffmpeg.ffmpeg_preset = "GOOD"
        sc.render.fps = FPS
    else:
        sc.render.image_settings.file_format = "PNG"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("[blossom] GPU unavailable, using CPU:", e)


def main():
    objs = mesh_objects()
    if not objs:
        raise SystemExit("[blossom] no mesh objects")
    lo, hi = world_bbox(objs)
    center = (lo + hi) / 2
    span_x, span_y = hi.x - lo.x, hi.y - lo.y
    span = max(span_x, span_y)

    setup_world()
    add_ground(lo.z, span)

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.angle = math.radians(42)

    # ---- still: ortho top view of the whole title ----
    cam.data.type = "ORTHO"
    cam.location = (center.x, center.y, hi.z + 10)
    cam.rotation_euler = (0, 0, 0)
    aspect = STILL_RES[0] / STILL_RES[1]
    cam.data.ortho_scale = max(span_x, span_y * aspect) * 1.08
    setup_render(STILL_RES, animation=False)
    bpy.context.scene.render.filepath = f"{OUT_DIR}/blossom_title_top.png"
    bpy.ops.render.render(write_still=True)
    print(f"[blossom] wrote {OUT_DIR}/blossom_title_top.png")

    # ---- walkthrough ----
    cam.data.type = "PERSP"
    target = bpy.data.objects.new("cam_target", None)
    bpy.context.collection.objects.link(target)
    tr = cam.constraints.new(type="TRACK_TO")
    tr.target = target
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"

    # corridor between the first and second text line (lines stack along -y)
    corridor_y = center.y + span_y / 6.0
    eye = lo.z + 1.7

    cam_keys = [
        (1,   (lo.x - 9.0, corridor_y, eye + 0.3)),
        (150, (center.x - span_x * 0.12, corridor_y, eye + 0.6)),
        (250, (center.x + span_x * 0.10, corridor_y - span_y * 0.35, eye + span * 0.24)),
        # end high enough that the widest line clears the 42° frustum with margin
        (N_FRAMES, (center.x, center.y - span_y * 0.55, lo.z + span_x * 1.5)),
    ]
    tgt_keys = [
        (1,   (lo.x + 4.0, corridor_y, eye + 0.6)),
        (150, (center.x + span_x * 0.25, corridor_y, eye + 0.4)),
        (250, (center.x, center.y, lo.z + 1.0)),
        (N_FRAMES, (center.x, center.y, lo.z)),
    ]
    for ob, keys in ((cam, cam_keys), (target, tgt_keys)):
        for f, loc in keys:
            ob.location = loc
            ob.keyframe_insert("location", frame=f)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = N_FRAMES
    setup_render(RES, animation=True)
    bpy.context.scene.render.filepath = f"{OUT_DIR}/blossom_walkthrough.mp4"
    bpy.ops.render.render(animation=True)
    print(f"[blossom] wrote {OUT_DIR}/blossom_walkthrough.mp4")


main()
