"""Nursery — "Sunlit Pastel Nursery" (guided-flow build; plan: tmp/plan_A_warm__sunlit_nursery_room_for_).

Design brief (planner): the crib is the sleeping anchor; a wide dresser doubles as the changing
station with a round mirror above; a caregiver cluster (rocking chair + knit pouf + side table with
a lamp) sits on a plush rug by the window; low, child-accessible toy storage; a plant and framed
pastel art; warm daylight. Palette: white/cream + light wood + soft blush pastels.

Layout (residential single-room, kid-scale — the bedroom hero + children_room zoning recipes):
- BACK wall  = SLEEP: the crib hero, with the pastel floral print hung above it (wall-hung art and
  wall-adjacent floor furniture occupy independent slots — the living_room_cozy hearth+gallery
  pattern). The crib carries the room's single flush ceiling fixture.
- LEFT wall  = the WINDOW (picture, sheer curtains) + the caregiver nook in front of it: rocker,
  pouf at its feet, side-table-with-lamp unit, all grounded on an ivory shag rug. The plant stands
  in the back-left corner, by the window (the plan's vertical accent).
- RIGHT wall = CHANGE: the dresser/changing station (folded linens + a basket ON it — an empty
  dresser reads as a bedroom, not a nursery: the jewelry_shop product rule), round mirror above.
- FRONT wall = PLAY/STORE: low cubby with baskets INSIDE and soft toys ON TOP; door on the right;
  the pastel geometric print on the centre.
- Centre floor is left open on purpose — it is the play/circulation space the category exists for
  (garage's "a legitimate open lane reads as empty to the occupancy metric").

Every fixture is kid-scale (crib 1.04 m, dresser 0.95 m, cubby 0.91 m, rocker 0.99 m) so nothing
reaches the ~1.4-1.5 m interior wall cameras — the kindergarten lesson, applied preventively: no
blinded view, and hence no hallucinated rotation storm (bakery).

Assets: every pin below was eyeballed at the audit gate and its real-world size verified OFFLINE
with get_whd() before the first build (hospital_room / garage rule). Notable catches:
- the dresser loads only 0.80 m wide (a nightstand) -> height-fit uniformly to a 0.95 m changing
  dresser via scale(w*H/h);
- the picker's rank-1 nursery "animal print" is a row of framed INSECT SPECIMENS, and another
  candidate previews as a blank rectangle (the empty-frame trap) -> pinned two prints with real,
  soft artwork instead;
- baby MOBILES exist in the dataset (a whole CeilingObjectRetriever pool) but every one is 0.36-2.80 m
  DEEP -- far past the ~0.25 m wall-hang limit -- and the DSL has no ceiling-hang verb for a
  non-luminous object (add_lighting would make the mobile EMIT). Dropped; logged as a DSL gap.

Beds/cribs are "set assets" — the mesh comes fully DRESSED (mattress included), so nothing is
placed on or in the crib.

Phase-gated (IDSDL/phases.py): --phase 1 = floor anchors (~1 min layout check); 2 adds surface
dressing; 3 adds walls/window/lighting.
"""
import os

# EXPOSURE — set BEFORE importing IDSDL (the renderer binds the sky at import time).
# The first full build came back BLOWN OUT to pure white: a big picture window + the default
# INTERIOR_SKY_STRENGTH of 3.0, bouncing around a room whose walls, floor, crib, rocker, rug and pouf
# are all white/cream — every surface is a reflector, so the pastel envelope washed out completely.
# Brightness is a SKY setting, never an add_lighting one (add_lighting spends a FIXED 500 W split
# across N fixtures, so density buys more/dimmer lamps, never a brighter room — greenhouse).
# 1.2 keeps the room daylit and "sunlit" while letting the blush walls hold their colour.
# NOTE: the MCP `run_scene` tool IGNORES this line — its server has already imported the renderer, so
# the constant is bound before this executes. Build this scene from the SHELL
# (`python workbench.py run scenes/work/nursery.py`) or you will chase a mood the renders can't show.
os.environ.setdefault("IDSDL_SKY", "1.2")

