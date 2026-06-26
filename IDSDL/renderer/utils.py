import os
import bpy
import sys
import numpy as np
from mathutils import Vector


# ---------------------------------------------------------------------
# GPU / CUDA SETUP
# ---------------------------------------------------------------------

def enable_cuda_rendering():
    """
    Enable CUDA GPU rendering for Cycles.

    This assumes:
    1. You are using an NVIDIA GPU.
    2. The Docker/Linux container can see the GPU.
    3. Blender was built with CUDA support.
    """

    prefs = bpy.context.preferences

    # Make sure Cycles addon is enabled.
    if "cycles" not in prefs.addons:
        bpy.ops.preferences.addon_enable(module="cycles")

    cycles_prefs = prefs.addons["cycles"].preferences

    # Use CUDA backend.
    cycles_prefs.compute_device_type = "CUDA"

    # Refresh device list.
    cycles_prefs.get_devices()

    print("\n========== Blender Cycles CUDA Device Info ==========")
    print(f"Compute device type: {cycles_prefs.compute_device_type}")

    gpu_found = False

    for device in cycles_prefs.devices:
        print(f"Device found: name={device.name}, type={device.type}, use={device.use}")

        if device.type == "CUDA":
            device.use = True
            gpu_found = True
            print(f"Enabled CUDA device: {device.name}")
        elif device.type == "CPU":
            # Usually disable CPU if you specifically want CUDA.
            device.use = False
            print(f"Disabled CPU device: {device.name}")

    if not gpu_found:
        print("WARNING: No CUDA GPU found by Blender. Rendering may fall back to CPU.")
    else:
        print("CUDA GPU rendering enabled.")

    print("=====================================================\n")

    # Set current scene to use GPU for Cycles.
    bpy.context.scene.cycles.device = "GPU"


# ---------------------------------------------------------------------
# SCENE UTILITIES
# ---------------------------------------------------------------------

def set_clamp_factor_to_zero():
    for material in bpy.data.materials:
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == 'MIX':
                    factor_input = node.inputs[0]
                    if factor_input.name == "Factor" and isinstance(factor_input.default_value, (int, float)):
                        factor_input.default_value = 0.0
                        print(f"Numeric Factor value set to: {factor_input.default_value}")
                    else:
                        print("Numeric Factor input not found or is not editable.")


