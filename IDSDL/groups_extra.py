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
    MirrorStationGroup - wall mirror + facing floor item + counter/shelf (salon/gym/vanity)
    WorkstationGroup   - desk + operator chair + computer/monitor + distributed desk accessories
    KitchenIslandGroup - island/peninsula attached to a fitted U/L/straight kitchen set by
                         rasterising the set's real footprint (tip / pocket / front modes)
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


class WorkstationGroup(AnchorGroup):
    """A desk workstation: a desk (anchor) on the floor, an operator chair in front of it, and a
    computer + a few small desk accessories seated ON the desktop. A general, reusable motif for an
    office desk, a reception counter, a study desk or a classroom desk -- anywhere a "seat + screen
    + desk clutter" unit is wanted.

    Built in a local frame whose +Z is the *operator* side: the desk's working front (knee-hole,
    modelled at +Z on dataset desks) faces the operator, so the chair sits at +Z facing back. Drop
    the finished unit into a room like any group -- e.g.
    ``room.place_on_back_left_corner(ws, facing="front")`` -- and it carries its layout rigidly.

    **On-top seating uses the DSL's own ``place_on_top``** (VLM-tournament placement onto the real
    top *surface*, with the deterministic AABB fallback), NOT a hand-computed y. This is the whole
    point: seating items at the desk's aabb *top* floats them whenever that isn't the writing
    surface (a hutch/back-unit desk, or a bbox inflated by baked-in props). ``place_on_top`` finds
    the highest substantial surface instead. It works best with **a few** items, so the desktop is
    capped at ``MAX_DESKTOP_ITEMS`` (3) -- pass the computer + your two best accessories; more are
    dropped with a warning. Pair it with the ``DesktopWorkstationRetriever`` for the on-top items::

        with scene.WorkstationGroup() as ws:
            ws.set_anchor(scene.AddAsset("a simple flat wooden office desk"))
            ws.place_chair(scene.AddAsset("an ergonomic office chair"))
            ws.place_computer(scene.AddAsset("an all-in-one desktop computer"))
            ws.place_accessories([scene.AddAsset("an articulated desk lamp"),
                                  scene.AddAsset("a small potted succulent for a desk")])
    """

    CHAIR_GAP = 0.10          # desk front face -> chair (tucked but not interpenetrating)
    MAX_DESKTOP_ITEMS = 3     # place_on_top is reliable with only a few items; keep the desk clean

    def __init__(self, scene, name=None):
        super().__init__(scene, name=name)
        # Deterministic seat + delegated on-top placement: skip the per-instance VLM proportion
        # render (waste, and it would re-render N identical desks in a row). place_on_top runs its
        # own VLM pass; the room-level VLM still vets the whole scene.
        self.vlm_solver = None
        self._chair = None
        self._chair_gap = False
        self._computer = None    # the primary screen, turned to face the operator after seating
        self._desktop = []       # computer + accessories, in priority order, seated via place_on_top

    # ---- slot setters: just record; positioned in compile() ----
    def place_chair(self, chair, gap=False):
        """The operator seat (optional). Sits in front of the desk facing it; ``gap=True`` leaves
        extra circulation space behind the desk instead of tucking the chair right up to it."""
        self._chair = chair
        self._chair_gap = gap
        self.add_child(chair)
        return chair

    def place_computer(self, computer):
        """The screen (optional): a monitor or an all-in-one desktop. Seated first (highest
        priority in the <=3 desktop budget) and turned to face the operator after placement."""
        items = self.to_list(computer)
        if items:
            self._computer = items[0]
        self._desktop = items + self._desktop
        return computer

    def place_accessories(self, objs):
        """Small desk-top items (optional): lamp, pen cup, plant, papers, frame, phone. Seated on
        the real desktop surface by place_on_top, after the computer, within the <=3 budget."""
        self._desktop = self._desktop + self.to_list(objs)
        return objs

    def compile(self):
        if self.anchor is None:
            raise ValueError("WorkstationGroup needs set_anchor(<desk>) before compile.")

        cx, _, cz = (float(v) for v in self.anchor.get_location())
        wa, ha, da = (float(v) for v in self.anchor.get_whd())

        # A flat seated desk is best (place_on_top's VLM path handles a hutch, but its AABB fallback
        # would seat on the hutch top). Warn + recommend pinning a ~0.75 m flat desk.
        if ha > 1.05:
            print(f"[WorkstationGroup] WARNING: desk '{getattr(self.anchor, 'retrieval_model', '?')}' "
                  f"is {ha:.2f} m tall — likely a hutch/standing desk. Prefer a flat (~0.75 m) desk "
                  f"(pin via asset_id=) so on-top items seat on the writing surface.")

        # operator chair on the floor in front (+Z), facing the desk (rotation 180) -- floor items
        # never float, so this stays a simple deterministic placement.
        if self._chair is not None:
            ch = self._chair
            _, _, dch = (float(v) for v in ch.get_whd())
            gap = self.CHAIR_GAP + (0.25 if self._chair_gap else 0.0)
            ch.set_rotation(180.0)
            ch.set_location(cx, self.compute_obj_y(ch), cz + da / 2.0 + gap + dch / 2.0)
            ch.ignore_overlap = True

        # desktop items: delegate to place_on_top so they seat on the REAL surface (no floating),
        # capped to a few. Records a delayed op that AnchorGroup.compile() executes after layout.
        items = self._desktop
        if len(items) > self.MAX_DESKTOP_ITEMS:
            print(f"[WorkstationGroup] {len(items)} desktop items requested; place_on_top is "
                  f"reliable with <= {self.MAX_DESKTOP_ITEMS}. Seating the first "
                  f"{self.MAX_DESKTOP_ITEMS}, dropping the rest.")
            items = items[:self.MAX_DESKTOP_ITEMS]
        if items:
            self.place_on_top(items)
            # turn the screen to face the operator (the chair) once positions have settled; this
            # opt-in rotation is applied at the end of compile, after place_on_top.
            if self._computer in items:
                self.face(self._computer, toward=self._chair if self._chair is not None else self.anchor)

        return super().compile()


