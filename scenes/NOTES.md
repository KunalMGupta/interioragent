# Scene batch — discussion notes (for review)

52 category scene programs live in `scenes/<name>.py`, one per category from your list.
Each is self-contained and written coarse-to-fine in the style of
`../skills/examples/classroom_v1.py` / `../skills/examples/living_room_v1.py`: primary
functional cluster(s) first (Relative/Around/Grid groups), then
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

Moved to `skills/workflow/dsl_gotchas.md` (single knowledge root under skills/).

## Per-category notes

Each `skills/examples/logs/<name>.md` lists the pattern used, where jitter is applied, what to look
at first, and the likely asset-gap risk (LOW/MED/HIGH). They're surfaced on the HTML cards.

## Seeds

Each scene has a fixed `seed=`, so renders are reproducible. Change the seed to roll a
different (still plausible) variant of the same program — handy for showing variety.
