"""
Music recording studio — "Moody Pro Studio: Central Console Anchor with Acoustic Architecture"
(planner headline). Built via the guided 9-gate flow: plan -> retrieve -> asset audit -> phased build.

Layout = the two-zone control/live split from the procedural signature:
  - FRONT/CENTER = the CONTROL zone hero: a professional mixer on its stand, flanked by a pair
    of nearfield monitor speakers on stands, the engineer's chair at the sweet spot behind it
    (chair faces the mixer/front wall), all grounded on a dark oriental rug.
  - BACK        = the LIVE zone sub-hero: the full drum kit on its own rug, a vocal mic stand
    in front of it.
  - LEFT        = keyboard station (digital keyboard on a stand, faces the room).
  - RIGHT wall  = the guitar line: two guitars on floor stands + a guitar-with-amp set.
  - FRONT wall  = a tall black gear-rack cabinet (left) + the entry door (right).
  - Walls carry the acoustic architecture (phase 3): black geometric panels massed on the red
    back wall, upholstered grid panels at the side-wall first-reflection points.

Asset audit notes (gate 3): no true mixing-console DESK in the dataset — the professional
mixer on a black stand (hssd/6990fec2, candidate #1) beats the VLM's white DJ table for the
dark palette. No real 19" rack -> tall black shelf cabinet stand-in. No acoustic foam ->
upholstered grid panel + black geometric panel as treatment (both thin, wall-hang safe).
The amp comes bundled with one guitar mesh (the SET is desirable here, not a trap).

Lighting: warm moody = ONE flush fixture layer at density 0.02 (small-room lesson: 0.05 is
a starfield) + a small standard window with dark curtains on the left wall (modest void).

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor
layout (~1 min) to verify room size / overlaps before surface dressing and walls/mood.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("MusicStudio", seed=42)

MIXER      = "hssd/6990fec2d8cf4336184047cd38168e81876a94f4"   # professional audio mixer on a black stand
MONITOR    = "hssd/5f1030c8e1c04c7a9a4c93ea7c3b8804eb6b174a"   # black monitor speaker on a stand
MIC_STAND  = "hssd/7b2ed578ddbdebd16402325998289f48bc91ed06"   # black microphone on a silver stand
DRUMS      = "hssd/eca42afb8979029cd267728a72ac1788c3e0a903"   # full classic drum kit, green shells + cymbals
KEYBOARD   = "hssd/f51e066d210a34e439921cec1d7b52a339fc298c"   # black digital keyboard on a stand
GUITAR     = "future/b4c95c67-9891-4379-b339-ecf719891272"     # white electric guitar on a metal floor stand
GUITAR_AMP = "future/0f058977-718c-41fd-a8b8-2a555b2681ec"     # white electric guitar + black amplifier set
GEAR_RACK  = "future/9f6fd95f-f16b-409b-a34b-dd7668545e63"     # tall black shelf cabinet (the "rack")
PANEL_GRID = "future/540e8add-3553-485e-bee6-bb56a5b86aac"     # upholstered grid-pattern acoustic panel
PANEL_BLK  = "future/2ab78653-2dc7-49ad-b1fd-524b494347b6"     # black geometric wall panel
STEREO     = "future/4c6888e5-5e3d-410b-8401-f5264243871d"     # stereo system w/ dual speakers (rack gear)

scene.prefetch_assets([
    "a professional audio mixing console on a black stand",
    "a black studio monitor loudspeaker on a stand",
    "a black microphone on a silver stand",
    "a drum kit with bass drum cymbals and snare",
    "an electronic keyboard synthesizer on a stand",
    "an electric guitar on a floor stand",
    "an electric guitar with a black amplifier",
    "a tall black studio equipment rack cabinet",
    "a black ergonomic studio office chair",
    "a dark red oriental patterned area rug",
    "a small dark grey area rug",
    "an upholstered grid pattern acoustic wall panel",
    "a black geometric acoustic wall panel",
    "a framed black and white concert photograph print",
    "a flat round black LED flush mount ceiling light",
    "a modern black stereo system with dual speakers",
    "a warm brass floor lamp with a fabric shade",
])

# --- CONTROL zone: mixer + flanking nearfield monitors + engineer chair (one unit) ---
mixer = scene.AddAsset("a professional audio mixing console on a black stand",
                       asset_id=MIXER, width=1.6)
with scene.RelativeGroup() as console:
    console.set_anchor(mixer)
    mon_l = scene.AddAsset("a black studio monitor loudspeaker on a stand", asset_id=MONITOR)
    mon_r = scene.AddAsset("a black studio monitor loudspeaker on a stand", asset_id=MONITOR)
    chair = scene.AddAsset("a black ergonomic studio office chair")
    console.place_on_left(mon_l)
    console.place_on_right(mon_r)
    console.place_on_front(chair)          # sweet-spot seat on the mixer's control side
    console.face(chair, toward=mixer)      # engineer faces the console
    console.face(mon_l, toward=chair)      # nearfields angle in at the listener
    console.face(mon_r, toward=chair)
    if PHASE >= 2:
        console.place_rug("a dark red oriental patterned area rug", size=1.4)

# --- LIVE zone: drum kit on its rug, vocal mic stand fronting it ---
drums = scene.AddAsset("a drum kit with bass drum cymbals and snare", asset_id=DRUMS)
with scene.RelativeGroup() as live_zone:
    live_zone.set_anchor(drums)
    live_zone.place_on_front_left(
        scene.AddAsset("a black microphone on a silver stand", asset_id=MIC_STAND))
    live_zone.place_on_right(
        scene.AddAsset("a black microphone on a silver stand", asset_id=MIC_STAND))
    if PHASE >= 2:
        live_zone.place_rug("a small dark grey area rug", size=1.3)

# --- guitar line: two guitars on stands + the guitar-with-amp set, one straight row ---
guitars = 2 * scene.AddAsset("an electric guitar on a floor stand", asset_id=GUITAR)
amp_set = scene.AddAsset("an electric guitar with a black amplifier", asset_id=GUITAR_AMP)
with scene.GridGroup(sparsity=0.35, randomness=0.15) as guitar_row:
    guitar_row.place_row([guitars[0], amp_set, guitars[1]])

keyboard = scene.AddAsset("an electronic keyboard synthesizer on a stand", asset_id=KEYBOARD)

# gear rack, stocked (an empty fixture names the fixture, not the studio — jewelry_shop lesson)
with scene.RelativeGroup() as rack_station:
    rack_station.set_anchor(scene.AddAsset("a tall black studio equipment rack cabinet",
                                           asset_id=GEAR_RACK))
    if PHASE >= 2:
        rack_station.place_inside([
            scene.AddAsset("a modern black stereo system with dual speakers", asset_id=STEREO),
        ])

# --- the room ---
with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:   # acts on the persistent 0.85/0.8 room-rescale vote (final phase)
    room.place_walls(floor_texture="warm medium oak wood plank floor",
                     ceiling_texture="dark wood slatted ceiling",
                     wall_texture="dark charcoal grey with one deep red accent wall")

    # control zone hero near the front wall, console pointing into the room,
    # engineer between console and room center facing the front wall
    room.place_on_front(console, facing="back")

    # live zone: drums anchor the back, facing the console down the centerline
    room.place_on_back(live_zone, facing="front")

    # keyboard station on the left, playing into the room
    room.place_on_left(keyboard, facing="right")

    # guitar line against the right wall (default facing = into the room)
    room.place_on_right_wall_center(guitar_row)

    # gear rack on the front wall beside the console zone; entry door on the right
    room.place_on_front_wall_left(rack_station)
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # acoustic architecture: black panel grid massed on the (red) back wall,
        # upholstered grid panels at the side-wall first-reflection points
        room.place_on_wall_freeform("back_wall", [
            scene.AddAsset("a black geometric acoustic wall panel", asset_id=PANEL_BLK),
            scene.AddAsset("a black geometric acoustic wall panel", asset_id=PANEL_BLK),
            scene.AddAsset("a black geometric acoustic wall panel", asset_id=PANEL_BLK),
        ])
        room.place_on_wall_left_center(
            scene.AddAsset("an upholstered grid pattern acoustic wall panel", asset_id=PANEL_GRID))
        room.place_on_wall_right_center(
            scene.AddAsset("an upholstered grid pattern acoustic wall panel", asset_id=PANEL_GRID))
        room.place_on_wall_front_center(
            scene.AddAsset("a framed black and white concert photograph print"))

        # a small punched window with dark curtains (modest void, reads as evening)
        room.place_window_standard("left_wall", position="left",
                                   curtain="dark charcoal blackout curtains")

        # warm moody light: one calm flush layer (small room -> low density) + a warm
        # brass floor lamp in the back corner as the decorative warm layer
        room.add_lighting("a flat round black LED flush mount ceiling light", density=0.01)  # 0.02 -> 12 fixtures = starfield on 38 m^2
        room.place_on_back_right_corner(
            scene.AddAsset("a warm brass floor lamp with a fabric shade"), facing="front")

scene.export("music_studio.blend")
