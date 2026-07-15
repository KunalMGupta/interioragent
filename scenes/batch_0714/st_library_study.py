"""Library-style study — "Dark Academia Study" (library.md's corridor, folded into one room).

A private study that borrows the reading-hall's ingredients at domestic scale: three TALL
stocked walnut bookcases along the back wall, a central walnut reading table with two chairs,
a green banker's lamp + a vintage globe on the tabletop (the two signature props that make a
bare table read "study"), and a leather armchair corner. Palette: deep green walls + dark oak
— dark academia. (Known risk, not fought: dark wall tones render paler than authored at room
scale — office_modern's wash-out class; the strings are still the closest honest match.)

Layout — one loaded wall, one hero table, light everywhere else:
- BACK wall  : the shelf wall. The bookcases are TALL (~2 m), and the interior cameras stand
               at each wall's CENTRE (~1.4 m) — a tall run parked across the back-wall centre
               contains/blinds a camera (closet/grocery rule). So the row is split into the
               wall SLOTS with the centre kept CLEAR: a flush 2-case GridGroup row in the
               LEFT slot + a single case in the RIGHT slot.
- CENTRE     : the reading table + 2 chairs via `place_rectilinear` (one chair per long side —
               a uniform straight facing per side; NEVER per-chair face(), which fans chairs
               at the anchor's centre point).
- FRONT-LEFT : the leather armchair + brass floor lamp corner, faced into the room.
- LEFT wall  : the window (phase 3) — daylight rakes across the shelf wall.
- FRONT wall : the door (right slot) + the framed antique map (phase 3, centre).

Phase-gated: phase 1 = all floor mass + door; phase 2 = banker's lamp, globe, rug, book
stack; phase 3 = window + curtains, wall art, pendants.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("StLibraryStudy", seed=42)

# --- pinned assets (library.md's audited pins + fresh retrievals for the study props) ------------
SHELF = "hssd/b356640d3d9d976c8ea2a29ae5ff48467e32262b"    # tall dark-walnut bookcase, stocked —
                                                           # the hero; an empty case reads generic
TABLE = "hssd/e5c0975d4c5bae809e505e440e74a449d503f4e2"    # long walnut rectangular table (retrieved
                                                           # as a "dark walnut DINING table", 0.71 —
                                                           # the literal "reading table" query is weak)
CHAIR = "hssd/b98286cc0fed6b814d3b5cf4afc825514ed51b54"    # wooden library chair, cushioned seat
LAMP = "hssd/721b75b49772e53e01785e943bfe8832fe3f9dfe"     # GREEN banker's dome lamp — the signature
                                                           # prop; MUST be shrunk (place_on_top
                                                           # oversizes small props to chair scale)
GLOBE = "hssd/55c813d9a522cc5e52176d01e75ea53d260c9003"    # vintage-map globe — retrieved fresh
                                                           # (0.72). It is a TABLE globe (native scale
                                                           # 0.3), so it lives ON the table, not on
                                                           # the floor. No floor-stand globe exists.
ARMCHAIR = "hssd/613ba909e59984d3a908ec4b52344bcd689fa79b" # brown tufted leather armchair
FLOORLAMP = "hssd/69fa8415108e7438a412ec0a52a55983f39119df"# slender brass floor lamp
MAP = "hssd/6234b80bc5581c92a7bcf8d016e32b9cb5f0bba5"      # framed world map, dark wooden frame —
                                                           # surfaced in the globe retrieval; exactly
                                                           # the dark-academia wall piece

scene.prefetch_assets([
    "a tall wooden bookshelf full of books",
    "a long walnut rectangular reading table",
    "a wooden library chair with a cushioned seat",
    "a green glass bankers desk lamp",
    "a decorative vintage world globe",
    "a cozy brown leather reading armchair",
    "a slender brass floor reading lamp",
])

# --- the shelf wall: a flush row of 2 + a single, wall SLOTS, centre clear ----------------------
# NOTE: no rolling library ladder exists in the dataset (library.md documented gap) — the
# stocked cases carry the read on their own; don't force a wrong mesh.
with scene.GridGroup(sparsity=0.04, randomness=0.0) as shelf_row:
    shelf_row.place_row(2 * scene.AddAsset("a tall wooden bookshelf full of books", asset_id=SHELF))
shelf_single = scene.AddAsset("a tall wooden bookshelf full of books", asset_id=SHELF)

# --- the hero: reading table + 2 chairs + the signature tabletop props --------------------------
with scene.AroundGroup(sparsity=0.25, jitter=0.15) as reading:
    reading.set_anchor(scene.AddAsset("a long walnut rectangular reading table", asset_id=TABLE))
    chairs = 2 * scene.AddAsset("a wooden library chair with a cushioned seat", asset_id=CHAIR)
    reading.place_rectilinear(longer_side1=chairs[:1], longer_side2=chairs[1:])
    if PHASE >= 2:
        # banker's lamp shrunk hard (library.md: 0.3 sits right on a table); the globe likewise
        # reads as a desk globe, not a beach ball
        reading.place_on_top([
            scene.AddAsset("a green glass bankers desk lamp", asset_id=LAMP, modulate_scale=0.3),
            scene.AddAsset("a decorative vintage world globe", asset_id=GLOBE, modulate_scale=0.35),
            scene.AddAsset("a stack of hardcover books", modulate_scale=0.5),
        ])
        reading.place_rug("a traditional patterned green and cream wool rug", size=0.9)

# --- the armchair corner (seat + its own light, composed as one nook) ---------------------------
with scene.RelativeGroup() as nook:
    nook.set_anchor(scene.AddAsset("a cozy brown leather reading armchair", asset_id=ARMCHAIR))
    nook.place_on_back_left(scene.AddAsset("a slender brass floor reading lamp", asset_id=FLOORLAMP))

with scene.RoomGroup(modulate_scale=0.9, randomness=0.1) as room:
    room.place_walls(floor_texture="dark brown hardwood floor",     # verified real warm-oak match
                     ceiling_texture="soft cream plaster ceiling",  # (kitchen.md; "warm oak" strings
                     wall_texture="deep green painted wall")        # embed to a salmon plank)

    # Phase 1 — all floor mass. The shelf wall goes in the back wall's SLOTS, centre clear:
    room.place_on_back_wall_left(shelf_row)     # facing omitted -> heuristic turns spines into room
    room.place_on_back_wall_right(shelf_single)
    room.place_on_center(reading)
    room.place_on_front_left_corner(nook, facing="back")  # armchair faces the room/table, corner-held
    room.place_door("front_wall", position="right")

    if PHASE >= 2:
        # a tall plant balances the armchair at the other end of the light front wall
        room.place_on_front_right_corner(scene.AddAsset("a tall potted plant with lush green leaves"))

    if PHASE >= 3:
        # window on the LEFT wall: daylight rakes ACROSS the shelf wall instead of backlighting it
        room.place_window_standard("left_wall", position="center",
                                   curtain="floor-length deep green velvet curtains")
        room.place_on_wall_front_center(
            scene.AddAsset("a framed antique world map in a dark wooden frame", asset_id=MAP,
                           width=1.0))
        room.place_on_wall_right_center(
            scene.AddAsset("a framed classical oil painting portrait in a gold frame", width=0.8))
        # warm drum pendant, size and count COUPLED (library.md: shrinking the fixture multiplies
        # the count) — 0.5 scale at density 0.02 keeps a small study to a few tidy pendants
        room.add_lighting("a warm fabric drum pendant ceiling light", density=0.02,
                          modulate_scale=0.5)

scene.export("st_library_study.blend")
