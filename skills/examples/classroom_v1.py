"""
Classroom v1 — "Front-Focused Flexible Classroom Core" (planner target tmp/plan_a_classroom/plan.png).
Supersedes the thin pre-workflow scenes/classroom.py.

Rows of light-wood student desks with orange stacking chairs face a front teaching wall
(dark chalkboard + wall-mounted display); a wooden teacher desk sits front-left facing the
class; white perimeter storage + a stocked bookshelf anchor the back wall; a window with
blinds on the left wall; dark grey carpet, white walls, flush LED ceiling lighting.

Recipe: the computer_room/classroom bones — ONE desk+chair unit via place_desk_chair
(correct pose by construction), duplicated with 6 * unit into a GridGroup (2 cols x 3 rows),
then room.face(grid, toward="front_wall") to aim the class at the board (place_desk_chair
grids face the FRONT wall — the opposite of a WorkstationGroup grid).

Asset notes (audited via inspect/browse, gate 3): teal acoustic panels have no dataset
match (same gap as computer_room) — dropped; wall interest carried by the framed world map
+ posters. Orange chair pinned because its color carries the palette. WALL_TV reused from
the proven meeting_room pin (1.2 m native -> pre-scaled before wall placement).

Phase-gated (IDSDL/phases.py): --phase 1 = floor layout only (~1 min check);
phase 2 adds surface dressing; phase 3 adds walls/window/lighting/mood.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Classroom", seed=21)

# --- pinned assets (previews eyeballed at gate 3) ---
STUDENT_DESK  = "hssd/c67c6e75945f75cbc530feb9568548802a1648a6"  # light-wood flat-top desk, slim metal legs
STUDENT_CHAIR = "hssd/d96243bc179651b7469f0e0a4ab6fa72e261bbf4"  # orange plastic stacking chair, metal legs
TEACHER_DESK  = "hssd/99e2a3e301a597ed93bf3dc57b36fec3b37b8846"  # classic wooden desk w/ drawers, flat top
CHALKBOARD    = "hssd/3a39fbaa3a1f5408939395df2f31a92585de0612"  # black chalkboard w/ chalk tray
WALL_TV       = "hssd/576f0a57271ccc62554b2603a48047854254119d"  # large flat-screen display (1.2 m native)
STORAGE       = "hssd/56366c90a4519ed83719b30cd4757008f0e558fb"  # white sideboard, dark wood top
BOOKSHELF     = "hssd/2db50fb1f8120974d6157ae9aff704a4fc9d181f"  # light-wood bookshelf filled with books
GLOBE         = "hssd/55c813d9a522cc5e52176d01e75ea53d260c9003"  # vintage world globe on a stand
WORLD_MAP     = "hssd/b22e386790fbc049bfc554f8eeab943ea228587f"  # framed two-hemisphere world map print

scene.prefetch_assets([
    "a simple student school desk with a light wood top and metal legs",
    "an orange plastic school chair with metal legs",
    "a classic wooden teacher desk with drawers",
    "a black office task chair",
    "a large dark chalkboard with a chalk tray",
    "a large wall-mounted flat screen display",
    "a white sideboard storage cabinet with a dark wood top",
    "a tall wooden open bookshelf filled with books",
    "a decorative vintage world globe on a stand",
    "a framed map of the world with a dark wooden frame",
    "a round office wall clock",
    "a colorful educational poster print",
    "a leafy potted plant in a ceramic planter",
    "a stack of books",
    "a small pen holder cup with pens",
    "an open notebook with a pen",
    "a flat rectangular LED flush mount ceiling light",
])

# --- ONE student unit (desk + tucked chair), then duplicate: build ONCE, 6 * unit ---
with scene.RelativeGroup() as student_unit:
    desk = scene.AddAsset("a simple student school desk with a light wood top and metal legs",
                          asset_id=STUDENT_DESK, width=1.1)
    chair = scene.AddAsset("an orange plastic school chair with metal legs",
                           asset_id=STUDENT_CHAIR)
    student_unit.place_desk_chair(desk, chair)
    if PHASE >= 2:
        student_unit.place_on_top([scene.AddAsset("an open notebook with a pen")])

# 6 stations, 2 columns x 3 rows, with aisles between them
with scene.GridGroup(sparsity=0.5, randomness=0.25) as desks:
    desks.place_grid(6 * student_unit, cols=2)

# --- teacher zone: desk facing the class, dressed with the identity props ---
with scene.RelativeGroup() as teacher_zone:
    tdesk = scene.AddAsset("a classic wooden teacher desk with drawers",
                           asset_id=TEACHER_DESK, width=1.5)
    tchair = scene.AddAsset("a black office task chair")
    teacher_zone.place_desk_chair(tdesk, tchair)
    if PHASE >= 2:
        teacher_zone.place_on_top([
            scene.AddAsset("a decorative vintage world globe on a stand", asset_id=GLOBE),
            scene.AddAsset("a stack of books"),
            scene.AddAsset("a small pen holder cup with pens"),
        ])

# --- back-wall perimeter storage, dressed so it reads as a classroom, not a showroom ---
with scene.RelativeGroup() as storage_group:
    storage_group.set_anchor(
        scene.AddAsset("a white sideboard storage cabinet with a dark wood top",
                       asset_id=STORAGE, width=1.8))
    if PHASE >= 2:
        storage_group.place_on_top([
            scene.AddAsset("a leafy potted plant in a ceramic planter"),
            scene.AddAsset("a stack of books"),
        ])

# --- the room ------------------------------------------------------------------
# modulate_scale=0.85: RoomProportions walked 0.96 -> 0.92 -> 0.85 across the phases;
# held per render-wins-early, applied once in the final phase (the floor read spacious)
with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:
    # plain color+material words — "with one teal accent wall" embedded to a green
    # tile texture on ALL walls, and "plain white ceiling" rendered BLACK
    # (computer_room texture lesson); teal accent dropped
    room.place_walls(floor_texture="dark grey carpet",
                     ceiling_texture="smooth white plaster",
                     wall_texture="smooth white painted plaster wall")

    # seating field: desk grid centred, class facing the front teaching wall
    # (place_desk_chair grid -> face the FRONT wall; the opposite of a WorkstationGroup grid)
    room.place_on_center(desks, facing="front")
    room.face(desks, toward="front_wall")

    # teacher front-left (clear of the door on front-right), facing the class
    room.place_on_front_left(teacher_zone, facing="back")
    room.face(teacher_zone, toward="back_wall")

    # back wall = storage zone: sideboard center + stocked bookshelf left
    room.place_on_back_wall_center(storage_group)
    room.place_on_back_wall_left(
        scene.AddAsset("a tall wooden open bookshelf filled with books", asset_id=BOOKSHELF))

    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # front teaching wall: chalkboard center + display left (pre-scaled BEFORE hanging)
        room.place_on_wall_front_center(
            scene.AddAsset("a large dark chalkboard with a chalk tray",
                           asset_id=CHALKBOARD, width=2.4))
        room.place_on_wall_front_left(
            scene.AddAsset("a large wall-mounted flat screen display",
                           asset_id=WALL_TV, modulate_scale=1.4))
        # decor: clock over the storage run (low, not a tall spine), map + poster on the right wall
        room.place_on_wall_back_center(scene.AddAsset("a round office wall clock"))
        room.place_on_wall_right_center(
            scene.AddAsset("a framed map of the world with a dark wooden frame",
                           asset_id=WORLD_MAP))
        room.place_on_wall_right_left(scene.AddAsset("a colorful educational poster print"))
        room.place_on_back_right_corner(
            scene.AddAsset("a leafy potted plant in a ceramic planter"), facing="front")
        # window with blinds on the left wall (STANDARD pane — full glazing = black void)
        room.place_window_standard("left_wall", position="center",
                                   curtain="light grey roller blinds")
        # flush fixture, low density (medium room; count scales with floor area)
        room.add_lighting("a flat rectangular LED flush mount ceiling light", density=0.02)

scene.export("classroom_v1.blend")