# ---------------------------------------------------------------------------
# Kitchen footprint analysis (pure functions, unit-testable without a scene)
# ---------------------------------------------------------------------------

_KI_CELL = 0.06          # raster cell, metres
_KI_ARM_COVERAGE = 0.45  # border coverage above which an adjacent border counts as an arm/wing
_KI_BASE_COVERAGE = 0.75 # a border must cover this much of its edge to be a candidate base run
                         # (kept permissive: a run whose modules differ in depth rasters ragged;
                         # the most-arms + longest-span tie-break disambiguates the candidates)

_KI_BORDERS = ("-x", "+x", "-z", "+z")
_KI_OPPOSITE = {"-x": "+x", "+x": "-x", "-z": "+z", "+z": "-z"}
_KI_ADJACENT = {"-x": ("-z", "+z"), "+x": ("-z", "+z"),
                "-z": ("-x", "+x"), "+z": ("-x", "+x")}
# 2D (x, z) unit vector pointing OUT of the grid through each border
_KI_AXIS = {"-x": np.array([-1.0, 0.0]), "+x": np.array([1.0, 0.0]),
            "-z": np.array([0.0, -1.0]), "+z": np.array([0.0, 1.0])}


def _ki_surface_points(obj, budget=60000):
    """World-space sample points of every leaf mesh under ``obj``: vertices plus AREA-WEIGHTED
    random points on the triangle surfaces (deterministic seed). Vertex-only sampling leaves
    big flat cabinet panels (two huge triangles) empty at raster resolution and the footprint
    degrades to noise — the surfaces themselves must be sampled."""
    chunks = []

    def rec(o):
        for c in o.children:
            rec(c)
        if o.vertices is None:
            return
        v = np.asarray(o.get_world_transform().transform_points(o.vertices))
        chunks.append(v)
        if o.faces is not None and len(o.faces):
            f = np.asarray(o.faces)
            a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
            area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
            total = float(area.sum())
            if total > 0:
                counts = np.maximum(1, np.rint(area / total * budget)).astype(int)
                idx = np.repeat(np.arange(len(f)), counts)
                rng = np.random.default_rng(0)      # deterministic: same mesh -> same raster
                r1 = np.sqrt(rng.random(len(idx)))
                r2 = rng.random(len(idx))
                chunks.append(a[idx] * (1 - r1)[:, None]
                              + b[idx] * (r1 * (1 - r2))[:, None]
                              + c[idx] * (r1 * r2)[:, None])

    rec(obj)
    if not chunks:
        raise ValueError(f"KitchenIslandGroup: '{obj.name}' has no mesh geometry to analyse.")
    return np.concatenate(chunks, axis=0)


