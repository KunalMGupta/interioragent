"""Compact powder room — "Teal Jewel-Box Powder Room".

Brief: the SMALLEST room in the batch — a single vanity (the mesh bundles its OWN mirror, so no
separate mirror is ever hung), a toilet SET, a hand-towel ladder, one plant, one small print.
No window: a powder room is an interior room, and the saturated wall does the mood instead.

Layout — four objects, four jobs, nothing in the middle:
- BACK wall  : the vanity (its bundled mirror faces the door — the first thing a guest sees).
- LEFT wall  : the toilet set. Low (~0.9 m), so the wall centre stays camera-safe.
- BACK-RIGHT : the towel ladder, in the corner — at ~1.7 m it is TALLER than the ~1.4-1.5 m
               interior cameras, so it stays off the wall centres (bakery/closet camera rule).
- FRONT wall : the door (left) + a small plant in the right corner.

The footprint is deliberately TIGHT: modulate_scale=0.6, far under 1 — a powder room that solves
to a full bathroom shell stops being a powder room (laundromat's "a genuinely sparse room may
shrink below 1.0", pushed further because sparse + tiny is the brief).

Phase-gated: phase 1 = ALL floor mass + door. Phase 2 is deliberately EMPTY — the vanity is a
complete SET with a complex top (never place_on_top a vanity) and the toilet set bundles its own
TP holder and brush, so there is no honest surface layer (the kitchen.md precedent). Phase 3 =
the print + the flush light.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BathroomPowderCompact", seed=33)

# ---- pinned heroes (audited on the retrieve contact sheets, 2026-07-14) -------------------------
# hssd/ca21a1bc floated 0.17 m at phase 1 (off-center mesh origin — the lint says swap, never
# compensate); replaced with the next type-tagged single from vanity_types.json.
VANITY = "hssd/6b408a09af773f17c06c960ad0ec13f2434638d9"  # single vanity SET — cabinet, sink
                                                          # AND its own matching mirror in one mesh
                                                          # (top similarity 0.74). Tagged 'single'
                                                          # in vanity_types.json, so AddAsset
                                                          # auto-applies its real width + mount —
                                                          # no manual scaling, no separate mirror.
                                                          # Black reads sharp against the teal wall.
TOILET = "hssd/c6699cfbd43780c6a1d3d1b5a8e540e148582e10"  # complete toilet SET (cistern + TP
                                                          # holder + brush bundled in the mesh).
LADDER = "hssd/f63203ce3955e3df53c4e59d9e73f9fff3a6c351"  # bathroom_v1's audited pin: a ladder
                                                          # that actually CARRIES a towel — bare
                                                          # picks read as a stepladder.

scene.prefetch_assets([
    "a black single sink bathroom vanity with mirror",
    "a modern white toilet",
    "a wooden towel ladder with a white towel",
    "a small potted plant in a ceramic pot",
    "a small framed abstract art print",
    "a small round flush mount ceiling light",
])


def _fit_width(o, target_w):
    """Bathroom fixtures carry BROKEN scale metadata — enforce real size by scaling UNIFORMLY
    from the width, so the mesh keeps its own proportions (never per-axis: it distorts bowls)."""
    w0, h0, d0 = o.get_width(), o.get_height(), o.get_depth()
    f = target_w / max(w0, 1e-6)
    o.scale_only_width(w0 * f); o.scale_only_height(h0 * f); o.scale_only_depth(d0 * f)
    return o


# ---- PHASE 1 fixtures, at real-world size -------------------------------------------------------
# the vanity's width + mount come free from the tagger metadata — just AddAsset and place it
vanity = scene.AddAsset("a black single sink bathroom vanity with mirror", asset_id=VANITY)

# toilet sets bundle peripherals into one bbox so the seat reads small — scale up uniformly to
# ~0.9 m overall (the bathroom_v1 calibration).
toilet = _fit_width(scene.AddAsset("a modern white toilet", asset_id=TOILET), 0.90)

ladder = scene.AddAsset("a wooden towel ladder with a white towel", asset_id=LADDER)
# uniform height-fit to ~1.6 m: hand-towel scale for a powder room (metadata width is a guess)
ladder.scale(ladder.get_width() * 1.6 / max(ladder.get_height(), 1e-6))

plant = scene.AddAsset("a small potted plant in a ceramic pot")

# modulate_scale=0.6 — the tight jewel-box footprint IS the brief; see module docstring.
with scene.RoomGroup(modulate_scale=0.6, randomness=0.1) as room:
    # the palette gotcha (bathroom.md): an all-white powder room under the fixed light budget
    # blows out to pure white. A SATURATED MID-TONE wall holds the tonal range — deep teal,
    # worded caption-style so the texture matcher lands on a true saturated swatch
    # (office_modern's "solid ... smooth uniform wall" phrasing).
    room.place_walls(floor_texture="honed grey marble tiles",
                     ceiling_texture="soft white",
                     wall_texture="solid deep teal smooth uniform wall")

    # --- PHASE 1: ALL the floor mass (four objects — slot economy keeps the shell tiny) ---
    room.place_on_back_wall_center(vanity)          # mirror faces the door
    room.place_on_left_wall_center(toilet)          # low fixture — camera-safe at the centre
    room.place_on_back_right_corner(ladder)         # tall piece -> CORNER, off the camera centres
    room.place_on_front_right_corner(plant)
    # door in PHASE 1: its clearance shapes the (tiny) floor solve. NO window — interior room.
    room.place_door("front_wall", position="left")

    # PHASE 2: deliberately EMPTY. The vanity is a SET with a complex top (place_on_top decor
    # sits unreliably — bathroom.md), and the toilet set already bundles its accessories.

    if PHASE >= 3:
        # ONE small print on the right wall — the left wall centre belongs to the toilet and the
        # back wall to the vanity's own mirror. Pre-shrunk before place_on_wall_* (mount height
        # derives from the UN-scaled height).
        print_art = scene.AddAsset("a small framed abstract art print")
        print_art.scale_only_width(0.5); print_art.scale_only_height(0.6); print_art.scale_only_depth(0.03)
        room.place_on_wall_right_center(print_art)
        # ONE small flush fixture: density 0.01 for the smallest floor area in the batch
        room.add_lighting("a small round flush mount ceiling light", density=0.01)

scene.export("ba_powder_compact.blend")
