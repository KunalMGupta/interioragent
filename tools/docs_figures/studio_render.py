"""Blender-headless studio renderer for the docs figures.

Usage (run by harness.py, never by hand):
    blender --background scene.blend --python studio_render.py -- \
        <out_dir> <name> <mode> [views]

mode:  group  — light-studio look: white world, soft sun, light-grey floor plane
       room   — cutaway: keep the exported room, hide ceiling + the two camera-side walls
views: comma list from {persp, top, front}; default "persp,top"

Writes <out_dir>/<name>_<view>.png
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT_DIR, NAME, MODE = argv[0], argv[1], argv[2]
VIEWS = (argv[3] if len(argv) > 3 else "persp,top").split(",")

RES = (1152, 864)
SAMPLES = 96
MARGIN = 1.10          # camera pull-back factor past exact fit
PERSP_AZIM = 40.0      # degrees, around +Z, 0 = looking from +Y side
PERSP_ELEV = 28.0      # degrees above the horizon


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
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 1.0 if MODE == "room" else 0.8
    bpy.context.scene.world = world

    sun = bpy.data.objects.new("studio_sun", bpy.data.lights.new("studio_sun", "SUN"))
    sun.data.energy = 4.0 if MODE == "room" else 3.0
    sun.data.angle = math.radians(20)   # soft shadows
    sun.rotation_euler = (math.radians(50), 0, math.radians(135))
    bpy.context.collection.objects.link(sun)


def add_floor(z, span):
    mat = bpy.data.materials.new("studio_floor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.86, 0.86, 0.86, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95

    bpy.ops.mesh.primitive_plane_add(size=span * 12, location=(0, 0, z - 0.001))
    floor = bpy.context.active_object
    floor.name = "studio_floor"
    floor.data.materials.append(mat)
    return floor


def remove_existing_lights():
    for o in list(bpy.context.scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)


def make_camera():
    cam = bpy.data.objects.new("studio_cam", bpy.data.cameras.new("studio_cam"))
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def frame_persp(cam, lo, hi, azim_deg, elev_deg):
    cam.data.type = "PERSP"
    cam.data.angle = math.radians(40)
    center = (lo + hi) / 2
    az, el = math.radians(azim_deg), math.radians(elev_deg)
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
    # Recenter: shift the film so the subject's projected bbox sits mid-frame
    # (fit-to-coords leaves asymmetric slack once the camera is pulled back).
    bpy.context.view_layer.update()
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    pts = [world_to_camera_view(sc, cam, Vector((x, y, z)))
           for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    aspect = RES[0] / RES[1]
    cam.data.shift_x += (cx - 0.5)
    cam.data.shift_y += (cy - 0.5) / aspect


def frame_top(cam, lo, hi):
    cam.data.type = "ORTHO"
    center = (lo + hi) / 2
    cam.location = (center.x, center.y, hi.z + 5)
    cam.rotation_euler = (0, 0, 0)
    aspect = RES[0] / RES[1]
    span_x, span_y = (hi.x - lo.x), (hi.y - lo.y)
    cam.data.ortho_scale = max(span_x, span_y * aspect) * MARGIN


def frame_side(cam, lo, hi, side):
    """Ortho elevation from front (-Y), back (+Y), left (-X), or right (+X)."""
    cam.data.type = "ORTHO"
    center = (lo + hi) / 2
    aspect = RES[0] / RES[1]
    span_x, span_y, span_z = (hi.x - lo.x), (hi.y - lo.y), (hi.z - lo.z)
    if side == "front":
        cam.location = (center.x, lo.y - 8, center.z)
        cam.rotation_euler = (math.radians(90), 0, 0)
        span_h = span_x
    elif side == "back":
        cam.location = (center.x, hi.y + 8, center.z)
        cam.rotation_euler = (math.radians(90), 0, math.radians(180))
        span_h = span_x
    elif side == "left":
        cam.location = (lo.x - 8, center.y, center.z)
        cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
        span_h = span_y
    else:  # right
        cam.location = (hi.x + 8, center.y, center.z)
        cam.rotation_euler = (math.radians(90), 0, math.radians(90))
        span_h = span_y
    cam.data.ortho_scale = max(span_h, span_z * aspect) * MARGIN


def hide_camera_side_walls(lo, hi):
    """Room cutaway: hide the ceiling and the two walls nearest the camera.

    With PERSP_AZIM=40 the camera sits at +X / -Y of the room, so hide the wall
    meshes whose center lies on the min-Y or max-X boundary, plus the ceiling.
    """
    cx = (lo.x + hi.x) / 2
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
        # Doors / windows / wall art hugging a culled wall must be culled with it,
        # or they render as slabs floating at the room's open edge. True wall
        # slabs are paper-thin (doors/windows ~0.05-0.1 m) or hang off the floor
        # (wall art); floor-standing furniture flush to the wall (e.g. a 0.37 m
        # deep console) must NOT be culled with the wall.
        def _slabbish(depth):
            return depth < 0.15 or bb_lo.z > lo.z + 0.15

        hugs_culled_wall = (
            (cy < lo.y + 0.2 and (bb_hi.y - bb_lo.y) < 0.4
             and _slabbish(bb_hi.y - bb_lo.y))
            or (ocx > hi.x - 0.2 and (bb_hi.x - bb_lo.x) < 0.4
                and _slabbish(bb_hi.x - bb_lo.x)))
        if not (is_wallish or hugs_culled_wall):
            continue
        if cy < lo.y + 0.3 or ocx > hi.x - 0.3:
            o.hide_render = True
    _ = cx


def setup_render():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "Medium Contrast"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:  # CPU fallback keeps the harness usable anywhere
        print("[studio] GPU unavailable, using CPU:", e)


def main():
    objs = mesh_objects()
    if not objs:
        raise SystemExit("[studio] no mesh objects in blend")
    lo, hi = world_bbox(objs)

    remove_existing_lights()
    setup_world_and_lights()

    if MODE == "group":
        span = max(hi.x - lo.x, hi.y - lo.y, 2.0)
        add_floor(lo.z, span)
    elif MODE == "room":
        hide_camera_side_walls(lo, hi)

    setup_render()
    cam = make_camera()

    for view in VIEWS:
        if view == "persp":
            frame_persp(cam, lo, hi, PERSP_AZIM, PERSP_ELEV)
        elif view == "top":
            frame_top(cam, lo, hi)
        elif view in ("front", "back", "left", "right"):
            frame_side(cam, lo, hi, view)
        else:
            raise SystemExit(f"[studio] unknown view {view}")
        bpy.context.scene.render.filepath = f"{OUT_DIR}/{NAME}_{view}.png"
        bpy.ops.render.render(write_still=True)
        print(f"[studio] wrote {bpy.context.scene.render.filepath}")


main()
