"""Garage — "Garage Workshop Grid: Car-Ready Multi-Tool Space" (planner target, tmp/garage/plan).

Planner target: a bright, organized home-workshop garage centred on the car — white matte
cabinetry, polished light-grey epoxy concrete floor, a wood-topped workbench, a dark-steel tool
chest, a pegboard tool "spine", tall white storage + open shelving, a rubber work mat, LED shop
lighting, and a side window for daylight.

Built the way the other examples compose scenes: cohesive relative CLUSTERS (a work-zone station,
corner piles) placed as units, not props scattered across wall slots.

Layout — a garage is DEEP, and the car bay sets the long axis:
- CENTRE      : the CAR bay (hero), nose toward the front (garage-door) wall. It is the reason the
                room exists, so it takes the floor centre and everything else works around it.
- RIGHT wall  : the WORK-ZONE cluster — wood-top workbench (anchor) + tool chest beside it + a shop
                stool in front, on a rubber mat. One RelativeGroup, one placement: a wall-flush
                cluster is what lets the pegboard land directly ABOVE the bench.
- LEFT wall   : the STORAGE run — two tall white cabinets + an open steel shelving unit. A long wall
                has exactly three slots (left/center/right) and the run fills all three.
- CORNERS     : a StackGroup tyre stack (front-right) + a PileGroup of boxes on a pallet
                (back-right) — garage character that stays out of the central circulation lane.
- FRONT wall  : the roll-up SHUTTER, the vehicle door the car noses toward.
- BACK wall   : the man-door (a side entry) + a daylight window + a wall clock. The man-door goes on
                a DIFFERENT wall from the shutter — two doors on one wall makes no sense.

Identity comes from the car being at REAL scale (an uncurated "car" query renders a toy) and from the
three zones reading as composed stations rather than loose props. The open floor in front of the car
is correct: it is the vehicle-door approach lane, not a hole in the layout.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/garage_v1.py --phase 1` builds only the
floor layout — car, work zone, storage run, the shell, the shutter and the man-door (~1-2 min); phase
2 adds the cluster detail (work mat, tyre stack, box pile); phase 3 adds the pegboard, the window,
the clock and the LED shop lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("GarageWorkshop", seed=9)

# --- pinned assets (audited previews; see scenes/work/garage_workshop.md) ---
CAR       = "hssd/5f4a14a4e5bc2feb7388b5d18d63350c38600f29"  # clean modern SUV (real car, not a toy):
                                                             # cars are an uncurated gap category and
                                                             # ~half the "car" hits are TOY cars
WORKBENCH = "hssd/107036734c8e21c8a103f7459cd72c9c486068aa"  # industrial wood-top work table
TOOLCHEST = "hssd/67bc354a50314d0a8e1ccc4ec9afad60bc0790ed"  # wide black steel drawer chest
CABINET   = "future/07cce174-309e-4e41-ba40-e9abd17f637c"    # tall white 2-door storage cabinet
SHELVING  = "hssd/9f0427019d5a329e5410547e4291b2c4b8b20195"  # heavy-duty open steel shelving unit
PEGBOARD  = "hssd/3ec1423e301fa0a5df85fda5875b15dd944d54b4"  # tool panel LOADED with hand tools — the
                                                             # tool display, so the bench stays clean
SHUTTER   = "custom/77209bcbf628ab88f537f7b1983e42ba1cde49fb"  # grey corrugated roll-up shutter (vehicle door)

# --- CAR: the hero. Pin a real width so an uncurated "car" query isn't scaled like a toy ---
car = scene.AddAsset("a modern silver SUV car", asset_id=CAR, width=1.85)

# --- WORK-ZONE cluster: bench (anchor) + tool chest beside it + a shop stool in front, on a mat.
#     Composed relative to the bench and placed as ONE unit (living-room U-cluster idiom). ---
with scene.RelativeGroup() as work_zone:
    workbench = scene.AddAsset("an industrial wooden-top workbench", asset_id=WORKBENCH, modulate_scale=0.8)
    work_zone.set_anchor(workbench)
    work_zone.place_on_right(scene.AddAsset("a wide black steel rolling tool chest", asset_id=TOOLCHEST))
    work_zone.place_on_front_further(scene.AddAsset("a round metal shop workshop stool"))
    if PHASE >= 2:
        work_zone.place_rug("a black rubber garage floor work mat", size=0.7)

# --- STORAGE run: two tall white cabinets + an open shelving unit (built once, placed as a row) ---
cabinets = 2 * scene.AddAsset("a tall white metal storage cabinet", asset_id=CABINET)
shelving = scene.AddAsset("a heavy-duty open steel garage shelving unit", asset_id=SHELVING)

with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:
    room.place_walls(floor_texture="polished light grey epoxy concrete",
                     ceiling_texture="white drywall", wall_texture="white painted drywall")

    # centre bay: the car, nose toward the front (garage-door) wall
    room.place_on_center(car, facing="front")

    # right (long) wall = the work-zone cluster flush against the wall (pegboard mounts above it)
    room.place_on_right_wall_center(work_zone)

    # left (long) wall = the storage run: cabinets then the shelving unit
    room.place_on_left_wall_left(cabinets[0])
    room.place_on_left_wall_center(cabinets[1])
    room.place_on_left_wall_right(shelving)

    # front (short) wall = the roll-up shutter: the vehicle door the car noses toward.
    # place_on_FRONT_WALL (floor-against-wall) stands it on the floor at full height — NOT
    # place_on_wall_front (hung art, which caps it small and floats it at mid-wall height).
    # width=2.174 -> 3.0 m tall (portrait mesh, aspect 1.38): floor-to-ceiling garage door.
    # UNGATED with the door: it is a floor-occupying opening, so it belongs to the layout solve.
    room.place_on_front_wall_center(scene.AddAsset("a corrugated metal roll-up garage shutter door",
                                                   asset_id=SHUTTER, width=2.174))

    # the man-door on the BACK wall (a side entry — a different wall from the shutter).
    # UNGATED: its automatic clearance shapes the floor solve, so it must exist in phase 1.
    room.place_door("back_wall", position="left")

    if PHASE >= 2:
        # corner clusters: a StackGroup tyre stack + a PileGroup of boxes on a pallet.
        # Tyres by the front-right, the box pile in the back-right (clear of the back-wall door).
        with scene.StackGroup() as tyre_stack:
            tyre_stack.place_stack(3 * scene.AddAsset("a black rubber car tyre"))
        room.place_on_front_right_corner(tyre_stack)

        with scene.PileGroup() as box_pile:
            box_pile.set_anchor(scene.AddAsset("a wooden shipping pallet"))
            box_pile.place_pile(4 * scene.AddAsset("a cardboard storage box"), spread=0.6)
        room.place_on_back_right_corner(box_pile)

    if PHASE >= 3:
        # walls & decor: the pegboard is the tool SPINE — it lands directly above the wall-flush bench
        room.place_on_wall_right_center(scene.AddAsset("a pegboard tool panel full of hand tools",
                                                       asset_id=PEGBOARD))
        room.place_window_standard("back_wall", position="center", curtain=None)
        room.place_on_wall_back_right(scene.AddAsset("a round industrial wall clock"))

        # lighting: bright LED shop ceiling
        room.add_lighting("a row of bright LED linear ceiling shop lights", density=0.03)

scene.export("garage_v1.blend")