from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Nursery", seed=12)

# --- pinned assets (previews eyeballed at gate 3; dims verified offline with get_whd) ---
CRIB    = "hssd/dea27cd0e303f87744985853c3c431732801bfec"   # white slatted 4-sided crib, 1.40x1.04x0.78 (true scale)
DRESSER = "hssd/d15420918c690dbe0c1e62db3e69a94db6ad109a"   # natural wood dresser, FLAT white top (loads 0.80 m wide)
ROCKER  = "hssd/xxxxdce8237exec05x4143xaf75xbd77fb6c94cd"   # cream high-back nursery glider on wooden rockers
CUBBY   = "hssd/56813e3f4a3d0ee408bf5aa9e7b4fe4d0bcbb288"   # low light-wood cubby unit, open compartments
POUF    = "hssd/eb1fbd5c7e9bcb4166c60fc016627ab8c23c396a"   # cream chunky-knit round pouf
RUG     = "hssd/8d0a5a5d529b1dc36187ca8360a4c122476bf027"   # ivory shag rug (flat, 0.01 m — no slab)
ART_FLO = "hssd/107b95a36ee015115b16bdf38934b3ef2df94452"   # pastel blue/pink watercolour floral (real artwork, 0.03 m deep)
ART_GEO = "hssd/b875ecb880fc97f65f6f770c4820dc8b6e4022e9"   # pastel geometric print, wood frame (0.02 m deep)
MIRROR  = "hssd/95e382d31b12e57aab88caeff004bf8a003baee8"   # plain round wall mirror, thin rim
LINENS  = "future/e888199b-7663-41a0-8384-81b5aefa7bd1"     # folded stack of textiles (the changing-station prop)
TEDDY   = "future/3e18ed6d-9f79-46cf-afe7-ac2a3512570d"     # beige plush teddy bear
PLUSH2  = "hssd/567ba453e60735e7667f25ea6d09377be18bda66"   # pastel plush bear w/ a pink heart (see the bunny note)
BASKET  = "future/76d01ea8-8c8c-44f5-bee2-80ebf6d57672"     # woven wicker storage basket
STABLE  = "hssd/2d3df1dcb067da43f85411fe601f24bb38d268a8"   # round white-top wooden PEDESTAL side table

scene.prefetch_assets([
    "a modern table lamp with a warm fabric shade",
    "a leafy potted plant in a ceramic planter",
    "a flat round LED flush mount ceiling light",
    "a woven seagrass storage basket",
])

# --- Phase 1 majors ---
crib = scene.AddAsset("a white wooden baby crib", asset_id=CRIB)

# The dresser loads at 0.80 x 0.76 x 0.43 m — a nightstand, not the plan's wide changing dresser.
# Height-fit it UNIFORMLY to ~0.95 m (a real changing-height dresser); aspect is preserved, so it
# comes out ~1.0 m wide. (Uniform, never width= alone — the children_room squash lesson.)
dresser = scene.AddAsset("a wide light wood baby changing dresser with drawers", asset_id=DRESSER)
dresser.scale(dresser.get_width() * 0.95 / dresser.get_height())

rocker = scene.AddAsset("a cream upholstered nursery rocking chair glider", asset_id=ROCKER)
cubby  = scene.AddAsset("a low light wood kids cubby storage shelf", asset_id=CUBBY)
plant  = scene.AddAsset("a leafy potted plant in a ceramic planter")

# --- the side table + its lamp as ONE unit: the TABLE must be the anchor, because place_on_top
# seats items on the group's ANCHOR — putting the lamp straight into the nook group (anchor = the
# rocker) would sit it on the CHAIR'S CUSHION (living_room_cozy v3). ---
# (phase-2 catch: the unpinned "small round light wood side table" resolved to a 1.20 x 0.55 m COFFEE
#  table that dwarfed the rocker beside it — and its coffee-table PROPORTIONS mean no amount of scaling
#  rescues it. Swapped the mesh for a genuine pedestal table and height-fit it to 0.60 m, so it sits at
#  the rocker's armrest.)
side_table = scene.AddAsset("a small round pedestal side table", asset_id=STABLE)
side_table.scale(side_table.get_width() * 0.60 / side_table.get_height())
with scene.RelativeGroup() as side_unit:
    side_unit.set_anchor(side_table)
    if PHASE >= 2:
        side_unit.place_on_top(scene.AddAsset("a modern table lamp with a warm fabric shade"))

