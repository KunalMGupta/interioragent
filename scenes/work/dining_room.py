"""Warm, lived-in family dining room — guided-flow build
(plan: tmp/plan_A_warm__lived_in_family_dining_r, "Warmth-Centered Family Dining Ensemble").

Layout = the meeting_room skeleton in its residential home key: a rectangular table ringed
by a rectilinear chair ring is the hero, one long wall is the SERVICE wall (sideboard + a
gallery hung above it), the opposite wall is DAYLIGHT (window + drapes), the short walls stay
light (art / door) so the interior cameras keep clear views.

- CENTER  = the dining cluster: a dark trestle table stretched to 2.2 m, 8 upholstered chairs
            (3 per long side + 1 each end), jittered so the seating reads used rather than
            CAD-perfect, grounded on a flat wool rug, lit by ONE drum pendant. The table is
            SET (plates + glassware + a floral centerpiece) — a set table is what makes the
            room read as a DINING room instead of "a table with chairs" (jewelry_shop's
            product rule: the category is carried by the product on the surface).
- BACK    = the service wall: the low warm-wood buffet, the framed gallery collage above it,
            a tall plant and the warm floor lamp in the two corners.
- LEFT    = floor-to-ceiling window + cream linen drapes (windows render DAYLIGHT since the
            greenhouse renderer fix — the old "black void" workarounds are obsolete).
- RIGHT   = a framed landscape.   FRONT = the door.
- Lighting: the table's drum pendant ONLY (density=0). No room-wide fixtures — the glazed
  wall supplies the ambient, and `density` buys more/dimmer fixtures, never a brighter room.

Heroes pinned + measured offline with get_whd() BEFORE the first build:
  table 1.50x0.82x0.82 -> width=2.2 (stretch the TOP only; keeps a real 0.82 m height)
  chair 0.50 wide      -> 3 per long side fits 2.2 m with room to pull back
  buffet 1.50x0.67x0.35 -> scaled BY HEIGHT to ~0.85 m (a real buffet height, and still far
                          under the ~1.4 m interior-camera eyeline at the back-wall centre)
  gallery 1.50x1.66 -> pre-scaled to ~0.95 m high: hung at the 1.5 m slot centre, a 1.66 m
                       collage's bottom edge lands at 0.67 m, BELOW the 0.85 m buffet top,
                       which fires the wall-object-clearance pass and slides the buffet
                       sideways off its own wall. Scaled down, its bottom sits ~1.02 m — clear.

Phase-gated (IDSDL/phases.py): --phase 1 = floor anchors only (~1 min layout check);
phase 2 adds the surface dressing; phase 3 adds walls/window/lighting/mood.
"""
import os

# ---------------------------------------------------------------------------------------------
# BUILD THIS SCENE AS:   IDSDL_SKY=1.5 python workbench.py run scenes/work/dining_room.py
# ---------------------------------------------------------------------------------------------
# The interior sky is the ONLY brightness lever (add_lighting splits a FIXED 500 W across N
# fixtures, so density buys more/dimmer fixtures, never a brighter or dimmer room). At the default
# 3.0 the beige walls wash to near-white and the "warm, lived-in" brief renders as a bright
# showroom; 1.5 keeps the daylight the plan wants while letting the wood, the beige and the
# pendant's pool read warm.
#
# It MUST be exported in the SHELL. `renderer/utils.py` binds INTERIOR_SKY_STRENGTH in a CLASS
# BODY at import time, and BOTH runners import IDSDL before they execute this file (workbench.py
# imports IDSDL.service at its own line 30, then runpy's the program; the MCP server is warm long
# before) — so the setdefault below is already too late under either, and a render that "ignored"
# your sky is a render still at 3.0. It is kept only for `python scenes/work/dining_room.py`,
# where nothing has imported IDSDL yet. (Refines wine_cellar v1, which prescribed the shell but
# set the var in the program — that is a no-op under workbench too, not just under MCP.)
os.environ.setdefault("IDSDL_SKY", "1.5")

from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("DiningRoom", seed=6)

