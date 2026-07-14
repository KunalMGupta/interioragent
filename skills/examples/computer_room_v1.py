"""Computer room — "Front-Facing Modular Computer Lab" (planner target tmp/cr_run/plan/plan.png).

Planner target: rows of white workstation desks + black caster chairs facing a front
instructional wall (large display + whiteboard); a server rack + open equipment shelving anchoring
the back wall; cool blue-grey anti-static flooring, brushed metal accents; a window with blinds;
bright diffuse ceiling lighting. (The plan's teal privacy screens have no dataset match and were
deliberately dropped — see computer_room.md, "Asset gaps".)

Layout — REPEATED-UNIT GRID + a focal TEACHING wall (the same bones as classroom/laboratory):
- CENTRE     : the 8-station grid (2 rows x 4 cols, aisles between). The room IS the grid; it gets
               the floor, and every wall is arranged around what the seated operators can see.
- FRONT wall : the instructional focal wall — the wall the whole grid looks AT. Display center,
               whiteboard left, door right: three slots, no collision. NB the grid is faced toward
               "back_wall" to point the operators HERE (see the facing note below).
- BACK wall  : the equipment end — server rack left, open equipment shelving right, clock center.
               Utility kit belongs BEHIND the class, out of the display's sightline.
- LEFT wall  : the window (floor-to-ceiling, blinds). The only wall carrying no furniture, so it
               stays the daylight source.
- RIGHT wall : the circuit-board print. The last long wall; a lab with two blank long walls reads
               like a corridor, so it gets the one decor slot.

Identity comes from the REPEATED UNIT, not from any hero: eight identical desks, each carrying an
identical computer, massed into a grid. A computer lab is a classroom with a computer per desk —
swap the on-desk product and the same program is a classroom or a wet lab.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/computer_room_v1.py --phase 1` builds
only the floor layout — the desk grid, the chairs, the back-wall equipment, walls + door (~1-2 min);
phase 2 seats the computers + desk accessories (the place_on_top tournament); phase 3 adds the
front-wall display/whiteboard, the wall decor, the window and the ceiling lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("ComputerRoom", seed=11)

# --- pinned assets (audited from `workbench.py browse`) ---
DESK = "hssd/5d17aa915ff1256757bfca9353609ade8f21e6ea"   # minimalist white FLAT-TOP desk. "computer
                                                         # desk" retrieved a white marble CONSOLE
                                                         # table; a flat ~0.75 m top is also what
                                                         # place_on_top needs to seat the computer on
                                                         # the writing surface, not on a hutch.
RACK = "custom/9f2a77c71313fa1f84c233717e70ca8371383174" # ingested real server rack
                                                         # (server_racking_system.glb, 0.8 m wide,
                                                         # floor-standing, rack-mounted units + status
                                                         # LEDs). The base dataset has NO true server
                                                         # rack (best matches ~0.48, generic industrial
                                                         # cabinets), so we ingested one and pin it.

scene.prefetch_assets([
    "a minimalist white computer desk with a flat top",
    "a black ergonomic office task chair on casters",
    "a tall black network server equipment rack",
    "a tall metal open storage shelf with equipment bins",
])

# --- one workstation (reusable WorkstationGroup), then duplicate (build ONCE, N * unit) ---
# WorkstationGroup handles the whole motif: operator chair tucked in front facing the desk, the
# computer seated on the real desktop surface (place_on_top) and turned to face the operator, and
# a few accessories — so we don't hand-roll place_desk_chair / face() here.
# The desktop items are the PHASE-2 layer: they route through place_on_top (one VLM sizing
# tournament), and the gate sits INSIDE the `with` block — gated outside it, the ops would never
# be recorded and the computers would simply be GONE.
with scene.WorkstationGroup() as ws:
    ws.set_anchor(scene.AddAsset("a minimalist white computer desk with a flat top", asset_id=DESK, width=1.2))
    ws.place_chair(scene.AddAsset("a black ergonomic office task chair on casters"))
    if PHASE >= 2:
        ws.place_computer(scene.AddAsset("a desktop computer"))           # all-in-one monitor set
        ws.place_accessories([scene.AddAsset("a small pen holder cup with pens")])

# grid of 8 stations, 2 rows of 4, with aisles between them
with scene.GridGroup(sparsity=0.55, randomness=0.3) as stations:
    stations.place_grid(8 * ws, cols=4)

with scene.RoomGroup(modulate_scale=1.0, randomness=0.18) as room:
    # plain color + material words: "cool blue-grey anti-static vinyl flooring" embedded to a WOOD
    # texture (brown floor); texture strings are matched against a fixed library, so drop the jargon.
    room.place_walls(floor_texture="smooth cool grey concrete floor",
                     ceiling_texture="white acoustic drop ceiling",
                     wall_texture="light grey painted wall")
    # desk grid centred; operators face the front (teaching) wall. NB: WorkstationGroup's operator
    # side is +Z (opposite the place_desk_chair convention), so we face the grid toward "back_wall"
    # to point the seated users AT the front display — verified in the interior renders.
    room.place_on_center(stations, facing="front")
    room.face(stations, toward="back_wall")
    # back (short) wall = the equipment end: server rack + open storage shelving
    room.place_on_back_wall_left(scene.AddAsset("a tall black network server equipment rack", asset_id=RACK))
    room.place_on_back_wall_right(scene.AddAsset("a tall metal open storage shelf with equipment bins"))
    # door in PHASE 1: its auto clearance shapes the floor solve, so deferring it would change the
    # layout you validated. It shares the front wall with the display + whiteboard (right slot).
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # front (short) wall = the instructional focal wall: large display + whiteboard
        room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted flat screen display monitor", width=1.8))
        room.place_on_wall_front_left(scene.AddAsset("a large wall-mounted whiteboard", width=1.6))
        # wall decor: a clock over the equipment end, a computing-themed print on the open right wall
        room.place_on_wall_back_center(scene.AddAsset("a round office wall clock"))
        room.place_on_wall_right_center(scene.AddAsset("a framed wall art print of a colorful computer circuit board", width=1.0))
        # window with blinds on a long side wall
        room.place_window_floor_to_ceiling("left_wall", curtain="grey window blinds")
        # bright diffuse ceiling lighting
        room.add_lighting("a row of bright linear LED ceiling panel lights", density=0.03)

scene.export("computer_room_v1.blend")
