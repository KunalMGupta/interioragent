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
3. **[examples/](examples/)** — the closest matching scene type (living_room, classroom, kitchen, …). Copy its skeleton, don't start from scratch.
4. **[workflow/coarse_to_fine.md](workflow/coarse_to_fine.md)** — the phase plan you will follow.
5. **[workflow/constraints.md](workflow/constraints.md)** and **[workflow/vlm_feedback.md](workflow/vlm_feedback.md)** — keep open while optimizing.

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

## The three constraint kinds (know which is which)

The DSL has three distinct constraint mechanisms. Confusing them is the #1
source of wasted effort. Full detail in [workflow/constraints.md](workflow/constraints.md);
the summary:

| Kind | Examples | Who applies it | What you do |
|------|----------|----------------|-------------|
| **Auto gradient** | Overlap, OutOfBounds | the DSL, automatically every compile | nothing — trust it |
| **Manual gradient** | Clearance, Access, Visibility | you, via `room.add_clearance/add_access/add_visibility(...)` inside the group | add it deliberately where physics/usage demands (wardrobe clearance, sofa→TV sightline, chair→desk access) |
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
