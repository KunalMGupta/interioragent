"""
Library — "Quiet Reading Hall".
Phase 1: reading tables ringed with chairs (AroundGroup, gentle jitter) at the center.
Phase 2: tall bookshelves lined up against the walls.
Phase 3: a couple of armchairs in a corner, window, wall art, pendant lighting, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Library", seed=36)

with scene.AroundGroup(sparsity=0.3, jitter=0.4) as reading:
    table = scene.AddAsset("a large wooden reading table")
    reading.set_anchor(table)
    reading.place_rectilinear(longer_side1=3 * scene.AddAsset("a wooden reading chair"),
                              longer_side2=3 * scene.AddAsset("a wooden reading chair"))
    reading.place_on_top(scene.AddAsset("a green banker's desk lamp"))
    reading.add_lighting("a row of linear ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.15) as room:
    room.place_walls(floor_texture="dark parquet wood",
                     ceiling_texture="cream", wall_texture="warm tan")
    room.place_on_center(reading, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a tall wooden bookshelf full of books"))
    room.place_on_left_wall_center(scene.AddAsset("a tall wooden bookshelf full of books"))
    room.place_on_right_wall_center(scene.AddAsset("a tall wooden bookshelf full of books"))
    room.place_on_front_left_corner(scene.AddAsset("a cozy leather reading armchair"))
    room.place_window_floor_to_ceiling("front_wall", curtain="heavy red drapes")
    room.place_door("front_wall", position="right")

scene.export("library.blend")
