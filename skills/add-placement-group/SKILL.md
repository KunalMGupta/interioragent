---
name: add-placement-group
description: >
  Use when asked to add a new placement group / arrangement motif to IDSDL — whether a
  hand-written geometric motif (stack, ring, scatter, …) or an integration of an external 3D
  scene-generation repo (SceneMotifCoder, diffusion/transformer/CNN/LLM layout models). The new
  group goes ONLY in IDSDL/groups_extra.py (never touch core IDSDL logic) and MUST be validated
  both numerically (assertions) and visually (rendered top-down + perspective views).
---

# Skill: Add a placement group to IDSDL

This skill extends IDSDL with new placement groups **without changing any core logic**. A
placement group is a context-managed object that records `@placemethod` calls and, on
`compile()`, resolves them into concrete object poses and freezes into a reusable, nestable unit.

## Step 0 — Decide: do you actually need a new group? (think before you build)

Adding a group is the right move only when an arrangement is a **recurring, named relationship
that no existing group expresses** — not for a one-off layout you can hand-place. Work through:

1. **Name the relationship as a general motif, not a scene prop.** When the salon needed a mirror
   on the wall + a chair facing it + a counter under it, the insight was *not* "salons need
   this" — it was "a **wall-mirror-with-a-facing-floor-item** is a relationship the DSL can't
   express" (wall-mounting was RoomGroup-only; RelativeGroup is floor-only). That generalized
   immediately to **gym treadmill + mirror**, **vanity + mirror**, **dressing-room stations** →
   it earned a group: `MirrorStationGroup`.
2. **Try existing groups first.** Can `RelativeGroup` / `AroundGroup` / `GridGroup` /
   `place_on_wall_freeform` + creative facing already do it? (e.g. a *row of mirrors alone* needs
   no new group — `place_on_wall_freeform("back_wall", mirrors)` already spaces+scales N of them.)
   Only when you've confirmed the relationship is unrepresentable do you build.
3. **Design for several scenes, not one.** Give it **optional slots** so it covers a family of
   needs (MirrorStationGroup: required mirror + anchor, optional counter / floating shelf+decor /
   `place_beside` side-cart). A group that only fits one scene isn't worth the surface area.
4. **Then test thoroughly** (Step 0 is not done until §3–§4 pass): a numeric `tests.py` case **and**
   a rendered figure you eyeball, **plus** a second, different scene to prove generality (the
   salon styling station was re-validated as a bare gym treadmill+mirror station).

If the answer is "no new group," stop here and use an existing one creatively. See the worked
example in `skills/examples/hair_salon.md`.

> **Second worked precedent — `WorkstationGroup`** (desk + operator chair + monitor/computer +
> distributed desk accessories). The generalizable motif is **"an anchor with a seat in front and
> a set of items arranged ON its top surface at exact, semantic positions"** — a
> desk-with-a-screen-and-clutter that recurs in offices, reception counters, study desks and
> classroom desks. What it adds over a bare `place_on_top`: a **paired operator seat placed on the
> floor in front of the desk facing it** (a named desk↔chair relationship), plus the *pairing of a
> desk anchor with the right retriever pool* — the group is the reusable unit. **Crucial
> lesson (learned the hard way):** the on-top items MUST be seated with the DSL's own
> **`place_on_top`**, never a hand-computed `y = desk_height`. Seating at the desk's *aabb top*
> floats the monitor whenever that isn't the writing surface (a hutch desk, or a bbox inflated by
> baked-in props) — v1 did exactly this and the monitor/pen-cup/plant floated in mid-air while the
> lamp (which happened to be a desk prop) sat right. `place_on_top` uses the highest *substantial*
> surface (VLM tournament, AABB fallback) so items rest on the real desktop. It is reliable with
> **only a few items**, so the group **caps the desktop at 3** (computer + two accessories) and
> drops extras with a warning. Slots: `place_chair`, `place_computer` (faced at the operator after
> seating), `place_accessories([...])`; still warns if the desk is a tall hutch (prefer a flat one).
> It is paired with a retrieval mechanism, the **`DesktopWorkstationRetriever`** (curated pool
> `assets/desktop_workstation.json`), which supplies the on-top layer — monitors / all-in-one
> desktop **sets** (the dataset has no standalone keyboard/mouse; they come bundled in an iMac-style
> set), desk lamps, pen cups, desk plants, books, frames. Worked in `skills/examples/dental_office.md`.

