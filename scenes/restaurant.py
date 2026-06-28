"""
Restaurant — "Bistro Dining Room".
Phase 1: several small dining clusters (table + chairs, AroundGroup with jitter so each
         table reads independently and a little lived-in), spread through the room.
Phase 2: a host stand near the entrance.
Phase 3: banquette/sideboard against a wall, window, wall art, pendant lights, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Restaurant", seed=37)


def table_for_two(light=False):
    g = scene.AroundGroup(sparsity=0.2, jitter=0.5)
    with g:
        t = scene.AddAsset("a small round bistro dining table")
        g.set_anchor(t)
        chairs = 2 * scene.AddAsset("a bentwood bistro chair")
        g.place_rectilinear(shorter_side1=[chairs[0]], shorter_side2=[chairs[1]])
        g.place_on_top(scene.AddAsset("a small vase with a flower"))
        if light:
            g.add_lighting("a small warm pendant light", density=0)
    return g

t1, t2, t3, t4 = table_for_two(True), table_for_two(), table_for_two(True), table_for_two()

with scene.RoomGroup(modulate_scale=1.05, randomness=0.25) as room:
    room.place_walls(floor_texture="herringbone wood floor",
                     ceiling_texture="warm white", wall_texture="dark green panelled")
    room.place_on_back_left(t1, facing="front")
    room.place_on_back_right(t2, facing="front")
    room.place_on_front_left(t3, facing="front")
    room.place_on_front_right(t4, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a wooden host stand podium"))
    room.place_on_left_wall_center(scene.AddAsset("a long upholstered banquette bench"))
    room.place_window_floor_to_ceiling("right_wall", curtain="sheer cafe curtains")
    room.place_on_wall_back_center(scene.AddAsset("a large framed vintage poster"))
    room.place_door("front_wall", position="right")

scene.export("restaurant.blend")
