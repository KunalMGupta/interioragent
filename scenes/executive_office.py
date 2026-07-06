"""
Executive office — "Integrated Library-Backbone Executive Office".

Built coarse-to-fine (see skills/workflow/coarse_to_fine.md). Planner headline:
a single executive workroom whose STORAGE BACKBONE is a wide open bookcase on the back
wall (the visual anchor), a warm-wood desk in front of it with the executive facing the
room + a daylight window, a sculptural ORANGE accent chair as the visitor pop of colour,
and a small lounge nook (2-seat sofa + round side table) set apart yet visible. Layered
light: a brass sputnik chandelier + a desk task lamp + daylight through full-height blinds.

Palette (dataset-strong "warm traditional-modern"): warm wood + light walls, grey
upholstery, brass fixture, greenery, and the orange chair as the single accent.

  Phase 1 — major floor masses: the wide bookcase backbone (back wall, sets proportions),
    the warm-wood desk WorkstationGroup (executive chair behind, facing the room/window),
    the 2-seat lounge sofa on the left wall.
  Phase 2 — secondary: an orange visitor accent chair angled at the desk; a round side
    table + tall corner plant for the lounge nook.
  Phase 3 — decor/openings: brass sputnik chandelier + desk lamp (in the group); a large
    window with light blinds on the wall the executive faces; a side entry door; framed art.

Facing note (WorkstationGroup): the operator side is the desk's local +Z and the chair
faces the desk, so placing the station with facing="back" seats the executive on the
bookcase side facing the room/window (the classic power layout). Verified in the render.
"""
from IDSDL.scene import SceneProgRoom

# --- pinned hero pieces (settled in the asset-first kickoff) ---
DESK = "hssd/6804953904df94d4abdb0776ad6d55c2a5b8aeaa"        # warm-wood top + slim metal legs (flat writing desk)
BOOKCASE = "future/f1f6fd18-6494-40d5-9fba-988c0734aaf3"      # wide warm-wood grid shelving + lower cabinet (backbone)
ACCENT_CHAIR = "hssd/91999bead15b71802e7a306d174b69a924619756"  # orange winged lounge/visitor accent chair
SOFA = "hssd/7092826dbd4e79eb1468f5f1be75b558b87c2c82"        # grey 2-seat sofa (lounge)
SIDE_TABLE = "hssd/d4bff7307857a9634e9785ce7febc342217cce7c"  # round natural-wood side table

scene = SceneProgRoom("ExecutiveOffice", seed=42)

# --- executive desk workstation: warm-wood desk + leather exec chair + laptop + task lamp + plant ---
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a modern warm wood writing desk with slim metal legs", asset_id=DESK))
    station.place_chair(scene.AddAsset("a brown leather executive office chair"))
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

    # Phase 2 — the orange visitor accent chair angled at the desk front; greenery in the back-right corner
    room.place_on_front_left(scene.AddAsset("a sculptural orange winged accent lounge chair", asset_id=ACCENT_CHAIR),
                             facing="back")
    room.place_on_back_right_corner(scene.AddAsset("a tall potted plant in a modern planter"))

    # Phase 3 — layered lighting, art, openings.
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
    room.place_door("right_wall", position="right")

scene.export("executive_office.blend")
