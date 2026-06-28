"""
Laboratory — "Research Lab".
Phase 1: lab benches with stools arranged in rows (GridGroup), a microscope on a bench.
Phase 2: a central bench carries the room lighting.
Phase 3: a fume hood and equipment shelving against walls, safety sign, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Laboratory", seed=19)


def lab_station():
    g = scene.RelativeGroup()
    with g:
        bench = scene.AddAsset("a white laboratory workbench")
        g.set_anchor(bench)
        g.place_on_front_adjacent(scene.AddAsset("a lab stool"))
        g.place_on_top(scene.AddAsset("a laboratory microscope"))
    return g

with scene.GridGroup(sparsity=0.6, randomness=0.2) as benches:
    benches.place_grid([lab_station() for _ in range(4)], cols=2)

with scene.RelativeGroup() as light_anchor:
    light_anchor.set_anchor(scene.AddAsset("a small lab cart"))
    light_anchor.add_lighting("a row of bright fluorescent lab lights", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.2) as room:
    room.place_walls(floor_texture="white epoxy lab floor",
                     ceiling_texture="white drop ceiling", wall_texture="clinical white")
    room.place_on_center(benches, facing="front")
    room.place_on_back(light_anchor)
    room.place_on_back_wall_left(scene.AddAsset("a laboratory fume hood cabinet"))
    room.place_on_right_wall_center(scene.AddAsset("a tall lab glassware storage shelf"))
    room.place_on_wall_back_center(scene.AddAsset("a framed laboratory safety poster"))
    room.place_window_picture("left_wall", curtain="white blinds")
    room.place_door("front_wall", position="right")

scene.export("laboratory.blend")
