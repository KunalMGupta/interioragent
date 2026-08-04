# DSL reference (IDSDL)

How to actually write a scene program. Distilled from the DSL source; treat the
source as ground truth if something here drifts. Verified examples: `tests.py`
(per-feature unit scenes), `tools/docs_figures.py`, and the worked programs in
`skills/examples/*_v1.py`.

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

**`acquire=` — what to do when the DATASET cannot serve an asset query.** Default `"low"`: take
the dataset's best hit, however wrong. That is usually right, and it is always reproducible — but
below a top-1 similarity of ~0.55 the "best hit" stops being the thing you asked for and nothing
downstream ever says so ("a chemistry fume hood" resolves to a kitchen chimney hood; "a hospital
defibrillator" to a wheelchair). Raise the dial and the retriever fills a MEASURED gap itself:

```python
scene = SceneProgRoom("Chapel", seed=3, acquire="mid")   # search Sketchfab for real gaps
scene = SceneProgRoom("Lab",    seed=3, acquire="high")  # ...and GENERATE (Meshy) if the web has none
```

`mid` is free but slow (minutes per gap); `high` spends Meshy credits. Both try the dataset first
and only engage on a measured gap, an acquisition that fails to close its gap is rolled back out
of the library, and a failure always falls back to the old behaviour — the scene still builds.
Full rules: [acquire-assets/SKILL.md](acquire-assets/SKILL.md).

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

**Scaling an object** (after `AddAsset`, before placement):
```python
obj.scale(0.9)                # UNIFORM scale so WIDTH = 0.9 m (aspect preserved)
obj.scale_only_height(1.5)    # single-axis (distorts aspect); also _width / _depth
w, h, d = obj.get_whd()       # measure native dims OFFLINE (no network) before choosing a target
```
`scale(w)` sets the width in metres and scales relative to the asset's current (often
pre-normalised, non-1.0) scale — so it is reliable regardless of how the mesh shipped. To scale
by a factor: `obj.scale(obj.get_width()*f)`. **To hit a target HEIGHT uniformly** (useful for
fixtures whose native proportions vary — shelves, cabinets): `obj.scale(obj.get_width()*H/obj.get_height())`.

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
  a shelf bay vs. solid body).
  - **Surface (`on_top`)**: only the real TOP is used — `top_surfaces()` returns the *highest
    substantial* horizontal region (≥ 50% of the max region area), **not** the largest-area
    one. (`detect_horizontal_regions` sorts by area, and a nightstand/dresser's biggest region
    is often a low internal shelf — picking it sinks the item into the body.)
  - **Sizing**: each item is height-fit to a fraction of the base height chosen by an LLM given
    the **real base + item dimensions** (not just text), then an **N-aware** footprint cap (a
    single item is barely capped; N items share the surface width). So decor is realistic — a
    lamp on a short nightstand stays ~0.5–0.7 m, not shrunk to a sliver.
  - **Heavy** — needs Blender + GPU + `OPENAI_API_KEY`. Any failure (no key, anchor isn't a
    single mesh, items lack `mesh_path`) silently falls through to:
  - **HARD RULE — never disable the tournament for speed.** `IDSDL_SMART_PLACEMENT=0` exists
    ONLY for environments genuinely lacking Blender/GPU/API; it is *not* a render-time
    optimization. `place_on_top` being heavy is core DSL behaviour — accept the slower render.
- **Fallback — deterministic AABB layout**: rows the items across the anchor's top (or
  interior mid-height) and **proportions** each to the anchor first — a mis-scaled
  retrieval (a "small desk lamp" that comes back huge) is uniformly shrunk to satisfy hard
  caps: footprint ≤ a share of the anchor top (`ON_TOP_FOOTPRINT_FRACTION`, 0.5, split
  across N), height ≤ **0.4× the anchor height** (`ON_TOP_HEIGHT_FRACTION`), and the
  **combined anchor+object stack ≤ 3.5 m** (`ON_TOP_MAX_COMBINED_HEIGHT`). Never up-scaled;
  the three caps are `AnchorGroup` class constants.

Both paths flag the items `ignore_overlap` and add them as children — the DSL call site is
identical either way.

