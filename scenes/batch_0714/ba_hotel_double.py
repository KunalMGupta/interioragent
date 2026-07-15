"""Hotel-style bathroom — "Grey Marble & Warm Wood Hotel Bath".

Brief: a DOUBLE vanity (the mesh bundles its own wide mirror — no separate mirror is hung), a
walk-in glass shower, a toilet SET, a towel ladder + plush rolled towels, candles, a botanical
print. Grey marble + warm wood palette.

Layout — the bathroom_v1 two-hero skeleton, hotel edition:
- BACK wall  (long) : the DOUBLE vanity HERO, centre — the his-and-hers run is the hotel
                      signature and the money shot from the door.
- LEFT wall  (short): the wet zone — the walk-in shower in the END slot (at ~2 m it would blind
                      the left camera parked at the wall CENTRE — bakery/closet rule) + the
                      toilet set beside it (low, camera-safe).
- RIGHT wall (short): the door (right) + a LOW teak bench at the centre the camera sees OVER
                      (grocery_store's counter trick) — it carries the plush towels and candles
                      at viewing height in phase 2, since the vanity top is off-limits.
- BACK-RIGHT corner : the towel ladder — 1.7 m tall, so corner, not a wall centre.
- FRONT wall        : a standard curtained window (phase 3) + a palm in the left corner.
- CENTRE            : open — the barefoot lane between vanity and window.

Phase-gated: phase 1 = ALL floor mass + door; phase 2 = the towels + candles on the bench ledge;
phase 3 = the botanical print, the window, the flush lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BathroomHotelDouble", seed=34)

# ---- pinned heroes (audited on the retrieve contact sheets, 2026-07-14) -------------------------
VANITY = "hssd/44a88da97b60a73257237b8bfe6e87dbfe1106c8"  # warm-wood DOUBLE vanity SET — cabinet,
                                                          # two sinks AND its own wide mirror in
                                                          # one mesh. bathroom_v1's audited pin,
                                                          # re-confirmed rank-1 (0.85) today.
                                                          # Tagged 'double' in vanity_types.json ->
                                                          # AddAsset auto-applies real width+mount.
SHOWER = "hssd/2c0d3b1f712185ebacd6cb5e39e1551e13e6ee60"  # the only candidate whose preview shows
                                                          # an actual OPEN walk-in glass entry —
                                                          # its siblings render as solid white
                                                          # boxes (form factor, not caption).
TOILET = "hssd/3ddc49c94cf0205a2d4673d81f671dc5f90b953a"  # complete toilet SET (cistern + TP
                                                          # holder + brush bundled), rank-1.
LADDER = "hssd/f63203ce3955e3df53c4e59d9e73f9fff3a6c351"  # bathroom_v1's audited pin — a ladder
                                                          # that actually CARRIES a towel.

scene.prefetch_assets([
    "a modern wood double bathroom vanity with two sinks and a wide mirror",
    "a walk-in glass shower enclosure",
    "a modern white toilet",
    "a wooden towel ladder with a white towel",
    "a low teak wood bathroom bench",
    "a stack of rolled white plush towels",
    "a cluster of white spa pillar candles",
    "a tall potted areca palm plant",
    "a framed botanical wall art print",
    "a flat round LED flush mount ceiling light",
])


def _fit_width(o, target_w):
    """Bathroom fixtures carry BROKEN scale metadata — enforce real size by scaling UNIFORMLY
    from the width so the mesh keeps its proportions (never per-axis: it distorts bowls/drawers)."""
    w0, h0, d0 = o.get_width(), o.get_height(), o.get_depth()
    f = target_w / max(w0, 1e-6)
    o.scale_only_width(w0 * f); o.scale_only_height(h0 * f); o.scale_only_depth(d0 * f)
    return o


def _dims(o, w=None, h=None, d=None):
    """Force per-axis dims — ONLY for meshes whose proportions are genuinely wrong (the shower
    enclosure class, modelled too shallow/short); everything else goes through _fit_width."""
    if w is not None: o.scale_only_width(w)
    if h is not None: o.scale_only_height(h)
    if d is not None: o.scale_only_depth(d)
    return o


# ---- PHASE 1 fixtures at real-world size --------------------------------------------------------
# the double vanity's 1.5 m width + floor mount come free from the vanity tagger metadata
vanity = scene.AddAsset("a modern wood double bathroom vanity with two sinks and a wide mirror",
                        asset_id=VANITY)

shower = _dims(scene.AddAsset("a walk-in glass shower enclosure", asset_id=SHOWER),
               w=1.1, h=2.0, d=1.0)   # a real walk-in footprint (bathroom_v1 calibration)

# toilet sets bundle peripherals into one bbox so the seat reads small -> uniform ~0.9 m
toilet = _fit_width(scene.AddAsset("a modern white toilet", asset_id=TOILET), 0.90)

ladder = scene.AddAsset("a wooden towel ladder with a white towel", asset_id=LADDER)
ladder.scale(ladder.get_width() * 1.7 / max(ladder.get_height(), 1e-6))  # uniform height-fit

# ---- the towel bench: the LOW ledge that carries the phase-2 ritual -----------------------------
# The vanity top is off-limits (complete SET, complex top — bathroom.md), so the plush towels and
# candles live on a bench instead. A LOW anchor also sizes on-top props readably (laundry_room's
# "product reads on a LOW surface"); at ~0.45 m the right camera sees clean over it.
with scene.RelativeGroup() as bench_unit:
    bench = scene.AddAsset("a low teak wood bathroom bench")
    _dims(bench, w=1.1, h=0.45, d=0.4)
    bench_unit.set_anchor(bench)
    if PHASE >= 2:
        # gates INSIDE the with block — an op registered after __exit__ silently never runs
        bench_unit.place_on_top([
            scene.AddAsset("a stack of rolled white plush towels"),
            scene.AddAsset("a cluster of white spa pillar candles"),
        ])

palm = scene.AddAsset("a tall potted areca palm plant")

# modulate_scale=0.75 — a hotel bath is generous but still enclosed (bathroom_v1 used 0.72).
with scene.RoomGroup(modulate_scale=0.75, randomness=0.1) as room:
    # grey marble + warm wood: the marble carries the walls/floor, the WOOD arrives on the vanity,
    # bench and ladder meshes. A warm greige wall (not white-marble walls) keeps the tonal range —
    # an all-high-albedo room blows out under daylight (bathroom.md palette gotcha).
    room.place_walls(floor_texture="honed grey marble tiles",
                     ceiling_texture="soft white",
                     wall_texture="warm light greige limestone")

    # --- PHASE 1: ALL the floor mass ---
    room.place_on_back_wall_center(vanity)          # the double-sink money shot from the door
    room.place_on_left_wall_left(shower)            # 2 m glass box -> END slot, off the camera centre
    room.place_on_left_wall_right(toilet)
    room.place_on_right_wall_center(bench_unit)     # 0.45 m — the camera sees over it
    room.place_on_back_right_corner(ladder)         # tall piece -> corner
    room.place_on_front_left_corner(palm)
    # door in PHASE 1: its clearance shapes the floor solve
    room.place_door("right_wall", position="right")

    if PHASE >= 3:
        # botanical print over the LOW bench run (laundromat: art over a low run is safe) —
        # pre-shrunk BEFORE place_on_wall_* so the mount height doesn't clip the ceiling
        botanical = scene.AddAsset("a framed botanical wall art print")
        botanical.scale_only_width(0.7); botanical.scale_only_height(0.9); botanical.scale_only_depth(0.03)
        room.place_on_wall_right_center(botanical)
        # daylight on the empty front wall; standard pane, sheer curtain
        room.place_window_standard("front_wall", position="center",
                                   curtain="sheer white curtains")
        # flush fixtures at 0.015 for a mid-size bath (0.02+ starfields)
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.015)

scene.export("ba_hotel_double.blend")
