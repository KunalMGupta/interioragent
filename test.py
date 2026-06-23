from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("LivingRoom", seed=42)

# with scene.RelativeGroup() as chair_pair:
#     chair = scene.AddAsset("an upholstered accent chair")
#     chair_pair.set_anchor(chair)
#     chair_pair.place_on_right(1*chair)

# with scene.RelativeGroup() as seating_area:
#     coffee_table = scene.AddAsset("a large round coffee table")
#     seating_area.set_anchor(coffee_table)

#     sofa = 2*scene.AddAsset("a sofa")
#     seating_area.place_on_right_further(sofa[0])
#     seating_area.place_on_back_further(sofa[1])
#     seating_area.place_on_front_further(chair_pair)

with scene.AroundGroup() as chairs_around_table:
    table = scene.AddAsset("a large round coffee table")
    chairs_around_table.set_anchor(table)
    chairs= 2*scene.AddAsset("an upholstered accent chair")
    chairs_around_table.place_arc(chairs)

sofa = 2*scene.AddAsset("a sofa")
with scene.RelativeGroup() as main_couch:
    main_couch.set_anchor(sofa[0])
    with scene.RelativeGroup() as side_table_group:
        side_table = scene.AddAsset("a small end table", modulate_scale=0.3)
        side_table_group.set_anchor(side_table)
        table_lamp = scene.AddAsset("a table lamp")
        side_table_group.place_on_top(table_lamp)
    main_couch.place_on_front_left(side_table_group)
    floor_lamp = scene.AddAsset("a fancy floor lamp")
    main_couch.place_on_back_left(floor_lamp)
    

with scene.RelativeGroup() as seating_area:
    seating_area.set_anchor(chairs_around_table)
    seating_area.place_on_back_further(main_couch)
    seating_area.place_on_right_further(sofa[1])
    seating_area.place_rug("a gray rug made of wool", size=0.8)
    seating_area.add_lighting("a chandilier", density=0)
    

with scene.RoomGroup() as room:
    room.place_walls(floor_texture="wooden planks", ceiling_texture="beige", wall_texture="beige")
    room.place_on_center(seating_area, facing="front")
    large_plant = scene.AddAsset("a large potted plant")
    room.place_on_back_right_corner(large_plant)
    cabinet = scene.AddAsset("a tall open shelving unit with decor")
    room.place_on_right_wall_center(cabinet)
    painting = scene.AddAsset("a large UCSD painting")
    room.place_on_wall_left_center(painting)
    room.place_door("left_wall", position="right")
    room.place_window_floor_to_ceiling("back_wall", curtain="light gray transparent curtains")

scene.export("test.blend")