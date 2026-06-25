"""
Additional placement-group motifs for IDSDL.

These are purely additive: each class is a thin subclass of the existing AnchorGroup /
AroundGroup and only adds @placemethod methods that call existing public primitives
(set_location, set_rotation, face_towards, compute_obj_y, get_anchor_center_dirs, get_whd,
to_list, n*obj copies, ignore_overlap). They inherit the standard compile()/freeze lifecycle,
so no core IDSDL logic is modified.

Motifs implemented (gaps relative to the HSM motif taxonomy):
    StackGroup     - vertical stack            (motif: stack)
    PyramidGroup   - centered decreasing tiers (motif: pyramid)
    PileGroup      - organic scatter           (motif: pile)
    SymmetryGroup  - mirrored / flanking pairs (motif: on_each_side)
    FacingGroup    - two rows facing an anchor (motif: face_to_face)
    RingsGroup     - concentric surround rings (motif: multi-ring surround)
"""
import numpy as np

from IDSDL.object import placemethod
from IDSDL.groups import AnchorGroup, AroundGroup


def _anchor_base(group):
    """Return (x0, z0, base_y) for an anchored group, or the origin/floor if anchorless."""
    if group.anchor is not None:
        cx, _, cz = group.anchor.get_location()
        base_y = float(group.anchor.get_whd()[1])
        return float(cx), float(cz), base_y
    return 0.0, 0.0, 0.0


class StackGroup(AnchorGroup):
    """Stack objects vertically, each resting on the one below. If an anchor is set, the stack
    starts on top of it."""

    @placemethod
    def place_stack(self, objs):
        objs = self.to_list(objs)
        if not objs:
            return
        x0, z0, base_y = _anchor_base(self)
        cum = base_y
        for obj in objs:
            obj.set_location(x0, cum + self.compute_obj_y(obj), z0)
            obj.ignore_overlap = True  # stacked items share a footprint
            self.add_child(obj)
            cum += float(obj.get_height())


class PyramidGroup(AnchorGroup):
    """Arrange objects as centered tiers of decreasing count, stacked upward (a pyramid)."""

    @placemethod
    def place_pyramid(self, objs, base_count=None, spacing=0.05):
        objs = self.to_list(objs)
        N = len(objs)
        if N == 0:
            return
        if base_count is None:
            base_count = 1
            while base_count * (base_count + 1) // 2 < N:
                base_count += 1

        x0, z0, base_y = _anchor_base(self)
        y = base_y
        idx = 0
        tier = base_count
        while idx < N and tier > 0:
            row = objs[idx: idx + tier]
            widths = [float(o.get_width()) for o in row]
            total = sum(widths) + spacing * (len(row) - 1)
            cx = x0 - total / 2.0
            tier_height = 0.0
            for o, w in zip(row, widths):
                o.set_location(cx + w / 2.0, y + self.compute_obj_y(o), z0)
                o.ignore_overlap = True
                self.add_child(o)
                cx += w + spacing
                tier_height = max(tier_height, float(o.get_height()))
            y += tier_height
            idx += tier
            tier -= 1


class PileGroup(AnchorGroup):
    """Scatter objects organically within a disk, then let the inherited overlap solver
    (AnchorGroup.compile runs OverlapConstraint + grad_optimize) relax them apart."""

    @placemethod
    def place_pile(self, objs, spread=1.0):
        objs = self.to_list(objs)
        N = len(objs)
        if N == 0:
            return
        x0, z0, _ = _anchor_base(self)
        footprints = [max(float(o.get_width()), float(o.get_depth())) for o in objs]
        radius = spread * float(np.mean(footprints)) * np.sqrt(max(N, 1))
        rng = np.random.default_rng()
        for o in objs:
            r = radius * np.sqrt(rng.random())
            theta = rng.random() * 2 * np.pi
            o.set_location(x0 + r * np.cos(theta), self.compute_obj_y(o), z0 + r * np.sin(theta))
            o.set_rotation(float(rng.random() * 360.0))
            self.add_child(o)  # overlap intentionally left on -> solver de-overlaps


class SymmetryGroup(AnchorGroup):
    """Flank the anchor with mirror-symmetric pairs. Each given object is placed on one side and
    an auto-copy on the mirrored side, both turned to face the anchor."""

    @placemethod
    def place_flanking(self, objs, gap=0.1):
        objs = self.to_list(objs)
        if not objs:
            return
        _, _, _, _, center, w0, _, _ = self.get_anchor_center_dirs()
        x0, _, z0 = center
        offset = float(w0) / 2.0 + gap
        for o in objs:
            ow = float(o.get_width())
            d = offset + ow / 2.0
            o.set_location(x0 + d, self.compute_obj_y(o), z0)
            o.face_towards(self.anchor)
            o.ignore_overlap = True
            self.add_child(o)

            mirror = o.copy()
            mirror.set_location(x0 - d, self.compute_obj_y(mirror), z0)
            mirror.face_towards(self.anchor)
            mirror.ignore_overlap = True
            self.add_child(mirror)

            offset = d + ow / 2.0 + gap


class FacingGroup(AnchorGroup):
    """Place two parallel rows on opposite sides of the anchor, each row facing it
    (e.g. two sofas across a coffee table)."""

    def _row(self, objs, sign, gap):
        objs = self.to_list(objs)
        n = len(objs)
        if n == 0:
            return
        _, _, _, _, center, _, _, d0 = self.get_anchor_center_dirs()
        x0, _, z0 = center
        a = np.radians(self.anchor.get_rotation())

        widths = [float(o.get_width()) for o in objs]
        spacing = 0.1
        total = sum(widths) + spacing * (n - 1)
        cx = -total / 2.0
        for o, w in zip(objs, widths):
            lx = cx + w / 2.0
            lz = sign * (float(d0) / 2.0 + gap + float(o.get_depth()) / 2.0)
            # rotate the (right, front) offset by the anchor yaw (sin/cos-from-+z convention)
            wx = x0 + lx * np.cos(a) + lz * np.sin(a)
            wz = z0 - lx * np.sin(a) + lz * np.cos(a)
            o.set_location(wx, self.compute_obj_y(o), wz)
            o.face_towards(self.anchor)
            o.ignore_overlap = True
            self.add_child(o)
            cx += w + spacing

    @placemethod
    def place_facing_rows(self, side1, side2, gap=0.3):
        self._row(side1, +1, gap)
        self._row(side2, -1, gap)


class RingsGroup(AroundGroup):
    """Concentric rings of objects around the anchor (inner ring first), each ring facing inward.
    Reuses AroundGroup's `sparsity` and the place_circle radial convention."""

    @placemethod
    def place_rings(self, rings):
        rings = [self.to_list(r) for r in rings]
        _, _, _, _, center, w0, _, _ = self.get_anchor_center_dirs()
        x0, _, z0 = center
        base_dist = 0.05 + self.sparsity * 0.8
        anchor_rot = self.anchor.get_rotation()

        prev_outer = float(w0) / 2.0
        for ring in rings:
            n = len(ring)
            if n == 0:
                continue
            ang = 360.0 / n
            ring_outer = prev_outer
            for i, o in enumerate(ring):
                radius = prev_outer + base_dist + float(o.get_depth()) / 2.0
                theta = np.radians(i * ang + anchor_rot)
                o.set_location(x0 + radius * np.sin(theta),
                               self.compute_obj_y(o),
                               z0 + radius * np.cos(theta))
                o.face_towards(self.anchor)
                self.add_child(o)
                ring_outer = max(ring_outer, prev_outer + base_dist + float(o.get_depth()))
            prev_outer = ring_outer + 0.1
