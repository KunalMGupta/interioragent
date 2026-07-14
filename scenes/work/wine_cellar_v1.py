"""
Wine cellar — "Chandelier-Centered Vaulted Wine Cellar" (planner target:
tmp/plan_A_wine_cellar__stone_brick_vault/plan.png).

Look (from the plan): a stone-and-brick vault where perimeter wine racks — visibly DENSE
with bottles — form a gallery backdrop, and a heavy oak tasting table sits on the centre
axis under warm dim light, set with a decanter and stemware. Oak barrels and weathered
crates are the rustic accents. Palette: warm brick, deep walnut, bottle-glass green, brass.

Layout = the library CORRIDOR skeleton (perimeter storage + central table), which is the
procedural twin of this scene:
  - LEFT + RIGHT (long) walls = the twin RACK RUNS (4 stocked racks each) -> the deep,
    longer-than-wide shell falls out of loading the two long walls.
  - CENTRE  = the HERO tasting table + 6 chairs, decanter/glassware on top, rug beneath.
  - BACK (short) wall = the feature wall: two stocked bottle cabinets, a barrel cluster,
    a stack of wine crates.
  - FRONT (short) wall = the entry: door + a rustic wine credenza + a framed wine print.

Notes carried in from the audit + the lesson bundle:
  1. IDENTITY = the PRODUCT on the fixture (jewelry_shop). The picker's top "wine rack"
     hit is an EMPTY white lattice; _RACK (future/daaa8299) is a dark rack with FOUR TIERS
     of bottles + an X-bin. An empty rack names the fixture, not the cellar.
  2. The trestle table mesh is only 0.51 m tall (coffee-table scale) -> scaled BY HEIGHT
     (uniform) to a real 0.76 m tasting table. Same class as the hospital-bed catch.
  3. add_lighting takes a COMPACT fixture, never a hanging chandelier (executive_office):
     the plan's chandelier is expressed as a warm caged industrial lamp, low density
     (small/medium room -> 0.015, the starfield band).
  4. No vaulted-ceiling geometry exists in the DSL — the vault is carried by the stone/
     brick textures. Texture strings stay plain (one colour + one material).

Phase 1: rack runs + tasting table/chairs + barrels/crates/credenza + door (floor layout).
Phase 2: decanter + stemware + wine service on the table; bottles on the credenza; rug.
Phase 3: brick/stone walls dressing — framed wine print, warm caged ceiling lamps.
"""
import os

# "warm DIM lighting" is a lighting-BUDGET problem, not a fixture-choice problem. Two dials,
# and they must be set BEFORE IDSDL imports (the renderer binds the sky at import):
#   IDSDL_SKY — the interior render hides the ceiling and lights the room from a strength-3.0
#     sky, which floods any room to daylight and is what actually washed this cellar out (no
#     fixture choice can beat it). The renderer documents 0.6-0.7 as the moody-room setting.
#   scene.light_budget (below) — the ceiling wattage the fixtures then split.
# With the sky dropped, the ceiling fixtures become the dominant source, which is what "dim,
# lit from above, stone in shadow" actually means.
os.environ["IDSDL_SKY"] = "0.6"

from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("WineCellar", seed=21)

# "warm DIM lighting" is the prompt's mood, and it is the one thing `add_lighting` could not
# express: `density` is fixture COUNT, and the ceiling budget was a hardcoded 500 W, which blew
# this cellar out to a white gallery (the executive_office overexposure, unfixable by fixture
# choice alone). `scene.light_budget` is now the dial — 200 W over ~30 m² of stone is candle-lit.
scene.light_budget = 90.0

