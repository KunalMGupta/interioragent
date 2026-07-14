"""
Children's room — "Playful Kids Bedroom".
Phase 1: a single bed anchor with a soft play rug; ceiling light.
Phase 2: toy storage and a low bookshelf against walls; a pile of toy bins.
Phase 3: wall art, window + cheerful curtains, door.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ChildrenRoom", seed=3)

with scene.RelativeGroup() as bed_group:
    bed = scene.AddAsset("a small kids single bed with a colorful duvet")
    bed_group.set_anchor(bed)
    bed_group.place_rug("a colorful round play rug", size=0.8)
    bed_group.add_lighting("a fun pendant ceiling light", density=0)

with scene.PileGroup() as toys:
    toys.set_anchor(scene.AddAsset("a small kids play mat"))
    toys.place_pile(5 * scene.AddAsset("a colorful toy storage bin"), spread=0.8)

with scene.RoomGroup(randomness=0.25) as room:
    room.place_walls(floor_texture="light maple wood",
                     ceiling_texture="white", wall_texture="pale sky blue")
    room.place_on_center(bed_group, facing="front")
    room.place_on_front_right(toys, facing="front")
    room.place_on_back_wall_left(scene.AddAsset("a low kids toy storage shelf"))
    room.place_on_right_wall_center(scene.AddAsset("a low kids bookshelf with picture books"))
    room.place_on_wall_back_center(scene.AddAsset("a framed cartoon animal print"))
    room.place_window_picture("left_wall", curtain="bright patterned curtains")
    room.place_door("front_wall", position="left")

scene.export("children_room.blend")
