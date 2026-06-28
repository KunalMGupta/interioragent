"""
Meeting room — "Daylit Boardroom". Built coarse-to-fine.
Phase 1: a central boardroom table ringed by office chairs (AroundGroup, jittered
         so the seating reads as lived-in rather than CAD-perfect).
Phase 2: a credenza against the back wall + a styled centerpiece on the table.
Phase 3: wall display on the front (presentation) wall, daylight window + blinds,
         entry door, and a ceiling light over the table.
Showcases the new realism controls: AroundGroup(jitter=...) and RoomGroup(randomness=...).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("MeetingRoom", seed=11)

# --- central table + ringed chairs (rectilinear: 4 each long side, 1 each end) ---
with scene.AroundGroup(sparsity=0.2, jitter=0.4) as boardroom:
    table = scene.AddAsset("a long rectangular wooden conference table")
    boardroom.set_anchor(table)
    long1 = 4 * scene.AddAsset("a black ergonomic office chair")
    long2 = 4 * scene.AddAsset("a black ergonomic office chair")
    ends = 2 * scene.AddAsset("a black ergonomic office chair")
    boardroom.place_rectilinear(longer_side1=long1, longer_side2=long2,
                                shorter_side1=[ends[0]], shorter_side2=[ends[1]])
    # a tidy centerpiece + the room's main light over the table
    boardroom.place_on_top(scene.AddAsset("a low floral centerpiece with a water carafe"))
    boardroom.add_lighting("a long linear LED ceiling pendant", density=0)

# --- room shell ---
with scene.RoomGroup(randomness=0.3) as room:
    room.place_walls(
        floor_texture="grey commercial carpet tiles",
        ceiling_texture="white acoustic ceiling",
        wall_texture="soft grey",
    )
    room.place_on_center(boardroom, facing="front")

    credenza = scene.AddAsset("a low wooden office credenza cabinet")
    room.place_on_back_wall_center(credenza)

    # Phase 3: presentation display on the front wall; framed art on the right wall
    display = scene.AddAsset("a large wall-mounted flat screen display", width=2.2)
    room.place_on_wall_front_center(display)
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract print"))

    # daylight + access
    room.place_window_floor_to_ceiling("left_wall", curtain="light grey roller blinds")
    room.place_door("back_wall", position="right")

scene.export("meeting_room.blend")
