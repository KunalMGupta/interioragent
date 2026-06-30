# DSL reference (IDSDL)

How to actually write a scene program. Distilled from the DSL source; treat the
source as ground truth if something here drifts. Verified examples: `test.py`
(living room), `tests.py` (per-feature unit scenes), `docs_figures.py`.

## Coordinate system

- DSL floor is the **XZ plane**, **Y is up**. (Export converts to Blender Z-up.)
- In a `RoomGroup`: **back wall = +Y(depth)**, **front wall = −**, **right = +X**,
  **left = −X**. `facing` values: `"front" | "back" | "left" | "right"`.
- Windowed walls (`place_window_floor_to_ceiling`) are **removed** from the
  scene's solid walls on export — that wall opening is why interior renders exist.

## Scene object

```python
from IDSDL.scene import SceneProgRoom
scene = SceneProgRoom("LivingRoom", seed=42)   # seed makes asset retrieval reproducible
...
scene.export("out.blend")                       # runs Blender; writes the .blend
```

Per run, the scene owns a unique scratchpad `scene.run_dir = tmp/<timestamp>_<pid>_<rand>/`.
All renders/intermediate meshes go there. `scene.vlm_feedback` accumulates VLM text.

## Assets

```python
obj = scene.AddAsset("a modern gray sofa")               # natural-language retrieval
obj = scene.AddAsset("a small end table", modulate_scale=0.3)   # scale the whole asset
obj = scene.AddAsset("a bookshelf", width=1.2, depth=0.4)        # pin specific dims (meters)
pair = 2 * scene.AddAsset("an accent chair")             # N*asset -> list of N copies
obj = scene.AddAsset("a desk", asset_id="hssd/<id>")     # pin a specific asset (override)
```

`AddAsset(description, modulate_scale=1.0, width=None, depth=None, asset_id=None)`.
The description is the retrieval query — be specific (style, material, color, type).

**Agentic retrieval (visual).** Retrieval shortlists candidates by embedding similarity
and a VLM picks the best by **looking** at each candidate's preview render (not just its
text description) — this is what stops "a small desk lamp" coming back as a whole
workstation. Every asset records its provenance: `obj.retrieval_query`,
`obj.retrieval_candidates` (each `{model, path, scale, preview, desc, similarity, chosen}`),
`obj.retrieval_model`. To **override** a pick: pass `asset_id="hssd/<id>"` (durable,
recompile-safe) or `scene.reselect_asset(obj, i_or_model)` (post-hoc swap, then recompile).
Inspect candidates with `python workbench.py inspect "<query>" [--render]` (the `--render`
flag renders the top finalists in-engine for a closer look).

## Groups

Groups are spatial-composition abstractions. Use them as context managers; the
group **compiles on `__exit__`** (runs layout + constraints). A group can be an
anchor placed inside another group — that is how you build hierarchy.

### RelativeGroup — place things relative to an anchor

```python
with scene.RelativeGroup() as g:
    g.set_anchor(sofa)
    g.place_on_front_left(side_table_group)
    g.place_on_back_left(floor_lamp)
```
Placement verbs (all relative to the anchor's faces):
`place_on_left/right/front/back`, `*_adjacent` (touching), `*_further` (with gap),
diagonal `place_on_front_left/front_right/back_left/back_right` and their
`_further` variants.

### AroundGroup — arrange objects around a central anchor

```python
with scene.AroundGroup(sparsity=0.2, jitter=0.4) as g:
    g.set_anchor(table)
    g.place_arc(2 * scene.AddAsset("an accent chair"))   # arc on one side
    # also: g.place_circle(objs), g.place_rectilinear(...)
```
`AroundGroup(sparsity=0.0, jitter=0.0)`. **`jitter` (0–1) adds real-world irregularity** —
each seat is nudged off its perfect position (≤25% of its own size) and rotation (±12° at
1.0). The anchor group's `OverlapConstraint` + grad solve still run afterward, so jitter
never produces interpenetration. Use it so ringed seating (dining/meeting/cafe) reads as
lived-in rather than CAD-perfect. Reproducible under a seeded scene (see Randomness below).

### GridGroup — regular rows/grids (deterministic; skips overlap optimization)

```python
with scene.GridGroup(sparsity=0.5, randomness=0.3) as g:
    g.place_grid(9 * desk_unit, cols=3)     # also place_row, place_rectilinear, place_arc
```
`GridGroup(sparsity=0.0, randomness=0.0)`. `sparsity` sets the gap between items;
**`randomness` (0–1) jitters those gaps** so rows aren't unnaturally even. (Now seeded —
reproducible per scene seed.)

