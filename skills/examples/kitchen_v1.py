"""
Kitchen — "Warm Marble Kitchen with Blue Panel Rhythm and Social Prep-to-Dine Flow" (planner-driven).

Plan (Phase 0): a warm palette of cream walls, light wood and marble surfaces, with a DARK cabinetry
run adding depth and vertical rhythm; a range under an open zone; glass-front upper cabinetry; a tall
blue-panel pantry defining the utility zone; a light-wood dining corner at the edge of the workflow;
brass pendants over the work zone; greenery and tactile props (wicker basket, ceramic pitcher).

Procedural signature (retrieved): a residential kitchen is a CONTINUOUS SERVICE RUN on the long wall
plus a facing work ANCHOR. So:
- BACK (long, hero) wall : the cook run as ONE rigid GridGroup row — base cab | range | base cab —
                           flush on the wall (laundromat's machine-row pattern: a heavy linear run of
                           modules is one floor slot, not a queue of separate wall items).
- ABOVE the run         : the chimney hood over the range + two glass-front upper cabinets.
- CENTER                : the marble-top island + a pair of counter stools + the brass pendants
                          (bar.md's counter + stool-row spine).
- LEFT wall             : the sink unit under a standard window (the plan's "brass faucet under a
                          generous window"), herb pot and canisters on its ledge.
- RIGHT wall            : the cold/dry storage block — stainless fridge + the blue-panel pantry.
- FRONT-LEFT            : the dining corner (light oak table + 4 chairs, AroundGroup).
- FRONT wall            : the door.

HOOD + UPPER CABINETS — the one non-obvious mechanic. `place_on_wall_*` is FLAT-only (a mesh deeper
than ~0.25 m hangs as furniture FLOATING in mid-air — the laundromat build dropped its uppers for
exactly this reason). The right tool is the wall-ADJACENT path with the `bottom=` lift
(`place_on_<wall>_wall_<pos>(obj, bottom=1.5)` — the warehouse exit-sign / retail wall-shelf
mechanic), which mounts a deep mesh up the wall at a real height. But that path registers the piece
as FLOOR furniture, so the 2D-footprint OverlapConstraint sees the hood and the range beneath it as
interpenetrating and would shove them apart along the wall. Fix: flag them `ignore_overlap` (skipped
by the gradient, `_snap_overlaps`, `_clamp_to_bounds` and `_warn_overlaps`) and `is_static` (grad
zeroed every solver step, so the action sampler's exploration floor can't random-walk them along the
wall — the living_room_cozy thin-wall-furniture drift). `_repin_wall_furniture` still snaps them
flush and preserves the Y lift, so they stay pinned exactly above the range.

Blue accent: the plan's blue tile backsplash / blue paneling has no texture or mesh in the library,
and an accent colour smuggled into a wall-texture string dominates the embedding and recolours all
four walls (classroom v1). The accent is carried by a PROP instead (music_studio lesson): the pinned
pantry mesh — captioned "tall gray" but rendering blue-grey paneled — IS the plan's blue rhythm.

Tall pieces (fridge, pantry) sit in wall LEFT/RIGHT slots, never a wall CENTRE: the interior cameras
sit at ~1.4-1.5 m at each wall's centre, and a fixture taller than that at a wall centre both blinds
that view and corrupts the VLM constraints judged from the strip (bakery v1).

Phase-gated (IDSDL/phases.py): `--phase 1` builds only the floor layout (~1 min) to verify room size
/ overlaps / clearances before the expensive surface dressing (2) and walls+lighting+mood (3).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Kitchen", seed=11)

# --- pinned heroes (every one eyeballed in the asset audit) --------------------
BASE_CAB = "hssd/559f21c7f5628a83b31d616e90bdcc02e7744731"   # walnut shaker base cab, WHITE MARBLE top
SINK_UNIT = "hssd/048d80c36ddc6ac63785ca08ccf231431195717c"  # wood cabinet + built-in steel sink + faucet (a SET)
RANGE = "hssd/4e74376ca5c86ab82bd86383f3551ab23f2d6c34"      # stainless freestanding range, black glass door
HOOD = "hssd/3904b36e135441d887b1328d7fae230b6fcb875e"       # stainless chimney hood
FRIDGE = "future/a266bc1f-0685-3080-beeb-b09d60a4f5ca"       # stainless side-by-side, visible handles
PANTRY = "hssd/722d9b8b0d8ad98e8798840b918121d2c126fa26"     # tall BLUE-GREY paneled cabinet (the blue accent)
UPPER_CAB = "hssd/4c911c25364d1cbb37493ecfaa6b889d931c78ac"  # walnut wall cabinet, two glass doors
STOOL = "hssd/609af80af4fb45e772a2109a7a4876b73601fb6b"      # light wood slat-back counter stool
TABLE = "future/9ff76d8d-af20-493d-a17c-a4aaaa94114a"        # light oak dining table, BARE top (no baked-in chairs)
CHAIR = "hssd/24fd37914321b915b9503d25add09332900a8d61"      # light wood classic dining chair
# identity props — a kitchen reads by the PRODUCT on its counters, not by empty cabinetry
# (jewelry_shop lesson); each was confirmed present in the dataset during the audit.
FRUIT = "hssd/51a22c69abd300c67c0b53c7045d1e7f2db52cfb"      # white pedestal bowl of fruit
PITCHER = "hssd/59d54ccbb28afc76a3c140ef50eba8a2f65cc850"    # classic white ceramic jug
CANISTERS = "hssd/221f50f3c5d67b6ca37bdc3b2d2d14f3d5ce2380"  # tea / coffee / sugar ceramic jars
CROCK = "hssd/xxxx112ab20axb6b2x4762x941axa03de965f252"      # utensil holder w/ wooden tools
BLENDER = "hssd/a88edd11e8996c7e09faa02c72afd5a613006a18"    # small counter appliance
HERB = "future/15b3e770-720b-4649-abb3-c17eba46c77f"         # potted herb in a grooved pot
BASKET = "future/c96d2ee0-8593-42b8-bcc3-bd9e4476b49d"       # wicker basket, warm texture accent
PLATES = "hssd/3db8975f3cc3a6fec983098c49a07157a788195b"     # stack of white ceramic plates
BOWLS = "hssd/e14232e0246e93cb5710b63aa2a88c64962578d9"      # pair of white ceramic bowls

scene.prefetch_assets([
    "a dark walnut kitchen base cabinet with a white marble countertop",
    "a wooden kitchen cabinet with a built-in stainless steel sink and faucet",
    "a stainless steel freestanding range oven with a cooktop",
    "a stainless steel chimney range hood",
    "a tall stainless steel side-by-side refrigerator",
    "a tall blue paneled kitchen pantry cabinet",
    "a dark walnut kitchen wall cabinet with two glass doors",
    "a light wood counter stool with a slatted backrest",
    "a light oak rectangular dining table",
    "a light wood classic dining chair",
    "a warm brass dome pendant light",
    "a flat round LED flush mount ceiling light",
    "a white pedestal bowl filled with fruit",
    "a classic white ceramic water jug",
    "a set of ceramic jars labeled tea coffee sugar",
    "a matte white utensil holder with wooden kitchen tools",
    "a modern kitchen blender",
    "a small potted green herb plant",
    "a wicker basket with a fabric liner",
    "a framed botanical print in a wooden frame",
    "a framed still life print of lemons in a thin wooden frame",
    "a stack of white ceramic plates",
    "a pair of white ceramic bowls",
])

# =============================================================================
# PHASE 1 — the floor anchors
# =============================================================================

# --- the COOK RUN: one rigid module row, flush on the long back wall -----------
# sparsity=0.02 keeps the modules essentially touching, so the row reads as ONE continuous
# run of cabinetry rather than three separate pieces standing near each other.
with scene.GridGroup(sparsity=0.02) as cook_run:
    cook_run.place_row([
        scene.AddAsset("a dark walnut kitchen base cabinet with a white marble countertop",
                       asset_id=BASE_CAB, width=1.1),
        scene.AddAsset("a stainless steel freestanding range oven with a cooktop", asset_id=RANGE),
        scene.AddAsset("a dark walnut kitchen base cabinet with a white marble countertop",
                       asset_id=BASE_CAB, width=1.1),
    ])

# --- the ISLAND: the room's work anchor; stools on ONE side (the seating side) --
# width= lengthens the cabinet into a proper island while keeping a realistic counter height
# (a uniform scale to 1.8 m wide would also make it absurdly TALL — the bar-counter rule).
island = scene.AddAsset("a dark walnut kitchen base cabinet with a white marble countertop",
                        asset_id=BASE_CAB, width=1.8)
with scene.AroundGroup(sparsity=0.15, jitter=0.2) as island_group:
    island_group.set_anchor(island)
    stools = 2 * scene.AddAsset("a light wood counter stool with a slatted backrest", asset_id=STOOL)
    # place_rectilinear already gives the row a uniform straight facing (anchor-180, square to the
    # island). Do NOT face() each stool at the island — that aims them at its centre POINT and fans
    # the end stools inward; a straight service row wants parallel seats (bar.md).
    # The phase-1 VLM asked to "rotate the counter stools by 180" — DECLINED: the left-wall view
    # shows both stools' seats/backrests correctly addressing the island. This is the same
    # place_rectilinear false positive bar.md declined; the render is the arbiter.
    island_group.place_rectilinear(longer_side1=stools)
    if PHASE >= 2:
        island_group.place_on_top([
            scene.AddAsset("a white pedestal bowl filled with fruit", asset_id=FRUIT),
            scene.AddAsset("a matte white utensil holder with wooden kitchen tools", asset_id=CROCK),
            scene.AddAsset("a modern kitchen blender", asset_id=BLENDER),
        ])
    if PHASE >= 3:
        # SINGULAR pendant query + LOW density: a plural query returns a mesh that is ALREADY a
        # cluster of globes, and add_lighting copies it N times into a cloud (bar.md). The count
        # also spreads across the group footprint (which includes the stool depth) — keep it low.
        island_group.add_lighting("a warm brass dome pendant light", density=0.12)

# --- the SINK RETURN: the short L leg on the left wall, under the window ---------
# The sink is a SET (cabinet + basin + faucet) and is natively only 0.60 m wide — placed alone it
# reads as a lost little side cabinet (v1 render), and it can't be widened: a uniform scale to a
# counter width would make it 1.5 m TALL, and a width-only stretch distorts the basin (the
# set-asset scaling rule). The fix is compositional — flank it with base cabinets so it reads as a
# continuous counter WITH a sink in it, which is what a real kitchen is. This is the signature's
# sanctioned "optional short return (L)"; the back run still dominates the read.
sink = scene.AddAsset("a wooden kitchen cabinet with a built-in stainless steel sink and faucet",
                      asset_id=SINK_UNIT)
with scene.GridGroup(sparsity=0.02) as sink_run:
    sink_run.place_row([
        scene.AddAsset("a dark walnut kitchen base cabinet with a white marble countertop",
                       asset_id=BASE_CAB),
        sink,
        scene.AddAsset("a dark walnut kitchen base cabinet with a white marble countertop",
                       asset_id=BASE_CAB),
    ])

# place_on_top ALWAYS targets the group's ANCHOR, so the surface to dress must BE the anchor
# (living_room_cozy v3). Anchoring on the whole RUN dresses the continuous counter, not one module.
with scene.RelativeGroup() as sink_station:
    sink_station.set_anchor(sink_run)
    if PHASE >= 2:
        sink_station.place_on_top([
            scene.AddAsset("a small potted green herb plant", asset_id=HERB),
            scene.AddAsset("a set of ceramic jars labeled tea coffee sugar", asset_id=CANISTERS),
        ])

# --- the cold / dry storage block ---------------------------------------------
fridge = scene.AddAsset("a tall stainless steel side-by-side refrigerator", asset_id=FRIDGE)
pantry = scene.AddAsset("a tall blue paneled kitchen pantry cabinet", asset_id=PANTRY)

# --- the DINING corner: table + two seats a side --------------------------------
# v1 used place_circle(4) at sparsity 0.2 / jitter 0.35: the chairs flung out into a ring far wider
# than the table, and THAT bloated cluster — not the item count — is what auto-sized the shell into
# a cavernous room (hospital_room's rule: find the footprint culprit before reaching for
# modulate_scale). place_rectilinear seats two down each long side of a RECTANGULAR table, which is
# both correct for the form and a much tighter footprint. Low sparsity/jitter tucks the chairs in.
with scene.AroundGroup(sparsity=0.05, jitter=0.15) as dining:
    table = scene.AddAsset("a light oak rectangular dining table", asset_id=TABLE, width=1.4)
    dining.set_anchor(table)
    chairs = 4 * scene.AddAsset("a light wood classic dining chair", asset_id=CHAIR)
    dining.place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])
    if PHASE >= 2:
        dining.place_on_top([
            scene.AddAsset("a classic white ceramic water jug", asset_id=PITCHER),
        ])

# --- the hood + the glass-front uppers (mounted UP the wall — see the docstring) -
# They are built as ONE row that MIRRORS the cook run, not as three separate wall placements. The
# back wall is wider than the 2.8 m run, so uppers dropped in the wall's left/right slots would
# hang out past the run's ends, floating over bare floor. A row centred on the same wall slot as
# the run instead lands the hood dead over the range (both the run and this row are symmetric
# about their own centre) and the uppers exactly over the two base cabinets.
if PHASE >= 3:
    hood = scene.AddAsset("a stainless steel chimney range hood", asset_id=HOOD)
    hood.scale(0.75)     # ~ the range's own width, not a canopy spanning the whole run
    # STOCK the glass-front uppers. Their doors are GLASS: left empty they read as the fixture, not
    # as a kitchen (the jewelry_shop rule — an empty display case names the case). Dishes behind the
    # glass are the plan's "glass-front cabinetry". Build ONE dressed unit and duplicate it with
    # 2 * unit, never two units separately: place_inside runs its sizing tournament PER CALL, so
    # building them apart would size the two cabinets' crockery differently (design_principles).
    # The dishes are children of the cabinet, and get_world_transform() composes parent transforms,
    # so they ride up the wall with it when the row is mounted at bottom=.
    with scene.RelativeGroup() as upper_unit:
        upper_unit.set_anchor(scene.AddAsset(
            "a dark walnut kitchen wall cabinet with two glass doors", asset_id=UPPER_CAB))
        upper_unit.place_inside([
            scene.AddAsset("a stack of white ceramic plates", asset_id=PLATES),
            scene.AddAsset("a pair of white ceramic bowls", asset_id=BOWLS),
        ])
    upper_l, upper_r = 2 * upper_unit
    with scene.GridGroup(sparsity=0.02) as upper_row:
        upper_row.place_row([upper_l, hood, upper_r])
    for _u in (upper_row, upper_l, hood, upper_r):
        _u.ignore_overlap = True   # it sits ABOVE the run — a 2D footprint clash is not a real one
        _u.is_static = True        # never let the exploration floor walk it along the wall

# =============================================================================
# the room
# =============================================================================
# modulate_scale=0.85 — the final-phase room shrink. RoomProportions voted 0.79 -> 0.80 -> 0.80: a
# unidirectional, non-decaying train, so it is signal, not the premature noise the hold-early rule
# guards against (living_room_cozy). Applied ONCE, decisively. Chose 0.85 over the voted 0.80: the
# cook run and the sink return are FIXED-SIZE rows, and shrinking a shell below the footprint its
# placements dictate makes those rows overflow their slots into overlaps the solver cannot undo
# (the locker_room packed-room rule) — the empty floor here is the working aisle around the island.
with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:
    # Plain COLOUR + MATERIAL words only. An accent clause ("cream walls with a blue tile
    # backsplash") dominates the texture embedding and recolours ALL FOUR walls (classroom v1).
    room.place_walls(floor_texture="light oak wood plank floor",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="warm cream painted plaster wall")

    room.place_on_back_wall_center(cook_run)        # the hero run, flush on the long wall
    room.place_on_center(island_group, facing="front")
    room.place_on_left_wall_center(sink_station)    # the L-return, under the window (phase 3)
    room.place_on_right_wall_left(fridge)           # tall block, held OFF the wall centre
    room.place_on_right_wall_right(pantry)          # the blue vertical accent
    room.place_on_front(dining, facing="back")      # dining at the edge of the workflow
    # the door goes in at PHASE 1: its auto-clearance shapes the whole floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # deep meshes mounted UP the wall (NOT place_on_wall_*, which is flat-only). One row,
        # same wall slot as the run below it -> hood over the range, uppers over the base cabs.
        room.place_on_back_wall_center(upper_row, bottom=1.50)
        # a modest punched pane, never a full-height glaze: any opening renders as a BLACK void
        # (there is no exterior environment), and a big pane = a wall of black (retail/exec_office).
        room.place_window_standard("left_wall", position="center",
                                   curtain="light linen roman shade")
        room.place_on_wall_front_left(
            scene.AddAsset("a framed botanical print in a wooden frame"))
        # the right wall was a blank expanse between the fridge and the pantry (my own read — the
        # VLM loop was fully clean and said nothing about it). Its centre slot is free: the fridge
        # sits in the back third and the pantry in the front third, so no wall-object clearance
        # fires and neither appliance gets slid.
        room.place_on_wall_right_center(
            scene.AddAsset("a framed still life print of lemons in a thin wooden frame"))
        room.place_on_back_right_corner(
            scene.AddAsset("a wicker basket with a fabric liner", asset_id=BASKET,
                           modulate_scale=1.6), facing="front")   # v1 rendered it doll-sized
        # a FLUSH fixture, never a hanging chandelier (add_lighting caps a fixture's height at 1.5 m
        # but pins its origin at the ceiling, so a long-drop fixture hangs into the room). density is
        # a fixture COUNT and it scales with FLOOR AREA — a kitchen wants the bottom of the band.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("kitchen_v1.blend")
