import os
import random
import matplotlib.pyplot as plt
from sceneprogexec import SceneProgExec
from IDSDL.renderer.renderer import SceneRenderer

import trimesh
import inspect
from functools import wraps
import numpy as np
from scipy.spatial.transform import Rotation as R
from IDSDL.constraints import CONSTRAINTS, GradSolver, VLMSolver


class Transform:
    def __init__(self):
        self.mat = np.eye(4, dtype=np.float32)
        self.translation = np.zeros(3, dtype=np.float32)
        self.rotation = 0.0   # yaw in degrees
        self.scale = np.ones(3, dtype=np.float32)
        self._dirty = True

    def set_translation(self, translation):
        self.translation = np.array(translation, dtype=np.float32)
        self._dirty = True

    def set_rotation(self, rotation):
        self.rotation = float(rotation)
        self._dirty = True

    def set_scale(self, scale):
        self.scale = np.array(scale, dtype=np.float32)
        self._dirty = True

    def copy(self):
        new_transform = Transform()
        new_transform.mat = self.mat.copy()
        new_transform.translation = self.translation.copy()
        new_transform.rotation = self.rotation
        new_transform.scale = self.scale.copy()
        new_transform._dirty = self._dirty
        return new_transform

    def compute_matrix(self):
        if not self._dirty:
            return self.mat

        S = np.diag(np.append(self.scale, 1.0)).astype(np.float32)

        Rmat = R.from_euler("y", self.rotation, degrees=True).as_matrix().astype(np.float32)
        R4 = np.eye(4, dtype=np.float32)
        R4[:3, :3] = Rmat

        T = np.eye(4, dtype=np.float32)
        T[:3, 3] = self.translation

        self.mat = T @ R4 @ S
        self._dirty = False
        return self.mat

    def __str__(self):
        return str(self.compute_matrix())

    def __repr__(self):
        return (
            f"Transform(translation={self.translation}, "
            f"rotation={self.rotation}, scale={self.scale})"
        )

    def transform_points(self, points):
        mat = self.compute_matrix()

        points = np.asarray(points, dtype=np.float32)
        if points.shape == (3,):
            points = points.reshape(1, 3)

        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("points must have shape (3,) or (N, 3)")

        homog = np.hstack([points, np.ones((points.shape[0], 1), dtype=np.float32)])
        transformed = (mat @ homog.T).T
        return transformed[:, :3]

    def transform_directions(self, directions):
        mat = self.compute_matrix().copy()
        mat[:3, 3] = 0.0

        directions = np.asarray(directions, dtype=np.float32)
        if directions.shape == (3,):
            directions = directions.reshape(1, 3)

        if directions.ndim != 2 or directions.shape[1] != 3:
            raise ValueError("directions must have shape (3,) or (N, 3)")

        homog = np.hstack([directions, np.ones((directions.shape[0], 1), dtype=np.float32)])
        transformed = (mat @ homog.T).T
        return transformed[:, :3]

    def apply(self, vertices, no_translation=False):
        if no_translation:
            return self.transform_directions(vertices)
        return self.transform_points(vertices)

    def __matmul__(self, other):
        if not isinstance(other, Transform):
            raise TypeError("Can only multiply with another Transform")

        combined = Transform()
        combined.mat = self.compute_matrix() @ other.compute_matrix()
        combined._dirty = False
        combined.translation, combined.rotation, combined.scale = combined.decompose_matrix()
        return combined

    def decompose_matrix(self):
        mat = self.compute_matrix()

        RS = mat[:3, :3]
        scale = np.linalg.norm(RS, axis=0)
        scale = np.where(scale == 0, 1e-8, scale)

        Rmat = RS / scale

        sin_y = Rmat[0, 2]
        cos_y = Rmat[2, 2]
        angle_rad = np.arctan2(sin_y, cos_y)
        angle_deg = np.degrees(angle_rad)

        translation = mat[:3, 3]
        return translation, angle_deg, scale