**Gotcha — `place_on_top` breaks on FLAT anchors (a rug, a pallet).** The surface-region tiler
computes a near-zero tile size and shatters the top into thousands of microscopic tiles, shrinking
the placed items to a few cm (seen: a flat rug → 0.029 m tiles → 7396 tiles → bean bags at ~3 cm).
For **floor seating / a rug-grounded cluster**, don't stack onto the rug — place the items as FLOOR
objects (anchor group's `place_on_left/right/front/back`) and add the rug under them with `place_rug`.

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

**Auto-size mechanics — room size is a consequence of slot occupancy.** Floor
placements land in a 3×3 slot grid; the shell grows until the widest slot-ROW and
deepest slot-COLUMN fit their occupants. So a small/cozy room = few occupied slots
(4-5) with modest hero widths; occupying all nine slots, or dropping one wide
multi-cluster composed group into a single slot, forces a cavernous shell that no
decor can fill (the coffee-shop lesson). `modulate_scale` only scales that computed
size — it cannot rescue a footprint the placements dictate, and raising it above 1.0
to dodge overlaps just inflates the room (shrink/remove furniture instead).
The same applies per WALL: many separate items queued along one wall (or one
direction) stretch that whole axis to fit the queue — cap a wall at ~2–3 items
unless it's a deliberate hero run, and spread the rest (see the "don't overload
a single wall" rule in workflow/coarse_to_fine.md; hospital_room lesson).

Floor placement: `place_on_center/back/front/left/right`, `*_left/right`, and
`*_corner` variants — all take optional `facing`. Wall-adjacent furniture:
`place_on_<wall>_wall_<pos>`. Wall-hung art: `place_on_wall_<wall>_<pos>`.

**Wall-hung = FLAT only.** `place_on_wall_*` hangs the mesh at art height; a mesh
deeper than ~0.25 m (shelving, a veneer panel, any cabinet) renders as furniture
FLOATING in mid-air. The DSL now warns (print + `scene.vlm_feedback`) when a deep
mesh is hung — fix by using `place_on_<wall>_wall_<pos>` (floor, against the wall)
or pinning a genuinely thin canvas/mirror/board mesh.

**Mounting a DEEP mesh UP the wall (a range hood, upper cabinets, a wall-hung TV
unit).** Some fixtures are genuinely deep AND genuinely up the wall — `place_on_wall_*`
floats them, and leaving them out guts the scene (a kitchen without its hood fails the
reads-as test). Use the wall-ADJACENT path with the **`bottom=` lift**, available on
every `place_on_<wall>_wall_<pos>`: `room.place_on_back_wall_center(hood, bottom=1.55)`.
Two things then bite, because that path registers the piece as **floor furniture**:
```python
hood.ignore_overlap = True   # else the 2D-footprint OverlapConstraint sees the hood and
                             # the range BENEATH it as interpenetrating and shoves them
                             # apart along the wall (skipped by the gradient,
                             # _snap_overlaps, _clamp_to_bounds and _warn_overlaps)
hood.is_static = True        # else the GradSolver's exploration floor (max(grad·dir,0.01)
                             # * free_space / area) random-walks a small-footprint piece
                             # along the wall — the living_room_cozy fireplace drift
```
`_repin_wall_furniture` still snaps it flush and **preserves the Y lift** (it translates
in x/z only). If several such pieces must line up over a run, mount them as ONE
`GridGroup` row in the **same wall slot as the run below** — a wall's `left`/`right`
slots are thirds of the WALL, not of your run, so separately-slotted uppers hang out
past the run's ends over bare floor. Worked example: [examples/kitchen.md](examples/kitchen.md).

Openings: `place_door(wall, position)`, `place_window_floor_to_ceiling`,
`place_window_picture`, `place_window_standard(wall, position, curtain)`.

**Windows show DAYLIGHT — glaze freely (fixed 2026-07-12, greenhouse).** Older examples warn that
any opening renders as a "black night void" and prescribe workarounds (small panes only, a foreground
object to mask the void, all-black wall renders are "camera artifacts"). **That was a bug and it is
fixed** — interior views rendered with a *transparent film*, so a ray that hit no geometry (through an
opening, or above the hidden ceiling) wrote alpha 0 and flattened to black; the same bug is why
ceilings rendered black. Interior views are now opaque-film with a raised sky
(`renderer/utils.py`: `INTERIOR_SKY_STRENGTH`, override per build with `IDSDL_SKY`). Treat those
workarounds as obsolete. See [examples/greenhouse.md](examples/greenhouse.md).

**Brightness is a SKY setting, never an `add_lighting` setting.** `add_lighting` spends a **fixed
500 W split across N fixtures** (`object.py`: `per_light_energy = 500.0 / max(1, N)`), so raising
`density` buys *more, dimmer* fixtures and can never make a room brighter. For a "bright"/"sunlit"
brief, glaze a wall and let the sky in; for a deliberately dim room, build with `IDSDL_SKY=0.7`.

**`facing` — leave it OFF for wall furniture (the default already faces the room).** `facing` names
the direction the asset points. For `place_on_<wall>_wall_*`, **omitting `facing`** applies the
correct default from `fill_facing_heuristic`: a wall asset faces the **opposite** direction — *into
the room* (back-wall→`front`, front-wall→`back`, left-wall→`right`, right-wall→`left`), so its access
side (locker doors, sink, cubby openings) is reachable. **Do NOT pass `facing=<the wall's own name>`**
(`place_on_left_wall_center(v, facing="left")`) — that turns the asset to face the wall it stands
against and denies access (the locker-room bug: the VLM flagged "rotate vanity to face center").
Override `facing` only for a genuinely non-default pose. (Asset mesh fronts are *unnormalized*, so if
one still renders backwards under the default, fix it once with the front cache — see below — not with
a per-scene facing hack.)

## Randomness / realism (jitter)

Perfectly-centered, perfectly-aligned layouts read as synthetic. **Every group** takes two
opt-in knobs — a spacing knob (`sparsity=0–1`) and a perturbation knob (`jitter=0–1`;
`randomness` on GridGroup/RoomGroup) — all **reproducible**: a seeded scene
(`SceneProgRoom(name, seed=...)`) gives every group its own RNG derived from the seed, so
the same seed reproduces the same jittered layout; an unseeded scene re-rolls each run.
At the 0.0 defaults every layout is exactly the legacy deterministic one.

| Group | sparsity | jitter |
|-------|----------|--------|
| `AroundGroup` | standoff from the anchor | per-seat offset (≤25% of the object's size) + ±12° on `place_circle`/`place_arc`/`place_rectilinear` |
| `RingsGroup` | radial standoff **and** ring-to-ring separation | as AroundGroup |
| `GridGroup(randomness=)` | row/grid gaps | jitters inter-item gaps (works even at `sparsity=0`) |
| `RoomGroup(randomness=)` | — | floor items drift within the **free space of their own slot** (translation only — facing preserved) |
| `RelativeGroup` | scales the side/front/circulation gaps of every directional slot (and the `_further` ring stays consistent) | in-slot slide (clamped to half the gap, so "left" stays left) + ±10° off the slot pose |
| `StackGroup` | vertical gap between levels | upper levels slide within the footprint below + ±8° (bottom level stays put) |
| `PyramidGroup` | in-tier spacing | in-slot slide + ±6°; tiers stay centered and seated |
| `PileGroup` | widens the scatter disk | accepted but inert — a pile is already maximal randomness |
| `SymmetryGroup` | gap from the anchor | one draw per pair applied **mirrored** to both twins — the pair stays exactly symmetric |
| `FacingGroup` | in-row spacing + row standoff | per-seat slide/push in the row's local frame + ±10° off dead-facing |
| `MirrorStationGroup` | chair↔counter and beside gaps | shelf decor drifts in its slot + anchor turns ±10°; the mirror/counter wall chain stays rigid |
| `WorkstationGroup` | chair gap from the desk | chair slides along the desk, tucks/pushes back, ±20°; the desk and desktop items stay put |
| `KitchenIslandGroup` | stool gap from the island | stools only: in-slot slide + ±15°; the island keeps its audited entry/aisle pose |

Groups that run a gradient solve (Around, Relative, Pile, Room) relax any overlap the jitter
introduces. The rigid motifs (Stack, Pyramid, Symmetry, Facing, MirrorStation, KitchenIsland)
apply jitter *final* — their clamps are sized so the arrangement stays intact, but keep their
`jitter` moderate. Good defaults: seating `jitter≈0.4`, rooms `randomness≈0.15–0.3`, grids
`randomness≈0.2–0.4`, rigid motifs `jitter≈0.3`.

## Constraints (see workflow/constraints.md for the full model)

- **Auto** (you do nothing): `OverlapConstraint`, `OutOfBoundsConstraint`,
  **door clearance** — every `place_door` auto-registers a `ClearanceConstraint`
  (~0.9 m) at the doorway, so floor furniture is kept out of the way (don't add your
  own clearance for a door) — and `CategoryClearanceConstraint`: counters/display
  cases/cabinets/appliances/fireplaces/pianos automatically get their functional
  front clearance from the table in `IDSDL/default_constraints.py`, matched on the
  asset's description (for a composed group, its anchor chain's). Disable per room
  with `RoomGroup(auto_clearances=False)`. Also **wall-object clearance** — every
  `place_on_wall_*` object keeps its wall patch visible: floor furniture tall enough
  to occlude it (AABB top above the object's AABB bottom, within a 0.75 m band) is
  slid along the wall out of its span post-solve; a console below a painting stays.
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
  - `add_clearance(obj, distance=0.5, dir="front"|"sides"|"all"|"front_back"|"front_sides", omit_objs=None)` → `ClearanceConstraint` (`front_back` = front+behind, e.g. a treadmill mount/dismount; `front_sides` = front+left+right, e.g. a reception desk queue+walk-around)
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

## Phases & lints (iterative verification)

- **Phase-gate your program** (`IDSDL/phases.py`): `PHASE = current_phase()` at the
  top (defaults to 3 = everything), then `if PHASE >= 2:` around surface dressing
  (place_on_top/place_inside) and `if PHASE >= 3:` around wall art/windows/lighting/
  mood. `workbench run <p>.py --phase 1` then builds just the floor layout (~1–2 min)
  for a cheap layout check. Later phases only ADD — never move phase-1 geometry.
  Canonical gated program: `skills/examples/coffee_shop_v1.py`.
- **Static lint** (`workbench lint <p>.py`, MCP `lint_program`): validates every
  method call + keyword against the real DSL surface in milliseconds — catches
  invented verbs (`place_on_left_adjacent`) and kwargs (`add_lighting(asset_id=…)`)
  before a build. `workbench run` lints first and refuses to build on errors.
- **Compile lints** (`IDSDL/lints.py`, auto): floor objects floating/sunk (AABB
  bottom off y=0 — usual cause: off-center mesh origin, SWAP the mesh), lighting
  starfield (fixture count far over the room's area budget), and **embedded wall
  objects** (below) are flagged as `[Lint]` lines in `scene.vlm_feedback`/the report.
  Keep them clean per phase; disable with `IDSDL_LINTS=0`.
- **`[Lint] … is EMBEDDED IN …` — the overlap solver's BLIND SPOT.** Every overlap
  check in the room is 2D-footprint *and* drops `ignore_overlap` items
  (`GradSolver.overlap_pairs` filters them by construction), so an object you mark
  `ignore_overlap` — which you MUST do for anything mounted with `bottom=`, or the 2D
  solver shoves the shelf and the cabinet under it apart — becomes invisible to every
  overlap pass, and a floor cabinet can end up **inside** it with nothing complaining.
  `lint_embedded_wall_objects` closes that hole: a full **3D** AABB test (a shelf ABOVE
  a console stays legal) over exactly the pairs the solver refuses to look at.
  There is no auto-fix — act in the program: move one to a different wall slot, change
  its `bottom=`, or shrink it. **Why this bites: wall furniture is placed at
  `row_centers[1..3]`, and the row centres are sized by each row's FLOOR occupants, not
  by the wall items — so the gap between two adjacent wall slots can be SMALLER than the
  two wall items sitting in them need.** Three long items on one wall is an arithmetic
  to check ((wᵢ + wⱼ)/2 ≤ the row-centre pitch), never a slot count to assume.

## Export

`scene.export("out.blend")` serializes all assets, walls, lights and packs
textures into a self-contained `.blend` (runs Blender as a subprocess).
