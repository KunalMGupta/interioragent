"""
Art studio — "Painter's Loft".
Phase 1: easels arranged loosely around the room (AroundGroup, heavy jitter for an
         informal, working feel) about a central supply table.
Phase 2: the supply table carries the room lighting; a pile of paint supplies.
Phase 3: a storage shelf of materials, canvases leaning on a wall, big north window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ArtStudio", seed=13)

with scene.AroundGroup(sparsity=0.5, jitter=0.7) as easels:
    table = scene.AddAsset("a paint-splattered wooden work table")
    easels.set_anchor(table)
    easels.place_circle(4 * scene.AddAsset("a wooden artist easel with a canvas"))
    easels.place_on_top(scene.AddAsset("a cluster of paint jars and brushes"))
    easels.add_lighting("a row of bright studio ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.3) as room:
    room.place_walls(floor_texture="paint-spattered wood floor",
                     ceiling_texture="white", wall_texture="raw white plaster")
    room.place_on_center(easels, facing="front")
    room.place_on_back_wall_left(scene.AddAsset("a tall art supply storage shelf"))
    room.place_on_right_wall_center(scene.AddAsset("a low cabinet stacked with canvases"))
    room.place_on_wall_back_center(scene.AddAsset("a large colorful abstract painting"))
    room.place_window_floor_to_ceiling("left_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("art_studio.blend")
