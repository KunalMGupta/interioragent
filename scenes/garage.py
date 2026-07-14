"""
Garage — "Home Workshop Garage".
Phase 1: a workbench anchor against the back wall carrying the room lighting.
Phase 2: a tool chest and metal shelving along walls; a pile of storage boxes.
Phase 3: a stack of tyres, a wall pegboard of tools, a small window, a side door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Garage", seed=9)

with scene.RelativeGroup() as bench_group:
    bench_group.set_anchor(scene.AddAsset("a heavy-duty workbench with a vice"))
    bench_group.add_lighting("a bright fluorescent shop ceiling light", density=0)

with scene.StackGroup() as tyres:
    tyres.set_anchor(scene.AddAsset("a low garage floor mat"))
    tyres.place_stack(3 * scene.AddAsset("a black car tyre"))

with scene.PileGroup() as boxes:
    boxes.set_anchor(scene.AddAsset("a wooden pallet"))
    boxes.place_pile(5 * scene.AddAsset("a cardboard storage box"), spread=0.7)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.3) as room:
    room.place_walls(floor_texture="grey concrete floor",
                     ceiling_texture="exposed beams", wall_texture="unfinished drywall")
    room.place_on_back_wall_center(bench_group)
    room.place_on_front_left(tyres, facing="front")
    room.place_on_front_right(boxes, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a tall red metal tool chest"))
    room.place_on_right_wall_center(scene.AddAsset("a metal garage storage shelf"))
    room.place_on_wall_back_left(scene.AddAsset("a wall pegboard with hanging tools"))
    room.place_window_picture("left_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("garage.blend")
