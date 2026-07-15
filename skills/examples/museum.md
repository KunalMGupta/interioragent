---
id: example:museum
kind: example
family: zoned-multi-zone
category: "museum / grand exhibit hall"
pattern: "The INGEST-FIRST room, at hall scale: identity is 100% the EXHIBITS, and the hero commands by standing ALONE."
---
> **Digest (from the pattern index):** **The INGEST-FIRST room, at hall scale: identity is 100% the EXHIBITS, and the hero commands by standing ALONE.** A 68-glb ingest (dino skeleton, belt-spanning rope stanchions, Rosetta Stone, knight-on-horse, Neptune…) is what makes the category buildable at all — the walls are just ivory plaster + a certified picture hang. Layout: hero in the CENTRE inside a stanchion cordon (`AroundGroup.place_rectilinear`, `sparsity=0.8` so the posts stand OFF the ribs — at 0.5 they read as scaffolding), plinth ranks and themed zones ringed around it in floor thirds, only LOW (0.5 m) benches wall-flush under the art. Teaches: size the hero to its CORDON, not the room (3.4 swept the tail through two zones; 3.0 converged); the tallest exhibit SETS the ceiling (`max_height=5.0` lets the knight's 4.10 m lance make a real hall — never shrink a showpiece to the 3 m default); a "wall" piece the scaler re-derives to >0.25 m deep is a PLINTH exhibit, not art (the mask warned as FLOATING furniture and was dropped); the `add_lighting` density ladder runs BACKWARDS (0.02 in a hall — 0.12 tiled a STARFIELD of track bars); ingested `scale` is a guessed width so retarget every exhibit BY HEIGHT; and hang CERTIFIED canvases only (4 dataset paintings are dud meshes that render empty/black — struck off in the companion probe). Companion `scenes/work/museum.py` (small gallery) holds the wall-art machinery story: two `place_on_wall_freeform` bugs fixed in groups.py + why sculptures stand mid-floor (a rank under an art run occludes every slot on the wall)


# Museum — worked example

Status: **built & converged** (`scenes/work/museum_grand.py`, seed=31; [museum_v1.py](museum_v1.py)
beside this file, phase-gated). Three-run arc on 2026-07-13: phase-1 layout pass (`no rotation` /
`no wall overlap`; shell 0.93 ignored per the partial-build rule) → full build WARNED on the
wall-hung mask + voted `rescale 0.9` → mask dropped, 0.9 applied once → final compile **fully
clean**: `no rescale / no rotation / no wall overlap`, no WARNING lines. Companion:
`scenes/work/museum.py`, the small sculpture gallery that debugged the wall-art machinery this
hall builds on (two `place_on_wall_freeform` bugs fixed in `IDSDL/groups.py`, the dud-canvas
audit, the occlusion lesson).

## Prompt this covers
- "a grand museum hall with a dinosaur skeleton centrepiece behind rope barriers, galleries of
  marble busts and statues on pedestals, historic machines, arms and armour, paintings on the
  walls and viewing benches"
- any big many-exhibit museum / "great gallery" room; for a small, calm sculpture-and-paintings
  gallery see the companion program.

## Why this scene exists (the ingest story)
The dataset has almost no museum content natively — the small gallery had to DROP its rope
stanchions (asset gap) and build identity from plinth-mounted decor sculptures. A 68-glb ingest
(2026-07-13) unlocked the real thing: a mounted **dinosaur skeleton**, a **stanchion whose mesh
includes its spanning belt**, the Rosetta Stone, busts (Caesar, Nefertiti), Neptune, a knight on
an armoured horse, a samurai, a dodo, Stephenson's Rocket, a loom, a potter's wheel… Identity
comes entirely from the EXHIBITS; the room itself is just ivory walls, a marble floor, benches
and a picture hang. This is the operating_room/laboratory arc at full strength: when a category
reads as impossible, the answer is an ingest, not a fake.

## Layout (hero in the middle, zones ringed around it)
- CENTRE: the dinosaur inside a rope CORDON — an `AroundGroup.place_rectilinear` rank of 3
  stanchions per flank. The stanchion mesh spans ~1.8 m including its belt, so a rank of them
  CHAINS into a continuous barrier rather than reading as loose poles.
- LEFT / RIGHT floor thirds: plinth ranks (classical busts | natural-history curiosities), each a
  `GridGroup.place_row` of `display()` units facing the central aisle.
- BACK: antiquities; BACK-LEFT/RIGHT: industry | crafts; FRONT-LEFT/RIGHT: arms & armour | the
  sculpture court. All tall exhibits stand in FLOOR slots, metres off the walls.
- WALLS: the certified picture hang + two LOW (0.5 m) benches wall-flush under the runs — a bench
  below a painting never occludes it; anything taller gets slid out of the art's span (the
  companion program's load-bearing lesson).
- FRONT: the axis bench + the door.

## What worked / gotchas
- **The hero commands the room by standing ALONE, not by being big.** At `scale(3.4)` the
  dinosaur's tail swept across the hall into the industry and crafts zones; 3.0 keeps it clear.
  Size a centrepiece to its cordon, not to the room.
- **The cordon must stand OFF the exhibit** — `AroundGroup(sparsity=0.8)`. At 0.5 the posts
  landed under the ribs and read as scaffolding, not a barrier.
- **The tallest exhibit sets the ceiling, not the other way round.** The knight keeps his native
  4.10 m lance and `RoomGroup(max_height=5.0)` turns the (tallest + 2 m) clamp into a genuine
  5 m hall. Never shrink a showpiece to fit the 3.0 m default (fixture-true-size rule).
- **A "wall" piece deeper than 0.25 m is a plinth exhibit, not wall art.** The ceremonial mask's
  manifest said 0.13 m deep, but the wall scaler re-derives depth from the hung size → 0.31 m →
  the build warned it would "read as furniture FLOATING in mid-air". Dropped from the hang (and
  the 0.43 m-deep ship figurehead was never hung at all). Respect this warning; a floating mask
  ships otherwise.
- **The `add_lighting` density ladder runs BACKWARDS from intuition.** Density is a fixture
  COUNT and the count grows with FLOOR AREA: the small gallery wanted 0.08, and at 0.12 this big
  hall tiled a STARFIELD of dozens of track bars. **0.02** gives a calm run over a floor this
  size. (retail_store's rule, at hall scale.)
- **Plinth = uniform `scale()` then `scale_only_height()`.** A plinth is a box; distortion is
  free. The `display()` helper anchors the PLINTH and `place_on_top`s the exhibit — never the
  other way round (`place_on_top` seats onto the group's ANCHOR).
- **Ingested `scale` is a GUESSED width — retarget every exhibit by HEIGHT** via
  `o.scale(o.get_width() * target_h / o.get_height())`. The per-asset heights in the pin table
  came from `get_whd()` audits, not the manifests.
- **Certified canvases only.** Four dataset paintings are DUDS that hang as an empty frame or a
  black panel (struck off in the companion program's probe: `hssd/b9c49bfc`, `future/7b0ad909`,
  `hssd/6a669a56`, `future/4d8d0fa9`). The six hung here are the certified set. Wall art scales
  UNIFORMLY — `width=` pins one axis, letterboxes the canvas, and the scale computer then hangs
  a sliver.
- **Slot verbs for the hang, not freeform:** in a 5 m hall freeform centres art at HEIGHT/2 =
  2.5 m — too high. The slot band hangs at viewing height, and in a hall this size the slot cap
  (`wall_len/5`) is generous (~2 m canvases).

## Program
[`museum_v1.py`](museum_v1.py) — phase 1 the floor layout (every exhibit, the cordon, benches,
door — identity is almost entirely phase 1, like game_room), phase 2 the plinth-top exhibits
(created inside the `display()` gate so they never orphan) + the corner palms, phase 3 the
picture hang + track lighting. `workbench run skills/examples/museum_v1.py --phase 1` builds the
layout alone. NOTE: the palms are floor-standing but corner slots the shell already reserves —
if a future edit moves them into open floor, ungate them (see the jewelry_shop/restaurant
floor-mass rule from the 2026-07-13 verification round).

## VLM feedback we hit and how we resolved it
- phase 1: `rescale room by 0.93` → ignored (partial-build rule; layout signals clean).
- full #1: the mask FLOATING warning (above) + `rescale room by 0.9` → dropped the mask, applied
  `modulate_scale=0.9` once.
- full #2: `no rescale / no rotation / no wall overlap` → converged, stopped.

## Manual constraints used
- None. Auto overlap/bounds + door clearance + the wall-art occlusion machinery carried it.
