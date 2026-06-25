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

### 5. Document it in `docs/motif-groups.md`
Add a section: short description, the `with scene.XGroup() as g:` snippet, and the two images.

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
- [ ] `docs/motif-groups.md` section added; `build_preview.py` regenerated.
- [ ] (External repo) cloned under `external/` and git-ignored; runs out-of-process; output
      normalized to IDSDL conventions; a weight-free mock path exists for testing.
