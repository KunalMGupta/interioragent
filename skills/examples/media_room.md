---
id: example:media_room
kind: example
family: hero-anchor-room
category: "home cinema / game media room"
pattern: "Focal-front theatre — TIERED seating via the bottom= lift, and a wall-hung hero whose ASPECT (not scale) beats the height penalty"
read_for:
  - "READ FOR ANY TIERED OR RAISED SEATING (riser, stage, platform, podium) — bottom= is AABB-referenced, and the lifted piece needs ignore_overlap + is_static"
  - "READ FOR ANY LARGE WALL-HUNG HERO (projection screen, mural, headboard wall) — freeform beats the slot clamp, and a >1 m-tall piece is penalized 10x: pin the ASPECT, not the scale"
  - "READ FOR ANY dense/large lighting fixture — add_lighting density is relative to the FIXTURE's footprint, not the room"
---
> **Digest (from the pattern index):** **Focal-front theatre** — every mass faces one hero
> wall. The three lessons that cost builds: (1) **tiered seating is a `bottom=` lift, and
> `bottom=` is AABB-referenced** (`_wall_furniture_y` adds `compute_obj_y`, which floors the
> AABB) — so an off-centre origin cannot sink the row, but the lifted piece MUST carry
> `ignore_overlap` (else the 2D solver shoves it off its own riser) + `is_static` (else the
> exploration floor drifts it). (2) The screen killer was NOT the wall-slot clamp but
> `wall_obj_scale_computer`'s `10*max(h-1,0)²` penalty — a 4:3 screen wide enough to matter is
> 1.76 m tall and gets ground to TV size; **a 16:9 mesh at 2.1 m wide is only ~1.1 m tall and
> hangs nearly twice as wide, free. Pin the aspect, not the scale** (and use
> `place_on_wall_freeform`, whose cap is 50% of the wall, not the slot's third). (3)
> `add_lighting` **density is relative to the fixture's own footprint**: a retrieved 1 m disc
> makes every density below ~0.13 round to N=1 — shrink the fixture (`modulate_scale=0.5`),
> then density moves again.

# Home game media room — worked example ("Stadium-Style Home Game Media Room")

## Status

Status: **built & VLM-clean** ([`media_room_v1.py`](media_room_v1.py), seed=31, Arm B guided
flow, 6 builds). Final compile: no rescale / no rotation / no wall overlap, zero lint or
WARNING lines, `ceiling_lights=5` (no starfield), 6.05 × 5.22 × 3.00 m. Per-view pure-black
fraction measured with PIL on the final build: ≤ 4.7%, no blinded view. All three prompt
elements verified IN THE EXPORTED BLEND, not just rendered: back row AABB 0.42–1.20 m sitting
on the riser's 0.00–0.40 m, both rows exactly collinear; 2.09 m 16:9 screen centred on the
front wall; snacks measured resting on the console's 0.84 m top.

## Prompt(s) this covers
- "a home game media room with tiered seating, a projector wall, and a snack console"

## Plan summary (from the planner)
A screen-centred theatre in deep neutrals — charcoal walls, grey acoustic carpet, two tiers of
black cinema recliners (the back row lifted on a light-oak riser), a walnut snack console with
a retro popcorn maker and drinks cooler. Delivered with two declared gaps: no framed
jerseys/memorabilia cases exist in the pool (substituted a framed-art collection + the one
baseball canvas), and no acoustic-panel mesh (dropped rather than forced — same gap `classroom`
hit).

## The layout idea: FOCAL-FRONT THEATRE, STAGED FRONT-TO-BACK
- **FRONT** — the projector wall: screen wall-hung dead centre (freeform), slim tower speakers
  in the LEFT/RIGHT slots only, centre floor slot left EMPTY (camera note below).
- **CENTRE** — tier 1: a 4-seat cinema recliner row on a charcoal rug, facing the screen.
- **BACK** — tier 2: the riser + an IDENTICAL row lifted onto it + the projector mounted high —
  three placements in the SAME wall-centre slot, 3D-disjoint (0–0.40 / 0.42–1.20 / 2.45–2.58 m).
- **LEFT** — the snack console run + retro red cooler (the palette accent, carried on a prop).
- **RIGHT** — the entry door at centre: its 0.9 m auto-clearance IS the plan's side aisle.

Camera safety by design: eye = 1.65 m (same arithmetic as `study_room` / `closet`); every wall
centre is low — riser+row top out at 1.18 m, console 0.84 m, screen is flat ON the wall, door
is an opening. The tall speakers live in wall-END slots. Near-miss worth knowing: the back-wall
camera lands 0.001 m in front of the screen face (looking away from it) — a thicker screen mesh
would have blinded that view.

## Pinned assets (audited previews, dims verified offline with `get_whd()`)
See the id block in the program. The ones that carry lessons:
- **CINEMA_ROW** `hssd/9d698f28` ships 2.50 × 0.78 × 0.81 — its LOW height is what makes the
  riser tier camera-safe (0.40 + 0.78 = 1.18 m). The taller reclining loveseat (1.36 m) on the
  riser would top out at 1.76 m and blind the front-wall view. Used for BOTH tiers → collinear
  by construction.
- **SCREEN** `custom/04918212` — a FLAT 16:9 retractable screen WITH a projected image, so the
  wall reads switched-ON. Replaced a 4:3 mesh that could only hang TV-sized (lesson below).
- The **"tall floor-standing speaker"** top hit ships 3.12 m tall — swapped to a 2.04 m mesh
  and height-fit uniformly to 1.15 m (reference examples are not safe; measure everything).
- Trap confirmed twice at the previews: a "Simple BLACK stage platform" is actually BLUE-topped;
  the popcorn CART renders as a pink team-branded unit with detached wheels. Both rejected only
  because the TRUE-COLOUR catalog previews were read (the inspect contact sheet is
  exposure-washed and misreports colour).

## Asset gaps
Memorabilia (jerseys/display cases) — substituted, declared. Acoustic panels — dropped. No
bias/riser step lighting, no subwoofer; two tiers rather than the plan's 2–3.

## Tiered seating: `bottom=` is AABB-referenced, plus the two riders
Read from source, not guessed: `RoomGroup._wall_furniture_y` (groups.py) returns
`compute_obj_y(obj) + b`, and `compute_obj_y` is `origin_y − aabb_min_y` — the offset that
floors the mesh's AABB. So `bottom=0.42` lands the row's true lowest point at 0.42 m
regardless of the mesh's origin — the usual way tiered seating dies (off-centre origins) simply
doesn't apply on this code path. What the path DOES demand:
- `ignore_overlap = True` — else the 2D-footprint solver sees row and riser as
  interpenetrating and shoves them apart along the wall. (This also exempts the row from
  `lint_floaters`, which would otherwise correctly call it a 0.42 m floater.)
- `is_static = True` — else GradSolver's exploration floor random-walks the small-footprint
  piece along the wall (the `living_room_cozy` fireplace drift).
Lift the AABB bottom a hair above the support (`bottom=RISER_H + 0.02`) so the embedded-object
lint's 3D test stays unambiguous. The riser itself is per-axis scaled — legal precisely because
a plain rectangular slab stays a plain rectangular slab.

## The wall-hung hero: aspect beats scale, freeform beats the slot
Two separate mechanisms conspire to shrink a wall-hung screen, and they need different fixes:
1. **The slot clamp**: `_place_on_wall` clamps any slot-verb piece to its slot's THIRD of the
   wall — TV size on any believable shell. `place_on_wall_freeform` passes no `along_bounds`;
   its cap is 50% of the wall, centred, hung at mid-height.
2. **The height penalty**: `wall_obj_scale_computer` minimises `L1 + 10·max(h−1,0)² + L3` — it
   pays 10× for every metre of height past 1 m. A 4:3 screen at 2.4 m wide is 1.76 m tall; the
   solver ground it to a measured 1.57 × 1.07 m. **The fix is not a bigger number, it is a
   WIDER ASPECT**: a 16:9 mesh at ~2.1 m wide is only ~1.1 m tall and clears the penalty almost
   free. Pin the aspect, not the scale.

## Lighting density is relative to the FIXTURE, not the room
`object.py` computes `max_lights = floor(W·D·0.64/(w·d))/4` from the FIXTURE's own footprint.
The retrieved flush disc arrives 1.0 × 1.0 m, so on this 6 × 5 m shell `max_lights=5` and every
density below ~0.13 rounds to N=1 — two builds were spent tuning a dial that could not move
(both 0.01 and 0.006 rendered one lone dish, `ceiling_lights=1` in report.json). Shrinking the
fixture (`modulate_scale=0.5`) raises `max_lights` to 20; `density=0.25` then gives N=6 real
downlights. Wattage is fixed at `scene.light_budget` and split across N — density changes the
ceiling's composition, never its brightness.

## A dark palette needs albedo headroom
Every seat is black leather against charcoal walls; the room has almost nothing to bounce
light. `scene.light_budget = 320` (dim, but NOT the wine cellar's 90) and MID-charcoal walls,
not near-black — the failure mode for this palette is an unreadable black box, not blowout.
`IDSDL_SKY=1.4` is set via `os.environ.setdefault` but only bites on a shell build — MCP
`run_scene` binds the sky at import on a warm server (the `wine_cellar` tooling gotcha).

## Program
[`media_room_v1.py`](media_room_v1.py) — phase 1 the whole floor layout incl. both tiers, the
riser, the console run and the door; phase 2 the snack dressing + the rug; phase 3 the screen,
projector, wall art and lighting. `workbench run media_room_v1.py --phase 1` validates the
tiers alone.

## What worked / gotchas
- `randomness=0.0`: two rows facing one screen must share a centre line, and no signal ever
  checks collinearity — zero jitter, then MEASURED in the exported blend (identical x-spans).
- The door's auto-clearance is load-bearing twice: it IS the side aisle, and at the original
  4.90 m width it shoved the front row 0.11 m off the back row — invisible to every signal;
  the final `modulate_scale=1.1` removed the conflict (`is_static` would NOT have helped: the
  deterministic door pass filters on `ignore_overlap`, not `is_static`).
- `modulate_scale=1.1` accepted from the FULL build's vote only (a room-size vote on a partial
  build is a vote on a room that does not exist yet), cross-checked against measured aisles
  (0.72 m and 0.59 m — genuinely tight for a room walked in the dark).
- Rug `size=1.15` on the one-row group: `size` is relative to the GROUP bbox — the ≤0.8 rule is
  about room-dominating clusters, and 0.85 here rendered a mat barely wider than the seats.

## VLM feedback we hit and how we resolved it
- `rescale room by 1.1` (full build) → accepted with measurement (aisles above).
- Phases 1–2 `no rescale` → correctly ignored as partial-build votes.
- The dim-mood gap (plan wants near-black plush; render is readable dim grey) → deliberately
  NOT chased with a shell build: an unreadable black box is the larger risk for this palette.

## Manual constraints used
None beyond the defaults — the tier stack is `bottom=` + the two riders; camera safety is
geometric.

## Possible refinements (not blocking)
- The screen renders BLANK WHITE at final quality (the 16:9 mesh that hangs large carries no
  visible content; the 4:3 mesh that showed content could only hang TV-sized) — a wide mesh
  with a baked-on projected image would resolve both at once.
- The seating axis sits 0.30 m off the screen axis (slot centres ≠ wall centres on this shell).
- The shell came out wider than deep, so the tiers are not staged down a long room as the plan
  wanted; a depth-biased shell would stage better.
