"""
Toy store — "Toy Emporium".
Phase 1: colorful toy shelving aisles (GridGroup) stocked with toys.
Phase 2: a central display table piled with toys carrying the lighting; a pile of plush toys.
Phase 3: a checkout counter, a giant plush mascot in a corner, bright signage, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ToyStore", seed=50)

with scene.GridGroup(sparsity=0.7) as aisles:
    aisles.place_grid(6 * scene.AddAsset("a colorful toy store shelf full of toys"), cols=3)

with scene.PileGroup() as plush:
    plush.set_anchor(scene.AddAsset("a low display table"))
    plush.place_pile(6 * scene.AddAsset("a colorful plush stuffed animal"), spread=0.6)
    plush.add_lighting("bright colorful ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.2) as room:
    room.place_walls(floor_texture="bright multicolor floor tiles",
                     ceiling_texture="white", wall_texture="cheerful primary blue")
    room.place_on_center(aisles, facing="front")
    room.place_on_front_left(plush, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a colorful toy store checkout counter"))
    room.place_on_back_right_corner(scene.AddAsset("a giant plush teddy bear"))
    room.place_on_wall_left_center(scene.AddAsset("a bright toy store sign"))
    room.place_window_floor_to_ceiling("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("toy_store.blend")
