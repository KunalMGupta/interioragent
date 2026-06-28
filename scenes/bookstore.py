"""
Bookstore — "Indie Bookshop".
Phase 1: bookshelves in aisles (GridGroup) plus a central display table piled with books.
Phase 2: a cozy reading armchair corner.
Phase 3: a checkout counter, signage, window, warm lighting, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Bookstore", seed=40)

with scene.GridGroup(sparsity=0.7) as shelves:
    shelves.place_grid(4 * scene.AddAsset("a tall wooden bookshelf full of books"), cols=2)

with scene.PileGroup() as display:
    display.set_anchor(scene.AddAsset("a low wooden display table"))
    display.place_pile(6 * scene.AddAsset("a stack of hardcover books"), spread=0.5)
    display.add_lighting("warm pendant ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.2) as room:
    room.place_walls(floor_texture="warm wooden floorboards",
                     ceiling_texture="cream", wall_texture="warm terracotta")
    room.place_on_center(shelves, facing="front")
    room.place_on_front_left(display, facing="front")
    room.place_on_front_right_corner(scene.AddAsset("a cozy reading armchair"))
    room.place_on_back_wall_center(scene.AddAsset("a wooden bookstore checkout counter"))
    room.place_on_wall_left_center(scene.AddAsset("a framed vintage bookshop sign"))
    room.place_window_picture("front_wall", curtain="warm cafe curtains")
    room.place_door("front_wall", position="right")

scene.export("bookstore.blend")
