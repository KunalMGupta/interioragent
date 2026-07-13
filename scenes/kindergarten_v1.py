"""
Kindergarten v1 — "Cheerful Zone-Driven Kindergarten Classroom" (planner target
tmp/plan_A_bright__cheerful_kindergarten_/plan.png). Supersedes the thin pre-workflow
scenes/kindergarten.py (which shipped place_window_picture -> a black void, unpinned
chairs, and a non-flush ceiling light).

A room for 4-5 year olds, built as zones ringed around ONE hero (game_room's
hero-in-the-middle), with toy_shop's identity rule doing the heavy lifting:

  * CENTRE      = CIRCLE TIME. The oval alphabet rug IS the hero. It is placed as a
                  FLOOR object, so the OverlapConstraint reserves its footprint and the
                  clear carpet a class sits on comes for free. (Never place_on_top onto
                  a rug -- the flat-surface tiler shatters it into 3 cm items.)
  * FRONT wall  = TEACHING WALL: whiteboard hung centre + ABC poster; the teacher desk
                  sits front-left FACING the class; the door is front-right.
  * BACK wall   = STOCKED STORAGE RUN (the identity): a toy shelf already loaded with
                  toys, a cubby already loaded with colourful labelled bins, and a
                  toddler locker. Every fixture arrives FULL -- an empty shelf names the
                  fixture, not the room (jewelry_shop/toy_shop).
  * LEFT        = READING NOOK by the window: two bean bags + a teddy on their own rug,
                  with the book stand (filled with picture books) against the wall so the
                  books are within reach.
  * RIGHT/BACK-RIGHT = ACTIVITY FIELD: two low round kid tables, each ringed by four
                  lion-faced kid chairs, dressed with alphabet blocks + crayons.

Everything is CHILD height (~0.5-1.15 m). That is both the brief and a camera rule: the
interior wall cameras sit at ~1.4-1.5 m, so any fixture taller than that at a wall centre
blinds the view and provokes hallucinated rotation flags (bakery v1).

Palette: light maple floor, white walls. The bright primary accent is carried entirely by
PROPS -- rug, lion chairs, bin fabrics, bean bags, art -- never by the wall-texture string
(classroom v1: "one teal accent wall" recoloured all four walls green).

Phase-gated (IDSDL/phases.py): --phase 1 = floor layout only (~1 min check);
phase 2 adds surface dressing; phase 3 adds walls/window/lighting/mood.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Kindergarten", seed=11)

# --- pinned assets (previews eyeballed at gate 3) ---------------------------------
ALPHABET_RUG   = "hssd/ba8bdada00a0781b3660b0adb3a7375719916164"   # oval rug, blue centre + letter border (HERO)
KIDS_TABLE     = "hssd/4b9ff34fe5d44b8ef57eed9f3d2001df29127a56"   # round natural kid table, BARE flat top (no chairs)
LION_CHAIR     = "future/938f5c3e-9c15-4239-86a6-de32b323b21f"     # cartoon lion kid chair, yellow seat (carries the accent)
CUBBY_BINS     = "future/187f9f51-4778-42bb-959f-47e4f71636fc"     # light-wood cubby PRE-STOCKED w/ colourful labelled bins
TODDLER_LOCKER = "hssd/e81617da960c31f70dcd4ad885e390509282c84d"   # 4-section toddler locker w/ colourful bins
TOYSHELF       = "future/1fc1d19b-87b5-4d16-8cfa-69d642a37dba"     # cartoon shelf PRE-STOCKED with toys
BOOK_DISP      = "hssd/f3a8d459c4e019b28b926e55d56e087cc82593fa"   # stand FILLED with colourful children's books
BEANBAG_BLUE   = "hssd/0598a08d6d048ed49026adf13247d4586033c864"   # blue cosmic-star bean bag
BEANBAG_YELLOW = "hssd/0839789da49edd699988877d5a39268b4deab118"   # yellow bean bag
WHITEBOARD     = "hssd/1b37271d2d52124cf69fa91a2acb11a6dde262f2"   # flat white board (teaching wall)
ABC_POSTER     = "hssd/caf281fc61ef48ec1800d2eec6d5adca4a70f652"   # ABC poster, letters + illustrations (FLAT)
TRAIN_ART      = "hssd/128c8d8dfa72c702a9f6faacee8cd7fffadd1b62"   # kid canvas, red train on blue -- VERIFIED visible content
OCEAN_ART      = "hssd/8e37f5aec35bbac7aafa160df0aa6cded71af9b0"   # kid canvas, whale/ocean -- VERIFIED visible content
ABC_BLOCKS     = "future/6b72a461-3bf3-47bd-bf58-31f1fa88e926"     # colourful wooden alphabet blocks (ABC at surface height)
TEACHER_DESK   = "hssd/99e2a3e301a597ed93bf3dc57b36fec3b37b8846"   # wooden desk, drawers, flat top (classroom_v1 pin)
GLOBE          = "hssd/55c813d9a522cc5e52176d01e75ea53d260c9003"   # vintage world globe (classroom_v1 pin)
TEDDY          = "future/3e18ed6d-9f79-46cf-afe7-ac2a3512570d"     # large teddy bear plush (toy_shop pin)
BLOCKS         = "hssd/6561f279b05e443c3e5d9c9951f9afedae97a66c"   # natural wooden building blocks (toy_shop pin)
PUZZLE_BOX     = "hssd/d5f0014aa089653a8c5a142ab966d73a9af40298"   # colourful boxed game/puzzle (toy_shop pin)

# AVOID (audited, gate 3):
#   hssd/12ef49da... "planets wall art" -- a WHEELED EASEL (0.26 m deep), not a print (children_room)
#   hssd/c5fcff66... "child's chair"    -- the picker's top pick is a WHEELED SWIVEL OFFICE chair
#   hssd/2af5d109..., hssd/f8261de4...  -- table+chair SET meshes (would double-seat the AroundGroup)
#   "a cup full of colored crayons"     -- NO crayon cup exists (best 0.43; the shortlist is beige
#       pencils / post-its). It resolved to a white ceramic DESIGNER pencil holder with two black
#       pens and put a vase-like object on every kid table -- an eye catch, invisible to the VLM
#       loop (the geometry is fine; "a designer pen pot doesn't belong in a kindergarten" is
#       semantics). Swapped for a boxed puzzle, a prop the library provably has (casino v1).

scene.prefetch_assets([
    "a colorful alphabet letters oval kids area rug",
    "a low round natural wood kids activity table, no chairs",
    "a small cartoon lion kids chair",
    "a light wood kids cubby shelf stocked with colorful storage bins",
    "a wooden toddler locker with colorful bins",
    "a kids shelf stocked with colourful toys",
    "a wooden display stand full of colourful children's books",
    "a blue star kids bean bag chair",
    "a yellow kids bean bag chair",
    "a soft colorful kids reading rug",
    "a large white classroom whiteboard",
    "a colorful ABC alphabet poster for a classroom",
    "a childrens wall canvas with a red train",
    "a childrens ocean animals wall canvas",
    "a set of colorful wooden alphabet blocks",
    "a classic wooden teacher desk with drawers",
    "a black office task chair",
    "a decorative vintage world globe on a stand",
    "a large teddy bear plush toy",
    "a set of natural wooden building blocks",
    "a cup full of colored crayons",
    "a leafy potted plant in a ceramic planter",
    "a flat rectangular LED flush mount ceiling light",
])


def sized(query, asset_id, width):
    """Pinned asset at a literal footprint WIDTH (uniform scale, metres)."""
    o = scene.AddAsset(query, asset_id=asset_id)
    o.scale(width)
    return o


def sized_h(query, asset_id, height):
    """Pinned asset at a literal HEIGHT (uniform scale, aspect preserved).

    Fixtures (shelves, cubbies, lockers, chairs) vary wildly in native proportion, so a
    WIDTH target squashes or blows their height -- a height target gives the consistent
    child-scale stance this room lives or dies by (toy_shop).
    """
    o = scene.AddAsset(query, asset_id=asset_id)
    o.scale(o.get_width() * height / o.get_height())
    return o


# === ACTIVITY UNIT: one low table ringed by four kid chairs =========================
# Built ONCE and duplicated (2 * unit): a composed unit constructed twice would run the
# place_on_top tournament twice and size the blocks DIFFERENTLY on each table.
# place_circle inherits the anchor's rotation and seats chairs sideways, so each chair is
# explicitly faced at the table (hospital_room's place_arc lesson).
with scene.AroundGroup(sparsity=0.18, jitter=0.35) as table_unit:
    kid_table = sized("a low round natural wood kids activity table, no chairs", KIDS_TABLE, 0.95)
    table_unit.set_anchor(kid_table)
    kid_chairs = 4 * sized_h("a small cartoon lion kids chair", LION_CHAIR, 0.62)
    table_unit.place_circle(kid_chairs)
    for _ch in kid_chairs:
        table_unit.face(_ch)                       # default target = the anchor (the table)
    if PHASE >= 2:
        # The ABC identity at SURFACE height -- the product, not the fixture (jewelry_shop).
        # Anchor IS the table, so place_on_top lands on the tabletop (living_room_cozy v3).
        table_unit.place_on_top([
            sized("a set of colorful wooden alphabet blocks", ABC_BLOCKS, 0.28),
            sized("a colourful childrens puzzle box", PUZZLE_BOX, 0.3),
        ])

table_a, table_b, table_c = 3 * table_unit

# === READING NOOK: a FLOOR cluster, never stacked on the rug ========================
# place_on_top onto a flat rug tiles it into ~3 cm cells and shrinks the bean bags to
# nothing (toy_shop). Bean bags are FLOOR objects; the rug goes under them via place_rug.
with scene.RelativeGroup() as reading_nook:
    reading_nook.set_anchor(sized("a blue star kids bean bag chair", BEANBAG_BLUE, 0.75))
    reading_nook.place_on_right(sized("a yellow kids bean bag chair", BEANBAG_YELLOW, 0.72))
    if PHASE >= 2:
        reading_nook.place_on_back(sized("a large teddy bear plush toy", TEDDY, 0.45))
        reading_nook.place_rug("a soft colorful kids reading rug", size=0.9)

# === TEACHER ZONE: desk + chair, dressed with the classroom identity props ==========
with scene.RelativeGroup() as teacher_zone:
    t_desk = sized("a classic wooden teacher desk with drawers", TEACHER_DESK, 1.3)
    t_chair = scene.AddAsset("a black office task chair")
    teacher_zone.place_desk_chair(t_desk, t_chair)   # pose correct BY CONSTRUCTION
    if PHASE >= 2:
        teacher_zone.place_on_top([
            sized("a decorative vintage world globe on a stand", GLOBE, 0.3),
            scene.AddAsset("a stack of books"),
        ])

# === BACK-WALL STORAGE RUN: every fixture arrives PRE-STOCKED =======================
# Child height (<= 1.15 m) so kids reach it AND the interior cameras see over it.
with scene.RelativeGroup() as cubby_unit:
    cubby_unit.set_anchor(
        sized_h("a light wood kids cubby shelf stocked with colorful storage bins", CUBBY_BINS, 1.0))
    if PHASE >= 2:
        cubby_unit.place_on_top([scene.AddAsset("a leafy potted plant in a ceramic planter")])

with scene.RelativeGroup() as toyshelf_unit:
    toyshelf_unit.set_anchor(
        sized_h("a kids shelf stocked with colourful toys", TOYSHELF, 1.15))
    if PHASE >= 2:
        toyshelf_unit.place_on_top([sized("a set of natural wooden building blocks", BLOCKS, 0.3)])

# === THE ROOM ======================================================================
# modulate_scale=0.85: the RoomProportions vote ran 0.92 -> 0.9 -> 0.8 across the phases
# (held per render-wins-early). Applied ONCE, decisively, in the final phase -- and paired
# with the third activity table rather than taken to the full 0.8, since a kindergarten
# genuinely wants open floor to sit and play on (the garage's "circulation lane reads as
# empty" rule): a shrink alone would have bought the occupancy number at the cost of the
# room's whole point.
with scene.RoomGroup(modulate_scale=0.85, randomness=0.12) as room:
    # Plain colour + material words only. An accent clause in a texture string recolours
    # every wall (classroom v1); the colour here rides on the props instead.
    room.place_walls(floor_texture="light maple wood planks",
                     ceiling_texture="smooth white plaster",
                     wall_texture="smooth white painted plaster wall")

    # ---- CENTRE: the circle-time rug is the hero and reserves its own clear floor ----
    circle_rug = sized("a colorful alphabet letters oval kids area rug", ALPHABET_RUG, 2.6)
    room.place_on_center(circle_rug)

    # ---- ACTIVITY FIELD: three table+chair clusters ringing the circle-time rug -----
    # The third table is the plan's "construction center" AND the fix for a floor that
    # read empty: the shrink vote ran 0.92 -> 0.9 -> 0.8 (same direction, growing = a
    # genuinely sparse room). Filling the open floor beats over-shrinking a room whose
    # kid-scale furniture is small by definition (children_room: add a piece, then shrink).
    room.place_on_right(table_a)
    room.place_on_back_right(table_b)
    room.place_on_back_left(table_c)

    # ---- READING NOOK: left, under the window; books within reach on the wall -------
    # Pinned to the WALL, not dropped in the left floor SLOT: a slot group gets pushed
    # around by door clearance + randomness and the bean bags ended up stranded mid-floor
    # (bakery's window-bar drift). Wall placements accept composed groups -- use them
    # whenever "tucked against a wall" is the intent. A nook is a corner, not an island.
    room.place_on_left_wall_center(reading_nook)
    room.place_on_left_wall_right(
        sized_h("a wooden display stand full of colourful children's books", BOOK_DISP, 1.0))

    # ---- TEACHING WALL: teacher front-left, facing the class across the rug ---------
    room.place_on_front_left(teacher_zone, facing="back")
    room.face(teacher_zone, toward="back_wall")

    # ---- BACK WALL: the stocked storage run (a deliberate 3-item hero run) ----------
    room.place_on_back_wall_left(toyshelf_unit)
    room.place_on_back_wall_center(cubby_unit)
    room.place_on_back_wall_right(
        sized_h("a wooden toddler locker with colorful bins", TODDLER_LOCKER, 1.0))

    # Door in PHASE 1: its automatic clearance shapes the floor solve from the start.
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # Teaching wall: whiteboard centre + the ABC display beside it.
        room.place_on_wall_front_center(
            sized("a large white classroom whiteboard", WHITEBOARD, 2.0))
        room.place_on_wall_front_left(
            sized("a colorful ABC alphabet poster for a classroom", ABC_POSTER, 0.6))
        # Cheerful art, pre-scaled SMALL: place_on_wall_* derives mount height from the
        # art's height, so a big print hangs above a 5-year-old's eyeline (children_room).
        # The ocean canvas hangs over the LOW storage run -- legal, and it cannot be
        # occluded (the cubby's top is well below the art's bottom edge).
        room.place_on_wall_back_center(
            sized("a childrens ocean animals wall canvas", OCEAN_ART, 0.55))
        room.place_on_wall_right_center(
            sized("a childrens wall canvas with a red train", TRAIN_ART, 0.55))

        # STANDARD pane, not floor-to-ceiling: every opening renders as a black void, and
        # a full glazing turns the reading nook's wall into a wall of night (retail_store).
        room.place_window_standard("left_wall", position="center",
                                   curtain="bright cheerful patterned curtains")

        # FLUSH fixture only (a hanging fixture drops 1.5 m into the room and blows the
        # exposure out). density is a fixture COUNT that grows with floor area: ~0.015 is
        # the calibrated value for a ~50 m2 room (bookstore); the starfield lint polices it.
        room.add_lighting("a flat rectangular LED flush mount ceiling light", density=0.015)

scene.export("kindergarten_v1.blend")
