"""Meeting / conference room — "Integrated Executive Boardroom" (planner headline).

Planner target: a long central table is the activity hub, ringed with office chairs; the
presentation wall (a large monitor + a whiteboard over a slim AV credenza) is the visual anchor;
a coffee & water station with a speakerphone within reach; a glass perimeter with blinds for
daylight; a recessed / linear ceiling light. Palette: white seating, charcoal surfaces, warm wood,
brushed metal. Built asset-first (retrieval stress test: 39/40 resolved, none < 0.30 — low-risk,
NO ingest) then coarse-to-fine.

Layout — the dining/conference cluster REFOCUSED on a presentation wall. Every wall has a job,
which is what keeps a boardroom from reading as "a table in an empty box":
- CENTRE     : the table HUB. A meeting table stretched to width=3.2 with a rectilinear ring of
               chairs (`AroundGroup.place_rectilinear`, 4 per long side + 1 each end = seats 10),
               jittered so the seating reads used; a grounding rug; ONE linear pendant.
- FRONT wall : the PRESENTATION anchor — the reason the room exists. A slim AV credenza on the
               floor, the large display hung ABOVE it, the whiteboard beside it.
- BACK wall  : the SERVICE zone — a coffee sideboard (machine + carafe on top), with the water
               cooler and the greenery pushed into the two corners so nothing tall stands at the
               wall centre.
- LEFT wall  : DAYLIGHT — floor-to-ceiling glass + blinds. It carries no furniture, so it stays
               the light source (and it is why this room needs no ceiling panels at all).
- RIGHT wall : framed art + the entry door — the light wall, kept clear of the sightline from the
               table to the display.

Identity comes from the table being STRETCHED (width=3.2, not uniformly scaled: a uniform scale
would give a 1.1 m-high table) and from the DISPLAY being oversized (modulate_scale=1.6 on a 1.2 m
mesh -> ~1.9 m). A short table with a small TV reads as a break room, not a boardroom.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/meeting_room_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the surfaces (tabletop, rug, greenery); phase 3
adds the wall decor, the glazing and the pendant.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("MeetingRoom", seed=17)

# --- pinned heroes (verified via the retrieve contact sheet + get_whd, offline, no network) ---
TABLE      = "hssd/aee7c3bde9e56a5b7207d7e19f8ad06580e80962"   # rectangular wood-top meeting table, dark trestle
                                                               # legs; measured 2.0x0.87 -> stretch to width=3.2
CHAIR      = "hssd/430315716f096225c260e048452d5361866e93b2"   # white leather high-back conference chair w/ arms
                                                               # + castors; 0.6 wide -> 4 fit a 3.2 m side
WALL_TV    = "hssd/576f0a57271ccc62554b2603a48047854254119d"   # large flat-screen display — measured only 1.2 m
                                                               # wide, so it must be scaled UP before wall mount
WHITEBOARD = "hssd/1b37271d2d52124cf69fa91a2acb11a6dde262f2"   # white dry-erase board, thin black frame (1.8 m).
                                                               # The "flip chart" query had no hit — this is it.
SIDEBOARD  = "hssd/70d4947007b0fafdfb7b4fc44a0b556f688ec4c4"   # low dark-wood sideboard, used for BOTH the AV
                                                               # credenza and the coffee station. Its finished
                                                               # doors are on its REVERSED face -> flip per wall.
COFFEE     = "hssd/85ba156832a3c03c731b50a54b8a724d837cb099"   # stainless office coffee machine ("coffee service
                                                               # cart" ERR'd -> compose the station instead)
WATER      = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"   # compact white water cooler
TALL_PLANT = "future/feeb8797-0f97-4fc1-b555-f206a8cdcf01"     # tall indoor plant, sleek pot
ABSTRACT   = "hssd/5e9d4d4d61e99ba9604ea74dbab640f487771502"   # framed abstract print
PHONE      = "hssd/b81bee4e4ef1682295bc9179f392cb68bc15f736"   # black desk phone — the "conference speakerphone"
                                                               # query returned a whole TABLE; this stands in
LAPTOP     = "hssd/57d2b6c1b3bb6903c7683cff9ba9016a8c50ff70"   # open silver laptop

scene.prefetch_assets([
    "a long rectangular boardroom conference table", "a white leather conference chair with armrests",
    "a large wall-mounted flat screen display", "a white dry-erase whiteboard",
    "a low dark wood office sideboard credenza", "a stainless steel office coffee machine",
    "a white office water cooler dispenser", "a tall potted indoor office plant",
    "a low floral centerpiece in a vase", "a black conference desk phone",
    "an open silver laptop computer", "a stack of notepads with pens",
    "a glass water carafe with drinking glasses", "a large framed abstract print",
    "a long linear LED ceiling pendant light", "a flush square panel ceiling light",
    "a large grey commercial area rug",
])

# --- the boardroom cluster — table + a rectilinear ring of chairs (4 per side, 1 each end) ---
with scene.AroundGroup(sparsity=0.15, jitter=0.35) as boardroom:
    table = scene.AddAsset("a long rectangular boardroom conference table", asset_id=TABLE, width=3.2)
    boardroom.set_anchor(table)
    long1 = 4 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    long2 = 4 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    ends  = 2 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    boardroom.place_rectilinear(longer_side1=long1, longer_side2=long2,
                                shorter_side1=[ends[0]], shorter_side2=[ends[1]])

    if PHASE >= 2:
        # restrained boardroom styling. The anchor is the TABLE, so place_on_top seats these on
        # the table top. Gate INSIDE the with-block: a place_on_top gated outside it never runs.
        boardroom.place_on_top([
            scene.AddAsset("a low floral centerpiece in a vase"),
            scene.AddAsset("a black conference desk phone", asset_id=PHONE),
            scene.AddAsset("an open silver laptop computer", asset_id=LAPTOP),
            scene.AddAsset("a stack of notepads with pens"),
        ])
        boardroom.place_rug("a large grey commercial area rug", size=0.9)

    if PHASE >= 3:
        # ONE linear pendant over the table, and it is the room's ONLY fixture: a room-wide
        # flush-panel add_lighting starfielded the ceiling AND blew out the exposure. density>0
        # copies the (wiry) pendant mesh across the group footprint -> a strip of clutter;
        # density=0 = one clean fixture. The floor-to-ceiling glass supplies the ambient daylight.
        boardroom.add_lighting("a long linear LED ceiling pendant light", density=0)

# --- the coffee & water service station: sideboard + coffee machine + carafe on top (back wall) ---
with scene.RelativeGroup() as coffee_station:
    coffee_station.set_anchor(scene.AddAsset("a low dark wood office sideboard credenza",
                                             asset_id=SIDEBOARD, width=1.6))
    if PHASE >= 2:
        # place_on_top sized both props to the WIDE sideboard and they landed ~2x oversized ->
        # modulate_scale=0.5 on each.
        coffee_station.place_on_top([
            scene.AddAsset("a stainless steel office coffee machine", asset_id=COFFEE, modulate_scale=0.5),
            scene.AddAsset("a glass water carafe with drinking glasses", modulate_scale=0.5),
        ])

# the same sideboard mesh, stretched wider, doing the AV-credenza job on the presentation wall
av_credenza = scene.AddAsset("a low dark wood office AV credenza cabinet", asset_id=SIDEBOARD, width=1.8)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.2, max_height=3.2) as room:
    room.place_walls(floor_texture="grey commercial carpet tile",
                     ceiling_texture="white acoustic panel ceiling",
                     wall_texture="soft warm grey with one charcoal accent wall")

    room.place_on_center(boardroom, facing="front")

    # FRONT wall = presentation anchor: the slim AV credenza on the floor (the display + whiteboard
    # hang above it in phase 3). This sideboard mesh's finished doors are on its REVERSED face, so
    # the default wall-facing shows its open legs -> flip it (front wall -> facing="front"; back
    # wall -> facing="back"). VLM caught both. This is the deliberate exception to "don't pass the
    # wall's own name as facing" — the default is right for a normal mesh, wrong for a reversed one.
    room.place_on_front_wall_center(av_credenza, facing="front")

    # BACK wall = service zone: the coffee sideboard at the centre, the water cooler in the corner
    room.place_on_back_wall_center(coffee_station, facing="back")
    room.place_on_back_left_corner(scene.AddAsset("a white office water cooler dispenser", asset_id=WATER),
                                   facing="front")

    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        # greenery in the far corner — nothing tall at a wall CENTRE, where the cameras sit
        room.place_on_back_right_corner(scene.AddAsset("a tall potted indoor office plant",
                                                       asset_id=TALL_PLANT, width=0.8), facing="front")

    if PHASE >= 3:
        # PRE-SCALE the display BEFORE place_on_wall_*: the mount height is derived from the
        # UN-scaled mesh. The TV is only 1.2 m wide -> modulate_scale=1.6 (uniform, keeps aspect)
        # gives the ~1.9 m presentation display the plan asks for.
        tv = scene.AddAsset("a large wall-mounted flat screen display", asset_id=WALL_TV,
                            modulate_scale=1.6)
        room.place_on_wall_front_center(tv)
        room.place_on_wall_front_right(scene.AddAsset("a white dry-erase whiteboard", asset_id=WHITEBOARD))

        # LEFT wall = daylight glass; RIGHT wall = framed art (the door is already placed above)
        room.place_window_floor_to_ceiling("left_wall", curtain="light grey roller blinds")
        room.place_on_wall_right_center(scene.AddAsset("a large framed abstract print", asset_id=ABSTRACT))

    # lighting: the table's linear pendant is the only fixture (a room-wide flush-panel set
    # starfielded + blew out the exposure); the floor-to-ceiling glass supplies the ambient daylight.

scene.export("meeting_room_v1.blend")
