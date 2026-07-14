"""
Bookstore — "Curved Spine Bookstore: Transparent Entry, Warm Shelving, and Cozy
Browsing Nooks" (planner headline; plan at tmp/plan_a_bookstore/plan.png).

Look (from the plan): warm honey-timber shelving loaded with books everywhere,
a central browsing spine of face-out book displays framing a clear centre aisle,
a "new releases" hero display table piled with books, a pastel reading nook
(dusk-pink + mint barrel chairs around a round timber table on a soft rug), a
wooden book cart in the aisle, and a checkout by the storefront entry.

Zone map (retail spine + perimeter loop, per the procedural signature):
  - LEFT + RIGHT walls = long runs of stocked honey bookcases (the loaded long walls).
  - LEFT + RIGHT floor = spine rows of double-sided face-out book displays,
    running front<->back to frame the centre aisle (retail_store rail pattern).
  - CENTER             = the HERO: new-releases display table massed with books.
  - BACK               = focal book display stand (visible from the entry) + the
    pastel reading nook (back-left) + plant (back-right corner) + neon sign above.
  - FRONT              = storefront: standard window (never floor-to-ceiling — the
    black-void lesson) + door on the right + checkout counter front-right, facing
    back so the cash-wrap sees the door.

Identity = PRODUCT at viewing height (jewelry_shop lesson): every fixture is
PRE-STOCKED with books (toy_shop lesson) — stocked wall bookcases, face-out
displays full of covers, book stacks massed on the display table + counter + nook.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the
floor layout (~1 min); phase 2 adds on-top dressing; phase 3 walls/window/lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Bookstore", seed=21)

# --- pinned pieces (gate-3 audit; every mesh eyeballed or verified in a prior scene) ---
WALL_SHELF   = "hssd/2db50fb1f8120974d6157ae9aff704a4fc9d181f"   # light honey bookcase, WELL-STOCKED shelves + lower cabinet
SPINE_DISP   = "hssd/7b9c92c0772bb1730ae9b1596566c449861be6e1"   # double-sided face-out book display, light wood, filled covers
DISPLAY_TBL  = "hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f"   # low wood-top + black-metal display table (retail_store hero)
COUNTER      = "hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860"   # curved wood-front reception/cash-wrap counter
POS          = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"   # touchscreen POS terminal
BOOK_STAND   = "hssd/f3a8d459c4e019b28b926e55d56e087cc82593fa"   # angled stand FULL of colourful books (focal display)
PINK_CHAIR   = "hssd/d4c936c5a9a20fcfe79fb3fcdd4e6d11ac191a84"   # dusk-pink barrel swivel chair (pin-for-palette)
GREEN_CHAIR  = "future/18d02c7b-f561-43bb-933a-d788af8d90eb"     # mint/sage tub lounge chair (pin-for-palette)
COFFEE_TBL   = "hssd/d4bff7307857a9634e9785ce7febc342217cce7c"   # natural wood round side table (nook)
BOOK_CART    = "hssd/458fbf1ed33949dfeacc3e20047cde5c1d774561"   # rustic wooden book cart on wheels
BOOK_STACK   = "hssd/55a5fd8649bd9cce577ea26cedd313ad4ec26bae"   # stack of decorative books, colourful spines
NEON         = "custom/d5884fb54a16d8f18a19a40989fcca074f5fcb84" # neon store sign, glowing tube lettering

scene.prefetch_assets([
    "a light wooden bookcase filled with books",
    "a double-sided wooden face-out book display filled with books",
    "a low wooden merchandise display table with a black metal frame",
    "a curved wood-front retail checkout counter",
    "a point of sale touchscreen terminal",
    "a wooden display stand full of colourful books",
    "a dusk pink round barrel lounge chair",
    "a mint green round tub lounge chair",
    "a natural wood round side table",
    "a rustic wooden book cart on wheels",
    "a stack of decorative books with colourful spines",
    "a stack of hardcover books",
    "a neon store brand sign with glowing tube lettering",
    "a soft neutral wool area rug",
    "a paper retail shopping bag",
    "a large potted indoor plant in a modern planter",
    "a flat round LED flush mount ceiling light",
    "a framed vintage botanical illustration print in a gold frame",
])


def sized_h(query, asset_id, height):
    """Pinned asset scaled uniformly to a target HEIGHT (fixtures vary in native
    proportion; a height target gives a consistent standing look — toy_shop lesson)."""
    o = scene.AddAsset(query, asset_id=asset_id)
    o.scale(o.get_width() * height / o.get_height())
    return o


# --- LEFT + RIGHT walls: long runs of stocked honey bookcases (3 per side) ------
def shelf_run():
    with scene.GridGroup(sparsity=0.04) as run:
        run.place_row([sized_h("a light wooden bookcase filled with books", WALL_SHELF, 2.1)
                       for _ in range(3)])
    return run

shelves_left = shelf_run()
shelves_right = shelf_run()

# --- LEFT + RIGHT floor: spine rows of double-sided face-out displays -----------
def spine_row():
    with scene.GridGroup(sparsity=0.3, randomness=0.05) as row:
        row.place_row([sized_h("a double-sided wooden face-out book display filled with books",
                               SPINE_DISP, 1.35) for _ in range(2)])
    return row

spine_left = spine_row()
spine_right = spine_row()

# --- CENTER hero: the "new releases" display table massed with books ------------
with scene.RelativeGroup() as new_releases:
    new_releases.set_anchor(scene.AddAsset(
        "a low wooden merchandise display table with a black metal frame",
        asset_id=DISPLAY_TBL))
    if PHASE >= 2:
        new_releases.place_on_top([
            scene.AddAsset("a stack of decorative books with colourful spines", asset_id=BOOK_STACK),
            scene.AddAsset("a stack of hardcover books"),
            scene.AddAsset("a stack of decorative books with colourful spines", asset_id=BOOK_STACK),
        ])
        new_releases.place_rug("a soft neutral wool area rug", size=0.9)

# --- BACK-LEFT: the pastel reading nook (chairs + round table, one unit) --------
with scene.AroundGroup(sparsity=0.25, jitter=0.3) as nook:
    _nook_tbl = scene.AddAsset("a natural wood round side table", asset_id=COFFEE_TBL)
    nook.set_anchor(_nook_tbl)
    _pink = scene.AddAsset("a dusk pink round barrel lounge chair", asset_id=PINK_CHAIR)
    _mint = scene.AddAsset("a mint green round tub lounge chair", asset_id=GREEN_CHAIR)
    nook.place_arc([_pink, _mint])
    nook.face(_pink, toward=_nook_tbl)
    nook.face(_mint, toward=_nook_tbl)
    if PHASE >= 2:
        nook.place_on_top([scene.AddAsset("a stack of hardcover books", modulate_scale=0.5)])
        nook.place_rug("a soft neutral wool area rug", size=1.0)

# --- FRONT-RIGHT: checkout by the entry (counter + POS + bag, sees the door) ----
pos = scene.AddAsset("a point of sale touchscreen terminal", asset_id=POS, modulate_scale=0.35)
with scene.RelativeGroup() as checkout:
    checkout.set_anchor(scene.AddAsset("a curved wood-front retail checkout counter",
                                       asset_id=COUNTER))
    if PHASE >= 2:
        checkout.place_on_top([
            pos,
            scene.AddAsset("a stack of decorative books with colourful spines", asset_id=BOOK_STACK),
            scene.AddAsset("a paper retail shopping bag"),
        ])

# --- the room --------------------------------------------------------------------
# modulate_scale 0.85: RoomProportions voted 0.75 (Ph1) -> 0.8 (Ph2); held per
# render-wins-early, applied one decisive shrink in the final phase (laundromat
# pattern — expect possibly one more step if the vote persists).
with scene.RoomGroup(modulate_scale=0.85, randomness=0.12) as room:
    room.place_walls(floor_texture="warm light oak wood plank floor",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="warm cream plaster")

    # long walls carry the loaded bookcase runs (omit facing -> shelves face the room)
    room.place_on_left_wall_center(shelves_left)
    room.place_on_right_wall_center(shelves_right)

    # browsing spine: face-out display rows run front<->back, framing the centre aisle
    room.place_on_left(spine_left, facing="left")
    room.place_on_right(spine_right, facing="left")

    # hero new-releases table on the centre axis; book cart fills the back aisle
    room.place_on_center(new_releases)
    room.place_on_back(scene.AddAsset("a rustic wooden book cart on wheels",
                                      asset_id=BOOK_CART), facing="right")

    # focal display on the back wall (visible from the entry), pastel nook back-left
    room.place_on_back_wall_center(sized_h("a wooden display stand full of colourful books",
                                           BOOK_STAND, 1.2))
    room.place_on_back_left_corner(nook, facing="front")

    # checkout by the storefront, facing back into the store (sees the door)
    room.place_on_front_right(checkout, facing="back")

    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        room.place_on_back_right_corner(
            scene.AddAsset("a large potted indoor plant in a modern planter"),
            facing="front")
        room.place_on_wall_back_center(
            scene.AddAsset("a neon store brand sign with glowing tube lettering", asset_id=NEON))
        room.place_on_wall_front_left(
            scene.AddAsset("a framed vintage botanical illustration print in a gold frame",
                           width=0.7))
        # storefront: modest pane + the checkout/displays in the foreground (void lesson)
        room.place_window_standard("front_wall", position="center",
                                   curtain="light cream sheer curtains")
        # 56 m^2 floor: density 0.04 tiled a 35-fixture starfield ([Lint], budget ~17);
        # 0.015 gives a calm ceiling (coffee-shop small-room lesson)
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.015)

    if PHASE >= 2:
        room.rotate(pos, 180)   # POS screen back to the approaching customer

scene.export("bookstore_v1.blend")
