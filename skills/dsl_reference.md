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
```

`AddAsset(description, modulate_scale=1.0, width=None, depth=None)`. The
description is the retrieval query — be specific (style, material, color, type).

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
with scene.AroundGroup() as g:
    g.set_anchor(table)
    g.place_arc(2 * scene.AddAsset("an accent chair"))   # arc on one side
    # also: g.place_circle(objs), g.place_rectilinear(...)
```
`AroundGroup(sparsity=0.0)`.

### GridGroup — regular rows/grids (deterministic; skips overlap optimization)

```python
with scene.GridGroup() as g:
    g.place_grid(9 * desk_unit, cols=3)     # also place_row, place_rectilinear, place_arc
```
`GridGroup(sparsity=0.0, randomness=0.0)`.

### Shared anchor-group helpers (Relative/Around)

```python
g.place_on_top(obj)                       # stack on the anchor's top surface
g.place_rug("a gray wool rug", size=0.8)  # rug under the group
g.add_lighting("a chandelier", density=0) # ceiling light(s); density=0 -> single central
```
These three run *last* in compile (after layout), so they sit correctly.

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

**Seat-behind-desk convention:** for a desk+seat unit, put the seat on the **back**
of the desk (`place_on_back_adjacent`), so the unit's look-direction is correct.

**Asset front is unnormalized** — meshes have no canonical front, so some render
rotated wrong even with correct `face()`. Fix an asset **once** (not per scene) with
the front cache: `python -m IDSDL.front_cache set <asset-id> <0|90|180|270>`. See
workflow/constraints.md.

### RoomGroup — the room shell + wall/floor placement

```python
with scene.RoomGroup() as room:                       # RoomGroup(modulate_scale=1.0, auto_render=True)
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

## Constraints (see workflow/constraints.md for the full model)

- **Auto** (you do nothing): `OverlapConstraint`, `OutOfBoundsConstraint`.
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
