"""Blender-headless 360° turntable for a finished scene blend, in the docs studio look.

    blender --background scene.blend --python orbit360.py -- <out_path> [mode]

mode:  video   (default) — H.264 orbit, FRAMES frames at FPS
       stills            — three azimuth PNGs (<out_path>_a{az}.png) for fast iteration

Style matches tools/docs_figures renders: existing lights removed, white world +
soft sun, ceiling hidden, Filmic Medium Contrast. All four walls are kept; the
camera orbits above wall height looking down into the room.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
MODE = argv[1] if len(argv) > 1 else "video"

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def retarget_missing_images():
    """Blends built elsewhere reference unpacked textures under the build
    machine's absolute path (e.g. /work/IDSDL/datasets/...). Remap anything
    missing onto this checkout's dataset tree so walls don't render magenta."""
    fixed = 0
    for im in bpy.data.images:
        if im.packed_file or im.source != "FILE" or not im.filepath:
            continue
        if os.path.exists(bpy.path.abspath(im.filepath)):
            continue
        idx = im.filepath.find("IDSDL/datasets")
        if idx >= 0:
            cand = os.path.join(REPO, im.filepath[idx:])
            if os.path.exists(cand):
                im.filepath = cand
                im.reload()
                fixed += 1
    if fixed:
        print(f"[orbit] retargeted {fixed} missing texture path(s)")

RES = (1280, 720)
SAMPLES = int(os.environ.get("ORBIT_SAMPLES", "64"))
FRAMES = int(os.environ.get("ORBIT_FRAMES", "240"))
FPS = 24
ELEV_DEG = 32.0        # camera elevation above the horizon
MARGIN = 1.12
STILL_AZIMS = (40.0, 160.0, 280.0)


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


def hide_ceiling(lo, hi):
    for o in mesh_objects():
        n = o.name.lower()
        bb_lo, bb_hi = world_bbox([o])
        flat_z = (bb_hi.z - bb_lo.z) < 0.35 and bb_lo.z > (hi.z - 0.6)
        if "ceiling" in n or flat_z:
            o.hide_render = True


def make_backface_transparent(o):
    """Dollhouse walls: the exported walls are zero-thickness planes whose normals
    point INTO the room, so mixing to a Transparent BSDF on backfacing makes each
    wall vanish exactly while the camera is on its far side — smoothly, all orbit."""
    for slot in o.material_slots:
        mat = slot.material
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        out_node = next((n for n in nt.nodes
                         if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
        if out_node is None or not out_node.inputs["Surface"].links:
            continue
        src = out_node.inputs["Surface"].links[0].from_socket
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        trans = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
        nt.links.new(src, mix.inputs[1])
        nt.links.new(trans.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out_node.inputs["Surface"])


BOUNDARY_HUG = 0.55
# Hide wall dressing slightly BEFORE its wall reaches edge-on: a zero-thickness
# wall vanishes at grazing angles, and a door still visible there floats in air.
HIDE_DOT = -0.1


def boundary_meshes(lo, hi):
    """(obj, outward_xy) for non-wall meshes that are wall DRESSING — doors,
    windows, curtains, rails, art. They vanish while their wall is transparent.
    Dressing is tall (reaches above furniture height) and elongated along its
    wall; furniture standing against a wall stays visible all orbit."""
    out = []
    for o in mesh_objects():
        if "wall" in o.name.lower():
            continue
        bb_lo, bb_hi = world_bbox([o])
        if bb_hi.z < lo.z + 1.5:
            continue                       # furniture-height: always visible
        tx, ty = bb_hi.x - bb_lo.x, bb_hi.y - bb_lo.y
        cx, cy = (bb_lo.x + bb_hi.x) / 2, (bb_lo.y + bb_hi.y) / 2
        if tx < 0.7 and ty > 1.5 * tx:
            if (cx - lo.x) < BOUNDARY_HUG:
                out.append((o, Vector((-1.0, 0.0))))
                continue
            if (hi.x - cx) < BOUNDARY_HUG:
                out.append((o, Vector((1.0, 0.0))))
                continue
        if ty < 0.7 and tx > 1.5 * ty:
            if (cy - lo.y) < BOUNDARY_HUG:
                out.append((o, Vector((0.0, -1.0))))
            elif (hi.y - cy) < BOUNDARY_HUG:
                out.append((o, Vector((0.0, 1.0))))
    return out


def near_side(outward, azim_deg):
    az = math.radians(azim_deg)
    cam_dir = Vector((math.sin(az), -math.cos(az)))
    return outward.dot(cam_dir) > HIDE_DOT


def cam_pos(center, radius, azim_deg):
    az = math.radians(azim_deg)
    el = math.radians(ELEV_DEG)
    return Vector((center.x + radius * math.cos(el) * math.sin(az),
                   center.y - radius * math.cos(el) * math.cos(az),
                   center.z + radius * math.sin(el)))


def fit_radius(cam, lo, hi, center):
    """Largest fitted camera distance over four azimuths, so the whole room stays
    in frame throughout the orbit."""
    dg = bpy.context.evaluated_depsgraph_get()
    corners = []
    for x in (lo.x, hi.x):
        for y in (lo.y, hi.y):
            for z in (lo.z, hi.z):
                corners.extend((x, y, z))
    best = 0.0
    for az in (0.0, 90.0, 180.0, 270.0):
        cam.location = cam_pos(center, 10.0, az)
        look = center - cam.location
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        loc, _ = cam.camera_fit_coords(dg, corners)
        best = max(best, (loc - center).length)
    return best * MARGIN


def setup_render(animation):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = RES
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
        print("[orbit] GPU unavailable, using CPU:", e)


def main():
    retarget_missing_images()
    objs = mesh_objects()
    if not objs:
        raise SystemExit("[orbit] no mesh objects in blend")
    lo, hi = world_bbox(objs)
    setup_world_and_lights()
    hide_ceiling(lo, hi)
    lo, hi = world_bbox(mesh_objects())     # re-measure without the ceiling

    for o in mesh_objects():
        if "wall" in o.name.lower():
            make_backface_transparent(o)
    mounted = boundary_meshes(lo, hi)

    # aim slightly below the room's mid-height so the floor dominates the frame
    center = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2,
                     lo.z + (hi.z - lo.z) * 0.35))

    cam = bpy.data.objects.new("orbit_cam", bpy.data.cameras.new("orbit_cam"))
    cam.data.angle = math.radians(40)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    radius = fit_radius(cam, lo, hi, center)

    target = bpy.data.objects.new("orbit_target", None)
    target.location = center
    bpy.context.collection.objects.link(target)
    tr = cam.constraints.new(type="TRACK_TO")
    tr.target = target
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"

    if MODE == "stills":
        setup_render(animation=False)
        base = OUT[:-4] if OUT.endswith(".png") else OUT
        for az in STILL_AZIMS:
            cam.location = cam_pos(center, radius, az)
            for o, outward in mounted:
                o.hide_render = near_side(outward, az)
            bpy.context.scene.render.filepath = f"{base}_a{int(az):03d}.png"
            bpy.ops.render.render(write_still=True)
            print(f"[orbit] wrote {bpy.context.scene.render.filepath}")
        return

    for f in range(1, FRAMES + 1):
        az = 360.0 * (f - 1) / FRAMES
        cam.location = cam_pos(center, radius, az)
        cam.keyframe_insert("location", frame=f)
        for o, outward in mounted:
            o.hide_render = near_side(outward, az)
            o.keyframe_insert("hide_render", frame=f)
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = FRAMES
    setup_render(animation=True)
    bpy.context.scene.render.filepath = OUT
    bpy.ops.render.render(animation=True)
    print(f"[orbit] wrote {OUT}")


main()
