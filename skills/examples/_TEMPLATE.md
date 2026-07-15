# <Scene type> — worked example ("<Plan name from the planner>")

Copy this when starting a new scene type. Fill it in as you build; the finished pair is the
distilled, reusable recipe for this kind of room.

> **Start the file with frontmatter — the catalog reads it, not the README table:**
>
> ```yaml
> ---
> id: example:<name>
> kind: example
> family: <one of the families in examples/README.md — pick the closest>
> category: "<human category, e.g. walk-in closet / dressing room>"
> pattern: "<one line: the layout pattern this teaches>"
> read_for:            # optional — situation triggers ("READ FOR ANY ...")
>   - "<trigger>"
> ---
> ```

> **A worked example is a PAIR, and the program is a real `.py` — never a code block.**
>
> * `<name>.md` — this file: the lessons, the pattern, the traps. Prose.
> * `<name>_v1.py` — the program, copied in beside it. **Runnable.**
>
> The `.py` is the artifact an agent copies. It must lint (`lint_program`), run (`run_scene`),
> and be phase-gated. A skeleton pasted into a markdown fence cannot do any of those, and rots
> silently the first time the DSL moves under it — which is exactly what happened to the
> pre-2026-07 examples. **Do not inline the full program here.** Point at the `.py`, and quote
> at most a ~10-line excerpt when a lesson needs the code in front of the reader.

Name both halves after the room, not the plan: `bakery.md` + `bakery_v1.py`. No `_v1` on the
`.md`; no other suffix on the `.py`.

---

## Status

One line, kept current — this is what a reader checks first:

`Status: **built & VLM-clean** (`skills/examples/<name>_v1.py`, seed=N, converged in N render passes).`
`Final compile: no rescale / no rotation / no wall overlap.`

If it is not converged, say so and say what is still wrong. A stale "VLM-clean" is worse than
an honest "phase-2 open".

## Prompt(s) this covers
- "<the prompt a user would actually type>"

## Plan summary (from the planner)
What the planner produced: the named idea, anchors, palette, mood. Note the retrieved skill
scores if the library was thin — a low top score is itself a finding.

## The layout idea: <NAME THE PATTERN>
**The most important heading in the file.** `README.md` indexes the catalogue by *pattern*,
not by room name, so an agent finds this example by recognising its shape. Name it, say which
existing example it inherits from, and say what is new:

> *hero-in-the-middle, sterile* — `game_room`'s clearance rule, `dental_office`'s discipline,
> and one thing neither teaches: the room reads by being BARE.

State the wall jobs and floor slots explicitly. Most layout bugs are a wall with no job.

## Pinned assets (audited previews, dims verified offline with `get_whd()`)
The ids you pinned and *why* — the caption that lied, the preview that saved you, the mesh that
loaded as a miniature. If you ingested, say what the raw zip needed before it was ingest-ready.

## Asset gaps
What does not exist in the pool, and what you did instead (mass a prop / hunt by silhouette /
ingest / drop it). Feed anything reusable into `../workflow/creative_asset_gaps.md`.

## The lesson(s) this scene mints
One `##` section per real lesson, named for the trap and not the room. Free-form — this is
where the value is, and it is the reason the file is long. A lesson earns a section when it
would change what the next author *does*; everything else belongs in "gotchas" below.

## Program
Point at the `.py`. Describe the phase split in prose so a reader knows what each build costs:

> [`<name>_v1.py`](<name>_v1.py) — phase 1 the floor anchors, phase 2 the surface dressing,
> phase 3 walls/glazing/lighting. `workbench run <name>_v1.py --phase 1` builds the layout
> alone in ~1–2 min.

## What worked / gotchas
Layout choices that read well; retrieval queries that returned good meshes (and the wordings
that returned junk); placement verbs that did what you wanted.

## VLM feedback we hit and how we resolved it
feedback → action → result. Include the votes you **declined** and the arithmetic that let you
decline them — a refuted vote is as instructive as an accepted one. Mirror the notable ones
into `../workflow/vlm_feedback.md`.

## Manual constraints used
Clearance / Access / Visibility, and why the default was not enough.

## Possible refinements (not blocking)
Honest loose ends, so the next author does not mistake them for finished work.

---

# The program: `<name>_v1.py`

```python
"""<Room> — "<Plan name>" (guided 9-gate flow).

Planner target: <the look, the anchors, the palette, the mood>.

Layout — <the wall-by-wall map; say WHY each centre slot is what it is>:
- BACK wall  : ...
- LEFT wall  : ...
- RIGHT wall : ...
- CENTRE     : ...
- FRONT      : ...

Identity comes from <what actually makes the room read as this room>.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor
layout (~1-2 min); phase 2 dresses the surfaces; phase 3 adds walls/glazing/lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("<RoomType>", seed=N)

# ---- pinned assets (gate-3 audit: every mesh eyeballed on a contact sheet) ----
HERO = "future/<id>"      # <why this one, and what the caption got wrong>

scene.prefetch_assets([...])

# ---- <the hero unit: name the group after its job, not its contents> ----
hero = scene.AddAsset("<query>", asset_id=HERO)
with scene.RelativeGroup() as unit:
    unit.set_anchor(hero)                 # place_on_top seats items on the ANCHOR
    if PHASE >= 2:
        unit.place_on_top(scene.AddAsset("<prop>"))

scene.place_on_back_wall_center(unit)

if PHASE >= 3:
    scene.place_walls(...)
    scene.place_door(...)
    scene.add_lighting("<a SINGULAR light>", density=...)   # N = 1 + (max-1)*density

scene.export("<name>_v1.blend")
```

**The phase contract** — an agent driving this through the 9-gate flow depends on it:

| Phase | Builds | Why it is separate |
|---|---|---|
| 1 | floor anchors only | cheap (~1–2 min); catches layout/scale errors before you pay for dressing |
| 2 | surface + floor detail (`place_on_top`, rugs, props) | the identity layer — the massed product that names the room |
| 3 | walls, glazing, ceiling, lighting, door | the mood layer; a *subtractive* room (prison_cell, operating_room) deliberately leaves it thin |

A `place_on_top` gated **outside** its `with` block never runs — the count still increments,
the loop stays clean, and the prop is simply GONE. Gate inside the block.
