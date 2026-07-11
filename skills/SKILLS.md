# SKILLS — entry point for scene generation

Read this first, every time, before writing a scene program. It is the master
index and workflow. The detailed knowledge lives in the linked files; this page
tells you the order of operations and where to look.

## What this is

A growing, hand-distilled knowledge base for building interior scenes with the
IDSDL DSL and iteratively optimizing them. It is updated *after* every scene we
build together: lessons, gotchas, and especially how we acted on VLM feedback
get written back into these files so the next scene starts smarter.

## Read order for a new scene

1. **This file** — workflow + constraint model (below).
2. **[dsl_reference.md](dsl_reference.md)** — the API: how to actually write the program.
3. **[examples/](examples/)** — the closest matching scene type. **Start at [examples/README.md](examples/README.md)** — the catalogue that maps each recipe to the *layout pattern* it teaches (set-piece hero, zoned single room, repeated-unit grid, long rows, large multi-zone, hero-in-the-middle, motif-group, focused cluster). Copy its skeleton, don't start from scratch. (dental_office is the reference for a **single-room build hung on one ingested "unit/set" hero asset**; executive_office is the reference for a **single room split into work + lounge zones around a storage backbone**, and carries the `add_lighting` "flush fixture, never a chandelier" lesson; retail_store is the reference for a **shop/showroom: a central double-sided-rail spine + perimeter merch loop + branded service wall**, and carries the "lighting density scales with floor area" + "storefront = worst-case black void" lessons; jewelry_shop is the reference for **making a retail scene read as its category by showing the PRODUCT at viewing height** (mass jewelry props on a display table + counter + pedestals — empty glass display cabinets read as furniture, not a shop) and carries the "VLM loop verifies geometry, not category legibility — human gut-check a retail scene" + "reword counter→display cabinet" + "pin anything whose colour carries the palette" lessons.)
4. **[workflow/coarse_to_fine.md](workflow/coarse_to_fine.md)** — the phase plan you will follow.
5. **[workflow/design_principles.md](workflow/design_principles.md)** — composition defaults to apply while placing (seating always gets a table; a seat's task light lives in the seat's group; build a symmetric/repeated unit once and duplicate with `N * unit`).
6. **[workflow/constraints.md](workflow/constraints.md)** and **[workflow/vlm_feedback.md](workflow/vlm_feedback.md)** — keep open while optimizing.
7. **[workflow/asset_selection.md](workflow/asset_selection.md)** — **start here for a new scene**: the asset-first kickoff (map → catalogue → curate a pool → ingest 5–10 high-impact missing assets), then agentic retrieval: inspect/override picks + the baked-in selection rules. A fast **retrieval stress test** (embedding-only `svc.browse` over ~30 brainstormed category queries, flag top-1 sim < 0.30 as a gap) is the cheapest way to confirm the dataset can carry a new category before you build — worked example in `examples/retail_store.md`.
8. **[workflow/asset_ingest.md](workflow/asset_ingest.md)** — only if you INGEST your own `.glb`s: the single-mesh invariant the loader depends on, why `_copy_centered` must be a verbatim copy (trimesh `force="mesh"` → white / Scene round-trip → disassembled), how to diagnose a stripped/exploded mesh from the glb JSON (a good preview PNG doesn't prove a good stored mesh), and why NOT to "fix" it in the shared loader.
9. **[add-placement-group/SKILL.md](add-placement-group/SKILL.md)** — only if an *arrangement relationship* isn't expressible in the DSL. Read "Step 0: do you actually need one?" first.

## The workflow in one paragraph

Given a prompt: (1) run the **planner** to get a look + conditioning skill, (2)
build the scene **coarse-to-fine** in three phases, (3) after each phase run the
**workbench** to get renders + VLM feedback, (4) act on that feedback, recompile,
repeat. Then distill what you learned back into these files.

### Tools

```bash
# Ideate: collage + conditioning skill + retrieved reference skills
PYTHONPATH=/work /opt/conda/envs/interioragent/bin/python -m planner_core "<prompt>" --out tmp/<run>/plan

# Build + observe: runs the program, prints VLM feedback + render index
PYTHONPATH=/work /opt/conda/envs/interioragent/bin/python workbench.py run <program>.py
```

The workbench prints the per-run scratchpad path, the collected VLM feedback,
and a list of every render PNG produced — open those to judge quality. See
[workflow/rendering.md](workflow/rendering.md).

### Category scene library + batch review

`scenes/<name>.py` holds a first-draft program for each room category (52 of them; see
`scenes/NOTES.md` for the design rationale and the cross-cutting open questions). To build
and review many at once — the parallel iteration loop — use the batch harness:

```bash
python batchgen.py living_room meeting_room bedroom      # a subset (work ~5 at a time)
python batchgen.py --all --workers 3                     # everything
```

It builds each scene in its own subprocess (a few concurrently) and writes a self-contained
`batch_review.html` (interior renders embedded + retrieval picks + each category's note from
`scenes/notes/<name>.md`) you open locally — no server needed. Edit the scene programs / add
assets+pools based on the review, then re-run (re-runs hit the seeded retrieval cache).

**Realism jitter** (reproducible under the scene `seed`): `AroundGroup(jitter=…)`,
`RoomGroup(randomness=…)`, `GridGroup(randomness=…)` — see dsl_reference.md → "Randomness".

## The three constraint kinds (know which is which)

The DSL has three distinct constraint mechanisms. Confusing them is the #1
source of wasted effort. Full detail in [workflow/constraints.md](workflow/constraints.md);
the summary:

| Kind | Examples | Who applies it | What you do |
|------|----------|----------------|-------------|
| **Auto gradient** | Overlap, OutOfBounds, **door clearance** | the DSL, automatically every compile (door clearance fires per `place_door`) | nothing — trust it |
| **Manual gradient** | Clearance, Access, Visibility | you, via `room.add_clearance/add_access/add_visibility(...)` inside the group | add it deliberately where physics/usage demands (wardrobe/cabinet/appliance clearance, sofa→TV sightline, chair→desk access). Keep visibility pairs axis-aligned + floor objects. |
| **VLM (textual)** | ObjectProportions, RoomProportions, WallOverlap | auto-runs, but only **writes text** to `scene.vlm_feedback` — never moves anything | read the feedback and act on it yourself (rescale, reposition, recompile) |

Key mental model: **gradient constraints move objects; VLM constraints only talk.**
The VLM tells you "rescale sofa by 0.8" — nothing happens until *you* change the
program and recompile.

## Coarse-to-fine phases (detail in [coarse_to_fine.md](workflow/coarse_to_fine.md))

1. **Phase 1 — floor anchors.** Place the high-impact furniture on the floor
   (seating, beds, tables, desks, large storage). Get layout + proportions right.
   These dominate prompt alignment.
2. **Phase 2 — surface & floor details.** Items on tables, plants, rugs, lamps,
   small props. Things that sit on or beside the phase-1 anchors.
3. **Phase 3 — walls, ceiling & decor.** Wall art, windows, doors, curtains,
   ceiling lights, and anything still missing to match the prompt/plan.

At each phase: render → read VLM feedback → fix → recompile before moving on.

## After a scene: write it back

When a scene is done, update:
- the matching `examples/<type>.md` with the working skeleton + what we changed and why,
- `workflow/vlm_feedback.md` with any new feedback→action patterns,
- this file if the workflow itself changed.
