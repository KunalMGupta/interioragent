"""Lobby — "Polished Corporate Lobby: Reception Anchor + Open Lounge" (planner-driven; v2 layout).

Planner target: a polished corporate reception — a marble+wood reception desk anchoring the service
end, an open waiting lounge of sofas and armchairs around a coffee table, tall greenery, big
colourful art, floor-to-ceiling glazing, a wall TV, warm flush disc lighting. Palette: polished
stone + warm wood + greige; clear sightlines, no bottlenecks.

Layout — RECEPTION ANCHOR + a WAITING LOUNGE pushed OFF-CENTRE:
- BACK third : the reception HERO — a WorkstationGroup whose desk is INVERTED (set_rotation(180)):
               marble transaction front -> customers, staff + monitor behind. Dropped with
               place_on_back(facing="back"), NOT place_on_back_wall — a wall-flush desk leaves the
               receptionist standing inside the wall.
- BACK wall  : the colourful focal artwork behind reception (the "focal wall" the branded-logo gap
               could not fill); the lamp-lit console vignette in the left corner, a tall plant right.
- LEFT wall  : floor-to-ceiling glazing — the only wall with NO furniture, so it stays the light wall.
- RIGHT wall : greenery beside the lounge + a secondary B&W print. The quiet wall.
- FRONT wall : the entrance. Door LEFT (moved off-centre to clear the TV), the wall-mounted TV
               centre (something to watch from the lounge), the water cooler in the left corner.
- FRONT-RIGHT: the waiting lounge — an AroundGroup.place_rectilinear cluster (2 sofas on the long
               sides + 2 armchairs on the short sides, auto-faced inward). It is pushed to the
               front-right ON PURPOSE: dead-centre (v1) it walled the desk off behind the seating,
               and you had to weave through the sofas to reach reception.
- CENTRE     : deliberately OPEN. It is not empty floor, it is the diagonal WALK-UP LANE from the
               entrance to the desk — circulation an occupancy metric always misreads as "empty".

Identity comes from the reception desk being an INVERTED workstation (nice front to the customer,
screen to the staff) and from the symmetric rectilinear seating cluster reading as a waiting lounge
rather than a living room. modulate_scale=0.9 keeps it corporate-tight while preserving the walk-up.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/lobby_v1.py --phase 1` builds only the
floor layout (~1-2 min); phase 2 dresses the surfaces and the floor; phase 3 adds the wall decor,
glazing and lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Lobby", seed=13)

# ---- pinned assets (from the retrieval stress test; every mesh eyeballed on a contact sheet) ----
DESK    = "custom/cffdedd8d354e346e510f227b4a6bc5b65dc3dcb"  # INGESTED wood+marble reception desk
                                                             # (hero). The pool had ONE reception desk
                                                             # (wooden, sim 0.69) and no marble at all.
SOFA    = "hssd/05206ad5b8ad9956a076ab73038089b964ddb2fd"    # straight beige 3-seat sofa (0.82) —
                                                             # pinned to dodge the SECTIONALS the
                                                             # generic "sofa" query keeps returning
ARMCHAIR= "future/1c8dfc96-1144-4be8-8894-e064d672a86c"      # grey bouclé tub accent chair
COFFEE  = "future/40860cf0-4d90-409e-92dc-14e57ee94d70"      # minimalist wood coffee table
SIDET   = "future/76d7a78e-2b24-45a3-aac6-f6ab2d7bcd57"      # round wood/metal side table (0.76)
PLANT   = "hssd/08d9ae37bc8bc5e0dc07942d0c3ceaa0ea076f0c"    # tall potted plant (0.83)
VASE    = "future/c6da6c9b-9b15-4c3e-a93b-2ae2f7266a01"      # white ceramic vase w/ branches
RUG     = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"    # FLAT beige wool rug — pinned flat to
                                                             # avoid the upright-slab place_rug warning
FOCAL   = "hssd/5e9d4d4d61e99ba9604ea74dbab640f487771502"    # colourful abstract art (focal wall)
ART     = "hssd/2b54eedde60d311599e833173ef0757ea4931ef9"    # B&W abstract art (right wall)
TV      = "future/ad98c113-55bd-403b-b2ad-7df2191e6567"      # large wall-mounted flat-screen TV (0.67)
WATER   = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"    # bottled office water cooler — auto-scale
                                                             # metadata is BAD, so pin width= explicitly
LAMP    = "hssd/487fc51880a2b94f0e9b7a031a5f4998c60b0583"    # modern black cylindrical table lamp
BOOKS   = "hssd/d0e0f0b5305ab8742ec51197e1dac1b4d208e5df"    # stack of decorative books

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
# The desktop items are the PHASE-2 layer, and the gate sits INSIDE the `with` block — gated outside
# it the ops would never be recorded and the computer would simply be GONE.
with scene.WorkstationGroup() as reception:
    desk = scene.AddAsset("a modern reception desk with a marble front", asset_id=DESK, width=2.2)
    desk.set_rotation(180)
    reception.set_anchor(desk)
    reception.place_chair(scene.AddAsset("a black leather office task chair on casters"), gap=True)
    if PHASE >= 2:
        reception.place_computer(scene.AddAsset("a desktop computer"))   # screen auto-faces the chair
        reception.place_accessories([scene.AddAsset("a small potted plant")])

# --- waiting lounge: symmetric sofas + armchairs around a coffee table (vase + books on top) ---
# place_rectilinear IS the waiting cluster: 2 sofas + 2 armchairs auto-faced inward in ONE call, no
# per-seat face(). The cluster (phase 1) is the layout; the vase/books/rug (phase 2) only dress it.
with scene.AroundGroup(sparsity=0.4, jitter=0.3) as lounge:
    coffee = scene.AddAsset("a low minimalist wood coffee table", asset_id=COFFEE, width=0.95)  # VLM: coffee ×0.8
    lounge.set_anchor(coffee)
    lounge.place_rectilinear(
        longer_side1=[scene.AddAsset("a straight modern beige three-seat sofa", asset_id=SOFA)],
        longer_side2=[scene.AddAsset("a straight modern beige three-seat sofa", asset_id=SOFA)],
        shorter_side1=[scene.AddAsset("a modern accent lounge armchair", asset_id=ARMCHAIR)],
        shorter_side2=[scene.AddAsset("a modern accent lounge armchair", asset_id=ARMCHAIR)])
    if PHASE >= 2:
        lounge.place_on_top([scene.AddAsset("an elegant white ceramic vase with branches", asset_id=VASE),
                             scene.AddAsset("a stack of decorative books", asset_id=BOOKS)])
        lounge.place_rug("a flat beige wool area rug", size=0.95, asset_id=RUG)

# --- console vignette: a purposeful lamp-lit accent table (side table + lamp + books) ---
# The anchor IS the side table, so place_on_top seats the lamp on the TABLE. An accent table with
# nothing on it reads as a mistake; the lamp + books give it a job.
with scene.RelativeGroup() as console:
    side = scene.AddAsset("a round wood and metal accent side table", asset_id=SIDET)
    console.set_anchor(side)
    if PHASE >= 2:
        console.place_on_top([scene.AddAsset("a modern table lamp", asset_id=LAMP),
                              scene.AddAsset("a stack of decorative books", asset_id=BOOKS)])

# --- room: zone reception (back) + lounge (front-right), amenities, walls, decor, light ---
with scene.RoomGroup(modulate_scale=0.9, randomness=0.12) as room:   # 0.9 = acted on VLM "rescale room by 0.8" (kept some openness for circulation)
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white ceiling",
                     wall_texture="warm greige painted wall")
    room.place_on_back(reception, facing="back")       # operator (+Z) to the back wall -> receptionist faces the room; WorkstationGroup turns the screen to the operator
    room.place_on_front_right(lounge, facing="front")  # lounge to the front-right -> clear walk-up to the desk
    room.place_on_back_left_corner(console)            # lamp-lit console vignette (purposeful accent table)
    # door in PHASE 1: its auto clearance shapes the floor solve, so deferring it would change the
    # layout you validated. Entrance moved LEFT to clear the front-centre TV.
    room.place_door("front_wall", position="left")

    if PHASE >= 2:
        # floor dressing: greenery + the entrance amenity
        room.place_on_back_right_corner(scene.AddAsset("a tall potted indoor plant in a planter", asset_id=PLANT))
        room.place_on_right(scene.AddAsset("a tall potted indoor plant in a planter", asset_id=PLANT))    # greenery by the lounge
        room.place_on_front_left_corner(scene.AddAsset("a tall office water cooler dispenser", asset_id=WATER, width=0.35))  # amenity by the entrance

    if PHASE >= 3:
        # focal + secondary art (pre-scaled via width= so the mount height doesn't clip the ceiling)
        room.place_on_wall_back_center(scene.AddAsset("a large vibrant colourful abstract framed wall art", asset_id=FOCAL, width=1.8))
        room.place_on_wall_right_center(scene.AddAsset("a large framed abstract wall art print", asset_id=ART, width=1.2))
        room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted flat screen television", asset_id=TV, width=1.7))  # something to watch from the lounge
        room.place_window_floor_to_ceiling("left_wall", curtain=None)   # bare glazing: curtain meshes render as ghost drapes over the night void
        # fixture COUNT is N = 1 + (max_lights-1)*density, max_lights ~= ceiling_area/fixture_footprint.
        # A small disc at density=0.2 exploded to ~250 dots: ENLARGE the fixture (modulate_scale=2.2
        # shrinks max_lights) AND drop density (0.03) -> a clean ~9-fixture grid.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.03, modulate_scale=2.2)

scene.export("lobby_v1.blend")