# --- caregiver nook: rocker + pouf at its feet + the lamp-topped side table, on a plush rug ---
with scene.RelativeGroup() as nook:
    nook.set_anchor(rocker)
    nook.place_on_front_adjacent(scene.AddAsset("a chunky knit round floor pouf ottoman",
                                                asset_id=POUF))
    nook.place_on_left(side_unit)
    if PHASE >= 2:
        # the rug grounds the READING corner (place_rug sizes relative to the GROUP bbox, so it
        # belongs on the cluster, not on the crib — a crib-sized rug would vanish under the crib)
        nook.place_rug("a soft cream plush shag area rug", size=0.9, asset_id=RUG)

# --- the changing station: an EMPTY dresser reads as a bedroom. The folded linens + basket ON the
# top are what make it a changing table (the jewelry_shop product rule). ---
with scene.RelativeGroup() as dresser_grp:
    dresser_grp.set_anchor(dresser)
    if PHASE >= 2:
        dresser_grp.place_on_top([
            scene.AddAsset("a folded stack of soft baby blankets and towels", asset_id=LINENS),
            scene.AddAsset("a woven seagrass storage basket", asset_id=BASKET),
        ])

# --- toy storage: baskets tucked INSIDE the compartments, soft toys styled ON TOP ---
with scene.RelativeGroup() as cubby_grp:
    cubby_grp.set_anchor(cubby)
    if PHASE >= 2:
        cubby_grp.place_inside(3 * scene.AddAsset("a woven seagrass storage basket",
                                                  asset_id=BASKET))
        # Both plushes are PINNED. The unpinned "a plush stuffed bunny toy" resolved to a 0.60 x 0.68 x
        # 0.12 m FLAT SLAB with a blank description — it rendered as a cardboard box standing on the
        # cubby, and the whole VLM loop stayed clean through it (geometry is fine; "that is not a bunny"
        # is semantics). The kindergarten crayon-cup rule: only place a prop you have VERIFIED.
        cubby_grp.place_on_top([
            scene.AddAsset("a plush teddy bear soft toy for a nursery", asset_id=TEDDY),
            scene.AddAsset("a pastel plush bear toy with a pink heart", asset_id=PLUSH2),
        ])
        # Vibe layer: a floor toy basket beside the storage run. It fills the bare play floor with
        # actual baby PRODUCT — the documented answer to a mild persistent shrink vote is to FILL the
        # floor, not shrink further (children_room/kindergarten). It lives IN the cubby group, not in a
        # room floor slot: a slot would let door-clearance + randomness strand it mid-room, and a lone
        # basket in open floor is an island, not a play corner (kindergarten).
        cubby_grp.place_on_right(scene.AddAsset("a woven wicker basket with a draped blanket",
                                                asset_id="future/9f1cfe06-b99a-4b9e-93e2-21571589b0f0"))

# --- HERO: the crib (a set asset — fully dressed; nothing goes on or in it) + the room's light ---
with scene.RelativeGroup() as crib_group:
    crib_group.set_anchor(crib)
    if PHASE >= 3:
        # ONE compact FLUSH fixture (density=0). Never a hanging mobile/chandelier here: add_lighting
        # caps height at 1.5 m but pins the origin at the ceiling, so a tall fixture dangles into the
        # room AND its emissive mesh blows out the exposure (executive_office). Brightness itself is a
        # SKY setting, not an add_lighting one — the "sunlit" brief is delivered by the window.
        crib_group.add_lighting("a flat round LED flush mount ceiling light", density=0)