> **Third worked precedent — `KitchenIslandGroup`** (island/peninsula attached to a fitted U/L/
> straight kitchen set), and the one to copy when a motif depends on the anchor's REAL SHAPE, not
> its AABB. The unrepresentable relationship: "attach the island at the frontal tip of a U's
> longer wing, across its mouth" / "float the island in the concave middle of an L" — every
> existing verb is AABB-relative, and the mouth/pocket of a U/L is *inside* the AABB. What it
> adds: a **mesh-footprint analysis stage** before layout — sample the anchor's surfaces, raster
> the base-height band into an occupancy grid, classify U/L/straight from border coverage, then
> compute the pose from measured wing tips / inner faces. Hard-won rules (all hit for real):
> 1. **Sample SURFACES, not vertices.** Vertices + centroids left big flat cabinet panels empty
>    at raster resolution and a U degraded to noise (misread as an L). Area-weighted triangle
>    sampling with a FIXED seed (deterministic builds) fixed it. Cap the grid ~48 cells across —
>    classification wants shape, not detail.
> 2. **Choose the base run by (most arms, longest span), not max coverage** — a U's own
>    full-length wing TIES its base run on coverage and the tiebreak decides correctly.
> 3. **Analyse in the base-height band** (y <= ~1.0 m) so bundled wall cabinets/hoods don't
>    pollute the floor footprint.
> 4. **Guard the composition, not just the math**: min_entry shrinks the island rather than seal
>    the U's mouth; stools that don't fit the (possibly shrunken) island are DROPPED with a print;
>    every analysis prints its ASCII raster + measurements so the choice is auditable in the log.
> 5. **Expose the analysis on the group** (`self.analysis`: shape/wing/mouth/entry/pocket) — the
>    numeric tests assert on it, and scene authors can audit it.
> 6. **Things inside the anchor's AABB need `ignore_overlap`** (the island is *supposed* to be in
>    the mouth), and the composed block is placed with ONE room corner op + `is_static = True` —
>    the group inherits the whole kitchen.md alignment/camera rulebook as a unit.
> 7. **A composed GridGroup anchor works** (the raster recurses children) **but only from
>    equal-depth modules** — a fridge composed into a cabinetry run rastered the back border
>    ragged AND pushed the run width past the interior-camera bound (W > 2 x run). Camera bounds
>    scale with whatever you compose; check them before composing.
> Slots: `place_island(island, mode="auto"|"tip"|"pocket"|"front", wing=, min_entry=, min_aisle=)`
> + `place_stools([...])`. The "island" can itself be a compiled sub-group (counter + its
> `add_lighting` pendant) — lights are `is_light` children, skipped by AABBs, so the entry-gap
> math still sees only the counter while the pendant rides along. Worked in
> `skills/examples/kitchen.md` (U peninsula: `kitchen_set_v3.py`; L pocket: `kitchen_l_v1.py`);
> numeric tests 52–53 in `tests.py`, figure `extra_kitchen_island` in `docs_figures.py`.

## Golden rules (do not break these)

1. **Never edit core files' logic.** `IDSDL/groups.py`, `IDSDL/object.py`, `IDSDL/constraints.py`
   are off-limits. All new group **classes** go in **`IDSDL/groups_extra.py`** (create it if
   missing).
2. The **only** allowed core touch is adding a one-line factory method to `SceneProgRoom` in
   `IDSDL/scene.py` (mirroring the existing `AroundGroup`/`GridGroup` factories) so the group works
   with the `with scene.XGroup() as g:` idiom. Nothing else in scene.py changes.
3. **Reuse, don't reinvent.** Build on existing primitives and inherit `compile()`. Do not write a
   new compile/optimization engine.
