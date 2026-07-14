"""
Shoe shop — "Footwear Boutique".
Phase 1: shoe display shelves lined along the walls.
Phase 2: a central row of fitting benches carrying the lighting; low stools.
Phase 3: a sales counter, a low mirror, a window, a door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ShoeShop", seed=49)

with scene.GridGroup(sparsity=0.05) as shelves_left:
    shelves_left.place_row(3 * scene.AddAsset("a shoe display shelf full of shoes"))

with scene.GridGroup(sparsity=0.05) as shelves_right:
    shelves_right.place_row(3 * scene.AddAsset("a shoe display shelf full of shoes"))

with scene.GridGroup(sparsity=0.5) as benches:
    benches.place_row(2 * scene.AddAsset("a padded shoe fitting bench"))

with scene.RelativeGroup() as light_anchor:
    light_anchor.set_anchor(scene.AddAsset("a low shoe fitting stool"))
    light_anchor.add_lighting("a row of bright track lights", density=0)

with scene.RoomGroup(modulate_scale=1.0, randomness=0.15) as room:
    room.place_walls(floor_texture="light grey porcelain tiles",
                     ceiling_texture="white", wall_texture="warm white")
    room.place_on_center(benches, facing="front")
    room.place_on_back(light_anchor)
    room.place_on_left_wall_center(shelves_left)
    room.place_on_right_wall_center(shelves_right)
    room.place_on_back_wall_center(scene.AddAsset("a retail sales counter"))
    room.place_on_wall_back_left(scene.AddAsset("a low wall mirror"))
    room.place_window_floor_to_ceiling("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("shoe_shop.blend")
