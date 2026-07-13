"""
Clothing store — "Warm-Industrial Boutique: Central Spine, Perimeter Merchandising"
(planner headline: "Central Focal Island with Perimeter Merchandising").

The retail spine + perimeter loop recipe (retail_store.md / bookstore.md), rebuilt on the
INGESTED custom shop fixtures — which for apparel is the whole game: every rack in this pool
comes PRE-HUNG with garments and every mannequin comes DRESSED, so the room reads "clothing
store" from its merchandise, not from empty fixtures (the jewelry_shop v1->v2 lesson).

Layout — a DEEP room (entry -> back), so the long runs go on the two SIDE walls:
  BACK (service wall)  : cash-wrap with an integrated POS under the brand sign, a framed rack and
                         a denim shelving unit flanking it. The cash-wrap is placed BARE — its POS
                         is modelled in and its free top area is tiny (see below).
  CENTRE SPINE         : two rack ROWS of three garment rails each (facing="left" runs them
                         front-to-back) framing a hero display island of folded stacks on a rug,
                         with a second folded table set back toward the service zone.
  LEFT WALL (apparel)  : a 5.27 m floor-standing merchandising WALL of clothes on hangers — the
                         hero run; it IS the wall.
  RIGHT WALL           : fitting-room bay (screen + full-length mirror + bench) at the back, the
                         shoe/bag/accessory case at the centre, a grid rack of jackets at the front.
  FRONT (storefront)   : three DRESSED mannequins staged in front of a standard window pane
                         (never floor-to-ceiling: a wall-sized black void), olive tree, door.

FIXTURE SIZE IS THE WHOLE SCENE (the lesson this build exists to record — see `native()`): the
ingested shop scans arrive at a VLM-guessed WIDTH, which miniaturises the big ones (a 5.27 m
merchandising wall loads at 0.6 m). Height-normalising them only compounds it. Pin the raw glb's
true width and let the room come out big — a clothing store IS big fixtures.

Palette (plan): warm neutrals + light wood + marble-look floor, black metal hardware; the
clothing is the colour.

Phase-gated (IDSDL/phases.py): `--phase 1` builds just the floor layout (~1 min).

Phase-1 build notes (what the first render taught):
  - hssd/76ae9b47 (the retail_store wall-merch shelf) has an OFF-CENTRE MESH ORIGIN: mounted
    with bottom=0.9 it settled at 1.65 m and tripped the floaters lint. Swapped, not
    compensated (coffee_shop bench lesson). NOTE `bottom=` on wall-ADJACENT furniture always
    trips that lint — only true place_on_wall_* items are exempt — so wall merchandising here
    is either floor-standing or genuinely wall-hung (thin).
  - the custom mannequin ships at h=1.06 m (its ingest `scale` is a WIDTH) and rendered as a
    toy-sized person -> height-normalised to 1.72 m.
  - v1 loaded 3 items on each side wall + a 3.5 m rack on the back wall: the shell auto-sized
    to 9.3 x 8.7 m (81 m²) and read cavernous (`rescale room by 0.77`). Trimmed the wall queues
    (hospital_room lesson: check for a wall queue BEFORE reaching for modulate_scale).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

# --- ingested custom shop fixtures (the PRODUCT is modelled into the mesh) ---
# REJECTED: custom/d7cf7f12… ("grey metal double-rail rack hung with garments") — the mesh carries a
# large SMOKED-GLASS backing panel that its low-res catalog preview doesn't show. Two of them as the
# spine rendered as brown glass partitions tinting their own garments — i.e. the fixture HIDES the
# product, the exact failure the jewelry_shop rule warns about. Caught by eye in the full render, not
# by any lint/VLM signal. Spine reverted to the proven future/a419b5a4 rails.
GRID_RACK   = "custom/45c9b0bb41b8325ad12adfbd3c8337cddd69fc25"  # perforated-grid rack, four black jackets
DENIM_UNIT  = "custom/459328e003398ab525d2d64a976fccb920c6b600"  # black metal denim shelving unit + signage
SHOE_TABLE  = "custom/c53de778cc431cbeca6cbb144593814c3f5f48ca"  # white-top / black-frame table OF SHOES
CASHWRAP    = "custom/eedaa74ba03140b24a6629be7ce4be699bd96307"  # curved light-wood counter, INTEGRATED POS
MANNEQUIN_F = "custom/0f626c5d19edec027e75f5c1f303787f9009b733"  # life-size mannequin, print dress + cardigan
DRESSFORM   = "custom/cd7e4e9c3523656c1d2a02072908607d07b2926e"  # blazer on a wooden dress form
OUTFIT_FORM = "custom/f226189cd46f33713817a3b05c69066fa38bbbe0"  # parka + cargo outfit on a form
FOLDED_WOOL = "custom/ca90cc08f591beaa7d24de2d6444d504b654ed49"  # stack of folded wool knits
JEANS_PROP  = "custom/3dcb3733291c9c8d15c265d03e621b1b1190cd68"  # folded denim
HANGER_WALL = "custom/12fd8ace4b837d791d219ad6ee5d419693b56ecd"  # 5.27 x 2.25 m merchandising WALL of clothes on hangers
NEON_SIGN   = "custom/d5884fb54a16d8f18a19a40989fcca074f5fcb84"  # glowing tube brand sign (wall)

# --- verified dataset pins (retail_store heroes, re-eyeballed) ---
SPINE_RAIL  = "future/a419b5a4-4bfe-4e04-a3f3-7c7e3e9fcd17"      # double-sided freestanding garment rail
FRAMED_RACK = "future/a3e8bf5a-c3dd-4211-bdda-483818d9d354"      # black-framed boutique rack, hung with garments
DISPLAY_TBL = "hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f"    # wood-top + black-frame display table
FOLDED_JEAN = "future/c17aa2e4-30f4-482a-badc-1c04309e487b"      # stack of folded jeans/sweaters
FLOOR_MIRROR= "hssd/2603ceec3f2913a4c4cb9af2855267babd1405a9"    # tall black-framed floor mirror
FIT_SCREEN  = "hssd/3d780643626fa80329154d35920d87d0df72d2fc"    # black-framed 3-panel screen (fitting bay)
HANDBAG     = "future/aa8e5dc9-69a1-441b-9758-7505fdda9e82"      # brown/beige leather handbag

scene = SceneProgRoom("ClothingStore", seed=13)

scene.prefetch_assets([
    "a freestanding double-rail garment rack hung with clothes",
    "a double-sided clothing display rail with hanging garments",
    "a black-framed boutique clothing rack with hanging garments",
    "a metal clothing rack with hanging jackets",
    "a black metal shelving unit stacked with folded jeans",
    "a low wooden merchandise display table with a black metal frame",
    "a display table with shoes and accessories",
    "a stack of folded knitwear",
    "a stack of folded jeans",
    "a stack of folded sweaters",
    "a brown leather handbag",
    "a curved retail checkout counter with an integrated point of sale terminal",
    "a life-size mannequin wearing a printed dress and cardigan",
    "a tailored blazer on a wooden dress form",
    "an outfit of a parka jacket and trousers on a mannequin form",
    "a tall black-framed full-length floor mirror",
    "a black-framed three-panel folding screen",
    "an upholstered bench with a fabric seat",
    "a tall potted olive tree in a concrete planter",
    "a neon store brand sign with glowing tube lettering",
    "a wooden merchandising wall of clothes on hangers",
    "a large flat neutral wool area rug",
    "a large rectangular wall mirror with a thin black frame",
    "a flat round LED flush mount ceiling light",
])


def sized_h(obj, h):
    """Uniform-scale a fixture to a target HEIGHT (aspect preserved)."""
    obj.scale(obj.get_width() * h / obj.get_height())
    return obj


def native(obj, true_width):
    """Restore an ingested scan to its REAL-WORLD size (uniform scale to the raw glb's width).

    The ingested shop scans are authored in real metres, but each one's retrieval `scale` is a
    VLM-GUESSED WIDTH that is applied on load — and for these big fixtures the guess is far too
    small, so they arrive as miniatures: the hanging-clothes merchandising wall is a 5.27 x 2.25 m
    shop fitting that loads at 0.6 m, the shoe/accessory case is 2.13 x 1.70 m and loads at 1.6 m
    wide, the mannequin is 1.85 m tall and loads at 1.06 m. Height-normalising them (sized_h) only
    compounds the shrink. Read the raw glb extents and pin the true width instead — a clothing
    store is SUPPOSED to be full of big fixtures, and the room is allowed to be large.
    """
    obj.scale(true_width)
    return obj


# raw glb extents (metres, W x H x D) of the ingested scans — the real fixture sizes
W_HANGER_WALL = 5.27   # 5.27 x 2.25 x 0.71 — a full apparel merchandising WALL (floor-standing)
W_SHOE_CASE   = 2.13   # 2.13 x 1.70 x 1.43 — shoes/bags/accessory display case
W_GRID_RACK   = 2.05   # 2.05 x 2.00 x 0.86
W_DENIM_UNIT  = 1.85   # 1.85 x 2.20 x 0.50
W_CASHWRAP    = 1.10   # 1.10 x 1.55 x 0.73 — height INCLUDES the POS screen
W_MANNEQUIN   = 0.70   # 0.70 x 1.85 x 0.45
W_DRESSFORM   = 0.52   # 0.52 x 1.96 x 0.48
W_OUTFIT_FORM = 0.63   # 0.63 x 1.85 x 0.38


def rail():
    """One double-sided garment rail — the spine unit, hung with garments, 1.5 m so the
    sightline to the service wall stays open (the plan's conditioning idea) and it stays out
    of the interior cameras' eyeline."""
    return sized_h(scene.AddAsset("a double-sided clothing display rail with hanging garments",
                                  asset_id=SPINE_RAIL), 1.5)


def rail_row():
    """A rack ROW of three rails — one spine side (retail_store's spine unit, one rail longer:
    a shop is read by the MASS of its merchandise, and two rails per side left the floor thin)."""
    with scene.GridGroup(sparsity=0.35, randomness=0.05) as row:
        row.place_row([rail(), rail(), rail()])
    return row


def folded_table(extra=None, rug=False):
    """A display table massed with folded stacks — the product at hand height."""
    stacks = [scene.AddAsset("a stack of folded sweaters", asset_id=FOLDED_JEAN),
              scene.AddAsset("a stack of folded knitwear", asset_id=FOLDED_WOOL)]
    if extra:
        stacks.append(scene.AddAsset(extra, asset_id=JEANS_PROP))
    with scene.RelativeGroup() as t:
        t.set_anchor(sized_h(scene.AddAsset("a low wooden merchandise display table with a black metal frame",
                                            asset_id=DISPLAY_TBL), 0.75))
        if PHASE >= 2:
            t.place_on_top(stacks)
            if rug:
                t.place_rug("a large flat neutral wool area rug", size=0.8)
    return t


# --- BACK / service wall: the cash-wrap — placed BARE -----------------------------------
# NOTHING goes on top of it. Two reasons, and the first is the general rule:
#   1. This reception-counter scan has very little FREE surface — its 1.55 m height already
#      INCLUDES an integrated POS screen sitting on the counter top, so the "register" the brief
#      asks for is modelled in and the usable top is a narrow strip either side of it. Crowning it
#      (folded stack + handbag) just piles props onto a surface that isn't there.
#   2. `place_on_top` is a VLM tournament that will happily find *some* horizontal region to seat
#      items on — it does not know the surface is already occupied or too small (the same blindness
#      that seated a lamp on an armchair cushion in living_room_cozy v3).
# RULE: before `place_on_top`, look at the anchor's FREE top area, not just its footprint. A counter
# whose product is modelled in wants nothing added.
checkout = native(scene.AddAsset("a curved retail checkout counter with an integrated point of sale terminal",
                                 asset_id=CASHWRAP), W_CASHWRAP)

# --- CENTRE: the hero display island — folded stacks at HAND height, on a grounding rug ---
island = folded_table(extra="a stack of folded jeans", rug=True)

# a second folded-clothes table set back into the service zone (retail_store's "more product" fix)
table2 = folded_table()

# --- FRONT: the storefront window display — three DRESSED forms in ONE row (one slot) ----
with scene.GridGroup(sparsity=0.55, randomness=0.08) as window_display:
    window_display.place_row([
        native(scene.AddAsset("a tailored blazer on a wooden dress form", asset_id=DRESSFORM), W_DRESSFORM),
        native(scene.AddAsset("a life-size mannequin wearing a printed dress and cardigan",
                              asset_id=MANNEQUIN_F), W_MANNEQUIN),   # 1.85 m; ships at 1.06 m
        native(scene.AddAsset("an outfit of a parka jacket and trousers on a mannequin form",
                              asset_id=OUTFIT_FORM), W_OUTFIT_FORM),
    ])

# --- RIGHT WALL: the fitting-room bay — screen + mirror + bench as ONE wall unit ---------
# (no purpose-built changing cubicle exists in the dataset; the screen carries the read)
with scene.RelativeGroup() as fitting_bay:
    fitting_bay.set_anchor(sized_h(scene.AddAsset("a black-framed three-panel folding screen",
                                                  asset_id=FIT_SCREEN), 1.8))
    fitting_bay.place_on_left(sized_h(scene.AddAsset("a tall black-framed full-length floor mirror",
                                                     asset_id=FLOOR_MIRROR), 1.7))
    fitting_bay.place_on_front(scene.AddAsset("an upholstered bench with a fabric seat"))

# --- RIGHT WALL: the shoe + accessory case, at its true 2.13 x 1.70 m --------------------
with scene.RelativeGroup() as shoe_unit:
    shoe_unit.set_anchor(native(scene.AddAsset("a display table with shoes and accessories",
                                               asset_id=SHOE_TABLE), W_SHOE_CASE))
    if PHASE >= 2:
        shoe_unit.place_on_top([
            scene.AddAsset("a brown leather handbag", asset_id=HANDBAG),
        ])

# --- the room ----------------------------------------------------------------------------
# modulate_scale: 1.0 (no multiplier). The RoomProportions vote asked to shrink all the way through
# (0.77 -> 0.80 -> 0.84 -> 0.60 when the floor emptied -> 0.88), but the real fault was never the
# shell: it was miniaturised fixtures. At TRUE size the same fixtures fill the same floor, and the
# shell is a CONSEQUENCE of them — a store full of 2 m shop fittings is simply a big store. Expect the
# occupancy vote to keep asking for a smaller box (the corridor/garage "open lane reads as empty"
# pattern) and let the render arbitrate.
with scene.RoomGroup(randomness=0.12) as room:
    # Envelope: the plan's "warm neutrals + light wood + marble-like floor". Greige walls rendered
    # cool/clinical against the pale marble — a warm sand beige plaster is the whole warmth of the
    # room (add_lighting has a fixed white budget, so the WARM in "warm retail lighting" has to be
    # carried by the envelope + the wood tops, not by the fixture).
    room.place_walls(floor_texture="polished light beige marble floor",
                     ceiling_texture="white",
                     wall_texture="warm sand beige plaster")

    # Service wall: the cash-wrap centred, facing the approaching customer; a framed rack beside
    # it (the bare stretch of brand wall read empty once the spine racks were swapped out).
    room.place_on_back_wall_center(checkout, facing="front")
    room.place_on_back_wall_left(
        scene.AddAsset("a black-framed boutique clothing rack with hanging garments", asset_id=FRAMED_RACK))
    room.place_on_back_wall_right(
        native(scene.AddAsset("a black metal shelving unit stacked with folded jeans",
                              asset_id=DENIM_UNIT), W_DENIM_UNIT))

    # Central merchandising spine: a rack ROW each side, facing="left" so they run front-to-back
    # and frame the centre aisle, with the hero island between them and a second folded table
    # set back toward the service zone.
    room.place_on_left(rail_row(), facing="left")
    room.place_on_center(island)
    room.place_on_right(rail_row(), facing="left")
    room.place_on_back_left(table2)

    # Storefront display, staged in front of the window pane — on the front-LEFT, not the
    # front-centre: an interior camera sits at each wall's centre at ~1.45 m, and a 1.72 m
    # mannequin parked there fills that whole view (bakery garbage-view lesson). Off-centre
    # it still reads as the window display and the entry lane from the door stays open.
    room.place_on_front_left(window_display, facing="front")

    # BOTH WALL CENTRES STAY CLEAR OF TALL FIXTURES. An interior camera sits at each wall's centre
    # at ~1.45 m looking across the room, so a 2 m fixture parked there SWALLOWS that camera — the
    # 2.25 m merchandising wall at left_wall_center and the 1.70 m shoe case at right_wall_center
    # each rendered one view as black geometry (bakery garbage-view lesson, at full strength now
    # that the fixtures are true-size). Slot the big runs to the wall ENDS instead; the centres
    # carry wall-HUNG pieces (flat, behind the camera) and the browsing lane.
    # LEFT wall = the hero apparel run: a 5.27 m floor-standing wall of clothes on hangers (0.71 m
    # deep, 2.25 m tall — real shop-fitting, never wall art), plus a grid rack of jackets.
    room.place_on_left_wall_left(
        native(scene.AddAsset("a wooden merchandising wall of clothes on hangers", asset_id=HANGER_WALL),
               W_HANGER_WALL))
    room.place_on_left_wall_right(
        native(scene.AddAsset("a metal clothing rack with hanging jackets", asset_id=GRID_RACK), W_GRID_RACK))

    # RIGHT wall = fitting bay (back) + the shoe/bag/accessory case (front).
    room.place_on_right_wall_left(fitting_bay)
    room.place_on_right_wall_right(shoe_unit)

    # Door in PHASE 1 — its auto clearance shapes the floor solve.
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        room.place_on_back_right_corner(
            scene.AddAsset("a tall potted olive tree in a concrete planter"), facing="front")
        # the brand sign auto-stacks ABOVE the cash-wrap (a wall op over a floor op on the same slot)
        room.place_on_wall_back_center(
            scene.AddAsset("a neon store brand sign with glowing tube lettering", asset_id=NEON_SIGN))
        # A boutique mirror on the back wall. (Nothing else is wall-HUNG: place_on_wall_* auto-scales
        # a hung piece to ~0.6 of a wall third, which blew the 0.8 m shoe ledge up to 0.38 m DEEP —
        # it would read as furniture floating in mid-air — and the clothes-on-hangers piece is a
        # 0.71 m deep, 5.27 m wide shop fitting that belongs ON THE FLOOR. Wall-hung = flat only.)
        room.place_on_wall_right_center(
            scene.AddAsset("a large rectangular wall mirror with a thin black frame"))
        # storefront: a STANDARD pane (floor-to-ceiling = a wall-sized black void)
        room.place_window_standard("front_wall", position="center")
        # flush fixture, low density. The true-size fixtures push the shell to 129 m², and density
        # is a fixture COUNT that GROWS with floor area — so a big room wants a LOWER density, not a
        # higher one: 0.02 tiled 41 discs (starfield lint, budget ~39). 0.01 -> a calm ~21. This
        # inverts the lint's own generic hint ("~0.05 for a medium room"); trust the printed budget.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("clothing_store_v1.blend")
