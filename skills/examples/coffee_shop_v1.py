"""Cozy coffee shop — agent-authored worked example (see coffee_shop.md).

Layout: slot economy for a small/cozy brief — few floor slots, modest hero widths,
so the RoomGroup shell auto-sizes cafe-scale by construction.
- BACK: rigid counter station (counter + massed pastries/espresso/POS on top,
  stocked light-oak back-bar behind, dessert cart at its left) — bar.md pattern.
- LEFT + CENTER: one 2-top cafe cluster each (built once, duplicated via 2 * unit).
- RIGHT: caramel-leather reading nook (armchair + side table + floor lamp, one unit).
- FRONT WALL: cream upholstered bench (wall-adjacent) + standard window + door.
- Identity = PRODUCT at viewing height (jewelry_shop lesson): cake stands, sponge
  cake, donuts, takeaway cups ON the counter; jars/mugs INSIDE the back-bar shelves;
  espresso chalkboard menu on the wall above.
- Lighting: rattan pendants over the counter zone (singular query, density 0.15) +
  flush-mount room fill at 0.01 (SMALL-room density lesson: 0.05 is a starfield) +
  window daylight.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the
floor layout (~1 min) to verify room size / overlaps / clearances before the
expensive surface dressing (phase 2) and walls/lighting/mood (phase 3). The
default build (no --phase) is the complete scene, identical to the ungated form.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("CozyCoffeeShop", seed=7)

COUNTER = "hssd/b1c9d7321512686e02f2d0be978056456479e14c"   # paneled wooden bar counter
BACKBAR = "future/da34f6fe-6160-4df4-9bd1-8ee0d309a396"     # light oak bookshelf (back-bar)
CART    = "custom/424f59cce4d18e1f55cb57fdabecb0f8567717f2" # vintage dessert cart, cream+gold
BENCH   = "hssd/a5faa788a66067bdb536364b705735ba7c5547af"   # cream upholstered bench, wood legs
# (the walnut bench hssd/66b84f2b... has an off-center mesh origin and floats when
#  wall-placed — its self-reported AABB disagrees with the render geometry; swapped)
TABLE   = "hssd/298047dc4741dee54e32b89e5776db61f2028971"   # weathered oak pedestal pub table
CHAIR   = "hssd/dd06f2c3881f6491c605dff6757742733b81c402"   # papercord cafe chair
ESPRESSO= "hssd/85ba156832a3c03c731b50a54b8a724d837cb099"   # stainless espresso machine
POS     = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"   # touchscreen POS
TIER3   = "hssd/351f165d750a156b71eb7df6ee9df679122205a1"   # 3-tier cake stand
CAKE    = "hssd/1c2885ea1bb5a23461ec5561f93dde711ffa8161"   # sponge cake with flowers
DONUTS  = "hssd/453c97f1448b845d012dad29bedc7376278318c4"   # trio of chocolate donuts
DONUTBOX= "hssd/243a31f2532e4060d033fe307c3e576dac17673b"   # open box of assorted donuts
CUP     = "hssd/280760263c95d8e413202565460a793d06e5576e"   # coffee cup and saucer
TAKEAWAY= "hssd/7e72a52e8b412403169fb06803adf6882f5dcc78"   # takeaway cups w/ carrier
PLANT   = "future/be7b52ed-6101-4dca-93e6-06b8eaef7342"     # ceramic planter, green foliage
MENU    = "hssd/dc704bb098f08b7a784d4b4f650c9e9c679cc64a"   # vintage espresso chalkboard (walls)
JARSET  = "hssd/221f50f3c5d67b6ca37bdc3b2d2d14f3d5ce2380"   # tea/coffee/sugar ceramic jars
BEANJAR = "hssd/72a0cb00b84683309970a14cadb99bdb75e03a43"   # wooden coffee jar
CAFEMUG = "hssd/ddfc354ff8c4df7ca1cd9a56c245e2e0b848d55b"   # 'Potting Shed Coffee' mug

scene.prefetch_assets([
    "a long wooden cafe counter with a paneled front",
    "a light oak open bookshelf back bar",
    "a vintage cream dessert cart with a canopy",
    "a cream upholstered window bench with wooden legs",
    "a small round weathered oak cafe table on a pedestal base",
    "a light wood cafe chair with a papercord seat",
    "a stainless steel commercial espresso machine",
    "a black touchscreen POS terminal",
    "a white three-tiered cake stand with pastries",
    "a white sponge cake with floral decoration",
    "a trio of chocolate donuts on a napkin",
    "an open box of assorted donuts",
    "a white coffee cup and saucer",
    "a set of takeaway coffee cups in a carrier",
    "a leafy potted plant in a gray ceramic planter",
    "a woven rattan dome pendant light",
    "a flat round LED flush mount ceiling light",
    "a neutral woven jute round rug",
    "a framed vintage coffee advertisement print",
    # vibe layer
    "a vintage espresso-themed chalkboard menu",
    "a set of ceramic jars labeled tea coffee sugar",
    "a wooden coffee bean jar",
    "a white ceramic coffee shop mug",
    "a caramel brown leather armchair",
    "a small round dark wood side table",
    "a warm brass floor lamp with a fabric shade",
    "a trailing potted pothos plant",
])

# --- BACK: the counter station (one rigid unit = one floor slot) ---------------
counter = scene.AddAsset("a long wooden cafe counter with a paneled front",
                         asset_id=COUNTER, width=2.4)
with scene.RelativeGroup() as counter_group:
    counter_group.set_anchor(counter)
    if PHASE >= 2:
        counter_group.place_on_top([
            scene.AddAsset("a stainless steel commercial espresso machine", asset_id=ESPRESSO),
            scene.AddAsset("a black touchscreen POS terminal", asset_id=POS),
            scene.AddAsset("a white three-tiered cake stand with pastries", asset_id=TIER3),
            scene.AddAsset("a white sponge cake with floral decoration", asset_id=CAKE),
            scene.AddAsset("a trio of chocolate donuts on a napkin", asset_id=DONUTS),
            scene.AddAsset("a set of takeaway coffee cups in a carrier", asset_id=TAKEAWAY),
        ])
    if PHASE >= 3:
        counter_group.add_lighting("a woven rattan dome pendant light", density=0.15)

backbar = scene.AddAsset("a light oak open bookshelf back bar", asset_id=BACKBAR, width=1.8)
# stock the back-bar shelves — a dressed shelf reads "coffee shop"; an empty one
# reads "furniture showroom" (jewelry_shop lesson, applied to the service wall)
with scene.RelativeGroup() as backbar_group:
    backbar_group.set_anchor(backbar)
    if PHASE >= 2:
        backbar_group.place_inside([
            scene.AddAsset("a set of ceramic jars labeled tea coffee sugar", asset_id=JARSET),
            scene.AddAsset("a wooden coffee bean jar", asset_id=BEANJAR),
            scene.AddAsset("a white ceramic coffee shop mug", asset_id=CAFEMUG),
            scene.AddAsset("a white coffee cup and saucer", asset_id=CUP),
        ])
        backbar_group.place_on_top([
            scene.AddAsset("a trailing potted pothos plant"),
        ])

cart = scene.AddAsset("a vintage cream dessert cart with a canopy", asset_id=CART)
with scene.RelativeGroup() as station:
    station.set_anchor(counter_group)
    station.place_on_back(backbar_group)
    station.place_on_left(cart)   # only front/back have _adjacent variants

# --- 2-top cafe cluster: built ONCE, duplicated -------------------------------
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

tt_left, tt_center = 2 * two_top

# cozy reading nook: seat + its table + its task light travel as one unit
with scene.RelativeGroup() as nook:
    armchair = scene.AddAsset("a caramel brown leather armchair")
    nook.set_anchor(armchair)
    nook.place_on_left(scene.AddAsset("a small round dark wood side table"))
    nook.place_on_back(scene.AddAsset("a warm brass floor lamp with a fabric shade"))

bench = scene.AddAsset("a cream upholstered window bench with wooden legs",
                       asset_id=BENCH, width=2.0)

# --- the room ------------------------------------------------------------------
with scene.RoomGroup(modulate_scale=0.9, randomness=0.15) as room:
    room.place_walls(floor_texture="medium brown oak wood plank floor",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="warm sand beige plaster")
    room.place_on_back(station, facing="front")
    room.place_on_left(tt_left, facing="front")
    room.place_on_center(tt_center, facing="front")
    room.place_on_right(nook, facing="left")                    # armchair looks into the room
    room.place_on_front_wall_center(bench)                      # default: faces the room
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")
    if PHASE >= 3:
        room.place_on_back_right_corner(
            scene.AddAsset("a leafy potted plant in a gray ceramic planter", asset_id=PLANT),
            facing="front")
        room.place_on_wall_back_center(
            scene.AddAsset("a vintage espresso-themed chalkboard menu", asset_id=MENU))
        room.place_on_wall_left_center(
            scene.AddAsset("a framed vintage coffee advertisement print"))
        room.place_window_standard("front_wall", position="left",
                                   curtain="cream cafe curtains")
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

# The walnut bench mesh has an off-center origin and floats when wall-placed
# (bottom ~0.6 m up; counter/back-bar rest fine) — snap it to the floor by its
# own world AABB after compile. Mesh-specific; logged as a front-cache-style
# per-asset fix candidate.
_gap = float(bench.get_aabb()[0][1])
if _gap > 0.01:
    bench.translate(0, -_gap, 0)

scene.export("coffee_shop_v1.blend")
