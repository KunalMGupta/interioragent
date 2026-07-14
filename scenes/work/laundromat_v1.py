"""Small laundromat — "Efficient Compact Laundromat Block" (planner target,
tmp/laundromat/plan/plan.png).

A compact coin-op laundry: bright and calm — white machines and cabinetry against
pale grey walls, a warm wood folding surface, natural textures (wicker basket,
plant), a framed ocean artwork as the focal point, durable grey concrete floor.

Layout (slot economy for a small brief — few floor slots, modest hero widths):
- BACK (service) wall: the MACHINE RUN — 2 washers + a slim white rolling cart
  parked between + 2 dryers, one GridGroup row flush on the wall (the hero;
  the plan's "slim rolling cart fits between machines"). Framed ocean art
  hung above the low run (low support -> clears the ceiling).
- LEFT wall: the FOLDING counter (white base, warm wood top) with stacked
  towels + a wicker laundry basket on top; a triple canvas laundry sorter in
  the left wall's front slot (laundromat identity prop).
- RIGHT wall: the WAITING nook — upholstered bench + plant, grey rug in front.
- FRONT wall: door (right), standard window (left; small pane — the void
  lesson), round wall clock (center).
- Lighting: a flat flush LED fixture, density 0.01 (SMALL-room lesson: 0.05
  is already a starfield).

Appliance fronts get their functional clearance automatically
(CategoryClearanceConstraint) — that keeps the loading aisle open.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the
floor layout (~1 min) to verify room size / overlaps before surface dressing
(phase 2) and walls/lighting/mood (phase 3).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("SmallLaundromat", seed=42)

WASHER  = "future/460819c5-917f-4c72-9b3d-84de0ca36aa0"   # white front-loader, chrome door ring
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

# --- BACK wall: the machine run (2 washers + rolling cart between + 2 dryers) ---
washers = 2 * scene.AddAsset("a white front-loading washing machine", asset_id=WASHER)
dryers  = 2 * scene.AddAsset("a white front-loading clothes dryer", asset_id=DRYER)
cart    = scene.AddAsset("a slim white three-tier rolling storage cart",
                         asset_id=CART, modulate_scale=0.6)
with scene.GridGroup(sparsity=0.04) as machine_row:
    machine_row.place_row(washers + [cart] + dryers)

# --- LEFT wall: the folding counter (towels + basket dress the wood top) --------
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

# --- RIGHT wall: the waiting nook (bench + plant travel as one unit) ------------
with scene.RelativeGroup() as waiting:
    bench = scene.AddAsset("a white upholstered waiting bench with wooden legs",
                           asset_id=BENCH, width=1.6)
    waiting.set_anchor(bench)
    if PHASE >= 3:
        waiting.place_on_left(scene.AddAsset("a leafy potted plant in a woven basket planter"))
    if PHASE >= 2:
        waiting.place_rug("a plain dark grey flatweave runner rug", size=1.1)

# --- the room --------------------------------------------------------------------
# 0.75 = final-phase shrink acting on the persistent RoomProportions vote
# (0.7 Ph1 -> 0.8 Ph2 -> 0.75 at 0.85); the room is sparse (empty center
# aisle), so a sub-1.0 shrink is safe here. Revert toward 0.85 if the solver
# reports residual overlaps (room-too-small warning).
with scene.RoomGroup(modulate_scale=0.75, randomness=0.1) as room:
    room.place_walls(floor_texture="smooth polished light grey concrete floor",
                     ceiling_texture="white",
                     wall_texture="pale grey")
    # facing omitted on wall placements: the default heuristic already faces the room
    room.place_on_back_wall_center(machine_row)
    room.place_on_left_wall_center(folding)
    room.place_on_left_wall_left(scene.AddAsset("a triple canvas laundry sorter with a metal frame",
                                                asset_id=SORTER))
    room.place_on_right_wall_center(waiting)
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")
    if PHASE >= 3:
        room.place_on_wall_back_center(
            scene.AddAsset("a framed ocean seascape wall art print"))
        room.place_on_wall_front_center(
            scene.AddAsset("a large round wall clock"))
        room.place_window_standard("front_wall", position="left",
                                   curtain="light grey sheer curtains")
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("laundromat_v1.blend")
