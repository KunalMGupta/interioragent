"""
Office — "Open-plan Workspace".
Phase 1: desk+chair units arranged in a grid with aisles (GridGroup sparsity+randomness
         so the workstations are not unnaturally perfectly aligned).
Phase 2: a central anchor cluster carries the room lighting.
Phase 3: filing cabinets + bookshelf against walls, whiteboard, window, plants, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Office", seed=18)

with scene.RelativeGroup() as desk_unit:
    desk = scene.AddAsset("a white office desk")
    chair = scene.AddAsset("a black mesh office chair")
    desk_unit.place_desk_chair(desk, chair)

with scene.GridGroup(sparsity=0.6, randomness=0.4) as desks:
    desks.place_grid(6 * desk_unit, cols=3)

# a small central plant cluster to host the ceiling lighting
with scene.RelativeGroup() as light_anchor:
    light_anchor.set_anchor(scene.AddAsset("a low office plant"))
    light_anchor.add_lighting("a rectangular LED panel ceiling light", density=0)

with scene.RoomGroup(randomness=0.2) as room:
    room.place_walls(floor_texture="grey carpet tiles",
                     ceiling_texture="white acoustic tiles", wall_texture="light grey")
    room.place_on_center(desks, facing="front")
    room.place_on_back(light_anchor)
    room.place_on_back_wall_left(scene.AddAsset("a row of metal filing cabinets"))
    room.place_on_right_wall_center(scene.AddAsset("a tall office bookshelf with binders"))
    room.place_on_back_left_corner(scene.AddAsset("a tall potted office plant"))
    room.place_on_wall_back_center(scene.AddAsset("a large wall-mounted whiteboard", width=2.0))
    room.place_window_floor_to_ceiling("left_wall", curtain="grey roller blinds")
    room.place_door("front_wall", position="right")

scene.export("office.blend")