# --- Phase 3 wall art: pre-scale FLAT prints small — place_on_wall_* derives the mount height from
# the art's UN-scaled height, so a big print hangs too high (bedroom/children_room). Both were picked
# by eye for visible artwork: the picker's rank-1 "nursery animal print" is a row of framed INSECT
# SPECIMENS, and its runner-up previews as a blank rectangle. ---
art_floral = scene.AddAsset("a framed pastel watercolour floral print", asset_id=ART_FLO)
art_geo    = scene.AddAsset("a framed pastel geometric print for a kids room", asset_id=ART_GEO)
art_floral.scale_only_width(0.55); art_floral.scale_only_height(0.70); art_floral.scale_only_depth(0.03)
art_geo.scale_only_width(0.50);    art_geo.scale_only_height(0.70);    art_geo.scale_only_depth(0.03)

with scene.RoomGroup(modulate_scale=0.8, randomness=0.15) as room:
    # Room size: the shell auto-sized to 6.44 x 4.85 m = 31 m² — a hall, not a nursery (a real one is
    # ~12-16 m²), and phase 1 voted `rescale room by 0.75`. Acting in phase 1 (rather than holding to
    # the final phase) is deliberate: the hold-early rule exists because occupancy CLIMBS as furniture
    # lands, but phases 2-3 here add only surface dressing and wall art — zero floor furniture — so the
    # vote cannot move. Calibrated by eye over cheap phase-1 builds (kitchen_set). Kept slightly ABOVE
    # the vote: the open centre floor is the play/circulation space the category exists for, and that
    # reads as "empty" to an occupancy metric (garage/corridor/operating_room).
    #
    # Textures resolved OFFLINE against the caption library before building (office_modern's 5-s rule):
    # "soft blush pink painted wall" matches pink bathroom TILES (a tiled nursery), and a literal
    # "pale pink painted plaster" matches a PEACH swatch that rendered as strong SALMON at room scale.
    # This wording matches a desaturated dusty-blush plaster that holds as a true pastel.
    room.place_walls(floor_texture="light oak wood plank floor",
                     ceiling_texture="smooth white painted plaster wall",
                     wall_texture="very pale barely-there pink white wall, almost white")

    # Phase 1 — floor anchors. No `facing` on the wall placements: the default heuristic already
    # turns each piece INTO the room (drawers/cubbies reachable).
    room.place_on_back_wall_center(crib_group)     # SLEEP hero
    room.place_on_right_wall_center(dresser_grp)   # CHANGE station
    room.place_on_left_wall_center(nook)           # the nook is a CORNER, not an island: a floor slot
                                                   # would let door-clearance + randomness strand the
                                                   # cluster mid-floor (kindergarten)
    room.place_on_front_wall_left(cubby_grp)       # STORE (door takes the front-right slot)
    room.place_on_back_left_corner(plant)          # vertical accent, by the window
    room.place_door("front_wall", position="right")   # in phase 1: its clearance shapes the solve

    # a dresser has a drawer swing + you stand at it to change a baby
    room.add_clearance(dresser, distance=0.6, dir="front")

    if PHASE >= 3:
        # wall-hung: art over the crib, mirror over the dresser, geometric print on the front wall.
        # Each sits ABOVE the top of the furniture below it (crib 1.04 / dresser 0.95 m vs a ~1.5 m
        # mount centre), so the automatic wall-object-clearance pass has no occluder to slide away.
        room.place_on_wall_back_center(art_floral)
        room.place_on_wall_right_center(scene.AddAsset("a round wall mirror with a thin gold frame",
                                                       asset_id=MIRROR))
        room.place_on_wall_front_center(art_geo)
        # The big sunlit window — glaze freely: the "black void" was a renderer BUG and is fixed
        # (greenhouse). It goes on the LEFT wall, opposite the changing wall, so daylight rakes ACROSS
        # the room and backlights nothing; the left wall carries no wall-hung item, so no slot clash.
        room.place_window_picture("left_wall", curtain="white sheer linen curtains")

scene.export("nursery.blend")
