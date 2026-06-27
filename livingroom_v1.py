"""
Living room — "Warm Modern Living Oasis". Built coarse-to-fine; VLM-clean.
Phase 1: floor anchors (U-style seating cluster + rug, bookshelf, shell).
Phase 2: surface & floor details (floor lamp, corner plants, coffee-table styling).
Phase 3: walls/ceiling/decor (ring pendant light, window + sheers, wall art, door)
         + final-phase room rescale (modulate_scale=0.9).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("LivingRoomV1", seed=42)

# --- U-style seating cluster: coffee table center, sofa back, chairs flanking front ---
with scene.RelativeGroup() as seating:
    coffee = scene.AddAsset("a low wooden coffee table")
    seating.set_anchor(coffee)

    sofa = scene.AddAsset("a cream low-profile 3-seat sofa")
    seating.place_on_back_further(sofa)

    chairs = 2 * scene.AddAsset("a wood-framed leather accent chair")
    seating.place_on_front_left_further(chairs[0])
    seating.place_on_front_right_further(chairs[1])
    # Placement leaves the flanking chairs facing sideways (±90°); turn them in
    # to face the coffee table so the cluster reads as a conversation U.
    seating.face(chairs[0], toward=coffee)
    seating.face(chairs[1], toward=coffee)

    # Phase 2: floor lamp beside the sofa + a styled centerpiece on the coffee table
    floor_lamp = scene.AddAsset("a warm-toned arc floor lamp")
    seating.place_on_back_right_further(floor_lamp)
    seating.place_on_top(scene.AddAsset("a decorative tray with stacked books and a small vase"))

    seating.place_rug("a plush ivory wool rug", size=0.9)

    # Phase 3: ring pendant over the cluster — also the room's main light source
    seating.add_lighting("a circular ring pendant light", density=0)

# --- room shell + the bookshelf anchor on the back wall ---
# Final-phase room rescale: VLM RoomProportions suggested 0.9 once all furniture
# was placed (occupancy settled). Applied per the "act on room size in the final
# phase" rule.
with scene.RoomGroup(modulate_scale=0.9) as room:
    room.place_walls(
        floor_texture="light oak planks",
        ceiling_texture="warm white",
        wall_texture="warm beige",
    )
    room.place_on_center(seating, facing="front")

    bookshelf = scene.AddAsset("a tall wooden open bookshelf with books and decor")
    room.place_on_back_wall_center(bookshelf)

    # Phase 2: corner greenery to soften the geometry
    room.place_on_back_left_corner(scene.AddAsset("a large potted fiddle-leaf fig plant"))
    room.place_on_front_right_corner(scene.AddAsset("a medium potted plant"))

    # Phase 3: daylight window + sheers, framed art, and an entry door
    room.place_window_floor_to_ceiling("left_wall", curtain="white sheer curtains")
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract art print"))
    room.place_door("front_wall", position="right")

scene.export("livingroom_v1.blend")
