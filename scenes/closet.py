"""
Walk-in closet — "Dressing Room". A small room.
Phase 1: clothing wardrobes along the walls.
Phase 2: a central ottoman carrying the ceiling light; a shoe rack.
Phase 3: a full-length mirror, a small window, a door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Closet", seed=21)

with scene.RelativeGroup() as ottoman_group:
    ottoman_group.set_anchor(scene.AddAsset("a round upholstered ottoman"))
    ottoman_group.place_rug("a small plush rug", size=0.6)
    ottoman_group.add_lighting("a small modern chandelier", density=0)

with scene.RoomGroup(modulate_scale=0.85, randomness=0.1) as room:
    room.place_walls(floor_texture="warm oak parquet",
                     ceiling_texture="white", wall_texture="soft taupe")
    room.place_on_center(ottoman_group, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("an open wardrobe with hanging clothes"))
    room.place_on_right_wall_center(scene.AddAsset("an open shelving wardrobe with folded clothes"))
    room.place_on_back_left_corner(scene.AddAsset("a wooden shoe rack with shoes"))
    room.place_on_wall_back_center(scene.AddAsset("a tall full-length mirror"))
    room.place_window_picture("front_wall", curtain="sheer white curtain")
    room.place_door("front_wall", position="right")

scene.export("closet.blend")
