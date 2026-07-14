# Bar / cocktail lounge — worked example

Status: **built & essentially VLM-clean** ("Moody Luxe Bar & Lounge", `scenes/work/bar_lounge.py`,
seed=26). Final compile: objects `no rescale`, stools `no rotation`, `no wall overlap`,
RoomProportions converged 0.8→0.95 after the final-phase shrink. Built coarse-to-fine through the
workbench (3 render passes). Built as `scenes/work/bar_lounge.py`; `bar_v1.py` is that program
phase-gated (2026-07-13), `lint_program`-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record).

## Prompt this covers
- "a stylish, moody cocktail bar / lounge: a long bar counter with a row of stools, a mirrored
  back-bar lined with bottles/glassware, warm ambient pendant lighting, a few velvet lounge nooks,
  rich materials (dark wood, brass, marble), sophisticated evening atmosphere."

## Plan summary (from the planner)
"Moody Luxe Bar & Lounge: **Linear Bar as Central Anchor**." A long front-facing bar line is the
room's social anchor; a row of stools along its front; a back-bar loaded with bottles/glassware as a
luminous focal wall; layered warm lighting (globe pendants + under-shelf glow); small velvet-clad
lounge nooks in the corners. Palette: charcoal walls, espresso wood, brass hardware, ivory marble,
dark herringbone floor. Retrieved skills were all 0.77–0.80 Bar/Restaurant matches — library covers
this type well.

## The layout idea: WIDE + SHALLOW, bar line on the long back wall
A bar is the archetypal "long run on a long wall" room (see coarse_to_fine "place long strips on the
long edges"). The **bar line** (back-bar cabinet against the wall + counter + a stool row in front of
it) occupies the whole long BACK wall; the **short walls stay light** (a mirror on one, a framed print
on the other); the **front half is the lounge** (two velvet nooks facing back toward the bar), with the
door on the front wall between them.

## Program

[`bar_v1.py`](bar_v1.py) — phase 1 builds the floor anchors (the rigid bar station: back-bar + baked
aisle + counter + stool row, the two lounge nooks, the door), phase 2 the floor dressing (nook rugs,
corner palm), phase 3 the short-wall decor (mirror, print) and the pendant lighting.

`workbench run skills/examples/bar_v1.py --phase 1` builds the layout alone in ~1–2 min.

## What worked / gotchas
- **Pin the hero fixtures.** Bar counter, stools and back-bar are the whole scene — browse + pin them
  (`asset_id=`) rather than trusting a cold NL query. Good picks from the dataset:
  bar counter `future/dd75f4ed…` (vintage paneled front, reads unmistakably as a serving bar),
  tufted leather stool `future/84e8c226…` (backrest = luxe), back-bar `future/f92b65d2…` (tall glass-
  door cabinet already displaying glassware — a self-contained focal wall, no need to place bottles).
- **Lengthen the counter with `width=` (NOT uniform scale).** `AddAsset(..., width=3.6)` stretches only
  the width into a long bar and keeps a realistic low height. Uniform-scaling a counter to 3.6 m wide
  would also make it absurdly tall.
- **Stool row = `AroundGroup.place_rectilinear(longer_side1=stools)`** puts all stools on ONE long side
  (the customer side), not wrapped around. **Keep the default facing — do NOT `face(s, toward=counter)`.**
  `place_rectilinear` already sets a uniform straight facing (`anchor.get_rotation() - 180`, so the whole
  row is parallel and faces the bar). A per-stool `face(toward=counter)` aims each at the counter's
  *centre point*, which fans the end stools inward and reads worse; a row of seating wants uniform
  straight facing. (Kunal, 2026-07-05.) `face(toward=...)` is for a *conversation* cluster where seats
  should angle at a shared anchor — not for a straight service row.
- **`place_circle(2)` = an intimate 2-top** (chairs on opposite sides facing across the table). Build the
  nook once and duplicate `nook_l, nook_r = 2 * nook` so both nooks are identical (design_principles).
- **A self-contained loaded back-bar beats assembling shelves + bottles.** The chosen cabinet already
  shows glassware, so Phase 2 needed no fiddly `place_on_top` bottle clusters on it (which float/clutter).

