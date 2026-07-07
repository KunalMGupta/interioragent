"""
Lobby — "Polished Corporate Lobby: Reception Anchor + Open Lounge" (planner-driven; v2 layout).

Layout (revised on user feedback):
  * Reception anchor: ingested wood+marble desk in the back third, staff chair behind, computer +
    plant on top, a tall plant flanking it; colourful focal art on the wall behind.
  * Waiting lounge: symmetric AroundGroup (2 sofas + 2 armchairs around a coffee table) pushed to the
    FRONT-RIGHT so there's clear open circulation straight up to the reception desk (was dead-centre,
    which walled the desk off behind the seating).
  * Amenities/decor: a wall-mounted TV on the front wall (something to watch), an entrance water
    cooler, a lamp-lit console vignette (side table + lamp + books) so the accent table reads with a
    clear purpose, extra greenery, books on the coffee table.
  * Floor-to-ceiling glazing (left wall), entrance door front-left, warm flush disc lighting.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Lobby", seed=13)

# --- pinned assets (from the retrieval stress test) ---
_DESK   = "custom/cffdedd8d354e346e510f227b4a6bc5b65dc3dcb"  # ingested wood+marble reception desk (hero)
_SOFA   = "hssd/05206ad5b8ad9956a076ab73038089b964ddb2fd"    # straight beige 3-seat sofa (0.82)
_ARMCH  = "future/1c8dfc96-1144-4be8-8894-e064d672a86c"      # grey bouclé tub accent chair
_COFFEE = "future/40860cf0-4d90-409e-92dc-14e57ee94d70"      # minimalist wood coffee table
_SIDET  = "future/76d7a78e-2b24-45a3-aac6-f6ab2d7bcd57"      # round wood/metal side table (0.76)
_PLANT  = "hssd/08d9ae37bc8bc5e0dc07942d0c3ceaa0ea076f0c"    # tall potted plant (0.83)
_VASE   = "future/c6da6c9b-9b15-4c3e-a93b-2ae2f7266a01"      # white ceramic vase w/ branches
_RUG    = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"    # flat beige wool rug
_FOCAL  = "hssd/5e9d4d4d61e99ba9604ea74dbab640f487771502"    # colourful abstract art (focal wall)
_ART    = "hssd/2b54eedde60d311599e833173ef0757ea4931ef9"    # B&W abstract art (right wall)
_TV     = "future/ad98c113-55bd-403b-b2ad-7df2191e6567"      # large wall-mounted flat-screen TV (0.67)
_WATER  = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"    # bottled office water cooler (auto-scale bad -> width=)
_LAMP   = "hssd/487fc51880a2b94f0e9b7a031a5f4998c60b0583"    # modern black cylindrical table lamp
_BOOKS  = "hssd/d0e0f0b5305ab8742ec51197e1dac1b4d208e5df"    # stack of decorative books

scene.prefetch_assets([
    "a black leather office task chair on casters",
    "a desktop computer",
    "a small potted plant",
])

# --- reception anchor: a WorkstationGroup (desk + chair + computer + desk plant).
# The group seats the computer with place_on_top and deterministically turns the SCREEN to face the
# operator/chair -- the robust, reusable fix for "monitor on a desk" facing (no per-scene face-hack).
# A reception desk is INVERTED vs a normal desk (nice front -> customers, staff + monitor behind), so
# flip the desk 180 (marble transaction front -> customer side; open staff side -> operator +Z) and
# place the group facing="back" below (operator to the back wall, receptionist facing the room).
with scene.WorkstationGroup() as reception:
    desk = scene.AddAsset("a modern reception desk with a marble front", asset_id=_DESK, width=2.2)
    desk.set_rotation(180)
    reception.set_anchor(desk)
    reception.place_chair(scene.AddAsset("a black leather office task chair on casters"), gap=True)
    reception.place_computer(scene.AddAsset("a desktop computer"))
    reception.place_accessories([scene.AddAsset("a small potted plant")])

# --- waiting lounge: symmetric sofas + armchairs around a coffee table (vase + books on top) ---
with scene.AroundGroup(sparsity=0.4, jitter=0.3) as lounge:
    coffee = scene.AddAsset("a low minimalist wood coffee table", asset_id=_COFFEE, width=0.95)  # VLM: coffee ×0.8
    lounge.set_anchor(coffee)
    lounge.place_rectilinear(
        longer_side1=[scene.AddAsset("a straight modern beige three-seat sofa", asset_id=_SOFA)],
        longer_side2=[scene.AddAsset("a straight modern beige three-seat sofa", asset_id=_SOFA)],
        shorter_side1=[scene.AddAsset("a modern accent lounge armchair", asset_id=_ARMCH)],
        shorter_side2=[scene.AddAsset("a modern accent lounge armchair", asset_id=_ARMCH)])
    lounge.place_on_top([scene.AddAsset("an elegant white ceramic vase with branches", asset_id=_VASE),
                         scene.AddAsset("a stack of decorative books", asset_id=_BOOKS)])
    lounge.place_rug("a flat beige wool area rug", size=0.95, asset_id=_RUG)

# --- console vignette: a purposeful lamp-lit accent table (side table + lamp + books) ---
with scene.RelativeGroup() as console:
    side = scene.AddAsset("a round wood and metal accent side table", asset_id=_SIDET)
    console.set_anchor(side)
    console.place_on_top([scene.AddAsset("a modern table lamp", asset_id=_LAMP),
                          scene.AddAsset("a stack of decorative books", asset_id=_BOOKS)])

# --- room: zone reception (back) + lounge (front-right), amenities, walls, decor, light ---
with scene.RoomGroup(modulate_scale=0.9, randomness=0.12) as room:   # 0.9 = acted on VLM "rescale room by 0.8" (kept some openness for circulation)
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white ceiling",
                     wall_texture="warm greige painted wall")
    room.place_on_back(reception, facing="back")       # operator (+Z) to the back wall -> receptionist faces the room; WorkstationGroup turns the screen to the operator
    room.place_on_front_right(lounge, facing="front")  # lounge to the front-right -> clear walk-up to the desk
    room.place_on_back_left_corner(console)            # lamp-lit console vignette (purposeful accent table)
    room.place_on_back_right_corner(scene.AddAsset("a tall potted indoor plant in a planter", asset_id=_PLANT))
    room.place_on_right(scene.AddAsset("a tall potted indoor plant in a planter", asset_id=_PLANT))    # greenery by the lounge
    room.place_on_front_left_corner(scene.AddAsset("a tall office water cooler dispenser", asset_id=_WATER, width=0.35))  # amenity by the entrance
    # focal + secondary art (pre-scaled via width= so the mount height doesn't clip the ceiling)
    room.place_on_wall_back_center(scene.AddAsset("a large vibrant colourful abstract framed wall art", asset_id=_FOCAL, width=1.8))
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract wall art print", asset_id=_ART, width=1.2))
    room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted flat screen television", asset_id=_TV, width=1.7))  # something to watch from the lounge
    room.place_window_floor_to_ceiling("left_wall", curtain=None)   # bare glazing: curtain meshes render as ghost drapes over the night void
    room.place_door("front_wall", position="left")     # entrance moved left to clear the front-centre TV
    room.add_lighting("a flat round LED flush mount ceiling light", density=0.03, modulate_scale=2.2)

scene.export("lobby.blend")