### Shared anchor-group helpers (Relative/Around)

```python
g.place_on_top(obj)                       # stack on the anchor's top surface
g.place_rug("a gray wool rug", size=0.8)  # rug under the group
g.add_lighting("a chandelier", density=0) # ceiling light(s); density=0 -> single central
```
These three run *last* in compile (after layout), so they sit correctly.

`place_on_top` (and `place_inside`, for cabinet/shelf interiors) seat the object(s) on
the anchor. Each has **two paths**:

- **Primary — VLM-tournament placement** (`IDSDL/vlm_placement.py`): renders candidate
  arrangements of the items on/in the anchor and runs a VLM value-iteration tournament
  (`tools/planar_regions.py:solve_placement`) to pick the best, then applies the winning
  transforms. Catches surface structure the AABB path can't (a real top vs. a raised lip,
  a shelf bay vs. solid body). **Heavy** — needs Blender + GPU + `OPENAI_API_KEY`; disable
  globally with `IDSDL_SMART_PLACEMENT=0`. Any failure (no API key, anchor isn't a single
  mesh, items lack `mesh_path`) silently falls through to:
- **Fallback — deterministic AABB layout**: rows the items across the anchor's top (or
  interior mid-height) and **proportions** each to the anchor first — a mis-scaled
  retrieval (a "small desk lamp" that comes back huge) is uniformly shrunk to satisfy hard
  caps: footprint ≤ a share of the anchor top (`ON_TOP_FOOTPRINT_FRACTION`, 0.5, split
  across N), height ≤ **0.4× the anchor height** (`ON_TOP_HEIGHT_FRACTION`), and the
  **combined anchor+object stack ≤ 3.5 m** (`ON_TOP_MAX_COMBINED_HEIGHT`). Never up-scaled;
  the three caps are `AnchorGroup` class constants.

Both paths flag the items `ignore_overlap` and add them as children — the DSL call site is
identical either way.

**Post-placement orientation (opt-in).** Placement bakes a fixed rotation into
each object, which is often wrong for orientation-sensitive cases. Available on
**every group** (anchor groups *and* RoomGroup); defaults unchanged — reorient
only when you ask:
```python
# anchor group: default target = the anchor
g.face(chair, toward=coffee_table)  # turn chair to face a target
g.face(chair)                       # toward the group's anchor
g.rotate(desk, 180)                 # absolute angle override (degrees)

# RoomGroup: target an object OR a wall name (wall = 90°-snapped, the right tool
# for functional orientation like a desk grid facing the teaching wall)
room.face(student_desk_grid, toward="front_wall")   # "front/back/left/right_wall"
room.face(teacher_area, toward="back_wall")
```
Applied at the **end of compile**, after layout settles, so facing is computed
from final positions. The `RotationConstraint` (VLM) flags mis-orientations — but
it's a noisy hint, not an authority; **your eye is the arbiter** (see
workflow/vlm_feedback.md).

**Desk+chair rule — use `place_desk_chair(desk, chair)`** (RelativeGroup). It anchors the
desk, puts the chair on the **back**, and **rotates the desk 180°** so its working front
(knee-hole/drawers) faces the chair. Every dataset desk is modeled with its front at +z, so
this fixed rotation gives the correct pose for *any* desk (student/teacher/reception) — no
per-asset front cache needed. (`gap=True` leaves circulation space behind the desk.)

**Asset front is unnormalized** — meshes have no canonical front, so some render
rotated wrong even with correct `face()`. Fix an asset **once** (not per scene) with
the front cache: `python -m IDSDL.front_cache set <asset-id> <0|90|180|270>`. See
workflow/constraints.md.

### RoomGroup — the room shell + wall/floor placement

```python
with scene.RoomGroup(randomness=0.2) as room:         # RoomGroup(modulate_scale=1.0, randomness=0.0, auto_render=True)
    room.place_walls(floor_texture="wooden planks",
                     ceiling_texture="beige", wall_texture="beige")
    room.place_on_center(seating_area, facing="front") # floor placement, sizes the room
    room.place_on_back_right_corner(large_plant)
    room.place_on_right_wall_center(cabinet)           # furniture against a wall
    room.place_on_wall_left_center(painting)           # hung ON the wall (art)
    room.place_door("left_wall", position="right")
    room.place_window_floor_to_ceiling("back_wall", curtain="light gray sheer curtains")
```
RoomGroup auto-sizes WIDTH/DEPTH from what you place. The room is the only group
that renders **interior** views (`auto_render=True` → `render_interior()` on compile;
also `render_interior_combined()` for the 4-view strip the VLM uses).

