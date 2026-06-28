"""
Greenhouse — "Glass Conservatory".
Phase 1: potting/plant benches in rows (GridGroup) covered with potted plants.
Phase 2: a central bench piled with potted plants carrying the light; a pile of pots.
Phase 3: tall plants in corners, glass walls (windows on multiple sides), a door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Greenhouse", seed=52)

with scene.GridGroup(sparsity=0.5) as benches:
    benches.place_grid(4 * scene.AddAsset("a greenhouse plant bench full of potted seedlings"), cols=2)

with scene.PileGroup() as pots:
    pots.set_anchor(scene.AddAsset("a potting soil bench"))
    pots.place_pile(6 * scene.AddAsset("a terracotta plant pot"), spread=0.7)
    pots.add_lighting("bright daylight ceiling grow lights", density=0)

with scene.RoomGroup(modulate_scale=1.1, randomness=0.25) as room:
    room.place_walls(floor_texture="gravel and stone path floor",
                     ceiling_texture="glass panels", wall_texture="white-framed glass")
    room.place_on_center(benches, facing="front")
    room.place_on_front_left(pots, facing="front")
    room.place_on_back_left_corner(scene.AddAsset("a tall tropical potted plant"))
    room.place_on_back_right_corner(scene.AddAsset("a tall tropical potted plant"))
    room.place_window_floor_to_ceiling("left_wall", curtain=None)
    room.place_window_floor_to_ceiling("right_wall", curtain=None)
    room.place_door("front_wall", position="center")

scene.export("greenhouse.blend")
