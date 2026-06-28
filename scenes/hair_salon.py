"""
Hair salon — "Styling Studio".
Phase 1: a row of styling chairs facing a mirrored wall (GridGroup row).
Phase 2: a central reception/product counter carrying the room lighting.
Phase 3: wash basins along a wall, product shelves, wall mirrors, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("HairSalon", seed=30)

with scene.GridGroup(sparsity=0.4) as stations:
    stations.place_row(4 * scene.AddAsset("a salon styling chair"))

with scene.GridGroup(sparsity=0.3) as basins:
    basins.place_row(3 * scene.AddAsset("a salon hair washing basin chair"))

with scene.RelativeGroup() as desk_group:
    desk_group.set_anchor(scene.AddAsset("a modern salon reception desk"))
    desk_group.add_lighting("a row of warm ceiling spotlights", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.15) as room:
    room.place_walls(floor_texture="polished concrete floor",
                     ceiling_texture="white", wall_texture="blush pink")
    room.place_on_front(desk_group, facing="back")
    room.place_on_back(stations, facing="back")
    room.face(stations, toward="back_wall")
    room.place_on_left_wall_center(basins)
    room.place_on_right_wall_center(scene.AddAsset("a salon product display shelf"))
    room.place_on_wall_back_left(scene.AddAsset("a large salon wall mirror"))
    room.place_on_wall_back_right(scene.AddAsset("a large salon wall mirror"))
    room.place_window_picture("right_wall", curtain="sheer white curtains")
    room.place_door("front_wall", position="left")

scene.export("hair_salon.blend")
