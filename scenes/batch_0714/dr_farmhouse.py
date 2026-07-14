"""Farmhouse dining room — batch_0714 (seed=24).

Layout = the dining_room worked example (meeting_room's table hub, domesticated)
in its rustic key:
- CENTER     = the dining cluster: a long rustic trestle-leg table stretched to
  2.4 m, chairs down the long sides via place_rectilinear — TWO cross-back
  chairs on one long side, a rustic BENCH taking the other (the farmhouse
  signature), one host chair at each end. place_rectilinear gives the whole
  ring a uniform straight facing — NO per-seat face(), which would fan the end
  seats inward (kitchen v1 / dining_room "correct by construction").
  Phase 2 SETS the table (plates + centerpiece — a set table is what makes it
  a DINING room), on the flat wool rug at 0.8.
- BACK wall  = the service wall: LOW rustic sideboard (deliberately the low
  buffet, NOT the glass-front hutch the same query surfaces — a >1.4 m hutch
  at a wall centre blinds that wall's camera; if a hutch is ever wanted it
  belongs in a wall LEFT/RIGHT slot), pitcher + plates on top in phase 2, the
  framed landscape hung above it in phase 3.
- FRONT wall = standard window + cream cotton curtains (opposite the service
  wall).  RIGHT wall = the door.  Corners: tall plant back-left.
- Lighting   = ONE black iron cage-lantern pendant over the table
  (add_lighting on the dining GROUP, density=0 -> exactly one fixture,
  singular query), with the light budget dropped to 180 W — the dining_room
  measurement: once phase 3 hangs a fixture the brightness dial is the BUDGET,
  and the fixed 500 W floods a room this size flat.

Palette: dark hardwood floor, verified warm-beige walls, raw/waxed wood
furniture, cream textiles, black iron accents.

Phase-gated (IDSDL/phases.py): --phase 1 = floor anchors + door; phase 2 =
surface dressing; phase 3 = wall art / window / lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("FarmhouseDining", seed=24)

# On a room with ONE fixture the brightness dial is the LIGHT BUDGET, not the
# sky (dining_room lesson 1, measured: 500 W flattens ~27 m2 to near-white;
# 180 W lets the pendant read as a warm pool while the window supplies daylight).
# A scene attribute, so it survives the warm MCP server too (laundry_room).
scene.light_budget = 180.0

# --- pinned assets (every preview eyeballed at the audit gate; scores noted) ---
TABLE     = "hssd/b752a35d7bd02b5d35fef7d25e9b18f8158e67d0"  # 0.64 rustic plank-top table, splayed legs, BARE
#  (farmhouse-table coverage is thin — the sheet sat 0.60–0.64; this one has the
#   honest reclaimed-plank top and no baked-in chairs. Pinned for FORM.)
CHAIR     = "hssd/ac92c090320c6273da3073b81639ae33b30a0fe0"  # 0.72 classic cross-back dining chair
BENCH     = "hssd/73f8ed8796181efd45b88de14543d22045c59475"  # 0.70 rustic all-wood rectangular bench
SIDEBOARD = "hssd/628d0c20a57798970b7e965946a7bd28267eb3bb"  # 0.72 LOW rustic sideboard, flat top
LANDSCAPE = "hssd/4192b93682edc3c5585701c1ba90a34e9fd2f75b"  # framed landscape painting (real content)
CENTERPIECE = "hssd/3a30a28972253be16cf15f50c3e59440a2aba520"  # spring flowers in a white vase (dining_room pick)
PLATES    = "hssd/f54404265057174a0daa5fb6d4d59610d6d13f15"  # stack of white ceramic dinner plates
RUG       = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"  # known-flat beige wool rug

scene.prefetch_assets([
    "a long rustic farmhouse wood dining table, no chairs",
    "a classic wooden dining chair with a cross-back design",
    "a rustic wooden dining bench, backless",
    "a rustic farmhouse wooden sideboard buffet with a low flat top",
    "a low floral centerpiece in a vase",
    "a stack of white ceramic dinner plates",
    "a white ceramic pitcher",
    "a tall leafy potted plant in a ceramic planter",
    "a flat beige wool area rug",
    "a black metal cage lantern pendant light",
])

# --- Phase 1: the dining cluster — long table, chairs down the long sides ------
# place_rectilinear (NOT place_circle): a circle around a rectangular table
# flings the seats into a ring wider than the table and the shell grows to fit
# it (kitchen v1). Tight sparsity + modest jitter = lived-in, not inflated.
with scene.AroundGroup(sparsity=0.1, jitter=0.25) as dining:
    table = scene.AddAsset("a long rustic farmhouse wood dining table, no chairs",
                           asset_id=TABLE, width=2.4)
    dining.set_anchor(table)
    side1 = 2 * scene.AddAsset("a classic wooden dining chair with a cross-back design",
                               asset_id=CHAIR)
    ends  = 2 * scene.AddAsset("a classic wooden dining chair with a cross-back design",
                               asset_id=CHAIR)
    bench = scene.AddAsset("a rustic wooden dining bench, backless",
                           asset_id=BENCH, width=1.5)
    # two chairs per long side was the brief's default; the bench TAKES the
    # second long side (the farmhouse signature move), host chairs at the ends
    dining.place_rectilinear(longer_side1=side1, longer_side2=[bench],
                             shorter_side1=[ends[0]], shorter_side2=[ends[1]])
    # uniform facing comes free from place_rectilinear — never face() these

    if PHASE >= 2:
        # SET THE TABLE — furniture + laid surface = a dining room. Anchor is
        # the table, so place_on_top lands on the tabletop. All three props are
        # audit-verified meshes (never place_on_top a prop you have not seen).
        dining.place_on_top([
            scene.AddAsset("a low floral centerpiece in a vase", asset_id=CENTERPIECE),
            scene.AddAsset("a stack of white ceramic dinner plates", asset_id=PLATES),
        ])
        dining.place_rug("a flat beige wool area rug", size=0.8, asset_id=RUG)
        # <=0.8 under a room-dominating cluster or the rug reads wall-to-wall

    if PHASE >= 3:
        # ONE iron cage lantern over the table: singular query, density=0 =
        # exactly one fixture; a cage has a small emissive area and a short
        # drop, dodging the chandelier exposure blowout (executive_office)
        dining.add_lighting("a black metal cage lantern pendant light", density=0)

# --- the sideboard as a dressed unit: anchor = the sideboard, so its TOP gets
# the props (place_on_top targets the group ANCHOR — living_room_cozy v3) -------
sideboard = scene.AddAsset("a rustic farmhouse wooden sideboard buffet with a low flat top",
                           asset_id=SIDEBOARD)
sideboard.scale(sideboard.get_width() * 0.9 / sideboard.get_height())
# uniform height-fit to ~0.9 m: real buffet height, far under the ~1.4 m
# interior-camera eyeline at the back-wall centre (bakery / dining_room rule)
with scene.RelativeGroup() as service:
    service.set_anchor(sideboard)
    if PHASE >= 2:
        service.place_on_top([
            scene.AddAsset("a white ceramic pitcher"),
            scene.AddAsset("a stack of white ceramic dinner plates", asset_id=PLATES),
        ])

# --- the room -------------------------------------------------------------------
with scene.RoomGroup(modulate_scale=1.0, randomness=0.15) as room:
    # start neutral; the builder tunes modulate_scale from the vote train later.
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="smooth white plaster",
                     wall_texture="solid warm beige smooth uniform wall")
    # both strings VERIFIED (dining_room lesson 4: "warm oak" floor = salmon
    # plank; "warm greige" wall = light gray — word the strings like captions)
    room.place_on_center(dining, facing="front")
    room.place_on_back_wall_center(service)         # service wall, faces the room
    room.place_on_back_left_corner(
        scene.AddAsset("a tall leafy potted plant in a ceramic planter"))
    # floor mass -> phase 1 (never gate floor mass to >=2)
    room.place_door("right_wall", position="right") # phase 1: clearance shapes the solve

    if PHASE >= 3:
        # landscape ABOVE the sideboard — at 0.75 m high its AABB bottom
        # (1.5 - 0.375 = 1.13 m) clears the 0.9 m sideboard top, so the
        # wall-object clearance pass never slides the buffet off its wall
        # (dining_room lesson 3: check art bottoms against furniture tops)
        landscape = scene.AddAsset("a framed traditional landscape painting",
                                   asset_id=LANDSCAPE)
        landscape.scale_only_width(1.1); landscape.scale_only_height(0.75); landscape.scale_only_depth(0.04)
        room.place_on_wall_back_center(landscape)
        # window OPPOSITE the service wall; cream cotton carries the textile
        # layer (palette accents belong on props/textiles, not wall strings)
        room.place_window_standard("front_wall", position="center",
                                   curtain="cream cotton curtains")

scene.export("dr_farmhouse.blend")