4. **Always verify twice**: a `tests.py` case with numeric assertions **and** a `docs_figures.py`
   render you actually inspect. A group is not "done" until both pass.

## What you can reuse (existing primitives)

Base classes (`from IDSDL.groups import AnchorGroup, AroundGroup`) and the decorator
(`from IDSDL.object import placemethod`). Pick the base by what you need from its inherited
`compile()`:

| Base | `compile()` behavior | Use for |
|---|---|---|
| `AnchorGroup` | runs `OverlapConstraint` + `ObjectProportionsConstraint`(VLM) + `grad_optimize`, then delayed `place_on_top`/`place_rug`/`add_lighting`, then freeze | most groups; **required if you want the overlap solver** to relax placements (e.g. a scatter/pile) |
| `AroundGroup` (subclass of AnchorGroup) | same, plus `sparsity` + radial circle/arc math | radial / ring motifs |
| `GridGroup` | deterministic — **no** solver | only if you explicitly want no optimization |

Primitives available on every object/group (all public, already used across IDSDL):
- Placement: `set_location(x,y,z)`, `set_rotation(deg)`, `face_towards(other)`, `translate`.
- Sizing: `scale_only_width/height/depth(v)`, `scale(target_width)`.
- Geometry: `get_aabb()`, `get_whd()`, `get_width/height/depth()`, `get_location()`, `get_rotation()`.
- Helpers: `self.to_list(x)`, `self.compute_obj_y(obj)` (returns the `y` that rests an object's
  **bottom** on a given base — pass `base + compute_obj_y(obj)`), `n * obj` (list of copies),
  `obj.copy()` (single copy), `obj.ignore_overlap = True`.
- Anchored groups: `set_anchor(obj)` then `get_anchor_center_dirs()` →
  `(front_dir, back_dir, left_dir, right_dir, center, w, h, d)`.
- `AroundGroup`/`RingsGroup`: `self.sparsity` (0 dense → 1 spread).

### Coordinate & orientation convention (get poses right!)
- Floor is the **XZ plane**, **Y is up**. Rotation is **degrees**, `0 = facing +Z (front)`.
- `facing_to_rotation`: front `0`, back `180`, left `-90`, right `90`.
- `set_anchor` rests the anchor on the floor; subsequent placements are relative to it.
- After `compile()`, `__exit__` calls `recenter()` (shifts the whole frozen group) — this preserves
  *relative* layout, so assert on relative quantities, not absolute coordinates.

### Key gotchas
- Objects that intentionally share a footprint (stacked / on-top / mirrored pairs you want kept
  exact) **must set `ignore_overlap = True`**, or `grad_optimize` will push them apart.
- Conversely, for a scatter/pile you **want** de-overlap: leave `ignore_overlap` off and let the
  inherited `AnchorGroup.compile` solver separate them (a deterministic `_snap_overlaps` pass
  guarantees no final overlap).
- Top-down renders are a poor angle for **vertical** motifs (stacks) — use perspective/front.
- `compile()` runs the VLM proportion check + Blender export, so it needs `OPENAI_API_KEY` and the
  `sceneprogexec`/Blender setup. The `results/` dir must exist for `.blend` export (`mkdir -p results`).

## Procedure

### 1. Implement the group in `IDSDL/groups_extra.py`
Thin subclass, only `@placemethod` methods, inherit `compile()`. Template:

```python
from IDSDL.object import placemethod
from IDSDL.groups import AnchorGroup

class MyMotifGroup(AnchorGroup):
    @placemethod
    def place_my_motif(self, objs, **params):
        objs = self.to_list(objs)
        # compute poses from existing primitives; for anchored motifs use:
        # _,_,_,_, center, w, h, d = self.get_anchor_center_dirs()
        for obj in objs:
            obj.set_location(x, self.compute_obj_y(obj), z)   # rest on floor at (x,z)
            obj.set_rotation(deg)        # or obj.face_towards(self.anchor)
            # obj.ignore_overlap = True  # only if items intentionally share footprint
            self.add_child(obj)
```

