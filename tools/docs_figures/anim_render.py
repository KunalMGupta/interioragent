"""Blender-headless animation renderer for the docs solver videos.

Usage (run by video.py, never by hand):
    blender --background scene.blend --python anim_render.py -- \
        <frames_json> <out_mp4>

frames_json (written by video.py): fps, lead_hold, tail_hold, view, and a list
of solver snapshots, each a list over scene-object index of [x, y, z, rot_deg]
in IDSDL coordinates (y-up). Exported instances are named by that index, with
Blender location = (x, -z, y) and yaw on the Z euler.

Writes <out_mp4> as H.264.
"""
import json
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
FRAMES_JSON, OUT_MP4 = argv[0], argv[1]

RES = (1152, 864)
SAMPLES = 48
MARGIN = 1.10
PERSP_AZIM = 40.0
PERSP_ELEV = 28.0

with open(FRAMES_JSON) as f:
    DATA = json.load(f)


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


def setup_world_and_lights():
    for o in list(bpy.context.scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = world
    sun = bpy.data.objects.new("studio_sun", bpy.data.lights.new("studio_sun", "SUN"))
    sun.data.energy = 4.0
    sun.data.angle = math.radians(20)
    sun.rotation_euler = (math.radians(50), 0, math.radians(135))
    bpy.context.collection.objects.link(sun)


def hide_camera_side_walls(lo, hi):
    for o in mesh_objects():
        n = o.name.lower()
        bb_lo, bb_hi = world_bbox([o])
        flat_z = (bb_hi.z - bb_lo.z) < 0.35 and bb_lo.z > (hi.z - 0.6)
        if "ceiling" in n or flat_z:
            o.hide_render = True
            continue
        cy = (bb_lo.y + bb_hi.y) / 2
        ocx = (bb_lo.x + bb_hi.x) / 2
        is_wallish = ("wall" in n) or (
            (bb_hi.z - bb_lo.z) > (hi.z - lo.z) * 0.7
            and min(bb_hi.x - bb_lo.x, bb_hi.y - bb_lo.y) < 0.3)
        hugs_culled_wall = (
            (cy < lo.y + 0.2 and (bb_hi.y - bb_lo.y) < 0.4)
            or (ocx > hi.x - 0.2 and (bb_hi.x - bb_lo.x) < 0.4))
        if not (is_wallish or hugs_culled_wall):
            continue
        if cy < lo.y + 0.3 or ocx > hi.x - 0.3:
            o.hide_render = True


def make_camera():
    cam = bpy.data.objects.new("studio_cam", bpy.data.cameras.new("studio_cam"))
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def frame_top(cam, lo, hi):
    cam.data.type = "ORTHO"
    center = (lo + hi) / 2
    cam.location = (center.x, center.y, hi.z + 5)
    cam.rotation_euler = (0, 0, 0)
    aspect = RES[0] / RES[1]
    span_x, span_y = (hi.x - lo.x), (hi.y - lo.y)
    cam.data.ortho_scale = max(span_x, span_y * aspect) * MARGIN


def frame_persp(cam, lo, hi):
    cam.data.type = "PERSP"
    cam.data.angle = math.radians(40)
    center = (lo + hi) / 2
    az, el = math.radians(PERSP_AZIM), math.radians(PERSP_ELEV)
    direction = Vector((math.sin(az) * math.cos(el),
                        -math.cos(az) * math.cos(el),
                        math.sin(el)))
    cam.location = center + direction * 10
    look = center - cam.location
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    corners = []
    for x in (lo.x, hi.x):
        for y in (lo.y, hi.y):
            for z in (lo.z, hi.z):
                corners.extend((x, y, z))
    loc, _ = cam.camera_fit_coords(dg, corners)
    cam.location = center + (loc - center) * MARGIN


def animate():
    frames = DATA["frames"]
    lead, tail = int(DATA["lead_hold"]), int(DATA["tail_hold"])
    n_obj_final = max(len(fr) for fr in frames)

    for idx in range(n_obj_final):
        ob = bpy.data.objects.get(str(idx))
        if ob is None:
            continue
        series = []
        for fi, fr in enumerate(frames):
            if idx < len(fr) and fr[idx] is not None:
                series.append((fi, fr[idx]))
        if not series:
            continue
        # hold at first known value through the lead-in (and any earlier frames)
        first_fi, first_val = series[0]
        keyed = [(0, first_val)] + [(lead + fi, val) for fi, val in series]
        keyed.append((lead + len(frames) - 1 + tail, series[-1][1]))
        moved = any(v != series[0][1] for _, v in series)
        if not moved:
            keyed = [keyed[0], keyed[-1]]
        for f, (x, y, z, rot) in keyed:
            ob.location = (x, -z, y)
            ob.rotation_euler = (0, 0, math.radians(rot))
            ob.keyframe_insert("location", frame=f + 1)
            ob.keyframe_insert("rotation_euler", frame=f + 1)
        if ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    total = lead + len(frames) + tail
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = total
    return total


def setup_render():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "Medium Contrast"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.fps = int(DATA["fps"])
    sc.render.filepath = OUT_MP4
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("[anim] GPU unavailable, using CPU:", e)


def main():
    objs = mesh_objects()
    if not objs:
        raise SystemExit("[anim] no mesh objects in blend")
    lo, hi = world_bbox(objs)

    setup_world_and_lights()
    hide_camera_side_walls(lo, hi)
    animate()
    setup_render()
    cam = make_camera()
    if DATA.get("view") == "persp":
        frame_persp(cam, lo, hi)
    else:
        frame_top(cam, lo, hi)
    bpy.ops.render.render(animation=True)
    print(f"[anim] wrote {OUT_MP4}")


main()