def _ki_footprint_grid(pts, cell=_KI_CELL):
    """Occupancy grid of the BASE-height band of ``pts`` over their XZ AABB.

    The band starts just above the plinth and stops at counter height (<= 1.0 m, or half the
    total height for a short run), so bundled wall cabinets / hoods high in a full-height set
    don't pollute the floor footprint. Returns (occ[nx, nz], (x0, z0), cell)."""
    y0 = float(pts[:, 1].min())
    h = float(np.ptp(pts[:, 1]))
    hi = y0 + (min(1.0, 0.5 * h) if h > 1.2 else h)
    band = pts[(pts[:, 1] >= y0 + 0.04) & (pts[:, 1] <= hi)]
    if len(band) < 16:
        band = pts
    x0, z0 = float(band[:, 0].min()), float(band[:, 2].min())
    # cap the raster at ~48 cells across: classification needs shape, not 6 cm detail, and a
    # coarser grid is far more robust to sampling gaps on a big set
    cell = max(cell, float(np.ptp(band[:, 0])) / 48.0, float(np.ptp(band[:, 2])) / 48.0)
    nx = max(2, int(np.ceil(float(np.ptp(band[:, 0])) / cell)))
    nz = max(2, int(np.ceil(float(np.ptp(band[:, 2])) / cell)))
    occ = np.zeros((nx, nz), dtype=bool)
    ix = np.clip(((band[:, 0] - x0) / cell).astype(int), 0, nx - 1)
    iz = np.clip(((band[:, 2] - z0) / cell).astype(int), 0, nz - 1)
    occ[ix, iz] = True
    return occ, (x0, z0), cell


def _ki_border_coverage(occ):
    """Fraction of each border band's edge length that has ANY occupied cell (band thickness
    18% of the grid, min 2 cells). A full run reads ~1.0; a U's short wing ~0.7; the mere
    side-spill of a perpendicular run ~0.3."""
    nx, nz = occ.shape
    tx = max(2, int(round(0.18 * nx)))
    tz = max(2, int(round(0.18 * nz)))
    return {
        "-x": float(occ[:tx, :].any(axis=0).mean()),
        "+x": float(occ[-tx:, :].any(axis=0).mean()),
        "-z": float(occ[:, :tz].any(axis=1).mean()),
        "+z": float(occ[:, -tz:].any(axis=1).mean()),
    }


def _ki_classify(occ, cell=_KI_CELL):
    """Classify a kitchen footprint as U / L / straight.

    The base run is the candidate border (coverage >= _KI_BASE_COVERAGE) with the MOST
    qualifying arms, tie-broken by physical span — coverage alone ties a U's base run with its
    own full-length wing. Returns dict(shape, base, arms={border: coverage}, coverage, fill)."""
    cov = _ki_border_coverage(occ)
    nx, nz = occ.shape
    span = {"-x": nz * cell, "+x": nz * cell, "-z": nx * cell, "+z": nx * cell}
    fill = float(occ.mean())

    candidates = [b for b in _KI_BORDERS if cov[b] >= _KI_BASE_COVERAGE]
    if not candidates:
        candidates = [max(cov, key=lambda b: cov[b])]

    def arms_of(b):
        return {a: cov[a] for a in _KI_ADJACENT[b] if cov[a] >= _KI_ARM_COVERAGE}

    base = max(candidates, key=lambda b: (len(arms_of(b)), span[b], cov[b]))
    arms = arms_of(base)

    if fill > 0.7:
        shape = "straight"      # a solid slab lights every border; it has no cavity to arm
        arms = {}
    elif len(arms) == 2:
        shape = "U"
    elif len(arms) == 1:
        shape = "L"
    else:
        shape = "straight"
    return {"shape": shape, "base": base, "arms": arms, "coverage": cov, "fill": fill}


