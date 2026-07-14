"""
Waiting room v1 — "Layered Focal Axis for a Modern Clinic Waiting"
(planner target tmp/plan_A_clinic_waiting_room__rows_of_l/plan.png).
Supersedes the thin pre-workflow scenes/waiting_room.py.

Two banks of olive-green waiting chairs face each other across a low walnut-top table
carrying magazines; a dark-walnut curved reception counter anchors the back third
(receptionist facing the room); tall palms in the corners, calm framed prints over
the seat backs, daylight from a picture window on the seating wall, neutral
greige/marble envelope, soft flush ceiling light.

Recipe: lobby's reception anchor (WorkstationGroup + INVERTED desk, place_on_back
so staff have space behind) + classroom's repeated-unit grid for the seat rows.
The dataset has NO beam-linked waiting bank (the closest meshes are domestic sofas
with throw pillows — wrong-kind-of-object for a clinic, the prison_cell rule), so
the "linked row" is built instead by packing single chairs in a GridGroup at
sparsity=0.05: GridGroup runs no overlap solve, so the chairs stay abutted and read
as one bank (the greenhouse v2 packing trick).

Asset notes (audited at gate 3 — previews eyeballed, dims verified offline with
get_whd since retrieval `scale` metadata lies):
  * CHAIR pinned for PALETTE — "olive green" captions render yellow/tan on the
    top hits; only this mesh is genuinely olive (jewelry_shop pin-for-colour rule).
  * DESK is natively 0.66 m TALL (a coffee-table-height "counter") -> uniform 2x
    height-fit to 1.10 m. PALM is natively 0.55 m -> height-fit to 1.75 m
    (the greenhouse tabletop-palm trap).
  * MAGS: the top magazine pick (future/057a6e38) is a FLAT mesh (H=0.00) and a
    place_on_top height-fit would detonate it (greenhouse flat-mesh rule) -> pinned
    a stack with real 3D height (H=0.047) instead.
  * ART pinned for VISIBLE artwork — half the top framed-print hits preview as
    blank white rectangles (the office_modern empty-frame trap).
  * TABLE: the plan asked for GLASS, but the best glass mesh (future/fcea3d53)
    rendered as a solid BLACK SLAB in phase 1 (dark glass + a dark lower shelf) —
    a heavy monolith in a calm beige clinic, and no VLM signal fires on it
    (geometry is fine; "that reads as a black box" is semantics). Swapped for an
    open-frame walnut top: it echoes the reception counter and gives the magazines
    an opaque surface to read against. Dropped the plan's glass, kept its warmth.

Phase-gated (IDSDL/phases.py): --phase 1 = floor layout only (~1 min check);
phase 2 adds surface dressing; phase 3 adds walls/window/lighting/mood.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("WaitingRoom", seed=11)

# --- pinned assets (previews eyeballed + get_whd verified at gate 3) ---
CHAIR = "hssd/f08e9f0057a74950b3b2637c4a462ca7e258b28a"   # olive boxy armchair, wood legs (0.85 W) — carries the palette
DESK  = "future/8f7519b8-9e6f-4712-a3c0-659866828ca8"      # dark walnut curved reception counter (0.66 H native!)
TABLE = "hssd/a54cf3794f633c60b8a5d21917622530f5a04435"    # walnut-top low table, slim metal frame (0.53 H native)
PALM  = "future/88360658-0fdc-4cc5-a058-13e3c48e665d"      # tall palm in a sleek black planter (0.55 H native!)
MAGS  = "hssd/37ab8971067d76a6992c2b230accebcada033eb3"    # stack of glossy magazines (H=0.047 — real height)
BOOKS = "hssd/55a5fd8649bd9cce577ea26cedd313ad4ec26bae"    # design-book stack w/ visible colour covers
ART1  = "hssd/950c82d2ac17a015cc5e063b664f78c965247743"    # PANORAMIC framed abstract landscape (1.92 aspect) — focal
ART2  = "hssd/b9c49bfce9696145e4328cd3e23b5b3e9eeb5b78"    # framed neutral abstract landscape
COOLER = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"   # compact water cooler (bad scale metadata -> width=)
CLOCK = "hssd/e1725f63ab8658c1a31edbf0be78375fa93770ee"    # round wall clock — the ONLY hit with a real face/hands

scene.prefetch_assets([
    "an olive green upholstered lounge armchair",
    "a dark walnut curved reception counter desk",
    "a black office task chair on casters",
    "a desktop computer",
    "a small potted plant",
    "a low walnut-top table with a slim metal frame",
    "a stack of glossy magazines",
    "a stack of design books",
    "a tall potted palm plant in a black planter",
    "a large vibrant colourful abstract framed landscape wall art",
    "a framed neutral abstract landscape print",
    "a tall office water cooler dispenser",
    "a round office wall clock with a white face",
    "a flat round LED flush mount ceiling light",
])

# --- reception anchor: a WorkstationGroup (lobby recipe).
# A reception desk is an INVERTED workstation: the display front (the walnut
# transaction counter) faces the CUSTOMERS while the staff + monitor sit behind.
# set_rotation(180) flips the counter to the customer side and turns the open staff
# side into the group's operator (+Z) side; place_on_back(facing="back") below then
# seats the receptionist toward the back wall, facing the room.
with scene.WorkstationGroup() as reception:
    desk = scene.AddAsset("a dark walnut curved reception counter desk", asset_id=DESK)
    desk.scale(desk.get_width() * 1.10 / desk.get_height())   # uniform height-fit: 0.66 -> 1.10 m
    desk.set_rotation(180)
    reception.set_anchor(desk)
    reception.place_chair(scene.AddAsset("a black office task chair on casters"), gap=True)
    if PHASE >= 2:
        reception.place_computer(scene.AddAsset("a desktop computer"))   # screen auto-faces the chair
        reception.place_accessories([scene.AddAsset("a small potted plant")])

# --- the two seat banks: single chairs PACKED into a row so they read as one
# linked bank (sparsity=0.05 — GridGroup runs no overlap solve, so they stay abutted).
# Build ONE bank, then duplicate: `2 * bank` deep-copies it (design_principles rule).
with scene.GridGroup(sparsity=0.05, randomness=0.12) as bank:
    bank.place_row(4 * scene.AddAsset("an olive green upholstered lounge armchair",
                                      asset_id=CHAIR))
bank_left, bank_right = 2 * bank

# --- the magazine table: the anchor IS the table, so place_on_top seats the
# magazines on the TABLE (living_room_cozy v3: place_on_top ALWAYS targets the anchor)
with scene.RelativeGroup() as table_group:
    table = scene.AddAsset("a low walnut-top table with a slim metal frame", asset_id=TABLE)
    table.scale(table.get_width() * 0.42 / table.get_height())   # height-fit: 0.53 -> 0.42 m
    table_group.set_anchor(table)
    if PHASE >= 2:
        table_group.place_on_top([
            scene.AddAsset("a stack of glossy magazines", asset_id=MAGS),
            scene.AddAsset("a stack of design books", asset_id=BOOKS),
        ])

# --- the room --------------------------------------------------------------
# modulate_scale=0.95: RoomProportions sat at 0.8-0.9 every phase. Held per
# render-wins-early, then FILLED the floor (palms + cooler) rather than crushing it
# — and stopped well SHORT of the vote, because the two seat banks are rigid
# GridGroup rows: a shell shrunk below the footprint they dictate makes fixed-size
# rows overflow their slots and the overlap solver cannot undo it (locker_room).
# The open centre is also the walk-up lane to the desk — circulation the occupancy
# metric always reads as "empty" (garage/corridor).
with scene.RoomGroup(modulate_scale=0.95, randomness=0.12) as room:
    # plain colour + material words only (the classroom accent-clause disaster)
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white plaster",
                     wall_texture="warm greige painted wall")

    # reception in the back third — place_on_back, NOT place_on_back_wall, so the
    # receptionist has floor to stand on (a wall-flush desk puts staff in the wall)
    room.place_on_back(reception, facing="back")

    # the two banks face each other across the table (long runs on the long walls).
    # NO `facing=` — the wall heuristic already turns each bank into the room.
    room.place_on_left_wall_center(bank_left)
    room.place_on_right_wall_center(bank_right)

    # the low table between them, within reach of both rows
    room.place_on_center(table_group)

    # door in PHASE 1: its auto-clearance shapes the floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # greenery: palms flank the reception (the plan's biophilic verticals),
        # height-fit to 1.75 m (native 0.55 m — the greenhouse tabletop-palm trap)
        palm_a = scene.AddAsset("a tall potted palm plant in a black planter", asset_id=PALM)
        palm_a.scale(palm_a.get_width() * 1.75 / palm_a.get_height())
        palm_b = scene.AddAsset("a tall potted palm plant in a black planter", asset_id=PALM)
        palm_b.scale(palm_b.get_width() * 1.75 / palm_b.get_height())
        room.place_on_back_left_corner(palm_a)
        room.place_on_back_right_corner(palm_b)

        # entrance amenity — fills the bare front floor without growing a wall queue
        # (auto-scale metadata is bad on this mesh: pin the width, per lobby)
        room.place_on_front_left_corner(
            scene.AddAsset("a tall office water cooler dispenser", asset_id=COOLER, width=0.35))

        # calm art: focal print behind reception, second over the right-hand seat run.
        # Both pinned for VISIBLE artwork (the empty-frame trap). Chair backs are
        # 0.84 m — well under the art's bottom edge, so the wall-object clearance
        # pass leaves the banks alone.
        #
        # The focal MUST be PANORAMIC. Wall art centres at ~1.5 m and the counter's
        # monitor tops out at ~1.6 m, so ANY back-centre print is crossed by it —
        # and the auto wall-object clearance pass can't help (it only slides FLOOR
        # objects, never an on-top item). v1 hung a PORTRAIT print (0.74 aspect) and
        # the monitor's back bisected it. A wide 1.92-aspect print at width=1.4 lets
        # the monitor interrupt only a small central strip, so the artwork still
        # reads on both sides — a desk in front of a picture, as in a real clinic.
        # (Widening the portrait print instead would have made it 2.16 m TALL:
        # wall scaling is uniform, so aspect is a layout property.)
        room.place_on_wall_back_center(
            scene.AddAsset("a large vibrant colourful abstract framed landscape wall art",
                           asset_id=ART1, width=1.4))
        room.place_on_wall_right_center(
            scene.AddAsset("a framed neutral abstract landscape print", asset_id=ART2))

        # the clock is THE waiting-room signifier (you watch it while you wait) and it
        # fills the otherwise-blank front wall — a free slot, the door is at right.
        # Pinned: 6 of the 8 top clock hits preview as FEATURELESS WHITE DISCS (no face,
        # no hands) — the empty-frame trap in clock form; only this one has a real face.
        room.place_on_wall_front_center(
            scene.AddAsset("a round office wall clock with a white face", asset_id=CLOCK))

        # daylight on the seating wall (the plan's window-adjacent seating).
        # Openings render as real daylight since the 2026-07-12 renderer fix.
        room.place_window_picture("left_wall", curtain=None)

        # flush fixture, low density (small-medium room; count scales with floor area)
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("waiting_room_v1.blend")
