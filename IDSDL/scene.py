import os
import numpy as np
from IDSDL.object import SceneProgObject
from sceneprogexec import SceneProgExec
from IDSDL.datasets.retrievers import SceneProgAssetRetriever
from IDSDL.groups import *
from IDSDL.groups_extra import (
    StackGroup, PyramidGroup, PileGroup, SymmetryGroup, FacingGroup, RingsGroup,
)


class SceneProgRoom:
    def __init__(self, name, seed=None):
        self.name = name
        self.objects = []
        self.walls = []
        self.wall_objects = []
        self.unique_assets = {}
        self.ceiling_lights = []
        self.exec = SceneProgExec()
        self.object_retriever = SceneProgAssetRetriever(seed=seed)
        self.vlm_feedback = ""
        self.HEIGHT = 4

    # ----------------------------
    # asset registration
    # ----------------------------
    def register_asset(self, mesh_path):
        """
        Keep track of mesh files only once.
        """
        if mesh_path not in self.unique_assets:
            name = os.path.splitext(os.path.basename(mesh_path))[0]
            self.unique_assets[mesh_path] = name.replace("-", "_").replace(" ", "_")

    # ----------------------------
    # object creation
    # ----------------------------
    def add_asset(self, path, scale, description):
        obj = SceneProgObject(self)
        obj.load(mesh_path=path)
        obj.scale(scale)
        obj.description = description
        return obj

    def AddAsset(self, description: str, modulate_scale: float = 1.0, width=None, depth=None):
        path, scale = self.object_retriever(description)
        scale = scale * modulate_scale

        obj = self.add_asset(path, scale, description)

        if width is not None:
            obj.scale_only_width(width)
        if depth is not None:
            obj.scale_only_depth(depth)

        return obj

    # ----------------------------
    # scene category helpers
    # ----------------------------
    def _append_unique(self, container, item):
        if item not in container:
            container.append(item)

    def add_wall(self, wall):
        self._append_unique(self.walls, wall)

    def add_wall_object(self, obj):
        self._append_unique(self.wall_objects, obj)

    def add_ceiling_light(self, obj):
        self._append_unique(self.ceiling_lights, obj)

    def clear_objects(self):
        self.objects = []

    def clear_walls(self):
        self.walls = []

    def clear_wall_objects(self):
        self.wall_objects = []

    def clear_ceiling_lights(self):
        self.ceiling_lights = []

    # ----------------------------
    # object binding
    # ----------------------------
    def _append_unique_object(self, obj):
        self._append_unique(self.objects, obj)

    def _collect_leaf_objects(self, obj):
        if isinstance(obj, list):
            leaf_objects = []
            for o in obj:
                leaf_objects.extend(self._collect_leaf_objects(o))
            return leaf_objects

        if not isinstance(obj, SceneProgObject):
            raise TypeError(f"Expected SceneProgObject or list, got {type(obj)}")

        if len(obj.children) == 0:
            return [obj]

        return obj.get_children()

    def bind(self, obj):
        leaf_objects = self._collect_leaf_objects(obj)
        for leaf in leaf_objects:
            self._append_unique_object(leaf)

    # ----------------------------
    # group factories
    # ----------------------------
    def RelativeGroup(self):
        return RelativeGroup(self)

    def AroundGroup(self, sparsity: float = 0.0):
        return AroundGroup(self, sparsity=sparsity)

    def GridGroup(self, sparsity: float = 0.0, randomness: float = 0.0):
        return GridGroup(self, sparsity=sparsity, randomness=randomness)

    # --- additional motif groups (IDSDL/groups_extra.py) ---
    def StackGroup(self):
        return StackGroup(self)

    def PyramidGroup(self):
        return PyramidGroup(self)

    def PileGroup(self):
        return PileGroup(self)

    def SymmetryGroup(self):
        return SymmetryGroup(self)

    def FacingGroup(self):
        return FacingGroup(self)

    def RingsGroup(self, sparsity: float = 0.0):
        return RingsGroup(self, sparsity=sparsity)

    def RoomGroup(self, modulate_scale: float = 1.0):
        return RoomGroup(self, modulate_scale)

    def SentenceASCIIGenerator(self):
        return SentenceASCIIGenerator(self)

    def BasicRoomGroup(self, width, depth, height):
        return BasicRoomGroup(self, width, depth, height)

    # ----------------------------
    # debugging helpers
    # ----------------------------
    def describe_scene(self):
        lines = [
            f"name={self.name}",
            f"objects={len(self.objects)}",
            f"walls={len(self.walls)}",
            f"wall_objects={len(self.wall_objects)}",
            f"ceiling_lights={len(self.ceiling_lights)}",
            f"unique_assets={len(self.unique_assets)}",
        ]
        return "\n".join(lines)

    # ----------------------------
    # export
    # ----------------------------
    def export(self, target: str = "scene.blend"):
        lines = f"""
import bpy
import os

def assign_generated_texture(obj, image_path, scale=(1.0, 1.0, 1.0), material_name="GeneratedTexture"):
    try:
        image = bpy.data.images.load(image_path)
    except Exception as e:
        print(f"Could not load image {{image_path}}: {{e}}")
        return

    mat = bpy.data.materials.new(name=material_name)
    mat.use_nodes = True
    mat.blend_method = 'OPAQUE'
    mat.use_backface_culling = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex_image = nodes.new("ShaderNodeTexImage")
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")

    tex_image.image = image
    tex_image.projection = 'BOX'  # Use box projection for better coverage
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_image.inputs['Vector'])
    links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    mapping.inputs['Scale'].default_value = scale

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

# Clear all existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

mesh_lookup = {{}}
"""
        for path, name in self.unique_assets.items():
            lines += f"""
# Import mesh: {name}
bpy.ops.import_scene.gltf(filepath=r'{path}')
imported_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
assert imported_objs, "No mesh found for {name}"
mesh_obj = imported_objs[0]
mesh_obj.name = '{name}_MESH'
mesh_lookup['{name}'] = mesh_obj.data

# Center origin
bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
mesh_obj.hide_set(True)
mesh_obj.hide_render = True
"""

        for i, obj in enumerate(self.objects):
            if obj.mesh_path not in self.unique_assets:
                raise ValueError(f"Object mesh path not registered: {obj.mesh_path}")

            mesh_key = self.unique_assets[obj.mesh_path]
            obj_name = str(i)
            translation, rotation_euler, scale = obj.get_state_info()

            rot_rad = np.radians(rotation_euler)
            lines += f"""
# Instance: {obj_name}
obj = bpy.data.objects.new('{obj_name}', mesh_lookup['{mesh_key}'])
bpy.context.collection.objects.link(obj)
obj.location = [{translation[0]}, -{translation[2]}, {translation[1]}]
obj.rotation_euler = (0, 0, {rot_rad})
obj.scale = [{scale[0]}, {scale[2]}, {scale[1]}]
"""
            if obj in self.ceiling_lights:
                w, h, d = obj.get_whd()
                lines += f"""
# Create a new area light
light_data = bpy.data.lights.new(name='{obj_name}_Light', type='AREA')
light_data.energy = 500       # Strength in watts
light_data.shape = 'RECTANGLE'  # Or 'SQUARE'
light_data.size = {w}          # Width (if RECTANGLE, this is X)
light_data.size_y = {d}        # Height (only used for RECTANGLE)

# Create a new light object
light_object = bpy.data.objects.new(name="{obj_name}_Light", object_data=light_data)

# Set light location
light_object.location = [{translation[0]}, -{translation[2]}, {self.HEIGHT}]  # X, Y, Z

# Link light to the current scene
bpy.context.collection.objects.link(light_object)
"""

        os.makedirs("tmp", exist_ok=True)

        for wall in self.walls:
            wall._rebuild()
            import random
            uid = random.randint(1000, 9999)
            mesh_path = f"tmp/{wall.name}_{uid}.glb"
            try:
                wall.export(mesh_path)
            except Exception:
                continue

            texture_path = wall.texture_path
            res = wall.res
            lines += f"""
# Wall: {wall.name}
bpy.ops.import_scene.gltf(filepath=r'{mesh_path}')
wall_obj = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH'][0]
wall_obj.name = '{wall.name}'
assign_generated_texture(
    wall_obj,
    image_path=r'{texture_path}',
    scale=({res}, {res}, {res}),
    material_name='{wall.name}_mat'
)
"""

        for obj in self.wall_objects:
            lines += f"""
bpy.ops.import_scene.gltf(filepath=r'{obj.mesh_path}')
"""

        lines += """
# Pack all external images/textures into the .blend file so it is self-contained
bpy.ops.file.pack_all()
"""

        self.exec(lines, target, verbose=True)
        # self.renderer.render_from_edge_midpoints(target, output_paths=['tmp/right.png', 'tmp/back.png', 'tmp/left.png', 'tmp/front.png'])

# from scene import SceneProgRoom
# from object import SceneProgObject


def main():
    room = SceneProgRoom("group_test_scene")

    sofa = room.AddAsset("a modern gray sofa")
    coffee_table = room.AddAsset("a wooden coffee table")
    side_table = room.AddAsset("a small round side table")

    living_group = SceneProgObject(room, name="living_group")
    living_group.add_child([sofa, coffee_table, side_table])

    sofa.set_location(0.0, 0.0, 0.0)
    coffee_table.set_location(0.0, 0.0, 1.5)
    side_table.set_location(1.5, 0.0, 0.3)

    room.bind(living_group)

    print("=== Scene Summary ===")
    print(room.describe_scene())
    print()

    print("=== Group Tree ===")
    print(living_group.describe_tree())
    print()

    room.export("group_test_scene.blend")
    print("Exported to group_test_scene.blend")


if __name__ == "__main__":
    main()