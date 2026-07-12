# Coarse-to-fine workflow

Build a scene in three phases, cheapest-impact-last. Rationale: the floor
furniture dominates how well the scene matches the prompt, and everything else
is positioned relative to it. Get the big rocks right before sand.

After **every** phase: run the workbench, look at the renders, read the VLM
feedback, fix, recompile. Do not advance to the next phase with a broken layout.

This loop is now MECHANICAL, not aspirational: gate the program on
`IDSDL/phases.py` (`PHASE = current_phase()`, then `if PHASE >= 2:` /
`if PHASE >= 3:` around the later layers) and build each phase separately —
`workbench run <program>.py --phase 1` builds just the floor layout in ~1–2 min
(vs ~9 for a full build). Canonical gated program:
`skills/examples/coffee_shop_v1.py`. Rule: later phases only ADD; never move
phase-1 geometry. Deterministic lints (floaters, lighting starfield — see
`IDSDL/lints.py`) land in the feedback of every build; keep them clean per phase.

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

## Phase 1 — major assets (layout + proportions)

Place only the **biggest pieces** — the hero anchor(s) and the long furniture
runs. Group each cluster with the **correct placement group** for its
relationship (don't reach for `RelativeGroup` if the motif is unrepresentable —
see `../add-placement-group/SKILL.md`), then wrap everything in a `RoomGroup` and
place the assembled groups so the room sizes itself.

Goal of this phase: **correct layout and correct proportions.** Nothing else.

**Asset distribution drives the room shape — place long strips on the long edges.**
The `RoomGroup` sizes each wall from what you hang on it, so *which walls you load*
determines whether the room comes out wide, square, or deep. Decide the target
shape from the room type, then load accordingly:
- A **wide, shallow** room (salon, gym, retail) ⇒ put the **long runs** (a styling
  row, a bench of lockers, a counter line) on the **two long walls**, and keep the
  **two short walls light** (a single cabinet, the backwash unit, the door/window).
- A **square** room ⇒ balance the load across all four walls.
- Place the **largest assets first** as those long strips; the big rocks set the
  footprint and everything later fits inside it. A long strip stranded on a short
  wall, or a heavy asset on every wall, fights the proportions you want.

Check:
- Room **shape** matches intent (long runs landed on the long walls, short walls light).
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
