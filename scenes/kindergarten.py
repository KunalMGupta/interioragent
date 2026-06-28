"""
Kindergarten — "Bright Activity Room".
Phase 1: low activity tables each ringed by tiny chairs (AroundGroup, jittered), a few of
         them spread around the room.
Phase 2: a play rug + a pile of toy bins.
Phase 3: cubby storage and a low bookshelf against walls, alphabet wall art, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Kindergarten", seed=14)


def activity_table(light=False):
    g = scene.AroundGroup(sparsity=0.25, jitter=0.5)
    with g:
        t = scene.AddAsset("a low round kids activity table")
        g.set_anchor(t)
        g.place_circle(4 * scene.AddAsset("a tiny colorful kids chair"))
        if light:
            g.add_lighting("a bright cheerful ceiling light", density=0)
    return g

t1, t2 = activity_table(True), activity_table(True)

with scene.PileGroup() as toys:
    toys.set_anchor(scene.AddAsset("a soft foam play mat"))
    toys.place_pile(5 * scene.AddAsset("a bright plastic toy bin"), spread=0.7)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.3) as room:
    room.place_walls(floor_texture="rainbow foam floor tiles",
                     ceiling_texture="white", wall_texture="sunny yellow")
    room.place_on_back_left(t1, facing="front")
    room.place_on_back_right(t2, facing="front")
    room.place_on_front_left(toys, facing="front")
    room.place_on_right_wall_center(scene.AddAsset("a low kids cubby storage unit"))
    room.place_on_left_wall_center(scene.AddAsset("a low kids bookshelf with picture books"))
    room.place_on_wall_back_center(scene.AddAsset("a colorful alphabet wall chart"))
    room.place_window_picture("front_wall", curtain="bright primary-color curtains")
    room.place_door("front_wall", position="right")

scene.export("kindergarten.blend")
