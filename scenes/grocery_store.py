"""
Grocery store — "Neighborhood Market".
Phase 1: gondola shelving aisles stocked with goods (GridGroup).
Phase 2: produce bins piled near the entrance; a checkout counter carries the lighting.
Phase 3: refrigerated cases along a wall, signage, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("GroceryStore", seed=46)

with scene.GridGroup(sparsity=0.7) as aisles:
    aisles.place_grid(6 * scene.AddAsset("a grocery gondola shelf stocked with products"), cols=3)

with scene.PileGroup() as produce:
    produce.set_anchor(scene.AddAsset("a wooden produce display bin"))
    produce.place_pile(5 * scene.AddAsset("a crate of fresh produce"), spread=0.7)

with scene.GridGroup(sparsity=0.3) as checkouts:
    checkouts.place_row(2 * scene.AddAsset("a grocery checkout counter"))

with scene.RelativeGroup() as light_anchor:
    light_anchor.set_anchor(scene.AddAsset("a shopping cart"))
    light_anchor.add_lighting("a grid of bright fluorescent ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.15, randomness=0.15) as room:
    room.place_walls(floor_texture="white vinyl floor tiles",
                     ceiling_texture="white drop ceiling", wall_texture="light grey")
    room.place_on_center(aisles, facing="front")
    room.place_on_back(light_anchor)
    room.place_on_front_left(produce, facing="front")
    room.place_on_front(checkouts, facing="back")
    room.place_on_back_wall_center(scene.AddAsset("a refrigerated grocery display case"))
    room.place_on_wall_left_center(scene.AddAsset("a grocery aisle sign"))
    room.place_window_floor_to_ceiling("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("grocery_store.blend")
