"""
Classroom — "Chalkboard-Centered Daylit Classroom".
Phase 1: student desk+chair units in a grid with aisles (GridGroup sparsity+randomness),
         all facing the teaching wall; teacher desk at the front.
Phase 2: storage shelf against a wall.
Phase 3: green chalkboard on the front wall, daylight windows, door, ceiling lighting.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Classroom", seed=31)

with scene.RelativeGroup() as desk_unit:
    desk = scene.AddAsset("a wooden student desk with metal frame")
    chair = scene.AddAsset("a small blue plastic school chair")
    desk_unit.place_desk_chair(desk, chair)

with scene.GridGroup(sparsity=0.5, randomness=0.35) as student_grid:
    student_grid.place_grid(6 * desk_unit, cols=3)

with scene.RelativeGroup() as teacher_area:
    teacher_desk = scene.AddAsset("a large teachers desk")
    teacher_chair = scene.AddAsset("a grey office chair")
    teacher_area.place_desk_chair(teacher_desk, teacher_chair)
    teacher_area.place_on_top(scene.AddAsset("a small desk task lamp"))
    teacher_area.add_lighting("a warm rectangular ceiling panel light", density=0)

with scene.RoomGroup(randomness=0.15) as room:
    room.place_walls(floor_texture="light wood planks",
                     ceiling_texture="white", wall_texture="warm cream")
    room.place_on_front(teacher_area, facing="back")
    room.face(teacher_area, toward="back_wall")
    room.place_on_center(student_grid, facing="front")
    room.face(student_grid, toward="front_wall")
    chalkboard = scene.AddAsset("a large green classroom chalkboard", width=2.5)
    room.place_on_wall_front_center(chalkboard)
    room.place_on_right_wall_center(scene.AddAsset("a white open storage shelf with bins and books"))
    room.place_window_floor_to_ceiling("left_wall", curtain="white classroom curtains")
    room.place_door("back_wall", position="right")

scene.export("classroom.blend")