class Operation:
    def __init__(self, func, *args, singleton=False, stage="main", **kwargs):
        self.func = func
        self.singleton = singleton
        self.stage = stage

        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        self.arguments = dict(bound.arguments)

        self.name = func.__name__
        self.obj = self._detect_main_obj()
        self.facing = self.arguments.get("facing", None)

    def _detect_main_obj(self):
        for key in ["obj", "objects"]:
            val = self.arguments.get(key)
            if isinstance(val, SceneProgObject):
                return val
        return None

    def __getattr__(self, item):
        if item in self.arguments:
            return self.arguments[item]
        raise AttributeError(f"'Operation' object has no attribute '{item}'")

    def __repr__(self):
        arg_str = ", ".join(f"{k}={v!r}" for k, v in self.arguments.items())
        return (
            f"<Operation: {self.name}("
            f"{arg_str}"
            f"), stage={self.stage!r}, singleton={self.singleton}>"
        )

    def execute(self):
        return self.func(**self.arguments)


def placemethod(_func=None, *, singleton=False, stage="main"):
    def decorator(func):
        @wraps(func)
        def wrapper(self_obj, *args, **kwargs):
            original_func = wrapper._original_function

            sig = inspect.signature(original_func)
            bound = sig.bind(self_obj, *args, **kwargs)
            bound.apply_defaults()

            op = Operation(
                original_func,
                *bound.args,
                singleton=singleton,
                stage=stage,
                **bound.kwargs,
            )

            self_obj.add_operation(op)

        wrapper._original_function = func
        wrapper._is_place_method = True
        wrapper._place_singleton = singleton
        wrapper._place_stage = stage
        return wrapper

    if _func is None:
        return decorator
    return decorator(_func)


