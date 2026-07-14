"""Minimal isolation scene to confirm the fixed jewelry assets assemble + place correctly.

Places the OLIVIA counter at three different (off-origin) spots + the triple necklace bust on a
pedestal. Before the fix these rendered disassembled with pieces stuck at the world origin; after
the verbatim-copy fix each should be a single whole, textured object at its placed position.
"""
from IDSDL.scene import SceneProgRoom

JCOUNTER = "custom/1028be7dddc5b7e1a0c4339582223f5d787400c3"   # OLIVIA jewelry display counter
NBUST3   = "custom/df9fc6e68ff291495a9fcf53945c3cda10e14e16"   # triple necklace bust

scene = SceneProgRoom("VerifyJewelry", seed=1)

with scene.RelativeGroup() as ped:
    ped.set_anchor(scene.AddAsset("a tall rectangular marble pedestal display stand"))
    ped.place_on_top([scene.AddAsset("a triple black velvet necklace display bust", asset_id=NBUST3)])

with scene.RoomGroup(modulate_scale=0.9, randomness=0.05) as room:
    room.place_walls(floor_texture="polished stone floor",
                     ceiling_texture="white", wall_texture="warm light greige")
    room.place_on_back_wall_center(scene.AddAsset("a glass-top jewelry display counter", asset_id=JCOUNTER), facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a glass-top jewelry display counter", asset_id=JCOUNTER), facing="right")
    room.place_on_right_wall_center(scene.AddAsset("a glass-top jewelry display counter", asset_id=JCOUNTER), facing="left")
    room.place_on_center(ped)
    room.add_lighting("a flat round LED flush mount ceiling light", density=0.12)

scene.export("verify_jewelry.blend")
