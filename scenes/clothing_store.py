"""
Clothing store — "Apparel Boutique".
Phase 1: clothing racks in aisles (GridGroup) on the sales floor.
Phase 2: a central display table with folded clothes carrying the room lighting; mannequins.
Phase 3: wall shelving, a checkout counter, a fitting-room mirror, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ClothingStore", seed=44)

with scene.GridGroup(sparsity=0.6, randomness=0.15) as racks:
    racks.place_grid(4 * scene.AddAsset("a clothing display rack with hanging clothes"), cols=2)

with scene.PileGroup() as folded:
    folded.set_anchor(scene.AddAsset("a wooden retail display table"))
    folded.place_pile(5 * scene.AddAsset("a stack of folded shirts"), spread=0.5)
    folded.add_lighting("a row of warm track lights", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.2) as room:
    room.place_walls(floor_texture="light wood floor",
                     ceiling_texture="white", wall_texture="soft greige")
    room.place_on_center(racks, facing="front")
    room.place_on_front_left(folded, facing="front")
    room.place_on_back_left_corner(scene.AddAsset("a retail clothing mannequin"))
    room.place_on_back_right_corner(scene.AddAsset("a retail clothing mannequin"))
    room.place_on_right_wall_center(scene.AddAsset("a wall clothing shelf with folded apparel"))
    room.place_on_back_wall_center(scene.AddAsset("a retail checkout counter"))
    room.place_on_wall_left_center(scene.AddAsset("a tall fitting-room mirror"))
    room.place_window_floor_to_ceiling("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("clothing_store.blend")
