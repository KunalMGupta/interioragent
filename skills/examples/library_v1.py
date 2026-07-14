"""Library — "Grand Public Library Reading Room" (planner target: tmp/library/plan/plan.png).

Planner target: a warm, academic reading hall. Twin FLOOR-TO-CEILING walnut bookcases line the two
long walls to form a legible CORRIDOR; a long communal READING TABLE runs down the centre axis,
ringed with wooden chairs, each table wearing green banker's lamps under soft warm pendants; a cosy
LEATHER ARMCHAIR nook sits by a grand arched window (the focal end); a librarian REFERENCE DESK
anchors the entrance. Palette: walnut/oak, dark brass, green (lamps + upholstery), a patterned wool
rug, linen curtains, leather. Light is layered: window daylight + pendants + banker's lamps.

Layout — SYMMETRIC CORRIDOR (twin shelf rows) + a centre table column. The corridor runs
front<->back, so the LONG walls are LEFT + RIGHT and the SHORT walls are BACK + FRONT:
- LEFT wall  : a `place_row` of 4 floor-to-ceiling bookcases. `facing` is OMITTED so the heuristic
               turns the shelves' open side into the room (book spines in).
- RIGHT wall : the mirror-image shelf run. Loading BOTH long walls is what makes the room read as a
               deep corridor rather than a room that happens to own some books.
- CENTRE     : the HERO — a column of communal reading tables (chairs on both long sides, green
               banker's lamps on top). It sits on the centre axis because the corridor's whole point
               is that you look down it and see the reading hall.
- BACK wall  : the focal end. The arched window (short, so the night-void stays small) + the cosy
               leather armchair nook in one corner + a tall plant in the other to balance it. The
               nook faces the ROOM, not its own side table.
- FRONT wall : the entrance end. Door on the right; the card catalog flush on the wall; and the
               librarian reference station standing OFF the wall on the front-LEFT floor third, so
               the librarian has real space behind the desk and it clears the centre table column.
- The long walls are full-height bookcases with NO headroom, so all wall art lives on the two short
               walls (back = botanical print + antique map, front = portrait + clock).

Identity comes from the GREEN BANKER'S LAMPS: a bare reading table reads generic, and the green
domes + the patterned wool rug make the hall read "library" instantly. They must be shrunk hard
(modulate_scale=0.3) — place_on_top oversizes small props to chair scale.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/library_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 dresses the surfaces and the floor; phase 3 adds the window,
the pendants and the wall decor.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Library", seed=36)

# --- pinned assets (audited previews; retrieval stress test in scratchpad/library_stress) ---
SHELF   = "hssd/b356640d3d9d976c8ea2a29ae5ff48467e32262b"   # dark walnut bookcase, leather-bound books + lower cabinet (GOOD)
TABLE   = "hssd/e5c0975d4c5bae809e505e440e74a449d503f4e2"   # long walnut rectangular table; retrieved as "long rectangular
                                                            # dark walnut DINING table" (0.71) — "library reading table" was
                                                            # weak (0.53) and returned white legs
CHAIR   = "hssd/b98286cc0fed6b814d3b5cf4afc825514ed51b54"   # wooden library chair, cushioned seat, slatted back
LAMP    = "hssd/721b75b49772e53e01785e943bfe8832fe3f9dfe"   # GREEN banker's dome desk lamp (the signature prop) — it exists
                                                            # in the pool, and it MUST be shrunk to sit right on a table
REFDESK = "hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860"   # curved wooden reception/reference desk — "reference desk" and
                                                            # "checkout counter" route to a BOOKCASE; the reception wording
                                                            # (0.81) is the right stand-in for a librarian service desk
ARMCHR  = "hssd/613ba909e59984d3a908ec4b52344bcd689fa79b"   # brown tufted leather reading armchair (the nook hero)
FLOOR   = "hssd/69fa8415108e7438a412ec0a52a55983f39119df"   # slender brass floor reading lamp
CATALOG = "hssd/14532900bdcd0f7a4599249c4a3a8a74c7facb3f"   # dark multi-drawer card-catalog cabinet (a faithful stand-in;
                                                            # no true card catalog in the pool)

# ============================ CENTRE: the communal reading table unit (hero) ============================
# Build ONE table unit (table + 3 chairs each long side + 2 banker's lamps on top), duplicate to a
# column of 2 -> a long communal reading run down the centre axis. place_on_top runs ONCE (per design
# principle: compose the unit once, then N * unit gives identical copies for free).
def reading_unit():
    with scene.AroundGroup(sparsity=0.28, jitter=0.35) as u:
        u.set_anchor(scene.AddAsset("a long walnut rectangular reading table", asset_id=TABLE))
        u.place_rectilinear(longer_side1=3 * scene.AddAsset("a wooden library chair with a cushioned seat", asset_id=CHAIR),
                            longer_side2=3 * scene.AddAsset("a wooden library chair with a cushioned seat", asset_id=CHAIR))
        if PHASE >= 2:
            # banker's lamps read SMALL — place_on_top oversizes them to chair-scale; 0.3 sits right on a table
            u.place_on_top(2 * scene.AddAsset("a green glass bankers desk lamp", asset_id=LAMP, modulate_scale=0.3))
            u.place_rug("a traditional patterned green and cream wool rug", size=0.9)
    return u

with scene.GridGroup(sparsity=0.4, randomness=0.1) as reading_hall:   # two tables in a centre column
    reading_hall.place_grid(2 * reading_unit(), cols=1)

# ============================ LEFT + RIGHT long walls: twin bookcase corridor ============================
left_shelves  = 4 * scene.AddAsset("a tall wooden bookshelf full of books", asset_id=SHELF)
right_shelves = 4 * scene.AddAsset("a tall wooden bookshelf full of books", asset_id=SHELF)
with scene.GridGroup(sparsity=0.04, randomness=0.0) as shelves_left:
    shelves_left.place_row(left_shelves)
with scene.GridGroup(sparsity=0.04, randomness=0.0) as shelves_right:
    shelves_right.place_row(right_shelves)

# ============================ BACK end: the cosy leather ARMCHAIR reading nook ============================
# Design principle: a seat always gets a table within reach + its own task light, built as ONE nook.
with scene.RelativeGroup() as side_tbl:
    side_tbl.set_anchor(scene.AddAsset("a small round wooden side table"))
    if PHASE >= 2:
        side_tbl.place_on_top(scene.AddAsset("a stack of hardcover books", modulate_scale=0.6))  # read small on the side table
with scene.RelativeGroup() as nook:
    nook.set_anchor(scene.AddAsset("a cozy brown leather reading armchair", asset_id=ARMCHR))
    nook.place_on_right(side_tbl)                                              # table within reach
    nook.place_on_back_left(scene.AddAsset("a slender brass floor reading lamp", asset_id=FLOOR))  # its task light
    if PHASE >= 2:
        nook.place_rug("a small patterned wool rug", size=0.7)

# ============================ FRONT: the librarian REFERENCE station ============================
# A reference/reception desk is an INVERTED workstation (lobby.md): the display counter faces the
# patrons, the librarian + chair sit BEHIND. Build it as a WorkstationGroup with desk.set_rotation(180)
# to flip the counter to the patron side and make the staff side the operator (+Z); place it on a floor
# THIRD (not flush on the wall) so the librarian has real space behind the desk.
_ref_desk = scene.AddAsset("a curved wooden reception front desk", asset_id=REFDESK, modulate_scale=1.2)  # 1.2x bigger
_ref_desk.set_rotation(180)
with scene.WorkstationGroup() as reference:
    reference.set_anchor(_ref_desk)
    reference.place_chair(scene.AddAsset("a brown leather office task chair on casters"), gap=True)
    if PHASE >= 2:
        reference.place_accessories([scene.AddAsset("a green glass bankers desk lamp", asset_id=LAMP, modulate_scale=0.3),
                                     scene.AddAsset("a stack of hardcover books", modulate_scale=0.45)])

# a rolling book cart to fill the browsing aisle (audited: white 3-tier iron rolling cart)
book_cart = scene.AddAsset("a rolling library book cart trolley on wheels")

# ============================ ROOM ============================
# modulate_scale 0.9: at 1.1 the hall read under-filled (VLM flipped 1.25 -> 0.8); 0.9 tightens the
# corridor while keeping circulation. Occupancy target is a render call, not the oscillating vote.
with scene.RoomGroup(modulate_scale=0.9, randomness=0.12) as room:
    room.place_walls(floor_texture="warm herringbone parquet oak wood flooring",
                     ceiling_texture="soft cream plaster ceiling",
                     wall_texture="warm ivory plaster wall")
    # CENTRE hero = communal reading tables (aligned down the corridor axis)
    room.place_on_center(reading_hall)
    # LEFT + RIGHT long walls = twin bookcase runs (omit facing -> heuristic faces shelves into room)
    room.place_on_left_wall_center(shelves_left)
    room.place_on_right_wall_center(shelves_right)
    # BACK end (window end) = the armchair nook (nook faces the room, NOT its own side table -- the
    # "rotate armchair to face the table" VLM vote is declined as noise)
    room.place_on_back_left_corner(nook, facing="front")
    # FRONT-LEFT = the reference station stands OFF the wall on a floor third (operator +Z toward the
    # front wall via facing="front" -> librarian faces the room, patron counter to the room, chair behind).
    # Placed front-LEFT so it clears the centre reading-table column (plain place_on_front jammed into it).
    room.place_on_front_left(reference, facing="front")
    # card catalog flush on the front wall behind the reference station; door on the right.
    room.place_on_front_wall_left(scene.AddAsset("a dark wooden card catalog cabinet with many small drawers", asset_id=CATALOG))
    room.place_on_right(book_cart)                                             # fill the browsing aisle
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 2:
        # a tall plant balances the nook at the other end of the window wall
        room.place_on_back_right_corner(scene.AddAsset("a tall potted plant with lush green leaves"))

    if PHASE >= 3:
        # focal arched-window read on the back wall (modest pane -> the "black void" stays small); linen drapes
        room.place_window_standard("back_wall", position="center", curtain="floor-length cream linen curtains")
        # warm pendants over the hall -- a COMPACT drum pendant, never a chandelier (blows the room out).
        # TWO coupled levers: modulate_scale is fixture SIZE (drum renders ~1.5 m + drops to table height at
        # 1.0 -> shrink to ~0.4); but count ~= density/footprint, so shrinking the fixture MULTIPLIES the
        # count (0.35 @ density 0.12 -> a 35-pendant starfield). So drop density in step -> ~8 tidy pendants.
        room.add_lighting("a warm fabric drum pendant ceiling light", density=0.025, modulate_scale=0.4)
        # gilded/academic wall decor over the low entrance supports (keeps art clear of the ceiling)
        room.place_on_wall_front_center(scene.AddAsset("a framed classical oil painting portrait in a gold frame"))
        room.place_on_wall_front_left(scene.AddAsset("a large round wall clock with roman numerals"))
        # a few library-themed framed artworks on the back wall (pre-scaled via width= so the mount height
        # clears the ceiling; the long walls are full-height bookcases with no headroom for art)
        room.place_on_wall_back_left(scene.AddAsset("a framed vintage botanical illustration print in a gold frame", width=0.7))
        room.place_on_wall_back_right(scene.AddAsset("a framed antique world map in a wooden frame", width=0.8))

scene.export("library_v1.blend")
