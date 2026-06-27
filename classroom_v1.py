"""
Classroom — "Chalkboard-Centered Daylit Classroom". Built coarse-to-fine.
Phase 1: floor anchors — student desk grid (aisles), teacher desk, chalkboard, storage.
Phase 2: reading nook (low shelf + poufs + rug), teacher desk-top lamp.
Phase 3: daylight windows + curtains, entry door, warm ceiling lighting.
Orientation lesson: the student grid faces the teacher via facing= alone; the
room-level RotationConstraint governs (per-unit chair flags were advisory).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ClassroomV1", seed=7)

# --- student desk unit: chair on the BACK of the desk ---
# Convention: for any desk+seat (student/teacher/reception), the seat goes on the
# BACK of the desk. The "look" direction is then chair->desk (the desk's front),
# so the whole unit is internally consistent and orients correctly as a block.
# (place_on_front_adjacent put the chair in front, making students look away from
# the teacher — see skills/workflow/vlm_feedback.md.)
with scene.RelativeGroup() as desk_unit:
    desk = scene.AddAsset("a wooden student desk with metal frame")
    desk_unit.set_anchor(desk)
    chair = scene.AddAsset("a small blue plastic school chair")
    desk_unit.place_on_back_adjacent(chair)

# --- rows of student desks (3 columns x 2 rows), spaced into individual desks
# with aisles (sparsity adds both column and row gaps; 0 = merged benches) ---
with scene.GridGroup(sparsity=0.5) as student_grid:
    student_grid.place_grid(6 * desk_unit, cols=3)

# --- teacher area at the front ---
with scene.RelativeGroup() as teacher_area:
    teacher_desk = scene.AddAsset("a large teachers desk")
    teacher_area.set_anchor(teacher_desk)
    teacher_chair = scene.AddAsset("a grey office chair")
    teacher_area.place_on_back_adjacent(teacher_chair)
    # Phase 2: a task lamp on the teacher's desk
    teacher_area.place_on_top(scene.AddAsset("a small desk task lamp"))
    # Phase 3: warm ceiling light over the front of the room
    teacher_area.add_lighting("a warm rectangular ceiling panel light", density=0)

# --- Phase 2: cozy reading nook (low bookshelf + bean-bag poufs + accent rug) ---
with scene.RelativeGroup() as reading_nook:
    nook_shelf = scene.AddAsset("a low kids bookshelf with picture books")
    reading_nook.set_anchor(nook_shelf)
    poufs = 2 * scene.AddAsset("a colorful round bean bag pouf")
    reading_nook.place_on_front_left(poufs[0])
    reading_nook.place_on_front_right(poufs[1])
    reading_nook.place_rug("a teal patterned area rug", size=0.5)  # VLM: rug too big at 0.85
    # Phase 3: a second warm light over the reading zone
    reading_nook.add_lighting("a warm rectangular ceiling panel light", density=0)

# --- room shell + front/side anchors ---
with scene.RoomGroup() as room:
    room.place_walls(
        floor_texture="light wood planks",
        ceiling_texture="white",
        wall_texture="warm cream",
    )
    # teacher near the front wall; explicitly face the students (the back wall
    # direction), 90-snapped.
    room.place_on_front(teacher_area, facing="back")
    room.face(teacher_area, toward="back_wall")
    # The teacher-desk asset is modeled front-reversed; its 180 correction now lives
    # in the front-orientation cache (IDSDL/datasets/front_offsets.json), applied
    # automatically on load — so no per-scene rotate() is needed here anymore.
    # student rows fill the room; functionally they MUST face the teaching wall.
    # Orient the grid toward the front wall (the wall the teacher/chalkboard are on),
    # snapped to 90 deg — robust and deterministic, unlike the VLM rotation check.
    room.place_on_center(student_grid, facing="front")
    room.face(student_grid, toward="front_wall")

    # chalkboard on the front (teaching) wall; width forces a wall-spanning board
    # (the default retrieval came back as a small tabletop-sized object)
    chalkboard = scene.AddAsset("a large green chalkboard", width=2.5)
    room.place_on_wall_front_center(chalkboard)
    storage = scene.AddAsset("a white open storage shelf with colorful bins and books")
    room.place_on_right_wall_center(storage)

    # Phase 2: reading nook tucked into the back-left corner
    room.place_on_back_left_corner(reading_nook)

    # Phase 3: tall daylight windows (left wall), entry door (back wall)
    room.place_window_floor_to_ceiling("left_wall", curtain="white classroom curtains")
    room.place_door("back_wall", position="right")

scene.export("classroom_v1.blend")
