"""
Library — "Grand Public Library Reading Room" (planner target: tmp/library/plan/plan.png).

Look (from the plan): a warm, academic reading hall. Twin FLOOR-TO-CEILING walnut bookcases line
the two long walls to form a legible CORRIDOR; a long communal READING TABLE runs down the centre
axis, ringed with wooden chairs, each table wearing green banker's lamps under soft warm pendants;
a cosy LEATHER ARMCHAIR nook sits by a grand arched window (the focal end); a librarian REFERENCE
DESK anchors the entrance. Palette: walnut/oak, dark brass, green (lamps + upholstery), a patterned
wool rug, linen curtains, leather. Light is layered: window daylight + pendants + banker's lamps.

Zone map (corridor runs front<->back; long walls = LEFT + RIGHT):
  - LEFT + RIGHT (long) = twin floor-to-ceiling BOOKCASE runs (the corridor walls).
  - CENTRE             = the HERO: a column of communal READING TABLES + chairs + banker's lamps.
  - BACK (short)       = the grand arched WINDOW (focal) + the leather ARMCHAIR reading nook + plant.
  - FRONT (short)      = entrance DOOR + the librarian REFERENCE desk + card catalog.

Phase 1: bookcase corridor + central reading tables (+chairs, +banker's lamps) + reference desk.
Phase 2: patterned rug, the armchair nook (chair+side table+floor lamp+books), plant, card catalog.
Phase 3: arched window + linen curtains, warm pendants, portrait + clock, a book cart, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Library", seed=36)

# --- pinned assets (audited previews; retrieval stress test in scratchpad/library_stress) ---
_SHELF   = "hssd/b356640d3d9d976c8ea2a29ae5ff48467e32262b"   # dark walnut bookcase, leather-bound books + lower cabinet (GOOD)
_TABLE   = "hssd/e5c0975d4c5bae809e505e440e74a449d503f4e2"   # long walnut rectangular table (black splayed legs; warm top)
_CHAIR   = "hssd/b98286cc0fed6b814d3b5cf4afc825514ed51b54"   # wooden library chair, cushioned seat, slatted back
_LAMP    = "hssd/721b75b49772e53e01785e943bfe8832fe3f9dfe"   # GREEN banker's dome desk lamp (the signature prop)
_REFDESK = "hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860"   # curved wooden reception/reference desk
_ARMCHR  = "hssd/613ba909e59984d3a908ec4b52344bcd689fa79b"   # brown tufted leather reading armchair (the nook hero)
_FLOOR   = "hssd/69fa8415108e7438a412ec0a52a55983f39119df"   # slender brass floor reading lamp
_CATALOG = "hssd/14532900bdcd0f7a4599249c4a3a8a74c7facb3f"   # dark multi-drawer card-catalog cabinet

# ============================ CENTRE: the communal reading table unit (hero) ============================
# Build ONE table unit (table + 3 chairs each long side + 2 banker's lamps on top), duplicate to a
# column of 2 -> a long communal reading run down the centre axis. place_on_top runs ONCE (per design
# principle: compose the unit once, then N * unit gives identical copies for free).
def reading_unit():
    with scene.AroundGroup(sparsity=0.28, jitter=0.35) as u:
        u.set_anchor(scene.AddAsset("a long walnut rectangular reading table", asset_id=_TABLE))
        u.place_rectilinear(longer_side1=3 * scene.AddAsset("a wooden library chair with a cushioned seat", asset_id=_CHAIR),
                            longer_side2=3 * scene.AddAsset("a wooden library chair with a cushioned seat", asset_id=_CHAIR))
        # banker's lamps read SMALL — place_on_top oversizes them to chair-scale; 0.3 sits right on a table
        u.place_on_top(2 * scene.AddAsset("a green glass bankers desk lamp", asset_id=_LAMP, modulate_scale=0.3))
        u.place_rug("a traditional patterned green and cream wool rug", size=0.9)
    return u

with scene.GridGroup(sparsity=0.4, randomness=0.1) as reading_hall:   # two tables in a centre column
    reading_hall.place_grid(2 * reading_unit(), cols=1)

# ============================ LEFT + RIGHT long walls: twin bookcase corridor ============================
left_shelves  = 4 * scene.AddAsset("a tall wooden bookshelf full of books", asset_id=_SHELF)
right_shelves = 4 * scene.AddAsset("a tall wooden bookshelf full of books", asset_id=_SHELF)
with scene.GridGroup(sparsity=0.04, randomness=0.0) as shelves_left:
    shelves_left.place_row(left_shelves)
with scene.GridGroup(sparsity=0.04, randomness=0.0) as shelves_right:
    shelves_right.place_row(right_shelves)

# ============================ BACK end: the cosy leather ARMCHAIR reading nook ============================
# Design principle: a seat always gets a table within reach + its own task light, built as ONE nook.
with scene.RelativeGroup() as side_tbl:
    side_tbl.set_anchor(scene.AddAsset("a small round wooden side table"))
    side_tbl.place_on_top(scene.AddAsset("a stack of hardcover books", modulate_scale=0.6))  # read small on the side table
with scene.RelativeGroup() as nook:
    nook.set_anchor(scene.AddAsset("a cozy brown leather reading armchair", asset_id=_ARMCHR))
    nook.place_on_right(side_tbl)                                              # table within reach
    nook.place_on_back_left(scene.AddAsset("a slender brass floor reading lamp", asset_id=_FLOOR))  # its task light
    nook.place_rug("a small patterned wool rug", size=0.7)

# ============================ FRONT: the librarian REFERENCE station (desk + chair, off the wall) ============================
# place_desk_chair = the correct group for a manned desk: anchors the desk, seats the librarian on its
# BACK, rotates the desk so its front faces the room, and gap=True keeps staff circulation behind it.
# Placed as a FLOOR group (not flush) so the desk stands proud of the wall with the chair in the gap.
_ref_desk  = scene.AddAsset("a curved wooden reception front desk", asset_id=_REFDESK, modulate_scale=1.2)  # 1.2x bigger
_ref_chair = scene.AddAsset("a brown leather office desk chair")
with scene.RelativeGroup() as reference:
    reference.place_desk_chair(_ref_desk, _ref_chair, gap=True)
    reference.face(_ref_chair, toward=_ref_desk)                              # librarian's chair turns to the desk

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
    # BACK end (window end) = the armchair nook + a tall plant to balance (nook faces the room, NOT its
    # own side table -- the "rotate armchair to face the table" VLM vote is declined as noise)
    room.place_on_back_left_corner(nook, facing="front")
    room.place_on_back_right_corner(scene.AddAsset("a tall potted plant with lush green leaves"))
    # FRONT = the reference station stands OFF the wall (desk faces the room, librarian's chair behind);
    # card catalog flush on the wall behind it; door on the right.
    room.place_on_front(reference, facing="front")   # patron side of the desk faces the room (chair tucks toward the wall)
    room.place_on_front_wall_left(scene.AddAsset("a dark wooden card catalog cabinet with many small drawers", asset_id=_CATALOG))
    room.place_on_right(book_cart)                                             # fill the browsing aisle
    room.place_door("front_wall", position="right")

    # --- Phase 3: walls, window, ceiling light ---
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

scene.export("library.blend")
