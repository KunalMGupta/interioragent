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

    @placemethod
    def place_on_top(self, objs):
        front_dir, back_dir, left_dir, right_dir, center, width, height, depth = self.get_anchor_center_dirs()
        objs = self.to_list(objs)
        N = len(objs)

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
    def place_rug(self, desc, size):
        rug = self.scene.AddAsset(desc)
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
        delayed_names = {"place_on_top", "place_rug", "add_lighting"}

        # Execute all main operations first
        for op in self.operations:
            if op.name not in delayed_names:
                op.execute()

        self.compile_children()

        # Run optimization
        self.OverlapConstraint()
        self.ObjectProportionsConstraint()
        self.grad_optimize()

        # Execute delayed operations last
        op = self.get_operation("place_on_top")
        if op is not None:
            op.execute()

        op = self.get_operation("place_rug")
        if op is not None:
            op.execute()

        op = self.get_operation("add_lighting")
        if op is not None:
            op.execute()

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
    def __init__(self, scene, name=None, sparsity=0.0):
        super().__init__(scene, name=name)
        self.anchor_info = None
        self.sparsity = max(0.0, min(sparsity, 1.0))

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
            self.add_child(obj)

class GridGroup(SceneProgObject):
    def __init__(self, scene, name=None, sparsity=0.0, randomness=0.0):
        super().__init__(scene, name=name)
        self.sparsity = max(0.0, min(sparsity, 1.0))
        self.randomness = max(0.0, min(randomness, 1.0))

    def _place_row(self, objects=None, along='x', facing='z', x0=0, z0=0):
        objects = self.to_list([] if objects is None else objects)
        N = len(objects)
        if N == 0:
            return 0.0

        widths = np.array([obj.get_width() for obj in objects], dtype=np.float32)
        total_width = np.sum(widths)
        base_gap = self.sparsity * (total_width / N)

        rng = np.random.default_rng()
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

        rng = np.random.default_rng()
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
                x = dist * np.sin(np.radians(rot)) + (np.random.random() - 0.5) * self.randomness * self.sparsity * obj.get_width()
                y = self.compute_obj_y(obj)
                z = -dist * np.cos(np.radians(rot)) + (np.random.random() - 0.5) * self.randomness * self.sparsity * obj.get_depth()
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

    def __init__(self, scene, name=None, modulate_scale=1.0):
        super().__init__(scene, name=name)
        self.modulate_scale = modulate_scale
        self.wall_assets = {
            'back_wall': {'left': [], 'center': [], 'right': []},
            'left_wall': {'left': [], 'center': [], 'right': []},
            'right_wall': {'left': [], 'center': [], 'right': []},
            'front_wall': {'left': [], 'center': [], 'right': []},
        }

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
        self.WIDTH = np.sum(col_widths) * self.modulate_scale
        self.DEPTH = np.sum(row_depths) * self.modulate_scale
        self.HEIGHT = np.min((np.max([heights + 2.0, 3.0]), 3.0))

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

    @placemethod
    def place_on_center(self, obj, facing=None):
        obj.set_location(self.WIDTH / 2, self.compute_obj_y(obj), self.DEPTH / 2)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back(self, obj, facing=None):
        obj.set_location(self.WIDTH / 2, self.compute_obj_y(obj), self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front(self, obj, facing=None):
        obj.set_location(self.WIDTH / 2, self.compute_obj_y(obj), 3 * self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left(self, obj, facing=None):
        obj.set_location(self.WIDTH / 4, self.compute_obj_y(obj), self.DEPTH / 2)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right(self, obj, facing=None):
        obj.set_location(3 * self.WIDTH / 4, self.compute_obj_y(obj), self.DEPTH / 2)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_left(self, obj, facing=None):
        obj.set_location(self.WIDTH / 4, self.compute_obj_y(obj), self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_right(self, obj, facing=None):
        obj.set_location(3 * self.WIDTH / 4, self.compute_obj_y(obj), self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_left(self, obj, facing=None):
        obj.set_location(self.WIDTH / 4, self.compute_obj_y(obj), 3 * self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_right(self, obj, facing=None):
        obj.set_location(3 * self.WIDTH / 4, self.compute_obj_y(obj), 3 * self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_wall_left(self, obj, facing=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH / 4, self.compute_obj_y(obj), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_wall_center(self, obj, facing=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH / 2, self.compute_obj_y(obj), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_back_wall_right(self, obj, facing=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(3 * self.WIDTH / 4, self.compute_obj_y(obj), delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left_wall_right(self, obj, facing=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self.compute_obj_y(obj), self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left_wall_center(self, obj, facing=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self.compute_obj_y(obj), self.DEPTH / 2)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_left_wall_left(self, obj, facing=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(delta_w, self.compute_obj_y(obj), 3 * self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right_wall_left(self, obj, facing=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self.compute_obj_y(obj), self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right_wall_center(self, obj, facing=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self.compute_obj_y(obj), self.DEPTH / 2)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_right_wall_right(self, obj, facing=None):
        delta_w, _ = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH - delta_w, self.compute_obj_y(obj), 3 * self.DEPTH / 4)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_wall_left(self, obj, facing=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(3 * self.WIDTH / 4, self.compute_obj_y(obj), self.DEPTH - delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_wall_center(self, obj, facing=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH / 2, self.compute_obj_y(obj), self.DEPTH - delta_d)
        obj.set_rotation(self.facing_to_rotation(facing))
        self.add_child(obj)

    @placemethod
    def place_on_front_wall_right(self, obj, facing=None):
        _, delta_d = self.wall_deltas(obj, facing)
        obj.set_location(self.WIDTH / 4, self.compute_obj_y(obj), self.DEPTH - delta_d)
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

        self.compile_children()

        self.OverlapConstraint()
        self.OutOfBoundsConstraint()
        self.grad_optimize()

        for op in self.operations:
            if op.name in skip_for_now:
                op.execute()

        for asset in self.scene.ceiling_lights:
            x, _, z = asset.transform.decompose_matrix()[0]
            asset.set_location(x, self.HEIGHT - asset.get_height() / 2, z)

        self.scene.WIDTH = self.WIDTH
        self.scene.DEPTH = self.DEPTH
        self.scene.HEIGHT = self.HEIGHT

        self.RoomProportionsConstraint()
        self.WallOverlapConstraint()
        self.vlm_optimize()

        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report
    
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
        self.grad_optimize()
        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report
        