### 2. Add the factory to `IDSDL/scene.py` (only additive change allowed there)
Import the class with the others and add:
```python
def MyMotifGroup(self):
    return MyMotifGroup(self)
```

### 3. Numeric test in `tests.py`
Add a `test_NN()` that builds the group, `scene.bind(group)`, then **asserts geometry** (use
relative checks), and register it in the `TESTS` dict. Example assertions: stacked levels abut;
mirrored pair symmetric about anchor; pile has zero pairwise AABB overlap; ring radii ordered.

### 4. Render & visually verify with `docs_figures.py`
Add a `extra_<name>()` figure function and a `FIGURES` entry, render top-down + perspective, and
**open the PNGs to confirm** the layout looks right (not just that it ran).

### 5. Document it where the group will be FOUND
The living documentation is the skills tree, not `docs/` (`docs/motif-groups.md` no longer
exists): add the group as a worked-precedent blockquote at the top of THIS file, and teach its
use in the worked example (`skills/examples/<scene>.md`) of the scene that motivated it.

### Verification commands (conda env `interioragent`)
```bash
mkdir -p results
OPENAI_API_KEY=<key> conda run -n interioragent python tests.py <NN>
OPENAI_API_KEY=<key> conda run -n interioragent python docs_figures.py extra_<name>
python build_preview.py   # refresh the standalone docs preview
```
Then Read the rendered `docs/assets/scenes/extra_<name>_*.png` and confirm correctness.

## Integrating an external 3D-generation repo as a group

New groups need **not** be clever math — they can wrap an entire external repo (SceneMotifCoder,
ATISS/DiffuScene/PhyScene/InstructScene diffusion models, transformers, CNNs, LLM layout models).
IDSDL already supplies what these pair a layout with — retrieval (`AddAsset`) and geometry-aware
optimization (the inherited solver). Precedents to copy (out-of-process model calls):
`SceneMotifCoderObject` and `create_model` in `IDSDL/datasets/retrievers.py`, and `CurtainBuilder`
in `IDSDL/window.py`.

Procedure:
1. **Research** (extensive web search): find the repo + paper. Identify its **input** (text /
   room dims / object list / partial scene) and **output**. Most layout models emit a per-object
   record `{category, position, size, orientation}`; some emit a mesh.
2. **Vendor the repo out-of-process**: `git clone` it into `external/<repo>/` and add
   `external/` to `.gitignore` (never commit weights/large data). Create its own env per its README
   — **do not** pollute the `interioragent` env or core deps.
3. **Run inference out-of-process** (subprocess/shell script written to `tmp/`, or an HTTP
   endpoint), writing results to `tmp/`. Mirror the `SceneMotifCoderObject` shell-out pattern.
4. **Normalize** the output to IDSDL's world convention in the adapter: map axes/units, convert
   radians→degrees, and map dataset category labels → natural-language descriptions for `AddAsset`.
5. **Ingest in the group's `place_*` method**: for each record,
   `obj = self.scene.AddAsset(description)`, optional `scale_only_width/height/depth(...)` to match
   predicted size, `set_location(pos)`, `set_rotation(deg)`, `self.add_child(obj)`. The inherited
   `AnchorGroup.compile` then repairs plausibility (overlap/grad). The result is a normal IDSDL
   group: editable, nestable into a `RoomGroup`, exportable.
6. **Validate** exactly as above (numeric + render). Also add a **mock backend** path (deterministic,
   no weights) so the test runs without the heavy model installed.

## Done checklist
- [ ] New class only in `IDSDL/groups_extra.py`; core logic untouched.
- [ ] One-line factory added to `scene.py`; `with scene.XGroup() as g:` works.
- [ ] `tests.py` case with numeric assertions, registered in `TESTS`, passes.
- [ ] `docs_figures.py` figure rendered and visually inspected (top-down + perspective).
- [ ] Documented as a worked-precedent blockquote in this file + taught in the motivating
      scene's `skills/examples/<scene>.md`.
- [ ] (External repo) cloned under `external/` and git-ignored; runs out-of-process; output
      normalized to IDSDL conventions; a weight-free mock path exists for testing.
