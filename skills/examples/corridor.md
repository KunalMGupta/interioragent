---
id: example:corridor
kind: example
family: rows-runs-corridors
category: "corridor / hallway"
pattern: "Pure passage — the empty center lane IS the scene"
---
> **Digest (from the pattern index):** **Pure passage — the empty center lane IS the scene** — both LONG walls loaded (gallery prints + console/mirror one side, a LOW dressed green cabinet run the other), short walls light, nothing in the center; teaches "the VLM shrink vote never goes quiet on a corridor — decline the residual" (0.75 cramped → 0.85 converged), scale-by-height for wardrobe-tall wall furniture, and "no b/w checkerboard texture exists — drop the accent"


# Corridor — worked example ("Long Gallery Corridor with Reflective Floor")

Built via the guided 9-gate flow from the planner target (`tmp/plan_a_corridor/plan.png`).
The working program is `scenes/work/corridor.py` (seed=21); converged copy beside this file
(`corridor_v1.py`). The reference for a **pure passage room**: no hero, the axis and the clear
travel lane ARE the scene — both long walls carry the identity, the center stays empty.

## Prompt(s) this covers
- "a corridor" / hallway / gallery hall / entry passage.

## Plan summary
Planner → **"Long Gallery Corridor with Reflective Floor."** A straight sightline entry→end;
a gallery wall of monochrome prints travels one long side; the opposite side carries a deep-green
storage cue; glossy black-and-white checkerboard floor as the visual spine; slim console with
vases mid-corridor + a round gold mirror doubling depth; linear ceiling lights pacing the axis;
wood doors between rooms; greenery softening the geometry.

## THE layout: both long walls loaded, center = the travel lane
`RoomGroup` auto-sizes near-square by default; a corridor must be FORCED long. The lever is the
library/locker_room one: **load the two LONG (left/right) walls with runs, keep the short end
walls light, and put NOTHING in the center** — the empty center lane is not wasted floor, it is
the category:
- **RIGHT (gallery side)**: slim console (`RelativeGroup`, vase trio on top) at `right_wall_center`;
  round mirror `wall_right_center` above it; prints flanking at `wall_right_left/right`.
- **LEFT (green side)**: a `GridGroup.place_row` of 3 low green cabinets (ONE composed unit with
  books + small plant on top, `3 *`-duplicated — locker_room cubby pattern); a side door at
  `left_wall right`; a print over the low run at `wall_left_left`.
- **BACK (short)**: `place_window_standard` center + sheer curtain caps the sightline; tall plant
  in the corner. **FRONT (short)**: the entry door only.
- **Ceiling**: a black linear spotlight bar (flat, small emissive area) via `add_lighting`,
  density 0.015.