class SceneProgObject:
    _zone_stack = []

    def __enter__(self):
        self.__class__._zone_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.compile()
        self.recenter()
        self.__class__._zone_stack.pop()

    def __str__(self):
        return self.get_descriptions()

    def __repr__(self):
        return f"SceneProgObject(name={self.name!r}, children={len(self.children)}, mesh_path={self.mesh_path!r})"

    def __init__(self, scene=None, name=None):
        self.scene = scene
        self.name = name or self.__class__.__name__

        self.T0 = Transform()
        self.transform = Transform()
        self.parent = None
        self.children = []
        self.anchor = None

        self.vertices = None
        self.faces = None
        self.mesh_path = None
        self.description = None
        self.ignore_overlap = False

        self.operations = []

        self.is_compiled = False
        self.compile_log = []
        self.last_compile_report = None

        self.grad = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        self.constraints = []
        self.grad_constraints = []
        self.vlm_constraints = []
        self.is_frozen_group = False
        
        for constraint_cls in CONSTRAINTS:
            self._add_constraint_method(constraint_cls)

        self.grad_solver = GradSolver(self)
        self.vlm_solver = VLMSolver(self)

    # ----------------------------
    # dynamic constraint binding
    # ----------------------------
    def _add_constraint_method(self, constraint_cls):
        def method(this, *args, **kwargs):
            constraint_instance = constraint_cls(this, *args, **kwargs)
            if constraint_instance not in this.constraints:
                this.constraints.append(constraint_instance)
            return constraint_instance

        setattr(self, constraint_cls.__name__, method.__get__(self))

    # ----------------------------
    # constraint bookkeeping helpers
    # ----------------------------
    def clear_constraints(self):
        self.constraints = []
        self.grad_constraints = []
        self.vlm_constraints = []

    def describe_constraints(self):
        lines = [
            f"constraints={len(self.constraints)}",
            f"grad_constraints={len(self.grad_constraints)}",
            f"vlm_constraints={len(self.vlm_constraints)}",
        ]
        return "\n".join(lines)

    # ----------------------------
    # copy helpers
    # ----------------------------
    def __rmul__(self, n):
        if isinstance(n, int):
            return self.copy(num=n)
        raise TypeError(f"Unsupported multiplier type: {type(n)}")

    def _copy_constructor_kwargs(self):
        sig = inspect.signature(self.__class__.__init__)
        kwargs = {}

        aliases = {
            "width": "WIDTH",
            "depth": "DEPTH",
            "height": "HEIGHT",
        }

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            if name == "scene":
                kwargs[name] = self.scene
            elif name == "name":
                kwargs[name] = self.name
            elif hasattr(self, name):
                kwargs[name] = getattr(self, name)
            elif name in aliases and hasattr(self, aliases[name]):
                kwargs[name] = getattr(self, aliases[name])
            elif param.default is not inspect._empty:
                continue
            else:
                raise TypeError(
                    f"Cannot auto-copy constructor arg '{name}' for {self.__class__.__name__}"
                )

        return kwargs

    def copy(self, num=1):
        objs = []

        for _ in range(num):
            new_obj = self.__class__(**self._copy_constructor_kwargs())

            # Copy realized object state only; operations/constraints are not copied.
            new_obj.T0 = self.T0.copy()
            new_obj.transform = self.transform.copy()
            new_obj.is_compiled = self.is_compiled
            new_obj.is_frozen_group = self.is_frozen_group
            new_obj.operations = []
            new_obj.clear_constraints()

            if self.vertices is not None:
                new_obj.vertices = self.vertices.copy()

            if self.faces is not None:
                new_obj.faces = self.faces.copy()

            if self.mesh_path is not None:
                new_obj.mesh_path = self.mesh_path

            if self.description is not None:
                new_obj.description = self.description

            new_obj.ignore_overlap = self.ignore_overlap

            children_to_copy = [child for child in self.children if child is not self.anchor]

            for child in children_to_copy:
                child_copy = child.copy()
                new_obj.add_child(child_copy)

            if self.anchor is not None:
                new_anchor = self.anchor.copy()
                new_obj.set_anchor(new_anchor)

                if self.anchor in self.children:
                    new_obj.add_child(new_anchor)

            objs.append(new_obj)

        return objs[0] if num == 1 else objs

    def get_children(self):
        all_objects = []
        for obj in self.children:
            if len(obj.children) > 0:
                all_objects.extend(obj.get_children())
            else:
                all_objects.append(obj)
        return all_objects

    def to_list(self, x):
        if isinstance(x, list):
            return x
        elif isinstance(x, SceneProgObject):
            return [x]
        elif isinstance(x, str):
            if self.scene is None:
                raise ValueError("Cannot resolve string object name without a scene")
            return [self.scene.get_object(x)]
        else:
            raise TypeError(f"Unsupported type: {type(x)}. Must be list, SceneProgObject, or str")

    # ----------------------------
    # operations
    # ----------------------------
    def add_operation(self, op: Operation):
        if op.singleton:
            self.operations = [old_op for old_op in self.operations if old_op.name != op.name]
        self.operations.append(op)

    def get_operations(self, stage=None):
        if stage is None:
            return list(self.operations)
        return [op for op in self.operations if op.stage == stage]

    def get_operation(self, name):
        for op in reversed(self.operations):
            if op.name == name:
                return op
        return None

    def has_operation(self, name):
        return self.get_operation(name) is not None

    def get_operations_by_name(self):
        ops = {}
        for op in self.operations:
            ops[op.name] = op
        return ops

    def clear_operations(self):
        self.operations = []

    def remove_operations(self, name):
        self.operations = [op for op in self.operations if op.name != name]

    def describe_operations(self):
        if not self.operations:
            return "No operations recorded."

        lines = []
        for i, op in enumerate(self.operations):
            lines.append(
                f"{i:02d} | name={op.name} | stage={op.stage} | singleton={op.singleton}"
            )
        return "\n".join(lines)

    # ----------------------------
    # compile lifecycle
    # ----------------------------
    def log_phase(self, name):
        self.compile_log.append(name)

    def reset_cached_state(self):
        if hasattr(self, "anchor_info"):
            self.anchor_info = None
        if hasattr(self, "inner_aabb"):
            self.inner_aabb = None

    def reset_compile_state(self):
        self.is_compiled = False
        self.compile_log = []
        self.last_compile_report = None
        self.reset_cached_state()

    def compile_children(self):
        for child in self.children:
            if (
                hasattr(child, "compile")
                and not child.is_compiled
                and not getattr(child, "is_frozen_group", False)
            ):
                child.compile()

    def execute_operation_stage(self, stage):
        self.log_phase(f"execute_operation_stage:{stage}")
        for op in self.get_operations(stage=stage):
            op.execute()

    def execute_main_operations(self):
        self.log_phase("execute_main_operations")
        for op in self.operations:
            if op.stage != "post":
                op.execute()

    def prepare_constraints(self):
        self.log_phase("prepare_constraints")
        if hasattr(self, "OverlapConstraint"):
            self.OverlapConstraint()

    def run_grad_optimization(self):
        self.log_phase("run_grad_optimization")
        self.grad_optimize()

    def execute_post_operations(self):
        self.log_phase("execute_post_operations")
        for op in self.get_operations(stage="post"):
            op.execute()

    def run_vlm_optimization(self):
        self.log_phase("run_vlm_optimization")
        self.vlm_optimize()

    def finalize_compile(self):
        self.log_phase("finalize_compile")
        self.is_compiled = True

    def make_compile_report(self):
        report = {
            "name": self.name,
            "compiled": self.is_compiled,
            "num_children": len(self.children),
            "num_operations": len(self.operations),
            "operation_names": [op.name for op in self.operations],
            "compile_log": list(self.compile_log),
            "world_location": self.get_world_location().tolist(),
            "world_rotation": float(self.get_world_rotation()),
            "local_location": self.get_local_location().tolist(),
            "local_rotation": float(self.get_local_rotation()),
            "has_anchor": self.has_anchor(),
            "num_constraints": len(self.constraints),
            "num_grad_constraints": len(self.grad_constraints),
            "num_vlm_constraints": len(self.vlm_constraints),
            "anchor_name": self.anchor.name if self.anchor is not None else None,
            "grad_constraint_names": [c.name for c in self.grad_constraints],
            "vlm_constraint_names": [c.name for c in self.vlm_constraints],
        }
        return report

    def compile(self):
        self.reset_compile_state()
        self.clear_constraints()

        self.execute_main_operations()
        self.compile_children()

        self.prepare_constraints()
        self.run_grad_optimization()
        self.execute_post_operations()
        self.run_vlm_optimization()
        self.finalize_compile()

        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report

    # ----------------------------
    # explicit transform semantics
    # ----------------------------
    def get_local_transform(self):
        return self.transform

    def get_intrinsic_transform(self):
        return self.T0

    def get_object_transform(self):
        return self.transform @ self.T0

    def get_world_transform(self):
        if self.parent is not None:
            return self.parent.get_world_transform() @ self.get_object_transform()
        return self.get_object_transform()

    def get_effective_transform(self):
        return self.get_world_transform()

    # ----------------------------
    # explicit location semantics
    # ----------------------------
    def get_local_location(self):
        return self.transform.translation.copy()

    def get_world_location(self):
        return self.get_world_transform().decompose_matrix()[0]

    def get_location(self):
        return self.get_world_location()

    # ----------------------------
    # explicit rotation semantics
    # ----------------------------
    def get_local_rotation(self):
        return self.transform.rotation

    def get_world_rotation(self):
        return self.get_world_transform().decompose_matrix()[1]

    def get_rotation(self):
        return self.get_world_rotation()

    # ----------------------------
    # directions
    # ----------------------------
    def get_local_dirs(self):
        front_dir = np.array([[0, 0, 1]], dtype=np.float32)
        back_dir = np.array([[0, 0, -1]], dtype=np.float32)
        left_dir = np.array([[-1, 0, 0]], dtype=np.float32)
        right_dir = np.array([[1, 0, 0]], dtype=np.float32)

        dirs = np.vstack((front_dir, back_dir, left_dir, right_dir))
        dirs = self.get_local_transform().transform_directions(dirs)
        dirs = dirs / np.linalg.norm(dirs, axis=1, keepdims=True)

        return [dirs[0], dirs[1], dirs[2], dirs[3]]

    def get_world_dirs(self):
        front_dir = np.array([[0, 0, 1]], dtype=np.float32)
        back_dir = np.array([[0, 0, -1]], dtype=np.float32)
        left_dir = np.array([[-1, 0, 0]], dtype=np.float32)
        right_dir = np.array([[1, 0, 0]], dtype=np.float32)

        dirs = np.vstack((front_dir, back_dir, left_dir, right_dir))
        dirs = self.get_world_transform().transform_directions(dirs)
        dirs = dirs / np.linalg.norm(dirs, axis=1, keepdims=True)

        return [dirs[0], dirs[1], dirs[2], dirs[3]]

    def get_dirs(self):
        return self.get_world_dirs()

    # ----------------------------
    # anchor helpers
    # ----------------------------
    def set_anchor(self, obj):
        if obj is not None and not isinstance(obj, SceneProgObject):
            raise TypeError("anchor must be a SceneProgObject or None")
        self.anchor = obj

    def get_anchor(self):
        return self.anchor

    def has_anchor(self):
        return self.anchor is not None

    # ----------------------------
    # state + debugging helpers
    # ----------------------------
    def get_state_info(self):
        return self.get_world_transform().decompose_matrix()

    def describe_state(self):
        world_loc = self.get_world_location()
        local_loc = self.get_local_location()
        anchor_name = self.anchor.name if self.anchor is not None else None

        lines = [
            f"name={self.name}",
            f"class={self.__class__.__name__}",
            f"compiled={self.is_compiled}",
            f"num_children={len(self.children)}",
            f"num_operations={len(self.operations)}",
            f"anchor={anchor_name}",
            f"local_location={local_loc.tolist()}",
            f"world_location={world_loc.tolist()}",
            f"local_rotation={float(self.get_local_rotation())}",
            f"world_rotation={float(self.get_world_rotation())}",
        ]
        return "\n".join(lines)

    def describe_tree(self, depth=0):
        indent = "  " * depth
        anchor_str = f", anchor={self.anchor.name}" if self.anchor is not None else ""
        line = (
            f"{indent}- {self.name} "
            f"(children={len(self.children)}, ops={len(self.operations)}, "
            f"compiled={self.is_compiled}{anchor_str})"
        )

        lines = [line]
        for child in self.children:
            lines.append(child.describe_tree(depth=depth + 1))
        return "\n".join(lines)

    def print_effective_transform(self):
        if self.parent is not None:
            return f"{self.parent.print_effective_transform()} @ {self.transform} @ {self.T0}"
        return f"{self.transform} @ {self.T0}"

    # ----------------------------
    # hierarchy helpers
    # ----------------------------
    def _is_ancestor_of(self, obj):
        current = self
        while current is not None:
            if current is obj:
                return True
            current = current.parent
        return False

    def add_child(self, obj):
        if isinstance(obj, list):
            for o in obj:
                self.add_child(o)
            return

        if obj is self:
            raise ValueError("Cannot add object as a child of itself")

        if self._is_ancestor_of(obj):
            raise ValueError("Cannot add an ancestor as a child")

        if obj not in self.children:
            self.children.append(obj)
            obj.parent = self

    # ----------------------------
    # mutation helpers
    # ----------------------------
    def set_rotation(self, rotation):
        self.transform.set_rotation(rotation)

    def set_location(self, x, y, z):
        self.transform.set_translation([x, y, z])

    def translate(self, dx, dy, dz):
        current_translation = self.transform.translation
        new_translation = current_translation + np.array([dx, dy, dz], dtype=np.float32)
        self.transform.set_translation(new_translation)

    # ----------------------------
    # geometry helpers
    # ----------------------------
    def get_aabb(self):
        if len(self.children) == 0:
            if self.vertices is None:
                raise ValueError(f"Object '{self.name}' must have vertices to compute AABB")

            vertices = self.get_world_transform().transform_points(self.vertices)
            aabb_min = np.min(vertices, axis=0)
            aabb_max = np.max(vertices, axis=0)
            return np.stack([aabb_min, aabb_max])

        minimums = []
        maximums = []

        # Decorative lights (added by add_lighting) sit at ceiling height and must not
        # inflate the object's bounding box. Skip them; fall back to all children only if
        # the node has nothing but lights.
        children = [c for c in self.children if not getattr(c, "is_light", False)]
        if not children:
            children = self.children

        for child in children:
            child_aabb = child.get_aabb()
            minimums.append(child_aabb[0])
            maximums.append(child_aabb[1])

        aabb_min = np.min(minimums, axis=0)
        aabb_max = np.max(maximums, axis=0)
        return np.stack([aabb_min, aabb_max])

    def get_whd(self):
        aabb = self.get_aabb()
        w = aabb[1, 0] - aabb[0, 0]
        h = aabb[1, 1] - aabb[0, 1]
        d = aabb[1, 2] - aabb[0, 2]
        return np.array([w, h, d], dtype=np.float32)

    def get_area(self):
        w, h, d = self.get_whd()
        return w * d

    def get_width(self):
        return self.get_whd()[0]

    def get_height(self):
        return self.get_whd()[1]

    def get_depth(self):
        return self.get_whd()[2]

    # ----------------------------
    # object manipulation helpers
    # ----------------------------
    def face_towards(self, target):
        v2 = target.get_world_location()
        v1 = self.get_world_location()

        rel = v2 - v1
        rel = rel[[0, 2]]
        rel /= np.linalg.norm(rel) + 1e-6
        rot = np.arctan2(rel[0], rel[1]) * 180.0 / np.pi
        self.set_rotation(rot)

    def scale(self, target_width):
        current_width = self.get_width()
        if current_width == 0:
            raise ValueError(f"Object '{self.name}' has zero width, cannot scale.")

        uniform_scale = target_width / current_width
        self.transform.set_scale([uniform_scale, uniform_scale, uniform_scale])

    def scale_only_width(self, target_width):
        current_width = self.get_width()
        if current_width == 0:
            raise ValueError(f"Object '{self.name}' has zero width, cannot scale width.")

        scale_factor = target_width / current_width
        current_scale = self.transform.scale
        self.transform.set_scale([
            scale_factor * current_scale[0],
            current_scale[1],
            current_scale[2],
        ])

    def scale_only_height(self, target_height):
        current_height = self.get_height()
        if current_height == 0:
            raise ValueError(f"Object '{self.name}' has zero height, cannot scale height.")

        scale_factor = target_height / current_height
        current_scale = self.transform.scale
        self.transform.set_scale([
            current_scale[0],
            scale_factor * current_scale[1],
            current_scale[2],
        ])

    def scale_only_depth(self, target_depth):
        current_depth = self.get_depth()
        if current_depth == 0:
            raise ValueError(f"Object '{self.name}' has zero depth, cannot scale depth.")

        scale_factor = target_depth / current_depth
        current_scale = self.transform.scale
        self.transform.set_scale([
            current_scale[0],
            current_scale[1],
            scale_factor * current_scale[2],
        ])

    # ----------------------------
    # group/object utility helpers
    # ----------------------------
    def recenter(self):
        aabb = self.get_aabb()
        pivot = np.array([
            (aabb[0, 0] + aabb[1, 0]) / 2.0,  # center x
            aabb[0, 1],                       # bottom y
            (aabb[0, 2] + aabb[1, 2]) / 2.0,  # center z
        ], dtype=np.float32)
        self.T0.set_translation(-pivot)

    def compute_obj_y(self, obj):
        aabb = obj.get_aabb()
        result = obj.get_world_location()[1] - aabb[0, 1]
        return result

    def get_descriptions(self):
        if len(self.children) > 0:
            descriptions = [child.get_descriptions() for child in self.children]
            descriptions = [d for d in descriptions if d is not None]
            return ",".join(descriptions) if descriptions else self.name
        return self.description if self.description is not None else self.name

    # ----------------------------
    # asset loading
    # ----------------------------
    def load(self, mesh_path):
        self.mesh_path = mesh_path

        mesh = trimesh.load(mesh_path, force="mesh", process=False)
        vertices = mesh.vertices.copy()

        bbox_center = (np.min(vertices, axis=0) + np.max(vertices, axis=0)) / 2.0
        self.T0.set_translation(-bbox_center)

        centered_vertices = vertices - bbox_center
        width = np.ptp(centered_vertices[:, 0])

        if width == 0:
            raise ValueError(f"Mesh '{mesh_path}' has zero width, cannot normalize scale.")

        scale_factor_init = np.array([1.0, 1.0, 1.0], dtype=np.float32) * (1.0 / width)
        self.T0.set_scale(scale_factor_init)

        self.vertices = mesh.vertices.copy()
        self.faces = mesh.faces.copy()

        if self.scene is not None and hasattr(self.scene, "register_asset"):
            self.scene.register_asset(mesh_path)

    @placemethod(singleton=True, stage="post")
    def add_lighting(self, desc, density, modulate_scale=1.0):
        density = float(np.clip(density, 0.0, 1.0))

        light = self.scene.AddAsset(desc, modulate_scale=modulate_scale)

        def compute_lights(density_value):
            W, _, D = self.get_whd()
            w, _, d = light.get_whd()

            area = W * D * 0.64
            unit_area = max(w * d, 1e-6)
            max_lights = max(1, int(np.floor(area / unit_area) / 4.0))

            N = max(1, int(np.round(1 + (max_lights - 1) * density_value)))

            def best_grid(n):
                best = (1, n)
                min_diff = float("inf")
                for cols in range(1, n + 1):
                    rows = int(np.ceil(n / cols))
                    if cols * rows >= n:
                        diff = abs(rows - cols)
                        if diff < min_diff:
                            best = (cols, rows)
                            min_diff = diff
                return best

            grid_cols, grid_rows = best_grid(N)

            if self.scene is not None and hasattr(self.scene, "HEIGHT"):
                y = self.scene.HEIGHT
            else:
                y = self.get_aabb()[1, 1] + 0.2

            return grid_cols, grid_rows, y, W, D, N

        grid_cols, grid_rows, y, W, D, N = compute_lights(density)

        xs = np.array([0.0]) if grid_cols == 1 else np.linspace(-0.4, 0.4, grid_cols)
        zs = np.array([0.0]) if grid_rows == 1 else np.linspace(-0.4, 0.4, grid_rows)

        locs_x, locs_z = np.meshgrid(xs, zs)
        locs = np.stack([locs_x, locs_z], axis=-1).reshape(-1, 2)
        locs[:, 0] *= W * 0.8
        locs[:, 1] *= D * 0.8

        aabb = self.get_aabb()
        x0 = (aabb[0, 0] + aabb[1, 0]) / 2.0
        z0 = (aabb[0, 2] + aabb[1, 2]) / 2.0
        locs[:, 0] += x0
        locs[:, 1] += z0

        for i in range(min(N, len(locs))):
            x = locs[i, 0]
            z = locs[i, 1]
            new_light = light.copy()
            # Lights are decorative children: they must move with the object but must not
            # count toward its bounding box / footprint (otherwise density, which controls
            # the light count and spread, would change the object's reported size).
            new_light.is_light = True
            new_light.ignore_overlap = True
            new_light.set_location(x, y, z)
            self.add_child(new_light)
            if self.scene is not None and hasattr(self.scene, "ceiling_lights"):
                self.scene.ceiling_lights.append(new_light)


    def render(self):
        lines = """
import bpy
import os

def assign_generated_texture(obj, image_path, scale=(1.0, 1.0, 1.0), material_name="GeneratedTexture"):
    try:
        image = bpy.data.images.load(image_path)
    except Exception as e:
        print(f"Could not load image {image_path}: {e}")
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
    tex_image.projection = 'BOX'
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_image.inputs['Vector'])
    links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    mapping.inputs['Scale'].default_value = scale

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

mesh_lookup = {}
    """

        for path, name in self.scene.unique_assets.items():
            lines += f"""
bpy.ops.import_scene.gltf(filepath=r'{path}')
imported_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
assert imported_objs, "No mesh found for {name}"
mesh_obj = imported_objs[0]
mesh_obj.name = '{name}_MESH'
mesh_lookup['{name}'] = mesh_obj.data

bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
mesh_obj.hide_set(True)
mesh_obj.hide_render = True
    """

        objects_to_render = self.get_children() if len(self.children) > 0 else [self]

        for i, obj in enumerate(objects_to_render):
            if obj.mesh_path is None:
                continue

            mesh_key = self.scene.unique_assets[obj.mesh_path]
            obj_name = str(i)
            translation, rotation_euler, scale = obj.get_state_info()
            rot_rad = np.radians(rotation_euler)

            lines += f"""
obj = bpy.data.objects.new('{obj_name}', mesh_lookup['{mesh_key}'])
bpy.context.collection.objects.link(obj)
obj.location = [{translation[0]}, -{translation[2]}, {translation[1]}]
obj.rotation_euler = (0, 0, {rot_rad})
obj.scale = [{scale[0]}, {scale[2]}, {scale[1]}]
    """

            if hasattr(self.scene, "ceiling_lights") and obj in self.scene.ceiling_lights:
                w, h, d = obj.get_whd()
                light_y = getattr(self.scene, "HEIGHT", 4.0)
                lines += f"""
light_data = bpy.data.lights.new(name='{obj_name}_Light', type='AREA')
light_data.energy = 500
light_data.shape = 'RECTANGLE'
light_data.size = {w}
light_data.size_y = {d}

light_object = bpy.data.objects.new(name="{obj_name}_Light", object_data=light_data)
light_object.location = [{translation[0]}, -{translation[2]}, {light_y}]
bpy.context.collection.objects.link(light_object)
    """

        if hasattr(self.scene, "walls") and len(self.scene.walls) > 0:
            for wall in self.scene.walls:
                wall._rebuild()
                uid = random.randint(0, 1000000)
                mesh_path = f"tmp/{wall.name}_{uid}.glb"
                try:
                    wall.export(mesh_path)
                except Exception:
                    continue

                texture_path = wall.texture_path
                res = wall.res
                lines += f"""
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

        if hasattr(self.scene, "wall_objects") and len(self.scene.wall_objects) > 0:
            for obj in self.scene.wall_objects:
                lines += f"""