# The pendant, not the sky, was washing this room out. MEASURED across builds (mean pixel value of
# the same view): dropping the sky 3.0 -> 1.5 moved a PHASE-1 render 139 -> 105 (sky is the only
# light there) but a FULL render only 197 -> 188 — because phase 3 adds add_lighting, whose fixed
# 500 W point light then DOMINATES a ~20 m2 room and flattens every surface to near-white. So on a
# room with a single fixture the brightness dial is the BUDGET, not the sky: 500 W -> 180 W lets
# the pendant read as a warm pool over the table while the glazed wall still supplies the daylight.
# (wine_cellar's dim-room recipe, arrived at from the bright side — and its warning holds: tune ONE
# dial at a time, or the sky and the wattage cancel and you conclude the lever is broken.)
scene.light_budget = 180.0

# --- pinned assets (every preview eyeballed at the audit gate) ---
TABLE       = "hssd/66602a70ec1d7612db667b49f530c85a87600b47"   # dark wood trestle dining table, BARE top (no baked-in chairs)
CHAIR       = "hssd/6c368c154ec8d7c649a89d2f2adda4f08b9f878e"   # beige upholstered high-back chair, wooden legs (carries the palette)
SIDEBOARD   = "future/ef3867e2-995e-4490-b3c3-260c75d8f80b"     # long LOW warm-wood buffet, flat top, tapered legs
RUG         = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"   # flat beige wool rug (known-flat — no slab)
GALLERY     = "future/e2b0dcb4-c660-415b-8b1e-cddeb905441b"     # framed collage WITH real photo content, front-correct
LANDSCAPE   = "hssd/4192b93682edc3c5585701c1ba90a34e9fd2f75b"   # framed landscape painting
CENTERPIECE = "hssd/3a30a28972253be16cf15f50c3e59440a2aba520"   # spring flowers in a white round vase
PLATES      = "hssd/f54404265057174a0daa5fb6d4d59610d6d13f15"   # stack of white ceramic dinner plates
GLASSWARE   = "hssd/a9d615bcd75af8e73df80fe7df1c64c938fa21ae"   # wine glasses + decanter set

scene.prefetch_assets([
    "a rectangular dark wood dining table",
    "an upholstered fabric dining chair with a high back",
    "a long low wooden sideboard buffet",
    "a low floral centerpiece in a vase",
    "a stack of white ceramic dinner plates",
    "a set of wine glasses and a decanter",
    "a white ceramic vase with branches",
    "a warm brass floor lamp with a fabric shade",
    "a tall leafy potted plant in a ceramic planter",
    "a flat beige wool area rug",
    "a round drum shade pendant ceiling light",
])

# --- Phase 1: the dining cluster — table + a rectilinear ring of 8 chairs -------------
# place_rectilinear (NOT place_circle): a circle flings chairs into a ring wider than a
# rectangular table and RoomGroup then grows the shell to fit that bbox (the kitchen v1
# cavernous-room bug). Tight sparsity + modest jitter = lived-in, not inflated.
with scene.AroundGroup(sparsity=0.1, jitter=0.25) as dining:
    table = scene.AddAsset("a rectangular dark wood dining table", asset_id=TABLE, width=2.2)
    dining.set_anchor(table)
    long1 = 3 * scene.AddAsset("an upholstered fabric dining chair with a high back", asset_id=CHAIR)
    long2 = 3 * scene.AddAsset("an upholstered fabric dining chair with a high back", asset_id=CHAIR)
    ends  = 2 * scene.AddAsset("an upholstered fabric dining chair with a high back", asset_id=CHAIR)
    dining.place_rectilinear(longer_side1=long1, longer_side2=long2,
                             shorter_side1=[ends[0]], shorter_side2=[ends[1]])

    if PHASE >= 2:
        # THE SET TABLE — the anchor is the table, so place_on_top seats these on the table
        # top (always ask "what is this group's anchor?" — living_room_cozy v3's lamp-on-the-
        # chair bug). Sizing is the tournament's job: modulate_scale is a NO-OP on on-top items.
        dining.place_on_top([
            scene.AddAsset("a low floral centerpiece in a vase", asset_id=CENTERPIECE),
            scene.AddAsset("a stack of white ceramic dinner plates", asset_id=PLATES),
            scene.AddAsset("a set of wine glasses and a decanter", asset_id=GLASSWARE),
        ])
        dining.place_rug("a flat beige wool area rug", size=0.8, asset_id=RUG)
        # size<=0.8 under a room-dominating cluster: at 1.0 the rug reads as wall-to-wall
        # carpet instead of defining the dining zone (living_room_cozy).

    if PHASE >= 3:
        # ONE drum pendant over the table. A fabric drum has a small emissive area and a short
        # drop — a tall/globed chandelier hangs ~1.5 m into the room and blows the exposure out
        # (executive_office). density=0 = a single fixture; add_lighting takes no asset_id, so
        # the query is worded to make the audited drum shade the top pick.
        dining.add_lighting("a round drum shade pendant ceiling light", density=0)

