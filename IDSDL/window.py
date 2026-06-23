import os
import numpy as np
import trimesh
from sceneprogexec import SceneProgExec

CURTAIN_BUILDER_SCRIPT = """
import bpy
from sceneprogllm import LLM

class CurtainBuilder:
    def __init__(self, path, query, curtain_path):
        self.myllm = LLM(
            system_desc="Your task is to create a seamless, flat texture pattern designed for curtain fabric, viewed from directly above, with no folds or shadows, showing only the fabric's surface pattern, suitable for use as a Blender material map.",
            response_format="image",
        )
        self.curtain_path = curtain_path
        self.path = path
        self.query = query

    def __call__(self):
        image = self.myllm(f"Create a curtain texture for the following query: {self.query}")
        import os
        os.makedirs("tmp/", exist_ok=True)
        image_path = "tmp/curtain_texture.png"
        image.save(image_path)
        curtain_obj, rod_obj = self.apply_texture_to_curtain(self.curtain_path, image_path)
        self.export_objs_as_glb([curtain_obj, rod_obj], self.path)

    def apply_texture_to_curtain(self, glb_path, image_path, curtain_name="curtain", rod_name="rod"):
        bpy.ops.import_scene.gltf(filepath=glb_path)

        curtain_obj = None
        rod_obj = None

        for obj in bpy.context.selected_objects:
            name = obj.name.lower()
            if curtain_name in name:
                curtain_obj = obj
            elif rod_name in name:
                rod_obj = obj

        mesh = curtain_obj.data
        mat = bpy.data.materials.new(name="Curtain_Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        tex_image = nodes.new("ShaderNodeTexImage")
        tex_image.image = bpy.data.images.load(image_path)
        links.new(tex_image.outputs["Color"], bsdf.inputs["Base Color"])

        if len(mesh.materials) > 0:
            mesh.materials[0] = mat
        else:
            mesh.materials.append(mat)

        return curtain_obj, rod_obj

    def export_objs_as_glb(self, objs, export_path):
        bpy.ops.object.select_all(action="DESELECT")
        valid_objs = [obj for obj in objs if obj is not None]
        for obj in valid_objs:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = valid_objs[0]

        bpy.ops.export_scene.gltf(
            filepath=export_path,
            export_format="GLB",
            use_selection=True,
            export_apply=True
        )
"""


class Curtain:
    def __init__(self, mesh_path):
        self.mesh_path = mesh_path

    def __repr__(self):
        return f"Curtain(mesh_path={self.mesh_path!r})"


