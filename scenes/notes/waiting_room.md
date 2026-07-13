# Waiting Room

- **Pattern:** Two facing seat banks + reception anchor. `WorkstationGroup` reception (dark-walnut
  curved counter, `set_rotation(180)` = INVERTED desk, `place_on_back(facing="back")` so staff have
  floor); two 4-chair banks pinned flush on the long walls facing each other; magazine table between
  them; palms flanking reception; clock + door front; picture window on the seating wall.
- **Hero / the gap:** no beam-linked waiting bank exists (the multi-seat meshes are moulded CAFETERIA
  rows; every "waiting bench" query returns a DOMESTIC sofa with throw pillows). Built the bank by
  PACKING single chairs — `GridGroup(sparsity=0.05)` runs no overlap solve, so they stay abutted and
  read as one linked row. Chair pinned for PALETTE (the top "olive green" hits render yellow/tan).
- **Scale metadata lied 3×** (all caught offline with `get_whd()` before the first build): desk 0.66 m
  tall → height-fit 1.10 m; palm 0.55 m → 1.75 m; and the best magazine mesh has **H = 0.00** (a flat
  mesh a `place_on_top` height-fit would detonate) → pinned one with real height (0.047).
- **Wall art:** the focal MUST be PANORAMIC — art centres at ~1.5 m and the counter's monitor tops out
  at ~1.6 m, so any back-centre print is crossed by it, and no clearance pass helps (it only slides
  FLOOR objects). Aspect, not size: widening the portrait print would have made it 2.16 m tall.
- **Empty-frame trap ×2:** half the framed prints AND 6 of 8 wall clocks preview as blank white
  rectangles/discs. Pinned only meshes with a visible face/artwork.
- **Eye catch (loop-clean):** the plan's glass table rendered as a solid BLACK MONOLITH → swapped for
  an open-frame walnut top. Caught in the cheap phase-1 loop.
- **Room size:** vote 0.8–0.9 every phase → FILLED the floor (palms + water cooler) and applied one
  decisive `modulate_scale=0.95`, short of the vote (the banks are rigid GridGroup rows — shrinking
  below their footprint overflows their slots). Converged at 0.95 ≈ neutral.
- **Built & VLM-clean** (seed=11): `no rotation` / `no wall overlap` / no lints from the FIRST phase-1
  build to the last — every orientation is structural (WorkstationGroup + no `facing=` on wall
  placements). Full write-up in `skills/examples/waiting_room.md`; program `scenes/waiting_room_v1.py`.
  Asset-gap risk: MED (linked seating — solved by packing, no ingest needed).