## Pinned assets (audited previews)
| Role | id | note |
|---|---|---|
| Console | `hssd/c33165b9d06aab9e2e162cd54b047883a80d5f00` | slim wood top, black metal legs |
| Round mirror | `hssd/f303d22d219dfb8878d74923c6d147fa02d0f64d` | champagne/gold thin frame; pass `width=0.7` for statement size |
| Prints ×3 | `hssd/xxxxd8a7…`, `hssd/32a0a181…`, `hssd/b42c22f3…` | thin flat monochrome abstracts |
| Linear light | `hssd/fb227c11d11cce96646739bba47c9997510d9e35` | black flush spotlight bar (add_lighting takes NO asset_id — this is the query's top pick) |
| Green cabinet | `future/024ee5bd-f5b5-4c2c-8c6e-ab6673c28faa` | the green cue; bad scale metadata + wardrobe-tall (see below) |
| Vase trio | `future/5a70fef8-a568-4138-b98f-6eba2af38d97` | ceramic vases w/ greenery, console top (`modulate_scale=0.5`) |

## What worked / gotchas
- **A corridor's open lane reads as "empty room" to the VLM — the shrink vote NEVER goes quiet.**
  `RoomProportions` voted 0.69–0.95 on every single build. Applied once in the final phase:
  0.75 → cramped (cameras jammed on the cabinets, vote flipped to 0.95); **0.85 = converged
  middle**. Decline the residual vote — the clear lane is the category (garage lesson at full
  strength).
- **Wardrobe-height wall furniture kills a corridor.** The green cabinets loaded ~2× AND are
  natively tall; at full height they crowded every view. Fix: **scale-by-height**
  (`_cab.scale(_cab.get_width()*0.9/_cab.get_height())`) to sideboard height — low runs leave
  the wall bands to art and keep the perspective open.
- **The texture library has NO black/white checkerboard.** Four wordings: "glossy b/w
  checkerboard marble tile floor" → pale planks; "b/w checkered tile floor" → plain dark grey;
  "b/w checkerboard floor tiles" / "black white checkerboard tiles" → a MULTICOLOR checker.
  Settled the **dark reflective tile** (the plan's "reflective spine" without its pattern) —
  same "drop the accent, don't smuggle it" call as classroom.
- **Per-wall textures are unsupported**, so the plan's green accent WALL became a green cabinet
  RUN — carry an accent color with furniture when the envelope can't.
- **`add_lighting` has no `asset_id` kwarg** (static lint caught it) — audit the fixture, then
  make the query specific enough that the audited mesh is the top pick.
- **A mirror "reflecting green" is not a bug** — the round mirror reads as a green/white disc in
  renders because it reflects the opposite green wall. Check what a mirror SHOULD show before
  swapping it.

## VLM feedback log
- `rescale room by 0.69–0.95` every phase → held per render-wins-early; final-phase two-step
  (0.75 cramped → 0.85 good); residual 0.8 vote declined as circulation noise.
- `no rotation` / `no wall overlap` every phase — all wall placements omitted `facing`, art
  hung over LOW supports, window on a slot no door claims (clean by construction, laundromat
  pattern).
- Green cabinets huge in phase 1 render (not a VLM signal — the eye) → uniform rescale, twice
  (metadata ~2× + height retarget).

## Post-ship bug hunt (user report → two core DSL fixes, 2026-07-12)
The shipped build had (a) a cabinet covering part of the left-wall door and (b) the mirror
overlapping the right-wall painting — both "impossible" per the auto constraints. Interrogating
the exported blend (world AABBs via a headless-Blender dump) found both root causes in core:
- **Door leaf ≠ clearance band.** `SceneProgObjectWall.translate` centered wall meshes by
  **vertex MEAN**; the door glb's dense hinge-side geometry skews its mean ~0.18 m off the bbox
  center, so the leaf landed z∈[0.34,1.39] while the doorway band (partition-center math)
  guarded z∈[0.17,1.22] — the cabinet run at z≥1.245 cleared the BAND by 2.7 cm while covering
  the LEAF by ~15 cm. Fix: center by bbox midpoint (window.py); leaf now lands exactly on the
  band. Follow-up: `_enforce_door_clearances` now **slides same-wall flush furniture ALONG the
  wall** out of the doorway span instead of pushing it off the wall into the room.
- **Wall art escaped its slot.** `place_on_wall_right_center(mirror)` anchors to the console
  (same wall+slot floor op), and the console had DRIFTED along the wall in the solve (z 1.96 →
  2.33); the mirror followed it into the `right` slot and overlapped the painting placed there —
  while the slot-occupancy model (and the VLM WallOverlap check) saw center vs right = clean.
  Fix: `_place_on_wall` clamps every wall-hung span (shrink + center-clamp) to its named slot.
- **Verification:** rebuilt and re-dumped the blend — door z[0.15,1.20] untouched (first cabinet
  slid to start exactly at 1.201, flush), art spans disjoint (gaps +0.52 / +0.04 m).
- **Meta-lesson: "no wall overlap" / silent constraints are claims about the MODEL, not the
  geometry.** When a render contradicts a constraint, dump the blend's world AABBs and compare
  against what the constraint actually computed — the bug lives in the gap between the two.
