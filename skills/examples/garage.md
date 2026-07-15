---
id: example:garage
kind: example
family: zoned-multi-zone
category: "garage / car workshop"
pattern: "Cluster composition, not scattered props"
---
> **Digest (from the pattern index):** **Cluster composition, not scattered props** — a garage is a CAR + a work station + a storage run, each composed as ONE cohesive cluster placed as a unit (the `living_room`/`classroom` rule); scattering bench/chest/stool across three separate wall slots reads sparse and disconnected. The car hero sizes the room.


# Garage — worked example (car-centred workshop, composed in clusters)

Status: **built & VLM-clean** (`scenes/work/garage_workshop.py`, seed=9). Final compile returns
`no rescale` / `no rotation` / `no wall overlap` on **all four groups**. The defining lesson:
**a garage is a car + a work station + a storage run — compose each as a cohesive cluster and place
it as one unit, the way `living_room`/`classroom` do. Do NOT scatter bench/chest/stool across three
separate wall slots** (the first pass did that and read as sparse, disconnected props).

Status (2026-07-13, phase-gating retrofit): the scene was built and iterated as
`scenes/work/garage_workshop.py`. [`garage_v1.py`](garage_v1.py) is that same program, phase-gated:
`lint_program`-clean, layout / pinned ids / seed / comments preserved. It has **NOT been re-rendered
since the retrofit**, so the phase-1 / phase-2 / phase-3 splits are UNVERIFIED — treat the phase
boundaries as a proposal until someone runs `--phase 1`.

## Prompt(s) this covers
- "a home workshop garage with a car, a workbench, tool storage, shelving, and pegboards"

## Plan summary (from the planner — always run it first)
"Garage Workshop Grid: Car-Ready Multi-Tool Space." Bright, organized: white matte cabinetry,
polished light-grey epoxy concrete floor, a wood-topped workbench, a dark-steel tool chest, a
pegboard tool **spine**, tall white vertical storage, a side window for daylight, LED shop lighting,
and a car in the central bay. The library covers garages well — three Garage reference skills at
0.71–0.75.

## Program

[`garage_v1.py`](garage_v1.py) — phase 1 the floor anchors (the car hero, the work-zone cluster, the
storage run, the shell, the shutter and the man-door), phase 2 the cluster detail (the rubber work
mat, the corner tyre stack and the box pile), phase 3 the pegboard spine, the window, the clock and
the LED shop lighting.

`workbench run skills/examples/garage_v1.py --phase 1` builds the layout alone in ~1–2 min.

## What worked / gotchas
- **Compose zones as clusters — this is the whole lesson.** v1 placed the bench on `right_wall_center`,
  the chest on `right_wall_right`, the stool on `right_wall_left` — three disconnected props on a bare
  wall. v2 builds ONE `RelativeGroup` work zone (bench anchor + `place_on_right(chest)` +
  `place_on_front_further(stool)` + `place_rug(mat)`) and drops it with a single
  `place_on_right_wall_center(work_zone)`. It reads as a real work station. Mirror `living_room`'s
  U-cluster and `classroom`'s teacher/reading-nook zones — always cluster, then place.
- **A whole cluster can go on a wall.** `place_on_*_wall_center` accepts a group, not just an asset
  (like the gym cardio bank), and seats the cluster flush so the **pegboard on `wall_right_center`
  lands directly above the bench** (floor-vs-mounted occupancy families don't collide — console+art
  pattern). This alignment is the money shot; you only get it if the bench is wall-flush.
- **Relative placement verbs: front/back have `_adjacent`, left/right do NOT.** `place_on_right_adjacent`
  raises `AttributeError` → use `place_on_right` / `place_on_left` (they space with a default gap);
  `_adjacent`/`_further` exist only for front/back.
- **Wall slots are `left/center/right`, even on side walls** (no `_back`/`_front`). One long wall has
  exactly three slots — the storage run (2 cabinets + shelving) fills all three; extra pieces (a step
  ladder) have nowhere to go, so drop them or use a corner rather than overloading a wall.
