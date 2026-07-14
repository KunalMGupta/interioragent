"""Executive office — "Integrated Library-Backbone Executive Office" (planner-driven).

Planner target: a single executive workroom whose STORAGE BACKBONE is a wide open bookcase on the
back wall (the visual anchor), a warm-wood desk in front of it with the executive facing the room +
a daylight window, a sculptural ORANGE accent chair as the visitor pop of colour, and a small lounge
nook (2-seat sofa + round side table) set apart yet visible. Layered light: a ceiling fixture + a
desk task lamp + daylight. Palette (dataset-strong "warm traditional-modern"): warm wood + light
walls, grey upholstery, brass, greenery, and the orange chair as the single accent.

Layout — STORAGE BACKBONE + two zones (work / lounge) sharing one floor:
- BACK wall  : the wide bookcase backbone. It is BOTH the anchor and the proportion-setter — a long
               unit like this fixes the room width, so it is placed FIRST and everything else is
               filled in around it.
- CENTRE     : the desk WorkstationGroup, in front of the bookcase, `facing="back"`. WorkstationGroup
               puts the operator on the desk's local +Z with the chair facing the desk, so
               facing="back" seats the executive on the BOOKCASE side looking out at the room and the
               window — the classic power layout. (Verified by eye in the render; the
               RotationConstraint cannot tell.)
- LEFT wall  : the lounge nook (2-seat sofa + round side table), faced "right" into the room — set
               apart from the desk yet visible from it. Seating never travels without a table.
- FRONT      : the visitor's side. The orange accent chair sits front-left angled back at the desk
               (facing="back"), and the daylight window is centred on the wall the executive FACES.
- RIGHT wall : the only wall with no floor mass, so it carries the art — and the door, at its right.

Identity comes from the BACKBONE + the single ACCENT: a wall of warm-wood shelving behind a desk,
and exactly one saturated object (the orange chair) in an otherwise warm-neutral room. Strip either
and this reads as a generic office.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/executive_office_v1.py --phase 1`
builds only the floor layout — bookcase, desk + exec chair, lounge, accent chair, walls + door
(~1-2 min); phase 2 dresses the desktop and drops the greenery; phase 3 adds the wall art, the
window and the ceiling lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("ExecutiveOffice", seed=42)

# --- pinned hero pieces (settled in the asset-first kickoff; all rank-1..3, pinned for durability) -
DESK = "hssd/6804953904df94d4abdb0776ad6d55c2a5b8aeaa"          # warm-wood top + slim metal legs, and
                                                                # crucially FLAT — a WorkstationGroup
                                                                # needs a plain writing surface for
                                                                # place_on_top to seat the laptop on
ACCENT_CHAIR = "hssd/91999bead15b71802e7a306d174b69a924619756"   # orange winged lounge/visitor chair —
                                                                # THE accent; a re-retrieval that came
                                                                # back grey would lose the palette
BOOKCASE = "future/f1f6fd18-6494-40d5-9fba-988c0734aaf3"        # wide warm-wood grid shelving + lower
                                                                # cabinet strip (the backbone). A long
                                                                # unit SETS ROOM PROPORTIONS — pinned so
                                                                # the room's width cannot drift
SOFA = "hssd/7092826dbd4e79eb1468f5f1be75b558b87c2c82"          # grey 2-seat sofa (lounge)
SIDE_TABLE = "hssd/d4bff7307857a9634e9785ce7febc342217cce7c"    # round natural-wood side table

scene.prefetch_assets([
    "a modern warm wood writing desk with slim metal legs",
    "a brown leather executive office chair",
    "a wide modern wood open bookcase with a lower cabinet",
    "a sculptural orange winged accent lounge chair",
    "a modern grey two-seat sofa",
    "a small round wooden side table",
])

# --- executive desk workstation: warm-wood desk + leather exec chair + laptop + task lamp + plant ---
# The desktop items are the PHASE-2 layer — place_computer / place_accessories both route through
# place_on_top, and the gate sits INSIDE the `with` block: gated outside it the ops are never
# recorded and the laptop/lamp/succulent are simply GONE.
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a modern warm wood writing desk with slim metal legs", asset_id=DESK))
    station.place_chair(scene.AddAsset("a brown leather executive office chair"))
    if PHASE >= 2:
        station.place_computer(scene.AddAsset("an open laptop computer"))
        station.place_accessories([   # <= 3 on-top items total (laptop + these two)
            scene.AddAsset("an articulated black desk task lamp"),
            scene.AddAsset("a small potted succulent for a desk"),
        ])

# --- lounge nook: 2-seat sofa + round side table (set apart on the left) ---
with scene.RelativeGroup() as lounge:
    sofa = scene.AddAsset("a modern grey two-seat sofa", asset_id=SOFA)
    lounge.set_anchor(sofa)
    lounge.place_on_front_right(scene.AddAsset("a small round wooden side table", asset_id=SIDE_TABLE))

with scene.RoomGroup(modulate_scale=0.85, randomness=0.1) as room:   # 0.85 acts on the repeated 'rescale 0.8' vote + empty floor
    room.place_walls(floor_texture="warm oak wood flooring",
                     ceiling_texture="white", wall_texture="soft warm white")

    # Phase 1 — the backbone bookcase on the back wall; the desk in front of it (exec faces the room)
    room.place_on_back_wall_center(scene.AddAsset("a wide modern wood open bookcase with a lower cabinet",
                                                  asset_id=BOOKCASE))
    room.place_on_center(station, facing="back")            # facing="back" -> executive faces the room/window
    room.place_on_left_wall_center(lounge, facing="right")  # sofa nook against the left wall, faces the room
    # The orange visitor chair is a FLOOR MASS: it stays in phase 1 even though the coarse-to-fine
    # notes call it "secondary", because it competes for floor with the desk and the lounge.
    room.place_on_front_left(scene.AddAsset("a sculptural orange winged accent lounge chair", asset_id=ACCENT_CHAIR),
                             facing="back")
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        # greenery in the back-right corner, off the bookcase's flank
        room.place_on_back_right_corner(scene.AddAsset("a tall potted plant in a modern planter"))

    if PHASE >= 3:
        # NOTE: a hanging sputnik/globe chandelier renders badly here -- add_lighting caps fixture
        # HEIGHT at 1.5 m but hangs it from the ceiling, so a tall chandelier drops ~1.5 m into the
        # room as giant emissive globes at head height AND its glowing globe meshes over-light the
        # scene to white. Use a COMPACT flush fixture (short -> sits flush, small emissive area); the
        # desk task lamp carries the decorative/task lighting layer instead.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.2)   # fewer fixtures -> no dithered ceiling band
        room.place_on_wall_right_center(scene.AddAsset("a large framed abstract wall art print in warm tones"))
        # daylight on the wall the executive faces. A STANDARD (smaller) punched window, not a wide
        # picture window -- the renderer has no exterior environment, so any opening shows a black
        # night void; a smaller pane keeps that void modest, and light curtains frame it.
        room.place_window_standard("front_wall", position="center", curtain="sheer white curtains")

scene.export("executive_office_v1.blend")
