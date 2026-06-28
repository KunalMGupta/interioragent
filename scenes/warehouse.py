"""
Warehouse — "Storage Depot". A large, high-ceilinged utilitarian space.
Phase 1: tall pallet racking shelves in rows (GridGroup) forming aisles.
Phase 2: pallets of boxes piled on the floor; a workbench anchor carries the lighting.
Phase 3: a roll-up door, high windows, concrete finishes.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Warehouse", seed=28)

with scene.GridGroup(sparsity=0.8) as racking:
    racking.place_grid(6 * scene.AddAsset("a tall industrial pallet racking shelf"), cols=3)

with scene.PileGroup() as pallets:
    pallets.set_anchor(scene.AddAsset("a wooden shipping pallet"))
    pallets.place_pile(6 * scene.AddAsset("a stacked cardboard shipping box"), spread=0.9)

with scene.RelativeGroup() as bench_group:
    bench_group.set_anchor(scene.AddAsset("a metal packing workbench"))
    bench_group.add_lighting("a grid of high-bay industrial ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.4, randomness=0.25) as room:
    room.place_walls(floor_texture="sealed grey concrete",
                     ceiling_texture="exposed steel deck", wall_texture="grey metal panel")
    room.place_on_center(racking, facing="front")
    room.face(racking, toward="front_wall")
    room.place_on_front_left(pallets, facing="front")
    room.place_on_back(bench_group, facing="front")
    room.place_window_standard("left_wall", position="center")
    room.place_door("front_wall", position="center")

scene.export("warehouse.blend")
