"""
Waiting room — "Clinic Waiting Area".
Phase 1: rows of linked waiting chairs along the side walls (GridGroup rows).
Phase 2: a central coffee table with magazines carrying the room lighting.
Phase 3: a reception desk, corner plants, wall art, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("WaitingRoom", seed=11)

with scene.GridGroup(sparsity=0.1) as chairs_left:
    chairs_left.place_row(4 * scene.AddAsset("a linked row waiting room chair"))

with scene.GridGroup(sparsity=0.1) as chairs_right:
    chairs_right.place_row(4 * scene.AddAsset("a linked row waiting room chair"))

with scene.RelativeGroup() as table_group:
    table_group.set_anchor(scene.AddAsset("a low coffee table"))
    table_group.place_on_top(scene.AddAsset("a stack of magazines"))
    table_group.add_lighting("a rectangular LED ceiling panel", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.15) as room:
    room.place_walls(floor_texture="light grey vinyl flooring",
                     ceiling_texture="white drop ceiling", wall_texture="soft sage")
    room.place_on_center(table_group, facing="front")
    room.place_on_left_wall_center(chairs_left)
    room.place_on_right_wall_center(chairs_right)
    room.place_on_back_wall_center(scene.AddAsset("a curved reception desk"))
    room.place_on_back_left_corner(scene.AddAsset("a tall potted plant"))
    room.place_on_wall_front_center(scene.AddAsset("a large framed calming landscape print"))
    room.place_window_picture("front_wall", curtain="light grey blinds")
    room.place_door("front_wall", position="right")

scene.export("waiting_room.blend")
