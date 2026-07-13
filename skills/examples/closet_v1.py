"""
Walk-in closet — "Boutique Walk-In Wardrobe: Perimeter Storage with Central Dressing Oasis"
(planner target: tmp/plan_A_walk_in_closet___dressing_room/plan.png).

The library/locker_room pattern: a compact CORRIDOR whose two LONG walls carry the storage
runs, with a hero down the centre. Here the runs are open closet bays packed with hanging
clothes, and the hero is a dressing island with a tufted ottoman.

Zone map (corridor runs front<->back; long walls = LEFT + RIGHT):
  - LEFT (long)   = an open WARDROBE bay (hanging clothes) + a low folded-goods shelf; the wall
                    CENTRE is left empty (the interior camera stands there — see below).
  - RIGHT (long)  = a matching WARDROBE bay, a low SHOE RACK, and a three-tier SHOE DISPLAY
                    column lifted up the wall.
  - ENTRY         = a freestanding valet RAIL of hanging clothes.
  - CENTRE        = the HERO: a dressing ISLAND (marble/oak, drawers) + the tufted OTTOMAN,
                    on a runner rug, wearing a vanity tray + handbag.
  - BACK (short)  = the FULL-LENGTH MIRROR (focal) + the window + a plant.
  - FRONT (short) = the entry DOOR + a framed print.

Identity = PRODUCT, not fixtures (jewelry_shop rule). Every storage mesh here was pinned
because the CLOTHES and SHOES are modelled IN it — the dataset is full of open closet frames
and shoe racks that are EMPTY, and those read as furniture showrooms, not as a wardrobe.
Only 2 of 12 shoe racks in the dataset actually carry shoes; both are pinned below.

CAMERA RULE, applied at DESIGN time (bakery/kitchen_set lesson, not diagnosed after a bad
render): the interior cameras sit on the room centreline at ~0.55x ceiling height, only
`0.04 x room_width` in from each wall — i.e. ~0.16 m off the side walls here. Deep cabinetry
at a wall's CENTRE would swallow the camera looking at the OPPOSITE wall and return a black
view (which the VLM loop reports as "clean"). So both long-wall centres carry only LOW pieces
(folded-goods shelf 1.07 m; shoe rack 0.28 m) and every tall bay sits in a wall END slot.

Palette (deviates from the plan's pale greige, deliberately): the only product-rich closet
bays in the dataset are dark walnut, so the room is a warm DARK-WALNUT boutique — dark
hardwood floor, cream plaster walls, light-oak island, black/brass hardware. Product
legibility beats palette (the plan's own pale cabinetry only exists as EMPTY meshes).

Lighting: a flush brass fixture at density=0.01 (small-room band; 0.05 is a starfield) —
never the plan's "sculptural chandelier" (add_lighting caps fixture height at 1.5 m but pins
the origin at the ceiling, so a chandelier hangs into the room and blows the exposure out).
The glamour is carried by the brass/oak props instead.

Phase 1: island + ottoman, the wardrobe runs, shoe rack + shoe column, mirror, door, shell.
Phase 2: the island's surface dressing (vanity tray, handbag, folded sweaters).
Phase 3: window + sheer curtain, runner rug, flush lighting, framed print.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("WalkInCloset", seed=21)

# --- pinned assets (every preview eyeballed; get_whd() probed on every hero) ---
# Native dims noted because the dataset's `scale` metadata lies often enough to plan around.
WARDROBE = "future/03608677-5363-4a95-ba5c-a7a0b112db56"      # 2.00x2.12x0.58 open bay: hanging shirts on 2 rails, folded stacks, drawers, boxes
# (CLOSETSYS future/28f855f2 — 2.50x1.93x0.44, clothes + shoe shelves — was tried on the right
#  wall and dropped; see the note at its placement. Kept here as an audited alternative.)
MERCH = "hssd/76ae9b47590b35c68e8ab908e4641d523f083b0c"       # 1.50x1.07x0.63 shelf: folded clothes on top + a hanging rod under
ISLAND = "hssd/e0c58f0e9cfa8fffaa6707541a2e7a79754a99be"      # 1.50x0.71x0.49 light-oak 6-drawer dresser, black top + splayed legs
OTTOMAN = "hssd/a58885b138c463870ae858aae6acd55ca46574c8"     # 0.80x0.39x0.80 beige round TUFTED ottoman, dark wood legs (the plan's perch)
MIRROR = "hssd/2603ceec3f2913a4c4cb9af2855267babd1405a9"      # 0.70x1.74x0.04 black-framed FULL-LENGTH mirror (4 cm thin -> leans flush)
SHOE_SHELF = "hssd/e9597e32600022ebbae20264d1fed4b7d6b89b37"  # 0.80x0.19x0.25 white shelf WITH pairs of shoes on it
SHOE_RACK = "hssd/26d31e9c1911118556e11b7d564b4b7bae8466bd"   # 1.20x0.28x0.37 black shoe shelf WITH shoes (the floor rack)
FOLDED = "future/c17aa2e4-30f4-482a-badc-1c04309e487b"        # stack of folded sweaters
HANDBAG = "future/aa8e5dc9-69a1-441b-9758-7505fdda9e82"       # structured brown/beige leather handbag
RAIL = "future/a419b5a4-4bfe-4e04-a3f3-7c7e3e9fcd17"         # 1.20x2.17x0.85 double-sided rail WITH garments (retail_store's)
TRAY = "future/725133ce-f094-4865-bd8a-5a5a5851efa0"          # glass bottles + diffuser on a tray (the vanity tray)

# ============================ CENTRE: the dressing island (hero) ============================
# The island is a chest of drawers, not a kitchen island: the one dataset mesh actually
# captioned "kitchen island with a marble countertop" previews as a RUSTIC FARMHOUSE WORK
# TABLE — a wrong-kind object (prison_cell's floral curtains in a jail cell). This oak/black
# dresser is natively only 0.71 m tall, so width-fit it uniformly to 1.7 m => a real 0.80 m
# island height (uniform, never scale_only_height: single-axis scaling distorts the drawers).
island = scene.AddAsset("a light oak six drawer dresser with a black top", asset_id=ISLAND)
island.scale(1.7)

def wardrobe_bay():
    """An open closet bay, width-fit to 1.8 m (uniform => a 1.91 m tall bay).

    THE FOOTPRINT CULPRIT LIVES HERE (kitchen rule: when a room reads too big, find the piece
    that SIZED it before reaching for modulate_scale — the occupancy vote tells you THAT the
    room is wrong, never WHICH piece made it wrong). The first build auto-sized to 4.48 x
    8.15 m: an 8 m long closet. Room DEPTH is 3 wall slots x the WIDEST wall item, so the
    widest bay sets the length of the room. Obeying the VLM's 0.8 shrink instead would squeeze
    the shell under the wall runs' own footprint and overflow them into their neighbours —
    overlaps the solver cannot undo on wall-pinned furniture (the locker_room packed-room
    trap). Trimming the bays 2.0 -> 1.8 m walks the room in to ~6.6 m honestly, and the shell
    then takes one safe 0.9 on top.
    """
    w = scene.AddAsset("an open wardrobe bay with hanging clothes", asset_id=WARDROBE)
    w.scale(1.8)      # NOTE: scale() returns None — never chain it (greenhouse)
    return w


# A freestanding valet rail of hanging clothes for the entry zone. The entry third rendered as
# dead floor, and a persistent shrink vote on a wall-packed room means ADD FURNITURE, not
# shrink the shell (kindergarten/greenhouse) — so the empty floor gets filled with PRODUCT
# rather than bought back with modulate_scale. Height-fit to 1.7 m (native 2.17 m reads as a
# shop fixture towering over the bays).
rail = scene.AddAsset("a double-sided clothing rail with hanging clothes", asset_id=RAIL)
rail.scale(rail.get_width() * 1.7 / rail.get_height())

with scene.RelativeGroup() as island_group:
    island_group.set_anchor(island)
    # The tufted ottoman is the try-on perch: it sits at the island's front, facing the door.
    island_group.place_on_front(scene.AddAsset("a round beige tufted upholstered ottoman", asset_id=OTTOMAN))
    if PHASE >= 2:
        # place_on_top ALWAYS targets the group's ANCHOR (living_room_cozy v3: a lamp landed
        # on an armchair's seat) — here the anchor IS the island, which is what we want.
        island_group.place_on_top([
            scene.AddAsset("a tray of glass perfume bottles", asset_id=TRAY),
            scene.AddAsset("an elegant leather handbag", asset_id=HANDBAG),
            scene.AddAsset("a stack of neatly folded sweaters", asset_id=FOLDED),
        ])
    if PHASE >= 3:
        # A runner down the dressing aisle. Keep it <= 0.8: a rug sized to a room-dominating
        # cluster's bbox reads as wall-to-wall carpet (living_room_cozy).
        island_group.place_rug("a flat neutral wool runner rug", size=0.7)

# ============================ ROOM ============================
# modulate_scale was held at 1.0 through phases 1-2 (render-wins-early). The vote sat at 0.8
# for four straight builds, but obeying it outright is the locker_room trap: the shell would
# drop below the wall runs' own footprint. So the room is walked in from BOTH ends instead —
# the wall items were trimmed (above), which shortens the slot grid honestly, and the shell
# takes ONE decisive, safe 0.9. That lands ~4.0 x 6.4 m: the slot is then 2.12 m against a
# 1.8 m widest wall item (no overflow) and the dressing aisles stay ~0.65 m either side of the
# island. Stopping SHORT of the vote is deliberate — a walk-in's aisle is working floor an
# occupancy metric always reads as emptiness (garage/corridor/operating_room).
with scene.RoomGroup(modulate_scale=0.9, randomness=0.1) as room:
    # Plain colour + material words only. An accent clause in a texture string recolours the
    # whole room (classroom's teal), and "warm oak plank floor" matches a SALMON-PINK plank
    # in this library (kitchen_set) — "dark brown hardwood" is the wording that holds.
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="smooth white plaster ceiling",
                     wall_texture="smooth cream painted plaster wall")

    # CENTRE: the island + ottoman down the middle (the only floor slot occupied — room size
    # is a consequence of slot occupancy, so a lean centre keeps the shell closet-scale).
    room.place_on_center(island_group, facing="front")

    # LEFT (long) wall = the hanging runs. Tall bays in the END slots; the CENTRE slot takes
    # the LOW folded-goods shelf so the right-view camera (which sits ~0.16 m off THIS wall)
    # clears it. `facing` omitted everywhere: the heuristic already faces wall furniture into
    # the room, and passing facing=<the wall's own name> turns its open side to the wall.
    # ONE bay at the back end + the folded-goods shelf at the door end, and the wall CENTRE
    # deliberately EMPTY (the camera stands there — the safest possible thing to put in it).
    #
    # v1 ran bay / shelf / bay across all three slots and the shelf ended 0.45 m INSIDE the
    # far bay. Cause (worth knowing — it is a property of the DSL, not of this scene): wall
    # furniture is placed at `row_centers[1..3]` (groups.py), and those row centres are sized
    # by the FLOOR occupants of each row, NOT by the wall items. The back row here is shallow,
    # so its centre sits only 1.20 m from the middle row's centre — while a 1.8 m bay beside a
    # 1.5 m shelf needs (1.8+1.5)/2 = 1.65 m between centres. Nothing in the DSL checks that,
    # and because the shelf must be `ignore_overlap` (below), no solver pass could push back:
    # it is invisible to every overlap check. **Three long items on one wall is not a slot
    # count you can assume — it is an arithmetic you must check against the row pitch.**
    # (`IDSDL/lints.py::lint_embedded_wall_objects` now catches this class; it was added for
    # exactly this bug, which the full VLM loop reported as `no wall overlap`.)
    room.place_on_left_wall_right(wardrobe_bay())

    # The folded-goods shelf. This mesh (and the shoe shelves below) is authored as a
    # WALL-MOUNTED unit — floor-placed it reports an AABB bottom 0.45 m up and trips the float
    # lint. That lint's advice ("swap the mesh") is for floor furniture; the right fix for a
    # wall unit is to MOUNT it, via the wall-adjacent + `bottom=` path (it is 0.63 m deep, far
    # past the 0.25 m limit where place_on_wall_* would float it). ignore_overlap is mandatory
    # (else the 2D solver reads the lifted shelf and the cabinet as interpenetrating and shoves
    # them apart along the wall) — and is_static because a lifted piece has a small footprint,
    # which the GradSolver's exploration floor random-walks along the wall.
    merch = scene.AddAsset("a shelf of folded clothes with a hanging rod", asset_id=MERCH)
    merch.ignore_overlap = True
    merch.is_static = True
    room.place_on_left_wall_left(merch, bottom=0.45)

    # RIGHT (long) wall = a matching bay + the shoe zone. Centre slot stays LOW (the shoe shelf
    # tops out at 0.48 m) so the left-view camera clears it.
    #
    # This slot first held CLOSETSYS (a closet system with its own shoe shelves). Rejected on a
    # look at the render: that mesh is 2.50 x 1.93 m, and uniform scaling couples width to
    # height, so the 1.8 m width the slot grid can afford drags it down to 1.39 m tall — a
    # stunted run under a blank wall band, opposite two 1.91 m bays. Tall would mean wide, and
    # wide is what made the room 8 m long. A matching bay keeps the twin floor-to-ceiling runs
    # the plan asks for (library's symmetric corridor), and the shoe zone below already carries
    # the shoes. Nothing in the VLM loop flags a stunted wall — it is a look-at-it call.
    room.place_on_right_wall_left(wardrobe_bay())
    shoe_rack = scene.AddAsset("a low shoe rack with pairs of shoes", asset_id=SHOE_RACK)
    shoe_rack.ignore_overlap = True
    shoe_rack.is_static = True
    room.place_on_right_wall_center(shoe_rack, bottom=0.20)   # a "floating" shoe shelf by design

    # A three-tier SHOE DISPLAY column, lifted up the wall in ONE end slot (the plan's lit
    # shoe niches). Wall-hung (place_on_wall_*) would FLOAT these — they are 0.25 m deep, so
    # they mount via the wall-ADJACENT path with a `bottom=` lift. That path registers them as
    # FLOOR furniture, which bites twice, so (per the range-hood recipe in dsl_reference):
    #   ignore_overlap -> the 2D-footprint solver sees the three stacked shelves as one
    #                     interpenetrating pile and would shove them apart along the wall;
    #   is_static      -> the GradSolver's exploration floor random-walks small-footprint
    #                     pieces along the wall (the living_room_cozy fireplace drift).
    for i, shelf in enumerate(3 * scene.AddAsset("a white shelf displaying pairs of shoes", asset_id=SHOE_SHELF)):
        shelf.ignore_overlap = True
        shelf.is_static = True
        room.place_on_right_wall_right(shelf, bottom=0.45 + 0.45 * i)   # 0.45 / 0.90 / 1.35 m

    # BACK (short) wall = the focal full-length mirror, dead centre. It is 4 cm deep, so it
    # cannot blind the front-view camera that sits just in front of it.
    room.place_on_back_wall_center(scene.AddAsset("a tall full length mirror with a black frame", asset_id=MIRROR))
    room.place_on_back_right_corner(scene.AddAsset("a tall potted olive tree in a plant pot"))

    # FRONT (short) wall = the entry. Door in the right slot; the window goes on the BACK wall
    # (a different wall entirely) so the two openings can never contend for a slot.
    room.place_door("front_wall", position="right")
    # The valet rail stands free in the entry third, opposite the door (its own floor slot, so
    # it costs no wall length and cannot stretch the shell).
    room.place_on_front_left(rail)

    if PHASE >= 3:
        # Daylight from the far end rakes ACROSS the cabinetry. `standard`, not `picture`:
        # picture spans wide and takes no position, so it collides with anything else on the
        # wall (dental_office). The window-as-black-void lore is obsolete (greenhouse fixed it).
        room.place_window_standard("back_wall", position="left", curtain="sheer white linen curtains")
        # FLUSH fixture, never a chandelier; density 0.01 = the small-room band (0.05 starfields).
        room.add_lighting("a flat round brass LED flush mount ceiling light", density=0.01)
        # Hung on the front wall, over the low/empty end — clear of the tall bays and the door.
        room.place_on_wall_front_left(scene.AddAsset("a framed black and white fashion photograph print", width=0.7))

scene.export("closet.blend")