# --- pinned assets (every preview eyeballed; dims verified offline with get_whd) -------
_RACK    = "future/daaa8299-afb9-4008-a00e-da7b736debc3"      # 1.00x2.06x0.33 tall rack, 4 tiers of BOTTLES + X-bin (hero)
_CAB     = "future/ca401fa0-7da7-4985-9231-60d43a9510f5"      # 0.80x1.97x0.24 dark bottle cabinet, stocked shelves
_TABLE   = "hssd/dad9e55721b563e24e25d575b256536985f1569c"    # rustic trestle table (NATIVE 0.51 m tall -> rescaled below)
_CHAIR   = "future/9c2e6c40-74b3-40b9-84bf-5de7cbfec0ff"      # dark leather + wood dining chair
_BARREL  = "future/19f58522-7c3d-493b-8657-417204dfdfa3"      # oak barrel, brass bands (native 0.65 m -> scaled up)
_BARRELD = "future/e591b956-a912-4570-a843-e38c928de172"      # barrel used as a display stand, bottles on top
_WCRATE  = "hssd/de123db78af8441c9abd5b45acb63fca224d493f"    # wine crate with metal handles, holding bottles
_CRATE   = "hssd/1038f7871d85a9318cf7854eb852f09bed912458"    # weathered vintage crate
_GLASS   = "hssd/a9d615bcd75af8e73df80fe7df1c64c938fa21ae"    # decanter + 4 stemmed glasses (the plan's centerpiece)
_SERVICE = "future/45884782-5d93-4c19-8d2d-1dd6fbd2096a"      # wine bottle in a holder + two glasses
_CREDENZ = "hssd/eedc60093cc3519ed6b7891469ad7097bd9867c0"    # rustic wine credenza, lattice + door (0.90 m tall)

scene.prefetch_assets([
    "a tall dark wooden wine rack full of wine bottles",
    "a tall dark wine cabinet stocked with wine bottles",
    "a long rustic dark wood trestle tasting table",
    "a dark leather and wood dining chair",
    "an oak wine barrel with metal bands",
    "an oak barrel used as a display stand with bottles",
    "a rustic wooden wine crate holding bottles",
    "a weathered vintage wooden crate",
    "a glass wine decanter with stemmed wine glasses",
    "a red wine bottle with two wine glasses",
    "a rustic wooden wine credenza with a bottle lattice",
    "an industrial black metal caged ceiling light with a metal shade",
    "a worn brown jute rug",
    "a framed vintage wine advertisement print",
])

# ============================ CENTRE: the tasting table (hero) =========================
# The trestle mesh ships at 0.51 m tall — coffee-table scale. Scale it UNIFORMLY by HEIGHT
# to a real 0.76 m tasting table (width 1.50 -> ~2.24 m long), per the dsl_reference recipe
# scale(get_width()*H/get_height()); a width= pin alone would squash the proportions.
_table = scene.AddAsset("a long rustic dark wood trestle tasting table", asset_id=_TABLE)
_table.scale(_table.get_width() * 0.76 / _table.get_height())

with scene.AroundGroup(sparsity=0.25, jitter=0.35) as tasting:
    tasting.set_anchor(_table)
    _seats_l = 3 * scene.AddAsset("a dark leather and wood dining chair", asset_id=_CHAIR)
    _seats_r = 3 * scene.AddAsset("a dark leather and wood dining chair", asset_id=_CHAIR)
    tasting.place_rectilinear(longer_side1=_seats_l, longer_side2=_seats_r)
    for _c in _seats_l + _seats_r:
        tasting.face(_c, toward=_table)          # arc/rectilinear seats orient sideways by default
    if PHASE >= 2:
        # the decanter + stemware IS the plan's centerpiece. Small props are oversized by the
        # on-top tournament (library banker's-lamp lesson): 0.55 read as a ~0.6 m magnum lying
        # across the table, 0.3 shrank to invisible specks — 0.4 is the size that reads.
        # Two glassware sets + the bottle service = a table laid for a tasting, not a lone prop.
        tasting.place_on_top([
            scene.AddAsset("a glass wine decanter with stemmed wine glasses",
                           asset_id=_GLASS, modulate_scale=0.4),
            scene.AddAsset("a red wine bottle with two wine glasses",
                           asset_id=_SERVICE, modulate_scale=0.4),
            scene.AddAsset("a glass wine decanter with stemmed wine glasses",
                           asset_id=_GLASS, modulate_scale=0.4),
        ])
        tasting.place_rug("a worn brown jute rug", size=0.75)   # <=0.8: frame the zone, not wall-to-wall

# ============================ LEFT + RIGHT long walls: the twin RACK RUNS ==============
# Loading the two LONG walls with continuous rack runs is what makes the shell read as a
# deep cellar corridor (library). Omit `facing` on the wall placement -> the heuristic turns
# the bottle faces into the room.
with scene.GridGroup(sparsity=0.03) as racks_left:
    racks_left.place_row(4 * scene.AddAsset("a tall dark wooden wine rack full of wine bottles",
                                            asset_id=_RACK))
