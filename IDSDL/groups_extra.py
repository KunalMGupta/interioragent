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


class MirrorStationGroup(AnchorGroup):
    """A wall-mirror station: a floor item (chair / treadmill / vanity stool) anchored on the
    floor, a mirror mounted on the wall behind it, plus optional counter / floating shelf (with
    decor on top) / side slot.

    Built in a local frame whose +Z is the *viewing axis*: the anchor faces +Z and the mirror
    (and any counter/shelf) sit on the +Z (wall) side, facing back toward the anchor. Place the
    finished unit against a wall with ``room.place_on_back(station)`` +
    ``room.face(station, toward="<wall>")`` -- or drop N of them in a GridGroup row first and face
    the row. ``face`` rotates the group rigidly, so the mirror is carried to the wall at height
    with the anchor facing it; the same unit works against any of the four walls.

    Only public primitives are used (set_location / set_rotation / scale_only_* / compute_obj_y /
    get_whd / ignore_overlap), so no core IDSDL logic is touched. Example::

        with scene.MirrorStationGroup() as st:
            st.set_anchor(scene.AddAsset("a salon styling chair"))
            st.place_counter(scene.AddAsset("a narrow styling console"))
            st.place_mirror(scene.AddAsset("an arched gold-framed salon mirror"))
    """

    # gaps / heights, metres
    CHAIR_COUNTER_GAP = 0.12       # anchor front face -> counter front face
    ABOVE_GAP = 0.12               # top of the floor stack -> bottom of the next wall element
    BESIDE_GAP = 0.12              # anchor side -> side object
    MIRROR_DEFAULT_CENTER_Y = 1.5  # standalone mirror centre (matches the RoomGroup wall default)
    MIRROR_MAX_HEIGHT = 1.8        # cap so a wide station does not tile the whole wall
    MIRROR_WALL_OFFSET = 0.05      # stand the mirror this far proud of the wall (toward the anchor)
                                   # so its reflective face isn't coplanar with the wall (no reflection)
    COUNTER_MAX_HEIGHT = 1.0       # a styling counter is desk-height, not a bar table
    SHELF_MAX_HEIGHT = 0.30        # a floating shelf is thin
    SHELF_DEFAULT_CENTER_Y = 1.05
    DEFAULT_MAX_TOP = 2.7          # keep the whole station under a standard ~3 m ceiling

    def __init__(self, scene, name=None, max_top=None):
        super().__init__(scene, name=name)
        # the station's topmost point (mirror top) is kept at/under this height so the unit never
        # breaches the ceiling; pass a smaller value for a known-short room.
        self.max_top = self.DEFAULT_MAX_TOP if max_top is None else float(max_top)
        # This is a deterministic, hand-laid-out, auto-fitting unit, so the per-instance VLM
        # proportion check (which renders the group) is pure waste — and a row of N identical
        # stations would render N times. Disable it; the room-level VLM still vets the whole scene.
        self.vlm_solver = None
        self._mirror = None
        self._mirror_height = None
        self._mirror_width_ratio = 1.0
        self._counter = None
        self._shelf = None
        self._shelf_items = []
        self._beside = None  # (obj, side)

    # ---- slot setters: record + parent the object; positioned later in _layout() ----
    def place_mirror(self, mirror, height=None, width_ratio=1.0):
        """The wall mirror (required). Sized to the station width (* ``width_ratio``); mounted on
        the wall above the floor stack, or centred at ~1.5 m if the station is bare. ``height``
        overrides the mirror-centre height explicitly."""
        self._mirror = mirror
        self._mirror_height = height
        self._mirror_width_ratio = width_ratio
        self.add_child(mirror)
        return mirror

    def place_counter(self, counter):
        """Optional console/credenza against the wall, under the mirror, on the floor."""
        self._counter = counter
        self.add_child(counter)
        return counter

    def place_shelf(self, shelf, items=None):
        """Optional thin floating wall shelf below the mirror; ``items`` (one or a list) are seated
        on its top surface."""
        self._shelf = shelf
        self._shelf_items = self.to_list(items) if items is not None else []
        self.add_child(shelf)
        for it in self._shelf_items:
            self.add_child(it)
        return shelf

    def place_beside(self, obj, side="right"):
        """Optional side slot (rolling trolley / side table) beside the anchor (``"right"``/``"left"``)."""
        self._beside = (obj, side)
        self.add_child(obj)
        return obj

    @staticmethod
    def _cap_height(obj, max_h):
        """Uniformly shrink ``obj`` so its height is at most ``max_h`` (never enlarges); returns
        the resulting (w, h, d)."""
        w, h, d = (float(v) for v in obj.get_whd())
        if h > max_h and h > 1e-6:
            f = max_h / h
            obj.scale_only_width(w * f)
            obj.scale_only_height(h * f)
            obj.scale_only_depth(d * f)
            w, h, d = (float(v) for v in obj.get_whd())
        return w, h, d

    # ---- deterministic layout, run once at the start of compile() ----
    def _layout(self):
        if self.anchor is None:
            raise ValueError("MirrorStationGroup needs set_anchor(<floor item>) before compile.")
        if self._mirror is None:
            raise ValueError("MirrorStationGroup needs place_mirror(<mirror>) before compile.")

        cx, _, cz = (float(v) for v in self.anchor.get_location())
        wa, _, da = (float(v) for v in self.anchor.get_whd())

        wall_z = cz + da / 2.0   # running wall plane (starts at the anchor's front face)
        stack_top = 0.0          # running top of the floor stack under the mirror
        station_w = wa           # width the mirror/shelf size themselves to

        # counter against the wall, in front of the anchor, facing back toward it
        if self._counter is not None:
            c = self._counter
            wc, hc, dc = self._cap_height(c, self.COUNTER_MAX_HEIGHT)  # desk-height, not a bar table
            cz_c = wall_z + self.CHAIR_COUNTER_GAP + dc / 2.0
            c.set_rotation(180.0)
            c.set_location(cx, self.compute_obj_y(c), cz_c)
            c.ignore_overlap = True
            wall_z = cz_c + dc / 2.0
            stack_top = hc
            station_w = max(station_w, wc)

        # floating shelf above the floor stack, below the mirror, with decor seated on top
        if self._shelf is not None:
            s = self._shelf
            ws, hs, ds = self._cap_height(s, self.SHELF_MAX_HEIGHT)  # a floating shelf is thin
            shelf_center = max(self.SHELF_DEFAULT_CENTER_Y, stack_top + self.ABOVE_GAP + hs / 2.0)
            s.set_rotation(180.0)
            s.set_location(cx, (shelf_center - hs / 2.0) + self.compute_obj_y(s), wall_z + ds / 2.0)
            s.ignore_overlap = True
            station_w = max(station_w, ws)
            shelf_top = shelf_center + hs / 2.0
            items_h = 0.0
            n = len(self._shelf_items)
            for i, it in enumerate(self._shelf_items):
                _, hi, _ = (float(v) for v in it.get_whd())
                ix = cx - ws / 2.0 + (i + 1) / (n + 1) * ws
                it.set_rotation(180.0)
                it.set_location(ix, shelf_top + self.compute_obj_y(it), wall_z + ds / 2.0)
                it.ignore_overlap = True
                items_h = max(items_h, hi)
            stack_top = shelf_top + items_h

        # the mirror: sized to the station width, mounted on the wall above the stack, and shrunk
        # if needed so its top stays under the ceiling cap (self.max_top)
        m = self._mirror
        w0, h0, d0 = (float(v) for v in m.get_whd())
        factor = (station_w * self._mirror_width_ratio) / max(w0, 1e-6)
        if h0 * factor > self.MIRROR_MAX_HEIGHT:
            factor = self.MIRROR_MAX_HEIGHT / max(h0, 1e-6)
        # available height before the mirror top reaches self.max_top, given where it will sit
        if self._mirror_height is not None:
            allowed_h = 2.0 * (self.max_top - float(self._mirror_height))     # symmetric about its centre
        elif stack_top > 0.0:
            allowed_h = self.max_top - (stack_top + self.ABOVE_GAP)           # sits just above the stack
        else:
            allowed_h = 2.0 * (self.max_top - self.MIRROR_DEFAULT_CENTER_Y)   # centred at the default height
        if allowed_h > 0.0 and h0 * factor > allowed_h:
            factor = allowed_h / max(h0, 1e-6)
        m.scale_only_width(w0 * factor)
        m.scale_only_height(h0 * factor)
        m.scale_only_depth(d0 * factor)
        _, hm, dm = (float(v) for v in m.get_whd())
        if self._mirror_height is not None:
            center_y = float(self._mirror_height)
        elif stack_top > 0.0:
            center_y = stack_top + self.ABOVE_GAP + hm / 2.0
        else:
            center_y = self.MIRROR_DEFAULT_CENTER_Y
        m.set_rotation(180.0)
        # Stand the mirror MIRROR_WALL_OFFSET proud of the floor stack's wall plane (wall_z),
        # toward the anchor. This keeps the counter (at wall_z) as the flush-to-wall element while
        # the mirror sits slightly off the wall, so its reflective face reads (isn't coplanar).
        mirror_z = wall_z - self.MIRROR_WALL_OFFSET - dm / 2.0
        m.set_location(cx, (center_y - hm / 2.0) + self.compute_obj_y(m), mirror_z)
        m.ignore_overlap = True

        # optional side object beside the anchor
        if self._beside is not None:
            obj, side = self._beside
            wb, _, _ = (float(v) for v in obj.get_whd())
            sign = 1.0 if side == "right" else -1.0
            obj.set_location(cx + sign * (wa / 2.0 + self.BESIDE_GAP + wb / 2.0),
                             self.compute_obj_y(obj), cz + da / 2.0)
            obj.ignore_overlap = True

    def compile(self):
        self._layout()
        return super().compile()
