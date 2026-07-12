"""
Garage — "Garage Workshop Grid: Car-Ready Multi-Tool Space" (planner target, tmp/garage/plan).

A bright, organized home-workshop garage centred on the car, built the way the other examples
compose scenes: cohesive relative CLUSTERS (a work-zone station, corner piles) placed as units,
not props scattered across wall slots.

Look: white matte cabinetry, polished light-grey epoxy concrete floor, a wood-topped workbench,
a dark-steel tool chest, a pegboard tool "spine", tall white storage + open shelving, a rubber
work mat, LED shop lighting, and a side window for daylight.

Zones (a garage is DEEP — the car bay sets the long axis):
  - centre            = the CAR bay (hero), nose toward the front (garage-door) wall.
  - right (long) wall = the WORK-ZONE cluster: wood-top workbench + tool chest + a shop stool on a
    rubber mat, with the loaded pegboard mounted on the wall right above the bench.
  - left  (long) wall = the STORAGE run: two tall white cabinets + an open steel shelving unit.
  - corners           = a StackGroup tyre stack + a PileGroup of boxes on a pallet.
  - front (short) wall = the roll-up SHUTTER (the vehicle door the car noses toward).
  - back  (short) wall = the man-door (a side entry) + a daylight window + a wall clock.
    (The man-door goes on a DIFFERENT wall from the shutter — two doors on one wall makes no sense.)

Phase 1: car + work-zone cluster + storage run           (floor anchors, layout & proportions).
Phase 2: rubber work mat + tyre stack + box pile + lights (cluster details).
Phase 3: pegboard + window + door + clock                 (walls & decor).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("GarageWorkshop", seed=9)

# --- pinned assets (audited previews; see scenes/work/garage_workshop.md) ---
_CAR       = "hssd/5f4a14a4e5bc2feb7388b5d18d63350c38600f29"  # clean modern SUV (real car, not a toy)
_WORKBENCH = "hssd/107036734c8e21c8a103f7459cd72c9c486068aa"  # industrial wood-top work table
_TOOLCHEST = "hssd/67bc354a50314d0a8e1ccc4ec9afad60bc0790ed"  # wide black steel drawer chest
_CABINET   = "future/07cce174-309e-4e41-ba40-e9abd17f637c"    # tall white 2-door storage cabinet
_SHELVING  = "hssd/9f0427019d5a329e5410547e4291b2c4b8b20195"  # heavy-duty open steel shelving unit
_PEGBOARD  = "hssd/3ec1423e301fa0a5df85fda5875b15dd944d54b4"  # tool panel loaded with hand tools
_SHUTTER   = "custom/77209bcbf628ab88f537f7b1983e42ba1cde49fb"  # grey corrugated roll-up shutter (vehicle door)

# --- CAR: the hero. Pin a real width so an uncurated "car" query isn't scaled like a toy ---
car = scene.AddAsset("a modern silver SUV car", asset_id=_CAR, width=1.85)

# --- WORK-ZONE cluster: bench (anchor) + tool chest beside it + a shop stool in front, on a mat.
#     Composed relative to the bench and placed as ONE unit (living-room U-cluster idiom). ---
with scene.RelativeGroup() as work_zone:
    workbench = scene.AddAsset("an industrial wooden-top workbench", asset_id=_WORKBENCH, modulate_scale=0.8)
    work_zone.set_anchor(workbench)
    work_zone.place_on_right(scene.AddAsset("a wide black steel rolling tool chest", asset_id=_TOOLCHEST))
    work_zone.place_on_front_further(scene.AddAsset("a round metal shop workshop stool"))
    work_zone.place_rug("a black rubber garage floor work mat", size=0.7)

# --- STORAGE run: two tall white cabinets + an open shelving unit (built once, placed as a row) ---
cabinets = 2 * scene.AddAsset("a tall white metal storage cabinet", asset_id=_CABINET)
shelving = scene.AddAsset("a heavy-duty open steel garage shelving unit", asset_id=_SHELVING)

# --- corner clusters: a StackGroup tyre stack + a PileGroup of boxes on a pallet ---
with scene.StackGroup() as tyre_stack:
    tyre_stack.place_stack(3 * scene.AddAsset("a black rubber car tyre"))

with scene.PileGroup() as box_pile:
    box_pile.set_anchor(scene.AddAsset("a wooden shipping pallet"))
    box_pile.place_pile(4 * scene.AddAsset("a cardboard storage box"), spread=0.6)

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

    # corners: tyres by the front-right, the box pile in the back-right (clear of the back-wall door)
    room.place_on_front_right_corner(tyre_stack)
    room.place_on_back_right_corner(box_pile)

    # front (short) wall = the roll-up shutter: the vehicle door the car noses toward.
    # place_on_FRONT_WALL (floor-against-wall) stands it on the floor at full height — NOT
    # place_on_wall_front (hung art, which caps it small and floats it at mid-wall height).
    # width=2.174 -> 3.0 m tall (portrait mesh, aspect 1.38): floor-to-ceiling garage door.
    room.place_on_front_wall_center(scene.AddAsset("a corrugated metal roll-up garage shutter door",
                                                   asset_id=_SHUTTER, width=2.174))

    # walls & decor
    room.place_on_wall_right_center(scene.AddAsset("a pegboard tool panel full of hand tools", asset_id=_PEGBOARD))
    room.place_window_standard("back_wall", position="center", curtain=None)
    room.place_on_wall_back_right(scene.AddAsset("a round industrial wall clock"))
    # the man-door on the BACK wall (a side entry — a different wall from the shutter)
    room.place_door("back_wall", position="left")

    # lighting: bright LED shop ceiling
    room.add_lighting("a row of bright LED linear ceiling shop lights", density=0.03)

scene.export("garage_workshop.blend")
