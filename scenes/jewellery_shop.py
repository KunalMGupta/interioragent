"""
Jewellery shop — "Boutique Counter". A small, luxe space.
Phase 1: glass display cases arranged in an L around the sales floor (AroundGroup
         rectilinear), with stools on the customer side.
Phase 2: the cases carry the room's bright spot lighting.
Phase 3: a tall wall display cabinet, a mirror, framed art, a window, a door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("JewelleryShop", seed=42)

with scene.AroundGroup(sparsity=0.2, jitter=0.15) as counters:
    case = scene.AddAsset("a glass jewellery display counter")
    counters.set_anchor(case)
    counters.place_rectilinear(shorter_side1=2 * scene.AddAsset("a small customer stool"))
    counters.add_lighting("bright warm jewellery spotlights", density=0)

with scene.RoomGroup(modulate_scale=0.85, randomness=0.1) as room:
    room.place_walls(floor_texture="cream polished marble",
                     ceiling_texture="warm white", wall_texture="champagne gold")
    room.place_on_center(counters, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a tall glass wall display cabinet"))
    room.place_on_wall_left_center(scene.AddAsset("an ornate wall mirror"))
    room.place_on_wall_right_center(scene.AddAsset("a small framed luxury art print"))
    room.place_window_picture("front_wall", curtain="elegant sheer curtains")
    room.place_door("front_wall", position="right")

scene.export("jewellery_shop.blend")
