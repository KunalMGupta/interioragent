import numpy as np
import random
from sceneprogllm import LLM


class Raytracer2D:
    def __init__(self, group, objects=None):
        self.objects = objects if objects is not None else group.get_children()
        self.MAX = 1000.0

        self.has_walls = hasattr(group, "WIDTH") and hasattr(group, "DEPTH")
        self.WIDTH = float(group.WIDTH) if hasattr(group, "WIDTH") else self.MAX
        self.DEPTH = float(group.DEPTH) if hasattr(group, "DEPTH") else self.MAX

        self.aabb = {obj: self.enhance_aabb(obj.get_aabb()) for obj in self.objects}

    def enhance_aabb(self, aabb):
        margin = 0.05
        aabb = np.asarray(aabb, dtype=np.float32)
        return np.array(
            [
                [aabb[0][0] - margin, aabb[0][1] - margin, aabb[0][2] - margin],
                [aabb[1][0] + margin, aabb[1][1] + margin, aabb[1][2] + margin],
            ],
            dtype=np.float32,
        )

    def overlap(self, obj1, obj2):
        aabb1 = self.aabb[obj1]
        aabb2 = self.aabb[obj2]
        return self.aabb_overlap(aabb1, aabb2)

    def aabb_overlap(self, aabb1, aabb2):
        if (
            aabb1[1][0] <= aabb2[0][0] or aabb2[1][0] <= aabb1[0][0]
            or aabb1[1][1] <= aabb2[0][1] or aabb2[1][1] <= aabb1[0][1]
            or aabb1[1][2] <= aabb2[0][2] or aabb2[1][2] <= aabb1[0][2]
        ):
            return False, 0.0

        overlap_x = max(0.0, min(aabb1[1][0], aabb2[1][0]) - max(aabb1[0][0], aabb2[0][0]))
        overlap_y = max(0.0, min(aabb1[1][1], aabb2[1][1]) - max(aabb1[0][1], aabb2[0][1]))
        overlap_z = max(0.0, min(aabb1[1][2], aabb2[1][2]) - max(aabb1[0][2], aabb2[0][2]))
        overlap_volume = overlap_x * overlap_y * overlap_z

        vol1 = np.prod(aabb1[1] - aabb1[0])
        vol2 = np.prod(aabb2[1] - aabb2[0])

        avg_volume = (vol1 + vol2) / 2.0
        degree = overlap_volume / avg_volume if avg_volume > 0 else 0.0

        return True, float(degree)

    def dist_in_xpos(self, obj1, obj2):
        aabb1 = self.aabb[obj1]
        aabb2 = self.aabb[obj2]

        xmin1, ymin1, zmin1 = aabb1[0]
        xmax1, ymax1, zmax1 = aabb1[1]
        xmin2, ymin2, zmin2 = aabb2[0]
        xmax2, ymax2, zmax2 = aabb2[1]

        if self.has_walls:
            if xmax1 > self.WIDTH:
                return 0.0
            max_dist = self.WIDTH - xmax1
        else:
            max_dist = self.MAX

        overlap, degree = self.aabb_overlap(aabb1, aabb2)
        if overlap:
            v1 = obj1.get_location()
            v2 = obj2.get_location()
            rel = v2 - v1
            rel = rel / (np.linalg.norm(rel) + 1e-3)
            if rel[0] > 0:
                return 0.0
            return max_dist

        if zmin1 > zmax2 or zmin2 > zmax1:
            return max_dist

        if xmax1 > xmax2:
            return max_dist

        if xmin2 < xmax1:
            return 0.0

        return xmin2 - xmax1

    def dist_in_xneg(self, obj1, obj2):
        aabb1 = self.aabb[obj1]
        aabb2 = self.aabb[obj2]

        xmin1, ymin1, zmin1 = aabb1[0]
        xmax1, ymax1, zmax1 = aabb1[1]
        xmin2, ymin2, zmin2 = aabb2[0]
        xmax2, ymax2, zmax2 = aabb2[1]

        if self.has_walls:
            if xmin1 < 0:
                return 0.0
            max_dist = xmin1
        else:
            max_dist = self.MAX

        overlap, degree = self.aabb_overlap(aabb1, aabb2)
        if overlap:
            v1 = obj1.get_location()
            v2 = obj2.get_location()
            rel = v2 - v1
            rel = rel / (np.linalg.norm(rel) + 1e-3)
            if rel[0] < 0:
                return 0.0
            return max_dist

        if zmin1 > zmax2 or zmin2 > zmax1:
            return max_dist

        if xmin1 < xmin2:
            return max_dist

        if xmax2 > xmin1:
            return 0.0

        return xmin1 - xmax2

    def dist_in_zpos(self, obj1, obj2):
        aabb1 = self.aabb[obj1]
        aabb2 = self.aabb[obj2]

        xmin1, ymin1, zmin1 = aabb1[0]
        xmax1, ymax1, zmax1 = aabb1[1]
        xmin2, ymin2, zmin2 = aabb2[0]
        xmax2, ymax2, zmax2 = aabb2[1]

        if self.has_walls:
            if zmax1 > self.DEPTH:
                return 0.0
            max_dist = self.DEPTH - zmax1
        else:
            max_dist = self.MAX

        overlap, degree = self.aabb_overlap(aabb1, aabb2)
        if overlap:
            v1 = obj1.get_location()
            v2 = obj2.get_location()
            rel = v2 - v1
            rel = rel / (np.linalg.norm(rel) + 1e-3)
            if rel[2] > 0:
                return 0.0
            return max_dist

        if xmin1 > xmax2 or xmin2 > xmax1:
            return max_dist

        if zmax1 > zmax2:
            return max_dist

        if zmin2 < zmax1:
            return 0.0

        return zmin2 - zmax1

    def dist_in_zneg(self, obj1, obj2):
        aabb1 = self.aabb[obj1]
        aabb2 = self.aabb[obj2]

        xmin1, ymin1, zmin1 = aabb1[0]
        xmax1, ymax1, zmax1 = aabb1[1]
        xmin2, ymin2, zmin2 = aabb2[0]
        xmax2, ymax2, zmax2 = aabb2[1]

        if self.has_walls:
            if zmin1 < 0:
                return 0.0
            max_dist = zmin1
        else:
            max_dist = self.MAX

        overlap, degree = self.aabb_overlap(aabb1, aabb2)
        if overlap:
            v1 = obj1.get_location()
            v2 = obj2.get_location()
            rel = v2 - v1
            rel = rel / (np.linalg.norm(rel) + 1e-3)
            if rel[2] < 0:
                return 0.0
            return max_dist

        if xmin1 > xmax2 or xmin2 > xmax1:
            return max_dist

        if zmin1 < zmin2:
            return max_dist

        if zmax2 > zmin1:
            return 0.0

        return zmin1 - zmax2

    def compute_free_space(self, obj, dir):
        dist = self.MAX
        nearest_obj = None

        if dir not in ["x+", "x-", "z+", "z-"]:
            raise ValueError("Invalid direction. Use 'x+', 'x-', 'z+', or 'z-'.")

        if dir == "x+":
            for other in self.objects:
                if other is obj:
                    continue
                tmp = self.dist_in_xpos(obj, other)
                if tmp < dist:
                    dist = tmp
                    nearest_obj = other

        elif dir == "x-":
            for other in self.objects:
                if other is obj:
                    continue
                tmp = self.dist_in_xneg(obj, other)
                if tmp < dist:
                    dist = tmp
                    nearest_obj = other

        elif dir == "z+":
            for other in self.objects:
                if other is obj:
                    continue
                tmp = self.dist_in_zpos(obj, other)
                if tmp < dist:
                    dist = tmp
                    nearest_obj = other

        elif dir == "z-":
            for other in self.objects:
                if other is obj:
                    continue
                tmp = self.dist_in_zneg(obj, other)
                if tmp < dist:
                    dist = tmp
                    nearest_obj = other

        return dist, nearest_obj

    def compute_free_space_all(self, obj):
        return {
            "dx+": self.compute_free_space(obj, "x+")[0],
            "dx-": self.compute_free_space(obj, "x-")[0],
            "dz+": self.compute_free_space(obj, "z+")[0],
            "dz-": self.compute_free_space(obj, "z-")[0],
        }