with scene.GridGroup(sparsity=0.03) as racks_right:
    racks_right.place_row(4 * scene.AddAsset("a tall dark wooden wine rack full of wine bottles",
                                             asset_id=_RACK))

# ============================ BACK wall: the feature/collection wall ===================
# The plan's "continuous perimeter backdrop of storage" wants the racks to WRAP the room, so
# the back wall carries the hero rack too, not the _CAB bottle cabinet: _CAB's mesh has a
# bright white base drawer that reads as a blown-out rectangle in a dim cellar (an eye catch —
# the VLM loop was clean on it), and its shelves are sparser than the rack's four full tiers.
with scene.GridGroup(sparsity=0.06) as bottle_cabs:
    bottle_cabs.place_row(2 * scene.AddAsset("a tall dark wooden wine rack full of wine bottles",
                                             asset_id=_RACK))

# barrel cluster: a real cask is ~0.9 m tall; the mesh is 0.65 -> 1.35x (uniform).
with scene.RelativeGroup() as barrels:
    barrels.set_anchor(scene.AddAsset("an oak wine barrel with metal bands",
                                      asset_id=_BARREL, modulate_scale=1.35))
    barrels.place_on_right(scene.AddAsset("an oak barrel used as a display stand with bottles",
                                          asset_id=_BARRELD, modulate_scale=1.1))

# a low stack of crates — the weathered crate carries the wine crate (with bottles) on top,
# so the PRODUCT sits at the top of the stack rather than being hidden in a bin.
with scene.RelativeGroup() as crate_stack:
    crate_stack.set_anchor(scene.AddAsset("a weathered vintage wooden crate", asset_id=_CRATE))
    if PHASE >= 2:
        crate_stack.place_on_top(scene.AddAsset("a rustic wooden wine crate holding bottles",
                                                asset_id=_WCRATE))

# ============================ FRONT wall: the entry / service credenza =================
with scene.RelativeGroup() as credenza:
    credenza.set_anchor(scene.AddAsset("a rustic wooden wine credenza with a bottle lattice",
                                       asset_id=_CREDENZ))
    if PHASE >= 2:
        credenza.place_on_top(scene.AddAsset("a red wine bottle with two wine glasses",
                                             asset_id=_SERVICE, modulate_scale=0.35))

# ============================ ROOM ====================================================
# RoomProportions voted 0.8 in every phase (unidirectional, never flipping) and the render
# agreed the aisles were over-wide -> ONE decisive final-phase step to 0.9 rather than the
# full 0.8: the rack runs are fixed-size rows, and shrinking a wall-loaded shell too far
# overflows them (locker_room). Same value the library corridor settled on.
# The wall texture is NOT a wording problem: "old red brick wall" already embeds to a genuine
# deep-red brick (c71761a5, 0.68) — the pale render is the room-scale tiling + light budget
# washing it out, a renderer limit, so converge instead of re-wording (bakery lesson).
with scene.RoomGroup(modulate_scale=0.9, randomness=0.12) as room:
    room.place_walls(floor_texture="worn beige stone floor tiles",
                     ceiling_texture="rough grey stone",
                     wall_texture="old red brick wall")
    room.place_on_center(tasting)
    room.place_on_left_wall_center(racks_left)      # omit facing -> bottles face the room
    room.place_on_right_wall_center(racks_right)
    room.place_on_back_wall_center(bottle_cabs)
    room.place_on_back_wall_left(barrels)
    room.place_on_back_wall_right(crate_stack)
    room.place_on_front_wall_left(credenza)
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # The plan's "statement chandelier" is NOT buildable: add_lighting caps a fixture's height
        # at 1.5 m but pins its origin at the ceiling, so any hanging fixture drops into the room —
        # the caged/industrial query came back a huge Tiffany lamp swinging over the table.
        # A COMPACT FLUSH disc is the rule (executive_office); in a dim cellar it reads as nothing
        # but the light itself. density 0.01: a small fixture MULTIPLIES the count for a given
        # density, and ~32 m2 sits at the bottom of the small-room band (music_studio).
        room.add_lighting("a flat round bronze flush mount ceiling light", density=0.01)
        # art on the entry wall only: the long walls are full-height racks with no headroom,
        # and the front-centre slot is clear (credenza left, door right).
        room.place_on_wall_front_center(
            scene.AddAsset("a framed vintage wine advertisement print", width=0.8))

scene.export("wine_cellar_v1.blend")