class SceneProgObjectWall:
    def __init__(self, WIDTH, HEIGHT, DEPTH):
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.DEPTH = DEPTH
        self.mesh = None

    def get_uid(self):
        import random
        os.makedirs("tmp", exist_ok=True)
        return random.randint(1000, 9999)

    def transform_position(self, position, wall):
        if wall.name == "back_wall":
            return position[0], position[1], position[2]
        elif wall.name == "left_wall":
            return position[2], position[1], position[0]
        elif wall.name == "front_wall":
            return position[0], position[1], self.DEPTH - position[2]
        elif wall.name == "right_wall":
            return self.WIDTH - position[2], position[1], position[0]
        else:
            raise ValueError(f"Unknown wall name: {wall.name}")

    def translate(self, mesh, translation):
        translation = np.asarray(translation, dtype=np.float32)
        vertices = mesh.vertices
        center = np.mean(vertices, axis=0)
        vertices -= center
        vertices += translation
        mesh.vertices = vertices
        return mesh

    def rotate(self, mesh, wall):
        def rot(mesh, angle):
            from scipy.spatial.transform import Rotation as R
            rotation = R.from_euler("y", angle, degrees=True)
            T = np.eye(4, dtype=np.float32)
            T[:3, :3] = rotation.as_matrix()
            mesh.apply_transform(T)

        if wall.name == "back_wall":
            rot(mesh, 0)
        elif wall.name == "left_wall":
            rot(mesh, 270)
        elif wall.name == "front_wall":
            rot(mesh, 180)
        elif wall.name == "right_wall":
            rot(mesh, 270)
        else:
            raise ValueError(f"Unknown wall name: {wall.name}")
        return mesh

    def scale(self, mesh, width, height, scale_depth=False):
        if width <= 0 or height <= 0:
            raise ValueError(f"width and height must be positive, got width={width}, height={height}")

        vertices = mesh.vertices
        vertices[:, 0] -= np.min(vertices[:, 0])
        vertices[:, 1] -= np.min(vertices[:, 1])

        max_x = np.max(vertices[:, 0])
        max_y = np.max(vertices[:, 1])

        if max_x <= 0:
            raise ValueError("Cannot scale mesh: x extent is zero.")
        if max_y <= 0:
            raise ValueError("Cannot scale mesh: y extent is zero.")

        vertices[:, 0] *= width / max_x
        vertices[:, 1] *= height / max_y

        if scale_depth:
            max_z = np.max(vertices[:, 2])
            if max_z <= 0:
                raise ValueError("Cannot scale mesh depth: z extent is zero.")
            vertices[:, 2] *= 0.05 / max_z

        mesh.vertices = vertices
        return mesh

    def cut_wall(self, wall):
        if self.mesh is None:
            raise ValueError("self.mesh is None. Cannot cut wall before mesh has been created.")

        window_vertices = self.mesh.vertices

        if wall.name in ["left_wall", "right_wall"]:
            x_coords = window_vertices[:, 2]
            y_coords = window_vertices[:, 1]
        else:
            x_coords = window_vertices[:, 0]
            y_coords = window_vertices[:, 1]

        x_min, x_max = np.min(x_coords), np.max(x_coords)
        y_min, y_max = np.min(y_coords), np.max(y_coords)

        dx = wall.width / wall.nx
        dy = wall.height / wall.ny

        i_min = max(0, int(x_min / dx)) + 1
        i_max = min(wall.nx - 1, int(x_max / dx)) - 1
        j_min = max(0, int(y_min / dy)) + 1
        j_max = min(wall.ny - 1, int(y_max / dy)) - 1

        for i in range(i_min, i_max + 1):
            for j in range(j_min, j_max + 1):
                wall.holes.add((i, j))


