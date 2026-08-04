"""Blender-side renderer for the cherry-blossom title demo (run by blossom.py).

    blender --background blossom_title.blend --python blossom_render.py -- <out_dir>

Renders a top-view still, then a walkthrough: a low dolly through the corridor
between text lines, followed by a crane up and back to reveal the whole title.
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = argv[0] if argv else "."

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
    """Procedural daylight: a Nishita sky drives both the backdrop and the sun."""
    for o in list(bpy.context.scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(55)
    sky.sun_rotation = math.radians(120)
    sky.sun_intensity = 0.5
    sky.altitude = 200
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs[1].default_value = 0.7
    bpy.context.scene.world = world


def add_ground(z, span):
    """Grass: two greens mixed by noise, with a darker large-scale patchiness."""
    mat = bpy.data.materials.new("grass")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    coords = nt.nodes.new("ShaderNodeTexCoord")      # Object coords = meters
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0        # blade-level speckle
    noise.inputs["Detail"].default_value = 8.0
    patch = nt.nodes.new("ShaderNodeTexNoise")
    patch.inputs["Scale"].default_value = 0.05       # broad patchiness (~20 m)
    nt.links.new(coords.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(coords.outputs["Object"], patch.inputs["Vector"])
    blade = nt.nodes.new("ShaderNodeMixRGB")
    blade.inputs["Color1"].default_value = (0.10, 0.22, 0.05, 1.0)
    blade.inputs["Color2"].default_value = (0.22, 0.34, 0.09, 1.0)
    dark = nt.nodes.new("ShaderNodeMixRGB")
    dark.blend_type = "MULTIPLY"
    dark.inputs["Fac"].default_value = 0.35
    dark.inputs["Color2"].default_value = (0.55, 0.62, 0.45, 1.0)
    nt.links.new(noise.outputs["Fac"], blade.inputs["Fac"])
    nt.links.new(blade.outputs["Color"], dark.inputs["Color1"])
    nt.links.new(patch.outputs["Fac"], dark.inputs["Fac"])
    nt.links.new(dark.outputs["Color"], bsdf.inputs["Base Color"])
    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(0, 0, z - 0.002))
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
    sc.view_settings.exposure = -2.0      # Nishita sky is physically bright
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
        # tight ending: the title nearly fills the frame
        (N_FRAMES, (center.x, center.y - span_y * 0.45, lo.z + span_x * 1.5)),
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


if __name__ == "__main__":
    main()
