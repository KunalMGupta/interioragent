"""Grocery store — "Produce-First Warm-Industrial Grocery" (guided 9-gate flow).

Planner target: produce as the entry magnet (timber crates bursting with fruit), a
broad central axis front->back, a light-wood/black-metal merchandising table as the hub,
perimeter refrigerated bays, left-side open shelving, branded service counter at the back.
Palette: polished concrete floor, warm light-grey plaster walls, white grid drop ceiling.

Layout — every wall's CENTRE slot is chosen so that wall's ~1.4 m interior camera can see the
room (v1 put the 1.93 m gondolas and 2.01 m coolers at the wall centres and rendered both side
views pure BLACK; see grocery_store.md):
- BACK wall  : gondolas ×2 | SERVICE COUNTER (0.93 m — the camera sees OVER it) | gondolas ×2.
               A wall of stocked shelves flanking the counter = the money shot from the door.
- LEFT wall  : coolers ×2 | the DOOR (an opening claims no floor and blinds no camera) | coolers ×2.
- RIGHT wall : beverage rack | (empty — camera) | stocked snack rack.
- CENTRE     : the merchandising hub table, massed with product.
- FRONT      : three low produce tables bursting with fruit against the glazed storefront.

Identity comes from PRE-STOCKED fixtures + the PRODUCT at viewing height (toy_shop /
bookstore / jewelry_shop lesson): the gondola, snack rack and beverage rack ship already
loaded with groceries, so the room reads "grocery" with no crowning; the produce is MASSED
on the tables because no supermarket produce-table mesh exists.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor
layout (~1-2 min); phase 2 dresses the surfaces; phase 3 adds walls/glazing/lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("GroceryStore", seed=23)

# ---- pinned assets (gate-3 audit: every mesh eyeballed on a contact sheet) -------------
GONDOLA  = "custom/d79cf88b2009bca2cc0b6295e664d560290f4526"  # STOCKED supermarket gondola (1.00 x 1.93 x 0.38)
COOLER   = "hssd/cae4c60830bba615ff533dc23ffee6e6e5c7d14e"    # slim glass-door display fridge (0.60 x 2.01 x 0.65)
BEVERAGE = "custom/0dbd08c161cf956e034c61f411dd269e1d3f5799"  # multi-tier drinks rack, stocked; AUTHORED 2.34 x 1.63
SNACKS   = "custom/781de2d18edc5455b09c46e5201ae31ab1ecdc2d"  # chrome wire rack of snack bags; AUTHORED 1.44 x 1.80
ENDCAP   = "custom/e6b832f2c09637e351d79da487e66fc5d3144e95"  # Borges-branded promo rack; AUTHORED 1.00 x 1.96
TABLE    = "hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f"    # wood top + black metal frame (1.20 x 0.47 x 0.65)
COUNTER  = "hssd/67b505c2cfc433bc4ffe39250cafda3951d91939"    # white base + warm wood top, TRUE 0.93 m counter
POS      = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"    # touchscreen POS
NEON     = "custom/d5884fb54a16d8f18a19a40989fcca074f5fcb84"  # neon brand sign (flat, 0.02 m deep)
# produce (no supermarket produce table exists -> MASS the product on a market table)
FRUITBOX = "hssd/51cc5969569fe2186bfe128023a4faf2d872b3cd"    # crate of apples/grapes/bananas
APPLES   = "hssd/2f3e604c427b164ecc71bb0763a8c420944292ba"    # wooden crate of red apples
GRAPES   = "hssd/f1baec5e20e8368e3dfad52b1523ab0cb14800ce"    # bowl of grapes
PEARS    = "hssd/205483105e52440b45691ff6eda5e7527903260f"    # two green pears
GREENS   = "hssd/c097e81e02b06fc607cddf794ee4d863d75857ab"    # planters of leafy greens (the veg)
# grocery product for the hub table
SNACKBAG = "hssd/fc41b57d334f2d68b613d903b0216097ba33b938"    # assorted snack bags
BREAD    = "hssd/92fc2ee204fda4be19d08b79f79f68fc87e9afaa"    # rustic sliced-bread board
BOXES    = "hssd/71e625e1cc238c233bc67dc7014766281b317e22"    # stacked cardboard boxes (back-stock)
# The custom shop-fixture scans are authored in real metres, but each one's retrieval `scale` is a
# VLM's GUESS at its width and is applied on load — so several arrive as MINIATURES, and get_whd()
# cannot show it (it reports the already-scaled size). Raw glb extents vs. what actually loaded:
#     gondola  0.93 x 1.80  -> 1.00 x 1.93   ok
#     snacks   1.44 x 1.80  -> 1.00 x 1.25   31% SMALL
#     endcap   1.00 x 1.96  -> 0.65 x 1.28   35% SMALL
#     beverage 2.34 x 1.63  -> 2.00 x 1.39   15% SMALL
# so those three are pinned back to their AUTHORED width below. This is why the floor kept reading
# "empty" and the shrink vote would not quit — the FURNITURE was toy-sized, not the room too big
# (clothing_store's lesson). Read raw extents with trimesh, NOT get_whd().
# AVOID: future/83abfae5… (Häagen-Dazs freezer) loads at 0.15 m — its scale metadata lies.
# AVOID: hssd/7379d887… "checkout counter" is only 0.60 m tall (a low reception desk).
# AVOID: hssd/2c751d20… "kids' wooden fruit set in a crate" — caption≠mesh, renders as a white blob.
# AVOID: custom/eb9d3e7b… wooden crate — native depth 1.96 m (a deformed/spread mesh).


def sized(q, aid, w):      # target WIDTH (m), uniform
    o = scene.AddAsset(q, asset_id=aid)
    o.scale(w)
    return o


def sized_h(q, aid, h):    # target HEIGHT (m), uniform — the fixture rule (toy_shop)
    o = scene.AddAsset(q, asset_id=aid)
    o.scale(o.get_width() * h / o.get_height())
    return o


def run(units, sparsity=0.02):        # a butted wall run (deterministic, no overlap solve)
    with scene.GridGroup(sparsity=sparsity, randomness=0.0) as g:
        g.place_row(units)
    return g


def market_table(h, w, d):
    """The display table is a SQUAT mesh (1.20 x 0.47, w:h = 2.5): a uniform height-fit to
    0.70 m blows it out to 1.79 m wide, and three of those in one slot force a cavernous
    shell (coffee_shop slot economy). Bakery recipe: uniform-scale to the target HEIGHT,
    then take the width/depth back single-axis — invisible on a plank top + black frame."""
    o = scene.AddAsset("a wooden display table with a black metal frame", asset_id=TABLE)
    o.scale(o.get_width() * h / o.get_height())
    o.scale_only_width(w)
    o.scale_only_depth(d)
    return o


# ---- the aisle + the cold chain -------------------------------------------------------
# Both runs are TALLER than the ~1.4 m interior wall-cameras, so they are split into two
# blocks per wall with the wall CENTRE deliberately left empty — otherwise the fixture sits
# on top of that wall's camera and swallows the whole view (bakery blinded-view; the v1
# phase-1 build rendered both side views pure BLACK). office_modern's design-time fix.
aisle_a, aisle_b = (run(2 * scene.AddAsset("a supermarket gondola shelf stocked with grocery products",
                                           asset_id=GONDOLA)) for _ in range(2))
chill_a, chill_b = (run(2 * scene.AddAsset("a glass door refrigerated display case",
                                           asset_id=COOLER)) for _ in range(2))

# ---- the produce unit: a low market table MASSED with fruit (built once, duplicated) -----
with scene.RelativeGroup() as produce:
    produce.set_anchor(market_table(h=0.70, w=1.25, d=0.70))
    if PHASE >= 2:
        # MASS the product (jewelry_shop/bakery rule) — a produce table with three small props
        # reads as a table with clutter on it; it needs to be BURSTING. Five crates fill the top.
        produce.place_on_top([
            sized("a crate of fresh apples grapes and bananas", FRUITBOX, 0.55),
            sized("a wooden crate of fresh red apples", APPLES, 0.52),
            sized("a crate of fresh apples grapes and bananas", FRUITBOX, 0.50),
            sized("a bowl of fresh grapes", GRAPES, 0.32),
            sized("two fresh green pears", PEARS, 0.22),
        ])
produce_l, produce_c, produce_r = 3 * produce

# ---- the hub: the central merchandising table, massed with product ----------------------
with scene.RelativeGroup() as hub:
    hub.set_anchor(market_table(h=0.80, w=1.60, d=0.95))
    if PHASE >= 2:
        hub.place_on_top([
            sized("a rustic board of sliced bread", BREAD, 0.48),
            sized("assorted snack bags with colourful packaging", SNACKBAG, 0.32),
            sized("a crate of fresh apples grapes and bananas", FRUITBOX, 0.50),
            sized("a wooden crate of fresh red apples", APPLES, 0.45),
            sized("a bowl of fresh grapes", GRAPES, 0.30),
        ])

# ---- the service station: counter + POS (the back-wall anchor) --------------------------
with scene.RelativeGroup() as service:
    service.set_anchor(scene.AddAsset("a shop service counter with a wood top", asset_id=COUNTER))
    if PHASE >= 2:
        service.place_on_top([scene.AddAsset("a point of sale touchscreen terminal", asset_id=POS)])

# modulate_scale: the shrink vote ran 0.82 -> 0.72 -> 0.65 -> 0.5 -> 0.7 while the floor was
# still bare, so it was held through phases 1-2 (render-wins-early) and the floor was FILLED
# first (kindergarten rule). ONE decisive shrink here: 0.9 takes 54 -> 43 m2.
#
# The residual `rescale room by 0.8` at 43 m2 is DECLINED, permanently, for a computable reason
# (kitchen_set's "refute the vote with arithmetic"): the back-wall gondola RUN is a rigid 2.02 m
# GridGroup sitting in a 2.18 m column, so any modulate_scale below ~0.93 shrinks the slot under
# the run and it overflows into the counter — an overlap the solver cannot undo (locker_room /
# greenhouse). We are already AT that floor. And what the occupancy metric is scoring as "empty"
# is the central shopper aisle, which is exactly the plan's "broad central axis / wide walkways"
# — legitimate circulation, the same false positive as garage/corridor/kitchen.
with scene.RoomGroup(modulate_scale=0.9, randomness=0.08) as room:
    room.place_walls(floor_texture="polished grey concrete floor",
                     ceiling_texture="white drop ceiling",
                     wall_texture="warm light grey plaster wall")

    # BACK WALL = the money shot from the entrance: two blocks of STOCKED GONDOLAS flanking
    # the service counter. The counter is 0.93 m — BELOW the ~1.4 m wall camera — so the back
    # view stays open, while the 1.93 m gondolas sit in the side slots where they blind nothing.
    room.place_on_back_wall_left(aisle_a)
    room.place_on_back_wall_center(service)
    room.place_on_back_wall_right(aisle_b)

    # LEFT WALL = the cold chain, split around the entrance (centre = the door, an opening,
    # which claims no floor and blinds no camera)
    room.place_on_left_wall_left(chill_a)
    room.place_on_left_wall_right(chill_b)

    # RIGHT WALL = the stocked racks; CENTRE deliberately EMPTY for that wall's camera.
    # Both are pinned to their TRUE authored width (see the miniature-scan note above).
    room.place_on_right_wall_left(sized("a multi-tier beverage display rack stocked with bottles",
                                        BEVERAGE, 2.34))
    room.place_on_right_wall_right(sized("a wire display rack stocked with snack bags",
                                         SNACKS, 1.44))

    # centre: the merchandising hub
    room.place_on_center(hub)

    # FRONT: the produce tables, staged against the glazed storefront (the entry magnet).
    # They go in front_left / front_right — the SAME 5x5 columns the back-wall gondolas
    # already pay for — so they cost the shell nothing. A 3-wide produce ROW at `front`
    # instead lands in the centre column and adds its whole 4 m width to the room (the shell
    # is the SUM of 5 column maxima): that one move took the room to 10.4 x 6.6 m.
    # A THIRD table at `front` is FREE: at 1.25 m it is narrower than the 1.60 m hub that
    # already sets the centre column, so the shell does not grow — and the three together
    # become the plan's continuous "Produce Wall" across the storefront.
    room.place_on_front_left(produce_l)
    room.place_on_front(produce_c)
    room.place_on_front_right(produce_r)

    # corners: veg planters + a promo endcap + loose timber crates ("stacked timber crates")
    room.place_on_back_left_corner(scene.AddAsset("planters of fresh leafy green vegetables",
                                                  asset_id=GREENS))
    room.place_on_back_right_corner(sized("a branded promotional display rack of tinned food",
                                          ENDCAP, 1.00))
    room.place_on_front_left_corner(sized("a wooden crate of fresh red apples", APPLES, 0.90))
    room.place_on_front_right_corner(sized("a crate of fresh apples grapes and bananas", FRUITBOX, 0.90))

    if PHASE >= 3:
        # branding behind the service counter (hung above a LOW run — laundromat rule)
        room.place_on_wall_back_center(scene.AddAsset("a neon store brand sign with glowing tube lettering",
                                                      asset_id=NEON))
        # the glazed storefront: daylight (the black-void limit is FIXED — greenhouse)
        room.place_window_floor_to_ceiling("front_wall", curtain=None)
        # the entrance goes in the left wall's empty CENTRE slot: an opening claims no floor
        # and doesn't blind that wall's camera, and it lands between the two gondola blocks
        room.place_door("left_wall", position="center")
        # 0.02 tripped the deterministic STARFIELD lint (15 fixtures on 43 m2, budget ~13).
        # The count is 1+(max_lights-1)*density, so it scales with the shrunken floor too.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.012)

print(f"[room] {room.WIDTH:.2f} W x {room.DEPTH:.2f} D x {room.HEIGHT:.2f} H  "
      f"= {room.WIDTH * room.DEPTH:.1f} m2")

scene.export("grocery_store_v1.blend")
