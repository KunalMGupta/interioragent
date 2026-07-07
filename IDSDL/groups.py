import os
import random
import numpy as np
from IDSDL.object import SceneProgObject, placemethod

SIDE_GAP = 0.1
FRONT_BACK_GAP = 0.45
CIRCULATION_GAP = 0.35
FURNITURE_CLEARANCE = 0.4
MAX_WALL_FURNITURE_HEIGHT = 2.0
OCCUPANCY_THRESHOLD = 0.4
WALL_FURNITURE_HEIGHT_MAX = 1.0
WALL_MID_LEVEL_MAX = 2.0
BUFFER = 0.05


class AnchorGroup(SceneProgObject):
    def __init__(self, scene, name=None):
        super().__init__(scene, name=name)
        self.anchor_info = None
        self.rug_multiplier = 1.15
        self.rng = scene._make_rng() if scene is not None and hasattr(scene, "_make_rng") \
            else np.random.default_rng()

    def set_anchor(self, anchor):
        self.anchor = anchor
        current_location = self.anchor.get_location()
        current_location[1] -= self.anchor.get_aabb()[0, 1]
        anchor.set_location(*current_location)
        self.add_child(anchor)

    def get_anchor_center_dirs(self, force=False):
        if not force and self.anchor_info is not None:
            return self.anchor_info

        front_dir, back_dir, left_dir, right_dir = self.anchor.get_dirs()
        center = self.anchor.get_location()
        width, height, depth = self.anchor.get_whd()

        self.anchor_info = (
            front_dir,
            back_dir,
            left_dir,
            right_dir,
            center,
            width,
            height,
            depth,
        )
        return self.anchor_info

    # Proportions for objects placed on top, relative to the anchor they rest on.
    # A mis-scaled retrieval (e.g. a "small desk lamp" that comes back huge) is
    # uniformly shrunk to a believable size: footprint to a share of the anchor top
    # (split across N items), height to a fraction of the anchor height, and the
    # combined anchor+object stack capped to a hard ceiling. Never up-scaled.
    # Deterministic — no VLM.
    ON_TOP_FOOTPRINT_FRACTION = 0.5   # object footprint <= this share of the anchor top
    ON_TOP_HEIGHT_FRACTION = 0.4      # object height <= this * anchor height
    ON_TOP_MAX_COMBINED_HEIGHT = 3.5  # anchor + on-top object stack must not exceed this [m]

    def _fit_on_top(self, obj, anchor_w, anchor_h, anchor_d, n):
        w0, h0, d0 = obj.get_whd()
        if min(w0, h0, d0) <= 0:
            return
        f = self.ON_TOP_FOOTPRINT_FRACTION
        caps = [
            f * (anchor_w / max(n, 1)) / w0,   # share of the anchor width
            f * anchor_d / d0,                  # within the anchor depth
            self.ON_TOP_HEIGHT_FRACTION * anchor_h / h0,  # <= 0.4x the anchor height
            1.0,                                # never enlarge
        ]
        # Hard ceiling on the combined anchor+object stack (e.g. a tall shelf plus a
        # tall object must still clear the room): object height <= 3.5m - anchor height.
        combined_headroom = self.ON_TOP_MAX_COMBINED_HEIGHT - anchor_h
        if combined_headroom > 0:
            caps.append(combined_headroom / h0)
        scale = min(caps)
        if scale < 1.0:
            # Uniform shrink by a factor: multiply the existing transform scale (which
            # carries the retriever's real-world size). NOTE: do NOT use obj.scale(),
            # which sets scale absolutely from the normalized (width=1) mesh and so
            # discards the retrieved size when called after load.
            cur = obj.transform.scale
            obj.transform.set_scale([cur[0] * scale, cur[1] * scale, cur[2] * scale])

    @placemethod
    def place_on_top(self, objs):
        objs = self.to_list(objs)

        # Primary: VLM-tournament placement (renders candidates, judges, applies the best).
        # Falls back to the deterministic AABB layout below on any failure or if disabled.
        from IDSDL import vlm_placement
        if vlm_placement.place_smart(self, self.anchor, objs, "on_top", log=print):
            return

        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        N = len(objs)

        # Size each object to the anchor before placing it (proportions fix).
        anchor_w, anchor_h, anchor_d = self.anchor.get_whd()
        for obj in objs:
            self._fit_on_top(obj, anchor_w, anchor_h, anchor_d, N)

        aabb = self.anchor.get_aabb()
        vmin = aabb[0]
        vmax = aabb[1]

        left = (
            np.array([vmin[0], 0, vmin[2]]),
            np.array([vmin[0], 0, vmax[2]])
        )
        right = (
            np.array([vmax[0], 0, vmin[2]]),
            np.array([vmax[0], 0, vmax[2]])
        )

        left = np.mean(left, axis=0)
        right = np.mean(right, axis=0)
        vector = right - left
        locs = [left + i * vector / (N + 1) for i in range(1, N + 1)]

        for i, obj in enumerate(objs):
            obj.set_location(locs[i][0], height + self.compute_obj_y(obj), locs[i][2])
            obj.ignore_overlap = True
            self.add_child(obj)

    @placemethod
    def place_inside(self, objs):
        """Place objects INSIDE the anchor's body (e.g. cabinet/shelf interior).

        Primary path is the VLM-tournament solver (mode='inside'); the fallback distributes
        the objects across the anchor's interior at mid-height, sized like place_on_top.
        """
        objs = self.to_list(objs)

        from IDSDL import vlm_placement
        if vlm_placement.place_smart(self, self.anchor, objs, "inside", log=print):
            return

        # Fallback: AABB interior — fit each object, then line them up along the anchor's
        # width at roughly mid-body height (no usable-surface info without rendering).
        N = len(objs)
        anchor_w, anchor_h, anchor_d = self.anchor.get_whd()
        for obj in objs:
            self._fit_on_top(obj, anchor_w, anchor_h, anchor_d, N)

        aabb = self.anchor.get_aabb()
        vmin, vmax = aabb[0], aabb[1]
        mid_y = (vmin[1] + vmax[1]) / 2.0
        left = np.array([vmin[0], 0, (vmin[2] + vmax[2]) / 2.0])
        right = np.array([vmax[0], 0, (vmin[2] + vmax[2]) / 2.0])
        vector = right - left
        locs = [left + i * vector / (N + 1) for i in range(1, N + 1)]
        for i, obj in enumerate(objs):
            obj.set_location(locs[i][0], mid_y + self.compute_obj_y(obj), locs[i][2])
            obj.ignore_overlap = True
            self.add_child(obj)

    @placemethod
    def place_rug(self, desc, size, asset_id=None):
        rug = self.scene.AddAsset(desc, asset_id=asset_id)
        # Rugs must be modelled FLAT (thin in height). Many "bath mat" meshes are authored upright
        # (thin in depth, ~0.4 m tall), and the export pipeline is yaw-only so we can't tilt them
        # down — place_rug scales width+depth and the upright height survives as a giant slab.
        # Warn loudly and pin a flat rug via asset_id= when this trips.
        rw, rh, rd = (float(v) for v in rug.get_whd())
        if rh > 0.1 * max(rw, rd):
            print(f"[place_rug] WARNING: '{desc}' -> {getattr(rug, 'retrieval_model', '?')} is not "
                  f"flat (h={rh:.3f} vs footprint {rw:.2f}x{rd:.2f}); pin a flat rug via asset_id=.")
        w, h, d = self.get_whd()

        size = 0.4 * (1 - size) + self.rug_multiplier * size

        mul = np.sqrt(self.rug_multiplier)
        new_width = mul * w * size
        new_depth = mul * d * size

        rug.scale_only_width(new_width)
        rug.scale_only_depth(new_depth)

        minimum = []
        maximum = []

        for child in self.children:
            minimum.append(child.get_aabb()[0])
            maximum.append(child.get_aabb()[1])

        minimum = np.min(minimum, axis=0)
        maximum = np.max(maximum, axis=0)

        end_location = (minimum + maximum) / 2

        if self.anchor is not None:
            starting = self.anchor.get_location()
        else:
            starting = end_location

        location = np.array(starting) * (1 - size) + np.array(end_location) * size
        rug.set_location(location[0], self.compute_obj_y(rug), location[2])
        self.add_child(rug)
        rug.ignore_overlap = True

        return rug

    def compile(self):
        self.reset_compile_state()
        self.clear_constraints()
        delayed_names = {"place_on_top", "place_inside", "place_rug", "add_lighting"}

        # Execute all main operations first
        for op in self.operations:
            if op.name not in delayed_names:
                op.execute()

        self.compile_children()

        # Run optimization
        self.OverlapConstraint()
        self.ObjectProportionsConstraint()
        self.RotationConstraint()
        self._run_constraint_hooks()
        self.grad_optimize()

        # Execute delayed operations last
        op = self.get_operation("place_on_top")
        if op is not None:
            op.execute()

        op = self.get_operation("place_inside")
        if op is not None:
            op.execute()

        op = self.get_operation("place_rug")
        if op is not None:
            op.execute()

        op = self.get_operation("add_lighting")
        if op is not None:
            op.execute()

        # Apply opt-in rotation overrides after positions have settled, so the
        # VLM rotation check below judges the corrected orientation.
        self._apply_orientations()

        self.vlm_optimize()
        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report


