"""
Kitchen — "Bright Family Kitchen".
Phase 1: central island with bar stools ringed on one side (AroundGroup arc).
Phase 2: a fruit bowl on the island + rug runner.
Phase 3: range, fridge and cabinetry against walls; pendant lights; window; door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Kitchen", seed=25)

with scene.AroundGroup(sparsity=0.3, jitter=0.3) as island_group:
    island = scene.AddAsset("a large kitchen island with a wooden countertop")
    island_group.set_anchor(island)
    stools = 3 * scene.AddAsset("a modern bar stool")
    island_group.place_arc(stools, dist=0.15)
    island_group.place_on_top(scene.AddAsset("a wooden fruit bowl with fruit"))
    island_group.add_lighting("two pendant lights over an island", density=0)

with scene.RoomGroup(randomness=0.15) as room:
    room.place_walls(floor_texture="terracotta tiles",
                     ceiling_texture="white", wall_texture="soft white")
    room.place_on_center(island_group, facing="front")
    room.place_on_back_wall_left(scene.AddAsset("a stainless steel kitchen range with oven"))
    room.place_on_back_wall_right(scene.AddAsset("a stainless steel refrigerator"))
    room.place_on_left_wall_center(scene.AddAsset("a run of white kitchen base cabinets with a sink"))
    room.place_on_wall_back_center(scene.AddAsset("white kitchen wall cabinets"))
    room.place_window_picture("right_wall", curtain="light cafe curtains")
    room.place_door("front_wall", position="right")

scene.export("kitchen.blend")
