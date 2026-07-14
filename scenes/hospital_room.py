"""
Hospital room — "Patient Room".
Phase 1: a hospital bed anchor with a bedside cabinet and an IV stand; ceiling light.
Phase 2: a visitor armchair and an overbed table.
Phase 3: a wall-mounted vitals monitor, supply cabinet, window + privacy curtain, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("HospitalRoom", seed=41)

with scene.RelativeGroup() as bed_group:
    bed = scene.AddAsset("an adjustable hospital patient bed")
    bed_group.set_anchor(bed)
    bed_group.place_on_back_right(scene.AddAsset("a bedside hospital cabinet"))
    bed_group.place_on_back_left(scene.AddAsset("an IV drip stand"))
    bed_group.add_lighting("a recessed hospital ceiling light", density=0)

with scene.RoomGroup(randomness=0.12) as room:
    room.place_walls(floor_texture="pale blue vinyl flooring",
                     ceiling_texture="white", wall_texture="soft hospital blue")
    room.place_on_center(bed_group, facing="front")
    room.place_on_front_right_corner(scene.AddAsset("a vinyl hospital visitor armchair"))
    room.place_on_left_wall_center(scene.AddAsset("a medical supply cabinet"))
    room.place_on_wall_back_center(scene.AddAsset("a wall-mounted patient vitals monitor"))
    room.place_window_picture("back_wall", curtain="hospital privacy curtain")
    room.place_door("front_wall", position="right")

scene.export("hospital_room.blend")
