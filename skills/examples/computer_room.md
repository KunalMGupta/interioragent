# Computer room — example

Status: built as `scenes/computer_room.py`. [`computer_room_v1.py`](computer_room_v1.py) is that program **phase-gated** (2026-07-13): `lint_program`-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record) — fully clean: `no rescale / no rotation / no wall overlap`.

Status: **built & converged** (`scenes/computer_room.py`, seed=11). Front-facing modular
computer lab, built coarse-to-fine through the workbench. Final compile: rotation clean,
no wall overlap, room proportions converged (`no rescale`/`no rotation` at every level).

## Prompt this covers
- "a modern computer lab / workstation room: rows of desks each with a desktop computer and
  monitor, ergonomic office task chairs, a large wall-mounted whiteboard, a server rack, open
  storage shelving, cool blue-grey anti-static flooring, bright ceiling lighting, a window with
  blinds."

## Plan summary (from the planner)
"Front-Facing Modular Computer Lab Grid": modular desk bays facing a front instructional wall
(large display + low whiteboard); teal privacy screens between stations; server rack anchoring
the back wall with open equipment shelving; cool blue-grey anti-static floor, brushed metal +
teal accents; bright diffuse ceiling lighting; window with blinds. Retrieved skills were all
strong "Classroom computer-lab" frames (0.69–0.77) — the library covers this well.

## Working program (coarse-to-fine)

```python
from IDSDL.scene import SceneProgRoom
scene = SceneProgRoom("ComputerRoom", seed=11)

_DESK = "hssd/5d17aa915ff1256757bfca9353609ade8f21e6ea"   # minimalist white flat-top desk
_RACK = "future/8647d988-aee5-43dc-8581-5f1a88ca548e"     # server-rack stand-in (no true rack in dataset)

# one station = a reusable WorkstationGroup; build ONCE, then `8 * ws` (ONE place_on_top tournament)
with scene.WorkstationGroup() as ws:
    ws.set_anchor(scene.AddAsset("a minimalist white computer desk with a flat top", asset_id=_DESK, width=1.2))
    ws.place_chair(scene.AddAsset("a black ergonomic office task chair on casters"))
    ws.place_computer(scene.AddAsset("a desktop computer"))            # all-in-one monitor set
    ws.place_accessories([scene.AddAsset("a small pen holder cup with pens")])

with scene.GridGroup(sparsity=0.55, randomness=0.3) as stations:
    stations.place_grid(8 * ws, cols=4)

with scene.RoomGroup(modulate_scale=1.0, randomness=0.18) as room:
    room.place_walls(floor_texture="smooth cool grey concrete floor",
                     ceiling_texture="white acoustic drop ceiling",
                     wall_texture="light grey painted wall")
    room.place_on_center(stations, facing="front")
    room.face(stations, toward="back_wall")   # WorkstationGroup operator side is +Z → face the
                                              # OPPOSITE wall to point seated users at the front display
    room.place_on_back_wall_left(scene.AddAsset("a tall black network server equipment rack", asset_id=_RACK))
    room.place_on_back_wall_right(scene.AddAsset("a tall metal open storage shelf with equipment bins"))
    room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted flat screen display monitor", width=1.8))
    room.place_on_wall_front_left(scene.AddAsset("a large wall-mounted whiteboard", width=1.6))
    room.place_door("front_wall", position="right")
    room.place_on_wall_back_center(scene.AddAsset("a round office wall clock"))
    room.place_on_wall_right_center(scene.AddAsset("a framed wall art print of a colorful computer circuit board", width=1.0))
    room.place_window_floor_to_ceiling("left_wall", curtain="grey window blinds")
    room.add_lighting("a row of bright linear LED ceiling panel lights", density=0.03)

scene.export("computer_room.blend")
```

## What worked / gotchas
- **Fixed a real `place_on_top` sinking bug (slab-top desks).** The all-in-one computers seated
  ~2 cm *below* the desktop. Root cause was NOT the DSL seating math (correct) but the surface
  picker in `tools/planar_regions.py`: this desk's thin top slab has its **underside modelled with
  upward-facing normals**, so `detect_horizontal_regions` reported two near-coplanar full-size
  surfaces (true top at y≈0.75 and a spurious one 2 cm below). `top_surfaces()` kept *both* (within
  its 2 cm `band`) but left each at its **own y**, so tournament tiles on the lower face seated 2 cm
  low — invisible on a short pen cup, a visible sink on a tall monitor. Fix: `top_surfaces()` now
  **snaps every near-coplanar region to the top plane** (`r["y"] = top_y`). Verified the computer
  bottom moved 0.7303 → 0.7500 (flush). General place_on_top fix, not per-scene. Diagnosis method:
  a tiny script printing `desk.get_aabb()[1,1]` vs `computer.get_aabb()[0,1]` isolates the gap fast
  (no full render). **Do not "fix" a sink by nudging the item's y — find the surface bug.** [[smart-placement]]
