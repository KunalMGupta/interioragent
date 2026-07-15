---
id: workflow:rendering
kind: workflow
role: "Workbench render types and when to use each"
---

# Rendering & inspection

How to see what you built. Everything lands in the per-run scratchpad
`tmp/<run_id>/`; nothing should be written to the repo root.

> **Minimal render policy is the DEFAULT** (`IDSDL/render_policy.py`). To keep
> iteration fast, the only render per compile is the **room VLM strip**
> (`render_interior_combined()`, cached once per compile in `tmp/<run>/vlm_views/`),
> and the only critique channel is the room-level VLM (RoomProportions + Rotation +
> WallOverlap). Anchor-group VLM constraints (ObjectProportions/Rotation — a full
> Blender render per group per compile) and the 8-view `render_interior()` set are
> skipped. Set `IDSDL_MINIMAL_RENDERS=0` to restore everything below.

## The workbench

```bash
PYTHONPATH=/work /opt/conda/envs/interioragent/bin/python workbench.py run <program>.py
```

Prints the run dir, the collected VLM feedback, and an index of every render
PNG. `workbench.py report` re-prints the latest run's saved report
(`tmp/<run>/report.json`, `feedback.txt`). Open the listed PNGs to judge quality.

## Render types

| Render | Cameras | Use for |
|--------|---------|---------|
| Group exterior 4-view (`group.render()`) | edge-midpoints, looking in | open furniture groups (no walls) — Phase 1/2 layout & object proportions |
| Room **interior** 4-view (`render_interior_combined()`) | inside, one per wall, ceiling hidden | inside a closed RoomGroup — the strip the RoomProportions VLM sees |
| Room interior set (`render_interior()`, auto on RoomGroup compile) | 4 walls + 4 corners | full interior inspection each compile |

Why interior renders exist: a closed room blocks exterior cameras — they only
see the outer box. Interior cameras sit inside and hide the ceiling. Windowed
walls are removed on export, which also opens sightlines.

## What to look at per phase

- **Phase 1 (anchors):** interior 4-view — layout, facing, circulation, room
  proportion. This is where most fixes happen.
- **Phase 2 (details):** interior set/corners — do table-top and beside-anchor
  items sit correctly, nothing floating or clipping.
- **Phase 3 (walls/ceiling):** wall views + corners — art placement, window/door,
  curtains, lighting mood; check `WallOverlapConstraint` feedback against them.

> **Lighting is illumination — don't judge the final look before lights exist.**
> A scene with **0 lights** (no `add_lighting`, no windows) renders dim and flat;
> that is *not* a quality problem, just an unlit room. `add_lighting(...)` adds a
> real area light (and `place_window_floor_to_ceiling` opens a daylight wall), so
> Phase 1–2 renders are expected to look dark. Add the lighting pass (usually
> Phase 3) before assessing materials, mood, or "is this scene good." Confirmed on
> the first living room (every render was dim until the Phase-3 ring pendant).

## Performance notes

- Rendering uses Cycles. With a CUDA GPU it accelerates automatically; in a
  CPU-only container it still works, just slower. Lower `render_samples` /
  resolution on the RoomGroup for faster iteration, raise for a final look.
- `auto_render=True` means every RoomGroup compile renders — expected, but it's
  why iteration has a per-compile cost. Turn it off for pure-layout experiments
  if needed.
