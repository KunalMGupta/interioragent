"""
Lobby — "Hotel Reception Lobby". A spacious welcoming room.
Phase 1: a lounge seating cluster (sofas + chairs around a coffee table, AroundGroup jitter).
Phase 2: a reception desk against the back wall.
Phase 3: large potted plants, wall art, a feature chandelier, glass entrance, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Lobby", seed=22)

with scene.AroundGroup(sparsity=0.4, jitter=0.4) as lounge:
    coffee = scene.AddAsset("a large rectangular lobby coffee table")
    lounge.set_anchor(coffee)
    lounge.place_rectilinear(longer_side1=[scene.AddAsset("a modern lobby sofa")],
                             longer_side2=[scene.AddAsset("a modern lobby sofa")],
                             shorter_side1=[scene.AddAsset("a lobby accent armchair")],
                             shorter_side2=[scene.AddAsset("a lobby accent armchair")])
    lounge.place_rug("a large neutral area rug", size=0.95)
    lounge.add_lighting("a grand modern chandelier", density=0)

with scene.RoomGroup(modulate_scale=1.25, randomness=0.2) as room:
    room.place_walls(floor_texture="polished marble floor",
                     ceiling_texture="warm white", wall_texture="warm stone")
    room.place_on_center(lounge, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a long modern hotel reception desk"))
    room.place_on_back_left_corner(scene.AddAsset("a very tall potted palm"))
    room.place_on_back_right_corner(scene.AddAsset("a very tall potted palm"))
    room.place_on_wall_left_center(scene.AddAsset("a very large framed abstract artwork"))
    room.place_window_floor_to_ceiling("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("lobby.blend")
