"""
Prison cell — "Containment Core: Bunk-Anchored Single-Occupancy Cell" (planner-driven).

Design brief (planner): the cot is the room's anchor with accessible sides for surveillance;
circulation around it stays clear; durable minimal materials (steel frame, cool grey concrete,
sealed floor); a BARRED window replaces any glazed opening; a narrow fixed desk strip; uniform
overhead panel light; austere neutral palette, steel accents, matte textures.

Procedural signature (retriever): tiny sparse single-occupancy room — institutional bed on a long
wall, plumbing fixtures sharing a chase on a perpendicular wall, a small fixed desk + stool, a
solid door, a small barred window; a clear aisle from the door to the window alongside the bed.

Layout (few floor slots so the shell auto-sizes to cell scale; wall load capped per wall — the
hospital_room "don't overload a single wall" rule):
  - LEFT (long wall)  : the steel BUNK hero, its 2.0 m run along the wall  -> 1 item.
  - RIGHT (long wall) : the hygiene corner — toilet + wall-hung basin sharing a plumbing chase -> 2 items.
  - BACK (short wall) : the desk + stool unit, directly under the barred window.
  - FRONT (short wall): the door (auto door-clearance keeps the entry lane open).
  - The room center stays EMPTY: that aisle from door to window is the category, not dead space
    (the garage/corridor "an open circulation lane reads as too big to the VLM" lesson — expect a
    persistent shrink vote and judge it by render).

Asset audit (gate 3): the dataset has NO stainless prison toilet/sink combo unit (it is
home-furniture biased, exactly as the catalog warns for institutional fixtures) — substituted a
plain white close-coupled toilet + a wall-hung basin with an exposed trap, placed adjacent to read
as one plumbing wall. Every pin below was eyeballed AND size-checked offline with get_whd()
(the half-scale-hero lesson): all six load at true real-world scale, so NO modulate_scale fixes.

The BARS are the identity prop (jewelry_shop "a scene reads by its product" rule): a black steel
fence panel of 5 vertical bars hung over the window opening. Two deliberate mechanics:
  - `place_on_wall_freeform` (NOT place_on_wall_back_center): freeform mounts at wall-height/2 —
    the same band as the window's 'middle' partition — keeps the panel at its OWN width instead of
    capping it to 0.6*(WIDTH/3) (too narrow to cover the pane), and registers NO wall slot, so the
    bars do not raise a spurious WallOverlap against the window they are meant to sit on.
  - The window is the one opening a cell cannot get wrong: bars read correctly whether the pane
    comes back BRIGHT (as here — the tree's opaque-film renderer change shows the lit world
    background, i.e. hard daylight through bars) or BLACK (the classic void = a night-time cell).

Phase-gated (IDSDL/phases.py): --phase 1 = floor layout only (~1 min).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("PrisonCell", seed=11)

# --- Audited pins (gate 3; native dims verified offline with get_whd()) ---
BUNK   = "hssd/0b750370480e2a26bfedafd6b5298f28d6074e70"  # white metal bunk, ladder + thin mattresses (2.00 x 1.52 x 0.90)
TOILET = "hssd/0c4ab4d4ccdc801b4093f10a9aa9c0bfd08ab584"  # plain white close-coupled toilet       (0.40 x 0.83 x 0.70)
SINK   = "hssd/3f0778f68a489d3995e2e3f13d13e4a90fb500a8"  # wall-hung basin, exposed trap          (0.50 x 0.54 x 0.40)
DESK   = "hssd/709745fbd3cc41050840793cdf67e73995e27270"  # flat-top desk, one drawer pedestal     (1.20 x 0.75 x 0.61)
STOOL  = "hssd/502ce37cd7bad20d9ff7a7fe64914dab16a8d7c6"  # low backless stool                     (0.45 x 0.43 x 0.34)
BARS   = "hssd/1370b0fb20e3fb98e25a86c30291ee80177bb20e"  # steel panel, 5 vertical bars           (1.20 x 1.17 x 0.12)
# (depth 0.12 < WALL_HUNG_MAX_DEPTH 0.25 -> safe to hang; a deeper mesh would float as furniture)

scene.prefetch_assets([
    "a white metal bunk bed with a ladder",
    "a plain white ceramic toilet",
    "a small wall-mounted washbasin",
    "a simple grey writing desk",
    "a low backless stool",
    "a black steel panel of vertical bars",
    "a stack of worn paperback books",
    "a small square wall mirror",
    "a flat rectangular LED flush mount ceiling light",
])

bunk   = scene.AddAsset("a white metal bunk bed with a ladder", asset_id=BUNK)
toilet = scene.AddAsset("a plain white ceramic toilet", asset_id=TOILET)
sink   = scene.AddAsset("a small wall-mounted washbasin", asset_id=SINK)
desk   = scene.AddAsset("a simple grey writing desk", asset_id=DESK)
stool  = scene.AddAsset("a low backless stool", asset_id=STOOL)

# --- The desk unit: stool on the desk's ROOM side, facing the desk (music_studio's
# "explicit face() inside the unit + default facing at the wall" = zero rotation churn).
# The inmate sits with his back to the room, facing the wall desk under the window. ---
with scene.RelativeGroup() as desk_unit:
    desk_unit.set_anchor(desk)
    desk_unit.place_on_front(stool)
    desk_unit.face(stool, toward=desk)
    if PHASE >= 2:
        # Sparse by design — a cell holds almost no personal property. One legible prop.
        # NOTE: this MUST live INSIDE the `with` block. A group compiles on __exit__, so a
        # place_on_top registered after the block never runs (my v1 bug: the books silently
        # never appeared, and nothing in the VLM loop or the lints flagged it — the desk just
        # rendered bare. Same shape as the canonical coffee_shop_v1 gating.)
        desk_unit.place_on_top(scene.AddAsset("a stack of worn paperback books"))

# modulate_scale=0.7 — the shell auto-sized to 4.0 x 5.1 m (20 m2), which is a dormitory, not a
# cell. `rescale room by 0.69` came back UNIDIRECTIONAL and undecayed across phases 1 and 2, so per
# the vote-train rule (living_room_cozy) that is signal, not early-phase noise: one decisive
# application near the vote (bakery: pick AT the vote, not above it) -> ~2.8 x 3.6 m / 10 m2, a
# believable single-occupancy cell. Shrinking below 1.0 is safe HERE (laundromat, not locker_room):
# the room is genuinely sparse — 4 floor slots, and every wall run (bunk 2.0 m along a 3.6 m wall,
# desk 1.2 m along a 2.8 m wall) still fits, so no fixed-size row overflows its slot.
with scene.RoomGroup(modulate_scale=0.7, randomness=0.08) as room:
    # Plain colour + material words only — an accent clause hijacks the whole texture embedding
    # (classroom's teal-accent -> green-tiled-room lesson).
    room.place_walls(floor_texture="smooth grey concrete floor",
                     ceiling_texture="white",
                     wall_texture="plain grey concrete wall")

    # --- Phase 1 — floor anchors (facing omitted everywhere: the wall heuristic already
    # turns each piece INTO the room, which is what makes the bunk/toilet/basin usable) ---
    room.place_on_left_wall_center(bunk)                     # hero run on the long wall
    room.place_on_back_wall_center(desk_unit)                # desk under the window
    room.place_on_right_wall_center(toilet)                  # hygiene corner: toilet + basin
    room.place_on_right_wall_left(sink, bottom=0.40)         # wall-HUNG: basin rim lands ~0.94 m
    room.place_door("front_wall", position="right")          # auto door-clearance holds the lane

    if PHASE >= 3:
        # Openings: a SMALL standard pane (never place_window_picture — a wide opening is a wide
        # black void), no curtain (a cell has none), with the steel bars hung over it.
        room.place_window_standard("back_wall", position="center")
        # Pre-scale the panel to the pane it must cover: freeform keeps a wall object at its OWN
        # width (no 0.6*(WIDTH/3) cap), so 1.2 m native would overhang the ~0.94 m pane onto the
        # concrete either side. 0.95 m wide (aspect preserved -> ~0.93 m tall) lands on the pane,
        # whose 'middle' partition is ~0.9 m tall and centred at the same 1.5 m the freeform
        # mount uses.
        bars = scene.AddAsset("a black steel panel of vertical bars", asset_id=BARS)
        bars.scale(0.95)
        room.place_on_wall_freeform("back_wall", [bars])
        # A small mirror over the basin (same third as the sink; it sits well above the basin rim,
        # so the wall-object clearance pass leaves the basin alone).
        room.place_on_wall_right_left(scene.AddAsset("a small square wall mirror"))
        # FLUSH fixture, low density: a ~10 m2 cell — 0.01 is the small-room band
        # (coffee_shop: 0.05 was a 26-fixture starfield). Uniform, institutional, no warmth.
        room.add_lighting("a flat rectangular LED flush mount ceiling light", density=0.01)

scene.export("prison_cell.blend")
