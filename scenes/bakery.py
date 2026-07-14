"""
Bakery — "Corner Bakery".
Phase 1: a glass bakery display counter as the anchor, carrying the lighting.
Phase 2: small cafe tables with chairs for eat-in (AroundGroup, jitter).
Phase 3: bread shelving behind the counter, a chalkboard menu, an oven, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Bakery", seed=45)

with scene.RelativeGroup() as counter_group:
    counter_group.set_anchor(scene.AddAsset("a glass bakery pastry display counter"))
    counter_group.add_lighting("warm pendant ceiling lights", density=0)


def cafe_table():
    g = scene.AroundGroup(sparsity=0.25, jitter=0.5)
    with g:
        t = scene.AddAsset("a small round cafe table")
        g.set_anchor(t)
        g.place_rectilinear(shorter_side1=[scene.AddAsset("a wooden cafe chair")],
                            shorter_side2=[scene.AddAsset("a wooden cafe chair")])
    return g

t1, t2 = cafe_table(), cafe_table()

with scene.RoomGroup(randomness=0.2) as room:
    room.place_walls(floor_texture="warm terracotta tiles",
                     ceiling_texture="cream", wall_texture="soft buttery yellow")
    room.place_on_back(counter_group, facing="front")
    room.place_on_front_left(t1, facing="front")
    room.place_on_front_right(t2, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a tall bakery shelf full of bread loaves"))
    room.place_on_left_wall_center(scene.AddAsset("a large stainless bakery oven"))
    room.place_on_wall_back_center(scene.AddAsset("a chalkboard bakery menu board"))
    room.place_window_picture("right_wall", curtain="gingham cafe curtains")
    room.place_door("front_wall", position="right")

scene.export("bakery.blend")