# --- the buffet as a dressed UNIT: anchor = the buffet, so its top gets the props ------
buffet = scene.AddAsset("a long low wooden sideboard buffet", asset_id=SIDEBOARD)
buffet.scale(buffet.get_width() * 0.85 / buffet.get_height())   # uniform fit to a real ~0.85 m buffet height
with scene.RelativeGroup() as service:
    service.set_anchor(buffet)
    if PHASE >= 2:
        service.place_on_top([
            scene.AddAsset("a white ceramic vase with branches"),
            scene.AddAsset("a stack of white ceramic dinner plates", asset_id=PLATES),
        ])

# --- the room -------------------------------------------------------------------------
with scene.RoomGroup(randomness=0.15) as room:
    # floor: "dark brown hardwood" matches a genuinely warm oak; "warm oak wood plank floor"
    # matches a SALMON-PINK plank in the texture library (kitchen_set v2 — verified offline).
    # Wall/ceiling strings take ONE colour + material: an accent clause recolours every wall.
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="smooth white plaster",
                     wall_texture="solid warm beige smooth uniform wall")
    # texture strings are matched against CAPTION text — word them like a caption, not a paint
    # chip. Verified OFFLINE against wall_textures_embeddings.npz (office_modern's 5-second rule,
    # never an 8-minute build): "warm greige painted wall" matched a LIGHT GRAY plaster at 0.596
    # (hence the cool, un-warm v1 walls); this wording matches a genuine solid beige at 0.744.

    room.place_on_center(dining, facing="front")
    room.place_on_back_wall_center(service)          # service wall (default facing = into the room)
    room.place_door("front_wall", position="left")   # in phase 1: its clearance shapes the solve

    if PHASE >= 3:
        # the gallery hangs ABOVE the buffet — pre-scaled so its bottom edge clears the
        # buffet top (see the header note); wall art and wall-adjacent floor furniture
        # occupy independent slots, so this stacks cleanly.
        gallery = scene.AddAsset("a gallery wall of framed pictures", asset_id=GALLERY)
        gallery.scale_only_width(1.30); gallery.scale_only_height(0.95); gallery.scale_only_depth(0.04)
        room.place_on_wall_back_center(gallery)

        landscape = scene.AddAsset("a framed traditional landscape painting", asset_id=LANDSCAPE)
        landscape.scale_only_width(1.1); landscape.scale_only_height(0.75); landscape.scale_only_depth(0.04)
        room.place_on_wall_right_center(landscape)

        # daylight rakes across the room from the long left wall; the drapes carry the plan's
        # cream textile layer (a palette accent belongs on a PROP, not in a texture string).
        room.place_window_floor_to_ceiling("left_wall", curtain="cream linen drapes")

        # corners only — nothing tall at a wall CENTRE, where the interior cameras sit (~1.4 m)
        room.place_on_back_right_corner(
            scene.AddAsset("a tall leafy potted plant in a ceramic planter"))
        room.place_on_back_left_corner(
            scene.AddAsset("a warm brass floor lamp with a fabric shade"))

scene.export("dining_room.blend")
