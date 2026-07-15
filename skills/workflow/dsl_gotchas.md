---
id: workflow:dsl_gotchas
kind: collection
role: "Cross-cutting DSL gotchas (ex scenes/NOTES.md), parsed as lesson:dsl/<slug>"
---

# Cross-cutting DSL gotchas & open design notes

Moved verbatim from `scenes/NOTES.md` (2026-07-15) so all knowledge lives under `skills/`.
These recur across many categories; each is an observed limitation plus the proposal it
prompted. Parsed into `lesson:dsl/*` cards by retriever_core.

1. **Room-level lighting is a workaround.** {#dsl-room-level-lighting-is-a-workaround} `RoomGroup` has no lighting method; lights are
   added via an anchor group's `add_lighting(...)`. For grid-only rooms (gym, warehouse,
   grocery, office) I add a small throwaway "light_anchor" cluster just to host the light.
   → *Proposal:* a first-class `room.add_ceiling_lights(desc, density=…)` (or auto a default
   panel grid). Worth adding.

2. **Room aspect is near-square.** {#dsl-room-aspect-is-near-square} `RoomGroup` auto-sizes from a 5×5 slot grid, so it can't
   make a genuinely long/narrow space. **Corridor** and the long **buffet/warehouse** halls
   suffer most (see corridor's header note). `BasicRoomGroup(width, depth, height)` takes
   explicit dims but is low-level (manual positions). → *Proposal:* an aspect/footprint
   override on `RoomGroup` (e.g. `min_width`/`min_depth`), or a corridor helper.

3. **Specialized fixtures will stress retrieval.** {#dsl-specialized-fixtures-will-stress-retrieval} The dataset (HSSD/3D-FRONT) is
   home-furniture-biased. Commercial/industrial/medical props — slot machines, dental/
   operating/hospital/dental chairs, fume hoods, pallet racking, gondola/deli/buffet
   counters, washing machines, treadmills, billiard tables — are the **most likely to come
   back wrong** and the prime candidates for the **ingestion pipeline** + new curated
   retriever pools (like `presentation_fixtures`). Risk is flagged per-category in the notes.

4. **`place_desk_chair` reused for non-desks.** {#dsl-place-desk-chair-reused-for-non-desks} Used it for the music-studio mixing console
   and the TV news desk (anchor + seat + 180° rotate). Validate the pose; may need a plain
   anchor instead for consoles.

5. **Corner facing is heuristic/random.** {#dsl-corner-facing-is-heuristic-random} `*_corner` placements pick one of two facings at
   random; corner plants/chairs can face oddly. Pin with `facing=` if it matters.

6. **Wall-mounted vs wall-adjacent.** {#dsl-wall-mounted-vs-wall-adjacent} `place_on_<wall>_wall_<pos>` = floor furniture against
   a wall (cabinets, shelves, machines); `place_on_wall_<wall>_<pos>` = mounted ON the wall
   (art, boards, displays, mirrors, menu boards), auto-scaled to a wall-fixture size. I used
   each per item; double-check anything that looks mis-scaled.
