"""
Kitchen L — "Greige L-Kitchen with a Pocket Island" — the L-shaped counterpart of kitchen_set_v3.

Kunal's second island rule (2026-07-14, from the layout-ideas sheet): for an L-SHAPED kitchen the
island (or a dining piece) goes in the MIDDLE — inside the L's AABB, in the concave quadrant the
two runs don't occupy. That is `KitchenIslandGroup` mode "pocket": the footprint raster finds the
base run and the leg, bounds the empty pocket, centres the island in it (aligned with the base
run, facing the open room), and warns when the aisles drop under min_aisle.

Set: `future/b3e7e64f` — the most complete L in the pool (8/11: base+wall cabinets, cooktop,
oven, range hood, sink, countertop, microwave; warm-grey fronts). Gaps that matter: the FRIDGE
(filled below) and the island (this scene's point).

BUILD 1 FAILED — the fridge must NOT be composed into the analysed run. The first build anchored
a GridGroup row [fridge | set] on the theory that the fridge should flush-extend the back run.
Two independent failures, both now standing rules:
1. **The camera bound scales with the RUN, and a composed run breaks it.** The back-wall-centre
   camera clears a wall-flush run only when W > 2 x run width (kitchen.md's bound). The set
   alone is ~2.9 m (bound ~5.8 m — achievable); with the fridge the run was 4.11 m (bound 8.2 m —
   never happens) and the FRONT view rendered solid black, exactly v1-of-v2's blinded camera.
2. **A depth-mismatched module rasters the run RAGGED.** The fridge is deeper than the cabinetry,
   so the composed back border's coverage fell to 0.79, the base-run detection flipped to the leg
   (base=+x), and the island+stools laid out rotated 90 degrees from the design. (The classifier's
   base threshold is now 0.75 with a most-arms/longest-span tie-break, but don't lean on it —
   compose runs from EQUAL-DEPTH modules only.)
So the fridge stands alone in the back-LEFT corner: a corner is camera-safe by construction
(cameras sit at wall CENTRES), and a lone tall appliance in a corner still reads as the cold
zone of an open kitchen.

Alignment (kitchen.md): an L goes in the corner its leg points into — this leg is at +x, so
back-RIGHT corner, leg flush along the right wall, facing="front", is_static. The set is scaled
to 2.3 m height (not 2.4+): the run width follows height, and 2.3 keeps the back-camera bound
W > 2 x 2.91 = 5.82 m inside what this room's slot occupancy actually produces. Window on the
LEFT wall (opposite the corner). Dining nook front-left, door front-right.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces (EMPTY by design) / 3 walls+mood

scene = SceneProgRoom("KitchenLV1", seed=7)

KITCHEN_SET = "future/b3e7e64f-417f-4da5-b4ce-cb2bfd06e039"   # warm-grey L, hood+oven+sink+micro
FRIDGE = "future/a266bc1f-0685-3080-beeb-b09d60a4f5ca"        # stainless side-by-side, legible
ISLAND = "hssd/559f21c7f5628a83b31d616e90bdcc02e7744731"      # walnut shaker base cab, WHITE MARBLE top
STOOL = "hssd/609af80af4fb45e772a2109a7a4876b73601fb6b"       # light wood slat-back counter stool
TABLE = "future/9ff76d8d-af20-493d-a17c-a4aaaa94114a"         # light oak dining table, BARE top
CHAIR = "hssd/24fd37914321b915b9503d25add09332900a8d61"       # light wood classic dining chair

scene.prefetch_assets([
    "a complete fitted kitchen unit with grey cabinets and integrated appliances",
    "a tall stainless steel side-by-side refrigerator",
    "a dark walnut kitchen island with a white marble countertop",
    "a light wood counter stool with a slatted backrest",
    "a warm brass dome pendant light",
    "a flat round LED flush mount ceiling light",
    "a tall leafy potted plant in a woven basket",
    "a framed botanical print in a light wood frame",
    "a light oak rectangular dining table",
    "a light wood classic dining chair",
    # rework 2026-07-14 (Kunal: too sparse + lonely plant behind the dining): CAMERA-SAFE fill
    # only — a dining rug + pendant + a wall-art pair; the plant moves to the front-left corner.
    "a flat woven jute area rug in warm cream tones",
])

# --- the SET: scaled BY HEIGHT — and the HEIGHT is the CAMERA lever, sized 2.1 m ----------------
# Build 4 (set 2.3 m -> run 2.91 m, shell 0.90) measured the trap exactly: interior W came out
# 5.70, the run spanned x[2.79, 5.70], and the back-wall-centre camera at x = W/2 = 2.85 sat
# 6 cm INSIDE the run's full-height larder column -> the front view rendered solid black. A
# wall-flush run whose inner end is TALL must satisfy  run <= W/2 - 0.3  (the camera cannot see
# over a full-height column, so it needs real lateral clearance). Growing W means an empty barn
# the VLM votes against forever; the honest lever is the SET's height — run width follows it
# (w ~ 1.27 x h for this mesh). 2.1 m is a real kitchen's upper-cabinet line and puts the run at
# ~2.66 m, clearing the camera by ~0.25 m at the 0.95 shell.
kitchen = scene.AddAsset("a complete fitted kitchen unit with grey cabinets and integrated appliances",
                         asset_id=KITCHEN_SET)
kitchen.scale(kitchen.get_width() * 2.1 / kitchen.get_height())

# --- the ISLAND UNIT: walnut+marble counter + its pendant, one rigid piece ----------------------
island = scene.AddAsset("a dark walnut kitchen island with a white marble countertop",
                        asset_id=ISLAND, width=1.2)
with scene.AroundGroup(sparsity=0.0, jitter=0.0) as island_unit:
    island_unit.set_anchor(island)
    if PHASE >= 3:
        island_unit.add_lighting("a warm brass dome pendant light", density=0.0)  # exactly one

# --- the KITCHEN ZONE: L set + pocket island + stools, ONE corner-aligned block -----------------
with scene.KitchenIslandGroup() as kz:
    kz.set_anchor(kitchen)
    # mode auto -> "pocket" for an L: the island floats in the concave middle of the L's AABB,
    # long axis parallel to the base run, stools on the outward (room) face. Floor mass -> phase 1
    # ALWAYS (the floor-mass gating rule). Judge any aisle warnings against the render.
    kz.place_island(island_unit)
    kz.place_stools(2 * scene.AddAsset("a light wood counter stool with a slatted backrest",
                                       asset_id=STOOL))
kz.is_static = True   # corner ops are never re-pinned; pin the block flush (kitchen.md trap 2)

# --- the FRIDGE: standalone, back-LEFT corner (camera-safe; see the docstring) ------------------
fridge = scene.AddAsset("a tall stainless steel side-by-side refrigerator", asset_id=FRIDGE)

# --- the DINING nook: front-left, the second open-plan zone -------------------------------------
# Rework 2026-07-14: a jute rug grounds the nook (phase 2) and a brass pendant hangs over it
# (phase 3, density=0 -> exactly one) — the open-plan floor read too bare with only a bare table.
with scene.AroundGroup(sparsity=0.05, jitter=0.15) as dining:
    table = scene.AddAsset("a light oak rectangular dining table", asset_id=TABLE, width=1.3)
    dining.set_anchor(table)
    chairs = 4 * scene.AddAsset("a light wood classic dining chair", asset_id=CHAIR)
    dining.place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])
    if PHASE >= 2:
        dining.place_rug("a flat woven jute area rug in warm cream tones", size=0.9)
    if PHASE >= 3:
        dining.add_lighting("a warm brass dome pendant light", density=0.0)

# --- the corner plant (greenery, moved to the front-LEFT corner) --------------------------------
# Rework 2026-07-14 (Kunal: too sparse + this plant floated oddly BEHIND the dining). FIRST attempt
# added a serving-console vignette on the front wall to fill the floor — it BLINDED the back-wall-
# centre camera (the back view rendered solid black): a console is FLOOR MASS, and adding a floor
# slot to a set-piece kitchen re-triggers the camera bound the whole scene is built around
# (kitchen.md). Lesson: a camera-bound kitchen is furnished with NON-FLOOR elements only — the nook
# rug, the pendant, and wall art (below) — never a new floor piece. The plant just moves to the
# front-left CORNER (corners are camera-safe by construction) so it reads intentional, not stranded.
plant = scene.AddAsset("a tall leafy potted plant in a woven basket")

# modulate_scale=0.95 — ONE decisive application against the 0.82 -> 0.7 vote train (signal:
# unidirectional and worsening), bounded by the camera arithmetic above: at 0.95 the interior
# W lands ~5.8-6.0 and the 2.66 m run's tall inner column stays ~0.25 m clear of the back-wall-
# centre camera. Builds 3 (0.85) and 4 (0.90, set 2.3) both went below the bound and the front
# view rendered SOLID BLACK — the shrink votes are refused on that arithmetic; the remaining
# "empty" floor is open-plan circulation (garage/corridor's effect).
with scene.RoomGroup(modulate_scale=0.95, randomness=0.0) as room:
    # sage + oak grounds the warm-grey fronts (bathroom's saturated-mid-tone rule keeps an
    # appliance-heavy room from blowing out to white under the window).
    room.place_walls(floor_texture="light oak wood plank floor",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="soft sage green painted plaster wall")

    # L goes in the corner the leg points into: leg at +x -> back-RIGHT corner, leg along the
    # right wall. facing MANDATORY; the block is is_static (corner ops are never re-pinned).
    room.place_on_back_right_corner(kz, facing="front")

    room.place_on_back_left_corner(fridge, facing="front")   # the cold zone, camera-safe corner
    room.place_on_front_left(dining, facing="back")
    room.place_on_front_left_corner(plant, facing="front")   # greenery, a camera-safe corner
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        room.place_window_standard("left_wall", position="center",
                                   curtain="white linen roman shade")
        # wall art breaks up the bare sage walls WITHOUT adding floor mass (camera-safe interest):
        # a botanical PAIR on the front wall (centre + left, over the nook) instead of one lone print
        room.place_on_wall_front_center(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        room.place_on_wall_front_left(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        # Builds 2-3 lint: 38 then 11 fixtures — a STARFIELD. Same call as v3 (0.4 scale, 0.01),
        # but the picker (seed 7) chose a TINY disc and max_lights = area/footprint exploded.
        # Lobby's rule: ENLARGE the fixture (shrinks max_lights quadratically), don't just drop
        # density. From the observed point (N=11 at density .02 / scale 1.0 -> max_lights ~500),
        # scale 2.0 quarters that -> ~4 fixtures, under the ~8 budget for 28 m^2.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.02,
                          modulate_scale=2.0)

scene.export("kitchen_l_v1.blend")
