# Kitchen — worked example (single complete fitted set)

The kitchen that taught: **use ONE complete fitted kitchen set, don't assemble separate pieces.**
Kitchens are the strongest "set asset" category — even more than the bathroom vanity/toilet sets
(see `../workflow/asset_selection.md` "Set assets" and `set-assets-and-scaling`).

## Prompt / plan
"A spacious, beautiful modern eat-in island kitchen." Planner (ALWAYS run it first): sage handleless
cabinetry, a white waterfall-stone island with bar seating, integrated appliances + statement hood,
brass globe pendants, a casual dining nook. Working scene: `scenes/work/kitchen_eatin.py`.

## The core lesson: ONE complete set, not glued-together pieces
A **complete fitted kitchen set** is a single mesh that bundles base + wall cabinets ("vanity"), the
cooktop/stove, the chimney/hood, *sometimes* a fridge, AND a separate island/countertop. Pick ONE good
comprehensive set as the backbone and add only the genuine GAPS (island/stools/dining nook, maybe a
fridge). Gluing a run + range + hood + fridge + ovens together instead gives **redundant cooktops,
mismatched styles, and scale fights**. (First pass assembled pieces and looked incoherent; Kunal
redirected to the single set.)

**Finding the set — hand-label its components.** Browse "complete fitted kitchen set … with island",
curate a pool (`assets/kitchen_set.json`, already a `KitchenUnitRetriever`), then label what each unit
bundles with the component tagger (`tools/build_kitchen_tagger.py` → `datasets/assets/
kitchen_components.json`: multi-select chips base/wall cabinets, cooktop, oven, range_hood, sink,
fridge, island, …). The labels tell you which set is most complete and exactly what's left to add.

## Sizing: cabinetry MAXES OUT the room height (floor-to-ceiling)
Room interior HEIGHT is hard-clamped to **3.0 m** (`RoomGroup`: `self.HEIGHT = min(max(heights+2,3),3)`).
Scale a kitchen set by **HEIGHT** (`_fit_height` uniform, target ~2.9–3.0 m), **NOT** `_fit_width` —
width-fitting a tall run overshoots and pokes the mesh THROUGH the ceiling (the bug we hit). Tall
oven/pantry columns also go floor-to-ceiling. Fridges read small at "real" width → size generously.

## A complete set is ONE mesh — you CANNOT edit it at part level
You can't recolor the uppers, restyle just the island, or move the bundled cooktop. The only lever is
to **swap the whole set** for a different complete set that already has the look you want. If a
planner/refine target asks for (e.g.) sage fronts but the set has black uppers, re-browse the pool and
swap the pinned `asset_id` — don't try to "edit" it.

## Lighting on a bundled-island set
The island is inside the set mesh, so a pendant group can only anchor to the WHOLE set — `add_lighting`
then spreads pendants across the full footprint and some clip the floor-to-ceiling cabinets, while
N×500 W area-lights blow the room out. `add_lighting` splits a fixed energy budget across N now (so
count no longer overexposes), but **render, then flag any OOB / overlap** rather than shipping it. A
clean pendant trio over just the island isn't reliably placeable on a bundled-island set.

## Status
`scenes/work/kitchen_eatin.py` — built around one complete set `future/a3cead55` (cabinets + cooktop
+ oven + sink + island with bar stools), floor-to-ceiling; added fridge, styled console (with
`add_clearance` front clearance), bare picture window, clock, pendant lighting. Not yet promoted to
`scenes/kitchen.py`.
