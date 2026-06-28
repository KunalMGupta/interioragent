"""
Dental office — "Exam Bay".
Phase 1: a dental chair anchor with a stool and an instrument tray; overhead exam light.
Phase 2: a cabinet of instruments and a sink counter along walls.
Phase 3: a wall-mounted x-ray viewer, a poster, a window, a door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("DentalOffice", seed=35)

with scene.RelativeGroup() as chair_group:
    chair = scene.AddAsset("a dental examination chair")
    chair_group.set_anchor(chair)
    chair_group.place_on_back_right(scene.AddAsset("a dentist rolling stool"))
    chair_group.place_on_back_left(scene.AddAsset("a dental instrument tray cart"))
    chair_group.add_lighting("a bright overhead dental exam light", density=0)

with scene.RoomGroup(randomness=0.12) as room:
    room.place_walls(floor_texture="light grey vinyl flooring",
                     ceiling_texture="white", wall_texture="mint clinical green")
    room.place_on_center(chair_group, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a dental instrument cabinet with a sink"))
    room.place_on_right_wall_center(scene.AddAsset("a tall medical supply cabinet"))
    room.place_on_wall_back_center(scene.AddAsset("a wall-mounted dental x-ray viewer"))
    room.place_window_picture("front_wall", curtain="white blinds")
    room.place_door("front_wall", position="right")

scene.export("dental_office.blend")