bpy.ops.import_scene.gltf(filepath=r'{obj.mesh_path}')
    """

        uid = random.randint(0, 1000000)
        target = f"tmp/group_{uid}.blend"
        os.makedirs("tmp", exist_ok=True)

        exec_runner = SceneProgExec()
        exec_runner(lines, target, verbose=True)

        renderer = SceneRenderer(verbose=True)
        right_path = f"tmp/right_{uid}.png"
        back_path = f"tmp/back_{uid}.png"
        left_path = f"tmp/left_{uid}.png"
        front_path = f"tmp/front_{uid}.png"

        renderer.render_from_edge_midpoints(
            target,
            output_paths=[right_path, back_path, left_path, front_path],
        )

        img1 = plt.imread(right_path)
        img2 = plt.imread(back_path)
        img3 = plt.imread(left_path)
        img4 = plt.imread(front_path)

        combined_img = np.hstack((img4, img1, img2, img3))
        combined_path = f"tmp/combined_{uid}.png"
        plt.imsave(combined_path, combined_img)
        return combined_path


    def render_wall(self, wall, wall_objects):
        lines = """
import bpy
import os

def assign_generated_texture(obj, image_path, scale=(1.0, 1.0, 1.0), material_name="GeneratedTexture"):
    try:
        image = bpy.data.images.load(image_path)
    except Exception as e:
        print(f"Could not load image {image_path}: {e}")
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
    tex_image.projection = 'BOX'
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_image.inputs['Vector'])
    links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    mapping.inputs['Scale'].default_value = scale

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