class Window(SceneProgObjectWall):
    def __init__(self, WIDTH, HEIGHT, DEPTH):
        super().__init__(WIDTH, HEIGHT, DEPTH)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "assets")

        self.floor_to_ceiling_window_path = os.path.join(assets_dir, "window_tofloor.obj")
        self.picture_window_path = os.path.join(assets_dir, "window_picture.obj")
        self.standard_window_path = os.path.join(assets_dir, "window_dropdown.obj")
        self.curtain_path = os.path.join(assets_dir, "curtain.glb")

        self.window_types = ["floor_to_ceiling", "picture", "standard"]

        uid = self.get_uid()
        self.mesh_path = f"tmp/window{uid}.glb"
        self.curtain_path_instance = f"tmp/curtain{uid}.glb"
        self.exec = SceneProgExec()

    def add_window_floor_to_ceiling(self, wall, curtain_texture=None):
        wall_width, wall_height = wall.width, wall.height

        def compute_width(width, max_width):
            num = max(1, int(np.round(width / max_width)))
            return int((width / num) * 100) / 100, int(num)

        def assemble_windows(width, height, max_width=1.5):
            width_, num = compute_width(width, max_width)
            mesh = trimesh.load(self.floor_to_ceiling_window_path, process=False, force="mesh")
            vertices = mesh.vertices.copy()
            vertices[:, 0] *= width_ * 2
            vertices[:, 1] *= height
            mesh = trimesh.Trimesh(vertices=vertices, faces=mesh.faces, process=False)

            meshes = []
            for i in range(num):
                mesh2 = mesh.copy()
                mesh2.apply_translation([width_ * i, 0, 0])
                meshes.append(mesh2)

            return trimesh.util.concatenate(meshes)

        if wall.name in ["left_wall", "right_wall"]:
            self.mesh = assemble_windows(self.DEPTH, wall_height, max_width=1.5)
        else:
            self.mesh = assemble_windows(wall_width, wall_height, max_width=1.5)

        self.mesh = self.rotate(self.mesh, wall)
        pos = (wall_width / 2, wall_height / 2, 0)
        pos = self.transform_position(pos, wall)
        self.mesh = self.translate(self.mesh, pos)
        self.mesh.export(self.mesh_path)

        mesh = self.add_curtain(curtain_texture)
        mesh = self.scale(mesh, 0.98 * wall_width, 0.98 * wall_height)
        mesh = self.rotate(mesh, wall)
        pos = (wall_width / 2, wall_height / 2, 0)
        pos = (pos[0], pos[1] + 0.2, 0.1)
        pos = self.transform_position(pos, wall)
        mesh = self.translate(mesh, pos)
        if wall.name in ["left_wall"]:
            mesh.invert()
        mesh.export(self.curtain_path_instance)

        return self, Curtain(self.curtain_path_instance)

    def add_window_picture(self, wall, curtain_texture=None):
        wall_width, wall_height = wall.width, wall.height
        self.mesh = trimesh.load(self.picture_window_path, process=False, force="mesh")

        window_height = wall_height - 1.2
        if wall_width <= 0 or window_height <= 0:
            raise ValueError(f"Invalid picture window dimensions: width={wall_width}, height={window_height}")

        self.mesh = self.scale(self.mesh, 0.8 * wall_width, window_height, scale_depth=True)
        self.mesh = self.rotate(self.mesh, wall)

        pos = (wall_width / 2, 0.6 + window_height / 2, 0)
        pos = self.transform_position(pos, wall)
        self.mesh = self.translate(self.mesh, pos)
        self.mesh.export(self.mesh_path)

        self.cut_wall(wall)

        mesh = self.add_curtain(curtain_texture)
        mesh = self.scale(mesh, 0.8 * wall_width + 0.4, 1.1 * window_height)
        mesh = self.rotate(mesh, wall)
        pos = (wall_width / 2, 0.6 + window_height / 2, 0)
        pos = (pos[0], pos[1] + 0.1, 0.1)
        pos = self.transform_position(pos, wall)
        mesh = self.translate(mesh, pos)
        if wall.name in ["left_wall"]:
            mesh.invert()
        mesh.export(self.curtain_path_instance)

        return self, Curtain(self.curtain_path_instance)

    def add_window_standard(self, wall, position, curtain_texture=None):
        window_width, window_height = wall.get_partition_dimensions_by_label(position, margin=0.05)
        if window_width <= 0 or window_height <= 0:
            raise ValueError(f"Invalid standard window dimensions at {position}: width={window_width}, height={window_height}")

        self.mesh = trimesh.load(self.standard_window_path, process=False, force="mesh")
        self.mesh = self.scale(self.mesh, window_width, window_height, scale_depth=True)
        self.mesh = self.rotate(self.mesh, wall)

        pos = wall.get_partition_center_by_label(position, margin=0.05)
        pos = (pos[0], pos[1], 0)
        pos = self.transform_position(pos, wall)

        self.mesh = self.translate(self.mesh, pos)
        self.mesh.export(self.mesh_path)

        self.cut_wall(wall)

        mesh = self.add_curtain(curtain_texture)
        mesh = self.scale(mesh, 1.1 * window_width, 1.1 * window_height)
        mesh = self.rotate(mesh, wall)
        pos = wall.get_partition_center_by_label(position, margin=0.05)
        pos = (pos[0], pos[1] - 0.05, 0.08)
        pos = self.transform_position(pos, wall)
        mesh = self.translate(mesh, pos)
        if wall.name in ["left_wall"]:
            mesh.invert()
        mesh.export(self.curtain_path_instance)

        return self, Curtain(self.curtain_path_instance)

    def add_curtain(self, texture=None):
        if texture:
            to_run = f"""
{CURTAIN_BUILDER_SCRIPT}
curtain_builder = CurtainBuilder("{self.curtain_path_instance}", {repr(texture)}, {repr(self.curtain_path)})
curtain_builder()
"""
            self.exec(to_run)
            path = self.curtain_path_instance
        else:
            path = self.curtain_path

        mesh = trimesh.load(path, process=False, force="mesh")
        return mesh