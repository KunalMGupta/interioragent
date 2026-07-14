"""
Museum — "Sculpture Gallery".
Phase 1: display pedestals each topped with a sculpture, in a grid (GridGroup).
Phase 2: a central bench for visitors carrying the gallery lighting.
Phase 3: large framed artworks hung along the walls, a tall plant, skylight window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Museum", seed=27)


def pedestal():
    g = scene.RelativeGroup()
    with g:
        p = scene.AddAsset("a white museum display pedestal")
        g.set_anchor(p)
        g.place_on_top(scene.AddAsset("a classical marble sculpture bust"))
    return g

with scene.GridGroup(sparsity=1.0) as pedestals:
    pedestals.place_grid([pedestal() for _ in range(4)], cols=2)

with scene.RelativeGroup() as bench_group:
    bench_group.set_anchor(scene.AddAsset("a museum backless bench"))
    bench_group.add_lighting("a row of recessed gallery spotlights", density=0)

with scene.RoomGroup(modulate_scale=1.2, randomness=0.1) as room:
    room.place_walls(floor_texture="polished pale stone floor",
                     ceiling_texture="white", wall_texture="warm gallery grey")
    room.place_on_center(pedestals, facing="front")
    room.place_on_front(bench_group, facing="front")
    room.place_on_back_left_corner(scene.AddAsset("a tall potted palm"))
    room.place_on_wall_left_center(scene.AddAsset("a very large framed classical painting"))
    room.place_on_wall_right_center(scene.AddAsset("a very large framed classical painting"))
    room.place_window_picture("back_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("museum.blend")