- **The car is the hero — `place_on_center`, `facing="front"`, pin a real width.** Cars are an
  **uncurated gap category** (route to the generic retriever; ~half the "car" hits are TOY cars, best
  real-car sim ~0.44). Pin a specific real id AND pass `width=1.85` so it comes in at real scale —
  retrieval scale alone renders it toy-sized. `hssd/5f4a…36d0` (a blue Range Rover Evoque) oriented
  correctly from `facing="front"` with no front-cache.
- **Corner clusters (`StackGroup` tyres, `PileGroup` boxes-on-a-pallet)** fill the room and add garage
  character without cluttering the central circulation lane. `place_on_*_corner` tucks them away.
- **The roll-up shutter is the vehicle door — place it FLOOR-against-wall, not hung.** The ingested
  shutter (`custom/77209…49fb`) has `placement="wall"`, but `place_on_wall_front_center` (hung art)
  caps it to ~0.2× the wall and floats it at mid-height → it read as a tiny floating window. Use
  `place_on_front_wall_center` (floor-against-wall) so it stands on the floor at full height like a
  real garage door. Width pins uniform-scale, so size by the target height: for the portrait mesh
  (2.0×2.76 m, aspect 1.38) `width = target_H/1.38` → `width=2.174` gives a floor-to-ceiling 3.0 m
  door. Put the car `facing="front"` so it noses toward the shutter.
- **Two doors go on two walls.** The vehicle shutter (front wall) and the pedestrian man-door
  (`place_door("back_wall","left")`) must be on *different* walls — a man-door beside the garage door
  reads wrong. This also keeps WallOverlap clean.
- **The open floor in front of the car is correct** — it's the vehicle-door approach lane. The
  RoomProportions VLM reads it as "too big"; trust the render (see below).

## Asset picks (audited by preview — see `scenes/work/garage_workshop.md`)
| role | id | note |
|---|---|---|
| car (hero) | `hssd/5f4a14a4e5bc2feb7388b5d18d63350c38600f29` | real SUV; pin `width=1.85` |
| workbench | `hssd/107036734c8e21c8a103f7459cd72c9c486068aa` | wood top, simple frame; `modulate_scale=0.8` |
| tool chest | `hssd/67bc354a50314d0a8e1ccc4ec9afad60bc0790ed` | wide black steel drawers |
| tall cabinet | `future/07cce174-309e-4e41-ba40-e9abd17f637c` | tall white 2-door; ×2 as a run |
| shelving | `hssd/9f0427019d5a329e5410547e4291b2c4b8b20195` | open 5-shelf steel utility unit |
| pegboard | `hssd/3ec1423e301fa0a5df85fda5875b15dd944d54b4` | panel LOADED with tools — reads as the spine |

**Gap: no standalone bench-top tools.** The dataset has **no** usable red portable toolbox (best
"toolbox" hit is the black chest again) and **no** standalone bench vise (a "vise" query returns whole
workbenches). So don't `place_on_top` bench tools here — the **pegboard is the tool display**; leave
the bench clean. "cardboard storage box" also skews to dark plastic bins (fine as storage, not literal
cardboard). All logged as ingest candidates.

## VLM feedback we hit and how we resolved it
- **RoomProportions drifted down as occupancy rose** (`0.9`→`0.8`). Held size through Ph1–2 (the front
  approach lane *should* be open), applied `RoomGroup(modulate_scale=0.85)` in the final phase →
  `no rescale`. Same "render wins early; act on room size last" pattern as the living room.
- **ObjectProportions flagged the workbench `by 0.5`** in Ph1; the render showed only a mild oversize
  → declined the aggressive 0.5, used `modulate_scale=0.8` → later phases `no rescale`. Trust the
  render over a borderline shrink number.
- **Rotation / WallOverlap:** WallOverlap clean throughout. After adding the shutter the VLM emitted
  `rotate workbench / tool chest to face the stool` — declined as noise (the bench correctly backs the
  wall with its working face into the room; a stool in front doesn't mean the bench should pivot to it).
  The rotation check is a weak smoke alarm; the render is the arbiter.

## Manual constraints used
- None needed — the auto overlap solver spaced the car/bench/cabinets and the automatic door clearance
  kept the man-door approach open. Natural add if the room is tightened:
  `room.add_clearance(cabinets[0], dir="front")` for guaranteed door-swing space.
