"""
Corridor — "Office Hallway". A long circulation space.
NOTE: the RoomGroup auto-sizes from placements, so a true narrow corridor aspect is hard
to force — this lays a runner of furniture front-to-back and leans on modulate_scale; the
resulting proportions are a good discussion point for a possible explicit room-aspect control.
Phase 1: a console table runner down the hall carrying the lighting.
Phase 2: benches and plants spaced along the length.
Phase 3: framed art along the walls, doors on the side walls.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Corridor", seed=33)

with scene.RelativeGroup() as console_group:
    console_group.set_anchor(scene.AddAsset("a narrow console hall table"))
    console_group.place_on_top(scene.AddAsset("a small decorative vase"))
    console_group.add_lighting("a row of recessed hallway ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.15) as room:
    room.place_walls(floor_texture="grey carpet tiles",
                     ceiling_texture="white", wall_texture="light beige")
    room.place_on_back(console_group, facing="front")
    room.place_on_front_left(scene.AddAsset("a slim hallway bench"), facing="right")
    room.place_on_front_right(scene.AddAsset("a tall narrow potted plant"), facing="left")
    room.place_on_wall_left_center(scene.AddAsset("a framed art print"))
    room.place_on_wall_right_center(scene.AddAsset("a framed art print"))
    room.place_door("front_wall", position="center")
    room.place_door("back_wall", position="center")

scene.export("corridor.blend")
