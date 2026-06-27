# Kitchen — example

Status: **stub.** To be filled when we build a kitchen with the workbench loop.

## Prompt(s) this covers
- A kitchen: counters/cabinets along walls, island or table, appliances (fridge,
  stove, sink), bar stools, overhead/under-cabinet lighting.

## Plan summary
_(fill from planner output)_

## Skeleton program
Likely shape (to validate):
- counter runs as wall-adjacent furniture (`place_on_<wall>_wall_*`)
- island/table as a floor anchor (RelativeGroup with stools `place_on_front`/arc)
- appliances against walls; fridge/stove/sink along the work triangle.

```python
# Phase 1 — island/table + main counter runs (floor & wall anchors)
# Phase 2 — stools, small appliances, counter props
# Phase 3 — upper cabinets, window, lighting, decor
```

## What worked / gotchas
- Kitchens are wall-driven — expect heavy use of `place_on_*_wall_*` and likely
  `WallOverlapConstraint` feedback as counters/appliances compete for wall slots.

## VLM feedback we hit and how we resolved it
_(fill)_

## Manual constraints used
- Candidate: `ClearanceConstraint` in front of fridge/oven/dishwasher (door swing
  + standing room); `AccessConstraint` for stools to the island.
