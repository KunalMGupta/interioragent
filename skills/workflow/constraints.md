---
id: workflow:constraints
kind: reference
role: "The 3-constraint-kind model and authoring rules"
---

# Constraints — the full model

Three mechanisms. They are not interchangeable. The DSL applies some for you;
others you must add; others only produce text you must act on.

> Companion: [`constraint_playbook.md`](constraint_playbook.md) — the other axis: given an
> ASSET or SITUATION, which constraint (and which numbers) to impose. DRAFT pending Kunal's
> review; its §5 is the open discussion agenda.

## 1. Auto gradient constraints — the DSL handles these

Instantiated automatically inside each group's `compile()` and solved by the
`GradSolver`, which **translates objects** to reduce violations. You never call
them and never tune them.

| Constraint | What it enforces | Added in |
|------------|------------------|----------|
| `OverlapConstraint` | objects don't interpenetrate (2D footprint) | every group's compile (GridGroup skips — deterministic layout) |
| `OutOfBoundsConstraint` | objects stay within group WIDTH/DEPTH | RoomGroup, BasicRoomGroup |
| **door clearance** (auto) | floor furniture is kept ~0.9 m clear of every doorway | RoomGroup, automatically per `place_door` |
| `CategoryClearanceConstraint` (auto) | functional clearance in front of counters/reception desks (0.9), display cases (0.75), cabinets/wardrobes/shelving (0.6), appliances (0.9), fireplaces (0.8), pianos (0.9) — matched by keywords in the asset description (for a composed group, its anchor's), each match expanding into a standard `ClearanceConstraint` | RoomGroup compile (any group can add it explicitly); table in `IDSDL/default_constraints.py`; disable with `RoomGroup(auto_clearances=False)` or `IDSDL_AUTO_CLEARANCES=0` |
| **wall-object clearance** (auto) | the wall surface occupied by every wall-HUNG object (art/mirror/clock/display) stays visible: floor furniture tall enough to occlude it (AABB top above the wall object's AABB bottom) inside a 0.75 m band is slid ALONG the wall out of the object's span; short furniture below it (a console under a painting) stays | RoomGroup, automatically per `place_on_wall_*` (`_enforce_wall_object_clearances`, deterministic post-solve — see below) |

> Grow the category table in `IDSDL/default_constraints.py` as new categories earn a
> rule — that file is the single list of "hardcoded" usage constraints. Note the door
> pass (and these) move **floor furniture only**: wall-hung items are exempt by design,
> so something that "blocks" a door in a render is usually a mis-hung wall item (see
> the deep-mesh wall-hang warning in dsl_reference.md).

Trust these. If two things overlap in the render anyway, the cause is usually
upstream (bad placement verb, an item that's a wall-object, or a group that
didn't recompile) — **or the room is simply too small** (see the overlap guarantee below).

### The overlap+bounds guarantee (`_settle`) and the too-small-room warning
After the gradient solve, the `GradSolver` runs two deterministic repair passes: `_snap_overlaps`
(push interpenetrating pairs apart) and `_clamp_to_bounds` (pull out-of-bounds items back in). These
two **fight each other** in a tight room — separating a pair can shove one object out of the room, and
clamping it back in can push it into a neighbour. Running snap-once-then-clamp-once could therefore
*end on an overlap the clamp had just created* (this actually shipped two dining tables interpenetrating).
Fixed: `GradSolver._settle()` **alternates** snap↔clamp until both hold (and always ends with a clamp,
so the final layout is guaranteed in-bounds). In a room big enough for its furniture this converges to
zero overlaps; in a genuinely **too-small** room it can't, and `RoomGroup._warn_overlaps()` (a final
post-compile check, mirroring `_warn_over_height`) prints + records in `scene.vlm_feedback`:
`[RoomGroup] WARNING: N pair(s) of floor objects still OVERLAP … the room is likely TOO SMALL`. A
residual overlap is almost always a size problem — **fix it by enlarging the room** (raise
`RoomGroup(modulate_scale=…)`) or removing/shrinking furniture, not by fighting the solver.

### Door clearance is automatic — you do nothing

Every `room.place_door(wall, position)` now **auto-keeps the doorway clear** so a person can
walk through and the door can swing. Two layers, both automatic:
1. **In-solve nudge** — on compile the RoomGroup drops an invisible, static floor proxy at
   the doorway (facing into the room, `ignore_overlap=True`, never rendered/exported) and runs
   the same `ClearanceConstraint` (`distance=RoomGroup.DOOR_CLEARANCE`, default 0.9 m,
   `dir="front"`) you'd add by hand, so the gradient solve moves furniture out as it settles.
2. **Deterministic guarantee** — after the solve, `_enforce_door_clearances()` moves any
   item still intruding into the doorway band and repairs resulting overlaps (the same
   belt-and-suspenders pattern as `_snap_overlaps`/`_clamp_to_bounds`). Wall-FLUSH furniture
   on the door's own wall (a cabinet run, a locker spine) **slides ALONG the wall** out of
   the doorway span — pushing it along the normal would strand it floating mid-room (the
   corridor bug, 2026-07-12); everything else is pushed out along the inward wall normal.
   This is needed because the area-weighted solver moves large/heavy furniture (a sofa)
   slowly, so the nudge alone can leave a big piece in the doorway.

   > The band and the leaf are guaranteed to AGREE: wall meshes are centered by **bbox
   > midpoint** on translate (`SceneProgObjectWall.translate`). They used to center by
   > vertex MEAN, so the door glb (dense hinge-side geometry, mean ~0.18 m off center)
   > landed offset from the partition center the clearance band is computed from —
   > furniture could sit "legally" outside the band while visibly covering the leaf.

No author action, no new constraint type. **Do not** add your own clearance for a door; just
place the door. Wall-mounted items and the door leaf itself are unaffected — only floor
furniture moves. (Caveat: a doorway is a no-furniture zone ~0.9 m deep × door-width wide — so
don't *design* a layout that needs that floor; put the door where the traffic lane already is.)

### Wall-object clearance is automatic — hung art stays visible (added 2026-07-12, Kunal's ask)

Every wall-HUNG placement (`place_on_wall_*`: art, mirrors, clocks, displays) now keeps
its patch of wall visible. After the wall ops execute, `_enforce_wall_object_clearances()`
takes each wall object's **AABB** and slides away any floor object that would occlude it —
one that (a) overlaps the object's along-wall span, (b) stands inside the
`WALL_OBJECT_CLEARANCE` band (0.75 m) in front of that wall, and (c) is **tall enough to
block it** (its AABB top rises above the wall object's AABB bottom). Three deliberate
design points:

- **Deterministic-only, no in-solve proxy** (unlike the doorway's two layers): wall-hung
  ops execute *after* the gradient solve, so the object's final AABB doesn't exist during
  the solve — there is nothing for a gradient to aim at.
- **The push is ALONG the wall, sideways** — never perpendicular. Wall-adjacent furniture
  is re-pinned flush to its wall every compile (`_repin_wall_furniture`), so a
  perpendicular push would be undone; a sideways slide survives and reads natural (the
  wardrobe ends up *beside* the painting). Overlaps/OOB introduced by a slide are
  repaired by `_settle()` and the doorway guarantee re-runs afterwards.
- **The height filter keeps legal compositions legal**: a low console/cabinet *under* a
  painting is untouched (its top is below the art's bottom edge). Only genuine occluders
  move.

If neither along-wall direction can clear the span (wall is full), it does not force it —
you get a `[RoomGroup] WARNING: '<obj>' occludes wall-hung '<art>' …` line and should move
one of them to a different wall/slot yourself. Worked example: hospital_room v1's tall
wardrobe slid off the front-wall botanical print.

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

### Clearance recipe — wardrobes, cabinets, appliances (you add these)

Anything with a door/drawer that opens, or that you stand in front of to use, needs a
clear band in front of it — **doors are auto-handled, everything else is on you:**

```python
with scene.RoomGroup() as room:
    room.place_on_back_wall_center(wardrobe)          # faces +z (into room) by default
    room.add_clearance(wardrobe, distance=0.8, dir="front")   # keep the swing/standing zone open
    room.place_on_left_wall_center(fridge)            # faces +x (into room)
    room.add_clearance(fridge, distance=0.9, dir="front")
```

- `dir="front"` is what you want almost always — it clears the space the doors open
  into / you stand in. It uses the object's **facing**, so make sure the wardrobe faces
  into the room (the wall placements do this by default; verify with the RotationConstraint
  render if unsure).
- Rough distances: wardrobe/closet **0.8–1.0 m**, kitchen appliances **0.9 m** (appliance
  + a person), dresser/low cabinet **0.6 m**, desk knee space **0.5 m**.
- `dir="sides"` / `dir="all"` exist but are rarely needed — reach for `front` first.

> **Clearance is a SOFT gradient — it can be overpowered; for a *guaranteed* gap between two
> specific pieces, use geometry instead.** `ClearanceConstraint` pushes the object and the nearest
> object apart, but competes with every other gradient (especially the `OverlapConstraint` of things
> right next to the target). When another object is jammed against the piece you're clearing, the two
> forces reach a weak equilibrium and the gap comes out far short of `distance`. Worked example (bar,
> 2026-07-05): `add_clearance(backbar, distance=0.5, dir="front")` to open a bartender aisle between the
> back-bar and the counter delivered only **~0.16 m** (verified by reading `get_aabb()` z-spans on an
> `auto_render=False` build) because the **stool row** overlapping the front of the counter pushed back;
> raising `distance` just fought the same tug-of-war. **Fix:** compose the two pieces in ONE rigid group
> with an explicit-gap placement — `RelativeGroup.place_on_back(backbar)` bakes a fixed `FRONT_BACK_GAP`
> (0.45 m) the solver can't collapse, then place the whole station. Rule of thumb: **clearance for
> "keep floor roughly open" (doors, standing room); geometric composition for "these two must sit N m
> apart."** (Latent quirk: for an axis-aligned object both `is_aligned_zpos` and `is_aligned_zneg`
> return true, so the constraint's `if/elif` never reaches the `zneg` branch — an object rotated 180°
> clears the wrong side.)
- The clearance **moves the blocker, not the cabinet**: the cabinet is wall-anchored and
  effectively pinned; the floor item in front gets pushed away. If two cabinets face each
  other across a narrow room the solve can fight itself — widen the room (`modulate_scale`)
  or drop one clearance.

### Visibility — keep it axis-aligned and use floor children (you add these)

`room.add_visibility(viewer, target)` keeps the sightline from `viewer` to `target` clear
by pushing **other floor objects** out of the trapezoid between them. To use it *properly*
(it is sharp-edged):

1. **`viewer` and `target` must both be floor objects the group can see** — direct floor
   children (or leaves of a nested cluster that the room flattens). A **wall-mounted** item
   (`place_on_wall_*`: art, a TV on a bracket, a board) is a *wall object*, **not** a group
   child — the solver can't reason about it as a target. For "keep the painting visible,"
   the thing you actually keep clear is the **floor in front of the wall** — put the viewer
   (sofa/bench) opposite the art and let blockers be pushed aside; or hang the focal piece
   on a floor console (a TV on a media unit) and target that.
2. **Keep `viewer → target` roughly axis-aligned** (along +x/−x/+z/−z). The sightline
   trapezoid is only defined for near-axis-aligned pairs; a diagonal pair is now a **silent
   no-op** (it used to raise and abort the whole scene). So if visibility "does nothing,"
   the usual cause is a diagonal or near-diagonal arrangement — line the two up on a row/column.
3. The blockers it moves are the group's other floor children; `ignore_overlap` items and
   wall objects are skipped. It will **not** separate two items locked inside the same frozen
   cluster (they move as a unit) — put the viewer and the blocker in the *room*, not nested.

Canonical good use: `sofa` on one wall, `media_console` opposite, both centred on the same
column → `room.add_visibility(sofa, media_console)` keeps the coffee table out of the line.

### place_inside / place_on_top tile clamp — items can't exceed their cell

The smart-placement solver (`tools/planar_regions.py`) tiles each detected surface/interior region
into cells and drops one item per cell. It sizes each item by **height** (LLM relative-height) with a
footprint cap taken against the **largest** region — which for a multi-compartment piece (a cubby, a
bookcase) is far bigger than the small cell an item actually lands in, so items **overflowed** their
compartments (the children's-room baskets bulged out of the cubbies). Fixed: `build_candidate` now
**uniformly clamps every item's WxD to its assigned tile** (`TILE_FOOTPRINT_FRAC = 0.9`, a margin so
it doesn't touch the cell walls) before placing it. It's a no-op for a normal tabletop (tile ≥ item),
and applies to both `place_inside` and `place_on_top`. If a `place_inside` item still looks too big,
suspect region detection (compartments merged into one region), not the sizing.

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

### Wall overlap is your job to resolve (the warning is text-only)

`WallOverlapConstraint` renders the walls and flags wall items that collide — with each
other or with a window/door opening. It **does not move anything**; resolving it is the
scene author's responsibility. The collisions come from the wall-slot occupancy model:
each wall has **three slots** (`left` / `center` / `right`), and every wall fixture, window,
and **door** registers the slot(s) it occupies. Two things in the same wall+slot overlap.

> Items in DIFFERENT slots can no longer overlap geometrically: `_place_on_wall` clamps
> every wall-hung piece's span (shrink + center-clamp) to its named slot's third of the
> wall (2026-07-12). Before that, a support-anchored piece (a mirror over a console)
> inherited its support's SOLVE-DRIFTED position unclamped, so it could invade the
> neighbouring slot and overlap art there while the slot model — and the VLM check —
> reported no collision (the corridor mirror-over-painting bug).

How to resolve a flagged overlap:
- **Different slot.** Move one item to a free slot — `place_on_wall_back_left` instead of
  `..._center`, etc. Check what's already there: a door on `front-center` means no wall art
  on `front-center`; a floor-to-ceiling window claims **all three** slots of its wall.
- **Different wall.** If a wall is full (e.g. door + window already), hang the art elsewhere.
- **Multiple items on one wall span.** Use `place_on_wall_freeform(wall, [a, b, c])` to lay
  several pieces along one wall without slot collisions, instead of stacking them in one slot.
- **Floor furniture vs wall-hung.** `place_on_<wall>_wall_<pos>` (floor item *against* the
  wall) and `place_on_wall_<wall>_<pos>` (item mounted *on* the wall) occupy independently —
  a console against the back wall and a picture above it is fine; two pictures in `back-center`
  is not.

Re-run after the fix and confirm the warning is gone before sign-off.

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
- Doorway blocked by furniture? → **already automatic** (`place_door` registers clearance);
  don't add your own. If something still sits in the doorway it's a wall object or a frozen
  cluster, not a free floor item.
- Cabinet/wardrobe/appliance door swing or standing space? → add a **manual** `add_clearance`
  (`dir="front"`, ~0.6–1.0 m).
- Need reach / sightline? → add a **manual** `add_access` / `add_visibility` (keep the
  visibility pair axis-aligned and both floor objects).
- Two wall items / a picture over a door overlapping? → **WallOverlap** (VLM text); move one
  to a free wall slot or use `place_on_wall_freeform` — the solver won't fix it.
- "Feels too big / small", "sofa dwarfs the table"? → **VLM** feedback; rescale in
  the program yourself and recompile.
- Object facing the wrong way (chair sideways to the group, desk drawers away from
  its chair)? → `RotationConstraint` (VLM); fix with `group.face()`/`group.rotate()`.
