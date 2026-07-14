"""
Bathroom — "Spa-style Bath".
Phase 1: vanity with sink as the anchor (mirror hung above it).
Phase 2: bath mat, toilet and bathtub against walls.
Phase 3: towel storage, mirror, small window, flush ceiling light, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Bathroom", seed=12)

with scene.RelativeGroup() as vanity_group:
    vanity = scene.AddAsset("a modern bathroom vanity with a sink and cabinet")
    vanity_group.set_anchor(vanity)
    vanity_group.place_rug("a soft grey bath mat", size=0.5)
    vanity_group.add_lighting("a modern flush bathroom ceiling light", density=0)

with scene.RoomGroup(randomness=0.1) as room:
    room.place_walls(floor_texture="white marble tiles",
                     ceiling_texture="white", wall_texture="pale grey subway tiles")
    room.place_on_back_wall_center(vanity_group)
    room.place_on_left_wall_center(scene.AddAsset("a white modern toilet"))
    room.place_on_right_wall_center(scene.AddAsset("a freestanding white bathtub"))
    room.place_on_front_left_corner(scene.AddAsset("a tall towel storage cabinet"))
    room.place_on_wall_back_center(scene.AddAsset("a large round wall mirror"))
    room.place_window_picture("front_wall", curtain="frosted privacy curtain")
    room.place_door("front_wall", position="right")

scene.export("bathroom.blend")