class RelativeGroup(AnchorGroup):
    def __init__(self, scene, name=None):
        super().__init__(scene, name=name)
        self.anchor_info = None
        self.inner_aabb = None
        self.operation_order = [
            'place_on_left',
            'place_on_right',
            'place_on_front_right',
            'place_on_front_left',
            'place_on_back_right',
            'place_on_back_left',
            'place_on_front',
            'place_on_back',
            'place_on_left_further',
            'place_on_right_further',
            'place_on_front_further',
            'place_on_back_further',
            'place_on_front_right_further',
            'place_on_front_left_further',
            'place_on_back_right_further',
            'place_on_back_left_further',
            'place_on_top',
            'place_inside',
        ]

    def get_inner_aabb(self):
        if self.inner_aabb is not None:
            return self.inner_aabb

        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()

        op_front_right = self.get_operation('place_on_front_right')
        op_back_right = self.get_operation('place_on_back_right')
        op_right = self.get_operation('place_on_right')
        op_back = self.get_operation('place_on_back')
        op_front = self.get_operation('place_on_front')

        op_front_left = self.get_operation('place_on_front_left')
        op_back_left = self.get_operation('place_on_back_left')
        op_left = self.get_operation('place_on_left')

        right_extent = max([
            op_front_right.obj.get_width() + SIDE_GAP if op_front_right is not None else 0,
            op_back_right.obj.get_width() + SIDE_GAP if op_back_right is not None else 0,
            op_right.obj.get_width() + SIDE_GAP if op_right is not None else 0,
            op_back.obj.get_width() / 2 - width / 2 if op_back is not None else 0,
            op_front.obj.get_width() / 2 - width / 2 if op_front is not None else 0,
        ])

        left_extent = max([
            op_front_left.obj.get_width() + SIDE_GAP if op_front_left is not None else 0,
            op_back_left.obj.get_width() + SIDE_GAP if op_back_left is not None else 0,
            op_left.obj.get_width() + SIDE_GAP if op_left is not None else 0,
            op_back.obj.get_width() / 2 - width / 2 if op_back is not None else 0,
            op_front.obj.get_width() / 2 - width / 2 if op_front is not None else 0,
        ])

        inner_width = right_extent + left_extent + width

        inner_depth = sum([
            op_front.obj.get_depth() + FRONT_BACK_GAP if op_front is not None else 0,
            op_back.obj.get_depth() + FRONT_BACK_GAP if op_back is not None else 0,
        ]) + max([
            sum([
                op_front_right.obj.get_depth() if op_front_right is not None else 0,
                op_right.obj.get_depth() if op_right is not None else 0,
                op_back_right.obj.get_depth() if op_back_right is not None else 0,
            ]),
            sum([
                op_front_left.obj.get_depth() if op_front_left is not None else 0,
                op_left.obj.get_depth() if op_left is not None else 0,
                op_back_left.obj.get_depth() if op_back_left is not None else 0,
            ]),
            depth,
        ])

        self.inner_aabb = (inner_width, inner_depth)
        return self.inner_aabb

    @placemethod
    def place_on_left(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        left = center + left_dir * (width / 2 + obj.get_width() / 2 + SIDE_GAP)
        obj.set_location(left[0], self.compute_obj_y(obj), left[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_right(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        right = center + right_dir * (width / 2 + obj.get_width() / 2 + SIDE_GAP)
        obj.set_location(right[0], self.compute_obj_y(obj), right[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_front_right(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        front_right = center + front_dir * (depth / 2 - obj.get_depth() / 2) + right_dir * (width / 2 + obj.get_width() / 2 + SIDE_GAP)
        obj.set_location(front_right[0], self.compute_obj_y(obj), front_right[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_front_left(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        front_left = center + front_dir * (depth / 2 - obj.get_depth() / 2) + left_dir * (width / 2 + obj.get_width() / 2 + SIDE_GAP)
        obj.set_location(front_left[0], self.compute_obj_y(obj), front_left[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_back_right(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        back_right = center + back_dir * (depth / 2 - obj.get_depth() / 2) + right_dir * (width / 2 + obj.get_width() / 2 + SIDE_GAP)
        obj.set_location(back_right[0], self.compute_obj_y(obj), back_right[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_back_left(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        back_left = center + back_dir * (depth / 2 - obj.get_depth() / 2) + left_dir * (width / 2 + obj.get_width() / 2 + SIDE_GAP)
        obj.set_location(back_left[0], self.compute_obj_y(obj), back_left[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_front(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        front = center + front_dir * (depth / 2 + obj.get_depth() / 2 + FRONT_BACK_GAP)
        obj.set_location(front[0], self.compute_obj_y(obj), front[2])
        obj.set_rotation(180)
        self.add_child(obj)

    @placemethod
    def place_on_front_adjacent(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        front = center + front_dir * (depth / 2 + obj.get_depth() / 2 + BUFFER)
        obj.set_location(front[0], self.compute_obj_y(obj), front[2])
        obj.set_rotation(180)
        self.add_child(obj)

    @placemethod
    def place_on_back(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        back = center + back_dir * (depth / 2 + obj.get_depth() / 2 + FRONT_BACK_GAP)
        obj.set_location(back[0], self.compute_obj_y(obj), back[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_back_adjacent(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        back = center + back_dir * (depth / 2 + obj.get_depth() / 2 + BUFFER)
        obj.set_location(back[0], self.compute_obj_y(obj), back[2])
        obj.set_rotation(0)
        self.add_child(obj)

    def place_desk_chair(self, desk, chair, gap=False):
        """Build a desk+seat unit with the correct pose, asset-independently.

        Dataset desks are modeled with their working front (knee-hole/drawers) at +z, but a
        seat on the desk's BACK needs that front to face it. So the rule for ANY desk-chair
        arrangement (student / teacher / reception desk): anchor the desk, put the chair on
        the back, then rotate the desk 180 so its front faces the chair. This is reliable
        across desks and needs no per-asset front-cache entry. `gap=True` leaves circulation
        space behind the desk instead of tucking the chair right up to it.
        """
        self.set_anchor(desk)
        if gap:
            self.place_on_back_further(chair)
        else:
            self.place_on_back_adjacent(chair)
        self.rotate(desk, 180)
        return desk

    @placemethod
    def place_on_left_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        left_further = center + left_dir * (inner_width / 2 + obj.get_depth() / 2 + CIRCULATION_GAP)
        obj.set_location(left_further[0], self.compute_obj_y(obj), left_further[2])
        obj.set_rotation(90)
        self.add_child(obj)

    @placemethod
    def place_on_right_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        right_further = center + right_dir * (inner_width / 2 + obj.get_depth() / 2 + CIRCULATION_GAP)
        obj.set_location(right_further[0], self.compute_obj_y(obj), right_further[2])
        obj.set_rotation(-90)
        self.add_child(obj)

    @placemethod
    def place_on_front_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        front_further = center + front_dir * (inner_depth / 2 + obj.get_depth() / 2 + CIRCULATION_GAP)
        obj.set_location(front_further[0], self.compute_obj_y(obj), front_further[2])
        obj.set_rotation(180)
        self.add_child(obj)

    @placemethod
    def place_on_back_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        back_further = center + back_dir * (inner_depth / 2 + obj.get_depth() / 2 + CIRCULATION_GAP)
        obj.set_location(back_further[0], self.compute_obj_y(obj), back_further[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_front_right_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        front_right_further = center + front_dir * (inner_depth / 2 + obj.get_depth() / 2 + CIRCULATION_GAP) + right_dir * (inner_width / 2 + obj.get_width() / 2 + CIRCULATION_GAP)
        obj.set_location(front_right_further[0], self.compute_obj_y(obj), front_right_further[2])
        obj.set_rotation(-90)
        self.add_child(obj)

    @placemethod
    def place_on_front_left_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        front_left_further = center + front_dir * (inner_depth / 2 + obj.get_width() / 2 + CIRCULATION_GAP) + left_dir * (inner_width / 2 + obj.get_depth() / 2 + CIRCULATION_GAP)
        obj.set_location(front_left_further[0], self.compute_obj_y(obj), front_left_further[2])
        obj.set_rotation(90)
        self.add_child(obj)

    @placemethod
    def place_on_back_right_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        back_right_further = center + back_dir * (inner_depth / 2 + obj.get_depth() / 2 + CIRCULATION_GAP) + right_dir * (inner_width / 2 + obj.get_width() / 2 + CIRCULATION_GAP)
        obj.set_location(back_right_further[0], self.compute_obj_y(obj), back_right_further[2])
        obj.set_rotation(0)
        self.add_child(obj)

    @placemethod
    def place_on_back_left_further(self, obj):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        inner_width, inner_depth = self.get_inner_aabb()
        back_left_further = center + back_dir * (inner_depth / 2 + obj.get_depth() / 2 + CIRCULATION_GAP) + left_dir * (inner_width / 2 + obj.get_width() / 2 + CIRCULATION_GAP)
        obj.set_location(back_left_further[0], self.compute_obj_y(obj), back_left_further[2])
        obj.set_rotation(0)
        self.add_child(obj)

class AroundGroup(AnchorGroup):
    # Max perturbation at jitter=1.0: position offset as a fraction of the object's own
    # size, and rotation in degrees. Kept modest so a real-world "lived-in" irregularity
    # is added without breaking the arrangement (and the post-layout OverlapConstraint +
    # grad solve still separate anything the jitter pushes into a neighbour).
    JITTER_POS_FRACTION = 0.25
    JITTER_ROT_DEG = 12.0

    def __init__(self, scene, name=None, sparsity=0.0, jitter=0.0):
        super().__init__(scene, name=name)
        self.anchor_info = None
        self.sparsity = max(0.0, min(sparsity, 1.0))
        self.jitter = max(0.0, min(jitter, 1.0))

    def _jit_pos(self, obj):
        """Random (dx, dz) world offset for `obj`, scaled by jitter and the object size."""
        if self.jitter <= 0:
            return 0.0, 0.0
        w, _, d = obj.get_whd()
        mag = self.jitter * self.JITTER_POS_FRACTION
        return float(self.rng.uniform(-1, 1) * mag * w), float(self.rng.uniform(-1, 1) * mag * d)

    def _jit_rot(self):
        """Random rotation perturbation (degrees), scaled by jitter."""
        if self.jitter <= 0:
            return 0.0
        return float(self.rng.uniform(-1, 1) * self.jitter * self.JITTER_ROT_DEG)

    def _apply_jitter(self, obj):
        """Nudge an already-placed object's local position and rotation by a jittered amount."""
        if self.jitter <= 0:
            return
        dx, dz = self._jit_pos(obj)
        t = obj.transform.translation
        obj.set_location(t[0] + dx, t[1], t[2] + dz)
        obj.set_rotation(float(obj.transform.rotation) + self._jit_rot())

    @placemethod
    def place_rectilinear(self, longer_side1=None, longer_side2=None, shorter_side1=None, shorter_side2=None):
        longer_side1 = self.to_list([] if longer_side1 is None else longer_side1)
        longer_side2 = self.to_list([] if longer_side2 is None else longer_side2)
        shorter_side1 = self.to_list([] if shorter_side1 is None else shorter_side1)
        shorter_side2 = self.to_list([] if shorter_side2 is None else shorter_side2)

        dist_between_chairs = 0.05 + self.sparsity * 0.6
        dist_from_table = 0.05 + self.sparsity * 0.6

        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        new_width1, new_width2 = width, width
        new_depth1, new_depth2 = depth, depth

        if len(longer_side1) > 0 and len(longer_side1) * (longer_side1[0].get_width() + dist_between_chairs) > width:
            new_width1 = len(longer_side1) * (longer_side1[0].get_width() + dist_between_chairs)

        if len(longer_side2) > 0 and len(longer_side2) * (longer_side2[0].get_width() + dist_between_chairs) > width:
            new_width2 = len(longer_side2) * (longer_side2[0].get_width() + dist_between_chairs)

        if len(shorter_side1) > 0 and len(shorter_side1) * (shorter_side1[0].get_width() + dist_between_chairs) > depth:
            new_depth1 = len(shorter_side1) * (shorter_side1[0].get_width() + dist_between_chairs)

        if len(shorter_side2) > 0 and len(shorter_side2) * (shorter_side2[0].get_width() + dist_between_chairs) > depth:
            new_depth2 = len(shorter_side2) * (shorter_side2[0].get_width() + dist_between_chairs)

        new_width = max(new_width1, new_width2, width)
        new_depth = max(new_depth1, new_depth2, depth)

        if new_width > width:
            self.anchor.scale_only_width(new_width)

        if new_depth > depth:
            self.anchor.scale_only_depth(new_depth)

        def compute_sideways_coordinates(length, seat_widths):
            N = len(seat_widths)
            assert N > 0, "Seat width list must not be empty."

            total_seat_width = sum(seat_widths)
            S = (length - total_seat_width) / (N + 1)

            positions = []
            current = -length / 2 + S
            for width in seat_widths:
                center = current + width / 2
                positions.append(center)
                current += width + S

            return positions

        front_dir, back_dir, left_dir, right_dir, center, total_width, height, total_depth = self.get_anchor_center_dirs(force=True)

        if len(longer_side1) > 0:
            sideways_coordinates_longer_side1 = compute_sideways_coordinates(
                total_width, [obj.get_width() for obj in longer_side1]
            )
            for i, obj in enumerate(longer_side1):
                starting = center + front_dir * (total_depth / 2 + longer_side1[i].get_depth() / 2 + dist_from_table)
                x, y, z = starting + right_dir * sideways_coordinates_longer_side1[i]
                y = self.compute_obj_y(obj)
                obj.set_location(x, y, z)
                obj.set_rotation(self.anchor.get_rotation() - 180)
                self._apply_jitter(obj)
                self.add_child(obj)

        if len(longer_side2) > 0:
            sideways_coordinates_longer_side2 = compute_sideways_coordinates(
                total_width, [obj.get_width() for obj in longer_side2]
            )
            for i, obj in enumerate(longer_side2):
                starting = center + back_dir * (total_depth / 2 + longer_side2[i].get_depth() / 2 + dist_from_table)
                x, y, z = starting + left_dir * sideways_coordinates_longer_side2[i]
                y = self.compute_obj_y(obj)
                obj.set_location(x, y, z)
                obj.set_rotation(self.anchor.get_rotation())
                self._apply_jitter(obj)
                self.add_child(obj)

        if len(shorter_side1) > 0:
            sideways_coordinates_shorter_side1 = compute_sideways_coordinates(
                total_depth, [obj.get_width() for obj in shorter_side1]
            )
            for i, obj in enumerate(shorter_side1):
                starting = center + left_dir * (total_width / 2 + shorter_side1[i].get_depth() / 2 + dist_from_table)
                x, y, z = starting + front_dir * sideways_coordinates_shorter_side1[i]
                y = self.compute_obj_y(obj)
                obj.set_location(x, y, z)
                obj.set_rotation(self.anchor.get_rotation() + 90)
                self._apply_jitter(obj)
                self.add_child(obj)

        if len(shorter_side2) > 0:
            sideways_coordinates_shorter_side2 = compute_sideways_coordinates(
                total_depth, [obj.get_width() for obj in shorter_side2]
            )
            for i, obj in enumerate(shorter_side2):
                starting = center + right_dir * (total_width / 2 + shorter_side2[i].get_depth() / 2 + dist_from_table)
                x, y, z = starting + back_dir * sideways_coordinates_shorter_side2[i]
                y = self.compute_obj_y(obj)
                obj.set_location(x, y, z)
                obj.set_rotation(self.anchor.get_rotation() - 90)
                self._apply_jitter(obj)
                self.add_child(obj)

    @placemethod
    def place_circle(self, objects=None):
        objects = self.to_list([] if objects is None else objects)
        N = len(objects)
        if N == 0:
            return

        dist = 0.05 + self.sparsity * 0.8
        ang_diff = 360 / N
        rot = [i * ang_diff for i in range(N)]

        front_dir, back_dir, left_dir, right_dir, center, w0, height, d0 = self.get_anchor_center_dirs()
        x0, y0, z0 = center

        def angle_subtended(obj, radius):
            width = obj.get_width()
            depth = obj.get_depth()
            return 2 * np.arctan((width / 2) / (radius - depth / 2))

        def compute_total_angle_subtended(objects, dist, w0):
            return np.sum([angle_subtended(obj, w0 / 2 + dist + obj.get_depth() / 2) for obj in objects])

        def compute_min_fitting_dist(objects, dist, w0):
            # Push the ring outward (increase dist) until every chair fits around
            # the circle. The anchor table keeps its natural retrieved size.
            while compute_total_angle_subtended(objects, dist, w0) > 2 * np.pi:
                dist += 0.05
            return dist

        total_angle_subtended = compute_total_angle_subtended(objects, dist, w0)

        if total_angle_subtended > 2 * np.pi:
            dist = compute_min_fitting_dist(objects, dist, w0)

        for i, obj in enumerate(objects):
            radius = w0 / 2 + dist + obj.get_depth() / 2
            x = x0 + radius * np.sin(np.radians(rot[i] + self.anchor.get_rotation()))
            y = self.compute_obj_y(obj)
            z = z0 + radius * np.cos(np.radians(rot[i] + self.anchor.get_rotation()))
            obj.set_location(x, y, z)
            obj.face_towards(self.anchor)
            self._apply_jitter(obj)
            self.add_child(obj)

    @placemethod
    def place_arc(self, objects=None, dist=0.1):
        objects = self.to_list([] if objects is None else objects)
        N = len(objects)
        if N == 0:
            return

        def angle_subtended(obj, radius):
            width = obj.get_width()
            depth = obj.get_depth()
            return 2 * np.arctan((width / 2) / (radius - depth / 2))

        front_dir, back_dir, left_dir, right_dir, center, w0, height, d0 = self.get_anchor_center_dirs(force=True)
        x0, y0, z0 = center

        total_angle_subtended = np.sum([
            angle_subtended(obj, d0 / 2 + dist + obj.get_depth() / 2) for obj in objects
        ])

        minimum_angle = total_angle_subtended * 180 / np.pi
        maximum_angle = 150
        angle = (1 - self.sparsity) * minimum_angle + self.sparsity * maximum_angle

        def compute_rotations(angle, N):
            if N == 1:
                return [0]
            if N % 2 == 1:
                half = N // 2
                return [(-half + i) * (angle / (N - 1)) for i in range(N)]
            else:
                half = N // 2
                return [(-half + 0.5 + i) * (angle / N) for i in range(N)]

        rot = compute_rotations(angle, N)
        for i, obj in enumerate(objects):
            radius = d0 / 2 + dist + obj.get_depth() / 2
            x = x0 + radius * np.sin(np.radians(rot[i] + self.anchor.get_rotation()))
            y = self.compute_obj_y(obj)
            z = z0 + radius * np.cos(np.radians(rot[i] + self.anchor.get_rotation()))
            obj.set_location(x, y, z)
            obj.face_towards(self.anchor)
            self._apply_jitter(obj)
            self.add_child(obj)

class GridGroup(SceneProgObject):
    def __init__(self, scene, name=None, sparsity=0.0, randomness=0.0):
        super().__init__(scene, name=name)
        self.sparsity = max(0.0, min(sparsity, 1.0))
        self.randomness = max(0.0, min(randomness, 1.0))
        self.rng = scene._make_rng() if scene is not None and hasattr(scene, "_make_rng") \
            else np.random.default_rng()

    def _place_row(self, objects=None, along='x', facing='z', x0=0, z0=0):
        objects = self.to_list([] if objects is None else objects)
        N = len(objects)
        if N == 0:
            return 0.0

        widths = np.array([obj.get_width() for obj in objects], dtype=np.float32)
        total_width = np.sum(widths)
        base_gap = self.sparsity * (total_width / N)

        rng = self.rng
        jitter_max = base_gap * self.randomness

        if N > 1:
            gaps = base_gap + rng.uniform(-jitter_max, jitter_max, size=N - 1)
        else:
            gaps = np.array([], dtype=np.float32)

        x_positions = [0.0]
        for i in range(1, N):
            prev_x = x_positions[i - 1]
            prev_width = widths[i - 1]
            this_width = widths[i]
            gap = gaps[i - 1]
            new_x = prev_x + 0.5 * prev_width + gap + 0.5 * this_width
            x_positions.append(new_x)

        center_offset = (x_positions[0] + x_positions[-1]) / 2
        x_positions = [x - center_offset for x in x_positions]

        def set_rotation(obj, facing):
            if facing == 'z':
                obj.set_rotation(0)
            elif facing == '-z':
                obj.set_rotation(180)
            elif facing == 'x':
                obj.set_rotation(90)
            elif facing == '-x':
                obj.set_rotation(-90)
            else:
                raise ValueError(f"Unknown facing direction: {facing}")

        if along == 'x':
            for obj in objects:
                xpos = x_positions.pop(0) + x0
                ypos = self.compute_obj_y(obj)
                zpos = z0
                obj.set_location(xpos, ypos, zpos)
                set_rotation(obj, facing)
                self.add_child(obj)

        elif along == 'z':
            for obj in objects:
                xpos = x0
                ypos = self.compute_obj_y(obj)
                zpos = x_positions.pop(0) + z0
                obj.set_location(xpos, ypos, zpos)
                set_rotation(obj, facing)
                self.add_child(obj)
        else:
            raise ValueError(f"Unknown axis for row placement: {along}")

        total_width = np.sum(widths) + np.sum(gaps)
        return float(total_width)

    @placemethod
    def place_row(self, objects):
        self._place_row(objects=objects)

    @placemethod
    def place_rectilinear(self, width1=None, width2=None, depth1=None, depth2=None):
        width1 = self.to_list([] if width1 is None else width1)   # top row
        width2 = self.to_list([] if width2 is None else width2)   # bottom row
        depth1 = self.to_list([] if depth1 is None else depth1)   # left column
        depth2 = self.to_list([] if depth2 is None else depth2)   # right column

        def compute_row_span(objects):
            objects = self.to_list(objects)
            N = len(objects)
            if N == 0:
                return 0.0

            widths = np.array([obj.get_width() for obj in objects], dtype=np.float32)
            total_width = np.sum(widths)
            base_gap = self.sparsity * (total_width / N)

            jitter_max = base_gap * self.randomness
            max_total_gap = (base_gap + jitter_max) * (N - 1)

            return float(total_width + max_total_gap)

        def max_depth(objects):
            return max([obj.get_depth() for obj in objects], default=0.0)

        # Span along each side's placement axis
        top_span = compute_row_span(width1)
        bottom_span = compute_row_span(width2)
        left_span = compute_row_span(depth1)
        right_span = compute_row_span(depth2)

        # Thickness perpendicular to each side
        top_thickness = max_depth(width1)
        bottom_thickness = max_depth(width2)
        left_thickness = max_depth(depth1)
        right_thickness = max_depth(depth2)

        # Inner opening
        inner_width = max(top_span, bottom_span)
        inner_depth = max(left_span, right_span)

        # Centers of the four sides
        top_z = -(inner_depth / 2.0 + top_thickness / 2.0)
        bottom_z = +(inner_depth / 2.0 + bottom_thickness / 2.0)
        left_x = -(inner_width / 2.0 + left_thickness / 2.0)
        right_x = +(inner_width / 2.0 + right_thickness / 2.0)

        self._place_row(width1, along='x', facing='z', x0=0.0, z0=top_z)
        self._place_row(width2, along='x', facing='-z', x0=0.0, z0=bottom_z)
        self._place_row(depth1, along='z', facing='x', x0=left_x, z0=0.0)
        self._place_row(depth2, along='z', facing='-x', x0=right_x, z0=0.0)

    @placemethod
    def place_grid(self, objects, cols):
        objects = self.to_list(objects)
        N = len(objects)
        if N == 0:
            return []

        if cols <= 0:
            raise ValueError("cols must be a positive integer")

        object_rows = []
        counter = 0
        tmp = []
        for obj in objects:
            tmp.append(obj)
            counter += 1
            if counter == cols:
                object_rows.append(tmp)
                tmp = []
                counter = 0
        if tmp:
            object_rows.append(tmp)

        row_depths = [max(obj.get_depth() for obj in row) for row in object_rows]

        total_depth = np.sum(row_depths)
        base_gap = self.sparsity * (total_depth / len(object_rows))

        rng = self.rng
        jitter_max = base_gap * self.randomness

        if len(object_rows) > 1:
            gaps = base_gap + rng.uniform(-jitter_max, jitter_max, size=len(object_rows) - 1)
        else:
            gaps = np.array([], dtype=np.float32)

        z_positions = [0.0]
        for i in range(1, len(object_rows)):
            prev_z = z_positions[i - 1]
            prev_depth = row_depths[i - 1]
            this_depth = row_depths[i]
            gap = gaps[i - 1]
            new_z = prev_z + 0.5 * prev_depth + gap + 0.5 * this_depth
            z_positions.append(new_z)

        center_offset = (z_positions[0] + z_positions[-1]) / 2
        z_positions = [z - center_offset for z in z_positions]

        for row in object_rows:
            self._place_row(row, along='x', facing='z', z0=z_positions.pop(0))

    @placemethod
    def place_arc(self, objects, towards=None):
        objects = self.to_list(objects)
        N = len(objects)
        if N == 0:
            return

        dist = np.max((np.log10(N), 1.0))
        inter_row_gap = self.sparsity * 0.5
        angle = 90 + self.sparsity * 60

        def angle_subtended(obj, radius):
            width = obj.get_width()
            depth = obj.get_depth()

            width += self.sparsity * width / 2
            depth += self.sparsity * depth / 2
            return (2 * np.arctan((width / 2) / (radius - depth / 2))) * 180 / np.pi

        def compute_object_rows():
            object_rows = []
            tmp = []
            curr_dist = dist
            used_angle = 0

            for obj in objects:
                obj_angle = angle_subtended(obj, curr_dist)
                if used_angle + obj_angle > angle:
                    if tmp:
                        object_rows.append(tmp)
                        curr_dist += 1.2 * max(o.get_depth() for o, _ in tmp) + inter_row_gap
                    tmp = [(obj, curr_dist)]
                    used_angle = obj_angle
                else:
                    tmp.append((obj, curr_dist))
                    used_angle += obj_angle

            if tmp:
                object_rows.append(tmp)

            return object_rows

        object_rows = compute_object_rows()
        if len(object_rows) > 2:
            while len(object_rows[-1]) < 0.3 * len(object_rows[-2]):
                inter_row_gap += 0.1
                object_rows = compute_object_rows()

        def compute_rotations(angle, N):
            if N == 1:
                return [0]
            if N % 2 == 1:
                half = N // 2
                return [(-half + i) * (angle / (N - 1)) for i in range(N)]
            else:
                half = N // 2
                return [(-half + 0.5 + i) * (angle / N) for i in range(N)]

        for row in object_rows:
            rots = compute_rotations(angle, len(row))
            for (obj, dist), rot in zip(row, rots):
                x = dist * np.sin(np.radians(rot)) + (self.rng.random() - 0.5) * self.randomness * self.sparsity * obj.get_width()
                y = self.compute_obj_y(obj)
                z = -dist * np.cos(np.radians(rot)) + (self.rng.random() - 0.5) * self.randomness * self.sparsity * obj.get_depth()
                obj.set_location(x, y, z)
                if towards is not None:
                    obj.face_towards(towards)
                else:
                    obj.set_rotation(-rot)
                self.add_child(obj)

    def compile(self):
        self.reset_compile_state()
        self.clear_constraints()
        self.execute_main_operations()
        self.compile_children()
        # GridGroup layout is deterministic — skip overlap/grad optimization
        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report


class RoomGroup(SceneProgObject):
    # Placement methods that take a `facing` argument and feed room-size computation.
    GRID_PLACEMENTS = frozenset({
        'place_on_center', 'place_on_back', 'place_on_front', 'place_on_left', 'place_on_right',
        'place_on_back_left', 'place_on_back_right', 'place_on_front_left', 'place_on_front_right',
        'place_on_back_wall_left', 'place_on_back_wall_center', 'place_on_back_wall_right',
        'place_on_front_wall_left', 'place_on_front_wall_center', 'place_on_front_wall_right',
        'place_on_left_wall_left', 'place_on_left_wall_center', 'place_on_left_wall_right',
        'place_on_right_wall_left', 'place_on_right_wall_center', 'place_on_right_wall_right',
        'place_on_back_left_corner', 'place_on_back_right_corner',
        'place_on_front_left_corner', 'place_on_front_right_corner',
    })

    # Which floor placements live in which (column, row) slot of the 5x5 layout grid.
    # Used to jitter a floor object within the free space of its own slot (randomness>0).
    # Wall-adjacent, corner, and wall-hung placements are intentionally excluded — moving
    # those off their wall/corner would look wrong.
    FLOOR_SLOTS = {
        'place_on_center': (2, 2),
        'place_on_back': (2, 1), 'place_on_front': (2, 3),
        'place_on_left': (1, 2), 'place_on_right': (3, 2),
        'place_on_back_left': (1, 1), 'place_on_back_right': (3, 1),
        'place_on_front_left': (1, 3), 'place_on_front_right': (3, 3),
    }

    def __init__(self, scene, name=None, modulate_scale=1.0, randomness=0.0,
                 auto_render=True, render_dir=None,
                 render_resolution=(1280, 900), render_samples=48, max_height=3.0):
        super().__init__(scene, name=name)
        self.modulate_scale = modulate_scale
        # Ceiling height is normally clamped to 3.0 m. For rooms with tall contents (a gym's
        # power racks / machines, a warehouse), raise this cap so the room can grow with its
        # tallest floor object instead of the ceiling cutting through it. Default 3.0 keeps
        # every existing scene identical (clip(_, 3.0, 3.0) == 3.0).
        self.max_height = float(max(max_height, 3.0))
        # Positional jitter (0..1) applied to free-standing floor placements within the
        # slack of their layout slot, for a less rigidly-centered, more natural room. Pure
        # translation (never rotation — that would break functional facing like a desk grid
        # toward a wall); the post-layout Overlap/OutOfBounds grad solve still applies.
        self.randomness = max(0.0, min(randomness, 1.0))
        self.rng = scene._make_rng() if scene is not None and hasattr(scene, "_make_rng") \
            else np.random.default_rng()
        self.wall_assets = {
            'back_wall': {'left': [], 'center': [], 'right': []},
            'left_wall': {'left': [], 'center': [], 'right': []},
            'right_wall': {'left': [], 'center': [], 'right': []},
            'front_wall': {'left': [], 'center': [], 'right': []},
        }
        # Interior auto-rendering: once the room is assembled (on compile), drop
        # a set of inside-the-room views (4 walls + 4 corners) so the layout can
        # be inspected without manually invoking the renderer. Disable with
        # scene.RoomGroup(auto_render=False).
        self.auto_render = auto_render
        self.render_dir = render_dir
        self.render_resolution = render_resolution
        self.render_samples = render_samples

    def _is_group_like(self, obj):
        return isinstance(obj, SceneProgObject) and len(obj.children) > 0

    def _get_wall_support_reference(self, obj, horizontal_axis="x", size_axis="width"):
        if obj is None:
            raise ValueError("obj cannot be None")

        if getattr(obj, "anchor", None) is not None:
            ref = obj.anchor
            aabb = ref.get_aabb()

            if horizontal_axis == "x":
                coord = ref.get_location()[0]
            elif horizontal_axis == "z":
                coord = ref.get_location()[2]
            else:
                raise ValueError(f"Unknown horizontal_axis: {horizontal_axis}")

            top_y = aabb[1, 1]

            if size_axis == "width":
                target_width = ref.get_width()
            elif size_axis == "depth":
                target_width = ref.get_depth()
            else:
                raise ValueError(f"Unknown size_axis: {size_axis}")

            return coord, top_y, target_width

        if self._is_group_like(obj):
            aabb = obj.get_aabb()

            if horizontal_axis == "x":
                coord = (aabb[0, 0] + aabb[1, 0]) / 2.0
            elif horizontal_axis == "z":
                coord = (aabb[0, 2] + aabb[1, 2]) / 2.0
            else:
                raise ValueError(f"Unknown horizontal_axis: {horizontal_axis}")

            top_y = aabb[1, 1]

            if size_axis == "width":
                target_width = aabb[1, 0] - aabb[0, 0]
            elif size_axis == "depth":
                target_width = aabb[1, 2] - aabb[0, 2]
            else:
                raise ValueError(f"Unknown size_axis: {size_axis}")

            return coord, top_y, target_width

        aabb = obj.get_aabb()

        if horizontal_axis == "x":
            coord = obj.get_location()[0]
        elif horizontal_axis == "z":
            coord = obj.get_location()[2]
        else:
            raise ValueError(f"Unknown horizontal_axis: {horizontal_axis}")

        top_y = aabb[1, 1]

        if size_axis == "width":
            target_width = obj.get_width()
        elif size_axis == "depth":
            target_width = obj.get_depth()
        else:
            raise ValueError(f"Unknown size_axis: {size_axis}")

        return coord, top_y, target_width

    def _register_wall_occupancy(self, wall_name, slots, obj):
        if isinstance(slots, str):
            slots = [slots]

        if wall_name not in self.wall_assets:
            raise ValueError(f"Unknown wall name: {wall_name}")

        for slot in slots:
            if slot not in ("left", "center", "right"):
                raise ValueError(f"Unknown wall slot: {slot}")

            if obj not in self.wall_assets[wall_name][slot]:
                self.wall_assets[wall_name][slot].append(obj)

    def _op(self, name):
        return self.get_operation(name)

    def _op_obj(self, name):
        op = self.get_operation(name)
        return op.obj if op is not None else None

    def _has_op(self, name):
        return self.get_operation(name) is not None

    def fill_facing_heuristic(self, placement, facing):
        import random
        if facing is not None:
            return facing
        placement = placement.replace('place_on_', '')
        if placement in ['back_wall_left', 'back_wall_center', 'back_wall_right']:
            return 'front'
        if placement in ['center', 'front', 'back', 'left', 'right', 'back_left', 'back_right', 'front_left', 'front_right']:
            return 'front'
        if placement in ['left_wall_left', 'left_wall_center', 'left_wall_right']:
            return 'right'
        if placement in ['right_wall_left', 'right_wall_center', 'right_wall_right']:
            return 'left'
        if placement in ['front_wall_left', 'front_wall_center', 'front_wall_right']:
            return 'back'
        if placement == 'back_left_corner':
            return random.choice(['front', 'right'])
        if placement == 'back_right_corner':
            return random.choice(['front', 'left'])
        if placement == 'front_left_corner':
            return random.choice(['back', 'right'])
        if placement == 'front_right_corner':
            return random.choice(['back', 'left'])

    def compute_dims_of_point(self, point):
        assert isinstance(point, str), "Point must be a string"
        point = 'place_on_' + point

        op = self._op(point)
        if op is None:
            return CIRCULATION_GAP, CIRCULATION_GAP, 0

        obj = op.obj
        facing = op.facing  # resolved (caller value or heuristic default) by the compile pre-pass

        w, h, d = obj.get_whd()
        if facing in ['front', 'back']:
            return w + CIRCULATION_GAP / 2, d + CIRCULATION_GAP / 2, h
        elif facing in ['left', 'right']:
            return d + CIRCULATION_GAP / 2, w + CIRCULATION_GAP / 2, h
        else:
            raise ValueError(f"Unknown facing direction: {facing}")

    def compute_grid_dims(self):
        col_widths = []
        tmp = []
        heights = []

        for point in ['back_left_corner', 'left_wall_right', 'left_wall_center', 'left_wall_left', 'front_left_corner']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(width)
            heights.append(height)
        col_widths.append(max(tmp))

        tmp = []
        for point in ['back_wall_left', 'back_left', 'left', 'front_left', 'front_wall_right']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(width)
            heights.append(height)
        col_widths.append(max(tmp))

        tmp = []
        for point in ['back_wall_center', 'back', 'center', 'front', 'front_wall_center']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(width)
            heights.append(height)
        col_widths.append(max(tmp))

        tmp = []
        for point in ['back_wall_right', 'back_right', 'right', 'front_right', 'front_wall_left']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(width)
            heights.append(height)
        col_widths.append(max(tmp))

        tmp = []
        for point in ['back_right_corner', 'right_wall_left', 'right_wall_center', 'right_wall_right', 'front_right_corner']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(width)
            heights.append(height)
        col_widths.append(max(tmp))

        row_depths = []

        tmp = []
        for point in ['back_left_corner', 'back_wall_left', 'back_wall_center', 'back_wall_right', 'back_right_corner']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(depth)
            heights.append(height)
        row_depths.append(max(tmp))

        tmp = []
        for point in ['left_wall_right', 'back_left', 'back', 'back_right', 'right_wall_left']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(depth)
            heights.append(height)
        row_depths.append(max(tmp))

        tmp = []
        for point in ['left_wall_center', 'left', 'center', 'right', 'right_wall_center']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(depth)
            heights.append(height)
        row_depths.append(max(tmp))

        tmp = []
        for point in ['left_wall_left', 'front_left', 'front', 'front_right', 'right_wall_right']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(depth)
            heights.append(height)
        row_depths.append(max(tmp))

        tmp = []
        for point in ['front_left_corner', 'front_wall_right', 'front_wall_center', 'front_wall_left', 'front_right_corner']:
            width, depth, height = self.compute_dims_of_point(point)
            tmp.append(depth)
            heights.append(height)
        row_depths.append(max(tmp))

        heights = np.array(heights)
        heights = np.max(heights)
        return col_widths, row_depths, heights

    def init_dims(self):
        col_widths, row_depths, heights = self.compute_grid_dims()
        cw = np.asarray(col_widths, dtype=float) * self.modulate_scale
        rd = np.asarray(row_depths, dtype=float) * self.modulate_scale
        self.WIDTH = float(np.sum(cw))
        self.DEPTH = float(np.sum(rd))
        # grow with the tallest floor object (+ headroom), clamped to [3.0, max_height]
        self.HEIGHT = float(np.clip(heights + 2.0, 3.0, self.max_height))
        # Cumulative center of each of the 5 columns / 5 rows. Placements land at
        # the center of their *sized* slot via these tables instead of fixed
        # W/4,W/2,3W/4 (and D/...) fractions — fractions assume evenly-sized rows,
        # so a deep item in one slot bled into the adjacent slot (e.g. a student
        # grid touching the teacher desk). col_centers[1..3]/row_centers[1..3] are
        # the interior floor slots; [0]/[4] are the wall rows/cols.
        self.col_centers = (np.cumsum(cw) - cw / 2.0).tolist()
        self.row_centers = (np.cumsum(rd) - rd / 2.0).tolist()
        # Per-slot sizes (after modulate_scale) — used to bound floor jitter to its own slot.
        self.col_widths = cw.tolist()
        self.row_depths = rd.tolist()

    def facing_to_rotation(self, facing):
        if facing == 'front':
            return 0
        elif facing == 'back':
            return 180
        elif facing == 'left':
            return -90
        elif facing == 'right':
            return 90
        else:
            raise ValueError(f"Unknown facing direction: {facing}")

    def wall_deltas(self, obj, facing):
        w, _, d = obj.get_whd()
        if facing in ['front', 'back']:
            return w / 2, d / 2
        else:
            return d / 2, w / 2

    def compute_occupancy(self):
        total_area = self.WIDTH * self.DEPTH
        occupied_area = 0.0
        for op in self.operations:
            if op is not None and op.obj is not None:
                occupied_area += op.obj.get_area()
        return occupied_area / total_area

    def _wall_furniture_y(self, obj, bottom, span):
        """Y-location for a floor/wall-mounted furniture piece, clamped to stay INSIDE
        the room. A piece placed with a ``bottom`` lift (a shelf mounted up the wall) or
        an oversized retrieved mesh could otherwise poke through the ceiling or run past
        the wall ends into a corner (the object extent is never checked against the room
        by the raw placement). Uniformly scale it down so (a) its along-wall footprint
        fits the wall ``span`` and (b) its lifted top clears the ceiling. Corrective only
        — it fires nothing for pieces that already fit, so existing scenes are unchanged.
        """
        b = bottom if bottom is not None else getattr(obj, "mount_bottom", 0.0)
        margin = 0.1
        # (a) along-wall footprint (the piece's width runs along the wall) <= wall span
        foot = obj.get_width()
        if foot > span - 2 * margin and foot > 1e-6:
            obj.scale(obj.get_width() * (span - 2 * margin) / foot)
        # (b) the lifted top must clear the ceiling
        h = obj.get_height()
        max_h = self.HEIGHT - b - margin
        if h > max_h and max_h > 1e-6:
            obj.scale(obj.get_width() * max_h / h)
        return self.compute_obj_y(obj) + b

    @placemethod
    def place_on_center(self, obj, facing=None):
        obj.set_location(self.col_centers[2], self.compute_obj_y(obj), self.row_centers[2])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back(self, obj, facing=None):
        obj.set_location(self.col_centers[2], self.compute_obj_y(obj), self.row_centers[1])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front(self, obj, facing=None):
        obj.set_location(self.col_centers[2], self.compute_obj_y(obj), self.row_centers[3])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left(self, obj, facing=None):
        obj.set_location(self.col_centers[1], self.compute_obj_y(obj), self.row_centers[2])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right(self, obj, facing=None):
        obj.set_location(self.col_centers[3], self.compute_obj_y(obj), self.row_centers[2])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_left(self, obj, facing=None):
        obj.set_location(self.col_centers[1], self.compute_obj_y(obj), self.row_centers[1])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_right(self, obj, facing=None):
        obj.set_location(self.col_centers[3], self.compute_obj_y(obj), self.row_centers[1])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_left(self, obj, facing=None):
        obj.set_location(self.col_centers[1], self.compute_obj_y(obj), self.row_centers[3])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_right(self, obj, facing=None):
        obj.set_location(self.col_centers[3], self.compute_obj_y(obj), self.row_centers[3])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_wall_left(self, obj, facing=None, bottom=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.col_centers[1], self._wall_furniture_y(obj, bottom, self.WIDTH), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_wall_center(self, obj, facing=None, bottom=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.col_centers[2], self._wall_furniture_y(obj, bottom, self.WIDTH), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_wall_right(self, obj, facing=None, bottom=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.col_centers[3], self._wall_furniture_y(obj, bottom, self.WIDTH), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left_wall_right(self, obj, facing=None, bottom=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self._wall_furniture_y(obj, bottom, self.DEPTH), self.row_centers[1])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left_wall_center(self, obj, facing=None, bottom=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self._wall_furniture_y(obj, bottom, self.DEPTH), self.row_centers[2])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left_wall_left(self, obj, facing=None, bottom=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self._wall_furniture_y(obj, bottom, self.DEPTH), self.row_centers[3])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right_wall_left(self, obj, facing=None, bottom=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self._wall_furniture_y(obj, bottom, self.DEPTH), self.row_centers[1])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right_wall_center(self, obj, facing=None, bottom=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self._wall_furniture_y(obj, bottom, self.DEPTH), self.row_centers[2])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right_wall_right(self, obj, facing=None, bottom=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self._wall_furniture_y(obj, bottom, self.DEPTH), self.row_centers[3])
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_wall_left(self, obj, facing=None, bottom=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.col_centers[3], self._wall_furniture_y(obj, bottom, self.WIDTH), self.DEPTH - delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_wall_center(self, obj, facing=None, bottom=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.col_centers[2], self._wall_furniture_y(obj, bottom, self.WIDTH), self.DEPTH - delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_wall_right(self, obj, facing=None, bottom=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.col_centers[1], self._wall_furniture_y(obj, bottom, self.WIDTH), self.DEPTH - delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_left_corner(self, obj, facing=None):
        delta_w, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self.compute_obj_y(obj), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_right_corner(self, obj, facing=None):
        delta_w, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self.compute_obj_y(obj), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_left_corner(self, obj, facing=None):
        delta_w, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self.compute_obj_y(obj), self.DEPTH - delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_right_corner(self, obj, facing=None):
        delta_w, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self.compute_obj_y(obj), self.DEPTH - delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    def _place_on_wall(self, obj, x, y, z, rot, target_width):
        orig_width = max(obj.get_width(), 1e-6)
        orig_height = max(obj.get_height(), 1e-6)
        orig_depth = max(obj.get_depth(), 1e-6)

        new_width, new_height = self.wall_obj_scale_computer(orig_width, orig_height, target_width)

        sx = new_width / orig_width
        sy = new_height / orig_height
        new_depth = 0.5 * (sx + sy) * orig_depth

        obj.scale_only_width(new_width)
        obj.scale_only_height(new_height)
        obj.scale_only_depth(new_depth)
        obj.set_location(x, y, z)
        obj.set_rotation(rot)
        obj.ignore_overlap = True
        self.add_child(obj)

    @placemethod
    def place_on_wall_back_center(self, obj):
        self._register_wall_occupancy('back_wall', 'center', obj)
        z = obj.get_depth() / 2 + BUFFER
        op = self._op('place_on_back_wall_center')

        if op is not None:
            x, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="x", size_axis="width"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
            y = max(y, (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2)
        else:
            x = self.WIDTH / 2
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.WIDTH / 3) * 0.6

        target_width = min(target_width, (self.WIDTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 0, target_width)

    @placemethod
    def place_on_wall_back_left(self, obj):
        self._register_wall_occupancy('back_wall', 'left', obj)
        z = obj.get_depth() / 2 + BUFFER
        op = self._op('place_on_back_wall_left')

        if op is not None:
            x, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="x", size_axis="width"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            x = self.WIDTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.WIDTH / 3) * 0.6

        target_width = min(target_width, (self.WIDTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 0, target_width)

    @placemethod
    def place_on_wall_back_right(self, obj):
        self._register_wall_occupancy('back_wall', 'right', obj)
        z = obj.get_depth() / 2 + BUFFER
        op = self._op('place_on_back_wall_right')

        if op is not None:
            x, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="x", size_axis="width"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            x = 3 * self.WIDTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.WIDTH / 3) * 0.6

        target_width = min(target_width, (self.WIDTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 0, target_width)

    @placemethod
    def place_on_wall_left_right(self, obj):
        self._register_wall_occupancy('left_wall', 'right', obj)
        x = obj.get_depth() / 2 + BUFFER
        op = self._op('place_on_left_wall_right')

        if op is not None:
            z, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="z", size_axis="depth"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            z = self.DEPTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.DEPTH / 3) * 0.6

        target_width = min(target_width, (self.DEPTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 90, target_width)

    @placemethod
    def place_on_wall_left_center(self, obj):
        self._register_wall_occupancy('left_wall', 'center', obj)
        x = obj.get_depth() / 2 + BUFFER
        op = self._op('place_on_left_wall_center')

        if op is not None:
            z, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="z", size_axis="depth"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            z = self.DEPTH / 2
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.DEPTH / 3) * 0.6

        target_width = min(target_width, (self.DEPTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 90, target_width)

    @placemethod
    def place_on_wall_left_left(self, obj):
        self._register_wall_occupancy('left_wall', 'left', obj)
        x = obj.get_depth() / 2 + BUFFER
        op = self._op('place_on_left_wall_left')

        if op is not None:
            z, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="z", size_axis="depth"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            z = 3 * self.DEPTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.DEPTH / 3) * 0.6

        target_width = min(target_width, (self.DEPTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 90, target_width)

    @placemethod
    def place_on_wall_right_left(self, obj):
        self._register_wall_occupancy('right_wall', 'left', obj)
        x = self.WIDTH - obj.get_depth() / 2 - BUFFER
        op = self._op('place_on_right_wall_left')

        if op is not None:
            z, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="z", size_axis="depth"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            z = self.DEPTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.DEPTH / 3) * 0.6

        target_width = min(target_width, (self.DEPTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, -90, target_width)

    @placemethod
    def place_on_wall_right_center(self, obj):
        self._register_wall_occupancy('right_wall', 'center', obj)
        x = self.WIDTH - obj.get_depth() / 2 - BUFFER
        op = self._op('place_on_right_wall_center')

        if op is not None:
            z, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="z", size_axis="depth"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            z = self.DEPTH / 2
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.DEPTH / 3) * 0.6

        target_width = min(target_width, (self.DEPTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, -90, target_width)

    @placemethod
    def place_on_wall_right_right(self, obj):
        self._register_wall_occupancy('right_wall', 'right', obj)
        x = self.WIDTH - obj.get_depth() / 2 - BUFFER
        op = self._op('place_on_right_wall_right')

        if op is not None:
            z, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="z", size_axis="depth"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            z = 3 * self.DEPTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.DEPTH / 3) * 0.6

        target_width = min(target_width, (self.DEPTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, -90, target_width)

    @placemethod
    def place_on_wall_front_left(self, obj):
        self._register_wall_occupancy('front_wall', 'left', obj)
        z = self.DEPTH - obj.get_depth() / 2 - BUFFER
        op = self._op('place_on_front_wall_left')

        if op is not None:
            x, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="x", size_axis="width"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            x = 3 * self.WIDTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.WIDTH / 3) * 0.6

        target_width = min(target_width, (self.WIDTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 180, target_width)

    @placemethod
    def place_on_wall_front_center(self, obj):
        self._register_wall_occupancy('front_wall', 'center', obj)
        z = self.DEPTH - obj.get_depth() / 2 - BUFFER
        op = self._op('place_on_front_wall_center')

        if op is not None:
            x, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="x", size_axis="width"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            x = self.WIDTH / 2
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.WIDTH / 3) * 0.6

        target_width = min(target_width, (self.WIDTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 180, target_width)

    @placemethod
    def place_on_wall_front_right(self, obj):
        self._register_wall_occupancy('front_wall', 'right', obj)
        z = self.DEPTH - obj.get_depth() / 2 - BUFFER
        op = self._op('place_on_front_wall_right')

        if op is not None:
            x, y_top, target_width = self._get_wall_support_reference(
                op.obj, horizontal_axis="x", size_axis="width"
            )
            y = y_top + FURNITURE_CLEARANCE + obj.get_height() / 2
        else:
            x = self.WIDTH / 4
            y = (WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX) / 2
            target_width = (self.WIDTH / 3) * 0.6

        target_width = min(target_width, (self.WIDTH / 3) * 0.6)
        self._place_on_wall(obj, x, y, z, 180, target_width)

    def wall_obj_scale_computer(self, w, h, W):
        lambda1 = 1.0
        lambda2 = 10
        lambda3 = 1.0

        w_grid = np.linspace(0.25 * w, 5 * w, 200)
        h_grid = np.linspace(0.25 * h, 5 * h, 200)

        wd_grid = np.array(np.meshgrid(w_grid, h_grid)).T.reshape(-1, 2)

        ratio = (W / wd_grid[:, 0])
        L1 = lambda1 * np.abs(np.log(ratio))
        L2 = lambda2 * (np.maximum((wd_grid[:, 1] - 1), 0)) ** 2
        ratio = (wd_grid[:, 0] / wd_grid[:, 1]) / (w / h)
        L3 = lambda3 * np.abs(np.log(ratio))

        L_total = L1 + L2 + L3
        min_index = np.argmin(L_total)

        return wd_grid[min_index, 0], wd_grid[min_index, 1]

    @placemethod
    def place_walls(self, floor_texture: str, ceiling_texture: str, wall_texture: str):
        from wall import BackWall, FrontWall, LeftWall, RightWall, Ceiling, Floor, WallTextureRetriever
        import os

        cell_size = 0.05
        wall_texture_retriever = WallTextureRetriever(
            os.path.join(os.path.dirname(__file__), "datasets/futurehssd", "3D-FRONT-texture")
        )
        wall_texture = wall_texture_retriever(wall_texture)
        back_wall = BackWall(self.WIDTH, self.HEIGHT, self.DEPTH, wall_texture, cell_size=cell_size)
        front_wall = FrontWall(self.WIDTH, self.HEIGHT, self.DEPTH, wall_texture, cell_size=cell_size)
        left_wall = LeftWall(self.WIDTH, self.HEIGHT, self.DEPTH, wall_texture, cell_size=cell_size)
        right_wall = RightWall(self.WIDTH, self.HEIGHT, self.DEPTH, wall_texture, cell_size=cell_size)
        ceiling_texture = wall_texture_retriever(ceiling_texture)
        ceiling = Ceiling(self.WIDTH, self.HEIGHT, self.DEPTH, ceiling_texture, cell_size=cell_size)
        floor_texture = wall_texture_retriever(floor_texture)
        floor = Floor(self.WIDTH, self.HEIGHT, self.DEPTH, floor_texture, cell_size=cell_size)

        self.scene.walls.extend([back_wall, front_wall, left_wall, right_wall, ceiling, floor])
        self.back_wall = back_wall
        self.front_wall = front_wall
        self.left_wall = left_wall
        self.right_wall = right_wall

    def wall_transform_position(self, position, wall):
        if wall == 'back_wall':
            return position[0], position[1], position[2]
        elif wall == 'left_wall':
            return position[2], position[1], position[0]
        elif wall == 'front_wall':
            return position[0], position[1], self.DEPTH - position[2]
        elif wall == 'right_wall':
            return self.WIDTH - position[2], position[1], position[0]
        else:
            raise ValueError(f"Unknown wall: {wall}")

    def wall_translate(self, mesh, translation):
        if isinstance(translation, (list, tuple)):
            translation = np.array(translation)

        vertices = mesh.vertices
        center = np.mean(vertices, axis=0)
        vertices -= center
        vertices += translation
        mesh.vertices = vertices
        return mesh

    def wall_rotate(self, mesh, wall):
        def rot(mesh_, angle):
            from scipy.spatial.transform import Rotation as R
            rotation = R.from_euler('y', angle, degrees=True)
            T = np.eye(4)
            T[:3, :3] = rotation.as_matrix()
            mesh_.apply_transform(T)

        if wall.name == 'back_wall':
            rot(mesh, 0)
        elif wall.name == 'left_wall':
            rot(mesh, 270)
        elif wall.name == 'front_wall':
            rot(mesh, 180)
        elif wall.name == 'right_wall':
            rot(mesh, 270)
        return mesh

    def wall_scale(self, mesh, width, height, scale_depth=False):
        vertices = mesh.vertices
        vertices[:, 0] -= np.min(vertices[:, 0])
        vertices[:, 1] -= np.min(vertices[:, 1])
        vertices[:, 0] *= width / np.max(vertices[:, 0])
        vertices[:, 1] *= height / np.max(vertices[:, 1])
        if scale_depth:
            vertices[:, 2] *= 0.05 / np.max(vertices[:, 2])
        return mesh

    def cut_wall(self, wall):
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

    def _wall_name_to_wall(self, wall_name):
        if wall_name == 'back_wall':
            return self.back_wall
        elif wall_name == 'left_wall':
            return self.left_wall
        elif wall_name == 'front_wall':
            return self.front_wall
        elif wall_name == 'right_wall':
            return self.right_wall
        else:
            raise ValueError(f"Unknown wall name: {wall_name}")

    @placemethod
    def place_door(self, wall, position):
        from door import Door
        door = Door(self.WIDTH, self.HEIGHT, self.DEPTH)
        wall_ = self._wall_name_to_wall(wall)
        door.add_door(wall_, position)
        self._register_wall_occupancy(wall, position, door)
        self.scene.wall_objects.append(door)

    @placemethod
    def place_window_floor_to_ceiling(self, wall, curtain=None):
        from window import Window
        window = Window(self.WIDTH, self.HEIGHT, self.DEPTH)
        wall_ = self._wall_name_to_wall(wall)
        window, curtain = window.add_window_floor_to_ceiling(wall_, curtain_texture=curtain)

        self.scene.walls.remove(wall_)
        self._register_wall_occupancy(wall, ["left", "center", "right"], window)
        self.scene.wall_objects.append(window)

        if curtain:
            self.scene.wall_objects.append(curtain)

    @placemethod
    def place_mirror_full_wall(self, wall):
        """Cover an entire wall with one floor-to-ceiling mirror (a real Cycles reflection).

        Unlike a retrieved wall-mirror prop this spans the whole wall as a single reflective
        surface, and unlike a window it leaves the wall intact (a mirror hangs on the wall).
        Occupies all three slots of that wall, so mount nothing else on it."""
        from mirror import Mirror
        mirror = Mirror(self.WIDTH, self.HEIGHT, self.DEPTH)
        wall_ = self._wall_name_to_wall(wall)
        mirror.add_mirror_floor_to_ceiling(wall_)

        self._register_wall_occupancy(wall, ["left", "center", "right"], mirror)
        self.scene.wall_objects.append(mirror)

    @placemethod
    def place_window_picture(self, wall, curtain=None):
        from window import Window
        window = Window(self.WIDTH, self.HEIGHT, self.DEPTH)
        wall_ = self._wall_name_to_wall(wall)
        window, curtain = window.add_window_picture(wall_, curtain_texture=curtain)

        self._register_wall_occupancy(wall, ["left", "center", "right"], window)
        self.scene.wall_objects.append(window)

        if curtain:
            self.scene.wall_objects.append(curtain)

    @placemethod
    def place_window_standard(self, wall, position, curtain=None):
        from window import Window
        window = Window(self.WIDTH, self.HEIGHT, self.DEPTH)
        wall_ = self._wall_name_to_wall(wall)
        window, curtain = window.add_window_standard(wall_, position, curtain_texture=curtain)

        self._register_wall_occupancy(wall, position, window)
        self.scene.wall_objects.append(window)

        if curtain:
            self.scene.wall_objects.append(curtain)

    @placemethod
    def place_on_wall_freeform(self, wall, objs):
        wall_ = self._wall_name_to_wall(wall)
        height = wall_.height

        if wall == 'back_wall':
            width = wall_.width
            obj_widths = [obj.get_width() for obj in objs]
            rot = 0
        elif wall == 'left_wall':
            rot = 90
            # LeftWall/RightWall store the room depth span in their `width` attribute.
            depth = wall_.width
            obj_depths = [obj.get_depth() for obj in objs]
        elif wall == 'front_wall':
            width = wall_.width
            obj_widths = [obj.get_width() for obj in objs]
            rot = 180
        elif wall == 'right_wall':
            rot = 270
            depth = wall_.width
            obj_depths = [obj.get_depth() for obj in objs]
        else:
            raise ValueError(f"Unknown wall: {wall}")

        if wall in ['back_wall', 'front_wall']:
            total_width = sum(obj_widths)
            if total_width > width * 0.5:
                scaling_factor = (width / total_width) * 0.5
                obj_widths = [w * scaling_factor for w in obj_widths]

            spacing = (width - total_width) / (len(objs) + 1)
            current_x = spacing
            xs, zs = [], []
            for obj in objs:
                xs.append(current_x + obj.get_width() / 2)  # center x
                current_x += obj.get_width() + spacing
                zs.append(obj.get_depth() / 2)
        else:
            total_width = sum(obj_depths)
            if total_width > depth * 0.5:
                scaling_factor = (depth / total_width) * 0.5
                obj_depths = [d * scaling_factor for d in obj_depths]

            spacing = (depth - total_width) / (len(objs) + 1)
            current_z = spacing
            xs, zs = [], []
            for obj in objs:
                xs.append(0.0)
                zs.append(current_z + obj.get_depth() / 2)  # center z
                current_z += obj.get_depth() + spacing
            obj_widths = obj_depths

        for i, obj in enumerate(objs):
            self._place_on_wall(obj, xs[i], height / 2, zs[i], rot, obj_widths[i])

    def compute_occupancy_ratio(self):
        area = 0.0
        for obj in self.children:
            area += obj.get_area()

        total_area = self.WIDTH * self.DEPTH
        return area / total_area if total_area > 0 else 0.0

    def _apply_face_wall(self, obj, wall_name):
        """Rotate `obj` to face the named wall, snapped to the nearest 90 degrees.

        Faces the wall's center direction (not an exact object) so the result is
        always orthogonal — the right tool for functional orientation like a desk
        grid facing the teacher's wall. The room spans [0,WIDTH]x[0,DEPTH] with
        back_wall at z=0, front_wall at z=DEPTH, left_wall at x=0, right_wall at x=WIDTH.
        """
        centers = {
            "back_wall":  (self.WIDTH / 2.0, 0.0),
            "front_wall": (self.WIDTH / 2.0, self.DEPTH),
            "left_wall":  (0.0, self.DEPTH / 2.0),
            "right_wall": (self.WIDTH, self.DEPTH / 2.0),
        }
        if wall_name not in centers:
            raise ValueError(
                f"Unknown wall name {wall_name!r}; expected one of {list(centers)}"
            )

        loc = obj.get_world_location()
        tx, tz = centers[wall_name]
        dx, dz = tx - float(loc[0]), tz - float(loc[2])
        if abs(dx) < 1e-6 and abs(dz) < 1e-6:
            return  # object sits at the wall's center line; nothing to do

        rot = np.degrees(np.arctan2(dx, dz))   # same convention as face_towards
        rot = round(rot / 90.0) * 90.0         # snap to the nearest 90 degrees
        obj.set_rotation(rot % 360.0)

    def _apply_floor_jitter(self):
        """Nudge each free-standing floor placement within the free space of its own slot.

        Runs after the floor placements execute (so col/row centers and object sizes are
        known) and before the gradient solve (which still resolves any overlap the jitter
        introduces). Translation only — facing is preserved. A larger object in a tight slot
        has little slack and so barely moves; a small object in a roomy slot moves more."""
        if self.randomness <= 0:
            return
        for op in self.operations:
            slot = self.FLOOR_SLOTS.get(op.name)
            if slot is None or op.obj is None:
                continue
            ci, ri = slot
            obj = op.obj
            slack_x = max(0.0, self.col_widths[ci] - float(obj.get_width())) / 2.0
            slack_z = max(0.0, self.row_depths[ri] - float(obj.get_depth())) / 2.0
            if slack_x <= 0 and slack_z <= 0:
                continue
            t = obj.transform.translation
            dx = float(self.rng.uniform(-1, 1)) * self.randomness * slack_x
            dz = float(self.rng.uniform(-1, 1)) * self.randomness * slack_z
            obj.set_location(t[0] + dx, t[1], t[2] + dz)

    # Auto door clearance: every doorway keeps a patch of floor clear so a door can
    # open and people can pass. Reuses the existing ClearanceConstraint via an invisible,
    # static floor proxy at the doorway — no new constraint type, zero author action.
    DOOR_CLEARANCE = 0.9       # metres kept clear in front of a doorway
    DOOR_PROXY_DEPTH = 0.05    # thin footprint hugging the wall

    def _make_door_proxy(self, door_width, center_along_wall, wall_name):
        """Invisible, static floor proxy at a doorway, facing into the room. Carries no
        mesh (never rendered/exported) but has a footprint the ClearanceConstraint pushes
        floor furniture away from."""
        facing = {'back_wall': 0.0, 'front_wall': 180.0,
                  'left_wall': 90.0, 'right_wall': 270.0}[wall_name]
        depth = self.DOOR_PROXY_DEPTH
        # wall-local (along-wall, height, into-room) -> room coords (mirrors window.transform_position)
        if wall_name == 'back_wall':
            rx, rz = center_along_wall, depth
        elif wall_name == 'front_wall':
            rx, rz = center_along_wall, self.DEPTH - depth
        elif wall_name == 'left_wall':
            rx, rz = depth, center_along_wall
        else:  # right_wall
            rx, rz = self.WIDTH - depth, center_along_wall

        hw, hd = door_width / 2.0, depth / 2.0
        verts = np.array([
            [-hw, 0.0, -hd], [hw, 0.0, -hd], [hw, 0.0, hd], [-hw, 0.0, hd],
            [-hw, 0.1, -hd], [hw, 0.1, -hd], [hw, 0.1, hd], [-hw, 0.1, hd],
        ], dtype=np.float32)

        proxy = SceneProgObject(self.scene, name="door_clearance_proxy")
        proxy.vertices = verts
        proxy.mesh_path = None        # -> skipped in _build_blend (never rendered)
        proxy.ignore_overlap = True   # -> skipped by Overlap / snap / clamp passes
        proxy.is_static = True        # -> grad zeroed each solver step (never moves)
        proxy.is_proxy = True         # -> purged before each recompile
        proxy.set_rotation(facing)
        proxy.set_location(float(rx), 0.05, float(rz))
        proxy.parent = self
        return proxy

    def _doorway_specs(self):
        """(wall_name, center_along_wall, door_width) for every placed door."""
        specs = []
        for op in self.operations:
            if op is None or op.name != 'place_door':
                continue
            wall = op.arguments.get('wall')
            position = op.arguments.get('position')
            wall_ = self._wall_name_to_wall(wall)
            door_width, _ = wall_.get_partition_dimensions_by_label(position, margin=0.05)
            door_height = 0.7 * wall_.height
            if door_width > 0.5 * door_height:
                door_width = 0.5 * door_height
            if door_width <= 0:
                continue
            center_along, _ = wall_.get_partition_center_by_label(position, margin=0.0)
            specs.append((wall, center_along, door_width))
        return specs

    def _register_door_clearances(self):
        """Drop an invisible static proxy at each placed doorway and register a
        ClearanceConstraint so floor furniture is nudged clear of it during the solve."""
        # purge proxies from a previous compile so they don't accumulate
        self.children = [c for c in self.children if not getattr(c, "is_proxy", False)]
        for wall, center_along, door_width in self._doorway_specs():
            proxy = self._make_door_proxy(door_width, center_along, wall)
            self.children.append(proxy)
            self.ClearanceConstraint(proxy, distance=self.DOOR_CLEARANCE, dir="front")

    def _enforce_door_clearances(self):
        """Deterministic guarantee (run after the stochastic solve, like _snap_overlaps /
        _clamp_to_bounds): push any floor item that still intrudes into a doorway band out
        along the inward wall normal, so every doorway is actually walkable. The gradient
        proxy above usually does this during the solve; this pass guarantees it even for
        large/heavy furniture the area-weighted solver moves slowly."""
        clear = self.DOOR_CLEARANCE
        moved = False
        floor_children = [c for c in self.children
                          if not getattr(c, "is_proxy", False)
                          and not getattr(c, "ignore_overlap", False)
                          and not getattr(c, "is_light", False)]
        for wall, center_along, door_width in self._doorway_specs():
            hw = door_width / 2.0
            for c in floor_children:
                aabb = c.get_aabb()
                xmin, _, zmin = aabb[0]
                xmax, _, zmax = aabb[1]
                if wall in ('back_wall', 'front_wall'):
                    # door spans x in [center-hw, center+hw]; band is `clear` deep off the wall
                    if xmax <= center_along - hw or xmin >= center_along + hw:
                        continue
                    if wall == 'back_wall':              # wall at z=0, push +z
                        if zmin < clear:
                            c.translate(0, 0, clear - zmin); moved = True
                    else:                                # front wall at z=DEPTH, push -z
                        if zmax > self.DEPTH - clear:
                            c.translate(0, 0, (self.DEPTH - clear) - zmax); moved = True
                else:
                    if zmax <= center_along - hw or zmin >= center_along + hw:
                        continue
                    if wall == 'left_wall':              # wall at x=0, push +x
                        if xmin < clear:
                            c.translate(clear - xmin, 0, 0); moved = True
                    else:                                # right wall at x=WIDTH, push -x
                        if xmax > self.WIDTH - clear:
                            c.translate((self.WIDTH - clear) - xmax, 0, 0); moved = True
        if moved:
            # repair any overlaps / OOB the push introduced (reuses the solver's deterministic passes,
            # alternating them so a bounds-clamp can't leave a re-introduced overlap — see _settle)
            self.grad_solver.objects = self.children
            self.grad_solver._settle()

    def _warn_over_height(self, tol=0.02):
        """Warn at compile time about any placed object whose top pokes through the ceiling.

        The room auto-sizes its WIDTH/DEPTH from the furniture footprint, but its HEIGHT is
        only grown to the tallest *floor* object (clamped to [3.0, max_height]). Wall-mounted
        art/fixtures are positioned relative to their support (e.g. a clock stacked above a
        locker bank) and their scale tracks the wall width, so in a wide room a big wall item
        can end up above HEIGHT and clip through the ceiling — which no constraint catches.
        There is no auto-fix (raising the ceiling changes the whole room), so we surface it:
        print a warning and record it in scene.vlm_feedback so the workbench report shows it.
        Fix by shrinking the offending asset (modulate_scale/width) or raising the ceiling with
        RoomGroup(max_height=...)."""
        offenders = []
        for obj in list(getattr(self.scene, "objects", [])):
            try:
                top = float(obj.get_aabb()[1, 1])
            except Exception:
                continue
            if top > self.HEIGHT + tol:
                offenders.append((getattr(obj, "name", "?"),
                                  getattr(obj, "retrieval_query", "") or "", top))
        if not offenders:
            return
        need = max(t for _, _, t in offenders)
        lines = [f"[RoomGroup] WARNING: {len(offenders)} object(s) exceed the room height "
                 f"(HEIGHT={self.HEIGHT:.2f} m). They will clip through the ceiling."]
        for name, q, top in sorted(offenders, key=lambda o: -o[2]):
            lines.append(f"    - {name} '{q[:40]}' top={top:.2f} m (over by {top - self.HEIGHT:+.2f} m)")
        lines.append(f"    Fix: shrink the asset (modulate_scale/width) or raise the ceiling with "
                     f"RoomGroup(max_height={need + 0.2:.1f}).")
        msg = "\n".join(lines)
        print(msg)
        self.scene.vlm_feedback += ("\n" if self.scene.vlm_feedback else "") + msg

    def _warn_overlaps(self, min_penetration=0.05):
        """Final guarantee CHECK: after the whole room is assembled, verify no two floor objects
        still interpenetrate. The gradient solve + _settle resolve overlaps whenever the room is
        big enough; a residual overlap almost always means the room is TOO SMALL — the furniture
        footprints don't fit, so separating one pair only forces another together and the clamp
        can't win. There is no safe auto-fix (growing the room silently would fight the author's
        modulate_scale), so we surface it: print + record in scene.vlm_feedback, routed alongside
        the RoomProportions signal so the workbench report shows it. Fix by enlarging the room
        (raise modulate_scale / RoomGroup size) or removing/shrinking some furniture."""
        solver = getattr(self, "grad_solver", None)
        if solver is None:
            return
        solver.objects = [c for c in self.children
                          if not getattr(c, "is_proxy", False)
                          and not getattr(c, "is_light", False)]
        pairs = solver.overlap_pairs(min_penetration=min_penetration)
        if not pairs:
            return

        def _q(o):
            return (getattr(o, "retrieval_query", None) or getattr(o, "name", None)
                    or o.__class__.__name__)

        occ = None
        try:
            occ = self.compute_occupancy_ratio()
        except Exception:
            pass
        lines = [f"[RoomGroup] WARNING: {len(pairs)} pair(s) of floor objects still OVERLAP after the "
                 f"solve — the room is likely TOO SMALL to hold this furniture"
                 + (f" (occupancy ratio {occ:.2f})." if occ is not None else ".")]
        for o1, o2, ox, oz in sorted(pairs, key=lambda p: -(p[2] * p[3])):
            lines.append(f"    - '{_q(o1)[:36]}' X '{_q(o2)[:36]}' "
                         f"(penetration {ox:.2f}x{oz:.2f} m)")
        lines.append("    Fix: enlarge the room (raise RoomGroup(modulate_scale=...) or reduce its "
                     "contents); overlaps here mean the gradient solve could not separate them.")
        msg = "\n".join(lines)
        print(msg)
        self.scene.vlm_feedback += ("\n" if self.scene.vlm_feedback else "") + msg

    def compile(self):
        self.reset_compile_state()
        self.clear_constraints()

        # Resolve each grid placement's facing exactly once (caller value, else heuristic
        # default) and inject it back into the op so both room-sizing and the placement body
        # see the same value. Idempotent on recompile, and resolving once keeps the random
        # corner choice consistent between sizing and placement.
        for op in self.operations:
            if op is not None and op.name in self.GRID_PLACEMENTS:
                resolved = self.fill_facing_heuristic(op.name, op.facing)
                op.facing = resolved
                op.arguments['facing'] = resolved

        self.init_dims()

        skip_for_now = {
            'place_on_wall_back_center', 'place_on_wall_back_left', 'place_on_wall_back_right',
            'place_on_wall_left_right', 'place_on_wall_left_center', 'place_on_wall_left_left',
            'place_on_wall_right_left', 'place_on_wall_right_center', 'place_on_wall_right_right',
            'place_on_wall_front_left', 'place_on_wall_front_center', 'place_on_wall_front_right',
            'place_window_floor_to_ceiling', 'place_window_picture', 'place_window_standard',
            'place_door',
        }

        for op in self.operations:
            if op.name in skip_for_now:
                continue
            op.execute()

        # Add positional jitter to free-standing floor placements (no-op when randomness=0),
        # before the solve so any introduced overlap is resolved.
        self._apply_floor_jitter()

        self.compile_children()

        # Auto-invoke door clearance: add invisible static proxies at every doorway and
        # register their ClearanceConstraint before the solve, so floor furniture is
        # pushed out of the doorway just like any author-added clearance.
        self._register_door_clearances()

        self.OverlapConstraint()
        self.OutOfBoundsConstraint()
        self._run_constraint_hooks()
        self.grad_optimize()

        # Deterministic doorway guarantee: ensure every doorway band is actually clear,
        # even for large furniture the area-weighted solver moves slowly.
        self._enforce_door_clearances()

        for op in self.operations:
            if op.name in skip_for_now:
                op.execute()

        for asset in self.scene.ceiling_lights:
            x, _, z = asset.transform.decompose_matrix()[0]
            asset.set_location(x, self.HEIGHT - asset.get_height() / 2, z)

        self.scene.WIDTH = self.WIDTH
        self.scene.DEPTH = self.DEPTH
        self.scene.HEIGHT = self.HEIGHT

        # Flag anything whose top pokes through the ceiling (see _warn_over_height).
        self._warn_over_height()

        # Final overlap guarantee-check: flag any floor objects that still interpenetrate
        # (almost always = the room is too small for its furniture). See _warn_overlaps.
        self._warn_overlaps()

        # Apply opt-in rotation overrides after layout/wall placement settle, so the
        # VLM rotation check below judges the corrected orientation.
        self._apply_orientations()

        self.RoomProportionsConstraint()
        self.RotationConstraint()
        self.WallOverlapConstraint()
        self.vlm_optimize()

        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()

        if self.auto_render:
            self.render_interior()

        return self.last_compile_report

    def render_interior(self, output_dir=None):
        """
        Render a set of inside-the-room views of the assembled room — four
        wall-facing shots and four 3/4 corner overviews — into output_dir
        (default: the run's tmp scratchpad, tmp/<run id>/room_views). Builds a
        temporary .blend from the current scene state (the same serialization
        render() uses) and drives the interior cameras in IDSDL/renderer.
        Returns the output directory.

        Wrapped so a renderer/Blender problem never breaks scene assembly.
        """
        from IDSDL.renderer.renderer import SceneRenderer

        if output_dir is None:
            output_dir = self.render_dir or self._run_dir("room_views")

        try:
            blend_path = self._build_blend()
            rx, ry = self.render_resolution
            renderer = SceneRenderer(
                resolution_x=rx, resolution_y=ry,
                samples=self.render_samples, verbose=True,
            )
            renderer.render_room(blend_path, output_dir)
            print(f"[RoomGroup] interior views written to '{output_dir}/'")
        except Exception as e:
            print(f"[RoomGroup] interior auto-render skipped ({type(e).__name__}: {e})")
        return output_dir

    def render_interior_combined(self, resolution=(640, 480), samples=None):
        """
        Render the four interior wall views and stack them side by side into one
        image (back | front | left | right), returning its path. This is the
        inside-the-room analogue of SceneProgObject.render(): VLM constraints on
        a closed room must see the interior, not the exterior box.
        """
        import matplotlib.pyplot as plt
        from IDSDL.renderer.renderer import SceneRenderer

        run_dir = self._run_dir("vlm_views")
        blend_path = self._build_blend()

        rx, ry = resolution
        renderer = SceneRenderer(
            resolution_x=rx, resolution_y=ry,
            samples=samples if samples is not None else self.render_samples,
            verbose=True,
        )

        uid = random.randint(0, 1000000)
        wall_paths = [
            os.path.join(run_dir, f"{name}_{uid}.png")
            for name in ("back", "front", "left", "right")
        ]
        renderer.render_interior_walls(blend_path, wall_paths)

        combined = np.hstack([plt.imread(p) for p in wall_paths])
        combined_path = os.path.join(run_dir, f"combined_{uid}.png")
        plt.imsave(combined_path, combined)
        return combined_path

    # -----------------------------------------------------------------
    # COLLECTION COLLAGE
    #
    # A planner-style 2xN montage of the BUILT room: a tightly-framed detail
    # shot of each item (a group or an object) + a few dollhouse overviews. Unlike
    # the wide interior room_views, each tile is filled by its subject — the kind of
    # "detail-focused" reference collage the planner consumes. Cameras are framed
    # here (Python) from each item's world AABB; the renderer just places + shoots.
    # -----------------------------------------------------------------

    def _frame_box(self, C, S, room_center, lens, dir_override=None):
        """Camera (location, target) that frames a Blender-space box (center C, size S)
        from the room-interior side as a 3/4 view, pulled back to fit and raised a touch.

        Always a diagonal (never head-on to a wall): a head-on shot at a window-cut wall
        drops the subject into the void. We bias the inward direction with a lateral
        component so the camera comes in at ~30 degrees off-axis.
        """
        import math
        bx, by, bz = C
        sx, sy, sz = S
        W, D, H = 2 * room_center[0], -2 * room_center[1], 2 * room_center[2]
        if dir_override is not None:
            dx, dy = dir_override
        else:
            inx, iny = room_center[0] - bx, room_center[1] - by   # toward room interior
            if math.hypot(inx, iny) < 1e-3:                       # central item
                inx, iny = 0.4, -1.0
            ninx = math.hypot(inx, iny)
            inx, iny = inx / ninx, iny / ninx
            # rotate ~30 deg toward whichever side has more room, for a 3/4 angle
            side = 1.0 if (bx < room_center[0]) else -1.0
            latx, laty = -iny * side, inx * side                  # perpendicular
            dx, dy = inx + 0.6 * latx, iny + 0.6 * laty
        n = math.hypot(dx, dy) or 1.0
        ux, uy = dx / n, dy / n
        hfov = 2.0 * math.atan(18.0 / float(lens))                # 36 mm sensor
        extent = max(0.4, min(max(sx, sy, sz), 1.2 * max(W, D)))
        d = 1.3 * extent / (2.0 * math.tan(hfov / 2.0)) + 0.4 * max(sx, sy)
        cam = [bx + ux * d, by + uy * d, bz + 0.40 * extent]
        m = 0.2                                                   # stay inside the shell
        cam = [min(max(cam[0], m), W - m), min(max(cam[1], -D + m), -m), min(max(cam[2], m), H - m)]
        target = [bx, by, bz + 0.05 * sz]
        return [float(v) for v in cam], [float(v) for v in target]

    def _collection_specs(self, items, run_dir, overviews, lens):
        """Build the per-tile (label, render-spec) list: a framed detail shot per item,
        then `overviews` dollhouse corners. DSL (x,y,z) maps to Blender (x, -z, y)."""
        def _safe(s):
            return "".join(c if c.isalnum() else "_" for c in str(s))[:40]
        W = float(getattr(self, "WIDTH", 0) or 0)
        D = float(getattr(self, "DEPTH", 0) or 0)
        H = float(getattr(self, "HEIGHT", 3.0) or 3.0)
        if W <= 0 or D <= 0:                            # fall back to the room's own AABB
            amin, amax = self.get_aabb()
            W = W or float(amax[0] - amin[0])
            D = D or float(amax[2] - amin[2])
        room_center = (W / 2.0, -D / 2.0, H / 2.0)
        tiles = []
        for entry in items:
            label, item = entry[0], entry[1]
            dir_override = entry[2] if len(entry) > 2 else None
            amin, amax = item.get_aabb()                # DSL world AABB
            C = ((amin[0] + amax[0]) / 2.0, -(amin[2] + amax[2]) / 2.0, (amin[1] + amax[1]) / 2.0)
            S = (amax[0] - amin[0], amax[2] - amin[2], amax[1] - amin[1])
            cam, target = self._frame_box([float(v) for v in C], [float(v) for v in S],
                                          room_center, lens, dir_override)
            tiles.append({"label": label, "spec": {
                "out": os.path.join(run_dir, f"detail_{len(tiles)}_{_safe(label)}.png"),
                "cam": cam, "target": target, "lens": lens}})
        # dollhouse overviews from the top corners
        inset, eye, tgtz = 0.9, 0.92 * H, 0.35 * H
        cxb, cyb, hx, hy = W / 2.0, -D / 2.0, W / 2.0, D / 2.0
        corners = [(cxb - hx * inset, cyb - hy * inset), (cxb + hx * inset, cyb + hy * inset),
                   (cxb + hx * inset, cyb - hy * inset), (cxb - hx * inset, cyb + hy * inset)]
        for i in range(min(overviews, len(corners))):
            cx, cy = corners[i]
            tiles.append({"label": f"overview {i + 1}", "spec": {
                "out": os.path.join(run_dir, f"overview_{i}.png"),
                "cam": [cx, cy, eye], "target": [cxb, cyb, tgtz], "lens": 22.0}})
        try:                                            # diagnostics: dump the framing geometry
            import json
            with open(os.path.join(run_dir, "_specs.json"), "w") as f:
                json.dump({"room": {"W": W, "D": D, "H": H, "center": list(room_center)},
                           "tiles": tiles}, f, indent=1)
        except Exception:
            pass
        return tiles

    @staticmethod
    def _build_collage(labeled_paths, out_path, cols=4, cell=(460, 300), pad=8, label_h=26):
        """Montage (label, image_path) tiles into one 2xN editorial PNG (transparent
        renders composited over a warm neutral, captioned)."""
        from PIL import Image, ImageDraw, ImageFont
        tiles = [lp for lp in labeled_paths if lp[1] and os.path.exists(lp[1])]
        if not tiles:
            return out_path
        cols = min(cols, len(tiles))
        rows = (len(tiles) + cols - 1) // cols
        cw, ch = cell
        W = cols * cw + (cols + 1) * pad
        Ht = rows * (ch + label_h) + (rows + 1) * pad
        canvas = Image.new("RGB", (W, Ht), (242, 240, 236))
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        except Exception:
            font = ImageFont.load_default()
        for k, (label, p) in enumerate(tiles):
            r, c = divmod(k, cols)
            x = pad + c * (cw + pad)
            y = pad + r * (ch + label_h + pad)
            im = Image.open(p).convert("RGBA")
            im.thumbnail((cw, ch))
            canvas.paste(im, (x + (cw - im.width) // 2, y + (ch - im.height) // 2), im)
            draw.text((x + 4, y + ch + 5), str(label), fill=(60, 60, 60), font=font)
        canvas.save(out_path, quality=90)
        return out_path

    def render_collection(self, items, out=None, overviews=2,
                          resolution=(900, 600), samples=None, lens=38.0):
        """Render a planner-style COLLECTION collage of the built room.

        `items` is a list of ``(label, group_or_object[, (dx, dy)])`` — each gets a
        camera framed tightly on its world AABB (optionally biased toward a horizontal
        direction ``(dx, dy)`` in Blender XY); `overviews` dollhouse corner shots are
        appended. Everything is montaged into one 2xN PNG at `out`. Returns the path.
        Wrapped so a renderer hiccup never breaks scene assembly.
        """
        from IDSDL.renderer.renderer import SceneRenderer
        run_dir = self._run_dir("collection")
        out = out or os.path.join(run_dir, "collection.png")
        try:
            blend = self._build_blend()
            tiles = self._collection_specs(items, run_dir, overviews, lens)
            rx, ry = resolution
            SceneRenderer(resolution_x=rx, resolution_y=ry,
                          samples=samples if samples is not None else self.render_samples,
                          verbose=True).render_views(blend, [t["spec"] for t in tiles])
            self._build_collage([(t["label"], t["spec"]["out"]) for t in tiles], out)
            print(f"[RoomGroup] collection collage -> '{out}' ({len(tiles)} tiles)")
        except Exception as e:
            print(f"[RoomGroup] collection render skipped ({type(e).__name__}: {e})")
        return out

    def recenter(self):
        self.scene.bind(self)
        
from sceneprogllm import LLM
import ast
class AlphabetGenerator:
    def __init__(self):
        self.llm = LLM(
            system_desc=f"""
You are a large language model based assistant, expert at generating ASCII art representations for alphabets and numbers.
Return only python code in Markdown format, e.g.:
```python
....
```
"""
        )

    def sanitize(self, text):
        pos = []
        # Loop through each row of the ASCII representation
        for y, row in enumerate(text):
            # Loop through each character of the row
            for x, char in enumerate(row):
                # If the character is 'G', add the coordinates to the list
                if char == '*':
                    pos.append((x, y))
        
        return np.array(pos), len(text[0])+1
    
    def _sanitize_output(self, text: str):
        _, after = text.split("```python")
        code = after.split("```")[0].strip()
        start = code.find('[')
        if start == -1:
            return code
        depth = 0
        for i, ch in enumerate(code[start:], start=start):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    return code[start:i + 1]
        return code[start:]
    
    def run(self, query):
        prompt = """
User Input: Generate ASCII art for 'G'
Your Response: 
```python   [       "  ****  ",
                    " *      ",
                    "*       ",
                    "*   **  ",
                    "*     * ",
                    " *    * ",
                    "  ****  "
]```    
User Input: Generate ASCII art for 'S'
Your Response:
```python  [    " ****  ",
                "*      ",
                "*      ",
                " ****  ",
                "     * ",
                "     * ",
                " ****  "   
]```  
        """
        prompt += f"""
User Input: Generate ASCII art for '{query}'
Your Response:
"""
        response = self.llm(prompt)
        response = self._sanitize_output(response)
        response = ast.literal_eval(response)
        return self.sanitize(response)
    
class WordGenerator:
    def __init__(self):
        self.alpha_gen = AlphabetGenerator()
    
    def run(self, word):
        points = []
        cw=5
        for letter in word:
            pt,w = self.alpha_gen.run(letter)
            pt[:,0] += cw
            points.append(pt)
            cw += w
        return np.vstack(points)
    
class SentenceASCIIGenerator(SceneProgObject):
    def __init__(self, scene, name=None):
        super().__init__(scene, name=name)
        self.name = "SentenceASCIIGenerator"
        self.description = f"""
Places assets in an ASCII art representation of a sentence.
Inputs:
- obj: An object to place in the scene.
- sentence: The sentence to represent in ASCII art.
"""
        self.usage = f"""
with scene.SentenceASCIIGenerator() as ascii_gen:
    plant = scene.AddAsset("A large potted plant")
    ascii_gen.place(plant, sentence="World\tPeace\n2045")
"""
        self.word_gen = WordGenerator()
        

    def run(self, sentence):
        points = []
        ch=5
        for line in sentence.split('\n'):
            cw=0
            tmp=[]
            for word in line.split('\t'):
                pt = self.word_gen.run(word)
                h = np.max(pt[:,1])+1
                w = np.max(pt[:,0])+5
                pt[:,1] += ch
                pt[:,0] += cw
                tmp.append(pt)
                cw+=w
            tmp=np.vstack(tmp)
            points.append(tmp)
            ch += h
        return points
    
    @placemethod
    def place(self, obj, sentence):
        points = self.run(sentence)
        total_points = np.vstack(points).shape[0]
        objs = total_points*obj
        height = self.compute_obj_y(obj)
        count = 0
        for line in points:
            for pt in line:
                objs[count].set_location(pt[0], height, pt[1])
                self.add_child(objs[count])
                count += 1

        return points
    
    def compile(self):
        self.reset_compile_state()
        self.clear_constraints()
        for op in self.operations:
            op.execute()
        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report

class BasicRoomGroup(RoomGroup):
    def __init__(self, scene, WIDTH, DEPTH, HEIGHT, name=None):
        self.WIDTH = WIDTH
        self.DEPTH = DEPTH
        self.HEIGHT = HEIGHT
        super().__init__(scene, name=name)

    @placemethod
    def place(self, objs, positions, rotations):
        for obj, position, rotation in zip(objs, positions, rotations):
            obj.set_location(*position)
            obj.set_rotation(rotation)
            self.add_child(obj)

    def compile(self):
        self.reset_compile_state()
        self.clear_constraints()
        for op in self.operations:
            op.execute()

        self.OverlapConstraint()
        self.OutOfBoundsConstraint()
        self._run_constraint_hooks()
        self.grad_optimize()
        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report
        