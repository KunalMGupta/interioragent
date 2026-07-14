# Restaurant kitchen (commercial back-of-house) — worked example

Status: **built & converged** (`scenes/work/resto_kitchen.py`, seed=17;
[resto_kitchen_v1.py](resto_kitchen_v1.py) beside this file, phase-gated). Four-render arc on
2026-07-13: phase-1 #1 caught a blinded camera (below) → phase-1 #2 passed clean → full #1
warned on the utensil rail + hung the hood in the camera's face + voted `rescale 0.8` → full #2
(rail dropped, hood raised, one decisive `modulate_scale=0.9`) **converged**: the vote decayed
to a trivial `0.97` (decay-toward-neutral = converging, executive_office's rule), `no rotation`,
`no wall overlap`, no warnings. This closed the LAST uncovered dataset category
(Restaurant-Kitchen).

## Prompt this covers
- "a commercial restaurant kitchen: a stainless cook line under an extraction hood, prep
  tables, a pass, walk-in style fridges/freezers, wire shelving, pots and pans"
- any back-of-house / hotel / canteen kitchen. For a DOMESTIC kitchen use `kitchen.md`
  (recipe A, the fitted set) — NOT this.

## Recipe-B is CORRECT here (the licensing note)
`kitchen.md`'s standing rule — build a kitchen on ONE fitted unit set, never from parts — is a
rule about DOMESTIC kitchens, and the dataset has no commercial-line "set" asset anyway. A
commercial kitchen is genuinely made of interchangeable stainless NSF modules, so recipe-B
composition (rigid `GridGroup` runs of separate machines) is both the only option and the
honest one. All 15 pinned assets are native HSSD — the category needed **no ingest** (browse
audit 2026-07-13): 6-burner range, industrial oven, 2-burner stove, worktables, a
sink-integrated commercial counter, a Bain-Marie wagon (the pass), tall freezer + side-by-side
fridge, chrome wire racks, a wide range hood, pan set / stockpot / red enamel set (the one
warm accent in an all-stainless palette).

## Layout (line + island + pass)
- BACK: the COOK LINE — range + oven + stove as one rigid run flush on the wall; the hood
  wall-mounted above it (phase 3).
- CENTRE: the PREP ISLAND — two worktables end-to-end; the cookware masses ON THE RUN in
  phase 2 (`RelativeGroup` anchored on the whole `GridGroup`, so `place_on_top` spreads props
  along the continuous counter — kitchen.md's rule; identity at working height — laboratory).
- LEFT: wire rack + the wash counter. RIGHT: the cold pair (one run) + a second rack.
- FRONT: the Bain-Marie pass facing back into the kitchen; door front-right. **Windowless by
  design** — back-of-house realism, and it sidesteps the black-void limit entirely.

## What worked / gotchas — the CAMERA-HEIGHT rules, twice
The interior cameras sit at ~1.4–1.5 m at each wall's CENTRE, and this scene tripped both ways
to blind one:
- **Phase-1 #1: the side-by-side fridge at `right_wall_center` rendered that view SOLID
  BLACK** (bakery's tall-fixture rule, caught live). Fix: the cold pair became ONE `GridGroup`
  run in the wall's END slot (`right_wall_left`), centre left clear. Tall pieces never take a
  wall's centre slot.
- **Full #1: the hood canopy at `bottom=1.55` hung exactly at camera height** — the whole back
  view rendered as a featureless grey slab (and a garbage view corrupts every constraint
  judged from it, laundry_room's law). Fix: `bottom=1.95` — the camera now looks UNDER the
  canopy. **A deep wall-mounted canopy must clear ~1.9 m**, not just "above the appliance".
- **The utensil rail replayed museum's mask rule**: manifest-thin, but the wall scaler
  re-derived it 0.36 m deep (> 0.25 m limit) → "furniture FLOATING in mid-air" warning →
  dropped. Utensils want a low anchor or a genuinely thin rail mesh, not the art band.
- **`rescale 0.8` on a working kitchen is mostly the AISLES** (garage/corridor
  legitimate-circulation rule) — but the vote was big, so ONE decisive `modulate_scale=0.9`
  (stopping short of the vote: the line and island are fixed-size `GridGroup` runs that
  overflow a shell shrunk below their footprint — kitchen.md's 0.85-over-0.80 precedent).
  It decayed to 0.97 and stopped. Never walk a shell vote in steps.
- **All floor mass is phase 1** — racks, pass, cold run, everything with a footprint — per the
  verification round's rule (a floor object gated to phase ≥2 shrinks the phase-1 shell;
  coarse_to_fine.md). Phase 2 is ONLY the cookware on the prep run, created inside its gate.

## VLM feedback we hit and how we resolved it
- phase 1: `rescale room by 0.87` / `0.8` → ignored (partial-build rule; layout signals clean
  both runs).
- full #1: `rescale room by 0.8` + the rail warning + the hood slab → the three fixes above.
- full #2: `rescale room by 0.97` (trivial, post-apply decay) / `no rotation` /
  `no wall overlap` → **converged, stopped.**

## Manual constraints used
- None. Auto overlap/bounds + door clearance carried it; the hood mount is geometry
  (`bottom=` + `ignore_overlap` + `is_static`), not a constraint.