class ConstraintBase:
    def __init__(self, group):
        self.group = group
        self.group.constraints.append(self)
        if self.type == "GRADIENT":
            if self not in self.group.grad_constraints:
                self.group.grad_constraints.append(self)
        elif self.type == "VLM":
            if self not in self.group.vlm_constraints:
                self.group.vlm_constraints.append(self)
        else:
            raise ValueError("Constraint type must be 'GRADIENT' or 'VLM'")

    def is_aligned_zpos(self, obj):
        rotation = float(obj.get_rotation())
        return np.abs(rotation) % 180 < 45

    def is_aligned_xpos(self, obj):
        rotation = float(obj.get_rotation())
        return np.abs(rotation - 90) % 180 < 45

    def is_aligned_zneg(self, obj):
        rotation = float(obj.get_rotation())
        return np.abs(rotation - 180) % 180 < 45

    def is_aligned_xneg(self, obj):
        rotation = float(obj.get_rotation())
        return np.abs(rotation - 270) % 180 < 45
    

class OverlapConstraint(ConstraintBase):
    def __init__(self, group):
        self.name = "OverlapConstraint"
        self.type = "GRADIENT"
        self.weight = 1.0
        super().__init__(group)

    def compute_gradients(self):
        objects = self.group.children
        raytracer = Raytracer2D(self.group, objects=objects)

        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                obj1 = objects[i]
                obj2 = objects[j]

                if getattr(obj1, "ignore_overlap", False) or getattr(obj2, "ignore_overlap", False):
                    continue

                status, degree = raytracer.overlap(obj1, obj2)
                if status:
                    v1 = obj1.get_location()
                    v2 = obj2.get_location()

                    grad1 = (v1 - v2) * degree
                    grad2 = (v2 - v1) * degree

                    obj1.grad += grad1 * self.weight
                    obj2.grad += grad2 * self.weight