- **Use the reusable `WorkstationGroup` for the station (`[[workstation-group]]`).** `set_anchor`
  (desk) + `place_chair` + `place_computer` + `place_accessories` — it tucks the operator chair,
  seats the computer on the real desktop via `place_on_top`, turns the screen to face the operator,
  and caps the desktop at 3 items. This is the idiomatic build; don't hand-roll `place_desk_chair` +
  `place_on_top` + `face()` (the v1 way) when a purpose-built group exists. `"a desktop computer"`
  routes to the `DesktopWorkstationRetriever` pool and returns an all-in-one screen set (richer than
  a bare monitor). `vlm_solver=None` on the group means no per-instance render — good for a grid.
- **WorkstationGroup grid facing: face the OPPOSITE wall.** Its operator side is local **+Z**
  (chair in front), the *opposite* of the `place_desk_chair` convention. So `face(stations,
  toward="front_wall")` pointed all 8 operators *away* from the front display; switching to
  `face(stations, toward="back_wall")` aimed them at it. **Always verify seating direction in the
  interior render** — the front-wall view shows whether you see operators' faces (correct) or the
  backs of their screens (flipped). VLM `RotationConstraint` said `no rotation` in *both* the
  right and the flipped orientation — useless for this; the render is the only arbiter.
- **Build the station ONCE, then `8 * ws`.** The computer's `place_on_top` runs one VLM tournament
  on the single unit; `N *` deep-copies realized transforms (ops are cleared on copy), so all 8 are
  identical and the tournament runs once, not 8×. The design-principles "duplicate a composed unit".
- **Same bones as classroom/office:** a station unit → `GridGroup` rows → face the teaching wall.
  A computer lab is a classroom with a computer per desk. (v1 built it with `place_desk_chair` +
  `place_on_top(monitor)` + `face(monitor, toward=chair)` — that also works and gives a bare black
  monitor; the WorkstationGroup version is richer and more idiomatic.)
- **Texture strings are embedding-matched against a fixed library — phrase for color, not jargon.**
  "cool blue-grey anti-static vinyl flooring" embedded closest to a *wood* texture (brown floor).
  Dropping the jargon to "smooth cool grey concrete floor" hit the grey concrete/vinyl textures.
  When a floor/wall renders the wrong color, simplify to plain color + material words.
- **Room enlarge: DECLINED — shipped `modulate_scale=1.0`** although the VLM asked for 1.2 twice
  (the lab brief wants wide circulation aisles). An earlier draft of this lesson claimed a 1.1 was
  applied in the final phase; the program and its entire git history show 1.0, so the claim was
  session-memory drift — the program is the record. If a rebuild reads cramped, 1.1 is the first
  knob to try.
- **Wall-slot hygiene (front wall):** display center, whiteboard left, door right — three slots,
  no collision. Window (left wall) claims all three of its wall's slots; back wall carries the
  server rack + shelf. WallOverlap stayed clean.

## Asset notes (retrieval)
- **Desk:** "computer desk" retrieval returned a **white marble console table** — pinned a
  minimalist white flat-top desk by id instead (`browse` → pick). Confirms the flat-top rule:
  audit the desk, pin when retrieval drifts to a fancy/stone top.
- **Server rack — was a dataset gap, now INGESTED.** No true server rack existed (best matches
  ~0.48, generic "industrial cabinets"), so we ingested one: `server_racking_system.glb` →
  `custom/9f2a77c71313fa1f84c233717e70ca8371383174` (0.8 m wide, floor-standing, rack-mounted
  units + blue/green status LEDs). Ingested with a manifest overriding `description` (drives the
  retrieval embedding → "a tall black network server equipment rack" now hits it #1), `scale`
  0.8 m, `placement` floor. Pin it as `_RACK`. Worked example of the asset-first ingest loop.
- **Teal privacy screen — no teal asset (deliberately dropped).** The plan's teal desk screens
  have no match (only a grey desktop screen `hssd/dedf56aa…` and a blue-grey freestanding divider
  `hssd/1b99ac87…`); omitted rather than force the wrong color.

## Manual constraints used
- None. The auto door-clearance + grid aisles were enough. Candidate for v2:
  `add_clearance(server_rack, dir="front")` for maintenance access to the back-wall equipment.

## Program

[`computer_room_v1.py`](computer_room_v1.py) — phase 1 the 8-station workstation grid + the ingested server rack, walls and door; phase 2 seats the computers and desk accessories (the place_on_top tournament); phase 3 the wall display, whiteboard, clock, circuit-board print, the floor-to-ceiling window and the LED panels.

`workbench run skills/examples/computer_room_v1.py --phase 1` builds the layout alone in ~1–2 min.
