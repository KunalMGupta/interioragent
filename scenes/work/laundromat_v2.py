"""Laundromat v2 — the v1 aesthetic at real coin-op scale (user: "needs a lot
more machines; I like the aesthetic appeal").

Same bright-calm envelope as v1 (white machines on pale grey walls, warm wood
folding top, wicker/greenery textures, framed ocean art, grey concrete floor) —
but the machine count goes 4 -> 9 and the machines take TWO walls:

- BACK (service) wall: the WASHER BANK — 5 front-loaders in one GridGroup row,
  the slim rolling cart parked at the counter end. Ocean art above the low run.
- RIGHT wall: the DRYER BANK — 4 dryers in a second flush row; washer aisle and
  dryer aisle meet in an open L of circulation (locker_room long-runs lesson:
  rows go flush-on-wall, never place_on_<side>).
- LEFT wall: the FOLDING counter (towels + wicker basket on top) + the triple
  canvas laundry sorter (front slot).
- FRONT wall: the WAITING nook (bench + plant + grey rug) center, door right,
  standard window left, wall clock above the bench (floor vs wall-hung occupy
  independently — console+picture pattern).
- Lighting: flush LED at density 0.02 (more floor area than v1's 0.01 room).

modulate_scale HOLDS at 1.0: v1's 0.75 shrink was for a SPARSE 4-slot room;
this room is wall-loaded on three sides (locker_room lesson: shrinking a packed
room below its furniture footprint forces unsolvable overlaps). Act on the
final-phase RoomProportions vote only if the render agrees.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the
floor layout (~1 min) to verify room size / overlaps before surface dressing
(phase 2) and walls/lighting/mood (phase 3).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("LaundromatV2", seed=42)

WASHER  = "future/460819c5-917f-4c72-9b3d-84de0ca36aa0"   # front-loader, chrome door ring
DRYER   = "hssd/6cd2dc2611c27f758c972b4874efad8c8cbd5d29" # white front-loading dryer
COUNTER = "hssd/67b505c2cfc433bc4ffe39250cafda3951d91939" # white counter table, warm wood top
BENCH   = "hssd/a5faa788a66067bdb536364b705735ba7c5547af" # white upholstered bench, wood legs (rests flat)
CART    = "hssd/491b7091a828edecf83eaa865059e3a680d0d728" # white 3-tier rolling cart
SORTER  = "hssd/aeae32d8bdeefca3ed46e3f0e6b69106e226fe22" # triple canvas laundry sorter
BASKET  = "future/c96d2ee0-8593-42b8-bcc3-bd9e4476b49d"   # wicker laundry basket, fabric liner
TOWELS  = "hssd/6ece1a15f0f508aab2371808d58eefa8420cf725" # stack of rolled white towels

scene.prefetch_assets([
    "a white front-loading washing machine",
    "a white front-loading clothes dryer",
    "a white counter table with a warm wood top",
    "a white upholstered waiting bench with wooden legs",
    "a slim white three-tier rolling storage cart",
    "a triple canvas laundry sorter with a metal frame",
    "a woven wicker laundry basket with a fabric liner",
    "a stack of rolled white towels",
    "a leafy potted plant in a woven basket planter",
    "a framed ocean seascape wall art print",
    "a large round wall clock",
    "a plain dark grey flatweave runner rug",
    "a flat round LED flush mount ceiling light",
])

# --- BACK wall: the WASHER BANK (5 washers, cart parked at the counter end) ------
washers = 5 * scene.AddAsset("a white front-loading washing machine", asset_id=WASHER)
cart    = scene.AddAsset("a slim white three-tier rolling storage cart",
                         asset_id=CART, modulate_scale=0.6)
with scene.GridGroup(sparsity=0.04) as washer_bank:
    washer_bank.place_row([cart] + washers)

# --- RIGHT wall: the DRYER BANK (4 dryers, second flush row) ---------------------
dryers = 4 * scene.AddAsset("a white front-loading clothes dryer", asset_id=DRYER)
with scene.GridGroup(sparsity=0.04) as dryer_bank:
    dryer_bank.place_row(dryers)

# --- LEFT wall: the folding counter (towels + basket dress the wood top) ---------
counter = scene.AddAsset("a white counter table with a warm wood top",
                         asset_id=COUNTER, width=1.8)
with scene.RelativeGroup() as folding:
    folding.set_anchor(counter)
    if PHASE >= 2:
        folding.place_on_top([
            scene.AddAsset("a stack of rolled white towels", asset_id=TOWELS,
                           modulate_scale=0.7),
            scene.AddAsset("a woven wicker laundry basket with a fabric liner",
                           asset_id=BASKET),
        ])

# --- FRONT wall: the waiting nook (bench + plant travel as one unit) -------------
with scene.RelativeGroup() as waiting:
    bench = scene.AddAsset("a white upholstered waiting bench with wooden legs",
                           asset_id=BENCH, width=1.6)
    waiting.set_anchor(bench)
    if PHASE >= 3:
        waiting.place_on_left(scene.AddAsset("a leafy potted plant in a woven basket planter"))
    if PHASE >= 2:
        waiting.place_rug("a plain dark grey flatweave runner rug", size=1.1)

# --- the room ---------------------------------------------------------------------
# 0.9 = final-phase mild shrink on the RoomProportions vote (0.7 Ph1 -> 0.82
# full at 1.0). Three walls are loaded, so no deeper than 0.9 (locker_room
# lesson: 0.8 on a packed room forced unsolvable overlaps).
with scene.RoomGroup(modulate_scale=0.9, randomness=0.1) as room:
    room.place_walls(floor_texture="smooth polished light grey concrete floor",
                     ceiling_texture="white",
                     wall_texture="pale grey")
    # facing omitted on wall placements: the default heuristic already faces the room
    room.place_on_back_wall_center(washer_bank)
    room.place_on_right_wall_center(dryer_bank)
    room.place_on_left_wall_center(folding)
    room.place_on_left_wall_left(scene.AddAsset("a triple canvas laundry sorter with a metal frame",
                                                asset_id=SORTER))
    room.place_on_front_wall_center(waiting)
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")
    if PHASE >= 3:
        room.place_on_wall_back_center(
            scene.AddAsset("a framed ocean seascape wall art print"))
        room.place_on_wall_front_center(
            scene.AddAsset("a large round wall clock"))
        room.place_window_standard("front_wall", position="left",
                                   curtain="light grey sheer curtains")
        # 0.01: 0.02 tiled 14 fixtures onto this ~39 m^2 room (starfield lint)
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("laundromat_v2.blend")
