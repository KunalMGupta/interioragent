"""
Prison cell — "Spartan Cell". A deliberately small, bare room.
Phase 1: a metal bunk bed against the wall.
Phase 2: a stainless toilet-sink combo and a small fixed desk + stool.
Phase 3: a small barred window, a single ceiling light (on the desk anchor), a heavy door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("PrisonCell", seed=7)

with scene.RelativeGroup() as desk_group:
    desk_group.set_anchor(scene.AddAsset("a small fixed metal wall desk"))
    desk_group.place_on_front_adjacent(scene.AddAsset("a metal stool"))
    desk_group.add_lighting("a caged ceiling light", density=0)

with scene.RoomGroup(modulate_scale=0.7, randomness=0.0) as room:
    room.place_walls(floor_texture="grey concrete floor",
                     ceiling_texture="grey concrete", wall_texture="bare concrete block")
    room.place_on_right(desk_group, facing="left")
    room.place_on_left_wall_center(scene.AddAsset("a grey metal bunk bed"))
    room.place_on_front_left_corner(scene.AddAsset("a stainless steel prison toilet sink combo"))
    room.place_window_standard("back_wall", position="center")
    room.place_door("front_wall", position="right")

scene.export("prison_cell.blend")
