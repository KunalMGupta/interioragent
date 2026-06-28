"""
Commercial (restaurant) kitchen — "Service Line".
Phase 1: stainless prep tables in rows (GridGroup) down the middle of the kitchen.
Phase 2: a central prep island carries the bright kitchen lighting.
Phase 3: a cooking range line, shelving and a reach-in fridge along walls, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("RestoKitchen", seed=17)

with scene.GridGroup(sparsity=0.4, randomness=0.1) as prep:
    prep.place_grid(4 * scene.AddAsset("a stainless steel kitchen prep table"), cols=2)

with scene.RelativeGroup() as island_group:
    island_group.set_anchor(scene.AddAsset("a stainless steel kitchen island"))
    island_group.add_lighting("a row of bright industrial kitchen lights", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.1) as room:
    room.place_walls(floor_texture="grey non-slip kitchen tiles",
                     ceiling_texture="white", wall_texture="stainless steel panels")
    room.place_on_center(prep, facing="front")
    room.place_on_back(island_group, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a commercial cooking range with multiple burners"))
    room.place_on_left_wall_center(scene.AddAsset("a stainless steel reach-in refrigerator"))
    room.place_on_right_wall_center(scene.AddAsset("a stainless steel kitchen shelving rack"))
    room.place_door("front_wall", position="right")

scene.export("resto_kitchen.blend")
