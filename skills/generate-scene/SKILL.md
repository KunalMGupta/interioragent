---
name: generate-scene
description: Generate a complete 3D interior scene from a text prompt through the
  9-gate recipe — plan, retrieve procedurally-similar traces, audit assets, author a
  phase-gated IDSDL program, build phase-by-phase with verification at every gate,
  judge against the plan, write back what you learned. Use when asked to "make/build
  a <room type>" end to end.
---

# Generate a scene from a text prompt — the nine gates

Scenes are built through a fixed recipe distilled from the ~26 worked examples:
verify EARLY and CHEAP at every step, never write the whole scene and hope. Three
ways to run the same recipe:

- **Guided (any MCP agent):** `howto()` then `flow_start("<prompt>")` — the server
  deals one gate at a time, validates your evidence mechanically (files, lint,
  fresh phase-N reports, no unresolved warnings), and records overrides. State is
  file-backed (`tmp/flows/`); `flow_status(flow_id)` resumes after a disconnect.
- **Manual (you are the author):** follow the gates below yourself. This is the
  same thing without the server holding your hand.
- **Automatic (one command):**
  ```bash
  PYTHONPATH=/work python main.py "<prompt>" --out results/<name>          # LLM author
  PYTHONPATH=/work python main.py "<prompt>" --author command \
      --command 'claude -p "$(cat TASK.md)" --permission-mode acceptEdits' # any coding agent
  # or as MCP background jobs: generate_scene_start / _status / _result
  ```
  The pipeline runs the same gates itself: static lint before every build,
  phase-1/2 gate builds before the first full one, critic loop, design judge.

Requires `OPENAI_API_KEY`, the datasets under `IDSDL/datasets/`, and Blender via
SceneProgExec. Builds run under the minimal render policy: the 4-wall room strip
in `tmp/<run>/vlm_views/` is your critique image.

## The gates

### 1. PLAN — get the design target
```bash
python -m planner_core "<prompt>" --out tmp/<run>/plan
```
Open `plan.png`, read `skill.txt`: anchors / secondary items / wall+decor /
palette / lighting mood. The plan image is what gate 8 judges against — keep it open.

### 2. RETRIEVE — reason over the knowledge catalog
```bash
python -m retriever_core "<prompt>" --plan tmp/<run>/plan/skill.txt --out tmp/<run>/ctx
```
Read `bundle.md` IN FULL: recipes matched by layout pattern (not category name),
their polished programs, and the atomic lessons selected for this scene.
Via MCP: `retrieve_context`.

### 3. AUDIT ASSETS — eyeball before placements
Batch-resolve your shopping list (`skills/workflow/asset_selection.md`) and —
non-negotiable — **eyeball the preview of every mesh you pin** (caption≠mesh; the
#1 late-caught failure class). Verify the category's IDENTITY props exist; if a
key fixture is missing, mass the product instead of shipping an empty fixture.

### 4. AUTHOR — write the phase-gated program, lint it
Follow the matched recipe's skeleton, gated on `IDSDL/phases.py` (canonical form:
`skills/examples/coffee_shop_v1.py`):
```python
from IDSDL.phases import current_phase
PHASE = current_phase()          # 1 anchors / 2 surfaces / 3 walls+mood (default 3)
...
if PHASE >= 2: station.place_on_top([...])
if PHASE >= 3: room.add_lighting(...)
```
Later phases only ADD — never move phase-1 geometry. Hard rules the bundle
enforces: room size is a CONSEQUENCE (few slots, modest hero widths, never
`modulate_scale > 1.0` to dodge overlaps); product at viewing height; rigid
composed stations; `N * unit` duplication; wall-hung = flat only (<0.25 m);
lighting density 0.01–0.02 small room. Then:
```bash
python workbench.py lint <program>.py     # instant; run refuses to build on errors
```

### 5. BUILD PHASE 1 — verify the floor layout (~1 min)
```bash
python workbench.py run <program>.py --phase 1
```
Strip check: room size right? overlaps? clearances? orientation? The report's
`[Lint]`/`WARNING` lines (floaters, starfield, overlap, over-height) must be
clean. Fix and rebuild phase 1 until they are — this loop is cheap, use it.

### 6. BUILD PHASE 2 — dress the surfaces
```bash
python workbench.py run <program>.py --phase 2
```
Product at viewing height, stocked shelves, items sized to their surfaces,
nothing floating.

### 7. BUILD PHASE 3 — full scene + converge
```bash
python workbench.py run <program>.py
```
Apply the `skills/workflow/vlm_feedback.md` policy: render is the arbiter; ONE
decisive change; rotation flags are weak alarms; converge, don't chase. If
exactly one object floats while neighbours rest, interrogate the exported blend
(`bottom = loc_z - dims_z/2`) — off-center mesh origin means SWAP the mesh.

### 8. JUDGE — against the plan, then the vibe layer
Compare the strip to `plan.png`: does it instantly read as the category? Are the
plan's identity elements present? Then add the **vibe layer** (see
`skills/examples/coffee_shop.md`): stocked shelves, menu/signage, one warm accent
seat, warm envelope, greenery. The VLM loop converging is necessary, not
sufficient — gut-check legibility yourself.

### 9. WRITE BACK — grow the knowledge base
Distill `skills/examples/<name>.md` (+ the program as `<name>_v1.py` beside it),
add its row to `skills/examples/README.md` **keeping the table format** (the
retriever parses it), and append concrete feedback→action entries to
`skills/workflow/vlm_feedback.md`'s decision log.

## Pointers
- DSL API: `../dsl_reference.md` · phases: `IDSDL/phases.py` + `../workflow/coarse_to_fine.md`
- Deterministic checks: `IDSDL/lints.py` (compile lints + `lint_program`)
- Worked reference end-to-end: `../examples/coffee_shop.md`
- Pipeline internals (lint/phase gates, critic/judge policies): `generator_core/pipeline.py`
- Guided-flow internals (gate validation, provenance): `IDSDL/service/flow.py`
