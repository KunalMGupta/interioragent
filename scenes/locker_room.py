"""
Locker room — "Team Locker Room".
Phase 1: rows of lockers along the side walls (GridGroup rows).
Phase 2: a central bench carrying the room lighting; a second bench down the room.
Phase 3: a mirror on a wall, a window, a door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("LockerRoom", seed=15)

with scene.GridGroup(sparsity=0.05) as lockers_left:
    lockers_left.place_row(5 * scene.AddAsset("a tall metal locker"))

with scene.GridGroup(sparsity=0.05) as lockers_right:
    lockers_right.place_row(5 * scene.AddAsset("a tall metal locker"))

with scene.RelativeGroup() as bench_group:
    bench_group.set_anchor(scene.AddAsset("a long wooden locker-room bench"))
    bench_group.add_lighting("a row of recessed ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.1) as room:
    room.place_walls(floor_texture="grey rubber sports flooring",
                     ceiling_texture="white", wall_texture="navy blue tiles")
    room.place_on_center(bench_group, facing="left")
    room.place_on_left_wall_center(lockers_left)
    room.place_on_right_wall_center(lockers_right)
    room.place_on_back_wall_center(scene.AddAsset("a long wooden bench"))
    room.place_on_wall_back_center(scene.AddAsset("a large wall mirror"))
    room.place_window_picture("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("locker_room.blend")
