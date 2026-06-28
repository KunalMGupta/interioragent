# Constraints — the full model

Three mechanisms. They are not interchangeable. The DSL applies some for you;
others you must add; others only produce text you must act on.

## 1. Auto gradient constraints — the DSL handles these

Instantiated automatically inside each group's `compile()` and solved by the
`GradSolver`, which **translates objects** to reduce violations. You never call
them and never tune them.

| Constraint | What it enforces | Added in |
|------------|------------------|----------|
| `OverlapConstraint` | objects don't interpenetrate (2D footprint) | every group's compile (GridGroup skips — deterministic layout) |
| `OutOfBoundsConstraint` | objects stay within group WIDTH/DEPTH | RoomGroup, BasicRoomGroup |

Trust these. If two things overlap in the render anyway, the cause is usually
upstream (bad placement verb, an item that's a wall-object, or a group that
didn't recompile) — not the solver.

## 2. Manual gradient constraints — you add these, they move objects

These take arguments (which object, how far, which direction) so they cannot be
auto-instantiated — you add them deliberately where real usage demands it. They
are `GRADIENT` type, so once registered the `GradSolver` enforces them by moving
objects, just like the auto ones.

| Constraint | Signature | Use when |
|------------|-----------|----------|
| `ClearanceConstraint` | `(obj, distance=0.5, dir="front"\|"sides"\|"all", omit_objs=None)` | keep a span clear in front of / around something — wardrobe & cabinet door swing, sofa front, appliance fronts |
| `AccessConstraint` | `(obj, target, min_dist=0.1, max_dist=0.15, dir="front"\|"sides")` | keep a target within reach of an anchor — nightstand beside bed, chair tucked to desk |
| `VisibilityConstraint` | `(source, target)` | keep a sightline clear — sofa → TV, seating → focal point |

### How to register them

Add them inside the group's `with` block with the native convenience methods —
they work on every grad-optimizing group (Relative/Around/Room/BasicRoom):

```python
with scene.RoomGroup() as room:
    room.place_on_center(seating, facing="front")
    room.add_clearance(sofa, distance=0.6, dir="front")
    room.add_access(desk, chair, dir="front")
    room.add_visibility(sofa, tv)
```

Mechanics: `compile()` clears constraints, adds the auto ones, then re-runs your
registered hooks, then solves — so manual constraints are enforced every compile
(and survive recompiles). Low-level form:
`room.add_constraint_hook(lambda g: g.ClearanceConstraint(sofa, distance=0.6, dir="front"))`.

> Caveats: the referenced objects must belong to the group you add the hook to.
> `GridGroup` runs no gradient solve, so hooks there do nothing — put manual
> constraints on a Relative/Around/Room group. (The older `tests.py`
> `ConstraintRoom(hooks=[...])` harness still works but is no longer needed.)

## 3. VLM constraints — auto-run, but only produce text

`VLM` type. They render the group, ask an LLM to judge it, and **append the
answer to `scene.vlm_feedback`**. The `VLMSolver` does *not* move or rescale
anything — it is write-only. Acting on the feedback is your job (edit the
program, recompile).

| Constraint | Runs in | Renders | Asks for |
|------------|---------|---------|----------|
| `ObjectProportionsConstraint` | anchor groups (Relative/Around) | exterior 4-view of the group | per-object `rescale <x> by 0.1–0.9`, or `no rescale` |
| `RotationConstraint` | anchor groups **and RoomGroup** | exterior 4-view (open groups) / **interior** 4-view (RoomGroup) | per-object rotation fix (`rotate <x> to face <y>` / `rotate <x> by 180`), or `no rotation` |
| `RoomProportionsConstraint` | RoomGroup | **interior** 4-view (`render_interior_combined`) + occupancy ratio | `rescale room by 0.5–2.0`, or `no rescale` |
| `WallOverlapConstraint` | RoomGroup | wall views | wall items overlapping each other / openings |

Act on `RotationConstraint` with the opt-in orientation controls:
`group.face(obj, toward=...)` (default = anchor; for RoomGroup pass an object or a
wall name like `"front_wall"`, which snaps to 90°) or `group.rotate(obj, degrees)`,
added inside the group's `with` block. They apply after layout settles, so the
re-check sees the corrected orientation.

### Asset front-orientation is unnormalized (systemic — read this)

Dataset assets carry **no canonical front** — each mesh is authored facing an
arbitrary direction, while all the DSL rotation logic assumes front = +z. So some
assets render rotated wrong even when your `face()`/`facing=` is correct. `RotationConstraint`
is a useful (if noisy) detector.

> **Desks are solved structurally** — don't cache them. Every dataset desk is modeled
> front-at-+z, and `place_desk_chair(desk, chair)` (RelativeGroup) rotates the desk 180°
> against the seat, giving the correct pose for any desk. Use that, not a per-desk cache.

For a genuinely reversed *non-desk* asset, fix it **once per asset** with the
front-correction cache, not per scene:

```bash
# find the asset id (mesh filename stem) — e.g. print obj.mesh_path — then:
python -m IDSDL.front_cache set <asset-id-or-mesh-path> <degrees>   # 0/90/180/270
python -m IDSDL.front_cache list
```

The correction is keyed by asset id, applied at load time on the serialized
rotation only (`SceneProgObject.get_state_info`), so the DSL geometry stays
canonical and **every future scene using that mesh is fixed automatically**. Use a
per-scene `room.rotate(obj, deg)` only for true one-offs; for a reversed *asset*,
cache it. (Desks are the exception — handle them with `place_desk_chair`, above.)

The workbench surfaces `scene.vlm_feedback` after a run. See
[vlm_feedback.md](vlm_feedback.md) for how to turn that text into edits.

### Why VLM feedback is "text only"

By design, for now: the VLM suggests, you decide. It avoids a recompile loop
that silently rescales things you intended. The recommended loop is human/agent-
in-the-loop: read feedback → judge against the render and the plan → apply the
change you agree with → recompile.

## Decision cheat-sheet

- Objects overlapping / leaving the room? → auto gradient already handles it; if
  not, the placement is wrong, not the solver.
- Need physical clearance / reach / sightline? → add a **manual** constraint (hook).
- "Feels too big / small", "sofa dwarfs the table"? → **VLM** feedback; rescale in
  the program yourself and recompile.
- Object facing the wrong way (chair sideways to the group, desk drawers away from
  its chair)? → `RotationConstraint` (VLM); fix with `group.face()`/`group.rotate()`.
