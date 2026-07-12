---
name: generate-scene
description: Generate a complete 3D interior scene from a text prompt — plan, retrieve
  procedurally-similar traces, audit assets, author the IDSDL program, build, and iterate
  on the room VLM strip until converged and design-matched. Use when asked to "make/build
  a <room type>" end to end.
---

# Generate a scene from a text prompt

Two modes share the same stages. **Mode A (agent-as-author)** — YOU are the coding agent:
follow the playbook below step by step; this is how the best scenes are made. **Mode B
(automatic)** — one command drives the same loop with a pluggable author:

```bash
PYTHONPATH=/work python main.py "<prompt>" --out results/<name>          # LLM author
PYTHONPATH=/work python main.py "<prompt>" --author command \
    --command 'claude -p "$(cat TASK.md)" --permission-mode acceptEdits' # any coding agent
# or as MCP background jobs: generate_scene_start / _status / _result
```

Requires `OPENAI_API_KEY`, the datasets under `IDSDL/datasets/`, and Blender via
SceneProgExec. Builds run under the minimal render policy: the 4-wall room strip in
`tmp/<run>/vlm_views/` is your critique image.

## The playbook (Mode A)

### 1. Plan — get the design target
```bash
python -m planner_core "<prompt>" --out tmp/<run>/plan
```
Open `plan.png` and read `skill.txt`. Extract anchors / secondary items / wall+decor /
palette / lighting mood. The plan image is the target every later judgement compares
against — keep it open.

### 2. Retrieve traces — reason, don't guess
```bash
python -m retriever_core "<prompt>" --plan tmp/<run>/plan/skill.txt --out tmp/<run>/ctx
```
Read `bundle.md` IN FULL: the matched recipes (by layout pattern, not category name),
their polished programs, and the lessons selected for this scene. Via MCP:
`retrieve_context` (then Read the bundle path it returns).

### 3. Audit assets BEFORE placements
Batch-resolve your shopping list (`skills/workflow/asset_selection.md` stress-test
pattern) and — non-negotiable — **eyeball the preview of every mesh you pin**
(caption≠mesh). Verify the category's IDENTITY props exist (the pastries, the gems, the
toys); if a key fixture is missing, mass the product instead of shipping an empty or
off-theme fixture.

### 4. Author the program
Follow the matched recipe's skeleton. Hard rules the retrieved bundle enforces —
the ones violated most often:
- **Room size is a consequence**: few floor slots for a cozy brief, modest hero widths,
  never a wide multi-cluster group in one slot, never `modulate_scale > 1.0` to dodge
  overlaps.
- Product at viewing height; stock service shelves with `place_inside`.
- Composed rigid stations (counter+back-bar+cart = one unit); repeated units built once,
  `N * unit`.
- Wall-hung = flat only (<0.25 m deep); deep meshes are floor furniture.
- `add_lighting`: flush fixture, density ~0.01–0.02 small room / ~0.05 medium; singular
  pendant queries on the key zone group.

### 5. Build & criticize
```bash
python workbench.py run <program>.py
```
Read the strip + `feedback.txt`. Apply the `skills/workflow/vlm_feedback.md` policy:
render is the arbiter; one decisive change; rotation flags are weak alarms; converge,
don't chase. **If exactly one object floats while neighbours rest, interrogate the
exported blend** (`bottom = loc_z - dims_z/2`) — an off-center mesh origin means SWAP the
mesh, not compensate.

### 6. Judge against the design
Compare the strip to `plan.png`: does it instantly read as the category? Are the plan's
identity elements present? Then add the **vibe layer** (see
`skills/examples/coffee_shop.md`): stocked shelves, menu/signage, one warm accent seat,
warm envelope textures, greenery. The VLM loop converging is necessary, not sufficient —
gut-check legibility yourself.

### 7. Write it back
New scene type converged? Distill `skills/examples/<name>.md` (+ the program as
`<name>_v1.py` beside it), add its row to `skills/examples/README.md` **keeping the table
format** (the retriever parses it), and append concrete feedback→action entries to
`skills/workflow/vlm_feedback.md`'s decision log.

## Pointers
- DSL API: `../dsl_reference.md` · phases: `../workflow/coarse_to_fine.md` ·
  composition defaults: `../workflow/design_principles.md`
- Worked reference for this exact playbook end-to-end: `../examples/coffee_shop.md`
- Pipeline internals (critic/judge policies live in code): `generator_core/pipeline.py`
