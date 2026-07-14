"""
Nursery — "Soft Pastel Nursery".
Phase 1: crib anchor with a soft rug and a gentle ceiling light.
Phase 2: changing table and a rocking chair.
Phase 3: toy shelf, wall art, window + blackout curtains, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Nursery", seed=10)

with scene.RelativeGroup() as crib_group:
    crib = scene.AddAsset("a white wooden baby crib")
    crib_group.set_anchor(crib)
    crib_group.place_rug("a soft pastel round rug", size=0.7)
    crib_group.add_lighting("a soft star-shaped ceiling light", density=0)

with scene.RoomGroup(randomness=0.15) as room:
    room.place_walls(floor_texture="pale oak wood",
                     ceiling_texture="white", wall_texture="soft blush pink")
    room.place_on_center(crib_group, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a white baby changing table with drawers"))
    room.place_on_front_right_corner(scene.AddAsset("a cozy nursery rocking chair"))
    room.place_on_right_wall_center(scene.AddAsset("a low white toy shelf with baskets"))
    room.place_on_wall_back_center(scene.AddAsset("a framed pastel nursery print"))
    room.place_window_picture("back_wall", curtain="soft blackout curtains")
    room.place_door("front_wall", position="left")

scene.export("nursery.blend")