def set_white_world_background(strength=0.2):
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new(name="World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    bg_node = nodes.new(type='ShaderNodeBackground')
    bg_node.location = (0, 0)
    bg_node.inputs['Color'].default_value = (0.7, 0.7, 0.7, 1.0)
    bg_node.inputs['Strength'].default_value = strength

    world_output_node = nodes.new(type='ShaderNodeOutputWorld')
    world_output_node.location = (200, 0)

    links.new(bg_node.outputs['Background'], world_output_node.inputs['Surface'])


def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    bpy.ops.object.select_by_type(type='CAMERA')
    bpy.ops.object.delete()

    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete()


def load_scene(scene_path):
    bpy.ops.wm.open_mainfile(filepath=scene_path)


def apply_smooth_shading():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_smooth()
            obj.select_set(False)


def save_current_scene(filepath):
    bpy.ops.wm.save_as_mainfile(filepath=filepath)


# ---------------------------------------------------------------------
# RENDER SETUP
# ---------------------------------------------------------------------

def setup_renderer(
    output_path,
    resolution_x=1920,
    resolution_y=1080,
    samples=100,
    use_cuda=True,
    transparent=True,
):
    scene = bpy.context.scene
    render = scene.render

    # Use Cycles instead of EEVEE because CUDA applies to Cycles.
    render.engine = 'CYCLES'

    if use_cuda:
        enable_cuda_rendering()
    else:
        scene.cycles.device = "CPU"

    # Cycles settings.
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True

    # Optional: useful for speed.
    # You can tune these depending on your scene.
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 8

    # Resolution.
    render.resolution_x = resolution_x
    render.resolution_y = resolution_y
    render.resolution_percentage = 100

    # Output.
    render.filepath = output_path
    render.image_settings.file_format = 'PNG'
    render.image_settings.color_mode = 'RGBA'

    # Transparent background.
    render.film_transparent = transparent


def setup_renderer_video(
    output_path,
    resolution_x=1920,
    resolution_y=1080,
    frame_rate=30,
    samples=100,
    use_cuda=True,
):
    scene = bpy.context.scene
    render = scene.render

    # Use Cycles because CUDA applies to Cycles.
    render.engine = 'CYCLES'

    if use_cuda:
        enable_cuda_rendering()
    else:
        scene.cycles.device = "CPU"

    # Cycles settings.
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True

    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 8

    # Video output.
    render.image_settings.file_format = 'FFMPEG'
    render.ffmpeg.format = 'MPEG4'
    render.ffmpeg.codec = 'H264'
    render.ffmpeg.constant_rate_factor = 'HIGH'
    render.ffmpeg.ffmpeg_preset = 'GOOD'
    render.ffmpeg.video_bitrate = 5000

    # Resolution.
    render.resolution_x = resolution_x
    render.resolution_y = resolution_y
    render.resolution_percentage = 100
    render.fps = frame_rate
    render.filepath = output_path


# ---------------------------------------------------------------------
# CAMERA
# ---------------------------------------------------------------------

def initialize_camera():
    cam_data = bpy.data.cameras.new('Camera')
    cam_ob = bpy.data.objects.new('Camera', cam_data)
    bpy.context.scene.collection.objects.link(cam_ob)
    bpy.context.scene.camera = cam_ob
    return cam_ob


def place_camera(cam_ob, loc, looking_at):
    cx, cy, cz = loc
    point = looking_at

    cam_ob.location = Vector((cx, cy, cz))
    direction = Vector(point) - cam_ob.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_ob.rotation_euler = rot_quat.to_euler()


def render_image():
    bpy.ops.render.render(write_still=True)


def animate_camera(cam_ob, cam_radius, scene_center, num_frames=360):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = num_frames

    for frame, theta in enumerate(range(0, num_frames), start=1):
        theta -= 90
        theta_rad = np.deg2rad(theta)

        cam_ob.location = Vector((
            scene_center[0] + cam_radius * np.cos(theta_rad),
            scene_center[1] + cam_radius * np.sin(theta_rad),
            scene_center[2] + cam_radius * 0.5
        ))

        cam_ob.keyframe_insert(data_path="location", frame=frame)

    for frame in range(1, num_frames + 1):
        bpy.context.scene.frame_set(frame)

        direction = Vector(scene_center) - cam_ob.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_ob.rotation_euler = rot_quat.to_euler()

        cam_ob.keyframe_insert(data_path="rotation_euler", frame=frame)


def render_video():
    bpy.ops.render.render(animation=True)


# ---------------------------------------------------------------------
# LIGHTING
# ---------------------------------------------------------------------

def add_ceiling_light(name="CeilingLight", location=None, type='POINT', energy=100.0):
    max_z = float('-inf')
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for vertex in obj.bound_box:
                world_vertex = obj.matrix_world @ Vector(vertex)
                max_z = max(max_z, world_vertex.z)
                min_x = min(min_x, world_vertex.x)
                max_x = max(max_x, world_vertex.x)
                min_y = min(min_y, world_vertex.y)
                max_y = max(max_y, world_vertex.y)

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    light_data = bpy.data.lights.new(name=name, type=type)

    if type == 'AREA':
        light_data.size = 2.0

    light_object = bpy.data.objects.new(name=name, object_data=light_data)

    light_data.energy = energy
    light_data.color = (1, 0.95, 0.8)

    light_object.location = location if location else (center_x, center_y, max_z - 0.1)

    bpy.context.scene.collection.objects.link(light_object)

    print(
        f"Added ceiling light at coordinates: "
        f"({light_object.location.x}, {light_object.location.y}, {light_object.location.z})"
    )

    return light_object


def adjust_ceiling_light(name="CeilingLight", location=None):
    light = bpy.data.objects.get(name)

    if not light:
        print(f"Light '{name}' not found.")
        return None

    if location:
        light.location = location
        print(f"Adjusted light position to: {location}")

    return light


# ---------------------------------------------------------------------
# SCENE BOUNDS
# ---------------------------------------------------------------------

def get_scene_params():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

    found_mesh = False

    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            found_mesh = True

            for vertex in obj.bound_box:
                world_vertex = obj.matrix_world @ Vector(vertex)

                min_x = min(min_x, world_vertex.x)
                min_y = min(min_y, world_vertex.y)
                min_z = min(min_z, world_vertex.z)

                max_x = max(max_x, world_vertex.x)
                max_y = max(max_y, world_vertex.y)
                max_z = max(max_z, world_vertex.z)

    if not found_mesh:
        raise RuntimeError("No mesh objects found in scene. Cannot compute scene bounds.")

    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2

    print(f"scene_center=({center_x}, {center_y}, {center_z})")
    print(f"scene_size=({size_x}, {size_y}, {size_z})")

    return (center_x, center_y, center_z), (size_x, size_y, size_z)


# ---------------------------------------------------------------------
# WORKER
# ---------------------------------------------------------------------

class SceneRendererWorker:
    def __init__(
        self,
        resolution_x: int = 1920,
        resolution_y: int = 1080,
        samples: int = 100,
        frame_rate: int = 30,
        num_frames: int = 360,
        cuda: bool = True,
    ):
        self.resolution_x = resolution_x
        self.resolution_y = resolution_y
        self.samples = samples
        self.frame_rate = frame_rate
        self.num_frames = num_frames
        self.cuda = cuda

        self.scene_center = None
        self.scene_size = None

    def add_environment_texture(self):
        set_white_world_background(strength=1.0)

    def init(self, path):
        clear_scene()
        load_scene(path)

        apply_smooth_shading()
        set_clamp_factor_to_zero()

        cam_ob = initialize_camera()

        self.add_environment_texture()

        self.scene_center, self.scene_size = get_scene_params()

        return cam_ob

    def render(self, path, output_path, location=None, target=None):
        cam_ob = self.init(path)

        base_location = list(self.scene_center)
        base_target = list(self.scene_center)

        if location is not None:
            base_location = [base_location[i] + location[i] for i in range(3)]

        if target is not None:
            base_target = [base_target[i] + target[i] for i in range(3)]

        final_location = tuple(base_location)
        final_target = tuple(base_target)

        place_camera(cam_ob, final_location, final_target)

        setup_renderer(
            output_path=output_path,
            resolution_x=self.resolution_x,
            resolution_y=self.resolution_y,
            samples=self.samples,
            use_cuda=self.cuda,
            transparent=True,
        )

        render_image()

    def render_from_front(self, path, output_path):
        cam_ob = self.init(path)

        W, D, H = self.scene_size
        cx, cy, cz = self.scene_center

        dist = np.max([W, D, H])

        camera_location = (cx, cy - dist * 3.0, cz + H * 0.5)
        target_location = (cx, cy, cz)

        place_camera(cam_ob, camera_location, target_location)

        setup_renderer(
            output_path=output_path,
            resolution_x=self.resolution_x,
            resolution_y=self.resolution_y,
            samples=self.samples,
            use_cuda=self.cuda,
            transparent=True,
        )

        render_image()

    def render_from_top(self, path, output_path):
        cam_ob = self.init(path)

        W, D, H = self.scene_size
        cx, cy, cz = self.scene_center

        dist = np.max([W, D, H])

        camera_location = (cx, cy, cz + dist * 3.0)
        target_location = (cx, cy, cz)

        place_camera(cam_ob, camera_location, target_location)

        setup_renderer(
            output_path=output_path,
            resolution_x=self.resolution_x,
            resolution_y=self.resolution_y,
            samples=self.samples,
            use_cuda=self.cuda,
            transparent=True,
        )

        render_image()

    def render_from_corners(self, path, output_paths):
        cam_ob = self.init(path)

        W, D, H = self.scene_size
        cx, cy, cz = self.scene_center

        corners = [
            ((cx + 2 * W, cy - 2 * D, cz + 3 * H), (cx, cy, cz)),
            ((cx + 2 * W, cy + 2 * D, cz + 3 * H), (cx, cy, cz)),
            ((cx - 2 * W, cy + 2 * D, cz + 3 * H), (cx, cy, cz)),
            ((cx - 2 * W, cy - 2 * D, cz + 3 * H), (cx, cy, cz)),
        ]

        for i, (camera_location, target_location) in enumerate(corners):
            place_camera(cam_ob, camera_location, target_location)

            setup_renderer(
                output_path=output_paths[i],
                resolution_x=self.resolution_x,
                resolution_y=self.resolution_y,
                samples=self.samples,
                use_cuda=self.cuda,
                transparent=True,
            )

            render_image()

    def render_from_edge_midpoints(self, path, output_paths):
        cam_ob = self.init(path)

        W, D, H = self.scene_size
        cx, cy, cz = self.scene_center

        edges = [
            ((cx + 3 * W, cy, cz + 3 * H), (cx, cy, cz)),
            ((cx, cy + 3 * D, cz + 3 * H), (cx, cy, cz)),
            ((cx - 3 * W, cy, cz + 3 * H), (cx, cy, cz)),
            ((cx, cy - 3 * D, cz + 3 * H), (cx, cy, cz)),
        ]

        for i, (camera_location, target_location) in enumerate(edges):
            place_camera(cam_ob, camera_location, target_location)

            setup_renderer(
                output_path=output_paths[i],
                resolution_x=self.resolution_x,
                resolution_y=self.resolution_y,
                samples=self.samples,
                use_cuda=self.cuda,
                transparent=True,
            )

            render_image()

    def render_360(self, path, output_path):
        cam_ob = self.init(path)

        W, D, H = self.scene_size
        scene_center = self.scene_center

        cam_radius = 3 * np.sqrt((W / 2) ** 2 + (D / 2) ** 2)

        animate_camera(
            cam_ob=cam_ob,
            cam_radius=cam_radius,
            scene_center=scene_center,
            num_frames=self.num_frames,
        )

        setup_renderer_video(
            output_path=output_path,
            resolution_x=self.resolution_x,
            resolution_y=self.resolution_y,
            frame_rate=self.frame_rate,
            samples=self.samples,
            use_cuda=self.cuda,
        )

        render_video()


# ---------------------------------------------------------------------
# OPTIONAL CLI ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    """
    Example usage:

    blender -b --python render_cuda.py -- \
        --input /work/scene.blend \
        --output /work/output.png \
        --mode front

    Modes:
        front
        top
        corners
        edges
        360
    """

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True, help="Path to input .blend file")
    parser.add_argument("--output", required=True, help="Path to output image/video")
    parser.add_argument(
        "--mode",
        default="front",
        choices=["front", "top", "corners", "edges", "360", "custom"],
        help="Render mode",
    )
    parser.add_argument("--resolution_x", type=int, default=1920)
    parser.add_argument("--resolution_y", type=int, default=1080)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--frame_rate", type=int, default=30)
    parser.add_argument("--num_frames", type=int, default=360)
    parser.add_argument("--cpu", action="store_true", help="Use CPU instead of CUDA")

    # Blender passes its own args before "--".
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    args = parser.parse_args(argv)

    worker = SceneRendererWorker(
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        samples=args.samples,
        frame_rate=args.frame_rate,
        num_frames=args.num_frames,
        cuda=not args.cpu,
    )

    if args.mode == "front":
        worker.render_from_front(args.input, args.output)

    elif args.mode == "top":
        worker.render_from_top(args.input, args.output)

    elif args.mode == "corners":
        root, ext = os.path.splitext(args.output)
        output_paths = [
            f"{root}_corner_0{ext}",
            f"{root}_corner_1{ext}",
            f"{root}_corner_2{ext}",
            f"{root}_corner_3{ext}",
        ]
        worker.render_from_corners(args.input, output_paths)

    elif args.mode == "edges":
        root, ext = os.path.splitext(args.output)
        output_paths = [
            f"{root}_edge_0{ext}",
            f"{root}_edge_1{ext}",
            f"{root}_edge_2{ext}",
            f"{root}_edge_3{ext}",
        ]
        worker.render_from_edge_midpoints(args.input, output_paths)

    elif args.mode == "360":
        worker.render_360(args.input, args.output)

    elif args.mode == "custom":
        worker.render(args.input, args.output)