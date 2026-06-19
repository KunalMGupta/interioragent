# from scene import SceneProgRoom

# scene = SceneProgRoom("simple_living_room")

# with scene.RelativeGroup() as seating:
#         sofa = scene.AddAsset("a modern 3-seat sofa")
#         coffee_table = scene.AddAsset("a rectangular wooden coffee table")
#         seating.set_anchor(sofa)
#         seating.place_on_front(coffee_table)
#         seating.place_rug("a soft neutral area rug", size=0.9)

# with scene.GridGroup() as display:
#       display.place_grid(4*seating, 2)

# with scene.RoomGroup() as room:
#     room.place_on_back_wall_center(display, facing="front")
#     room.place_walls(
#         floor_texture="light oak wood floor",
#         ceiling_texture="smooth white ceiling",
#         wall_texture="warm off-white painted wall",
#     )

# scene.export("simple_living_room.blend")

#     # armchair = scene.AddAsset("a cozy lounge chair")
#     # side_table = scene.AddAsset("a small side table")
#     # floor_lamp = scene.AddAsset("a tall floor lamp")
#     # tv_console = scene.AddAsset("a low TV console")
#     # plant = scene.AddAsset("a medium indoor potted plant")
#     # rug = scene.AddAsset("a soft neutral area rug")

#     # room.place_on_back_wall_center(sofa, facing="front")
#     # room.place_on_front_wall_center(tv_console, facing="back")
#     # room.place_on_left(armchair, facing="right")
#     # room.place_on_right(plant, facing="left")
#     # room.place_on_left_wall_right(floor_lamp, facing="right")
#     # room.place_on_right_wall_center(side_table, facing="left")

from IDSDL.scene import SceneProgRoom
scene = SceneProgRoom("simple_bed_room")

with scene.RelativeGroup() as bed_area:
    bed = scene.AddAsset("a queen-sized bed with a wooden frame and a plush mattress")
    with scene.RelativeGroup() as nightstand_area:
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        lamp = scene.AddAsset("a modern table lamp with a white shade")
        nightstand_area.set_anchor(nightstand)
        nightstand_area.place_on_top(lamp)
    bed_area.set_anchor(bed)
    bed_area.place_on_back_left(nightstand_area)
    bed_area.place_on_back_right(1*nightstand_area)
    bed_area.place_rug("a soft neutral area rug", size=0.9)

with scene.RoomGroup() as room:
    room.place_on_back_wall_center(bed_area, facing="front")
    cabinet = scene.AddAsset("a tall and wide wooden wardrobe with mirrored doors")
    room.place_on_right_wall_left(cabinet, facing="left")

scene.export("results/simple_bed_room.blend")






# from IDSDL.scene import SceneProgRoom
# scene = SceneProgRoom("simple_bed_room")

# bed = scene.AddAsset("a queen-sized bed with a wooden frame and a plush mattress")
# nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
# lamp = scene.AddAsset("a modern table lamp with a white shade")
# rug = scene.AddAsset("a soft neutral area rug")
# cabinet = scene.AddAsset("a tall and wide wooden wardrobe with mirrored doors")
# nightstand.place_on_top(lamp)
# bed.place_on_back_left(nightstand)
# bed.place_on_back_right(nightstand)
# bed.place_under(rug)
# bed.place_on_left(cabinet, facing="bed")







# with scene.RelativeGroup() as bed_area:
#     bed = scene.AddAsset("a queen-sized bed with a wooden frame and a plush mattress")
#     with scene.RelativeGroup() as nightstand_area:
#         nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
#         lamp = scene.AddAsset("a modern table lamp with a white shade")
#         nightstand_area.set_anchor(nightstand)
#         nightstand_area.place_on_top(lamp)
#     bed_area.set_anchor(bed)
#     bed_area.place_on_back_left(nightstand_area)
#     bed_area.place_on_back_right(1*nightstand_area)
#     bed_area.place_rug("a soft neutral area rug", size=0.9)

# with scene.RoomGroup() as room:
#     room.place_on_back_wall_center(bed_area, facing="front")
#     cabinet = scene.AddAsset("a tall and wide wooden wardrobe with mirrored doors")
#     room.place_on_right_wall_left(cabinet, facing="left")

# scene.export("results/simple_bed_room.blend")



# from scene import SceneProgRoom
# scene = SceneProgRoom("dining_room")
# with scene.AroundGroup() as dining_area:
#     table = scene.AddAsset("a large rectangular dining table with a dark wood finish")
#     dining_area.set_anchor(table)
#     chair = scene.AddAsset("an elegant dining chair with a cushioned seat and a high backrest")
#     dining_area.place_rectilinear(longer_side1=3*chair, longer_side2=3*chair, shorter_side1=2*chair, shorter_side2=2*chair)
#     dining_area.place_rug("a large area rug with a subtle pattern in neutral tones", size=1.2)

# with scene.RoomGroup() as room:
#     room.place_on_center(dining_area, facing="front")
#     room.place_window_picture("left_wall")
#     room.place_door("right_wall", position="right")
#     painting = scene.AddAsset("A painting of a serene landscape with soft colors")
#     room.place_on_wall_back_center(painting)
#     room.place_walls(
#         floor_texture="light oak wood floor",
#         ceiling_texture="smooth white ceiling",
#         wall_texture="warm off-white painted wall",
#     )   

# print(scene.vlm_feedback)
# scene.export("results/dining_room.blend")

# from scene import SceneProgRoom
# scene = SceneProgRoom("classroom")
# with scene.RelativeGroup() as seating_area:
#     desk = scene.AddAsset("a student desk with a wooden top and metal legs")
#     chair = scene.AddAsset("a standard classroom chair with a plastic seat and backrest")
#     seating_area.set_anchor(desk)
#     seating_area.place_on_front_adjacent(chair)

# with scene.GridGroup() as student_rows:
#     student_rows.place_rectilinear(width1=3*seating_area, width2=3*seating_area, depth1=3*seating_area, depth2=3*seating_area)

# with scene.RoomGroup() as room:
#     room.place_on_center(student_rows, facing="front")
#     room.place_window_picture("left_wall")
#     room.place_door("right_wall", position="right")
#     painting = scene.AddAsset("A painting of a serene landscape with soft colors")
#     room.place_on_wall_back_center(painting)
#     room.place_walls(
#         floor_texture="light oak wood floor",
#         ceiling_texture="smooth white ceiling",
#         wall_texture="warm off-white painted wall",
#     )

# print(scene.vlm_feedback)
# scene.export("results/classroom.blend")