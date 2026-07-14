"""
Game room — "Rec Room".
Phase 1: a pool table centerpiece with a low hanging light over it.
Phase 2: a lounge sofa + armchairs around a small table for spectators.
Phase 3: arcade cabinets against a wall, a wall-mounted TV, neon art, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("GameRoom", seed=4)

with scene.RelativeGroup() as pool_group:
    pool = scene.AddAsset("a green felt pool billiards table")
    pool_group.set_anchor(pool)
    pool_group.add_lighting("a low rectangular billiard pendant light", density=0)

with scene.AroundGroup(sparsity=0.4, jitter=0.5) as lounge:
    ltable = scene.AddAsset("a small low coffee table")
    lounge.set_anchor(ltable)
    lounge.place_arc(2 * scene.AddAsset("a comfy gaming armchair"))

with scene.RoomGroup(modulate_scale=1.05, randomness=0.25) as room:
    room.place_walls(floor_texture="dark wood laminate",
                     ceiling_texture="charcoal", wall_texture="deep navy")
    room.place_on_center(pool_group, facing="front")
    room.place_on_front_right(lounge, facing="back")
    room.place_on_back_wall_left(scene.AddAsset("a retro upright arcade cabinet"))
    room.place_on_back_wall_right(scene.AddAsset("a retro upright arcade cabinet"))
    room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted flat screen TV", width=1.8))
    room.place_on_wall_left_center(scene.AddAsset("a neon game-room wall sign"))
    room.place_window_picture("right_wall", curtain="blackout curtains")
    room.place_door("front_wall", position="right")

scene.export("game_room.blend")
