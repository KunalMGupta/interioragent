"""Residential computer study — "Ladder-Frame Study Wall" (planner headline).

Prompt: "a residential computer study room with an L-desk, a monitor arm, and a bookshelf wall".

Built on the office_modern skeleton (ONE hero work zone + a storage backbone + two light walls),
re-cut for the three explicit prompt clauses: the desk must be an L, the screen must ride a monitor
ARM, and one wall must read as a wall of books.

Layout -- HERO WORKSTATION + a BOOKSHELF BACKBONE, arranged so the interior cameras can see:
  CENTRE    = the hero work zone. A WorkstationGroup anchored on a genuine live-edge L-SHAPED desk
              (1.50 x 0.709 x 1.51, flat top) + black mesh task chair + the MONITOR ARM + task lamp
              + pen cup, on a wool rug. placed facing="back" so the operator sits with their back to
              the bookshelf wall looking OUT at the window -- the office_modern/executive_office
              power pose, reconfirmed.
  BACK wall = THE BOOKSHELF WALL (the prompt's third clause, and the room's identity). A three-unit
              run, stepped: 2.175 m book-filled bookcases in the LEFT and RIGHT slots, a 1.25 m
              book-filled bookcase in the CENTRE.
  LEFT wall = the reading perch: green velvet armchair + its round side table (a seat never travels
              without a surface within reach -- design_principles).
  RIGHT wall= a low rustic credenza (0.75 m) with greenery, plus the tall fig in the back-right
              corner.
  FRONT wall= daylight + entry: a STANDARD punched window centre, the door right.

*** THE CAMERA BUDGET IS A DESIGN CONSTRAINT HERE, NOT AN AFTERTHOUGHT ***
renderer/utils.py:741 puts each interior camera at eye = floor_z + 0.55*H, standing at the OPPOSITE
wall's CENTRE, inset 0.92 of the half-dimension (i.e. ~0.04*room_dim off that wall). groups.py:1349
computes H = clip(tallest + 2.0, 3.0, max_height=3.0) = 3.0 m, so **the eye sits at 1.65 m**.
Anything taller than that parked at a wall CENTRE physically CONTAINS the camera and renders that
view pure black -- while the VLM still cheerfully reports "no rotation / no wall overlap", because
it checks per-object geometry and never asserts that a render exists.

So the bookshelf wall is deliberately STEPPED rather than a flat 2.175 m run: the tall pair goes to
the wall's ENDS and the CENTRE slot takes the measured 1.25 m unit, which clears 1.65 m with 0.40 m
to spare. Every one of the four wall centres carries a measured camera-safe occupant:
    back  -> 1.250 m book-filled bookcase   (camera for the FRONT view stands here)
    front -> a window opening, no geometry  (camera for the BACK view stands here)
    left  -> 0.642 m armchair + side table  (camera for the RIGHT view stands here)
    right -> 0.750 m credenza               (camera for the LEFT view stands here)
All tall mass (2.175 m shelves, the 1.5 m fig) is slotted to wall ENDS and CORNERS only.

Heroes measured offline with get_whd() BEFORE the first build (never trust a reference example):
  L-desk       1.500 x 0.709 x 1.506  flat top, real desk height -- WorkstationGroup warns over 1.05
  monitor arm  0.500 x 1.141 x 0.988  a REAL articulated arm + monitor on a desk clamp. Native
                                      1.141 m is oversized for a desktop item, so it is height-fit
                                      UNIFORMLY to 0.62 m. Aspect-checked, not just height-checked:
                                      the panel's width lies along D, so 0.988 * (0.62/1.141) =
                                      0.54 m -- a 24" monitor. A single-axis `width=` pin here would
                                      have squashed the arm's reach instead.
  tall shelf   0.800 x 2.175 x 0.393  shelves modelled FULL of books
  low shelf    1.000 x 1.250 x 0.265  also book-filled -- the camera-safe centre of the run
  credenza     1.500 x 0.750 x 0.375
  armchair     0.800 x 0.642 x 0.721  green velvet (the palette accent, carried on a PROP)
  side table   1.200 native (a coffee table) -> scale(0.5)
  fig          0.400 x 0.947          -> uniform height-fit to 1.5 m
  art          0.600 x 0.048 / 0.500 x 0.020  -- both genuinely FLAT, so wall-hanging is legal

BOOKS ARE THE IDENTITY and they are already IN the meshes. There is deliberately no place_inside()
stocking pass: the pantry lesson measured that `place_inside` grinds a tall fixture's fixed product
mass into ever-smaller specks (n=3 -> 0.15 m; n=18 -> invisible), so adding books to a bookcase is
the one move guaranteed to make it read emptier. All three units were pinned because their shelves
ship full.

PALETTE NOTE (a deliberate, declared deviation from the planner): the plan's signature is a TEAL
back panel behind the shelving. `place_walls` applies ONE wall texture to all four walls, so a
single accent wall is not expressible; and the office_modern texture lesson showed that a dark tone
washes out to grey-taupe at room-scale tiling under the fixed light budget anyway. The accent is
therefore carried on PROPS -- the green velvet armchair and the greenery -- which is where that
lesson says an accent belongs.

Phase-gated (IDSDL/phases.py): `--phase 1` builds only the floor layout (~1 min) -- the workstation,
the whole bookshelf wall, the credenza, the reading perch, the fig and the door; phase 2 dresses the
desktop (monitor arm / lamp / pen cup), the credenza and the side table and lays the rug; phase 3
adds the window, the wall art and the ceiling fixture.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("StudyRoom", seed=11)

# --- pinned heroes (eyeballed on the contact sheets, then measured with get_whd) ---
LDESK    = "hssd/5f27a5439c763328e9addc223ecaaf2d61115a1f"  # L-SHAPED desk, warm walnut panels + drawer pedestals
# (build 1 used the live-edge L hssd/5e33b625: correct geometry, but its "wooden" top RENDERED as a
#  pale grey concrete slab at camera distance and killed the plan's warm-wood palette -- caught in
#  the phase-1 render, not by the VLM, which said `no rescale` on it. Same failure class as
#  office_modern's white-topped executive desk. This one is 1.800 x 0.719 x 1.800, still a flat
#  ~0.72 m writing surface, and its drawer pedestals also deliver the plan's under-desk storage.)
CHAIR    = "hssd/2502dd408e62b2aa751080d4555d9b126f5a8d22"  # black mesh-back task chair on castors
ARM      = "hssd/878fded4b4bc0dcec55d68a662a89ab81c8f0cd5"  # THE MONITOR ARM -- a real articulated arm + panel
SHELF_T  = "hssd/2e29b3aa38387e1a9682778d64f27e8a9ec40296"  # tall bookcase, shelves FILLED with books
SHELF_L  = "hssd/b356640d3d9d976c8ea2a29ae5ff48467e32262b"  # LOW book-filled bookcase -> camera-safe centre
CRED     = "hssd/628d0c20a57798970b7e965946a7bd28267eb3bb"  # rustic wooden sideboard, 0.75 m
ARMCHR   = "hssd/bf96d2cce0097d4eeb20de5e736103b626baf0ac"  # green velvet armchair (the palette accent)
SIDETBL  = "hssd/d4bff7307857a9634e9785ce7febc342217cce7c"  # round mid-century wood table (ships 1.2 m)
PLANT    = "future/f3a1cc15-c18b-49e7-be30-8f7698a26129"    # fiddle-leaf fig in a ceramic planter
DESKLAMP = "hssd/a980ba02a55b4f8bd67d9e1c6dc2231679bc82c9"  # black articulated desk task lamp
ART_LAND = "hssd/b9c49bfce9696145e4328cd3e23b5b3e9eeb5b78"  # framed abstract landscape (real artwork, FLAT)
ART_ABS  = "hssd/18a5ab4d9f66855d5fcf59051ec83820a4a49f14"  # framed textured abstract (real artwork, FLAT)

scene.prefetch_assets([
    "an L-shaped wooden corner computer desk with metal legs",
    "a modern black ergonomic office task chair with wheels",
    "a single monitor arm desk mount with a computer monitor",
    "a tall wooden bookshelf full of books",
    "a low wooden bookcase filled with books",
    "a low rustic wooden sideboard credenza",
    "a green velvet upholstered reading armchair",
    "a small round wooden side table",
    "a tall potted fiddle leaf fig plant in a ceramic planter",
    "a black articulated desk task lamp",
    "a black pen cup with pens and pencils",
    "a stack of hardcover books",
    "a small potted succulent in a ceramic pot",
    "a large framed abstract landscape art print",
    "a framed textured abstract art print in neutral tones",
    "a warm grey wool area rug",
    "a flat round LED flush mount ceiling light",
])


def _fit_height(obj, h):
    """Uniform height-fit -- preserves the mesh's own proportions (design_principles).

    Used instead of a `width=` pin, which is a SINGLE-AXIS stretch: height-fitting a piece whose
    native aspect already matches its class is safe, and both pieces below were aspect-checked
    against their class before this was applied.
    """
    W, H, D = (float(v) for v in obj.get_whd())
    f = h / H
    obj.scale_only_width(W * f)
    obj.scale_only_height(H * f)
    obj.scale_only_depth(D * f)
    return obj


# ===================== CENTRE: the hero L-desk workstation =====================
# WorkstationGroup keeps the whole motif correct BY CONSTRUCTION: the chair lands in front of the
# desk facing it, the screen is seated on the real writing surface by place_on_top, and -- the bit
# that matters for a monitor -- place_computer AIMS it at the operator afterwards. The computer_room
# lesson is explicit that a bare place_on_top never aims an orientation-sensitive item; the arm
# would otherwise render side-on.
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("an L-shaped wooden corner computer desk with metal legs",
                                      asset_id=LDESK))

    chair = scene.AddAsset("a modern black ergonomic office task chair with wheels", asset_id=CHAIR)
    chair.scale(0.6)                    # uniform: 0.50 m native -> 0.6 m wide (~1.0 m tall task chair)
    station.place_chair(chair)
    # WorkstationGroup seats the chair off the anchor's BOUNDING-BOX front face. That is right for a
    # rectangular desk, but an L-desk's bbox is SQUARE (1.80 x 1.80) and mostly empty air, so build 2
    # left the chair stranded ~1 m out in open floor, square-on to the room, and the VLM correctly
    # flagged `rotate office chair to face the L-shaped desk`. face() is re-applied at the END of
    # compile, from final positions, so it aims the seat at the desk whatever the layout settles to.
    station.face(chair)

    if PHASE >= 2:
        # The prompt's monitor ARM. Pre-scaled to a believable desktop size so we do not depend on
        # the tournament's height vote -- and note the AABB fallback would cap an on-top item at
        # 0.4 * anchor height = 0.28 m, which would shrink a monitor arm to a toy.
        arm = scene.AddAsset("a single monitor arm desk mount with a computer monitor", asset_id=ARM)
        _fit_height(arm, 0.62)
        station.place_computer(arm)
        station.place_accessories([      # <= 3 on-top items total (arm + these two)
            scene.AddAsset("a black articulated desk task lamp", asset_id=DESKLAMP),
            scene.AddAsset("a black pen cup with pens and pencils"),
        ])
        # the rug zones the work area; kept well inside the cluster bbox so the oak floor still
        # reads around it (living_room_cozy: an oversized rug reads as wall-to-wall carpet)
        station.place_rug("a warm grey wool area rug", size=0.8)

# ===================== BACK wall: THE BOOKSHELF WALL =====================
# STEPPED tall-low-tall, one unit per wall slot. Getting the DENSITY of this run right took three
# builds and it is a genuine three-way tension, so the reasoning is recorded here:
#
#   build 1  single 0.80 m bookcase per end slot -> 2.60 m of shelving on a 5.33 m wall (49%
#            coverage). Right-sized room (22.5 m2) but it read as "a room that owns three
#            bookcases", not as the prompt's BOOKSHELF WALL.
#   build 2  doubled each end to a `place_row` of two -> 4.20 m of shelving, and the wall face
#            genuinely read as a library. But the shell blew out to 7.29 x 4.52 = 33 m2, and with
#            the corner desk added, 7.66 x 5.85 = 44.8 m2 -- a "residential study" the size of a
#            squash court, the cavernous-shell failure the coffee_shop lesson is about.
#   WHY      a wall's slots are THIRDS of that wall, so the shell must grow until every slot fits
#            its occupant: a 1.60 m row in a third forces the wall past 4.8 m before margins. Wall
#            mass is not free -- it is paid for in floor area.
#   build 4  (this) back to single tall units at the ends, and the coverage bought instead from the
#            CENTRE unit via `width=1.40`. A single-axis pin is normally the wrong tool -- but here
#            it is exactly right and the uniform fit is the trap: this unit's HEIGHT is pinned by
#            the camera (see below), and scaling it uniformly to 1.40 m wide would drag the height
#            to 1.75 m, straight through the 1.65 m eye, blinding the front-wall view. Stretching a
#            bookcase's shelves 1.00 -> 1.40 m along its width alone is a mild, believable change.
#            Run = 0.80 + 1.40 + 0.80 = 3.00 m, and the shell stays study-sized.
#
# The CENTRE unit is measured at 1.250 m and that is the reason the front-wall view is not black:
# the camera for that view stands at the back wall's centre at 1.65 m, clearing it by 0.40 m. The
# tall 2.175 m units are confined to the wall's ENDS, where no camera ever stands.
# The tall ends are widened 0.80 -> 1.10 m on the WIDTH AXIS ONLY, for the same reason as the centre
# unit and with the same care: uniform scaling would drag their 2.175 m height to 2.99 m and jam
# them into the 3.0 m ceiling. Widening costs nothing here -- the wall's binding constraint is the
# widest slot occupant (the 1.40 m centre unit, 3 x 1.40 = 4.20 m <= the 4.61 m wall), so 1.10 m
# ends do not grow the shell at all. Coverage goes 3.00 -> 3.60 m of shelving across a 4.61 m wall
# (65% -> 78%), which is the difference between "a room with three bookcases in it" and the prompt's
# BOOKSHELF WALL. The 1.375x stretch matches the magnitude already proven benign on the centre unit.
shelf_left  = scene.AddAsset("a tall wooden bookshelf full of books", asset_id=SHELF_T, width=1.1)
shelf_right = scene.AddAsset("a tall wooden bookshelf full of books", asset_id=SHELF_T, width=1.1)
shelf_mid   = scene.AddAsset("a low wooden bookcase filled with books", asset_id=SHELF_L, width=1.4)

# ===================== RIGHT wall: the low credenza =====================
# Its own RelativeGroup so the phase-2 decor lands on the CREDENZA's top surface -- place_on_top
# always targets the group's ANCHOR, never a sibling child (living_room_cozy v3).
credenza = scene.AddAsset("a low rustic wooden sideboard credenza", asset_id=CRED)
# Uniform 1.50 -> 1.20 m (height follows to 0.60 m, still a credenza, still camera-safe). This is a
# CONSEQUENCE of the room shrink below, not a taste call: wall slots are thirds of their wall, so
# the left wall's slot is depth/3 = 1.51 m at modulate_scale 1.0 -- the 1.50 m credenza only just
# fits, and ANY shrink of the shell pushes it out of its own slot into the neighbouring one. That is
# the locker-room failure (a room-shrink vote applied to a wall-loaded room, overflowing fixed-size
# runs into overlaps the solver cannot undo). Shrink the shell and its wall runs together, or not at all.
credenza.scale(1.2)
with scene.RelativeGroup() as credenza_unit:
    credenza_unit.set_anchor(credenza)
    if PHASE >= 2:
        credenza_unit.place_on_top([
            scene.AddAsset("a small potted succulent in a ceramic pot"),
            scene.AddAsset("a stack of hardcover books", modulate_scale=0.6),
        ])

# ===================== LEFT wall: the reading perch =====================
# A seat always gets a surface within reach, and it travels as ONE unit so the pair stays together
# when the group is placed or rotated (design_principles).
side_table = scene.AddAsset("a small round wooden side table", asset_id=SIDETBL)
side_table.scale(0.5)                   # uniform: ships 1.2 m (a coffee table) -> a real side table
with scene.RelativeGroup() as perch:
    perch.set_anchor(scene.AddAsset("a green velvet upholstered reading armchair", asset_id=ARMCHR))
    perch.place_on_right(side_table)

# ===================== the greenery =====================
plant = scene.AddAsset("a tall potted fiddle leaf fig plant in a ceramic planter", asset_id=PLANT)
_fit_height(plant, 1.5)                 # 0.947 m native -> a genuinely "tall" plant, still under 1.65

# ===================== the room =====================
# modulate_scale=0.85 is applied ONCE, here in the final phase, on a room-size vote that has been
# stable at 0.78-0.84 across every build of every layout variant (0.84 / 0.78 / 0.80 / 0.71 / 0.80) --
# unidirectional, never once asking to grow, which is a converged signal rather than the oscillation
# you decline as noise. Held at 1.0 through phases 1-2 per render-wins-early, because a room-size
# vote on a partial build is voting on a room that does not exist yet (bedroom lesson).
# It is picked slightly ABOVE the 0.80 vote deliberately: 5.37 x 4.52 -> 4.56 x 3.84 = 17.5 m2, and
# the slot arithmetic still clears at that value (back wall 4.56/3 = 1.52 m slots vs the 1.40 m
# centre bookcase; left wall 3.84/3 = 1.28 m slots vs the now-1.20 m credenza). At the vote's 0.80
# the left wall's slot falls to 1.21 m and the run starts overflowing -- a shrink that buys occupancy
# by creating overlaps is not a win.
with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:
    # Texture strings are embedding-matched against the library's CAPTION text, so they are worded
    # like captions. Warm neutral walls: the plan's teal is carried on props instead (see docstring).
    room.place_walls(floor_texture="warm oak wood flooring",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="solid warm greige smooth uniform wall")

    # --- PHASE 1: the floor masses. Six occupied slots = a real study, not a hall. ---
    # The workstation takes the CENTRE floor slot, operator's back to the books, facing the window.
    #
    # Build 3 hard-aligned it into the front-left CORNER instead -- which is what this room type's
    # procedural signature asks for, and it did fix the chair pose. It was still reverted, because a
    # corner slot is brutally expensive in floor area: the station lands in the FRONT slot-row, so
    # the shell has to grow a front row deep enough for it AND keep a middle row, and the same
    # happens across the width. Measured, same program otherwise:
    #     station at centre -> 5.33 x 4.23 = 22.5 m2      station in a corner -> 6.40 x 5.85 = 37.4 m2
    # 15 m2 of dead floor is a far worse failure than a desk that doesn't touch two walls -- an
    # over-sized shell is the one thing no amount of decor can fix afterwards, and the room-size vote
    # got monotonically ANGRIER as the room grew (0.84 -> 0.78 -> 0.80 -> 0.71). The desk still reads
    # as an L from every view; it just isn't jammed into a corner. Room size is a consequence of slot
    # occupancy, so the fix belongs at the slot, not in modulate_scale.
    room.place_on_center(station, facing="back")
    # the bookshelf wall, stepped so the front-wall camera survives
    room.place_on_back_wall_left(shelf_left)
    room.place_on_back_wall_center(shelf_mid)
    room.place_on_back_wall_right(shelf_right)
    # The perch moves to the RIGHT wall, diagonally opposite the workstation. In build 2 both the
    # desk (centre) and the armchair (left wall) reached into the same left-of-room region and the
    # chair ended up wedged behind the desk -- two groups fighting for one region reads broken even
    # though every constraint passes (the st_writer_studio trap). `facing` is OMITTED on both wall
    # placements: the wall heuristic already turns furniture into the room, and passing the wall's
    # own name would turn it to face the wall.
    room.place_on_right_wall_center(perch)
    room.place_on_left_wall_center(credenza_unit)
    # greenery in a CORNER, never a wall centre
    room.place_on_back_right_corner(plant, facing="front")
    # door in PHASE 1: its auto clearance shapes the floor solve, so deferring it would change the
    # layout you validated. Right of the front wall, clear of the window slot.
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # daylight on the wall the operator faces. A STANDARD punched window, never _picture.
        room.place_window_standard("front_wall", position="center", curtain="sheer white curtains")
        # the light walls carry one print each, in slots no door/window claims. Both meshes verified
        # FLAT (0.048 / 0.020 m deep) -- a deep mesh hung with place_on_wall_* floats in mid-air.
        room.place_on_wall_left_center(scene.AddAsset("a large framed abstract landscape art print",
                                                     asset_id=ART_LAND))
        room.place_on_wall_right_center(scene.AddAsset("a framed textured abstract art print in neutral tones",
                                                      asset_id=ART_ABS))
        # ONE compact FLUSH disc. add_lighting pins the fixture origin at the CEILING and spends a
        # fixed 500 W split across N, so density is a fixture COUNT, never brightness -- a hanging
        # pendant would drop into the room as an emissive globe and blow the exposure (executive_office).
        # 0.01 is the small-room value; 0.05 starfields a room this size (coffee_shop).
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("study_room_v1.blend")
