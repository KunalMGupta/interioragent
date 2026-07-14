"""Bakery — "Glassfront Bakery with Brick Anchor and Blue Mullion Rhythm" (planner headline).

Layout (slot economy for a street-corner shop — 4 floor slots + walls):
- BACK = the service spine (bar.md rigid-station pattern): white counter with a warm
  wood top (the plan's "white service spine") + the industrial stainless wire shelving
  composed BEHIND it (geometric staff aisle, not a clearance constraint). Identity =
  PRODUCT at viewing height (jewelry/coffee_shop lesson — no glass pastry-case mesh
  exists; the audit's best "case" hits were an empty white cabinet and a Haagen-Dazs
  freezer): 3-tier pastry stand, sponge cake, rustic bread board, takeaway cups,
  espresso machine, POS massed ON the counter; the wire shelving stocked with bread
  bins / wicker basket / bread board / donuts so back-of-house doesn't read empty.
- FRONT = the window bar: slim rustic wood console flush to the glass storefront +
  a row of 3 round-seat wooden stools facing it (plan's front-edge seating). Standard
  window with deep blue curtains (NEVER floor-to-ceiling — retail black-void lesson)
  + door on the right.
- LEFT-CENTER = one 2-top cafe cluster (coffee_shop unit: pedestal table + papercord
  chairs + jute rug + cup/donut box).
- Brick comes from the WALL texture (no brick-counter mesh); blue identity = the
  French blue menu blackboard behind the counter + the blue window curtains.
- Lighting: pinned black dome pendants over the counter zone (SINGULAR query,
  density 0.15) + flush LED room fill at 0.01 (small-room density lesson).

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds the floor
layout (~1 min) to verify size/overlaps/clearances before surface dressing (2) and
walls/lighting/mood (3).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Bakery", seed=12)

COUNTER   = "hssd/67b505c2cfc433bc4ffe39250cafda3951d91939"   # white counter + warm wood top (rests flat — laundromat)
BACKSHELF = "custom/71bda402b67456713f4f06f422bb8bb8ce1455da" # industrial grey wire shelving, 5 tiers
WINDOWBAR = "hssd/f72c0e86085c6b6f48b82d47d5066248be8b7c4a"   # rustic warm wood console (the window ledge-bar)
STOOL     = "hssd/5cbddc4215af577a945d42dae708197b48a6a14e"   # simple wooden bar stool, round seat, three legs
PENDANT   = "hssd/b1c964b529d36176ec5a13f5b325262dfdd7f217"   # black metal dome pendant (singular, short drop)
TIER3     = "hssd/351f165d750a156b71eb7df6ee9df679122205a1"   # 3-tier cake stand with pastries
CAKE      = "hssd/1c2885ea1bb5a23461ec5561f93dde711ffa8161"   # sponge cake with flowers
BREADBRD  = "hssd/92fc2ee204fda4be19d08b79f79f68fc87e9afaa"   # rustic bread board set (sliced loaves)
DONUTS    = "hssd/453c97f1448b845d012dad29bedc7376278318c4"   # trio of chocolate donuts
DONUTBOX  = "hssd/243a31f2532e4060d033fe307c3e576dac17673b"   # open box of assorted donuts
TAKEAWAY  = "hssd/7e72a52e8b412403169fb06803adf6882f5dcc78"   # takeaway cups w/ carrier
CUP       = "hssd/280760263c95d8e413202565460a793d06e5576e"   # coffee cup and saucer
ESPRESSO  = "hssd/85ba156832a3c03c731b50a54b8a724d837cb099"   # stainless espresso machine (the steel cue)
POS       = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"   # touchscreen POS
BREADBIN  = "hssd/27584d59cc4fe564020ed5d65dbb5762d0638404"   # cream bread bin with beech lid
WICKER    = "future/c96d2ee0-8593-42b8-bcc3-bd9e4476b49d"     # wicker basket, fabric liner
TABLE     = "hssd/298047dc4741dee54e32b89e5776db61f2028971"   # weathered oak pedestal pub table
CHAIR     = "hssd/dd06f2c3881f6491c605dff6757742733b81c402"   # papercord cafe chair
FRBOARD   = "hssd/a8fe5f34c49c3e11bd9f5ef3380b5e7efef943e2"   # French blue menu blackboard sticker (FLAT — the blue brand wall)
BREADCLK  = "hssd/ca5f5dfd4564353aee167464dae2c409c42634b6"   # vintage tin 'Bread' wall clock
STILLLIFE = "hssd/116cb370fa811f28af6559ff1fc2448489e4541f"   # rustic still life: wine, bread, cheese
PLANT     = "future/be7b52ed-6101-4dca-93e6-06b8eaef7342"     # leafy plant, gray ceramic planter
FRIDGE    = "hssd/cae4c60830bba615ff533dc23ffee6e6e5c7d14e"   # slim glass-door display fridge (drinks/cake fridge)

scene.prefetch_assets([
    "a white bakery service counter with a warm wood top",
    "an industrial stainless steel wire shelving rack",
    "a narrow rustic light wood console bar table",
    "a simple wooden bar stool with a round seat",
    "a black metal dome industrial pendant light",
    "a white three-tiered cake stand with pastries",
    "a white sponge cake with floral decoration",
    "a rustic wooden board with assorted sliced bread loaves",
    "a set of takeaway coffee cups in a carrier",
    "a stainless steel commercial espresso machine",
    "a black touchscreen POS terminal",
    "a trio of chocolate donuts on a napkin",
    "a cream enamel bread bin with a wooden lid",
    "a wicker basket with a fabric liner",
    "a small round weathered oak cafe table on a pedestal base",
    "a light wood cafe chair with a papercord seat",
    "a white coffee cup and saucer",
    "an open box of assorted donuts",
    "a neutral woven jute round rug",
    "a leafy potted plant in a gray ceramic planter",
    "a tall glass door display refrigerator",
    "a French bakery menu blackboard in blue",
    "a vintage tin wall clock with bread lettering",
    "a rustic still life painting with bread and wine",
    "a flat round LED flush mount ceiling light",
])

# --- BACK: the service spine (one rigid station = one floor slot) -----------------
counter = scene.AddAsset("a white bakery service counter with a warm wood top",
                         asset_id=COUNTER, width=2.4)
with scene.RelativeGroup() as counter_group:
    counter_group.set_anchor(counter)
    if PHASE >= 2:
        # the pastry display IS the counter top — massed product at viewing height
        counter_group.place_on_top([
            scene.AddAsset("a white three-tiered cake stand with pastries", asset_id=TIER3),
            scene.AddAsset("a white sponge cake with floral decoration", asset_id=CAKE),
            scene.AddAsset("a rustic wooden board with assorted sliced bread loaves", asset_id=BREADBRD),
            scene.AddAsset("a set of takeaway coffee cups in a carrier", asset_id=TAKEAWAY),
            scene.AddAsset("a stainless steel commercial espresso machine", asset_id=ESPRESSO),
            scene.AddAsset("a black touchscreen POS terminal", asset_id=POS),
        ])
    if PHASE >= 3:
        counter_group.add_lighting("a black metal dome industrial pendant light",
                                   density=0.15)

backshelf = scene.AddAsset("an industrial stainless steel wire shelving rack",
                           asset_id=BACKSHELF)
# the mesh is natively SQUAT (w:h ~1.45) — a pure uniform scale to rack height blew
# it up to ~2.5 m wide/deep and swallowed the back-wall interior camera. Take height
# to 1.6 uniformly, then pin real wire-rack width/depth (mild distortion is invisible
# on an open wire frame).
backshelf.scale(backshelf.get_width() * 1.25 / backshelf.get_height())
backshelf.scale_only_width(1.8)
backshelf.scale_only_depth(0.35)
# height 1.25: the interior wall cameras sit at ~1.4-1.5 m at the wall centers, and a
# taller rack anywhere near a wall center occludes that wall's whole view (three builds
# hit this at 1.6-1.75). Mid-height also matches the plan collage's bread shelving.
with scene.RelativeGroup() as backshelf_group:
    backshelf_group.set_anchor(backshelf)
    if PHASE >= 2:
        # stocked back-of-house — an empty fixture names the fixture, not the shop
        backshelf_group.place_inside([
            scene.AddAsset("a cream enamel bread bin with a wooden lid", asset_id=BREADBIN),
            scene.AddAsset("a wicker basket with a fabric liner", asset_id=WICKER),
            scene.AddAsset("a rustic wooden board with assorted sliced bread loaves", asset_id=BREADBRD),
            scene.AddAsset("a trio of chocolate donuts on a napkin", asset_id=DONUTS),
        ])

with scene.RelativeGroup() as station:
    station.set_anchor(counter_group)
    # diagonal offset: staff aisle stays baked-in (bar.md gap lesson), the rack sits
    # off the room's centerline (plan collage composition; also keeps the back-wall
    # interior camera out of the rack)
    station.place_on_back_left(backshelf_group)

# --- FRONT: the window bar (console flush to the glass + stool row) ---------------
with scene.AroundGroup(sparsity=0.15, jitter=0.2) as window_bar:
    ledge = scene.AddAsset("a narrow rustic light wood console bar table",
                           asset_id=WINDOWBAR, width=2.8)
    # user feedback: the ledge read undersized against its three stools — widen the
    # top to a real bar depth (single-axis is fine on a plank-top console)
    ledge.scale_only_depth(0.5)
    window_bar.set_anchor(ledge)
    stools = 3 * scene.AddAsset("a simple wooden bar stool with a round seat",
                                asset_id=STOOL, modulate_scale=0.85)
    # keep the default uniform straight facing (bar.md: no face(toward=anchor) on a row)
    window_bar.place_rectilinear(longer_side1=stools)

# --- LEFT-CENTER: one 2-top cafe cluster ------------------------------------------
with scene.AroundGroup(sparsity=0.2, jitter=0.35) as two_top:
    t = scene.AddAsset("a small round weathered oak cafe table on a pedestal base",
                       asset_id=TABLE, width=0.7)
    two_top.set_anchor(t)
    chairs = 2 * scene.AddAsset("a light wood cafe chair with a papercord seat",
                                asset_id=CHAIR, modulate_scale=0.95)
    two_top.place_circle(chairs)
    for c in chairs:
        two_top.face(c, toward=t)
    if PHASE >= 2:
        two_top.place_on_top([
            scene.AddAsset("a white coffee cup and saucer", asset_id=CUP),
            scene.AddAsset("an open box of assorted donuts", asset_id=DONUTBOX),
        ])
        two_top.place_rug("a neutral woven jute round rug", size=1.1)

# --- the room ----------------------------------------------------------------------
# modulate_scale=0.78: RoomProportions voted shrink every phase (0.87→0.85→0.77→0.76→
# 0.75); held per render-wins-early, applied ONE decisive shrink in the final phase —
# the open centre aisle is genuinely sparse (laundromat lesson: a sparse room may go
# well below 1.0).
with scene.RoomGroup(modulate_scale=0.78, randomness=0.15) as room:
    # plain color+material words — "warm red brick" embedded to a pale pink plaster,
    # "light oak wood plank floor" to near-white tile (texture-embedding lesson)
    room.place_walls(floor_texture="natural oak wood floor planks",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="a brick wall with reddish-brown bricks and light mortar joints")
    room.place_on_back(station, facing="front")
    # wall placement so the ledge hugs the glass storefront (a front SLOT placement
    # left it drifting mid-floor); default facing turns the unit into the room
    room.place_on_front_wall_center(window_bar)
    room.place_on_left(two_top, facing="front")
    # drinks/cake fridge fills the open right side (user feedback: room read empty);
    # OFF the wall center — a ~1.8 m fixture at a wall center blinds that wall's camera
    room.place_on_right_wall_left(
        scene.AddAsset("a tall glass door display refrigerator", asset_id=FRIDGE))
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")
    if PHASE >= 3:
        room.place_on_back_left_corner(
            scene.AddAsset("a leafy potted plant in a gray ceramic planter", asset_id=PLANT),
            facing="front")
        room.place_on_wall_back_center(
            scene.AddAsset("a French bakery menu blackboard in blue", asset_id=FRBOARD))
        room.place_on_wall_left_center(
            scene.AddAsset("a vintage tin wall clock with bread lettering", asset_id=BREADCLK))
        room.place_on_wall_right_center(
            scene.AddAsset("a rustic still life painting with bread and wine", asset_id=STILLLIFE))
        room.place_window_standard("front_wall", position="left",
                                   curtain="deep blue linen curtains")
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("bakery_v1.blend")