def _ki_raster_str(occ):
    """ASCII footprint, z increasing downward (rows) and x rightward (columns)."""
    return "\n".join(
        "".join("#" if occ[i, j] else "." for i in range(occ.shape[0]))
        for j in range(occ.shape[1]))


class KitchenIslandGroup(AnchorGroup):
    """Attach an island / dining counter to a fitted kitchen set the way a kitchen designer
    would, by analysing the set's REAL footprint (rasterised from its mesh) instead of its AABB:

    - ``tip``    (U-shaped sets): the island attaches at the frontal tip of the LONGER wing and
      runs across the U's mouth, half-enclosing the cook zone and leaving a single walk-in gap
      at the other wing (a peninsula/G-kitchen). ``min_entry`` guards the gap; the island is
      shrunk if it would seal the mouth.
    - ``pocket`` (L-shaped sets): the island floats in the concave middle of the L — inside the
      set's AABB, centred in the quadrant the counters don't occupy — with ``min_aisle``
      clearance to both runs. Also works inside a deep U's cavity.
    - ``front``  (straight sets): the classic galley — the island runs parallel to the run,
      ``min_aisle`` in front of it.

    ``mode="auto"`` picks tip / pocket / front for U / L / straight respectively. The analysis
    (ASCII raster, border coverages, wing lengths, chosen attachment) is printed at compile so
    the choice is auditable. The whole unit is rigid: place it in the room with ONE corner op
    (kitchen.md's alignment rules apply to the composed group exactly as to a bare set) and pin
    it with ``is_static = True``.

    The island and stools necessarily sit inside the set's AABB (that is the point), so they are
    flagged ``ignore_overlap`` — the 2D footprint clash with the set is not a real one. Example::

        with scene.KitchenIslandGroup() as kz:
            kz.set_anchor(scene.AddAsset("...", asset_id=U_SET))
            kz.place_island(scene.AddAsset("a kitchen island counter", asset_id=ISLAND))
            kz.place_stools(3 * scene.AddAsset("a counter stool", asset_id=STOOL))
        ...
        room.place_on_back_right_corner(kz, facing="front")
        kz.is_static = True
    """

    STOOL_GAP = 0.08        # island outward face -> stool front
    MIN_ISLAND_WIDTH = 0.6  # below this, shrinking the island to protect the entry is refused

    def __init__(self, scene, name=None, cell=_KI_CELL):
        super().__init__(scene, name=name)
        self.cell = cell
        # Deterministic, self-auditing layout: the per-group VLM proportion render is waste
        # (and the room-level VLM still vets the whole scene).
        self.vlm_solver = None
        self._island = None
        self._island_opts = {}
        self._stools = []
        self._stool_gap = self.STOOL_GAP
        self.analysis = None    # filled by _layout(); exposed for tests / offline audits

    # ---- slot setters: record + parent; positioned in _layout() at compile ----
    def place_island(self, island, mode="auto", wing="auto",
                     min_entry=0.9, min_aisle=0.75, attach_overlap=0.05):
        """The island/peninsula counter (required). ``wing`` (tip mode) is one of
        ``"auto"|"-x"|"+x"|"-z"|"+z"`` in the SET'S OWN frame as printed by the raster —
        ``auto`` attaches at the longer wing. ``attach_overlap`` sinks the attached end this far
        into the wing so the joint reads as continuous joinery, not two nearby blocks."""
        self._island = island
        self._island_opts = dict(mode=mode, wing=wing, min_entry=float(min_entry),
                                 min_aisle=float(min_aisle), attach_overlap=float(attach_overlap))
        self.add_child(island)
        return island

    def place_stools(self, stools, gap=None):
        """Counter stools, seated in a straight row along the island's OUTWARD face (the side
        away from the cook zone), each facing the island. A parallel row, deliberately NOT
        fanned at the island's centre point (bar.md's place_rectilinear rule)."""
        self._stools = self.to_list(stools)
        if gap is not None:
            self._stool_gap = float(gap)
        for s in self._stools:
            self.add_child(s)
        return stools

    # ---- geometry helpers ----
    @staticmethod
    def _rot_deg(u):
        """Rotation (deg) that turns local +z into the 2D direction ``u`` under the DSL's yaw
        convention (x' = x cos a + z sin a, z' = -x sin a + z cos a)."""
        return float(np.degrees(np.arctan2(u[0], u[1])))

    def _layout(self):
        if self.anchor is None:
            raise ValueError("KitchenIslandGroup needs set_anchor(<kitchen set>) before compile.")
        if self._island is None:
            raise ValueError("KitchenIslandGroup needs place_island(<counter>) before compile.")

        opts = self._island_opts
        pts = _ki_surface_points(self.anchor)
        occ, (gx0, gz0), cell = _ki_footprint_grid(pts, self.cell)
        info = _ki_classify(occ, cell)
        nx, nz = occ.shape
        gx1, gz1 = gx0 + nx * cell, gz0 + nz * cell
        cov = info["coverage"]
        tag = "[KitchenIslandGroup]"
        print(f"{tag} set footprint {nx * cell:.2f} x {nz * cell:.2f} m, fill {info['fill']:.2f}; "
              f"border coverage " + " ".join(f"{b}:{cov[b]:.2f}" for b in _KI_BORDERS))
        print(_ki_raster_str(occ))

        # occupied cell centres, world metres
        ii, jj = np.nonzero(occ)
        px = gx0 + (ii + 0.5) * cell
        pz = gz0 + (jj + 0.5) * cell
        P = np.stack([px, pz], axis=1)

        base = info["base"]
        n = _KI_AXIS[_KI_OPPOSITE[base]]          # away from the base run, into the room
        s_n = P @ n                                # scalar coord of each occupied cell along n
        corners = np.array([[gx0, gz0], [gx0, gz1], [gx1, gz0], [gx1, gz1]])
        cn = corners @ n
        base_edge_n, far_n = float(cn.min()), float(cn.max())

        # base-run thickness: leading full-ish slices from the base edge
        prof_axis = 1 if base in ("-x", "+x") else 0     # mean over the axis PERPENDICULAR to n
        slices = occ.mean(axis=prof_axis)                # coverage per slice along n
        if base in ("+x", "+z"):
            slices = slices[::-1]
        thick_cells = 1
        while thick_cells < len(slices) and slices[thick_cells] >= 0.5:
            thick_cells += 1
        base_front_n = base_edge_n + thick_cells * cell

        def arm_metrics(w):
            """(tip_n, inner_s) for arm at border ``w``: how far it runs from the base edge, and
            the scalar coord (along +w's axis) of its inner face past the base run."""
            e = _KI_AXIS[w]                       # toward the arm
            s_e = P @ e
            ce = corners @ e
            arm_band = s_e >= float(ce.max()) - max(2, int(round(0.18 * (nx if w in ("-x", "+x") else nz)))) * cell
            tip_n = float(s_n[arm_band].max()) + 0.5 * cell if arm_band.any() else base_front_n
            beyond = s_n > base_front_n
            half = s_e > (float(ce.min()) + float(ce.max())) / 2.0
            sel = beyond & half
            inner_s = float(s_e[sel].min()) - 0.5 * cell if sel.any() else float(ce.max())
            return tip_n, inner_s

        mode = opts["mode"]
        if mode == "auto":
            mode = {"U": "tip", "L": "pocket", "straight": "front"}[info["shape"]]
        self.analysis = dict(info, mode=mode, grid=(nx, nz), cell=cell)

        island = self._island
        wi, hi_, di = (float(v) for v in island.get_whd())
        min_aisle = opts["min_aisle"]

        if mode == "tip":
            if len(info["arms"]) < 2:
                raise ValueError(f"{tag} tip mode needs a U footprint; analysis says "
                                 f"{info['shape']} (arms {info['arms']}). Pass mode= explicitly "
                                 f"or pick a U set.")
            wing = opts["wing"]
            lens = {w: arm_metrics(w)[0] - base_edge_n for w in info["arms"]}
            if wing == "auto":
                wing = max(lens, key=lens.get)
                if abs(max(lens.values()) - min(lens.values())) < 0.05:
                    print(f"{tag} wings are near-equal ({lens}); attached at {wing} — pass "
                          f"wing= to choose explicitly.")
            elif wing not in info["arms"]:
                raise ValueError(f"{tag} wing={wing!r} is not an arm of this set "
                                 f"(arms: {list(info['arms'])}).")
            other = _KI_OPPOSITE[wing]
            e = _KI_AXIS[wing]                    # toward the attach wing
            tip_n, inner_s = arm_metrics(wing)
            _, inner_other = arm_metrics(other)
            mouth = inner_s - (-inner_other)      # clear span between the two wings' inner faces
            print(f"{tag} shape=U base={base} wings: " +
                  ", ".join(f"{w} {lens[w]:.2f} m" for w in lens) +
                  f" -> attach at {wing}; mouth {mouth:.2f} m")

            ov = opts["attach_overlap"]
            entry = mouth + ov - wi
            if entry < opts["min_entry"]:
                new_w = mouth + ov - opts["min_entry"]
                if new_w < self.MIN_ISLAND_WIDTH:
                    print(f"{tag} WARNING: mouth {mouth:.2f} m cannot fit an island "
                          f">= {self.MIN_ISLAND_WIDTH} m plus a {opts['min_entry']} m entry — "
                          f"island left at {wi:.2f} m; entry gap {entry:.2f} m is TIGHT.")
                else:
                    print(f"{tag} island {wi:.2f} m would leave a {entry:.2f} m entry "
                          f"(< {opts['min_entry']} m) — shrunk to {new_w:.2f} m.")
                    island.scale_only_width(new_w)
                    wi = float(island.get_width())
                    entry = mouth + ov - wi
            print(f"{tag} island {wi:.2f} m across the mouth, flush with the {wing} wing tip; "
                  f"entry gap {entry:.2f} m at the {other} side.")
            c_n = tip_n - di / 2.0                # far face flush with the wing's frontal tip
            c_s = inner_s + ov - wi / 2.0         # attached end sunk `ov` into the wing
            cx, cz = e * c_s + n * c_n
            out_dir = n
            self.analysis.update(wing=wing, mouth=mouth, entry=entry, tip_n=tip_n)

        elif mode == "pocket":
            if info["shape"] == "straight" or not info["arms"]:
                raise ValueError(f"{tag} pocket mode needs an L (or U) footprint; analysis says "
                                 f"{info['shape']}. Pass mode='front' for a straight set.")
            # pocket bounds: past the base run along n; between the arm inner faces (or the open
            # AABB edges) across. For an L, one side is an arm and the other is open.
            lo_n, hi_n = base_front_n, far_n
            s_bounds = []
            for w in _KI_ADJACENT[base]:
                e = _KI_AXIS[w]
                ce = corners @ e
                if w in info["arms"]:
                    tip_n_w, inner_w = arm_metrics(w)
                    s_bounds.append((e, inner_w))
                    hi_n = min(hi_n, max(tip_n_w, base_front_n + 2 * cell)) if info["shape"] == "U" else hi_n
                else:
                    s_bounds.append((e, float(ce.max())))
            (e1, b1), (e2, b2) = s_bounds         # e2 = -e1; span across is [-b2, b1] along e1
            lo_s, hi_s = -b2, b1
            c_n = (lo_n + hi_n) / 2.0
            c_s = (lo_s + hi_s) / 2.0
            aisle_base = (c_n - di / 2.0) - lo_n
            print(f"{tag} shape={info['shape']} base={base} arms {list(info['arms'])} -> pocket "
                  f"{hi_s - lo_s:.2f} x {hi_n - lo_n:.2f} m; island centred at its middle.")
            span = hi_s - lo_s
            if wi > span - 2 * min_aisle:
                new_w = span - 2 * min_aisle
                if new_w >= self.MIN_ISLAND_WIDTH:
                    print(f"{tag} island {wi:.2f} m leaves < {min_aisle} m aisles across the "
                          f"{span:.2f} m pocket — shrunk to {new_w:.2f} m.")
                    island.scale_only_width(new_w)
                    wi = float(island.get_width())
                else:
                    print(f"{tag} WARNING: pocket span {span:.2f} m is tight for the island "
                          f"({wi:.2f} m); aisles will be narrow.")
            if aisle_base < min_aisle:
                print(f"{tag} WARNING: aisle to the base run is {aisle_base:.2f} m "
                      f"(< {min_aisle} m) — consider a shallower island or a bigger room.")
            cx, cz = e1 * c_s + n * c_n
            out_dir = n
            self.analysis.update(pocket=(hi_s - lo_s, hi_n - lo_n), aisle_base=aisle_base)

        elif mode == "front":
            run_w = (gx1 - gx0) if base in ("-z", "+z") else (gz1 - gz0)
            e = _KI_AXIS[_KI_ADJACENT[base][1]]   # +x for a z base, +z for an x base
            mid_s = float((corners @ e).min() + (corners @ e).max()) / 2.0
            c_n = base_front_n + min_aisle + di / 2.0
            print(f"{tag} shape={info['shape']} base={base} -> galley island {min_aisle:.2f} m "
                  f"in front of the {run_w:.2f} m run.")
            cx, cz = e * mid_s + n * c_n
            out_dir = n

        else:
            raise ValueError(f"{tag} unknown mode {mode!r} (tip / pocket / front / auto).")

        island.set_rotation(self._rot_deg(out_dir))
        island.set_location(float(cx), self.compute_obj_y(island), float(cz))
        island.ignore_overlap = True              # it sits inside the set's AABB by design

        # stools: a straight parallel row along the island's outward face, each facing it
        if self._stools:
            e_along = np.array([out_dir[1], -out_dir[0]])   # island's long axis
            stool_rot = self._rot_deg(-out_dir)
            row_n = float(np.array([cx, cz]) @ out_dir) + di / 2.0
            c_along = float(np.array([cx, cz]) @ e_along)
            # a shrunken island seats fewer stools — drop the overflow instead of overlapping them
            sw = max(float(s.get_width()) for s in self._stools)
            max_n = max(1, int(wi // (sw + 0.05)))
            if len(self._stools) > max_n:
                print(f"{tag} island is {wi:.2f} m wide — seats {max_n} of the "
                      f"{len(self._stools)} stools; dropping the rest.")
                for st in self._stools[max_n:]:
                    self.children.remove(st)
                self._stools = self._stools[:max_n]
            N = len(self._stools)
            for k, st in enumerate(self._stools):
                _, _, sd = (float(v) for v in st.get_whd())
                frac = (k + 1) / (N + 1) - 0.5
                p = e_along * (c_along + frac * wi) + out_dir * (row_n + self._stool_gap + sd / 2.0)
                st.set_rotation(stool_rot)
                st.set_location(float(p[0]), self.compute_obj_y(st), float(p[1]))
                st.ignore_overlap = True

    def compile(self):
        self._layout()
        return super().compile()
