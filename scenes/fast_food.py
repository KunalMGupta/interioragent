"""
Fast food — "Burger Joint Dining".
Phase 1: fixed booth-and-table seating units in a grid (GridGroup) on the dining floor.
Phase 2: a central anchor carrying the bright lighting.
Phase 3: a service counter with menu boards, a drink station, signage, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("FastFood", seed=47)


def booth():
    g = scene.RelativeGroup()
    with g:
        t = scene.AddAsset("a fast food dining table")
        g.set_anchor(t)
        g.place_on_back_adjacent(scene.AddAsset("a fast food bench seat"))
        g.place_on_front_adjacent(scene.AddAsset("a fast food bench seat"))
    return g

with scene.GridGroup(sparsity=0.5, randomness=0.1) as booths:
    booths.place_grid([booth() for _ in range(4)], cols=2)

with scene.RelativeGroup() as light_anchor:
    light_anchor.set_anchor(scene.AddAsset("a small trash and tray station"))
    light_anchor.add_lighting("a grid of bright ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.15) as room:
    room.place_walls(floor_texture="red and white floor tiles",
                     ceiling_texture="white", wall_texture="bright red")
    room.place_on_center(booths, facing="front")
    room.place_on_back(light_anchor)
    room.place_on_back_wall_center(scene.AddAsset("a fast food service counter"))
    room.place_on_left_wall_center(scene.AddAsset("a self-serve soda drink station"))
    room.place_on_wall_back_center(scene.AddAsset("a backlit fast food menu board", width=2.0))
    room.place_window_floor_to_ceiling("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("fast_food.blend")
