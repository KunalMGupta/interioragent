"""
Florist shop — "Flower Market".
Phase 1: tiered flower display stands arranged around the shop (AroundGroup, jitter),
         brimming with bouquets.
Phase 2: a work counter with wrapping supplies carrying the lighting; buckets of flowers.
Phase 3: a shelf of vases and pots, hanging plants feel via potted greenery, window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("FloristShop", seed=48)

with scene.AroundGroup(sparsity=0.5, jitter=0.6) as stands:
    center = scene.AddAsset("a tiered wooden flower display stand")
    stands.set_anchor(center)
    stands.place_circle(4 * scene.AddAsset("a flower display stand full of bouquets"))
    stands.add_lighting("bright natural-tone ceiling lights", density=0)

with scene.PileGroup() as buckets:
    buckets.set_anchor(scene.AddAsset("a small floor mat"))
    buckets.place_pile(5 * scene.AddAsset("a metal bucket full of cut flowers"), spread=0.7)

with scene.RoomGroup(randomness=0.25) as room:
    room.place_walls(floor_texture="weathered grey wood planks",
                     ceiling_texture="white", wall_texture="sage green")
    room.place_on_center(stands, facing="front")
    room.place_on_front_left(buckets, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a wooden florist work counter"))
    room.place_on_right_wall_center(scene.AddAsset("a shelf of vases and flower pots"))
    room.place_on_back_left_corner(scene.AddAsset("a tall leafy potted plant"))
    room.place_window_floor_to_ceiling("front_wall", curtain=None)
    room.place_door("front_wall", position="right")

scene.export("florist_shop.blend")
