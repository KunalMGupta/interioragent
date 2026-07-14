"""
Music studio — "Recording Room".
Phase 1: a mixing desk anchor with a studio chair, carrying the room lighting.
Phase 2: a drum kit and a keyboard station around the room.
Phase 3: studio monitor speakers on stands, acoustic panels on the walls, a small window, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("MusicStudio", seed=16)

with scene.RelativeGroup() as desk_group:
    mixer = scene.AddAsset("a studio audio mixing desk console")
    chair = scene.AddAsset("a studio rolling chair")
    desk_group.place_desk_chair(mixer, chair)
    # studio monitor speakers flanking the console
    monitors = 2 * scene.AddAsset("a studio monitor speaker on a stand")
    desk_group.place_on_left_further(monitors[0])
    desk_group.place_on_right_further(monitors[1])
    desk_group.add_lighting("warm recessed studio ceiling lights", density=0)

with scene.RoomGroup(randomness=0.2) as room:
    room.place_walls(floor_texture="dark engineered wood",
                     ceiling_texture="charcoal acoustic ceiling", wall_texture="dark grey acoustic foam")
    room.place_on_back(desk_group, facing="front")
    room.place_on_front_right(scene.AddAsset("a five-piece acoustic drum kit"), facing="left")
    room.place_on_left_wall_center(scene.AddAsset("a digital piano keyboard on a stand"))
    room.place_on_wall_back_left(scene.AddAsset("a framed gold record award"))
    room.place_window_picture("right_wall", curtain="heavy sound curtain")
    room.place_door("front_wall", position="right")

scene.export("music_studio.blend")
