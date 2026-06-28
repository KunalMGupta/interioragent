"""
Laundromat — "Coin Laundry".
Phase 1: a row of front-load washing machines along the back wall (GridGroup row).
Phase 2: a central folding table carrying the room lighting; a row of waiting chairs.
Phase 3: dryers along a side wall, a vending machine, signage, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Laundromat", seed=5)

with scene.GridGroup(sparsity=0.15) as washers:
    washers.place_row(5 * scene.AddAsset("a front-load washing machine"))

with scene.GridGroup(sparsity=0.15) as dryers:
    dryers.place_row(4 * scene.AddAsset("a commercial clothes dryer"))

with scene.GridGroup(sparsity=0.4) as chairs:
    chairs.place_row(4 * scene.AddAsset("a molded plastic waiting chair"))

with scene.RelativeGroup() as fold_group:
    fold_group.set_anchor(scene.AddAsset("a long laundry folding table"))
    fold_group.add_lighting("a row of bright fluorescent ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.15) as room:
    room.place_walls(floor_texture="speckled vinyl floor tiles",
                     ceiling_texture="white drop ceiling", wall_texture="pale mint green")
    room.place_on_center(fold_group, facing="front")
    room.place_on_back_wall_center(washers)
    room.place_on_left_wall_center(dryers)
    room.place_on_front(chairs, facing="back")
    room.place_on_front_right_corner(scene.AddAsset("a tall snack vending machine"))
    room.place_on_wall_back_center(scene.AddAsset("a framed laundry instructions sign"))
    room.place_window_picture("right_wall", curtain=None)
    room.place_door("front_wall", position="left")

scene.export("laundromat.blend")
