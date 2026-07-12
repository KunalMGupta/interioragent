import os
import json
import time
import random
import numpy as np
from IDSDL.object import SceneProgObject
from sceneprogexec import SceneProgExec
from IDSDL.datasets.retrievers import SceneProgAssetRetriever
from IDSDL.groups import *
from IDSDL.groups_extra import (
    StackGroup, PyramidGroup, PileGroup, SymmetryGroup, FacingGroup, RingsGroup,
    MirrorStationGroup, WorkstationGroup,
)


class SceneProgRoom:
    # Vanities are complete "set" assets (cabinet+sink+mirror) whose dataset scale metadata is
    # unreliable. Each is hand-tagged in datasets/assets/vanity_types.json with a type that maps
    # to a real width + mount; AddAsset applies this transparently (no helper/import at call sites).
    _VANITY_SPEC = {
        "floating":   {"w": 0.80, "mount": "wall",  "bottom": 0.40},
        "single":     {"w": 0.70, "mount": "floor", "bottom": 0.0},
        "double":     {"w": 1.50, "mount": "floor", "bottom": 0.0},
        "extra_wide": {"w": 2.10, "mount": "floor", "bottom": 0.0},
    }
    _vanity_tags_cache = None

    @classmethod
    def _vanity_tags(cls):
        if cls._vanity_tags_cache is None:
            path = os.path.join(os.path.dirname(__file__), "datasets", "assets", "vanity_types.json")
            try:
                with open(path) as f:
                    cls._vanity_tags_cache = json.load(f)
            except FileNotFoundError:
                cls._vanity_tags_cache = {}
        return cls._vanity_tags_cache

    def _apply_vanity_metadata(self, obj):
        """If `obj` is a hand-tagged vanity, size it to its real width (UNIFORM scale, so the mesh's
        proportions are preserved) and stash its mount height on the object, so wall placement floats
        wall-hung/floating vanities and floor-rests the rest. Transparent: callers just AddAsset a
        vanity and place it — no separate module, no `bottom=`."""
        tag = self._vanity_tags().get(getattr(obj, "retrieval_model", None))
        if not tag:
            return
        spec = self._VANITY_SPEC.get(tag.get("type"), self._VANITY_SPEC["double"])
        w = tag.get("width_m") or spec["w"]
        w0, h0, d0 = obj.get_width(), obj.get_height(), obj.get_depth()
        f = w / max(w0, 1e-6)
        obj.scale_only_width(w0 * f); obj.scale_only_height(h0 * f); obj.scale_only_depth(d0 * f)
        obj.mount_bottom = spec["bottom"]

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

        # Placement randomness (group jitter) is reproducible when the scene is
        # seeded: each group draws its own RNG from the scene seed via _make_rng(),
        # so the same seed reproduces the same jittered layout, and an unseeded
        # scene gets fresh entropy each run. Groups are seeded in creation order.
        self.seed = seed
        self._rng_counter = 0

        # Unique per-run scratchpad under tmp/. Every intermediate (group
        # blends, wall meshes) and rendering (VLM views, RoomGroup interior
        # views) for this run is written here, so a run's outputs are isolated
        # and can be browsed afterwards to inspect quality.
        run_id = f"{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}_{random.randint(0, 0xFFFF):04x}"
        self.run_dir = os.path.join("tmp", run_id)

    def _make_rng(self):
        """A per-group numpy RNG. Derived from the scene seed (reproducible) when set,
        else fresh entropy. Advances a counter so distinct groups get distinct streams."""
        if self.seed is None:
            return np.random.default_rng()
        rng = np.random.default_rng([int(self.seed), self._rng_counter])
        self._rng_counter += 1
        return rng

    def run_subdir(self, name=""):
        """Return (creating if needed) a subdirectory of this run's scratchpad."""
        path = os.path.join(self.run_dir, name) if name else self.run_dir
        os.makedirs(path, exist_ok=True)
        return path

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

    def AddAsset(self, description: str, modulate_scale: float = 1.0, width=None, depth=None,
                 asset_id: str = None):
        # asset_id pins a specific dataset asset (e.g. "hssd/<id>"), bypassing the
        # agentic visual selection — the durable, recompile-safe override.
        path, scale = self.object_retriever(description, pin=asset_id)
        scale = scale * modulate_scale

        obj = self.add_asset(path, scale, description)

        # Retrieval provenance: the query, the candidates the picker saw, and the choice.
        obj.retrieval_query = description
        obj.retrieval_candidates = list(getattr(self.object_retriever, "last_candidates", []) or [])
        obj.retrieval_model = next(
            (c["model"] for c in obj.retrieval_candidates if c.get("chosen")), None
        )

        # set assets with type-driven sizing/mount (vanities) are handled transparently here
        self._apply_vanity_metadata(obj)

        if width is not None:
            obj.scale_only_width(width)
        if depth is not None:
            obj.scale_only_depth(depth)

        return obj

    def prefetch_assets(self, queries, max_workers=8):
        """Resolve a list of asset descriptions in parallel up front to warm the cache.

        Retrieval is network-bound, so calling this once with all of a scene's queries
        before the AddAsset calls turns N serial round-trips into one concurrent batch
        (subsequent AddAsset(...) then hit the warm cache). Needs a seeded scene.
        """
        return self.object_retriever.prefetch(queries, max_workers=max_workers)

    def reselect_asset(self, obj, choice):
        """Swap obj to a different retrieval candidate (override the auto pick).

        ``choice`` is an index into ``obj.retrieval_candidates`` or a model id. This is a
        convenience post-hoc swap — recompile the owning group/scene afterward. For a
        durable override prefer ``AddAsset(..., asset_id=...)``.
        """
        cands = getattr(obj, "retrieval_candidates", None) or []
        if isinstance(choice, int):
            cand = cands[choice]
        else:
            cand = next((c for c in cands if c["model"] == choice or choice in c["model"]), None)
            if cand is None:
                raise ValueError(f"no retrieval candidate matching {choice!r}")
        obj.load(mesh_path=cand["path"])
        obj.scale(cand["scale"])
        if getattr(obj, "retrieval_query", None):
            obj.description = obj.retrieval_query
        obj.retrieval_model = cand["model"]
        for c in cands:
            c["chosen"] = (c["model"] == cand["model"])
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

    def AroundGroup(self, sparsity: float = 0.0, jitter: float = 0.0):
        return AroundGroup(self, sparsity=sparsity, jitter=jitter)

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

    def MirrorStationGroup(self, max_top=None):
        return MirrorStationGroup(self, max_top=max_top)

    def WorkstationGroup(self):
        return WorkstationGroup(self)

    def RoomGroup(self, modulate_scale: float = 1.0, randomness: float = 0.0,
                  auto_render: bool = True,
                  render_dir=None, render_resolution=(1280, 900), render_samples=48,
                  max_height: float = 3.0, auto_clearances: bool = True):
        return RoomGroup(
            self,
            modulate_scale=modulate_scale,
            randomness=randomness,
            auto_render=auto_render,
            render_dir=render_dir,
            render_resolution=render_resolution,
            render_samples=render_samples,
            max_height=max_height,
            auto_clearances=auto_clearances,
        )

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
            # Mesh-less helper objects (e.g. the invisible door-clearance proxy) take part
            # in the layout solve but carry no geometry — skip them in serialization, as
            # _build_blend already does.
            if obj.mesh_path is None:
                continue
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

        run_dir = self.run_subdir()

        for wall in self.walls:
            wall._rebuild()
            uid = random.randint(1000, 9999)
            mesh_path = os.path.join(run_dir, f"{wall.name}_{uid}.glb")
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