"""
Computer room — "Lab of Workstations".
Phase 1: desk+chair units each carrying a monitor, in a grid of rows (GridGroup).
Phase 2: a server rack and supply shelving against the walls.
Phase 3: whiteboard, window, ceiling lighting, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ComputerRoom", seed=38)


def workstation():
    g = scene.RelativeGroup()
    with g:
        desk = scene.AddAsset("a computer desk")
        chair = scene.AddAsset("a black office task chair")
        g.place_desk_chair(desk, chair)
        g.place_on_top(scene.AddAsset("a desktop computer monitor"))
    return g

with scene.GridGroup(sparsity=0.5, randomness=0.3) as stations:
    stations.place_grid([workstation() for _ in range(6)], cols=3)

with scene.RelativeGroup() as light_anchor:
    light_anchor.set_anchor(scene.AddAsset("a small server cabinet"))
    light_anchor.add_lighting("a rectangular LED ceiling panel", density=0)

with scene.RoomGroup(randomness=0.2) as room:
    room.place_walls(floor_texture="grey anti-static flooring",
                     ceiling_texture="white drop ceiling", wall_texture="cool grey")
    room.place_on_center(stations, facing="front")
    room.face(stations, toward="front_wall")
    room.place_on_back(light_anchor)
    room.place_on_back_wall_left(scene.AddAsset("a tall server rack with equipment"))
    room.place_on_right_wall_center(scene.AddAsset("a metal storage shelf"))
    room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted whiteboard", width=2.0))
    room.place_window_picture("left_wall", curtain="grey blinds")
    room.place_door("back_wall", position="right")

scene.export("computer_room.blend")
