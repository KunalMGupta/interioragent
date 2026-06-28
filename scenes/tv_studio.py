"""
TV studio — "News Set".
Phase 1: a news anchor desk with chairs facing the cameras (RelativeGroup), studio lighting.
Phase 2: TV cameras on tripods arranged in an arc facing the desk (AroundGroup).
Phase 3: a backdrop screen on the wall, monitors, dark studio finishes, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("TvStudio", seed=39)

with scene.RelativeGroup() as desk_group:
    desk = scene.AddAsset("a curved tv news anchor desk")
    desk_group.set_anchor(desk)
    chairs = 2 * scene.AddAsset("a tv presenter chair")
    desk_group.place_on_back_left(chairs[0])
    desk_group.place_on_back_right(chairs[1])
    desk_group.add_lighting("bright studio softbox ceiling lights", density=0)

with scene.AroundGroup(sparsity=0.6, jitter=0.3) as cameras:
    pivot = scene.AddAsset("a small studio floor marker")
    cameras.set_anchor(pivot)
    cameras.place_arc(3 * scene.AddAsset("a professional tv camera on a tripod"))

with scene.RoomGroup(modulate_scale=1.1, randomness=0.2) as room:
    room.place_walls(floor_texture="black studio floor",
                     ceiling_texture="black with rigging", wall_texture="dark grey")
    room.place_on_back(desk_group, facing="front")
    room.face(desk_group, toward="front_wall")
    room.place_on_front(cameras, facing="back")
    room.place_on_wall_back_center(scene.AddAsset("a large studio backdrop video screen", width=2.5))
    room.place_on_wall_left_center(scene.AddAsset("a wall of broadcast monitors"))
    room.place_door("front_wall", position="right")

scene.export("tv_studio.blend")
