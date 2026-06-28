"""
Dining room — "Family Dinner". Built coarse-to-fine.
Phase 1: dining table with chairs ringed around it (AroundGroup, jittered so the
         seating looks used rather than perfectly machine-placed).
Phase 2: a centerpiece on the table + rug + sideboard against a wall.
Phase 3: chandelier, window + drapes, wall art, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("DiningRoom", seed=6)

with scene.AroundGroup(sparsity=0.25, jitter=0.5) as dining:
    table = scene.AddAsset("a rectangular wooden dining table")
    dining.set_anchor(table)
    side1 = 3 * scene.AddAsset("an upholstered dining chair")
    side2 = 3 * scene.AddAsset("an upholstered dining chair")
    dining.place_rectilinear(longer_side1=side1, longer_side2=side2)
    dining.place_on_top(scene.AddAsset("a decorative table runner with a vase of flowers"))
    dining.place_rug("a large patterned area rug", size=0.95)
    dining.add_lighting("an elegant linear chandelier", density=0)

with scene.RoomGroup(randomness=0.2) as room:
    room.place_walls(floor_texture="dark walnut planks",
                     ceiling_texture="white", wall_texture="deep blue-grey")
    room.place_on_center(dining, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a wooden sideboard buffet cabinet"))
    room.place_on_back_left_corner(scene.AddAsset("a tall potted plant"))
    room.place_window_floor_to_ceiling("left_wall", curtain="cream drapes")
    room.place_on_wall_right_center(scene.AddAsset("a large framed landscape painting"))
    room.place_door("front_wall", position="left")

scene.export("dining_room.blend")
