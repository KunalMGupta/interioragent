"""
Pantry — "Stocked Larder". A small utility room.
Phase 1: tall shelving units lined along the walls (GridGroup rows).
Phase 2: a small central worktable carrying the ceiling light; a pile of baskets.
Phase 3: a step stool, a small window, a door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Pantry", seed=20)

with scene.GridGroup(sparsity=0.05) as shelves_left:
    shelves_left.place_row(3 * scene.AddAsset("a tall pantry shelf stocked with jars and cans"))

with scene.GridGroup(sparsity=0.05) as shelves_right:
    shelves_right.place_row(3 * scene.AddAsset("a tall pantry shelf stocked with jars and cans"))

with scene.RelativeGroup() as table_group:
    table_group.set_anchor(scene.AddAsset("a small wooden worktable"))
    table_group.place_on_top(scene.AddAsset("a wicker storage basket"))
    table_group.add_lighting("a simple ceiling light", density=0)

with scene.RoomGroup(modulate_scale=0.8, randomness=0.1) as room:
    room.place_walls(floor_texture="terracotta floor tiles",
                     ceiling_texture="white", wall_texture="cream")
    room.place_on_center(table_group, facing="front")
    room.place_on_left_wall_center(shelves_left)
    room.place_on_right_wall_center(shelves_right)
    room.place_on_back_left_corner(scene.AddAsset("a small wooden step stool"))
    room.place_window_standard("back_wall", position="center")
    room.place_door("front_wall", position="center")

scene.export("pantry.blend")
