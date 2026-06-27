# Coarse-to-fine workflow

Build a scene in three phases, cheapest-impact-last. Rationale: the floor
furniture dominates how well the scene matches the prompt, and everything else
is positioned relative to it. Get the big rocks right before sand.

After **every** phase: run the workbench, look at the renders, read the VLM
feedback, fix, recompile. Do not advance to the next phase with a broken layout.

---

## Phase 0 — ideate

Run the planner on the prompt:

```bash
PYTHONPATH=/work /opt/conda/envs/interioragent/bin/python -m planner_core "<prompt>" --out tmp/<run>/plan
```

Open `plan.png`, read `skill.txt`. Extract a concrete shopping list:
- the **anchors** (1–4 big floor pieces),
- the **secondary** items (what sits on/around the anchors),
- the **wall/ceiling/decor** elements,
- materials/colors (floor, walls, textiles) and the lighting mood.

Check `retrieved.json` — which reference skills fired tells you whether the
prompt is well-covered by the library.

## Phase 1 — floor anchors

Place only the dominant floor furniture. Group them with Relative/Around/Grid as
the layout demands, then wrap in a `RoomGroup` and place the assembled group(s)
on the floor so the room sizes itself.

Goal of this phase: **correct layout and correct proportions.** Nothing else.

Check:
- Layout reads correctly from the interior renders (circulation, facing, grouping).
- `RoomProportionsConstraint` / `ObjectProportionsConstraint` feedback — act on
  rescales now, while there's little else to disturb.
- Room not too cramped/spacious (occupancy ratio ~0.4 is the target the VLM uses).

## Phase 2 — surface & floor details

Add what sits on or beside the anchors: table-top items, plants, rugs, floor and
table lamps, small props. Use `place_on_top`, `place_rug`, nested RelativeGroups
(e.g. lamp on a side table on the front-left of the sofa).

Check:
- Details sit where intended (top surfaces, beside anchors) and don't float/clip.
- Proportions of the new small items (`ObjectProportionsConstraint`).

## Phase 3 — walls, ceiling & decor

Wall art (`place_on_wall_*`), wall-adjacent furniture (`place_on_*_wall_*`),
windows + curtains, doors, ceiling lights (`add_lighting`), and any remaining
decor to close the gap to the prompt/plan.

Check:
- `WallOverlapConstraint` feedback — wall items overlapping each other or doors/windows.
- Final interior renders match the plan's look and the prompt.

---

## The per-phase loop

```
edit program  ->  workbench run  ->  open renders + read VLM feedback  ->  decide fixes  ->  repeat
```

Stop a phase when: layout is sound, VLM feedback is "no rescale"/empty or
consciously overridden, and the renders look right. Then record anything notable
in the example file and vlm_feedback.md before moving on.