Floor placement: `place_on_center/back/front/left/right`, `*_left/right`, and
`*_corner` variants — all take optional `facing`. Wall-adjacent furniture:
`place_on_<wall>_wall_<pos>`. Wall-hung art: `place_on_wall_<wall>_<pos>`.
Openings: `place_door(wall, position)`, `place_window_floor_to_ceiling`,
`place_window_picture`, `place_window_standard(wall, position, curtain)`.

## Randomness / realism (jitter)

Perfectly-centered, perfectly-aligned layouts read as synthetic. Three opt-in knobs add
controlled irregularity, all **reproducible**: a seeded scene (`SceneProgRoom(name, seed=...)`)
gives every group its own RNG derived from the seed, so the same seed reproduces the same
jittered layout; an unseeded scene re-rolls each run.

| Group | Param | Effect |
|-------|-------|--------|
| `AroundGroup(jitter=0–1)` | per-seat | position offset (≤25% of the object's size) + rotation (±12° at 1.0) on `place_circle`/`place_arc`/`place_rectilinear` |
| `RoomGroup(randomness=0–1)` | free-standing floor placements | position jitter within the **free space of each item's layout slot** (translation only — facing is preserved, so a desk grid still faces its wall) |
| `GridGroup(randomness=0–1)` | row/grid gaps | jitters the inter-item gaps (needs `sparsity>0` to have gaps to jitter) |

Safe by construction: AroundGroup and RoomGroup run their overlap/out-of-bounds gradient
solve *after* the jitter, so nothing ends up interpenetrating or out of the room. GridGroup
is deterministic (no solve), so keep its `randomness` modest. Good defaults: seating
`jitter≈0.4`, rooms `randomness≈0.15–0.3`, grids `randomness≈0.2–0.4`.

## Constraints (see workflow/constraints.md for the full model)

- **Auto** (you do nothing): `OverlapConstraint`, `OutOfBoundsConstraint`, and
  **door clearance** — every `place_door` auto-registers a `ClearanceConstraint`
  (~0.9 m) at the doorway, so floor furniture is kept out of the way. Don't add your
  own clearance for a door.
- **Manual gradient** (you add, they move objects): add them *inside* the group's
  `with` block via the native convenience methods (available on every group).
  `compile()` (on `__exit__`) re-runs them after the auto constraints and before
  the gradient solve, so they're enforced like the auto ones:
  ```python
  with scene.RoomGroup() as room:
      sofa = scene.AddAsset("a sofa"); tv = scene.AddAsset("a tv")
      room.place_on_center(seating, facing="front")
      room.add_clearance(sofa, distance=0.6, dir="front")  # keep front clear
      room.add_access(desk, chair, dir="front")            # chair within reach of desk
      room.add_visibility(sofa, tv)                        # keep the sofa→tv sightline clear
  ```
  Methods (each registers a hook; returns self):
  - `add_clearance(obj, distance=0.5, dir="front"|"sides"|"all", omit_objs=None)` → `ClearanceConstraint`
  - `add_access(obj, target, min_dist=0.1, max_dist=0.15, dir="front"|"sides")` → `AccessConstraint`
  - `add_visibility(source, target)` → `VisibilityConstraint`
  - low-level escape hatch: `add_constraint_hook(lambda g: g.SomeConstraint(...))`
  > The objects you reference must belong to the group you add the hook to (the
  > constraint operates on that group's members). `GridGroup` is deterministic and
  > runs no gradient solve, so hooks there have no effect — add manual constraints
  > on a Relative/Around/Room group.
- **VLM** (auto-run, text only): `ObjectProportionsConstraint` + `RotationConstraint`
  (anchor groups), `RoomProportionsConstraint` + `WallOverlapConstraint` (RoomGroup).
  They append rescale/rotation/feedback text to `scene.vlm_feedback`. Nothing moves
  automatically — act via the program (rescale, `face()`/`rotate()`, reposition).

## Export

`scene.export("out.blend")` serializes all assets, walls, lights and packs
textures into a self-contained `.blend` (runs Blender as a subprocess).
