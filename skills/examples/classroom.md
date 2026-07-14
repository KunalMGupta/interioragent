# Classroom — worked example

Status: **built & converged** (`scenes/classroom_v1.py`, seed=21, 4 builds: 2× phase-1, 1× phase-2,
2× full). Final compile: `no rotation`, `no wall overlap`, no `[Lint]`/WARNING lines; room size
converged at `modulate_scale=0.85` (the post-apply vote flipped to 1.1 = oscillation across neutral,
declined per converge-don't-chase). Built through the guided 9-gate flow (flow_0712_171017_8858).
Supersedes the thin pre-workflow `scenes/classroom.py` build (this lesson replaced that draft's).

## Prompt this covers
- "a classroom": rows of student desks with chairs all facing a front teaching wall (chalkboard +
  wall display), a teacher desk facing the class, perimeter storage + bookshelf, window with blinds,
  educational wall decor, bright even lighting.

## Plan summary (from the planner)
"Front-Focused Flexible Classroom Core": instruction-driven front zone (chalkboard wall + wall-mounted
monitor), rows of wood-topped desks on metal frames facing front, orange chairs + teal accent panels as
the palette, perimeter storage keeping desk surfaces clean, side window with blinds, dark acoustic
flooring, linear ceiling lights.

## The layout idea: the repeated desk+chair unit, tiled toward a teaching wall
A classroom is the computer_room grid with the workstation swapped for a bare desk+chair unit and the
front wall promoted to the teaching anchor:
- **CENTER = the seating field** — ONE `place_desk_chair` unit (desk + tucked orange chair), built once,
  `6 *` duplicated into a `GridGroup(sparsity=0.5, randomness=0.25)`, 2 cols × 3 rows, then
  `room.face(desks, toward="front_wall")`.
- **FRONT wall = teaching anchor** — black chalkboard (wall-hung, center) + pre-scaled wall display
  (left) + door (right); teacher desk+chair front-LEFT on the floor, faced `toward="back_wall"` so the
  teacher looks at the class.
- **BACK wall = storage zone** — white sideboard (dressed: plant + books) center + stocked bookshelf left,
  wall clock hung above the LOW sideboard run (laundromat art-over-a-low-run rule).
- **RIGHT wall = identity decor** — framed world map center + educational poster left; plant in the
  back-right corner. **LEFT wall = daylight** — `place_window_standard` (never full glazing: black void).

## Step 0 — asset audit (gate 3)
All heroes eyeballed via `inspect`/`browse` before any placement. Pins:
STUDENT_DESK `hssd/c67c6e75…` (light-wood flat top, slim metal legs — the flat-top rule),
STUDENT_CHAIR `hssd/d96243bc…` (orange plastic stacker — **pinned because its color carries the
palette**, the jewelry_shop pin-for-palette rule), TEACHER_DESK `hssd/99e2a3e3…` (classic wood, drawers,
flat top), CHALKBOARD `hssd/3a39fbaa…` (routes via `PresentationFixtureRetriever`), WALL_TV
`hssd/576f0a57…` (reused meeting_room pin, 1.2 m native → `modulate_scale=1.4` BEFORE hanging),
STORAGE `hssd/56366c90…` (white sideboard, dark wood top), BOOKSHELF `hssd/2db50fb1…` (pre-filled with
books = stocked for free), GLOBE `hssd/55c813d9…`, WORLD_MAP `hssd/b22e386790…` (genuinely flat print).
**Gaps:** teal acoustic panels — no dataset match (same as computer_room's teal screens) → dropped
rather than forcing a wrong color; no true cork bulletin board (closest is a custom 3-panel green
chalkboard) → skipped, the front wall already carries a board.

## What worked / gotchas
- **`place_desk_chair` grid faces the FRONT wall** — `room.face(desks, toward="front_wall")` is correct
  for this unit type (the OPPOSITE of a `WorkstationGroup` grid, which faces `back_wall`). Verified in
  the interior render: chair backs to the viewer from the back of the room.
- **Build the unit ONCE, `6 *` it** — the notebook `place_on_top` tournament ran once; all six desks got
  identical notebooks. Same lesson as computer_room's `8 * ws`.
- **Texture strings bite twice.** (1) `"white painted wall with one teal accent wall"` embedded to a
  GREEN TILE texture on ALL walls — the accent-clause dragged the whole match; plain
  `"smooth white painted plaster wall"` fixed it. An accent COLOR the texture library can't express is
  better dropped (or carried by props) than smuggled into the texture string. (2) The ceiling renders
  black in interior strips regardless of ceiling texture wording — that's the renderer's open-top
  interior view, not a texture failure; don't chase it.
- **Room size: hold early, apply once, stop on oscillation.** RoomProportions walked 0.96 → 0.92 → 0.85
  across the phases (held per render-wins-early), applied `modulate_scale=0.85` in the final phase, and
  the next vote flipped to **1.1** — crossing neutral = converged; declined the enlarge and kept 0.85.
- **Teacher desk front-LEFT, door front-RIGHT** — the teaching wall's three slots stay clean
  (chalkboard center, display left as wall-hung; door right as floor opening) and the door's auto
  clearance never fights the teacher zone.
- **Identity at surface height** — notebooks on every student desk, globe + book stack + pen cup on the
  teacher desk, plant + books on the sideboard. The desks reading "in use" is what separates a classroom
  from a furniture showroom (jewelry_shop product-not-fixtures, applied to desks).

## VLM feedback log (chronological)
- Ph1 `rescale room by 0.96` → held (noise, render fine). `no rotation`/`no wall overlap` from the
  first build — correct-by-construction orientation collapsed the loop to the size thread only.
- Ph2 `rescale room by 0.92` → held (occupancy still rising).
- Ph3 full `rescale room by 0.85` → applied `RoomGroup(modulate_scale=0.85)` (final phase).
- Ph3 re-run `rescale room by 1.1` → **declined** (oscillation across neutral after one decisive
  application = converge signal; render reads well-filled).

## Manual constraints used
- None. Door auto-clearance + grid aisles + `CategoryClearanceConstraint` on the storage run were enough.
