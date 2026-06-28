"""
Wine cellar — "Tasting Cellar". A moody stone room.
Phase 1: wine racks lined along the walls.
Phase 2: a central tasting table ringed with chairs (AroundGroup, slight jitter); warm light.
Phase 3: a stack of oak barrels in a corner, a small high window, an arched door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("WineCellar", seed=23)

with scene.AroundGroup(sparsity=0.3, jitter=0.35) as tasting:
    table = scene.AddAsset("a round wooden wine tasting table")
    tasting.set_anchor(table)
    tasting.place_circle(4 * scene.AddAsset("a wooden tasting stool"))
    tasting.place_on_top(scene.AddAsset("a wine bottle and glasses"))
    tasting.add_lighting("a warm wrought-iron pendant light", density=0)

with scene.StackGroup() as barrels:
    barrels.set_anchor(scene.AddAsset("an oak wine barrel"))
    barrels.place_stack(2 * scene.AddAsset("an oak wine barrel"))

with scene.RoomGroup(modulate_scale=0.95, randomness=0.1) as room:
    room.place_walls(floor_texture="aged stone floor",
                     ceiling_texture="brick arched ceiling", wall_texture="rustic stone")
    room.place_on_center(tasting, facing="front")
    room.place_on_back_left_corner(barrels)
    room.place_on_left_wall_center(scene.AddAsset("a tall wooden wine rack full of bottles"))
    room.place_on_right_wall_center(scene.AddAsset("a tall wooden wine rack full of bottles"))
    room.place_on_back_wall_center(scene.AddAsset("a wooden wine rack full of bottles"))
    room.place_window_standard("front_wall", position="center")
    room.place_door("front_wall", position="right")

scene.export("wine_cellar.blend")