## VLM feedback we hit and how we resolved it
- **Pendant lighting exploded into a ~30-globe cloud (the big one).** `add_lighting(desc, density)`
  copies the *retrieved light mesh* N times (`N = 1 + (max_lights-1)*density`). A plural/"**a row of**
  … lights" query returns a mesh that is ALREADY a cluster of globes → N copies = a cloud. **Fix: query
  a SINGULAR "a warm brass globe pendant light."** Then tune density: the count also spreads across the
  **group footprint**, and the bar_group includes the stool depth, so a high density fans the globes
  forward into the room. `density=0.2` gave a tight ~4-6-globe cluster over the counter. (`best_grid`
  always makes the count squarish, so you can't force a perfect 1×N single row without a code change —
  a low count is the lever.)
- **RoomProportions drifted 0.9 → 0.8 → 0.95 across phases.** Held the size through phases 1–2 (render
  looked fine, occupancy still rising), then applied `RoomGroup(modulate_scale=0.85)` in the final phase
  (used 0.85 not the suggested 0.8 — a bar wants some open circulation). Re-check returned 0.95 ≈
  converged. (Same "render wins early; act on room size in the final phase" rule as living_room.)
- **Persistent "rotate velvet tub chair to face the coffee table" — declined as noise.** `place_circle(2)`
  already seats the pair facing across the table; the render confirmed correct conversational seating.
  Per vlm_feedback.md, the RotationConstraint is a weak smoke alarm — the render is the arbiter.

## The bartender aisle: use GEOMETRY, not a clearance constraint (verified)
Kunal wanted a real gap between the back-bar ("cellar") and the counter. First attempt was
`room.add_clearance(backbar, distance=0.5, dir="front")` — **it under-delivered**. Verified numerically
(build with `auto_render=False`, read `get_aabb()` z-spans): the constraint fires in the right direction
(raytraces toward the counter, sees it 0.06 m away) but only opened the gap to **~0.16 m, not 0.5 m**. It
loses a tug-of-war: the clearance pushes the counter forward while the stool-row *overlap* (stools sit
right in front of the counter) plus the tight room push back, settling at a weak compromise. Bumping
`distance` fought the same tug-of-war.

**Robust fix — bake the gap into the geometry.** Compose the back-bar BEHIND the whole bar line as one
rigid station; `RelativeGroup.place_on_back` seats it a fixed `FRONT_BACK_GAP` (0.45 m from the anchor's
back face) behind, and the solver can't collapse a rigid group's internal spacing:
```python
with scene.AroundGroup(...) as bar_group:      # counter + stool row (as before)
    ...
backbar = scene.AddAsset("...back-bar...", asset_id="future/f92b65d2-...", width=2.6)
with scene.RelativeGroup() as bar_station:
    bar_station.set_anchor(bar_group)          # anchor = the counter+stool line
    bar_station.place_on_back(backbar)         # ~0.84 m aisle here (anchor incl. stool depth inflates 0.45)
# in the room: place the whole station; the back-bar lands flush on the wall, gap becomes the aisle
room.place_on_back(bar_station, facing="front")   # NOT place_on_back_wall_center(backbar) separately
```
Measured result: back-bar flush on the wall, counter ~0.84 m in front, both at rotation 0 (facing the
room) — a guaranteed, generous service aisle. **General lesson (also in ../workflow/constraints.md):**
`add_clearance` is a soft gradient that can be overpowered by adjacent overlap; when you need a *reliable*
gap between two specific pieces, compose them in one group with an explicit-gap placement rather than
asking the solver to open it. (Latent quirk noticed: for an axis-aligned object `is_aligned_zpos` and
`is_aligned_zneg` are both true, so the clearance's `if/elif` never takes the `zneg` branch — a back-bar
rotated 180° would clear the wrong side. Ours was rotation 0, so it picked the right side by luck.)

## Manual constraints used
- None in the final version. The door auto-clearance keeps the entrance clear; the bartender aisle is
  geometric (see above), not a `ClearanceConstraint`.

## Possible refinements (not blocking)
- The back-bar cabinet renders a dusty-mauve wood, not espresso — a complete-mesh material can't be
  edited; swap the pinned `asset_id` for a darker back-bar if a stricter palette is wanted.
- A `MirrorStationGroup`-style true mirror behind the back-bar (see salon `IDSDL/mirror.py`) would sell
  the "mirrored back-bar" from the plan; the loaded glass-door cabinet was enough here.
