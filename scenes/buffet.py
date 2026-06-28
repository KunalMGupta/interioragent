"""
Buffet — "Hotel Buffet Hall".
Phase 1: long buffet serving counters down the middle (GridGroup row).
Phase 2: dining tables ringed with chairs (AroundGroup, jitter) spread around the hall.
Phase 3: a beverage station and stacked plates, warm lighting, large windows, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Buffet", seed=51)

with scene.GridGroup(sparsity=0.2) as serving:
    serving.place_row(3 * scene.AddAsset("a long buffet serving counter with sneeze guard"))


def dining_table(light=False):
    g = scene.AroundGroup(sparsity=0.3, jitter=0.5)
    with g:
        t = scene.AddAsset("a round banquet dining table")
        g.set_anchor(t)
        g.place_circle(4 * scene.AddAsset("a banquet dining chair"))
        if light:
            g.add_lighting("a warm ceiling light", density=0)
    return g

t1, t2 = dining_table(True), dining_table(True)

with scene.RoomGroup(modulate_scale=1.2, randomness=0.25) as room:
    room.place_walls(floor_texture="patterned hotel carpet",
                     ceiling_texture="warm white", wall_texture="soft gold")
    room.place_on_back(serving, facing="front")
    room.place_on_front_left(t1, facing="front")
    room.place_on_front_right(t2, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a beverage and coffee station"))
    room.place_on_right_wall_center(scene.AddAsset("a stack of plates and trays station"))
    room.place_window_floor_to_ceiling("back_wall", curtain="elegant sheer drapes")
    room.place_door("front_wall", position="right")

scene.export("buffet.blend")
