"""
Bedroom — "Calm Modern Retreat".
Phase 1: bed anchor with flanking nightstands + table lamps on top.
Phase 2: bench at the foot, rug, dresser on a wall.
Phase 3: wardrobe, window + curtains, wall art, pendant, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Bedroom", seed=2)

with scene.RelativeGroup() as bed_group:
    bed = scene.AddAsset("a modern upholstered queen bed with headboard")
    bed_group.set_anchor(bed)
    nightstands = 2 * scene.AddAsset("a small wooden nightstand")
    bed_group.place_on_back_left(nightstands[0])
    bed_group.place_on_back_right(nightstands[1])
    bench = scene.AddAsset("an upholstered bedroom bench")
    bed_group.place_on_front_adjacent(bench)
    bed_group.place_rug("a soft grey area rug", size=0.8)
    bed_group.add_lighting("a modern flush ceiling light", density=0)

# table lamps resting on the nightstands
with scene.RelativeGroup() as lamp_l:
    lamp_l.set_anchor(nightstands[0])
    lamp_l.place_on_top(scene.AddAsset("a small bedside table lamp"))
with scene.RelativeGroup() as lamp_r:
    lamp_r.set_anchor(nightstands[1])
    lamp_r.place_on_top(scene.AddAsset("a small bedside table lamp"))

with scene.RoomGroup(randomness=0.2) as room:
    room.place_walls(floor_texture="warm oak planks",
                     ceiling_texture="white", wall_texture="muted sage green")
    room.place_on_center(bed_group, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a wide wooden dresser with drawers"))
    room.place_on_back_left_corner(scene.AddAsset("a tall potted plant"))
    room.place_on_right_wall_center(scene.AddAsset("a tall wardrobe closet"))
    room.place_window_floor_to_ceiling("front_wall", curtain="linen drapes")
    room.place_on_wall_back_center(scene.AddAsset("a framed botanical print"))
    room.place_door("right_wall", position="left")

scene.export("bedroom.blend")
