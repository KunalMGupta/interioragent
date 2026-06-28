"""
Gym — "Fitness Floor".
Phase 1: a grid of cardio machines (treadmills) with walking aisles (GridGroup).
Phase 2: a weight bench in the center carrying the room lighting; a pile of exercise balls.
Phase 3: a dumbbell rack against a wall, a mirrored wall, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Gym", seed=8)

with scene.GridGroup(sparsity=0.7, randomness=0.25) as cardio:
    cardio.place_grid(6 * scene.AddAsset("a treadmill exercise machine"), cols=3)

with scene.RelativeGroup() as bench_group:
    bench_group.set_anchor(scene.AddAsset("a flat weight training bench"))
    bench_group.add_lighting("a row of bright industrial ceiling lights", density=0)

with scene.PileGroup() as balls:
    balls.set_anchor(scene.AddAsset("a rubber gym floor mat"))
    balls.place_pile(4 * scene.AddAsset("a large exercise stability ball"), spread=0.7)

with scene.RoomGroup(modulate_scale=1.15, randomness=0.2) as room:
    room.place_walls(floor_texture="black rubber gym flooring",
                     ceiling_texture="exposed grey ceiling", wall_texture="industrial grey")
    room.place_on_center(cardio, facing="front")
    room.face(cardio, toward="back_wall")
    room.place_on_back(bench_group)
    room.place_on_front_right(balls, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a weight rack with dumbbells"))
    room.place_on_wall_right_center(scene.AddAsset("a large gym wall mirror"))
    room.place_window_floor_to_ceiling("back_wall")
    room.place_door("front_wall", position="left")

scene.export("gym.blend")
