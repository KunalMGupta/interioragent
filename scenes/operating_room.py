"""
Operating room — "Surgical Suite".
Phase 1: an operating table at the center with surgical lights overhead.
Phase 2: anesthesia and equipment carts around the table.
Phase 3: a wall-mounted surgical monitor and supply cabinets, sterile finishes, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("OperatingRoom", seed=34)

with scene.RelativeGroup() as table_group:
    optable = scene.AddAsset("a surgical operating table")
    table_group.set_anchor(optable)
    table_group.place_on_back_right(scene.AddAsset("an anesthesia machine cart"))
    table_group.place_on_back_left(scene.AddAsset("a surgical instrument cart"))
    table_group.add_lighting("a dual surgical overhead light", density=0)

with scene.RoomGroup(randomness=0.1) as room:
    room.place_walls(floor_texture="seamless grey surgical floor",
                     ceiling_texture="white", wall_texture="pale surgical green tiles")
    room.place_on_center(table_group, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a stainless steel surgical supply cabinet"))
    room.place_on_right_wall_center(scene.AddAsset("a stainless steel scrub sink station"))
    room.place_on_wall_back_center(scene.AddAsset("a wall-mounted surgical vitals monitor"))
    room.place_door("front_wall", position="right")

scene.export("operating_room.blend")