class ClearanceConstraint(ConstraintBase):
    def __init__(self, group, obj, distance=0.5, dir="front", omit_objs=None):
        self.name = "ClearanceConstraint"
        self.type = "GRADIENT"
        self.weight = 1.0

        self.obj = obj
        self.distance = float(distance)
        self.omit_objs = [] if omit_objs is None else omit_objs

        assert dir in ["front", "sides", "all"], "Type must be 'front', 'sides', or 'all'"
        self.dir = dir

        super().__init__(group)

    def compute_gradients(self):
        raytracer = Raytracer2D(self.group)

        if self.dir == "front" or self.dir == "all":
            if self.is_aligned_zpos(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "z+")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([0, 0, -delta / 2], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([0, 0, delta / 2], dtype=np.float32) * self.weight

            elif self.is_aligned_zneg(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "z-")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([0, 0, delta / 2], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([0, 0, -delta / 2], dtype=np.float32) * self.weight

            elif self.is_aligned_xpos(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "x+")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([-delta / 2, 0, 0], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([delta / 2, 0, 0], dtype=np.float32) * self.weight

            elif self.is_aligned_xneg(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "x-")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([delta / 2, 0, 0], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([-delta / 2, 0, 0], dtype=np.float32) * self.weight

        if self.dir == "sides" or self.dir == "all":
            if self.is_aligned_zpos(self.obj) or self.is_aligned_zneg(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "x+")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([-delta / 2, 0, 0], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([delta / 2, 0, 0], dtype=np.float32) * self.weight

                dist, nearest_obj = raytracer.compute_free_space(self.obj, "x-")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([delta / 2, 0, 0], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([-delta / 2, 0, 0], dtype=np.float32) * self.weight

            elif self.is_aligned_xpos(self.obj) or self.is_aligned_xneg(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "z+")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([0, 0, -delta / 2], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([0, 0, delta / 2], dtype=np.float32) * self.weight

                dist, nearest_obj = raytracer.compute_free_space(self.obj, "z-")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([0, 0, delta / 2], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([0, 0, -delta / 2], dtype=np.float32) * self.weight

        if self.dir == "all":
            if self.is_aligned_zpos(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "z-")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([0, 0, delta / 2], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([0, 0, -delta / 2], dtype=np.float32) * self.weight

            elif self.is_aligned_zneg(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "z+")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([0, 0, -delta / 2], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([0, 0, delta / 2], dtype=np.float32) * self.weight

            elif self.is_aligned_xpos(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "x-")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([delta / 2, 0, 0], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([-delta / 2, 0, 0], dtype=np.float32) * self.weight

            elif self.is_aligned_xneg(self.obj):
                dist, nearest_obj = raytracer.compute_free_space(self.obj, "x+")
                if dist < self.distance and nearest_obj is not None:
                    delta = self.distance - dist
                    self.obj.grad += np.array([-delta / 2, 0, 0], dtype=np.float32) * self.weight
                    nearest_obj.grad += np.array([delta / 2, 0, 0], dtype=np.float32) * self.weight
                    
class AccessConstraint(ConstraintBase):
    def __init__(self, group, obj, target, min_dist=0.1, max_dist=0.15, dir="front"):
        self.name = "AccessConstraint"
        self.type = "GRADIENT"
        self.weight = 1.0

        self.obj = obj
        self.other = target
        self.min_dist = float(min_dist)
        self.max_dist = float(max_dist)

        assert dir in ["front", "sides"], "Type must be 'front' or 'sides'"
        self.dir = dir

        super().__init__(group)

    def compute_gradients(self):
        raytracer = Raytracer2D(self.group)

        x1min, _, z1min = raytracer.aabb[self.obj][0]
        x1max, _, z1max = raytracer.aabb[self.obj][1]
        x2min, _, z2min = raytracer.aabb[self.other][0]
        x2max, _, z2max = raytracer.aabb[self.other][1]

        if self.dir == "sides":
            if self.is_aligned_zpos(self.obj) or self.is_aligned_zneg(self.obj):
                if z1min < z2min and z1max > z2max:
                    if x1max <= x2min:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = x2min - x1max
                        if dist < self.min_dist:
                            delta = self.min_dist - dist
                            self.obj.grad -= rel * delta * self.weight
                            self.other.grad += rel * delta * self.weight
                        elif dist > self.max_dist:
                            delta = dist - self.max_dist
                            self.obj.grad += rel * delta * self.weight
                            self.other.grad -= rel * delta * self.weight

                    elif x1min >= x2max:
                        rel = np.array([-1, 0, 0], dtype=np.float32)
                        dist = x1min - x2max
                        if dist < self.min_dist:
                            delta = self.min_dist - dist
                            self.obj.grad -= rel * delta * self.weight
                            self.other.grad += rel * delta * self.weight
                        elif dist > self.max_dist:
                            delta = dist - self.max_dist
                            self.obj.grad += rel * delta * self.weight
                            self.other.grad -= rel * delta * self.weight

                if x1max < x2min or x1min > x2max:
                    if z1min >= z2min:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = (z1max + z1min) / 2 - z2max
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif z1max < z2max:
                        rel = np.array([0, 0, -1], dtype=np.float32)
                        dist = z2min - (z1max + z1min) / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                elif x2max > x1min or x2min < x1max:
                    if (x1max + x1min) / 2 <= (x2max + x2min) / 2:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = (x1max - x1min) / 2 + (x2max - x2min) / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif (x1max + x1min) / 2 > (x2max + x2min) / 2:
                        rel = np.array([-1, 0, 0], dtype=np.float32)
                        dist = (x1max - x1min) / 2 + (x2max - x2min) / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

            elif self.is_aligned_xpos(self.obj) or self.is_aligned_xneg(self.obj):
                if x1min < x2min and x1max > x2max:
                    if z1max <= z2min:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = z2min - z1max
                        if dist < self.min_dist:
                            delta = self.min_dist - dist
                            self.obj.grad -= rel * delta * self.weight
                            self.other.grad += rel * delta * self.weight
                        elif dist > self.max_dist:
                            delta = dist - self.max_dist
                            self.obj.grad += rel * delta * self.weight
                            self.other.grad -= rel * delta * self.weight

                    elif z1min >= z2max:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = z1min - z2max
                        if dist < self.min_dist:
                            delta = self.min_dist - dist
                            self.other.grad += rel * delta * self.weight
                            self.obj.grad -= rel * delta * self.weight
                        elif dist > self.max_dist:
                            delta = dist - self.max_dist
                            self.other.grad -= rel * delta * self.weight
                            self.obj.grad += rel * delta * self.weight

                if z1max < z2min or z1min > z2max:
                    if x1min >= x2min:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = (x1max + x1min) / 2 - x2max
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif x1max < x2max:
                        rel = np.array([-1, 0, 0], dtype=np.float32)
                        dist = x2min - (x1max + x1min) / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                elif z2max > z1min or z2min < z1max:
                    if (z1max + z1min) / 2 <= (z2max + z2min) / 2:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = (z1max - z1min) / 2 + (z2max - z2min) / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif (z1max + z1min) / 2 > (z2max + z2min) / 2:
                        rel = np.array([0, 0, -1], dtype=np.float32)
                        dist = (z1max - z1min) / 2 + (z2max - z2min) / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

        elif self.dir == "front":
            if self.is_aligned_zpos(self.obj):
                if z2min <= z1max:
                    if (x2min + x2max) / 2 < (x1min + x1max) / 2 and x2max > x1min:
                        rel = np.array([-1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight

                    elif (x2min + x2max) / 2 > (x1min + x1max) / 2 and x2min < x1max:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight

                    else:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight

                else:
                    if x1min >= (x2max + x2min) / 2:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif x1max <= (x2min + x2max) / 2:
                        rel = np.array([-1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    else:
                        dist = z2min - z1max
                        if dist < self.min_dist:
                            rel = np.array([0, 0, 1], dtype=np.float32)
                            delta = self.min_dist - dist
                            self.other.grad += rel * delta * self.weight
                            self.obj.grad -= rel * delta * self.weight
                        elif dist > self.max_dist:
                            rel = np.array([0, 0, 1], dtype=np.float32)
                            delta = dist - self.max_dist
                            self.other.grad -= rel * delta * self.weight
                            self.obj.grad += rel * delta * self.weight

            elif self.is_aligned_xpos(self.obj):
                if x2min <= x1max:
                    if (z2min + z2max) / 2 < (z1min + z1max) / 2 and z2max > z1min:
                        rel = np.array([0, 0, -1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight

                    elif (z2min + z2max) / 2 > (z1min + z1max) / 2 and z2min < z1max:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight

                    else:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight

                else:
                    if z1min >= (z2max + z2min) / 2:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif z1max <= (z2min + z2max) / 2:
                        rel = np.array([0, 0, -1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    else:
                        dist = x2min - x1max
                        if dist < self.min_dist:
                            rel = np.array([1, 0, 0], dtype=np.float32)
                            delta = self.min_dist - dist
                            self.other.grad += rel * delta * self.weight
                            self.obj.grad -= rel * delta * self.weight
                        elif dist > self.max_dist:
                            rel = np.array([1, 0, 0], dtype=np.float32)
                            delta = dist - self.max_dist
                            self.other.grad -= rel * delta * self.weight
                            self.obj.grad += rel * delta * self.weight

            elif self.is_aligned_zneg(self.obj):
                if z1min >= z2max:
                    if (x2min + x2max) / 2 < (x1min + x1max) / 2 and x2min > x1max:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight

                    elif (x2min + x2max) / 2 > (x1min + x1max) / 2 and x2max < x1min:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad -= rel * dist * self.weight

                    else:
                        rel = np.array([0, 0, -1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight

                else:
                    if x1min >= (x2max + x2min) / 2:
                        rel = np.array([1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif x1max <= (x2min + x2max) / 2:
                        rel = np.array([-1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    else:
                        dist = z1min - z2max
                        if dist < self.min_dist:
                            rel = np.array([0, 0, -1], dtype=np.float32)
                            delta = self.min_dist - dist
                            self.other.grad += rel * delta * self.weight
                            self.obj.grad -= rel * delta * self.weight
                        elif dist > self.max_dist:
                            rel = np.array([0, 0, -1], dtype=np.float32)
                            delta = dist - self.max_dist
                            self.other.grad -= rel * delta * self.weight
                            self.obj.grad += rel * delta * self.weight

            elif self.is_aligned_xneg(self.obj):
                if x2max >= x1min:
                    if (z2min + z2max) / 2 < (z1min + z1max) / 2 and z2max > z1min:
                        rel = np.array([0, 0, -1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight

                    elif (z2min + z2max) / 2 > (z1min + z1max) / 2 and z2min < z1max:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight

                    else:
                        rel = np.array([-1, 0, 0], dtype=np.float32)
                        dist = self.obj.get_width() / 2 + self.other.get_width() / 2
                        self.other.grad += rel * dist * self.weight

                else:
                    if z1min >= (z2max + z2min) / 2:
                        rel = np.array([0, 0, 1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    elif z1max <= (z2min + z2max) / 2:
                        rel = np.array([0, 0, -1], dtype=np.float32)
                        dist = self.obj.get_depth() / 2 + self.other.get_depth() / 2
                        self.other.grad += rel * dist * self.weight
                        self.obj.grad -= rel * dist * self.weight

                    else:
                        dist = x1min - x2max
                        if dist < self.min_dist:
                            rel = np.array([-1, 0, 0], dtype=np.float32)
                            delta = self.min_dist - dist
                            self.other.grad += rel * delta * self.weight
                            self.obj.grad -= rel * delta * self.weight
                        elif dist > self.max_dist:
                            rel = np.array([-1, 0, 0], dtype=np.float32)
                            delta = dist - self.max_dist
                            self.other.grad -= rel * delta * self.weight
                            self.obj.grad += rel * delta * self.weight


class OutOfBoundsConstraint(ConstraintBase):
    def __init__(self, group):
        self.name = "OutOfBoundsConstraint"
        self.type = "GRADIENT"
        self.weight = 1.0

        assert hasattr(group, "WIDTH") and hasattr(group, "DEPTH"), (
            "Group must have WIDTH and DEPTH attributes"
        )

        self.WIDTH = float(group.WIDTH)
        self.DEPTH = float(group.DEPTH)

        super().__init__(group)

    def compute_gradients(self):
        buffer = 0.1
        margin = 0.05
        # Iterate over direct children so gradients land on the objects GradSolver moves.
        # For hierarchical scenes the direct children are frozen sub-groups whose AABB
        # already spans all their leaf descendants.
        objects = self.group.children

        for obj in objects:
            if getattr(obj, "ignore_overlap", False):
                continue

            raw_aabb = obj.get_aabb()
            xmin = raw_aabb[0, 0] - margin
            zmin = raw_aabb[0, 2] - margin
            xmax = raw_aabb[1, 0] + margin
            zmax = raw_aabb[1, 2] + margin

            if xmin < 0:
                dist = -xmin + buffer
                obj.grad += np.array([dist, 0, 0], dtype=np.float32) * self.weight
            elif xmax > self.WIDTH:
                dist = xmax - self.WIDTH + buffer
                obj.grad += np.array([-dist, 0, 0], dtype=np.float32) * self.weight

            if zmin < 0:
                dist = -zmin + buffer
                obj.grad += np.array([0, 0, dist], dtype=np.float32) * self.weight
            elif zmax > self.DEPTH:
                dist = zmax - self.DEPTH + buffer
                obj.grad += np.array([0, 0, -dist], dtype=np.float32) * self.weight

class VisibilityConstraint(ConstraintBase):
    def __init__(self, group, source, target):
        self.name = "VisibilityConstraint"
        self.type = "GRADIENT"
        self.weight = 1.0
        self.source = source
        self.target = target

        super().__init__(group)

    def is_point_in_trapezoid(self, point, trapezoid):
        def is_left(p0, p1, p2):
            return (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1]) > 0

        for i in range(4):
            a = trapezoid[i]
            b = trapezoid[(i + 1) % 4]
            if not is_left(a, b, point):
                return False
        return True

    def build_trapezoid(self, source, target):
        aabb1 = source.get_aabb()
        aabb2 = target.get_aabb()

        x1min, _, z1min = aabb1[0]
        x1max, _, z1max = aabb1[1]
        x2min, _, z2min = aabb2[0]
        x2max, _, z2max = aabb2[1]

        v1 = source.get_location()
        v2 = target.get_location()

        rel = v2 - v1
        rel = rel / (np.linalg.norm(rel) + 1e-3)
        rel = rel[[0, 2]]

        if rel @ np.array([0, 1], dtype=np.float32) > 0.9:
            trapezoid = np.array(
                [
                    [x1min, z1max],
                    [x1max, z1max],
                    [x2max, z2min],
                    [x2min, z2min],
                ],
                dtype=np.float32,
            )

        elif rel @ np.array([1, 0], dtype=np.float32) > 0.9:
            trapezoid = np.array(
                [
                    [x1max, z1min],
                    [x2min, z2min],
                    [x2min, z2max],
                    [x1max, z1max],
                ],
                dtype=np.float32,
            )

        elif rel @ np.array([0, -1], dtype=np.float32) > 0.9:
            trapezoid = np.array(
                [
                    [x1min, z1min],
                    [x2min, z2max],
                    [x2max, z2max],
                    [x1max, z1min],
                ],
                dtype=np.float32,
            )

        elif rel @ np.array([-1, 0], dtype=np.float32) > 0.9:
            trapezoid = np.array(
                [
                    [x1min, z1min],
                    [x1min, z1max],
                    [x2max, z2max],
                    [x2max, z2min],
                ],
                dtype=np.float32,
            )

        else:
            raise ValueError("Invalid direction for trapezoid construction")

        return trapezoid

    def is_obj_in_trapezoid(self, obj_aabb, trapezoid):
        pts = np.array(
            [
                [obj_aabb[0, 0], obj_aabb[0, 2]],
                [obj_aabb[1, 0], obj_aabb[0, 2]],
                [obj_aabb[1, 0], obj_aabb[1, 2]],
                [obj_aabb[0, 0], obj_aabb[1, 2]],
            ],
            dtype=np.float32,
        )
        for loc in pts:
            if self.is_point_in_trapezoid(loc, trapezoid):
                return True
        return False

    def projection_vector(self, v1, v2, v3):
        v1 = v1[[0, 2]]
        v2 = v2[[0, 2]]
        v3 = v3[[0, 2]]

        d = v2 - v1
        a = v3 - v1
        d_norm_sq = np.dot(d, d)

        if d_norm_sq < 1e-8:
            raise ValueError("v1 and v2 cannot be the same point")

        proj_scalar = np.dot(a, d) / d_norm_sq
        v_proj = v1 + proj_scalar * d
        vt = v3 - v_proj
        return vt

    def compute_gradients(self):
        raytracer = Raytracer2D(self.group)
        trapezoid = self.build_trapezoid(self.source, self.target)

        v1 = self.source.get_location()
        v2 = self.target.get_location()

        for obj in self.group.get_children():
            if obj is self.source or obj is self.target:
                continue

            if getattr(obj, "ignore_overlap", False):
                continue

            aabb = raytracer.aabb[obj]
            if self.is_obj_in_trapezoid(aabb, trapezoid):
                v3 = obj.get_location()
                vt = self.projection_vector(v1, v2, v3)
                vt = np.array([vt[0], 0, vt[1]], dtype=np.float32)

                norm_vt = np.linalg.norm(vt)
                mag = 10.0 / (norm_vt if norm_vt > 1e-3 else 1.0)

                if norm_vt < 1e-3:
                    rel = (v2 - v1) / (np.linalg.norm(v2 - v1) + 1e-3)
                    if rel @ np.array([0, 0, 1], dtype=np.float32) > 0.9 or rel @ np.array([0, 0, -1], dtype=np.float32) > 0.9:
                        vt = random.choice(
                            [
                                np.array([1, 0, 0], dtype=np.float32),
                                np.array([-1, 0, 0], dtype=np.float32),
                            ]
                        )
                    else:
                        vt = random.choice(
                            [
                                np.array([0, 0, 1], dtype=np.float32),
                                np.array([0, 0, -1], dtype=np.float32),
                            ]
                        )

                obj.grad += mag * vt * self.weight
            
class ObjectProportionsConstraint(ConstraintBase):
    def __init__(self, group):
        self.name = "ObjectProportionsConstraint"
        self.type = "VLM"

        self.VLM = LLM(
            system_desc="""
You are given an image which shows front, right, back, left renders of a scene which consists of several objects.
You are required to reason about the relative proportions of the objects in the scene and ensure that they make sense in context.

If an object is clearly too large or too small, respond with rescale instructions like:
- rescale coffee table by 0.5
- rescale sofa by 0.8

The rescale factor should be a float between 0.1 and 0.9.
If no rescaling is needed, respond with:
no rescale

Do not output anything except rescale instructions or 'no rescale'.
""",
        )

        super().__init__(group)

    def compute_gradients(self):
        render = self.group.render()
        descriptions = self.group.get_descriptions()

        if isinstance(descriptions, str):
            object_desc = descriptions
        else:
            object_desc = ",".join(descriptions)

        prompt = f"""
The scene has the following objects: {object_desc}
Now reason about the relative proportions of the objects in the scene and determine whether any of them should be rescaled.
"""

        response = self.VLM(prompt, image_paths=[render])
        return response
    
    
class RoomProportionsConstraint(ConstraintBase):
    def __init__(self, group):
        self.name = "RoomProportionsConstraint"
        self.type = "VLM"

        self.VLM = LLM(
            system_desc="""
You are given an image which shows front, right, back, left renders of a scene which consists of several objects.
You are required to reason about the relative proportion (size) of the room in the scene and ensure that it makes sense in context.

The room should not feel too spacious or too cramped.
You should respond with a rescale instruction so the room feels more appropriate.

The rescale factor should be a float between 0.5 and 2.0.

Also consider the occupancy ratio of the room.
An occupancy ratio around 0.4 is usually appropriate.
If the occupancy ratio is too low, the room may need to be smaller.
If the occupancy ratio is too high, the room may need to be larger.

Example:
- rescale room by 0.8

If no change is needed, respond with:
no rescale

Do not output anything except a room rescale instruction or 'no rescale'.
""",
        )

        super().__init__(group)

    def compute_gradients(self):
        render = self.group.render()
        occupancy_ratio = self.group.compute_occupancy_ratio()
        descriptions = self.group.get_descriptions()

        if isinstance(descriptions, str):
            object_desc = descriptions
        else:
            object_desc = ",".join(descriptions)

        prompt = f"""
The scene has the following objects: {object_desc}
The occupancy ratio of the room is {occupancy_ratio:.2f}.
Now reason about whether the room should be rescaled.
"""

        response = self.VLM(prompt, image_paths=[render])
        return response
         
class WallOverlapConstraint(ConstraintBase):
    def __init__(self, group):
        self.name = "WallOverlapConstraint"
        self.type = "VLM"
        super().__init__(group)

    def _describe_obj(self, obj):
        if getattr(obj, "description", None) is not None:
            return obj.description
        return getattr(obj, "name", obj.__class__.__name__)

    def _describe_bucket(self, wall_name, bucket_name):
        objs = self.group.wall_assets[wall_name][bucket_name]
        if len(objs) == 0:
            return "empty"
        return ", ".join(self._describe_obj(obj) for obj in objs)

    def check_overlap_wall(self):
        feedback = []
        status = False

        for wall_name in ["back_wall", "front_wall", "left_wall", "right_wall"]:
            for slot_name in ["left", "center", "right"]:
                objs = self.group.wall_assets[wall_name][slot_name]

                if len(objs) > 1:
                    status = True
                    obj_descs = ", ".join(f"'{self._describe_obj(obj)}'" for obj in objs)
                    feedback.append(
                        f"{wall_name} slot '{slot_name}' has multiple occupants: {obj_descs}."
                    )

        return "\n".join(feedback), status

    def compute_gradients(self):
        feedback, status = self.check_overlap_wall()
        if not status:
            return "no wall overlap"

        current_placement = f"""
back_wall: left -> {self._describe_bucket('back_wall', 'left')}
back_wall: center -> {self._describe_bucket('back_wall', 'center')}
back_wall: right -> {self._describe_bucket('back_wall', 'right')}
front_wall: left -> {self._describe_bucket('front_wall', 'left')}
front_wall: center -> {self._describe_bucket('front_wall', 'center')}
front_wall: right -> {self._describe_bucket('front_wall', 'right')}
left_wall: left -> {self._describe_bucket('left_wall', 'left')}
left_wall: center -> {self._describe_bucket('left_wall', 'center')}
left_wall: right -> {self._describe_bucket('left_wall', 'right')}
right_wall: left -> {self._describe_bucket('right_wall', 'left')}
right_wall: center -> {self._describe_bucket('right_wall', 'center')}
right_wall: right -> {self._describe_bucket('right_wall', 'right')}
"""

        return f"""
There are overlaps found on wall placements:
{feedback}

Current wall placements are:
{current_placement}

Consider moving overlapping assets to different wall positions to resolve these overlaps.
"""
    

CONSTRAINTS = [
    OverlapConstraint,
    ClearanceConstraint,
    AccessConstraint,
    OutOfBoundsConstraint,
    VisibilityConstraint,
    ObjectProportionsConstraint,
    RoomProportionsConstraint,
    # RenderingConstraint,
    WallOverlapConstraint,
]


class VLMSolver:
    def __init__(self, group):
        self.group = group
        self.objects = group.children
        self.constraints = group.vlm_constraints
        self.scene = group.scene

    def __call__(self):
        if self.scene is None:
            return ""

        if not hasattr(self.scene, "vlm_feedback") or self.scene.vlm_feedback is None:
            self.scene.vlm_feedback = ""

        outputs = []
        for constraint in self.constraints:
            response = constraint.compute_gradients()
            if response is None:
                continue

            response = str(response).strip()
            if response:
                outputs.append(response)

        if outputs:
            if self.scene.vlm_feedback:
                self.scene.vlm_feedback += "\n"
            self.scene.vlm_feedback += "\n".join(outputs)

        return self.scene.vlm_feedback


class GradSolver:
    def __init__(self, group, lr=0.3, num_steps=100, num_actions=2):
        self.group = group
        self.objects = group.children
        self.lr = float(lr)
        self.num_steps = int(num_steps)
        self.num_actions = int(num_actions)

    def init_gradients(self):
        for obj in self.objects:
            obj.grad = np.zeros(3, dtype=np.float32)

    def compute_gradients(self):
        for constraint in self.group.grad_constraints:
            constraint.compute_gradients()

        if len(self.objects) == 0:
            return 0.0

        avg_grad_norm = 0.0
        for obj in self.objects:
            norm = np.linalg.norm(obj.grad)
            if norm < 1e-3:
                obj.grad = np.zeros(3, dtype=np.float32)
                norm = 0.0
            avg_grad_norm += norm

        avg_grad_norm /= len(self.objects)
        return float(avg_grad_norm)

    def free_space_affinity(self, space):
        return 1.0 - np.exp(-2.0 * max(space, 0.0))

    def sample_k_indices_from_pdf(self, pdf, k=2):
        flat_pdf = pdf.ravel().astype(np.float64)
        total = flat_pdf.sum()

        if total <= 0 or not np.isfinite(total):
            flat_pdf = np.ones_like(flat_pdf, dtype=np.float64)
            total = flat_pdf.sum()

        flat_pdf /= total
        k = min(k, len(flat_pdf))

        try:
            flat_indices = np.random.choice(len(flat_pdf), size=k, replace=False, p=flat_pdf)
        except ValueError:
            flat_indices = np.random.choice(len(flat_pdf), size=k, replace=True, p=flat_pdf)

        n_cols = pdf.shape[1]
        indices = [(idx // n_cols, idx % n_cols) for idx in flat_indices]
        return indices

    def tidy_array(self, arr):
        arr = np.asarray(arr)
        arr = (100 * arr).astype(np.int32)
        arr = arr / 100.0
        return arr

    def compute_action(self):
        if len(self.objects) == 0:
            empty = np.zeros((0, 4), dtype=np.float32)
            return [], empty, empty

        raytracer = Raytracer2D(self.group, objects=self.objects)

        def safe_area(obj):
            return max(float(obj.get_area()), 1e-6)

        def do_for(obj):
            distances = raytracer.compute_free_space_all(obj)
            dxpos = self.free_space_affinity(distances["dx+"])
            dxneg = self.free_space_affinity(distances["dx-"])
            dzpos = self.free_space_affinity(distances["dz+"])
            dzneg = self.free_space_affinity(distances["dz-"])

            area = safe_area(obj)

            xpos = max(float(obj.grad.dot(np.array([1, 0, 0], dtype=np.float32))), 0.01) * dxpos / area
            zpos = max(float(obj.grad.dot(np.array([0, 0, 1], dtype=np.float32))), 0.01) * dzpos / area
            xneg = max(float(obj.grad.dot(np.array([-1, 0, 0], dtype=np.float32))), 0.01) * dxneg / area
            zneg = max(float(obj.grad.dot(np.array([0, 0, -1], dtype=np.float32))), 0.01) * dzneg / area

            return xpos, zpos, xneg, zneg, dxpos, dzpos, dxneg, dzneg

        actions = []
        dists = []

        for obj in self.objects:
            xpos, zpos, xneg, zneg, dxpos, dzpos, dxneg, dzneg = do_for(obj)
            actions.append(np.array([xpos, zpos, xneg, zneg], dtype=np.float32).reshape(1, 4))
            dists.append(np.array([dxpos, dzpos, dxneg, dzneg], dtype=np.float32).reshape(1, 4))

        actions = np.concatenate(actions, axis=0)
        dists = np.concatenate(dists, axis=0)

        actions = actions ** 3
        action_sum = np.sum(actions)

        if action_sum <= 0 or not np.isfinite(action_sum):
            actions = np.ones_like(actions, dtype=np.float32) / actions.size
        else:
            actions = actions / action_sum

        indices = self.sample_k_indices_from_pdf(actions, k=self.num_actions)

        objects = []
        for row, col in indices:
            obj = self.objects[row]

            if col == 0:
                action = np.abs(obj.grad[0]) * np.array([1, 0, 0], dtype=np.float32)
            elif col == 1:
                action = np.abs(obj.grad[2]) * np.array([0, 0, 1], dtype=np.float32)
            elif col == 2:
                action = np.abs(obj.grad[0]) * np.array([-1, 0, 0], dtype=np.float32)
            elif col == 3:
                action = np.abs(obj.grad[2]) * np.array([0, 0, -1], dtype=np.float32)
            else:
                continue

            objects.append((obj, action))

        return objects, actions, dists

    def _snap_overlaps(self):
        """Deterministic pass: push any still-overlapping pair apart by their penetration depth."""
        objs = self.objects
        for _ in range(20):
            any_overlap = False
            for i in range(len(objs)):
                for j in range(i + 1, len(objs)):
                    o1, o2 = objs[i], objs[j]
                    if getattr(o1, "ignore_overlap", False) or getattr(o2, "ignore_overlap", False):
                        continue
                    a1, a2 = o1.get_aabb(), o2.get_aabb()
                    ox = min(a1[1, 0], a2[1, 0]) - max(a1[0, 0], a2[0, 0])
                    oz = min(a1[1, 2], a2[1, 2]) - max(a1[0, 2], a2[0, 2])
                    if ox <= 0 or oz <= 0:
                        continue
                    any_overlap = True
                    if ox <= oz:
                        d = ox / 2 + 1e-3
                        sign = 1.0 if o1.get_location()[0] < o2.get_location()[0] else -1.0
                        o1.translate(-sign * d, 0, 0)
                        o2.translate(sign * d, 0, 0)
                    else:
                        d = oz / 2 + 1e-3
                        sign = 1.0 if o1.get_location()[2] < o2.get_location()[2] else -1.0
                        o1.translate(0, 0, -sign * d)
                        o2.translate(0, 0, sign * d)
            if not any_overlap:
                break

    def _clamp_to_bounds(self):
        """Hard-clamp any objects still outside room boundaries after gradient optimization.

        GradSolver can get stuck when free_space_affinity returns 0 for a packed object
        that is simultaneously OOB — the gradient exists but the action weight is zero.
        This pass guarantees correctness regardless of solver convergence.
        """
        if not hasattr(self.group, "WIDTH") or not hasattr(self.group, "DEPTH"):
            return

        WIDTH = float(self.group.WIDTH)
        DEPTH = float(self.group.DEPTH)

        for obj in self.objects:
            if getattr(obj, "ignore_overlap", False):
                continue

            aabb = obj.get_aabb()
            xmin, zmin = float(aabb[0, 0]), float(aabb[0, 2])
            xmax, zmax = float(aabb[1, 0]), float(aabb[1, 2])

            dx = 0.0
            if xmin < 0:
                dx = -xmin
            elif xmax > WIDTH:
                dx = WIDTH - xmax

            dz = 0.0
            if zmin < 0:
                dz = -zmin
            elif zmax > DEPTH:
                dz = DEPTH - zmax

            if abs(dx) > 1e-6 or abs(dz) > 1e-6:
                obj.translate(dx, 0, dz)

    def __call__(self):
        if len(self.objects) == 0:
            return

        for _ in range(self.num_steps):
            self.init_gradients()
            avg_grad_norm = self.compute_gradients()

            if avg_grad_norm < 1e-3:
                break

            objects, actions, dists = self.compute_action()
            if len(objects) == 0:
                break

            for obj, action in objects:
                action = action * self.lr
                obj.translate(action[0], action[1], action[2])

        self._snap_overlaps()
        self._clamp_to_bounds()



# class RenderingConstraint(ConstraintBase):
#     def __init__(self, group, wall, paintings, target_image_path):
#         from painting_detector import PaintingDetector
#         self.name = 'RenderingConstraint'
#         self.description = f"""
# Helps in optimizing placement of paintings on the wall to match a given image target.
# Inputs:
# - wall: The wall name (str)
# - paintings: List of painting objects (list)
# - target_image_path: Path to the target image (str)
# """
#         self.examples = f"""
# with scene.RoomGroup() as room:
#     ...
#     painting = scene.AddAsset("A Beautiful Landscape")
#     paintings = 3*paintings
#     room.place_on_wall_back_left(paintings[0])
#     room.place_on_wall_back_center(paintings[1])
#     room.place_on_wall_back_right(paintings[2])

#     room.RenderingConstraint("back_wall", paintings, "path/to/target/image.jpg")
# """

#         self.type = 'GRADIENT'
#         self.painting_detector = PaintingDetector()
#         self.target_image_path = target_image_path

#         self.target_centroids, self.target_bbox = self.painting_detector(self.target_image_path, resize=(1920,1080))
#         self.wall = wall
#         self.paintings = paintings

#         super().__init__(self.name, group)

#     def compute_gradients(self):
#         ## Render the wall with paintings
#         current_image_path = self.group.render_wall(self.wall, self.paintings)
#         ## Detect centroids of each painting using Owlv2
#         centroids, tmp = self.painting_detector(current_image_path, resize=(1920,1080))
        
#         ## Use hungarian method to derieve optimal 1-1 mapping between centroids. 
#         perm = self.painting_detector.compute_mapping(centroids, self.target_centroids)
#         mapped_centroids = [self.target_centroids[i] for i in perm]

#         for i, painting in enumerate(self.paintings):
#             grad = mapped_centroids[i] - centroids[i] ## pseudo gradient
#             img_grad[0] *= 1/1920
#             img_grad[1] *= 1/1080
#             painting.grad += np.array([img_grad[0], img_grad[1], 0], dtype=np.float32)