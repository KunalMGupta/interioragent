"""Home laundry room — "Integrated Laundry Command Center" (planner target:
tmp/plan_a_home_laundry_room__washer_and_/plan.png).

Look (from the plan): a bright, durable utility room. White front-loading machines
run into a warm-wood folding worktop with the utility tub at the far end; open
shelving carries the laundry products and baskets; a concertina airer and an
ironing board take the light walls; light tile floor, white plaster, daylight.

Zone map — a laundry is a ONE-HEAVY-WALL service room (the laundromat skeleton at
domestic scale). The centre is an empty working aisle, and the SHAPE is a galley:

  - BACK (the hero) = THE RUN: washer + dryer + folding counter + utility tub as ONE
    GridGroup row, flush on the wall. The plan's "integrated sink at the counter end"
    is why the tub belongs IN the run and not on a side wall — and it is also what
    keeps the room small (see the footprint note below). Everything in the run is
    ~0.9 m, so it never blinds the interior camera. Framed art hangs above it.
  - LEFT  = the open shelving, STOCKED (the product layer).
  - RIGHT = the concertina airer.  Shelf and airer face each other ACROSS the aisle,
    both in the wall-CENTRE slot, so they share ONE grid row instead of claiming two.
  - FRONT = the ironing board (centre, where its 0.40 m depth costs a shallow row
    instead of its 1.20 m width costing a deep one), the door (right), window (left).
  - CENTRE = the working aisle, holding only the basket of laundry you carry in.

FOOTPRINT NOTE (the v1 phase-1 lesson — kitchen's "find the culprit, don't rescale"):
RoomGroup sums 5 column-widths and 5 row-depths, and a SIDE-wall item contributes its
WIDTH to a row's depth. The first layout put sink / shelf / airer / ironing board in
four different rows and auto-sized a 4.5 x 3.9 m hall around 12 m² of furniture
(`rescale room by 0.6`). Collapsing them into the run + one shared row is what makes
this a laundry room instead of a laundry hall — no modulate_scale involved.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor
layout (~1 min) before surface dressing (phase 2) and walls/window/lighting (phase 3).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("LaundryRoom", seed=17)

# The full build blew out to white: the 500 W default budget (add_lighting splits it
# across N fixtures) on top of the interior sky, in an ~11 m² room whose every surface
# is white, washed the tile floor away entirely. Brightness is the BUDGET, never the
# fixture or the density (wine_cellar) — and unlike IDSDL_SKY, this dial is a scene
# attribute, so it survives the warm MCP server's import-time binding. 180 W lights a
# small daylit utility room without crushing the highlights.
scene.light_budget = 180.0

# --- pinned assets (previews eyeballed at gate 3) ---------------------------------
WASHER  = "future/39482d28-ac90-4f33-a07b-923edf6bd054"   # white front-loader, black porthole
DRYER   = "future/3a419f6e-b0d4-46e8-b5fe-d031008fee39"   # white front-loader, silver drum (the pair)
COUNTER = "hssd/fa5562e2e06d5c189107ed10f1c3e05552cb1bb2" # white base cabinet, warm wood top
SINK    = "hssd/f06b92490816c0ae1d22b0e979718e475b8903a0" # grey utility tub on legs, faucet
SHELF   = "hssd/cf3140a9b17b1de888dc3670dd00799488566d19" # white 5-tier open shelving
AIRER   = "hssd/a55da36088048698a1bebfd9aa7aaa5c17422961" # chrome concertina clothes airer
IRONING = "hssd/cc916aa81e794cea2f80fd42864aa66b285334c4" # white ironing board, metal legs
BASKET_LAUNDRY = "future/684d3071-f52e-48d9-a572-4288304678c5"  # grey basket, laundry spilling out
BASKET_WICKER  = "future/9f1cfe06-b99a-4b9e-93e2-21571589b0f0"  # wicker basket, cloth draped
TOWELS  = "hssd/6ece1a15f0f508aab2371808d58eefa8420cf725" # stack of rolled white towels
# No laundry-DETERGENT mesh exists (gate 3: best 0.49, all bathroom toiletries — the
# casino poker-chip trap). At room scale a prop is its SILHOUETTE (tv_studio), so the
# products are a bottle trio + a big pump jug massed on the shelf: they read as
# detergent from the aisle. Logged as the scene's one ingest candidate.
BOTTLES = "hssd/9a83f86ed492c9283fed9baa9a97e1cfdc5140f3" # three bottles with metal lids
JUG     = "hssd/e55406dff300de474e7a08711a7e75afd3495004" # large plastic pump bottle

scene.prefetch_assets([
    "a white front-loading washing machine",
    "a white front-loading clothes dryer",
    "a white base cabinet with a warm wood countertop",
    "a grey utility sink tub with a faucet on metal legs",
    "a white five-tier open metal shelving unit",
    "a chrome concertina folding clothes airer",
    "a white ironing board with metal legs",
    "a grey woven laundry basket full of clothes",
    "a woven wicker laundry basket with a fabric liner",
    "a stack of rolled white towels",
    "three plastic bottles with metal lids",
    "a large plastic bottle with a pump dispenser",
    "a framed botanical wall art print",
    "a small potted green plant in a white pot",
    "a flat round LED flush mount ceiling light",
])

# --- BACK wall: THE RUN — washer + dryer + folding counter + utility tub -----------
# The plan wants the machines "under a continuous folding counter"; the DSL has no
# fitted joinery, so the counter CONTINUES the machine line (same box silhouette,
# same ~0.9 m height) and the tub caps it — a run, not a stack.
washer  = scene.AddAsset("a white front-loading washing machine", asset_id=WASHER)
dryer   = scene.AddAsset("a white front-loading clothes dryer", asset_id=DRYER)
counter = scene.AddAsset("a white base cabinet with a warm wood countertop",
                         asset_id=COUNTER, width=1.2)
sink    = scene.AddAsset("a grey utility sink tub with a faucet on metal legs", asset_id=SINK)
with scene.RelativeGroup() as folding:
    folding.set_anchor(counter)          # the counter IS the anchor: place_on_top targets it
    if PHASE >= 2:
        # The detergent lineup lives HERE, not only on the shelf: place_inside
        # height-fits a bottle to ~0.14 m against a 1.35 m shelf, which is a speck
        # from across the aisle, while place_on_top sizes it against the 0.9 m
        # counter — the readable band, in the back view's frame. jewelry_shop's rule
        # is product at VIEWING HEIGHT on the display surface, and this is it.
        folding.place_on_top([
            scene.AddAsset("a stack of rolled white towels", asset_id=TOWELS,
                           modulate_scale=0.7),
            scene.AddAsset("a woven wicker laundry basket with a fabric liner",
                           asset_id=BASKET_WICKER),
            scene.AddAsset("three plastic bottles with metal lids", asset_id=BOTTLES),
        ])
with scene.GridGroup(sparsity=0.03) as run:
    run.place_row([washer, dryer, folding, sink])

# --- LEFT wall: the open shelving, STOCKED (the product layer) ---------------------
# jewelry_shop's rule: an empty fixture names the fixture, not the room — and a
# 3-item first pass proved it, landing as specks on a shelf that read as a bare
# bookcase. `modulate_scale` is a NO-OP on place_inside items (the tournament
# height-fits each to its tile — tv_studio), so the only lever is to MASS the
# product: 7 items across the tiers, with the big-silhouette baskets carrying the
# read from across the aisle and the bottles supplying the detergent lineup.
shelf = scene.AddAsset("a white five-tier open metal shelving unit", asset_id=SHELF)
# 1.35 m tall: the tower stands in the wall-CENTRE slot, which is exactly where the
# opposite view's camera sits (~1.88 m eye) — the native 1.68 m would crowd that lens.
# Height-only (the frame is rectilinear, so closer tiers read fine; a uniform fit
# would also shave the width to 0.80 m and shrink every tile the product sits in).
shelf.scale_only_height(1.35)
with scene.RelativeGroup() as shelving:
    shelving.set_anchor(shelf)
    if PHASE >= 2:
        shelving.place_inside(
            2 * scene.AddAsset("three plastic bottles with metal lids", asset_id=BOTTLES)
            + [scene.AddAsset("a large plastic bottle with a pump dispenser", asset_id=JUG)]
            + 2 * scene.AddAsset("a woven wicker laundry basket with a fabric liner",
                                 asset_id=BASKET_WICKER)
            + [scene.AddAsset("a stack of rolled white towels", asset_id=TOWELS)]
            + [scene.AddAsset("a large plastic bottle with a pump dispenser", asset_id=JUG)]
        )

# --- the room ---------------------------------------------------------------------
# Room size, settled by ARITHMETIC rather than by negotiating with the occupancy
# metric (kitchen_set's rule). Held at 1.0 through phases 1-2 (render-wins-early);
# the vote ran 0.72 -> 0.80 (unidirectional, decaying = converging). The shell
# auto-sizes to ~5.03 x 3.06 m, but the back-wall run is a RIGID GridGroup row that
# cannot compress, so shrinking has a hard floor:
#     WIDTH >= run (3.0) + shelf depth (0.26) + airer depth (0.64) + margin ~= 4.1 m
#     => modulate_scale >= 4.1 / 5.03 = 0.82   (DEPTH is not binding: 0.69)
# The voted 0.80 is BELOW that floor — obeying it would overflow the run into the
# side-wall pieces (the locker_room packed-row bug). 0.85 is a real shrink
# (4.28 x 2.60 m ~= 11 m²) with margin: stop SHORT of the vote when rigid rows and a
# working aisle are what the floor is for (kitchen / operating_room).
with scene.RoomGroup(modulate_scale=0.85, randomness=0.1) as room:
    # plain colour + material words only — an accent clause hijacks the whole
    # embedding match (classroom's teal-wall disaster)
    room.place_walls(floor_texture="light beige ceramic floor tiles",
                     ceiling_texture="smooth white plaster ceiling",
                     wall_texture="smooth white painted plaster wall")
    # facing omitted on every wall placement: the default heuristic already turns
    # each piece into the room (laundromat's clean-by-construction rule)
    room.place_on_back_wall_center(run)
    room.place_on_left_wall_center(shelving)
    room.place_on_right_wall_center(
        scene.AddAsset("a chrome concertina folding clothes airer", asset_id=AIRER))
    room.place_on_front_wall_center(
        scene.AddAsset("a white ironing board with metal legs", asset_id=IRONING))
    # the basket you carry in — a FLOOR object in the aisle (the centre slot is already
    # sized by the run's column and the shelf's row, so it costs the shell nothing) and
    # it is the prop that says "laundry in progress". The appliance clearance keeps it
    # off the machine fronts by itself.
    room.place_on_center(
        scene.AddAsset("a grey woven laundry basket full of clothes", asset_id=BASKET_LAUNDRY))
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")
    if PHASE >= 2:
        # the plan's greenery, and the one piece of dead floor in the renders. A CORNER
        # is free in the grid model — it shares the shelf's column and the run's row, so
        # neither grows. (The plan's entry RUG is deliberately declined: the prompt asks
        # for a tile floor and a utility room reads better hard-floored — dental_office.)
        room.place_on_back_left_corner(
            scene.AddAsset("a small potted green plant in a white pot"))
    if PHASE >= 3:
        # art over the LOW run — its AABB bottom (~1.2 m) clears the run's 0.9 m tops,
        # so the wall-object clearance pass has no occluder to slide (laundromat)
        room.place_on_wall_back_center(
            scene.AddAsset("a framed botanical wall art print"))
        # daylight (the brief's "bright"): windows render as real sky now. The front
        # wall's LEFT slot is free — the door claims right, the board is floor furniture.
        room.place_window_standard("front_wall", position="left",
                                   curtain="light ivory sheer curtains")
        # flush fixture, never a pendant; density 0.01 = the small-room band
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("laundry_room_v1.blend")
