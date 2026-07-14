"""
Meeting room — "Integrated Executive Boardroom" (planner headline). Built asset-first
(retrieval stress test: 39/40 resolved, none < 0.30 — low-risk, NO ingest) then coarse-to-fine.

Layout = the classic boardroom: a long central conference table ringed by chairs is the activity
hub; the FRONT wall is the presentation anchor (a large wall display + a whiteboard over a slim AV
credenza); the BACK wall is the service zone (a coffee/water sideboard, a water cooler, greenery);
the LEFT wall is floor-to-ceiling glass with blinds for daylight; the RIGHT wall carries framed art +
the door. A single long linear pendant runs down the table, flush panels give even ambient light.

Heroes pinned + measured via retrieve/get_whd: table 2.0x0.87 (stretched to width=3.2), white leather
conference chair 0.6 wide, wall TV 1.2 wide (modulate_scale 1.6 -> ~1.9 m display), whiteboard 1.8 wide.

Build state: DONE / essentially VLM-clean (2026-07-09, seed=17, 3 render passes). No rescale / no
room-rescale / no wall overlap / no overlap warning; only the noisy RotationConstraint on two tiny
on-top props (coffee machine/carafe "face center") remains, declined as noise. Three fixes across the
passes: (1) a room-wide flush-panel add_lighting starfielded the ceiling + blew out exposure -> use
ONLY the table's linear pendant at density=0 (density>0 multiplies the wiry pendant mesh into a strip);
the floor-to-ceiling glass supplies ambient daylight. (2) this sideboard mesh's finished doors are on
its REVERSED face, so default wall-facing showed its open legs -> flip per wall (front wall facing
"front", back wall facing "back"). (3) coffee machine + carafe came out 2x oversized on the credenza ->
modulate_scale=0.5.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("MeetingRoom", seed=17)

# --- pinned heroes (verified via retrieve contact sheet + get_whd) ---
TABLE      = "hssd/aee7c3bde9e56a5b7207d7e19f8ad06580e80962"   # rectangular wood-top meeting table, dark trestle legs
CHAIR      = "hssd/430315716f096225c260e048452d5361866e93b2"   # white leather high-back conference chair w/ arms + castors
WALL_TV    = "hssd/576f0a57271ccc62554b2603a48047854254119d"   # large flat-screen display (1.2 m -> scale up)
WHITEBOARD = "hssd/1b37271d2d52124cf69fa91a2acb11a6dde262f2"   # white dry-erase board, thin black frame
SIDEBOARD  = "hssd/70d4947007b0fafdfb7b4fc44a0b556f688ec4c4"   # low dark-wood sideboard (AV credenza + coffee station)
COFFEE     = "hssd/85ba156832a3c03c731b50a54b8a724d837cb099"   # stainless office coffee machine
WATER      = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"   # compact white water cooler
TALL_PLANT = "future/feeb8797-0f97-4fc1-b555-f206a8cdcf01"     # tall indoor plant, sleek pot
ABSTRACT   = "hssd/5e9d4d4d61e99ba9604ea74dbab640f487771502"   # framed abstract print
PHONE      = "hssd/b81bee4e4ef1682295bc9179f392cb68bc15f736"   # black desk phone (the conference speakerphone)
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

# --- Phase 1: the boardroom cluster — table + a rectilinear ring of chairs (4 per side, 1 each end) ---
with scene.AroundGroup(sparsity=0.15, jitter=0.35) as boardroom:
    table = scene.AddAsset("a long rectangular boardroom conference table", asset_id=TABLE, width=3.2)
    boardroom.set_anchor(table)
    long1 = 4 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    long2 = 4 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    ends  = 2 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    boardroom.place_rectilinear(longer_side1=long1, longer_side2=long2,
                                shorter_side1=[ends[0]], shorter_side2=[ends[1]])
    # Phase 2: restrained boardroom styling on the table + the hero linear light + a grounding rug
    boardroom.place_on_top([
        scene.AddAsset("a low floral centerpiece in a vase"),
        scene.AddAsset("a black conference desk phone", asset_id=PHONE),
        scene.AddAsset("an open silver laptop computer", asset_id=LAPTOP),
        scene.AddAsset("a stack of notepads with pens"),
    ])
    boardroom.add_lighting("a long linear LED ceiling pendant light", density=0)  # ONE linear pendant (density>0 starfields the wiry mesh)
    boardroom.place_rug("a large grey commercial area rug", size=0.9)

# --- a coffee & water service station: sideboard + coffee machine + carafe on top (back wall) ---
with scene.RelativeGroup() as coffee_station:
    coffee_station.set_anchor(scene.AddAsset("a low dark wood office sideboard credenza",
                                             asset_id=SIDEBOARD, width=1.6))
    coffee_station.place_on_top([
        scene.AddAsset("a stainless steel office coffee machine", asset_id=COFFEE, modulate_scale=0.5),
        scene.AddAsset("a glass water carafe with drinking glasses", modulate_scale=0.5),
    ])

# TV pre-scaled BEFORE wall placement (wall-art-mount-height lesson) -> ~1.9 m display
tv = scene.AddAsset("a large wall-mounted flat screen display", asset_id=WALL_TV, modulate_scale=1.6)

# --- Phase 3: room shell + presentation wall + service wall + daylight + decor ---
av_credenza = scene.AddAsset("a low dark wood office AV credenza cabinet", asset_id=SIDEBOARD, width=1.8)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.2, max_height=3.2) as room:
    room.place_walls(floor_texture="grey commercial carpet tile",
                     ceiling_texture="white acoustic panel ceiling",
                     wall_texture="soft warm grey with one charcoal accent wall")

    room.place_on_center(boardroom, facing="front")

    # FRONT wall = presentation anchor: slim AV credenza (floor) + large display (hung above) + whiteboard.
    # This sideboard mesh's finished doors are on its REVERSED face, so the default wall-facing shows its
    # open legs -> flip it (front wall -> facing="front"; back wall -> facing="back"). VLM caught both.
    room.place_on_front_wall_center(av_credenza, facing="front")
    room.place_on_wall_front_center(tv)
    room.place_on_wall_front_right(scene.AddAsset("a white dry-erase whiteboard", asset_id=WHITEBOARD))

    # BACK wall = service zone: coffee sideboard (center) + water cooler + greenery in the corners
    room.place_on_back_wall_center(coffee_station, facing="back")
    room.place_on_back_left_corner(scene.AddAsset("a white office water cooler dispenser", asset_id=WATER),
                                   facing="front")
    room.place_on_back_right_corner(scene.AddAsset("a tall potted indoor office plant",
                                                   asset_id=TALL_PLANT, width=0.8), facing="front")

    # LEFT wall = daylight glass; RIGHT wall = framed art + entry door
    room.place_window_floor_to_ceiling("left_wall", curtain="light grey roller blinds")
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract print", asset_id=ABSTRACT))
    room.place_door("right_wall", position="right")

    # lighting: the table's twin linear pendants are the only fixtures (a room-wide flush-panel set
    # starfielded + blew out the exposure); the floor-to-ceiling glass supplies the ambient daylight.

scene.export("meeting_room.blend")
