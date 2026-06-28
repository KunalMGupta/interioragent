"""
Deli — "Corner Delicatessen".
Phase 1: a refrigerated display counter as the anchor, carrying the lighting.
Phase 2: a couple of small cafe tables with chairs for eat-in (AroundGroup, jitter).
Phase 3: shelving of products behind the counter, a menu board, a fridge, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Deli", seed=43)

with scene.RelativeGroup() as counter_group:
    counter_group.set_anchor(scene.AddAsset("a refrigerated deli display counter"))
    counter_group.add_lighting("a row of warm ceiling lights", density=0)


def cafe_table():
    g = scene.AroundGroup(sparsity=0.25, jitter=0.5)
    with g:
        t = scene.AddAsset("a small round cafe table")
        g.set_anchor(t)
        g.place_rectilinear(shorter_side1=[scene.AddAsset("a metal cafe chair")],
                            shorter_side2=[scene.AddAsset("a metal cafe chair")])
    return g

t1, t2 = cafe_table(), cafe_table()

with scene.RoomGroup(modulate_scale=1.0, randomness=0.2) as room:
    room.place_walls(floor_texture="black and white checkerboard tiles",
                     ceiling_texture="cream", wall_texture="warm cream")
    room.place_on_back(counter_group, facing="front")
    room.place_on_front_left(t1, facing="front")
    room.place_on_front_right(t2, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a tall deli shelf stocked with products"))
    room.place_on_left_wall_center(scene.AddAsset("a glass-door beverage fridge"))
    room.place_on_wall_back_center(scene.AddAsset("a chalkboard deli menu board"))
    room.place_window_picture("right_wall", curtain="cafe curtains")
    room.place_door("front_wall", position="right")

scene.export("deli.blend")
