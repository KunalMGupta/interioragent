"""
Computer room — "Front-Facing Modular Computer Lab" (planner target tmp/cr_run/plan/plan.png).
Rows of white workstation desks + black caster chairs face a front instructional wall
(large display + whiteboard); a server rack + open equipment shelving anchor the back wall;
cool-grey anti-static flooring; a window with blinds; bright diffuse ceiling lighting.

Built coarse-to-fine through the workbench (seed=11); final compile is rotation/overlap/
proportion clean (no rescale, no rotation, no wall overlap).

Phase 1: workstation grid (desk+chair) + back-wall server rack & equipment shelf (floor anchors).
Phase 2: each station is a reusable `WorkstationGroup` (desk anchor + operator chair + a desktop
         computer SET + one desk accessory). Built ONCE — its internal `place_on_top` runs a single
         VLM sizing tournament — then duplicated across the grid with `8 * ws`, so all 8 stations
         are identically laid out (the copy replicates realized transforms, not the op).
Phase 3: front display + whiteboard + door on the focal wall; window/blinds; ceiling lighting.

Asset note: the base dataset has no true server rack (best matches ~0.48, generic industrial
cabinets), so we ingested a real one — `custom/9f2a77c7…` (server_racking_system.glb, 0.8 m
wide, floor-standing, rack-mounted units + status LEDs) — and pin it as _RACK.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ComputerRoom", seed=11)

# --- pinned assets (audited from `workbench.py browse`) ---
_DESK = "hssd/5d17aa915ff1256757bfca9353609ade8f21e6ea"   # minimalist white flat-top desk
_RACK = "custom/9f2a77c71313fa1f84c233717e70ca8371383174" # ingested real server rack (server_racking_system.glb)

# --- one workstation (reusable WorkstationGroup), then duplicate (build ONCE, N * unit) ---
# WorkstationGroup handles the whole motif: operator chair tucked in front facing the desk, the
# computer seated on the real desktop surface (place_on_top) and turned to face the operator, and
# a few accessories — so we don't hand-roll place_desk_chair / face() here.
with scene.WorkstationGroup() as ws:
    ws.set_anchor(scene.AddAsset("a minimalist white computer desk with a flat top", asset_id=_DESK, width=1.2))
    ws.place_chair(scene.AddAsset("a black ergonomic office task chair on casters"))
    ws.place_computer(scene.AddAsset("a desktop computer"))           # all-in-one monitor set
    ws.place_accessories([scene.AddAsset("a small pen holder cup with pens")])

# grid of 8 stations, 2 rows of 4, with aisles between them
with scene.GridGroup(sparsity=0.55, randomness=0.3) as stations:
    stations.place_grid(8 * ws, cols=4)

with scene.RoomGroup(modulate_scale=1.0, randomness=0.18) as room:
    room.place_walls(floor_texture="smooth cool grey concrete floor",
                     ceiling_texture="white acoustic drop ceiling",
                     wall_texture="light grey painted wall")
    # desk grid centred; operators face the front (teaching) wall. NB: WorkstationGroup's operator
    # side is +Z (opposite the place_desk_chair convention), so we face the grid toward "back_wall"
    # to point the seated users AT the front display — verified in the interior renders.
    room.place_on_center(stations, facing="front")
    room.face(stations, toward="back_wall")
    # back (short) wall = the equipment end: server rack + open storage shelving
    room.place_on_back_wall_left(scene.AddAsset("a tall black network server equipment rack", asset_id=_RACK))
    room.place_on_back_wall_right(scene.AddAsset("a tall metal open storage shelf with equipment bins"))
    # front (short) wall = the instructional focal wall: large display + whiteboard, entry door
    room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted flat screen display monitor", width=1.8))
    room.place_on_wall_front_left(scene.AddAsset("a large wall-mounted whiteboard", width=1.6))
    room.place_door("front_wall", position="right")
    # wall decor: a clock over the equipment end, a computing-themed print on the open right wall
    room.place_on_wall_back_center(scene.AddAsset("a round office wall clock"))
    room.place_on_wall_right_center(scene.AddAsset("a framed wall art print of a colorful computer circuit board", width=1.0))
    # window with blinds on a long side wall
    room.place_window_floor_to_ceiling("left_wall", curtain="grey window blinds")
    # bright diffuse ceiling lighting
    room.add_lighting("a row of bright linear LED ceiling panel lights", density=0.03)

scene.export("computer_room.blend")
