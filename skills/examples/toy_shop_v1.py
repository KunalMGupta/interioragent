"""Toy shop — "Bright Primary-Play Toy Store" (planner headline).

Planner target: a cheerful children's toy / comic / book shop. White walls, warm-oak laminate floor,
bright primary-colour toys as the accent. Zones: a perimeter merchandising ring, a central play
island, a teepee reading corner + bean-bag seating nook, and a near-entrance checkout.

Layout — a PERIMETER MERCH RING around a CENTRAL PLAY ISLAND (say WHY each slot is what it is):
- BACK wall  : the merch ring's face — toy shelf (crowned with the dollhouse) / the long comic-book
               wall dead centre (it is the widest, fullest fixture, so it reads as the focal wall and
               the neon sign hangs above it) / toy shelf (crowned with blocks). Three display tables
               mass boxed toys on the floor in front of it.
- LEFT wall  : the ring continues — book/game shelf (giraffe crown) + a stocked toy shelf. Its RIGHT
               slot holds the children's book display, which feeds the front-left reading corner.
- RIGHT wall : book/game shelf (train crown) + the figurine tower (a narrow accent, not a mass), and
               the DOOR at its right — the entrance lands beside the checkout.
- CENTRE     : the hero. A low round kids' table on a round multicolour rug, train + blocks on top,
               flanked by the rocking horse (left) and the ride-on car (right) — the two heroes that
               must be seen from the door.
- FRONT      : the storefront window centre; the teepee reading nook front-left (teepee + big teddy
               in the corner); the bean-bag seating nook front-centre; the checkout front-right,
               facing back into the store so the customer meets it on the way out.

Identity comes from the PRE-STOCKED shop fixtures (`ShopFixtureRetriever`): the shelves themselves
ship packed with toys / comics / game boxes, so most need NO crown at all. Do not fake a stocked shop
by crowning empty shelves — a generic gondola reads as a shoe rack and a too-tall shelf auto-clamps
into thin EMPTY verticals. Fixtures are scaled by HEIGHT (`sized_h`), not width: shop shelves vary
wildly in native proportion and a width target squashes or blows up the standing height.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/toy_shop_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 dresses the surfaces (shelf crowns, table props, rugs); phase 3
adds the neon wall sign, the storefront window and the lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

# --- pinned pieces (asset-first kickoff + stress test; perimeter fixtures from the new ShopFixtureRetriever) ---
TOYSHELF   = "future/1fc1d19b-87b5-4d16-8cfa-69d642a37dba"     # cartoon kids' shelves PRE-STOCKED with toys (1.2x1.49)
COMICSHELF = "custom/61cd86192945aa341da03d3033c8a9d1638f158c" # long shelf packed w/ colourful comics, red base (2.2x1.3x0.48) -- VISUALLY VERIFIED (91fa23e0 caption said "comic" but its MESH is a clothing rack)
GAMESHELF  = "future/1ecf937a-58e9-4516-b9c9-dfbf6535950c"     # cartoon shelf of books/game boxes (1.2x0.94)
FIGURINES  = "future/b8812342-67aa-4ca0-adac-24f5a58fa266"     # narrow tiered tower of figurines (0.5x1.42, accent)
BOOK_DISP  = "hssd/f3a8d459c4e019b28b926e55d56e087cc82593fa"   # book display FULL of colourful children's books
TEDDY      = "future/3e18ed6d-9f79-46cf-afe7-ac2a3512570d"     # large beige teddy bear plush (hero)
GIRAFFE    = "future/747f89ae-5054-4c60-a8a9-5745cae6509a"     # plush giraffe (reading-nook plush)
ROCKING    = "future/439cb8bf-a806-458f-8cec-87a154587e4e"     # red wooden rocking horse (hero)
TRAIN      = "future/751feb3c-8efa-4262-ae61-3ec4fa912dc4"     # colourful wooden toy train (on the island)
DOLLHOUSE  = "hssd/7a3e0a25e205a9e7fd61d99b07a139206aa25829"   # white wooden dollhouse (shelf-top hero)
TEEPEE     = "hssd/19401d9b9e4155e1e9d99d9ea9c61c525a211dba"   # colourful kids' teepee tent (nook)
KIDS_TABLE = "hssd/4b9ff34fe5d44b8ef57eed9f3d2001df29127a56"   # round natural kids' activity table (island/tables)
COUNTER    = "hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860"   # curved wood-front checkout counter
RIDE_ON    = "hssd/c9dd11b6d8113a4f2d55fe6442f242e9f491e97f"   # vintage kids' ride-on car (hero)
RUG        = "hssd/6f26eb169111a17c566bfb1ed56bd82adc2db686"   # round concentric multicolour rug (island)
CUSHION    = "future/e3648671-aa1a-4c6f-83cb-d8b4c79761c4"     # red floor cushion
BEANBAG_P  = "hssd/256102db5561f21d2a2e071e76798bfb54fb82f1"   # pink kids' bean-bag chair (0.9m)
BEANBAG_B  = "hssd/0598a08d6d048ed49026adf13247d4586033c864"   # blue star kids' bean-bag chair (0.75m)
FLOORCUSH  = "hssd/859e59d95cf7d15023e25c9ac5c93931553caed3"   # colourful blue/yellow floor cushion pad (1.2m)
BLOCKS     = "hssd/6561f279b05e443c3e5d9c9951f9afedae97a66c"   # natural wooden building blocks (on-top)
NEON       = "custom/d5884fb54a16d8f18a19a40989fcca074f5fcb84" # neon store sign, glowing tube lettering
POS        = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"   # POS touchscreen terminal
BOARDGAME  = "hssd/d5f0014aa089653a8c5a142ab966d73a9af40298"   # colourful board-game box (display-table prop)

scene = SceneProgRoom("ToyShop", seed=42)


def sized(query, asset_id, width):
    """Retrieve a pinned asset and set its footprint WIDTH (uniform scale, literal metres)."""
    o = scene.AddAsset(query, asset_id=asset_id)
    o.scale(width)
    return o


def sized_h(query, asset_id, height):
    """Retrieve a pinned asset and set its HEIGHT (uniform scale, aspect preserved). Used for the
    perimeter shelves so each stands at a sensible RETAIL height regardless of native proportions."""
    o = scene.AddAsset(query, asset_id=asset_id)
    o.scale(o.get_width() * height / o.get_height())
    return o


SHELVES = {   # pre-stocked shop fixtures from ShopFixtureRetriever (id, query, STAND HEIGHT in m)
    "toy":   (TOYSHELF,   "a kids' retail shelf stocked with colourful toys", 1.5),
    "comic": (COMICSHELF, "a long retail shelf packed with colourful comic books, red base", 1.4),
    "game":  (GAMESHELF,  "a retail shelf of children's books and game boxes", 1.35),
    "book":  (BOOK_DISP,  "a display stand full of colourful children's books", 1.1),
    "figs":  (FIGURINES,  "a tiered tower of small toy figurines", 1.42),
}


def shelf_unit(kind, crown_query=None, crown_id=None, crown_w=None):
    """A perimeter merch unit — a PRE-STOCKED toy / comic / book shop shelf sized to a proper
    standing height, optionally crowned with one hero toy on top. Returned as a RelativeGroup so a
    single place_on_*_wall_* call seats the shelf (and its crown) against the wall (clamped to
    span + ceiling). The crown is phase-2 dressing: gated (and RETRIEVED) INSIDE the with-block, so
    a phase-1 build pays for the shelf only — a gate placed outside the block would silently drop it."""
    sid, sq, sh = SHELVES[kind]
    with scene.RelativeGroup() as s:
        s.set_anchor(sized_h(sq, sid, sh))
        if PHASE >= 2 and crown_query:
            s.place_on_top([sized(crown_query, crown_id, crown_w)])
    return s


def display_table(tops):
    """A low kids' table massing colourful boxed toys / games / plush on top. `tops` is a THUNK (a
    zero-arg callable) so the props are only RETRIEVED in phase >= 2, inside the with-block."""
    with scene.RelativeGroup() as t:
        t.set_anchor(sized("a low round wooden kids' display table", KIDS_TABLE, 1.0))
        if PHASE >= 2:
            t.place_on_top(tops())
    return t


# --- central play island: round table + train + blocks, grounded on a round rug ---
with scene.RelativeGroup() as island:
    island.set_anchor(sized("a round natural wooden kids' activity table", KIDS_TABLE, 1.1))
    if PHASE >= 2:
        island.place_on_top([sized("a colourful wooden toy train set", TRAIN, 0.45),
                             sized("a set of natural wooden building blocks", BLOCKS, 0.3)])
        island.place_rug("a round concentric multicolour kids' area rug", size=1.0, asset_id=RUG)

# --- little seating / reading nook: a rug grounding two bean-bag chairs + a big floor cushion.
#     (was a single 0.5 m cushion — invisible from above; bumped to a real, visibly-scaled cluster.) ---
with scene.RelativeGroup() as seating:
    # floor cluster (NOT place_on_top — that tiles a flat rug into microscopic slots and hides them):
    # a big floor cushion in the middle flanked by two bean-bag chairs, all grounded on a rug.
    seating.set_anchor(sized("a large colourful kids' floor cushion", FLOORCUSH, 1.1))
    seating.place_on_left(sized("a pink kids' bean-bag chair", BEANBAG_P, 0.9))
    seating.place_on_right(sized("a blue kids' bean-bag chair", BEANBAG_B, 0.8))
    if PHASE >= 2:
        seating.place_rug("a colourful round kids' area rug", size=1.0, asset_id=RUG)

# --- checkout / cash-wrap near the entrance (counter + POS + shopping bag) ---
pos = None   # the POS is phase-2 dressing; the late rotate() below is gated on it
with scene.RelativeGroup() as checkout:
    checkout.set_anchor(scene.AddAsset("a curved wood-front retail checkout counter", asset_id=COUNTER))
    if PHASE >= 2:
        pos = sized("a point of sale touchscreen terminal", POS, 0.35)
        checkout.place_on_top([pos, scene.AddAsset("a paper retail shopping bag")])

# --- display tables massing boxed toys / board games / plush (colour identity, floor density) ---
table_games = display_table(lambda: [sized("a colourful board game box", BOARDGAME, 0.32),
                                     scene.AddAsset("a colourful jigsaw puzzle box"),
                                     sized("a set of natural wooden building blocks", BLOCKS, 0.28)])
table_plush = display_table(lambda: [sized("a plush giraffe stuffed animal toy", GIRAFFE, 0.28),
                                     scene.AddAsset("a small colourful plush toy")])
table_cars  = display_table(lambda: [sized("a colourful board game box", BOARDGAME, 0.3),
                                     scene.AddAsset("a colourful toy car")])

# --- perimeter merch ring: PRE-STOCKED toy/comic/book shop shelves, a few crowned with a hero toy ---
back_l = shelf_unit("toy",   "a white wooden dollhouse toy", DOLLHOUSE, 0.5)
back_c = shelf_unit("comic")                                                 # tall comic-book wall, reads full (neon above)
back_r = shelf_unit("toy",   "a set of natural wooden building blocks", BLOCKS, 0.4)
left_l = shelf_unit("game",  "a plush giraffe stuffed animal toy", GIRAFFE, 0.4)
left_c = shelf_unit("toy")                                                   # stocked toy shelf, reads full on its own
right_l = shelf_unit("game", "a colourful wooden toy train set", TRAIN, 0.4)
right_c = shelf_unit("figs")                                                 # figurine tower accent

with scene.RoomGroup(modulate_scale=0.98, randomness=0.1) as room:   # tightened (VLM wanted less floor)
    room.place_walls(floor_texture="warm light oak laminate wood floor",
                     ceiling_texture="white", wall_texture="bright white")

    # Perimeter merch ring (back + both side walls), each crowned with a toy.
    room.place_on_back_wall_left(back_l, facing="front")
    room.place_on_back_wall_center(back_c, facing="front")
    room.place_on_back_wall_right(back_r, facing="front")
    room.place_on_left_wall_left(left_l, facing="right")
    room.place_on_left_wall_center(left_c, facing="right")
    room.place_on_right_wall_left(right_l, facing="left")
    room.place_on_right_wall_center(right_c, facing="left")

    # Central play island + flanking hero playthings.
    room.place_on_center(island)
    room.place_on_left(sized("a red wooden rocking horse", ROCKING, 0.9), facing="right")
    room.place_on_right(sized("a vintage kids' ride-on car toy", RIDE_ON, 0.85), facing="left")

    # Colourful display tables filling the floor.
    room.place_on_back_left(table_games)
    room.place_on_back_right(table_plush)
    room.place_on_back(table_cars)

    # Reading nook — front-left corner: teepee + book display + big teddy + a floor cushion.
    room.place_on_front_left(sized("a colourful kids' teepee tent", TEEPEE, 1.15), facing="back")
    room.place_on_left_wall_right(scene.AddAsset("a wooden display stand full of colourful children's books", asset_id=BOOK_DISP), facing="right")
    room.place_on_front_left_corner(sized("a large beige teddy bear plush", TEDDY, 0.6), facing="back")
    room.place_on_front(seating)   # the bean-bag + floor-cushion seating nook

    # Checkout near the entrance (front-right), facing back into the store.
    room.place_on_front_right(checkout, facing="back")

    # Entrance, near the checkout. UNGATED in phase 1: its auto clearance shapes the floor solve.
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        room.rotate(pos, 180)   # keep the checkout screen facing the approaching customer

    if PHASE >= 3:
        # Brand focal wall sign + storefront glazing + light.
        room.place_on_wall_back_center(scene.AddAsset("a colourful neon toy store sign with glowing tube lettering", asset_id=NEON))
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.05)   # 0.08 packed the ceiling
        room.place_window_standard("front_wall", position="center")   # storefront pane

scene.export("toy_shop_v1.blend")
