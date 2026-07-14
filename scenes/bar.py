"""
Bar — "Moody Cocktail Lounge".
Phase 1: bar counter with a row of stools along its front (AroundGroup, jittered).
Phase 2: a couple of lounge tables with chairs in the room.
Phase 3: back-bar shelving against the wall, wall art, low warm lighting, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Bar", seed=26)

with scene.AroundGroup(sparsity=0.15, jitter=0.4) as bar_group:
    counter = scene.AddAsset("a long modern bar counter")
    bar_group.set_anchor(counter)
    stools = 5 * scene.AddAsset("a tall industrial bar stool")
    bar_group.place_rectilinear(longer_side1=stools)
    bar_group.add_lighting("a row of warm pendant lights", density=0)

with scene.AroundGroup(sparsity=0.3, jitter=0.5) as lounge:
    ltable = scene.AddAsset("a small round cocktail table")
    lounge.set_anchor(ltable)
    lounge.place_circle(3 * scene.AddAsset("a low velvet lounge chair"))

with scene.RoomGroup(randomness=0.2) as room:
    room.place_walls(floor_texture="dark stained concrete",
                     ceiling_texture="charcoal", wall_texture="dark teal")
    room.place_on_back(bar_group, facing="front")
    room.place_on_front_right(lounge, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a tall back-bar shelf lined with bottles"))
    room.place_on_wall_left_center(scene.AddAsset("a neon framed wall art sign"))
    room.place_door("front_wall", position="left")

scene.export("bar.blend")
