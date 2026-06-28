# Scene batch — discussion notes (for review)

52 category scene programs live in `scenes/<name>.py`, one per category from your list.
Each is self-contained and written coarse-to-fine in the style of `classroom_v1.py` /
`livingroom_v1.py`: primary functional cluster(s) first (Relative/Around/Grid groups), then
the `RoomGroup` shell with wall furniture, wall-mounted fixtures, windows, a door, and a
ceiling light. They're all first drafts meant as **starting points to iterate on with you**,
not finished scenes.

## How to work these in parallel (the fast loop)

```bash
python batchgen.py living_room meeting_room bedroom dining_room kitchen   # any ~5 at a time
python batchgen.py --all --workers 3                                      # everything
python batchgen.py --list                                                 # names
```

After a run (or several), `python batchgen.py --collect --out combined_review.html` rebuilds
**one combined review of every category already rendered** from `tmp/` — no re-render — which
is the easiest single file to open. (Images are downscaled to JPEG so the whole 52-scene
report is a few MB, not hundreds.)

`batchgen.py` builds each scene in its own subprocess (retrieval + Blender isolated; a crash
can't sink the batch), a few concurrently, then writes a **single self-contained
`batch_review.html`** (interior renders embedded as base64 — opens locally, no server, since
the container has no port forwarding). Each card shows the category's renders, the retrieval
picks (query → chosen asset), and that category's note file (`scenes/notes/<name>.md`). The
loop: run a subset → open the HTML → for each card note what works / what's wrong / which
assets are bad → I edit the scene program (and we add assets/skills) → re-run. Re-runs hit the
**seeded retrieval cache**, so they're fast.

## What's new in the DSL (used throughout)

Realism **jitter**, all reproducible under the scene seed (see `skills/dsl_reference.md` →
"Randomness / realism"):
- `AroundGroup(jitter=…)` — nudges ringed seating off perfect positions/angles (dining,
  meeting, cafe, library). Overlap solve still runs, so no interpenetration.
- `RoomGroup(randomness=…)` — jitters free-standing floor items within their layout slot
  (translation only; facing preserved).
- `GridGroup(randomness=…)` — jitters row/grid gaps (was already there but **unseeded** →
  now seeded/reproducible).

## Cross-cutting issues to decide on (these recur across many categories)

1. **Room-level lighting is a workaround.** `RoomGroup` has no lighting method; lights are
   added via an anchor group's `add_lighting(...)`. For grid-only rooms (gym, warehouse,
   grocery, office) I add a small throwaway "light_anchor" cluster just to host the light.
   → *Proposal:* a first-class `room.add_ceiling_lights(desc, density=…)` (or auto a default
   panel grid). Worth adding.

2. **Room aspect is near-square.** `RoomGroup` auto-sizes from a 5×5 slot grid, so it can't
   make a genuinely long/narrow space. **Corridor** and the long **buffet/warehouse** halls
   suffer most (see corridor's header note). `BasicRoomGroup(width, depth, height)` takes
   explicit dims but is low-level (manual positions). → *Proposal:* an aspect/footprint
   override on `RoomGroup` (e.g. `min_width`/`min_depth`), or a corridor helper.

3. **Specialized fixtures will stress retrieval.** The dataset (HSSD/3D-FRONT) is
   home-furniture-biased. Commercial/industrial/medical props — slot machines, dental/
   operating/hospital/dental chairs, fume hoods, pallet racking, gondola/deli/buffet
   counters, washing machines, treadmills, billiard tables — are the **most likely to come
   back wrong** and the prime candidates for the **ingestion pipeline** + new curated
   retriever pools (like `presentation_fixtures`). Risk is flagged per-category in the notes.

4. **`place_desk_chair` reused for non-desks.** Used it for the music-studio mixing console
   and the TV news desk (anchor + seat + 180° rotate). Validate the pose; may need a plain
   anchor instead for consoles.

5. **Corner facing is heuristic/random.** `*_corner` placements pick one of two facings at
   random; corner plants/chairs can face oddly. Pin with `facing=` if it matters.

6. **Wall-mounted vs wall-adjacent.** `place_on_<wall>_wall_<pos>` = floor furniture against
   a wall (cabinets, shelves, machines); `place_on_wall_<wall>_<pos>` = mounted ON the wall
   (art, boards, displays, mirrors, menu boards), auto-scaled to a wall-fixture size. I used
   each per item; double-check anything that looks mis-scaled.

## Per-category notes

Each `scenes/notes/<name>.md` lists the pattern used, where jitter is applied, what to look
at first, and the likely asset-gap risk (LOW/MED/HIGH). They're surfaced on the HTML cards.

## Seeds

Each scene has a fixed `seed=`, so renders are reproducible. Change the seed to roll a
different (still plausible) variant of the same program — handy for showing variety.