mesh_lookup = {}
    """

        wall_obj_ref = self._wall_name_to_wall(wall)
        wall_obj_ref._rebuild()

        uid = random.randint(0, 1000000)
        mesh_path = f"tmp/{wall_obj_ref.name}_{uid}.glb"
        try:
            wall_obj_ref.export(mesh_path)
        except Exception:
            mesh_path = None

        if mesh_path is not None:
            texture_path = wall_obj_ref.texture_path
            res = wall_obj_ref.res
            lines += f"""
bpy.ops.import_scene.gltf(filepath=r'{mesh_path}')
wall_obj = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH'][0]
wall_obj.name = '{wall_obj_ref.name}'
assign_generated_texture(
    wall_obj,
    image_path=r'{texture_path}',
    scale=({res}, {res}, {res}),
    material_name='{wall_obj_ref.name}_mat'
)
    """

        for path, name in self.scene.unique_assets.items():
            lines += f"""
bpy.ops.import_scene.gltf(filepath=r'{path}')
imported_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
assert imported_objs, "No mesh found for {name}"
mesh_obj = imported_objs[0]
mesh_obj.name = '{name}_MESH'
mesh_lookup['{name}'] = mesh_obj.data

bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
mesh_obj.hide_set(True)
mesh_obj.hide_render = True
    """

        for i, obj in enumerate(wall_objects):
            if obj.mesh_path is None:
                continue

            mesh_key = self.scene.unique_assets[obj.mesh_path]
            obj_name = str(i)
            translation, rotation_euler, scale = obj.get_state_info()
            rot_rad = np.radians(rotation_euler)

            lines += f"""
obj = bpy.data.objects.new('{obj_name}', mesh_lookup['{mesh_key}'])
bpy.context.collection.objects.link(obj)
obj.location = [{translation[0]}, -{translation[2]}, {translation[1]}]
obj.rotation_euler = (0, 0, {rot_rad})
obj.scale = [{scale[0]}, {scale[2]}, {scale[1]}]
    """

        target = f"tmp/group_{uid}.blend"
        os.makedirs("tmp", exist_ok=True)

        exec_runner = SceneProgExec()
        exec_runner(lines, target, verbose=True)

        renderer = SceneRenderer(verbose=True)
        import json
        with open("tmp/scene_dims.json", "w") as f:
            json.dump({"W": wall_obj_ref.width, "D": 0.1, "H": wall_obj_ref.height}, f)

        output_path = f"tmp/front_{uid}.png"
        renderer.render_from_front(target, output_path=output_path)
        return output_path


    def grad_optimize(self):
        if self.grad_solver is None:
            return
        self.grad_solver.objects = self.children
        self.grad_solver()


    def vlm_optimize(self):
        if self.vlm_solver is None:
            return
        self.vlm_solver.objects = self.children
        self.vlm_solver.constraints = self.vlm_constraints
        self.vlm_solver()