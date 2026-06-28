"""
Living room — "Warm Modern Living Oasis".
Phase 1: U-style seating cluster (coffee table center, sofa back, accent chairs flanking).
Phase 2: floor lamp, corner plants, styled coffee table.
Phase 3: bookshelf, ring pendant, window + sheers, wall art, door.
RoomGroup(randomness) loosens the corner plants / bookshelf off dead-center.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("LivingRoom", seed=42)

with scene.RelativeGroup() as seating:
    coffee = scene.AddAsset("a low wooden coffee table")
    seating.set_anchor(coffee)
    sofa = scene.AddAsset("a cream low-profile 3-seat sofa")
    seating.place_on_back_further(sofa)
    chairs = 2 * scene.AddAsset("a wood-framed leather accent chair")
    seating.place_on_front_left_further(chairs[0])
    seating.place_on_front_right_further(chairs[1])
    seating.face(chairs[0], toward=coffee)
    seating.face(chairs[1], toward=coffee)
    floor_lamp = scene.AddAsset("a warm-toned arc floor lamp")
    seating.place_on_back_right_further(floor_lamp)
    seating.place_on_top(scene.AddAsset("a decorative tray with stacked books and a small vase"))
    seating.place_rug("a plush ivory wool rug", size=0.9)
    seating.add_lighting("a circular ring pendant light", density=0)

with scene.RoomGroup(modulate_scale=0.9, randomness=0.25) as room:
    room.place_walls(floor_texture="light oak planks",
                     ceiling_texture="warm white", wall_texture="warm beige")
    room.place_on_center(seating, facing="front")
    bookshelf = scene.AddAsset("a tall wooden open bookshelf with books and decor")
    room.place_on_back_wall_center(bookshelf)
    room.place_on_back_left_corner(scene.AddAsset("a large potted fiddle-leaf fig plant"))
    room.place_on_front_right_corner(scene.AddAsset("a medium potted plant"))
    room.place_window_floor_to_ceiling("left_wall", curtain="white sheer curtains")
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract art print"))
    room.place_door("front_wall", position="right")

scene.export("living_room.blend")
