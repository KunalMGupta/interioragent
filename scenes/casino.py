"""
Casino — "Gaming Floor".
Phase 1: rows of slot machines (GridGroup) forming the main floor.
Phase 2: a felt card table ringed with chairs (AroundGroup, jittered).
Phase 3: a bar counter against a wall, ornate finishes, neon art, low warm lighting, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Casino", seed=29)

with scene.GridGroup(sparsity=0.5, randomness=0.2) as slots:
    slots.place_grid(6 * scene.AddAsset("a colorful slot machine"), cols=3)

with scene.AroundGroup(sparsity=0.3, jitter=0.5) as card_table:
    table = scene.AddAsset("a green felt blackjack card table")
    card_table.set_anchor(table)
    card_table.place_arc(4 * scene.AddAsset("a padded casino chair"))
    card_table.add_lighting("a low warm pendant light", density=0)

with scene.RelativeGroup() as light_anchor:
    light_anchor.set_anchor(scene.AddAsset("a small casino podium"))
    light_anchor.add_lighting("warm decorative ceiling lights", density=0)

with scene.RoomGroup(modulate_scale=1.15, randomness=0.25) as room:
    room.place_walls(floor_texture="ornate red patterned carpet",
                     ceiling_texture="dark gold", wall_texture="deep burgundy")
    room.place_on_center(slots, facing="front")
    room.place_on_front_right(card_table, facing="front")
    room.place_on_back(light_anchor)
    room.place_on_back_wall_center(scene.AddAsset("a long casino bar counter"))
    room.place_on_wall_left_center(scene.AddAsset("a bright neon casino wall sign"))
    room.place_door("front_wall", position="left")

scene.export("casino.blend")
