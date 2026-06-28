"""
Video store — "Rental Shop".
Phase 1: media display shelves in aisles (GridGroup rows).
Phase 2: a checkout counter near the entrance carrying the room lighting.
Phase 3: a couple of beanbags in a corner, movie posters on the walls, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("VideoStore", seed=32)

with scene.GridGroup(sparsity=0.7) as aisles:
    aisles.place_grid(6 * scene.AddAsset("a media display shelf with dvd cases"), cols=3)

with scene.PileGroup() as beanbags:
    beanbags.set_anchor(scene.AddAsset("a small floor rug"))
    beanbags.place_pile(2 * scene.AddAsset("a colorful beanbag chair"), spread=0.6)

with scene.RelativeGroup() as counter_group:
    counter_group.set_anchor(scene.AddAsset("a retail checkout counter"))
    counter_group.add_lighting("a row of fluorescent ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.2) as room:
    room.place_walls(floor_texture="grey commercial carpet",
                     ceiling_texture="white drop ceiling", wall_texture="bright blue")
    room.place_on_center(aisles, facing="front")
    room.place_on_front_left(counter_group, facing="back")
    room.place_on_front_right(beanbags, facing="front")
    room.place_on_wall_back_left(scene.AddAsset("a framed movie poster"))
    room.place_on_wall_back_right(scene.AddAsset("a framed movie poster"))
    room.place_window_picture("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("video_store.blend")
