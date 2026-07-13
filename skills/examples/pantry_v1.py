"""
Pantry — "Vertical-Integrated Pantry System" (planner target:
tmp/plan_A_walk_in_food_pantry___storage_/plan.png).

Look (from the plan): a narrow walk-in larder. Tall white-and-oak open shelving runs
floor-to-ceiling down BOTH long walls, densely stocked with glass jars, canisters,
labelled boxes and woven baskets; a work counter with a warm wood top caps the far end
under a small window; a freestanding stainless fridge stands beside it; a two-step stool
parks by the entry for the high shelves. A single white globe pendant lights the aisle.
Palette: light neutrals (white plaster, pale concrete floor) + warm oak + glass.

Zone map (pantry runs front<->back; the LONG walls = LEFT + RIGHT — loading them is what
elongates the auto-sized shell; the short end walls stay light):
  - LEFT  (long)  = stocked shelf run x4 (glass jars + spice racks + canisters).
  - RIGHT (long)  = stocked shelf run x3 (tins + jars) + the FRIDGE.
  - BACK  (short) = the work counter run + the window above it (the sightline cap) + bulk boxes.
  - FRONT (short) = the single door + the step stool + a crate/sack corner.
  - CENTER        = kept EMPTY: the clear walk-in aisle (corridor circulation rule).

The category read is the PRODUCT, not the fixture (jewelry_shop lesson): the dataset has no
pre-stocked domestic pantry shelf — only branded retail gondolas — so the racks are stocked by
hand with place_inside. An empty rack reads as furniture; a full one reads as a pantry. See the
"WHAT GOES ON A SHELF" note below — getting the goods list wrong is what makes a rack read empty.

Phase 1: the two shelf runs + counter run + fridge + door + shell (floor layout).
Phase 2: stock the shelves (place_inside) + dress the counter + step stool, crate + sack.
Phase 3: window over the counter, globe pendant, wall shelf/decor (mood).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Pantry", seed=20)

# --- pinned assets (audited previews, gate 3) ---
_SHELF   = "hssd/93ca3ca5a4d3284bb1e870b571e7ff3b6358232d"   # tall oak+white open shelving, many bays (the hero)
_COUNTER = "hssd/fa5562e2e06d5c189107ed10f1c3e05552cb1bb2"   # white base cabinet, warm wood worktop
_FRIDGE  = "future/a266bc1f-0685-3080-beeb-b09d60a4f5ca"     # stainless side-by-side fridge
_STOOL   = "hssd/8a199393aa14b1487354e6fcc8df37de1b6a8b51"   # wooden two-step stool

# the PRODUCT (all "set" meshes — several vessels per placement = more visible mass per bay)
_JARS_GLASS = "hssd/309e63ae4c2dd92335bbad28bbfeac1f75d47f44"   # set of square glass storage jars
_JARS_CHALK = "hssd/88a74bcb73482e4f54859bbf8b71b6d2751e7bb9"   # chalk-labelled storage jars
_TINS_DARK  = "hssd/11b88fa116c0d97bab6e306e0e445006e5341916"   # three dark metal canisters, brown lids
_TINS_BW    = "hssd/e20a7e44504c3c98891d6d56d4af6bcc1ad66e22"   # black/white "cafe / sucre" tins
_SPICE      = "hssd/dd3b98de6287ba8bfe2260acd64776079aba5dcc"   # wooden spice rack, twelve glass jars
_BOXES      = "hssd/66f9623be165c339763d833a7666c34e94744f33"   # stack of labelled storage boxes
_BASKET     = "future/8a0f0758-347e-4c34-b987-e3b2a79141fe"     # woven basket, contents visible
_SACK       = "future/c1ebb64b-4ca0-4826-bba6-f0b974e23713"     # burlap sack of dry goods
_CRATE      = "custom/eb9d3e7bc84027186dadc23ce1dcd332429eed11" # natural wooden storage crate

scene.prefetch_assets([
    "a tall oak and white open shelving unit",
    "a white kitchen base cabinet with a wooden worktop",
    "a stainless steel freestanding fridge freezer",
    "a wooden two step stool",
    "a set of square glass storage jars",
    "a set of chalk labelled kitchen storage jars",
    "a set of three dark metal kitchen canisters",
    "a set of black and white kitchen storage tins",
    "a wooden spice rack with twelve glass jars",
    "a stack of labelled storage boxes",
    "a woven storage basket",
    "a burlap sack of dry goods",
    "a natural wooden storage crate",
    "a white globe pendant ceiling light",
])


# ============================ the STOCKED SHELF unit (the hero, x2 flavours) ============================
# Compose ONE unit (shelf + its bay contents), then N * unit -> the whole run is identical and the
# heavy place_inside tournament runs ONCE (locker_room cubby / corridor pattern).
# The shelving mesh is natively narrow-and-tall; scale by HEIGHT to a real 2.1 m larder rack
# (scale-by-height idiom: scale(width * H/height) keeps the aspect).
def stocked_shelf(goods):
    shelf = scene.AddAsset("a tall oak and white open shelving unit", asset_id=_SHELF)
    shelf.scale(shelf.get_width() * 2.4 / shelf.get_height())   # floor-to-ceiling in a 3 m room
    with scene.RelativeGroup() as unit:
        unit.set_anchor(shelf)
        if PHASE >= 2:
            # THE category cue: food in every bay, at viewing height. Sizing is the tournament's
            # call (modulate_scale is a no-op on place_inside/on_top items — tv_studio lesson).
            unit.place_inside(goods)
    return unit


# WHAT GOES ON A SHELF — the hard part of this scene, and not what you would guess. place_inside
# resizes every item to a TILE it computes from the anchor and the goods list; you do not control
# the size (modulate_scale is a no-op here — tv_studio lesson). Two consequences, both measured:
#   * a huge mesh poisons the tile floor: the 1.07 m box stack forced ~1 m tiles => one lonely
#     prop per board. Box stacks, cartons and the jar tray belong on the FLOOR/counter, at their
#     own size — not on a rack.
#   * item size collapses as the goods list grows (see HOW MANY below).
# The product that has to READ (the jars — this is a pantry) is therefore massed on the 0.9 m
# COUNTER with place_on_top, where the height-fit gives a believable ~0.2 m jar at viewing height.
def _goods(*specs):
    return [scene.AddAsset(q, asset_id=i) for q, i in specs]

_G_JARS_GLASS = ("a set of square glass storage jars", _JARS_GLASS)
_G_JARS_CHALK = ("a set of chalk labelled kitchen storage jars", _JARS_CHALK)
_G_TINS_DARK  = ("a set of three dark metal kitchen canisters", _TINS_DARK)
_G_TINS_BW    = ("a set of black and white kitchen storage tins", _TINS_BW)
_G_SPICE      = ("a wooden spice rack with twelve glass jars", _SPICE)
_G_BOXES      = ("a stack of labelled storage boxes", _BOXES)
_G_BASKET     = ("a woven storage basket", _BASKET)

# HOW MANY — measured on the real solver, and it is the opposite of the intuition. Item size and
# item COUNT trade off inversely: judge_tile_size shrinks the tile until all n items would fit on
# ONE board, then every item is resized to that tile. Solved widths on this rack:
#     n=3 -> 0.15 m (reads)      n=8 -> 0.06 m       n=18 -> speck      n=36 -> invisible
# So a long goods list does NOT stock a rack, it sands it down to dust — 36 goods rendered EMPTIER
# than 6. The rack's total product mass is roughly fixed; you only choose how it is divided.
# => a FEW substantial goods per rack. Keep one basket in each list: it has the largest footprint
# (0.45 m), which holds the tile floor generous so the jars beside it come out chunky, not tiny.
# LEFT long wall: the dry-goods wall — jar clusters and spice racks between the baskets
left_unit = stocked_shelf(_goods(
    _G_BASKET, _G_SPICE, _G_JARS_GLASS, _G_BASKET, _G_JARS_CHALK, _G_TINS_DARK,
))
with scene.GridGroup(sparsity=0.04) as shelves_left:
    shelves_left.place_row(4 * left_unit)

# RIGHT long wall: the preserves wall — tins and canisters between the baskets
right_unit = stocked_shelf(_goods(
    _G_BASKET, _G_TINS_BW, _G_SPICE, _G_BASKET, _G_JARS_GLASS, _G_TINS_DARK,
))
with scene.GridGroup(sparsity=0.04) as shelves_right:
    shelves_right.place_row(3 * right_unit)

# ============================ BACK short wall: the WORK COUNTER run ============================
# One counter unit dressed on top, duplicated into a 2-wide run -> a continuous worktop that caps
# the aisle (the plan's focal end). place_on_top targets the group ANCHOR = the counter (living_room
# lesson: always ask what the anchor is).
def counter_unit():
    with scene.RelativeGroup() as u:
        u.set_anchor(scene.AddAsset("a white kitchen base cabinet with a wooden worktop", asset_id=_COUNTER))
        if PHASE >= 2:
            # the JARS live HERE, not on the racks: against a 0.9 m counter the height-fit gives a
            # believable ~0.2 m jar at viewing height — the same prop on a 2.4 m rack becomes a speck
            u.place_on_top([
                scene.AddAsset("a set of square glass storage jars", asset_id=_JARS_GLASS),
                scene.AddAsset("a set of three dark metal kitchen canisters", asset_id=_TINS_DARK),
                scene.AddAsset("a set of black and white kitchen storage tins", asset_id=_TINS_BW),
            ])
    return u

with scene.GridGroup(sparsity=0.02) as counter_run:
    counter_run.place_row(2 * counter_unit())

# ============================ FRONT: the crate + sack corner (a lived-in pantry vignette) ============
_crate = scene.AddAsset("a natural wooden storage crate", asset_id=_CRATE)
_crate.scale(0.6)          # a crate, not a chest: the native mesh loads furniture-sized
with scene.RelativeGroup() as crate_stack:
    crate_stack.set_anchor(_crate)
    if PHASE >= 2:
        crate_stack.place_on_top(scene.AddAsset("a burlap sack of dry goods", asset_id=_SACK))
        crate_stack.place_on_left(scene.AddAsset("a woven storage basket", asset_id=_BASKET))

# the fridge: future/ scale metadata is unreliable (corridor lesson) -> retarget to a real 1.8 m body
fridge = scene.AddAsset("a stainless steel freestanding fridge freezer", asset_id=_FRIDGE)
fridge.scale(fridge.get_width() * 1.8 / fridge.get_height())


# ============================ ROOM ============================
# Long walls carry the shelf runs; the center aisle stays EMPTY — that clear lane IS the walk-in
# category (corridor). Expect the RoomProportions shrink vote to persist on it; the render arbitrates.
with scene.RoomGroup(modulate_scale=0.85, randomness=0.05) as room:
    room.place_walls(floor_texture="pale grey polished concrete floor",
                     ceiling_texture="soft white plaster ceiling",
                     wall_texture="warm white plaster wall")
    # the two long walls (omit facing -> the heuristic turns the open shelf side into the room)
    room.place_on_left_wall_center(shelves_left)
    room.place_on_right_wall_center(shelves_right)
    # the service end: counter caps the aisle; the fridge stands on the right wall beside it
    room.place_on_back_wall_center(counter_run)
    room.place_on_right_wall_right(fridge)
    # the single door (phase 1: its auto clearance shapes the floor solve)
    room.place_door("front_wall", position="center")

    if PHASE >= 2:
        # the step stool + the crate/sack corner live on the light FRONT wall, clear of the
        # full-length shelf runs (locker_room: never drop a prop into a corner a wall run owns)
        _stool = scene.AddAsset("a wooden two step stool", asset_id=_STOOL)
        _stool.scale(0.5)  # a step stool, not a bench (native mesh loads ~1 m wide)
        room.place_on_front_wall_left(_stool)
        room.place_on_front_wall_right(crate_stack)
        # the bulk boxes are floor-sized meshes (1.07 m) — on a shelf they poison the tile size,
        # on the floor beside the counter they read as exactly what they are: sacks-and-boxes bulk
        room.place_on_back_wall_left(scene.AddAsset("a stack of labelled storage boxes", asset_id=_BOXES))

    if PHASE >= 3:
        # a modest window over the LOW counter run: daylight down the aisle, and it caps the
        # sightline (windows render as daylight now — the black-void workaround is obsolete)
        room.place_window_standard("back_wall", position="center",
                                   curtain="a natural linen roller shade")
        # one calm globe pendant over the aisle. Small room -> density at the BOTTOM of the
        # 0.01-0.02 band (music_studio starfield-lint lesson); brightness comes from the sky.
        # The globe renders ~1.5 m at scale 1.0 (it filled the v2 ceiling); 0.3 shrank it to a dot
        # AND multiplied it into 8 (count ~ 1/footprint — the library coupling). 0.5 is the middle.
        room.add_lighting("a white globe pendant ceiling light", density=0.006, modulate_scale=0.5)

scene.export("pantry.blend")
