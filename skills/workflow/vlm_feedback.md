# Acting on VLM feedback

VLM constraints only emit text (see [constraints.md](constraints.md)). This file
is how we turn that text into program edits. It is the most important file to
grow: every scene, we add the concrete feedback→action decisions we made and
*why*. Over time this becomes our judgment, written down.

> When building a scene, ask the user how to act on each new/ambiguous piece of
> VLM feedback rather than guessing. Record the answer here.

## The raw signals

- **ObjectProportionsConstraint** → `rescale <object> by <0.1–0.9>` or `no rescale`.
  Always a *shrink* factor; it never asks to enlarge.
- **RoomProportionsConstraint** → `rescale room by <0.5–2.0>` or `no rescale`,
  informed by the occupancy ratio (target ~0.4).
- **RotationConstraint** → per-object rotation fixes (`rotate <obj> to face <y>` /
  `rotate <obj> by 180`) or `no rotation`. Catches seating that faces sideways/away
  from the group, desks/consoles whose front is flipped from their chair, and (at
  the **room** level, via the interior render) a desk/seat grid facing away from the
  teacher/front. Runs on anchor groups and on RoomGroup. Fix with `face()`/`rotate()`
  on the same group (RoomGroup needs an explicit `toward=`).
- **WallOverlapConstraint** → free-text about wall items overlapping each other
  or doors/windows.
- **`[Lint]` lines** (deterministic, `IDSDL/lints.py` — not a VLM) → floor objects
  floating/sunk off y=0 and lighting starfields. Unlike the VLM signals these are
  computed facts, not judgements: treat them as MUST-FIX (or explain why not),
  never as noise to decline. Also `[RoomGroup] WARNING:` lines (residual overlaps
  = room too small; over-height; deep wall-hung mesh) — same standing.

## How to act (default heuristics — refine these as we learn)

1. **Read the render first, then the feedback.** The text is a hint, not a
   command. If the render looks right, a rescale suggestion can be declined.
   Trust your eyes over a borderline number.
2. **Object rescale:** apply by editing that asset's `modulate_scale` (or
   `width`/`depth`) in the program, then recompile. Prefer one decisive change
   over many tiny ones.
3. **Room rescale:** the VLM judges by occupancy ratio. <0.4 (empty/spacious) →
   it suggests shrinking; >0.4 (cramped) → enlarging. Decide whether the *layout*
   or the *room size* is the real problem before resizing the room — often the
   fix is adding/removing furniture, not rescaling the shell.
   **Rule (set 2026-06-27): render wins in early phases.** Do NOT resize the room
   shell in Phase 1–2. Occupancy is still rising as you add furniture, so an early
   "enlarge"/"shrink" is judged against an unfinished room. Trust the render, hold
   the size, and only act on `RoomProportions` rescale in the **final phase**, once
   all furniture is placed. Apply via `RoomGroup(modulate_scale=<factor>)`.
   **Rule (set 2026-07-05): a `modulate_scale < 1.0` shrink is UNSAFE on a
   furniture-packed room.** RoomGroup auto-sizes WIDTH/DEPTH to *fit* the furniture at
   1.0; a value below 1.0 shrinks the shell **below** that footprint, so fixed-size
   rows (a locker spine, a bench row) overflow their grid slots and the overlap solver
   can't undo it — you get benches punching into a wall vanity, corner props buried in a
   wall row. If the VLM keeps asking to shrink a room that is already wall-loaded, that
   is occupancy noise: **ignore it, hold `modulate_scale=1.0`**, and if it truly feels
   empty add furniture. Only shrink below 1.0 for a genuinely sparse room. (Locker-room
   lesson — the "rescale room by 0.8" that caused the overlaps.)
4. **Wall overlap:** move one item to a different wall slot (`*_left/center/right`)
   or a different wall; don't shrink art to dodge an overlap.
4b. **Rotation:** apply `group.face(obj, toward=...)` (default = anchor) or
   `group.rotate(obj, degrees)` inside the group's `with` block, then recompile.
   For conversation seating, face each chair toward the central table/anchor; for a
   desk-and-chair, face the desk toward its chair (or `rotate(desk, 180)`). These are
   opt-in and applied after layout, so a re-check sees the corrected orientation.
5. **Converge, don't chase.** Apply a change, recompile, re-read. If feedback
   oscillates (shrink ↔ grow) or contradicts a clearly-good render, stop and keep
   the better version. "no rescale" / empty feedback = done for that constraint.
6. **One phase at a time.** Resolve proportion feedback in Phase 1 before adding
   detail; resolve wall-overlap feedback in Phase 3.

## Rotation: don't trust the VLM for it — use deterministic structure (revised 2026-06-27)

**Superseded the earlier "room-level governs" rule — it was wrong.** On classroom v1
the room-level `RotationConstraint` said `no rotation` on a scene that was actually
mis-oriented (students looking away from the teacher), while the per-unit check
*correctly* flagged "rotate desk by 180" and we wrongly dismissed it. Lesson: **the VLM
rotation check (either level) is unreliable for functional orientation. Treat it as a
weak smoke alarm, not an authority — your own look at the render is the arbiter.**

For orientation that *matters functionally*, don't rely on VLM feedback at all — make it
correct by construction:

1. **Desk+chair rule — `place_desk_chair(desk, chair)`.** For any desk+seat unit (student,
   teacher, reception, office) it puts the seat on the **back** and rotates the desk 180°
   so the desk's working front faces the chair. All dataset desks are modeled front-at-+z,
   so this single rule gives the correct pose for every desk with no per-asset front cache.
   (Don't hand-roll `place_on_back_adjacent` + a manual flip; use the helper.)
2. **Face the wall, not the point, for required orientation.** When a group must face a
   certain way (a desk grid facing the teaching wall), use
   `room.face(group, toward="<wall>_wall")` — it snaps to the nearest 90°, so rows stay
   orthogonal. Reserve `face(obj, toward=<object>)` (arbitrary angle) for genuinely
   non-orthogonal one-offs. Both are deterministic and re-applied every compile.

So: structure + wall-facing for anything that matters; `face()`/`rotate()` to act on a
rotation issue you can *see*; the VLM rotation text is just a hint.

## Open questions to resolve with the user (then delete once answered)

- When ObjectProportions and the render disagree, which wins, and by how much
  margin do we trust the VLM? (partial: see room-rescale rule — render wins early.)
- Should repeated "no rescale" across a phase be the formal gate to advance?

## Decision log (append per scene)

> Format: **[scene] feedback → action → result.** Keep these concrete.

- **[living_room v1]** `RoomProportions` drifted as occupancy rose:
  Phase 1 `1.2` (enlarge) → Phase 2 `0.92` → Phase 3 `0.9` (shrink); ObjectProportions
  `no rescale` and WallOverlap clean throughout. → **Held the size in phases 1–2**
  (render looked fine; occupancy still climbing — the flip from enlarge to shrink
  confirmed early suggestions were premature). In the **final phase** applied the
  `0.9` via `RoomGroup(modulate_scale=0.9)`; recompiled → RoomProportions returned
  `no rescale`. Outcome: clean convergence, cozier room. This is the worked example
  behind the "render wins early; act on room size in the final phase" rule.
- **[living_room v1, orientation]** The two flanking accent chairs were placed with
  `place_on_front_left/right_further`, which bake ±90° → chairs faced sideways, not
  the coffee table. → Added `seating.face(chair, toward=coffee)` for both. After
  recompile the chairs angled in (proper conversation U) and `RotationConstraint`
  returned `no rotation`. Lesson: `*_further`/side placements orient sideways by
  default — face seating at the cluster anchor explicitly.
- **[dental_office v1, room size]** `rescale room by 0.8` (Ph1) → `0.85` (Ph2). → **Held
  in Ph1–2**, applied `RoomGroup(modulate_scale=0.85)` in the final phase → `no rescale`.
  Same "render wins early; act on room size last" outcome as living_room.
- **[dental_office v1, rotation]** Every phase emitted `rotate dental unit / stool / cart
  by 180 / to face the operator`. → **Declined all** — the render read correctly from all
  four corners and a reclining dental unit has no meaningful "front." Reinforces: the
  `RotationConstraint` is a weak smoke alarm; the render is the arbiter.
- **[dental_office v1, wall overlap]** `front_wall slot 'right' has Door + Window` — the
  **picture window spans wide** and collided with the door. → Swapped
  `place_window_picture` → `place_window_standard("front_wall", position="left")` (single
  slot) → `no wall overlap`. Lesson: `place_window_picture` takes **no `position` and spans
  wide**; on a wall that also holds a door, use `place_window_standard` with an explicit
  non-conflicting slot.
- **[bar/lounge, lighting]** `add_lighting("a row of warm pendant lights", density=0.4)` over the bar
  produced a **cloud of ~30 globes**. Cause: the retrieved mesh for a *plural* query was already a
  cluster of globes, and `add_lighting` copies that mesh `N = 1 + (max_lights-1)*density` times. → Fix
  in two parts: (1) query a **SINGULAR** fixture ("a warm brass globe pendant light") so each copy is one
  globe; (2) **lower density** (0.5→0.2) — the count spreads across the *group footprint*, and an
  anchor group that includes the stool depth fans the globes forward into the room, so a low count keeps
  a tight cluster over the counter. Result: a clean ~4-6-globe row. General rule now in
  ../dsl_reference.md/examples: **for a countable row of pendants, query the fixture singular and keep
  density low; a plural query = a pre-clustered mesh = a cloud.** (`best_grid` squares the count, so a
  perfect 1×N row isn't achievable via density alone — low count is the only lever without a code change.)
- **[bar/lounge, room size]** RoomProportions drifted `0.9 → 0.8 → 0.95` across the three phases. Held
  the size in phases 1–2, applied `RoomGroup(modulate_scale=0.85)` in the final phase (chose 0.85 over
  the suggested 0.8 — a bar wants open circulation), re-check returned 0.95 ≈ converged. Same rule as
  living_room. And the recurring **"rotate velvet tub chair to face the coffee table"** on a `place_circle(2)`
  2-top was **declined as noise** — the render showed correct across-table seating (RotationConstraint =
  weak smoke alarm).
- **[casino v1, room size]** Final `RoomProportions` = `rescale room by 1.05` (occupancy a hair over the
  0.4 target) with `no rescale`/`no rotation`/`no wall overlap` everywhere else. → **Declined the 1.05** —
  a ~5% enlarge is within noise and the render read well-filled at `modulate_scale=1.0`. Render wins /
  converge-don't-chase; a full re-render for an imperceptible size change isn't worth it.
- **[casino v1, place_on_top]** `hub.place_on_top("a stack of colorful casino poker chips")` retrieved a
  **children's book display rack** (poker chips / playing cards / chip trays aren't in the dataset;
  "colorful … stack" matched a book rack) and it dominated the hero card table. Not a VLM-constraint
  signal — a *retrieval* failure caught by looking at the render. → **Removed the line** (the felt top
  reads fine bare); logged a chip tray as an ingest target. Lesson: only `place_on_top` a prop the dataset
  actually has — verify the pick in the render, never assume a small decorative object exists.
- **[computer_room v1, on-top orientation]** `place_on_top(monitor)` baked a fixed rotation → the 8
  monitors faced random ways and the VLM flagged `rotate monitor to face the chair` every compile. →
  Added `workstation.face(monitor, toward=chair)` on the single unit *before* `8 * workstation`, so all
  8 reorient identically. Recompile → `no rotation`. Lesson: any orientation-sensitive `place_on_top`
  item (monitor/TV/clock) needs an explicit `face()` — the tournament sizes/seats it but never aims it.
- **[computer_room v1, desk+chair]** VLM again emitted a false-positive `rotate desk 180 / rotate chair
  to face desk` on a `place_desk_chair` unit that was correct by construction (same as classroom). →
  Ignored; verified by eye. Confirms: **don't chase the VLM rotation hint on `place_desk_chair` units.**
- **[computer_room v1, texture]** floor came back **brown** for `"cool blue-grey anti-static vinyl
  flooring"` — texture strings embed against a fixed library and "anti-static vinyl" matched a wood
  texture. → Simplified to `"smooth cool grey concrete floor"` → correct grey. Lesson: texture strings
  are embedding-matched; drop jargon, use plain **color + material** words. A floor/wall rendering the
  wrong color is a wording fix, not a constraint.
- **[computer_room v1, retrieval gaps]** "computer desk" retrieved a **white marble console table** →
  pinned a flat-top white desk by id (`browse` → pick; reaffirms the flat-top rule). No **server rack**
  exists in the dataset (best ~0.48, generic industrial cabinets) → used a tall black perforated cabinet
  stand-in; and no **teal desk privacy screen** exists → omitted the plan's accent rather than force a
  wrong color. Both logged as asset-first ingest candidates. (v2: the stand-in was replaced by an
  **ingested** real server rack `custom/9f2a77c7…`.)
- **[computer_room v2, WorkstationGroup facing]** Rebuilt the stations on the reusable
  `WorkstationGroup` (operator side = local **+Z**). The same `face(stations, toward="front_wall")`
  that was correct for the v1 `place_desk_chair` grid now pointed all 8 operators **away** from the
  front display (screens' backs to the front wall). VLM `RotationConstraint` said `no rotation` in
  BOTH orientations — no help. → Flipped to `face(stations, toward="back_wall")`; the front-wall
  interior render then showed operator faces + screens facing them. Lesson: **a WorkstationGroup grid
  faces the OPPOSITE wall from a place_desk_chair grid — face it toward `back_wall` to seat users
  at the front — and confirm seating direction by eye (faces vs screen-backs), never via the VLM.**
- **[garage v1, room size]** RoomProportions drifted down `0.9` (Ph1) → `0.8` (Ph2). → **Held through
  phases 1–2** — the open floor in front of the car is the correct vehicle-door approach lane, not
  empty room — then applied `RoomGroup(modulate_scale=0.85)` in the final phase → `no rescale`. Same
  render-wins-early pattern; note a legitimate open circulation lane reads as "too big" to the VLM.
- **[garage v1, object proportions]** `rescale workbench by 0.5` (Ph1), but the render showed only a
  mild oversize. → Declined the aggressive 0.5; applied `modulate_scale=0.8` → Ph2/3 `no rescale`.
  Trust the render over a borderline shrink number (heuristic #1); one decisive moderate change.
- **[garage v1, car retrieval]** "car" has **no retriever/pool** and routes to the generic retriever,
  whose top hits are ~half TOY cars (best real-car sim ~0.44). → **Pinned a real car id** and passed
  `width=1.85` so it comes in at real scale instead of toy-sized; `place_on_center(car, facing="front")`
  then oriented it correctly with no front-cache. Lesson: for any uncurated hero (vehicles), pin the id
  AND pin a real-world dimension — retrieval scale alone can't be trusted for a gap category.
- **[children_room v1, room size]** `RoomProportions` `0.83` → `0.85` → `0.92` → `0.9` across phases.
  → Held early, applied `RoomGroup(modulate_scale=0.80)` in the final phase **and added a bean-bag** to
  fill the open play floor (better than over-shrinking a kids room that wants play space). Converged
  ~0.9, accepted. Same "render wins early; size last" rule, plus: fill floor before shrinking further.
- **[children_room v1, bad scale metadata]** A "large yellow bean bag" loaded at **0.15 m** (native
  mesh 0.92 m — the retriever `scale` is ~6x off) and rendered as a tiny blob. → `modulate_scale=5.0`
  (uniform). `width=` alone scales only X and **squashes it flat** — for a bad-scale asset use uniform
  `modulate_scale`, not a single-axis `width=`.
- **[children_room v1, wheeled "art"]** A "planets/stars" wall-art pick was a **wheeled easel/display**
  (0.26 m deep) that read as a standing frame on the wall. → Swapped for a genuinely FLAT canvas
  (`d ≈ 0.005 m`). Lesson: for `place_on_wall_*`, check the asset **depth** — a deep mesh is a stand/
  easel, not a print; pin a thin canvas and pre-scale it small.
- **[children_room v1, place_inside overflow]** Cubby baskets **overflowed** their compartments — the
  smart-placement footprint cap sized items vs. the *largest* region, not the cell they land in. →
  Code fix (`tools/planar_regions.py:build_candidate` now clamps each item's WxD to its tile,
  `TILE_FOOTPRINT_FRAC=0.9`). After: baskets sit inside the cubbies. See ../workflow/constraints.md.
- **[children_room v1, rotation]** `rotate desk by 180 / rotate chair to face the desk / rotate
  nightstand` emitted on a layout that reads correct in every render. → **Declined all** —
  `place_desk_chair` makes the desk pose correct by construction; the check is a weak smoke alarm.
- **[executive_office v1, LIGHTING — the big one]** `add_lighting("a brass sputnik chandelier …")`
  rendered as **giant white emissive globes hanging at head height in the middle of the room** AND
  **blew the whole scene out to pure white**. Cause (see `IDSDL/object.py::add_lighting`): the helper
  **caps a fixture's HEIGHT at 1.5 m but pins its origin at the ceiling**, so a *tall* fixture (a
  chandelier/pendant with long drop) hangs ~1.5 m down into the room; and its glowing globe *meshes*
  emit on top of the 500 W point-light budget → overexposure. → **Use a COMPACT flush fixture** (`"a
  flat round LED flush mount ceiling light"`): short, so it sits flush at the ceiling, and little
  emissive area, so the fixed budget lights evenly without blowing out. The **desk task lamp** carries
  the decorative/warm-light layer instead. Lesson (generalizable): **`add_lighting` wants a FLAT/FLUSH
  fixture, never a tall hanging chandelier — pick the fixture by its geometry (short + small emissive
  area), not by how pretty the catalog render is.** Complements the bar-scene "singular pendant + low
  density" rule. Also: **`density` is fixture COUNT, not brightness** (total wattage is fixed) — high
  density tiles the ceiling and, seen edge-on at the top of a frame, reads as a dithered black/white
  band; keep density ~0.2 for one calm room.
- **[executive_office v1, window = black void]** Same renderer limit as dental: any opening (window or
  floor-to-ceiling) shows a **black night void** (no exterior environment), and curtains render as
  parted opaque drapes with the void between them. → Used a **STANDARD (small) punched window**, not a
  wide `place_window_picture` — a smaller pane keeps the void modest — with light sheer curtains to
  frame it. Balanced (non-blown) room lighting also helps: the void only screamed when the walls were
  overexposed white. Lesson: **prefer `place_window_standard` over `place_window_picture` unless you
  truly want a wall of black; the void reads as "evening" once the room isn't blown out.**
- **[executive_office v1, WorkstationGroup facing — reconfirmed]** For a single executive desk I wanted
  the boss seated *behind* the desk facing the room/window (power layout). Operator side = local **+Z**
  and the chair faces the desk, so `room.place_on_center(station, facing="back")` (rotate the group
  180°) seats the executive on the bookcase side facing front. Verified by eye. Same "+Z operator,
  face the group at the OPPOSITE wall" rule as the computer_room grid.
- **[executive_office v1, converged rescale]** `RoomProportions` walked `0.8 (no change other view)` →
  `0.9` as I shrank `modulate_scale` 1.0 → 0.9 → 0.85. A vote that **decays toward neutral** as you act
  = converging; stopped at 0.85 on a well-proportioned render rather than chasing 0.8 forever. Also
  declined the perennial "rotate sofa to face the round [side] table" — a wall-backed lounge sofa
  should not pivot to face its own end table (noise, like the dental unit rotation).
- **[retail_store v1, lighting density scales with FLOOR AREA]** `add_lighting(..., density=0.3)` —
  perfectly calm in the small executive office — tiled **~40 flush discs into a dense ceiling grid**
  on the large retail floor. Dropped to **0.08** for a clean ~5. Refines the executive_office rule:
  `density` is a fixture COUNT *and the count grows with room footprint*, so a **big room wants a much
  lower density (~0.05–0.1)** than a small one for the same visual calm. (Still a FLUSH fixture — the
  chandelier ban stands.) When a ceiling reads as a grid/band of fixtures, cut density first.
- **[retail_store v1, storefront = worst-case black void]** `place_window_floor_to_ceiling("front_wall")`
  filled the ENTIRE front wall with a pure-black void (no exterior env) — the window-void limit at its
  worst because a storefront wall is huge. → `place_window_standard(position="center")` (a modest pane)
  + **staged the three mannequins in front of it as the "window display."** Now reads as an evening
  storefront. Lesson: **never full-height-glaze a wall you'll look at; a standard pane + a foreground
  object (mannequin/plant) turns the void into a backdrop.** Generalizes the executive_office window rule.
- **[retail_store v1, converged in 3]** render1 (void + 40-disc grid) → window+density fixes; render2
  one vote `rescale room by 0.9` (floor visibly empty) → applied `modulate_scale=0.9`, **declined**
  `rotate checkout counter/POS to face customer` (a back-wall cash-wrap facing into the store already
  faces approaching customers — ambiguous noise); render3 `no rescale / no rotation / no wall overlap`
  everywhere → stop. The single mild rescale vote acted-on-once + clean next render = the converge signal.
- **[jewelry_shop v1→v2, a shop reads by its PRODUCT, not its fixtures — the user caught what the
  VLM couldn't]** No velvet jewelry bust exists (~0.5 → decorative sculptures, recall ≠ quality, the
  florist trap). **v1 wrong move:** massed the strong *fixture* — glass display vitrines ×6 —
  assuming "cases = jewelry store." But the vitrine meshes are EMPTY (no jewelry modelled inside), so
  the room read as a **furniture showroom**, and 6 tall cabinets **congested** it. The VLM feedback
  loop went fully clean (it checks per-object geometry, NOT "does this look like a jewelry shop" or
  "is it crowded"), so I shipped it — and the **user** flagged both problems. **v2 fix:** a dedicated
  *jewelry-PROP* scan (the furniture stress test never surfaces "a diamond ring / a gem on a stand")
  found real props — gold hand-shaped stand, geode, agate-on-stand, cloche, jewelry boxes, display
  bust — **massed at viewing height** on a central display table + the cash-wrap + the window
  pedestals; cut vitrines 6→4; up-scaled 0.8→0.9. Lessons: (a) **to make a retail scene read as its
  category, put the PRODUCT on the display surfaces at eye level — an empty fixture names the fixture,
  not the shop**; (b) **the VLM loop converging is necessary but NOT sufficient — gut-check category
  legibility + crowding yourself**; (c) congestion is driven by TALL pieces blocking sightlines (cut
  those), not low displays.
- **[jewelry_shop v1, pin anything whose COLOUR carries the palette]** The accent armchair was left
  unpinned; retrieval **flipped it pink → emerald between two runs at the same seed=42** (the VLM
  pick is not deterministic). Because the jewel-tone palette leaned on it, pinned the emerald chair.
  Reinforces restaurant's "pin for palette, not just type": a fixed seed does NOT fix an unpinned
  pick's colour — pin it.
- **[jewelry_shop v1, converged in 2 via pattern reuse]** Copied the retail "central piece + perimeter
  loop + branded service wall" recipe (vitrines for rails, pedestals for mannequins) → render1 hit only
  the routine trio (`rescale room 0.8` empty floor + `rescale jewelry boxes 0.5` oversized + a
  `density=0.1` disc-band on a medium room → 0.05); render2 clean everywhere. Reusing a solved pattern
  collapses the feedback loop. Also refines lighting: even a MEDIUM room over-tiled at 0.1 → 0.05.
- **[coffee_shop v1, floating mesh with off-center origin]** The walnut storage bench
  (`hssd/66b84f2b…`) hovered ~0.6 m up when wall-placed; its self-reported AABB disagrees with
  its render geometry, so even an AABB-based floor-snap left it ~0.3 m off the floor (counter/
  back-bar/tables from the same build all rested fine). Dataset-mesh analogue of the ingest
  off-center-origin lesson. → **Swapped the mesh** (`hssd/a5faa788…` rests perfectly). Lesson:
  if ONE object floats while its neighbours rest, suspect that mesh's origin — verify in the
  exported blend (`bottom = loc_z - dims_z/2`), and swap rather than compensate.
- **[coffee_shop v0, lighting density on a SMALL room]** `add_lighting(flush, density=0.05)`
  — calm on nothing: it produced a ~26-fixture starfield on a café-sized room (count is
  `1+(max_lights-1)*density`). → **0.01 gave a clean 6.** Extends the retail area-scaling rule
  downward: small room ≈ 0.01-0.02, medium ≈ 0.05, and only genuinely big floors near 0.08.
- **[laundromat v1, room size — a SPARSE room may shrink below 1.0]** `RoomProportions`
  voted `0.7` (Ph1) → `0.8` (Ph2); held per render-wins-early. Applied
  `modulate_scale=0.85` in the final phase → the vote PERSISTED at `0.75` (the centre
  aisle was genuinely empty — 4 floor slots, small furniture). Took one more decisive
  shrink to **0.75** → `no rescale`. Refines the locker_room rule: "never shrink below
  1.0" applies to furniture-PACKED rooms (wall rows overflow their slots); a room that
  is genuinely sparse in the render CAN go well below 1.0 — expect a two-step
  final-phase convergence when the first application undershoots.
- **[laundromat v1, clean by construction]** `no rotation` / `no wall overlap` every
  phase: all three wall placements (machine row back / counter left / bench right)
  omitted `facing` (the heuristic faces the room), art hung over the LOW machine run
  (not a tall spine), window `standard` on a slot the door doesn't claim. Copying the
  worked-example defaults collapsed the feedback loop to a single room-size thread.
- **[hospital_room v1, half-scale hero mesh]** The pinned hospital bed rendered TOY-sized
  next to the armchairs. `get_whd()` (offline) showed native length 1.0 m vs a real
  ~2.1 m bed. → `modulate_scale=2.1` (UNIFORM — `width=` alone would squash the
  proportions; children_room bean-bag lesson) → true scale, IV arm at ~1.75 m.
  Reconfirms the garage-car rule: for any uncurated hero, pin the id AND verify a
  real-world dimension with `get_whd()` before the first build.
- **[hospital_room v1, floating vanity]** `[Lint] vanity FLOATS 0.14 m` on the first
  phase-1 build (off-center mesh origin, the coffee_shop bench failure class). →
  Swapped to a sibling pick from the same browse (`future/a521cb7a…`) → clean next
  build. Swap the mesh, never compensate with translate hacks in a v1.
- **[hospital_room v1, place_arc chairs]** `rotate left/right armchair to face the
  coffee table` — accepted (render agreed: the two `place_arc` visitor chairs sat
  angled away from their table). → `face(chair, toward=table)` on both inside the
  AroundGroup → `no rotation`. Same class as living_room's flanking chairs: arc/side
  placements orient sideways by default; aim seating at the cluster anchor explicitly.
- **[hospital_room v1, ONE overloaded wall inflates the room — the shrink vote can't fix it]**
  Wheelchair + wardrobe + vanity + med cart queued along the left wall → RoomGroup grew
  the depth to fit the queue; shrink votes (0.8→0.85→0.94) never truly converged and the
  USER called the room oversized (the VLM's occupancy metric can't localize *which wall*
  is the cause). → **Redistributed** (wardrobe → front wall) + `modulate_scale=0.75` →
  `no rescale`. General rule now in coarse_to_fine.md / dsl_reference.md: cap a wall at
  ~2–3 items unless it's a deliberate hero run; when a room "feels too big", check for a
  wall queue BEFORE reaching for modulate_scale.
- **[hospital_room v1, REVERSED-front vanity — user catch, VLM-invisible]** The sink
  vanity (`future/a521cb7a…`) rendered its blank back to the room under the correct
  default facing; every VLM pass said nothing (and later noise votes asked it to "face
  the BED", which is wrong anyway). Bad ASSET, not bad code → fixed once, durably, with
  `python -m IDSDL.front_cache set a521cb7a… 180` (constraints.md's prescribed path; a
  per-scene `facing=` hack would leak the bug into every other scene using this mesh).
  Reconfirms: eyeball each wall face in the render yourself — orientation of function
  surfaces (sinks, drawers) is invisible to the loop.
- **[hospital_room v1, tall furniture occluding wall art → NEW auto constraint]** After the
  wall-load redistribution, the tall wardrobe (front-wall left) stood partly in front of
  the front-wall-center botanical print — no signal fired (WallOverlap only compares wall
  items to each other; the occluder was FLOOR furniture; user catch). → Added the
  **wall-object clearance** auto pass (`RoomGroup._enforce_wall_object_clearances`,
  Kunal's design: use the wall object's AABB): floor objects whose AABB top rises above
  the wall object's AABB bottom, within a 0.75 m band in front of its along-wall span,
  are slid ALONG the wall out of the span (sideways — a perpendicular push would be
  undone by `_repin_wall_furniture`); consoles below the art stay; unresolvable cases
  emit a `[RoomGroup] WARNING`. Rebuild: wardrobe beside the print, art fully visible,
  no new votes. Details in workflow/constraints.md.
- **[TOOLING GOTCHA — `run_scene` mtime-fallback]** `mcp__idsdl__run_scene` reports whichever
  `report.json` is **newest by mtime across all `tmp/*` dirs**, so when a build **errors before writing
  its own report** (or another run finished more recently) it surfaces a *different scene's* renders +
  feedback — I got a full **garage** back for a retail program (`ok=False`, but the images/asset-list
  were garage). **Tell by the printed asset list**: if it isn't your program's assets, ignore the
  render and re-run directly (`python workbench.py run <prog>`) to see the real build output/traceback.
- **[music_studio v1, room size — a flip across neutral after acting = STOP]** `rescale room by
  0.85` (Ph1) → `0.8` (Ph2), held per render-wins-early; applied `modulate_scale=0.85` in the
  final phase → the next full render voted `1.1` (slight enlarge). → **Declined the 1.1** — a vote
  that crosses neutral right after you act is the oscillation signal (converge-don't-chase), same
  as casino's declined 1.05. One decisive change, then stop.
- **[music_studio v1, lighting lint at the "safe" density]** `add_lighting(flush, density=0.02)`
  tripped the starfield lint: 12 fixtures on a 38 m² room (area budget ~11). The 0.01–0.02
  small-room band is not flat — ~38 m² already needs the bottom of it. → `0.01` → clean. When in
  doubt start at 0.01; the lint tells you if the ceiling is starved (it won't be).
- **[music_studio v1, clean rotation by construction]** `no rotation` every build on an
  orientation-heavy scene (chair↔mixer, angled monitors, wall furniture): built the console as ONE
  RelativeGroup with explicit `face(chair, toward=mixer)` + `face(monitor, toward=chair)`, omitted
  `facing` on all wall placements, and let `place_on_front(console, facing="back")` produce the
  engineer pose. Explicit `face()` inside the unit + facing defaults at the walls = zero VLM
  rotation churn.
- **[music_studio v1, texture accent didn't take — carry the accent with a prop]** Wall texture
  "dark charcoal grey with one deep red accent wall" resolved to plain dark grey (accent phrasing
  is not reliably honored by the texture embedding). The plan's red accent arrived via the red
  Persian rugs instead, and read better. If a palette accent matters, put it on a pinnable PROP
  (rug/chair/art), not in the wall-texture string. (Extends computer_room's plain-words texture
  lesson and jewelry_shop's pin-for-palette.)
- **[living_room_cozy v1, room size — a vote that NEVER flips is signal]** `RoomProportions` voted
  ENLARGE in every phase (`1.2` → `1.25` → `1.1` → `1.1`), decaying but never flipping direction —
  unlike living_room v1's enlarge→shrink drift that founded the hold-early rule. Held through
  phases 1–2 per the rule, applied the final-phase `modulate_scale=1.1` → immediate `no rescale`.
  Refinement: hold early always, but read the vote TRAIN — unidirectional+decaying converges in one
  final application; flip-flopping means the early votes were premature noise.
- **[living_room_cozy v1, phantom-object rotation noise]** Phase 1 emitted `rotate left accent
  chair / rotate right accent chair to face the coffee table` — the scene has ONE accent chair, and
  `seating.face(nook, toward=coffee)` had already angled it (confirmed in the render). → Declined;
  the vote never recurred. A rotation vote naming objects that don't exist is self-identifying noise.
- **[living_room_cozy v1, corner mesh at a wall center]** The audit-pinned fireplace (best fire
  glow) was a **corner** unit; its straight-on preview hid it, and the phase-1 render showed V-angled
  wings at the back-wall center. → Swapped to a straight wood-mantel fireplace. Lesson: a mesh's
  FORM FACTOR (corner vs straight) is a layout property — the caption word "corner" matters, and the
  cheap phase-1 loop is where it surfaces. Not a VLM signal (rotation/wall-overlap stayed clean);
  caught by eye.
- **[living_room_cozy v1, rug size vs cluster bbox]** `place_rug(size=1.0)` under a seating group
  whose bbox spans sofa + nook + coffee table covered nearly the whole auto-sized floor → read as
  wall-to-wall carpet. → `size=0.75` framed the seating zone with visible walnut floor. For a
  room-dominating cluster keep rug size ≤ 0.8; not a VLM signal (no lint fires) — judged by eye.
- **[classroom v1, room size — oscillation ends the thread]** `RoomProportions` walked `0.96` →
  `0.92` → `0.85` across the phases (held per render-wins-early), applied `modulate_scale=0.85`
  in the final phase, and the re-run vote flipped to **`1.1`** (enlarge). → Declined: a flip
  ACROSS neutral right after one decisive application is the converge signal (the living_room
  flip-flop rule seen post-apply); the render read well-filled at 0.85. Contrast laundromat
  (same-direction persistence → second shrink) and living_room_cozy (unidirectional decay → one
  application, done): read the vote TRAIN, not the last vote.
- **[classroom v1, accent color in a texture string]** `wall_texture="white painted wall with one
  teal accent wall"` embedded to a GREEN TILE texture on ALL FOUR walls — the accent clause
  dominated the embedding match (worse than computer_room's jargon-drift: it recolored the whole
  room). → Plain `"smooth white painted plaster wall"` → correct white. Rule: texture strings take
  ONE color + material; an accent color the texture library can't express is better dropped or
  carried by props (posters/chairs) than smuggled into the wall string.
- **[classroom v1, black ceiling is the renderer, not a texture]** The ceiling rendered BLACK in
  every interior strip; re-wording `ceiling_texture` ("plain white ceiling" → "smooth white
  plaster") changed nothing — the interior views render the room open-topped, so the black is
  void, not a texture failure. Don't burn iterations re-wording the ceiling string when the walls
  and floor came back correct.
- **[classroom v1, clean-by-construction orientation]** `no rotation` + `no wall overlap` from the
  FIRST phase-1 build to the last: `place_desk_chair` unit (pose correct by construction) +
  `room.face(grid, toward="front_wall")` (place_desk_chair grids face the FRONT wall — opposite of
  a WorkstationGroup grid) + default wall-facing everywhere + door and wall fixtures in disjoint
  slots. Copying the worked-example defaults collapsed the whole feedback loop to the single
  room-size thread (same effect as laundromat).
- **[bookstore v1, decaying rescale vote = converged]** `rescale room by 0.75` (Ph1) → `0.8` (Ph2)
  → held per render-wins-early → applied ONE decisive `modulate_scale=0.85` in the final phase →
  the vote decayed to `0.9` and repeated there across two full builds while the render read
  well-filled with clear browsing aisles. → **Declined the residual 0.9** — a vote that decays
  toward neutral after you act is the converge signal (executive_office), and stacking it would
  have been laundromat's two-step only if the render had *agreed* it was still sparse (it didn't).
  Render is the arbiter of whether a persisting mild vote is signal or noise.
- **[bookstore v1, lighting density mid-size calibration]** `density=0.04` — chosen as "medium
  room" per the retail ladder — tripped the deterministic starfield lint: **35 fixtures on a
  56 m² room (budget ~17)**. → **0.015** → clean. Refines the area ladder with a real datapoint:
  small café ≈ 0.01, **~50-60 m² shop ≈ 0.015-0.02**, only genuinely large floors 0.05-0.08.
  The lint line states the budget — trust it over the remembered ladder.
- **[corridor v1, the shrink vote NEVER goes quiet on a passage room]** `rescale room by
  0.69–0.76` every phase → held per render-wins-early. Final phase: applied **0.75** → the render
  went CRAMPED (cameras jammed against the cabinet run) and the vote flipped to `0.95`; backed off
  to **0.85** → the vote resettled at `0.8` on a render that read as a real hallway with a clear
  lane. → **Declined the residual** — a corridor's open center lane IS the category (garage's
  "circulation lane reads as empty" at full strength); expect the occupancy vote to persist
  forever and let the two-sided render evidence (cramped at 0.75, right at 0.85) pick the point.
- **[corridor v1, oversized wall furniture is an EYE catch, not a VLM signal]** Phase-1 render:
  the green `future/` cabinets loaded ~2× (bad scale metadata) and dominated every view; VLM said
  only `rescale room 0.76` / `no rotation`. → Fixed in two eye-driven steps: uniform `_cab.scale(1.0)`
  (metadata), then **scale-by-height** `_cab.scale(_cab.get_width()*0.9/_cab.get_height())` —
  wardrobe-tall furniture crowds a corridor; sideboard height leaves the wall band to art.
- **[corridor v1, texture-library gap: no b/w checkerboard]** Four floor wordings: "glossy black
  and white checkerboard marble tile floor" → pale planks; "black and white checkered tile floor"
  → plain dark grey; "black and white checkerboard floor tiles" and "black white checkerboard
  tiles" → a MULTICOLOR checker. → Settled the **dark reflective tile** (keeps the plan's
  "reflective spine", drops its pattern) — classroom's "drop the accent, don't smuggle it" applied
  to floors. When two wordings return different WRONG things, the library lacks the texture.
- **[corridor v1, add_lighting has no asset_id]** Static lint caught `add_lighting(...,
  asset_id=…)` (accepts only desc/density/modulate_scale). → Audit the fixture with `inspect`,
  then write the query specific enough ("a slim linear black LED flush mount ceiling light bar")
  that the audited mesh is the top pick anyway.
- **[corridor v1, a mirror reflecting the room looks like a wrong asset]** The round wall mirror
  rendered as a green/white half-disc and looked like a mis-picked shelf — it was correctly
  REFLECTING the opposite green cabinet wall. Before swapping a "weird" mirror mesh, ask what a
  real mirror would show from that camera.
- **[bakery v1, garbage interior view → hallucinated rotation flags]** A build whose back-wall
  interior camera sat INSIDE the tall wire rack (one view = black shelf tiers) emitted 8 rotation
  flags (`rotate stool/chair/counter/console to face the central seating area`) on a layout that
  read correct in every other view; the same layout with the rack lowered below camera height
  came back `no rotation`. → Lesson: interior wall cameras sit at ~1.4-1.5 m at each wall's
  center; any fixture taller than that near a wall center both blinds that view AND corrupts the
  VLM constraints judged from the strip. Keep wall-center fixtures ≤ ~1.25 m (or offset them);
  treat rotation storms that coincide with a garbage view as camera artifacts, not layout errors.
- **[bakery v1, room size — sparse-shop shrink, one step]** `rescale room by 0.87→0.77` drifting
  down through phase-1 iterations, `0.76` (Ph2), `0.75` (full). Held per render-wins-early,
  applied ONE decisive `modulate_scale=0.78` in the final phase → `0.92` then `0.95` = noise,
  declined. (Laundromat's two-step convergence wasn't needed — picking a value near the vote,
  not above it, converged immediately.)
- **[bakery v1, texture "wrong color" that ISN'T a wording problem]** Walls rendered pale blush
  for "warm red brick" AND for caption-exact wording. Verified the retrieval directly (embed the
  query against `IDSDL/assets/wall_textures_embeddings.npz`, open the winning texture.png): a
  genuine deep-red brick was matched and applied — the room-scale tiling + light budget washes
  it out. → Lesson: before iterating on texture WORDING (computer_room lesson), check whether
  the match is already right; if it is, the pale render is a renderer limit — converge. The
  wording fix and the renderer limit are different failure modes with the same symptom.
- **[bakery v1, window-bar drift]** `place_on_front(window_bar_group)` (front SLOT) left the
  glass-front ledge drifting mid-floor (door clearance + randomness push slot groups around).
  → `place_on_front_wall_center(window_bar_group)` pins the console flush to the storefront
  with the stool row on the room side (default wall-facing heuristic, no `face()` per the
  bar.md straight-row rule) → `no rotation` every subsequent build. Wall placements accept
  composed groups; use them whenever "flush to a wall" is the intent.
- **[living_room_cozy v2, THIN wall furniture drifts off its wall — core fix]** The wall-centered
  fireplace ended 1.6 m off the back wall while the FULL VLM loop read clean (`no rescale / no
  rotation / no wall overlap`, no lints) — the USER caught it in the blend. Root cause (probed
  stage-by-stage, clearances and randomness ruled out): `GradSolver.compute_action` scores every
  direction `max(grad·dir, 0.01) * free_space_affinity / area` — an exploration floor that moves
  objects with NO constraint pressure toward open space, damped by footprint area. A fireplace is
  the worst case (0.24 m deep = tiny area, a whole room of free space in front), so it random-walks
  off the wall over the 100-step solve; deep/heavy wall pieces (counters, machine rows) never showed
  it. **Fixed in core**: `RoomGroup._repin_wall_furniture()` (groups.py) — a deterministic post-solve
  pass (mirrors `_enforce_door_clearances`) that snaps every `place_on_<wall>_wall_*` item flush by
  its world AABB, keeping along-wall drift, running before the doorway pass so doors still win.
  NOTE: snap by AABB, not by re-running `wall_deltas` — `get_whd()` is rotation-aware post-solve, so
  recomputed deltas double-swap w/d for 90°-rotated items (the bookcase got pushed OFF its wall by
  the first draft of the fix). Meta-lesson: the VLM loop verifies proportions/rotation/wall-slots,
  NOT wall flushness — check wall gaps in the blend (`aabb` vs wall plane), like the jewelry-shop
  "converged ≠ correct" lesson.
- **[living_room_cozy v2, wall art faced the wall — caption≠front]** The back-wall photo grid
  (`future/09f28392…`) rendered as brown rectangles: its mesh FRONT pointed into the wall (what the
  interior render showed was the wooden backing), and `RotationConstraint` never flagged it (the
  backing reads as plausible frames). Its catalog preview also revealed the true front is four EMPTY
  frames. → Both fixes: `front_cache set 09f28392… 180` (fix-once-per-asset, helps future users) AND
  swapped to a collage with real photo content (`future/e2b0dcb4…`). Lesson: if wall art looks like
  bare boards/mats in the render, compare against the catalog preview (`3D-FUTURE-images/<id>.png`)
  — a reversed front and an empty-frame asset LOOK identical from behind; and an empty-frame
  "gallery set" fails the jewelry-shop product rule even when correctly oriented.
- **[office_modern v1, texture — a MATCHING bug and a RENDERING limit look identical, and you can
  tell them apart OFFLINE in 5 seconds]** The plan's green wall took three wordings, and the two
  failure modes are genuinely different: `"deep green painted wall"` matched a **pale** green
  stucco (0.53) and rendered BEIGE — a *wording* bug, fixable (computer_room/classroom).
  `"a dark olive green color with subtle irregular brush stroke patterns"` matched the library's
  **darkest** green at **0.82** — an unambiguously correct match — and still rendered **GREY-TAUPE**,
  because room-scale tiling + the fixed light budget wash dark tones out (the bakery brick lesson,
  now confirmed on a second colour family). `"solid deep green smooth uniform wall"` (0.70) gave a
  true green that HOLDS. → Two rules. **(1) Verify the match offline before rebuilding**: embed the
  query against `IDSDL/assets/wall_textures_embeddings.npz` and read the winning caption (~5 s) —
  the wording loop should never cost an 8-minute build. **(2) A correct match is NOT a guarantee of
  the colour**: if the caption is already right and the render is still wrong, STOP re-wording — the
  library can't give you that tone at room scale; pick a value that survives the wash or carry the
  accent on a prop (music_studio). Corollary: texture strings are matched against CAPTION text, so
  word them like a caption ("solid deep green, smooth and uniform"), not like a paint chip.
- **[office_modern v1, design the wall so the CAMERA can see the room]** The storage backbone
  (a 2.17 m book-filled bookcase) would naturally go at `back_wall_center` — which is exactly where
  the interior camera sits (~1.4–1.5 m at each wall's centre), i.e. the bakery garbage-view failure
  that ALSO hallucinates rotation flags on a correct layout. → Split the backbone to the corners
  (`back_wall_left` bookcase + `back_wall_right` filing cabinet), leaving back-centre empty. Result:
  four clean views and `no rotation` from the first build to the last. Applied the bakery lesson
  **preventively at design time** rather than diagnosing it after a bad render — that is what the
  worked examples are for.
- **[office_modern v1, room size — one decisive application, then decline the BOUNCE]** Vote train
  `0.67` → `0.7` (Ph1) → `0.8` (Ph2): unidirectional and decaying = converging (living_room_cozy).
  Held through phases 1–2, applied ONE `modulate_scale=0.8` in the final phase — **at** the latest
  vote, not below it (bakery). The vote then bounced `0.92` / `0.8` / `0.85` across *identical*
  builds → declined. Note the refinement: an oscillation across REPEATED builds of the same program
  is measurement noise, which is even stronger grounds to stop than a single post-apply flip.
- **[office_modern v1, the empty-frame trap caught at AUDIT time]** The rank-1 pick for a warm
  abstract print (`hssd/fd940fdb…`) previews as a **blank white rectangle** — the living_room_cozy
  v2 asset class (an empty frame and a reversed front look identical from behind, and the VLM flags
  neither). Caught it on the contact sheet at gate 3 and pinned two prints with visible artwork
  instead. Cost: 30 seconds. The same asset shipped would have been a post-build mystery. **Eyeball
  the previews — that IS the gate.**

- **[living_room_cozy v3, place_on_top seats items on the group ANCHOR — a lamp on the chair]**
  `nook.place_on_top(table_lamp)` inside the reading-nook group (anchor = the armchair) put the
  lamp on the chair's SEAT — the placement tournament happily picks the cushion as a valid surface,
  and no check objects (geometry is fine; "a lamp doesn't belong on a seat" is semantics). The side
  table being a child of the group doesn't matter: `place_on_top` ALWAYS targets the anchor. →
  Restructured per the bedroom/design-principles unit rule: a `side_unit` RelativeGroup with the
  TABLE as anchor + `place_on_top(lamp)`, then `nook.place_on_left(side_unit)`. Rule: before any
  `place_on_top`/`place_inside`, ask "what is this group's anchor?" — if the intended surface isn't
  the anchor, compose a sub-unit around the surface first. (User catch #3 this scene that the clean
  VLM loop missed.)
- **[prison_cell v1, the loop cannot see a WRONG-KIND object — floral curtains in a jail cell]**
  The barred window rendered with cream patterned DRAPES. Every signal was clean (`no rescale` /
  `no rotation` / `no wall overlap`): the curtains were geometrically perfect, correctly scaled,
  correctly slotted — they were simply *the wrong kind of object for the room*, and no constraint
  asks "does this belong in a prison?". Root cause was a core DSL gap, not the program:
  `place_window_standard(wall, pos)` defaults to `curtain=None`, but `add_window_standard` called
  `add_curtain(None)` **unconditionally** and `add_curtain` falls back to the DEFAULT drape mesh
  when given no texture — so there was **no way to author an undressed window** (it was silently
  draping the retail/jewelry/toy storefronts, wine_cellar, pantry and warehouse too).
  `add_window_picture` already had the right guard; `add_window_standard` never got it. → Fixed in
  core (`IDSDL/window.py`: return early with no curtain when the texture is falsy). Lesson, in the
  jewelry_shop family: **the VLM loop verifies geometry, never category legibility — a converged
  build can still contain an object that has no business in the room. Look at the render and ask
  "would this be HERE?"** (Same class of catch, opposite direction, as jewelry_shop's empty
  vitrines: there the fixture was right and the product missing; here the object was simply alien.)
- **[prison_cell v1, a phase-2 `place_on_top` gated OUTSIDE its `with` block silently never runs]**
  `if PHASE >= 2: desk_unit.place_on_top(books)` written *after* the `desk_unit` block exited. A
  group compiles on `__exit__`, so the op registered too late to execute: the books never entered
  the scene and the desk rendered BARE. Nothing caught it — `report.json`'s object COUNT still
  incremented to 6, the VLM loop was clean, no lint fired. Found only by reading the exported
  `.blend` (the books sat there as an un-instanced template at the origin). → Gate INSIDE the block,
  as `coffee_shop_v1` does. Lesson: **verify a phase-2 prop by EYE (zoom the render); the object
  count is not evidence that anything was placed.**
- **[prison_cell v1, the float lint's false-positive class: `bottom=` wall-mounts]** `[Lint]
  'washbasin' FLOATS 0.40 m` on every single build — that 0.40 m is exactly the intended
  `place_on_right_wall_left(sink, bottom=0.40)`. A wall-hung basin is SUPPOSED to float;
  `IDSDL/lints.py` tests AABB-bottom ≈ 0 and does not exempt items placed with an explicit
  `bottom=`, so **any correctly wall-mounted basin/vanity/floating unit trips it**. → Declined all
  three times (with the reason recorded), and did NOT take the lint's "swap the mesh" advice. This
  is the one documented exception to "lints are computed facts, treat them as MUST-FIX": the fact
  is real (the mesh IS off the floor), the inference ("off-center origin, swap it") is wrong.
  Worth exempting `bottom=` items in core.
- **[prison_cell v1, room size — read the vote TRAIN, then stop]** `rescale room by 0.69` (Ph1) →
  `0.69` (Ph2): unidirectional and UNDECAYED, and the shell had auto-sized to 4.0×5.1 m — a
  dormitory, not a cell. → Held per render-wins-early, then ONE decisive `modulate_scale=0.7` AT
  the vote (bakery: pick at the vote, not above it). The next build flipped to `1.1` — a flip
  ACROSS neutral immediately after acting = converge (music_studio/classroom) → **declined**, and
  it settled to `no rescale` by itself. Also declined a one-shot `rotate desk by 180` (the render
  shows the knee-hole and stool facing the room; 180° would drive the working front into the wall).
- **[prison_cell v1, check a wall object's AABB bottom BEFORE hanging it — the rejected hatch]**
  Wanted a barred vision hatch on the (domestic-looking) cell door. Slot-mounted wall objects
  centre at y=1.5 m, so the panel's AABB bottom (~1.22 m) would sit BELOW the bunk's top (1.52 m) —
  which is precisely the trigger for the automatic wall-object-clearance pass to slide the **bunk**
  sideways along the front wall, off its wall and into the middle of the cell (hospital_room's
  wardrobe mechanic, but wrecking the hero this time). → **Designed, then rejected on geometry
  without building.** Lesson: that clearance pass is a *layout* force, not just a cosmetic one —
  before hanging anything, compare its AABB bottom against the TOPS of the floor furniture near
  that wall.
- **[operating_room v1, room size — shrink the shell, but stay ABOVE the vote when the empty
  floor is FUNCTIONAL]** `RoomProportions` voted `0.8` (Ph1) → `0.69` (Ph2) → `0.8` (full).
  Held per render-wins-early, then applied ONE decisive `modulate_scale=0.85` — deliberately a
  touch above the vote, because the hero's 1.2 m sterile ring (`add_clearance(dir="all")`, the
  thing that SIZES the room) is working space a scrub team walks, not emptiness. Vote decayed
  `0.9` → `0.97` ≈ neutral → declined the residual. Same family as garage's vehicle-door lane
  and corridor's centre lane: **when the open floor IS the category, shrink toward the vote but
  never onto it.**
- **[operating_room v1, "that fixture is too small to be the thing it is" — no signal fires]**
  The surgical dome at `modulate_scale=1.6` rendered as an ordinary downlight; the entire VLM
  loop was clean (`no rotation / no wall overlap`, no lints) and said nothing, because the
  geometry is fine — only the SEMANTICS are wrong. Caught by eye, fixed with one decisive bump
  to `2.6`. Same class as corridor's oversized cabinets and jewelry_shop's empty vitrines:
  **the loop verifies geometry, never "does this read as the object it is named after."**
- **[operating_room v1, the VIBE layer is INVERTED for a clinical room]** The judge gate's
  standard finishing moves (greenery, warm accent seat, rug, warm envelope) would have *broken*
  the OR — it earns its category read by being BARE (hard resin floor, tile, stainless, no
  plants). The planner's own brief asked for biophilic warmth and daylight windows; that is the
  PLAN being wrong about its category, and the right call was to decline it (extends
  dental_office's "clinical rooms want a hard floor — drop the rug"). The sterile equivalent of
  jewelry_shop's product rule is **folded drape stacks massed at working height** on the carts
  and counter.
- **[operating_room v1, browse before believing the catalog's gap warning — but believe it when
  it's right]** The catalog flags operating tables as a prime ingest candidate; a browse found a
  genuine OR table hiding under the caption "medical examination table" (`future/51434359`) —
  the mesh, not the words, is the evidence (hospital_room's bed lesson again). The SAME browse
  proved the warning true for the other two: "surgical dome light" returns residential frosted-
  glass lamps, and "a stainless steel tray of surgical instruments" returns **kitchen cutlery**
  — a casino-poker-chip trap that would have made the mayo stands read as a catering cart.
  Substituted (flush dome, med cart, folded linen) rather than shipping a wrong prop.
- **[kindergarten v1, a prop the dataset DOESN'T have — the clean loop can't see semantics]**
  `place_on_top("a cup full of colored crayons")` resolved at **0.43** to a *white ceramic
  geometric DESIGNER pencil holder with two black pens* (the shortlist is beige pencils, wooden
  pencils, post-its — no crayon cup exists). It put a **vase-like object on every kid table**,
  and the FULL VLM loop ran clean straight through it (`no rescale / no rotation / no wall
  overlap`, zero lints) — because the geometry is fine and *"a designer pen pot doesn't belong
  in a kindergarten"* is **semantics**. → Caught by eye in the render; swapped for a boxed
  puzzle the library provably has. Casino's poker-chip rule at full strength: **only
  `place_on_top` a prop you have VERIFIED exists — and the loop converging is never evidence
  that it does.**
- **[kindergarten v1, room size — "fill the floor, THEN shrink"]** `RoomProportions` ran
  `0.92 → 0.90 → 0.80`: same direction and **growing** (contrast living_room_cozy's decaying
  vote, which converges in one application). Growing = the room really is sparse — but kid-scale
  furniture is small **by definition**, so chasing the vote to 0.8 would have bought the
  occupancy number by crushing the open floor a kindergarten exists for (garage's "circulation
  lane reads as empty"). → Applied `modulate_scale=0.85` **and** filled the empty `back_left`
  slot with a third activity table (a piece the PLAN had already asked for — the "construction
  center") → next build **`no rescale`**. Generalises children_room's "add a bean bag rather
  than over-shrink": **when the vote GROWS, ask whether the room is too big or the floor is too
  empty, and fix the one that is actually true — the plan usually already names the missing
  piece.** (The intermediate build's post-apply flip to `1.1` was declined as the usual
  across-neutral converge signal.)
- **[kindergarten v1, a nook is a corner, not an island]** `place_on_left(reading_nook)` — a
  floor SLOT — left the composed bean-bag group **stranded mid-floor** (door clearance +
  `randomness` push slot groups around). VLM said nothing; the layout is geometrically legal, it
  just isn't a *nook*. → `place_on_left_wall_center(reading_nook)` pins the whole group flush
  under the window. Same fix as bakery's drifting window-bar: **wall placements accept composed
  groups — use them whenever "tucked against a wall" is the intent, and don't trust a slot to
  keep a cluster where you pictured it.**
- **[kindergarten v1, kid scale IS the camera rule — rotation-clean by construction]** Every
  fixture came in at child height (tables 0.95 m, chairs 0.62 m, all storage ≤ 1.15 m) because
  the brief demanded it — and that alone bought the bakery camera rule: nothing at a wall centre
  reaches the ~1.4–1.5 m interior cameras, so no view was ever blinded and **`no rotation` held
  from the first phase-1 build to the last** (the only vote was the standard `place_desk_chair`
  false positive on the teacher's chair — declined by eye, as in children_room/computer_room/
  classroom). Where a category's own scale keeps the walls low, the whole rotation thread
  disappears.
- **[kindergarten v1, the picker's #1 for a kid chair is an OFFICE chair]** *"a small colourful
  child's chair"* → the visual picker chose a **wheeled swivel office chair** (`hssd/c5fcff66`);
  caption and similarity both look reasonable, only the PREVIEW gives it away. A wider `browse`
  found a cartoon **lion-faced kid chair** (`future/938f5c3e`) that is unmistakably kindergarten
  AND carries the primary-colour accent as a prop. Reconfirms the eyeball-at-gate-3 rule, and
  music_studio's accent rule: with white walls mandatory (classroom v1's teal-accent disaster),
  **the furniture is where the palette has to live.**

- **[tv_studio v1, a gap-category hero hides behind a DISMISSIVE caption — hunt by SILHOUETTE]**
  A TV studio needs three meshes the dataset simply does not have: a broadcast camera, a softbox on
  a light stand, and a news desk. The queries return telescopes, tripod LAMPS and camcorders, and
  the reflex ("commercial gear → ingest", asset_selection.md) would have stopped the scene at gate 3.
  → Instead I read the previews (`show n --big`), not the captions: `hssd/6d5c2629`
  ("**antique** metal camera with a tripod, serving as a **decorative**…") renders as a boxy body +
  lens + film reels on a splayed tripod, and `hssd/4c5ab0e1` ("black standing **floor lamp** with a
  **tripod base**") is a tilted dish head on a stand — i.e. the studio camera and the key/fill lights,
  exactly. Scaled to real heights (1.5 m / 1.85 m via `obj.scale(w*H/h)`) they are the most legible
  objects in the finished room. Lesson: **at room scale a prop is its SILHOUETTE, so search the
  shape, not the category name** — "antique"/"decorative"/"floor lamp" are captioner adjectives, not
  disqualifiers. Ingest is the fallback AFTER you have eyeballed the near-misses, not before.
- **[tv_studio v1, you cannot hang a big backdrop — the two wall paths trap you from both sides]**
  Wanted a news backdrop (big panel + two flanking monitors) on the back wall. **Freeform** caps the
  ENTIRE run at 50% of the wall width (`groups.py:2052`) → three items came out ~0.75 m plaques and
  the `modulate_scale=1.6` I passed the monitors was silently discarded. Switched to the three
  **slots** (`target_width = WIDTH/3*0.6`, bigger) → they mount LOW, the panel's bottom edge fell
  below the anchors' chair-backs, and the wall-object clearance pass tried to slide the whole set out
  of its span, failed (`[RoomGroup] WARNING: 'RelativeGroup' occludes wall-hung …`) and **cascaded** a
  second warning onto the left-wall panel it had just shoved the set into. Standing the set flush to
  the wall (to make the panel support-anchored and inherit the desk's 2.4 m width) reproduced the
  same occlusion. → **Reverted to freeform** (mid-wall mount clears the set) and accepted a modest
  backdrop. General rule: `wall_obj_scale_computer` penalizes heights over ~1 m by `10*(h-1)²`, so
  **no wall-hung mesh can become a floor-to-ceiling backdrop — if a scene needs one, it is a
  floor-standing asset or an ingest, not wall art.** Corollary: a wall item hung near furniture-top
  height will fight your own furniture; check the wall object's AABB bottom against the tops of what
  stands in front of it (prison_cell's rule, hit here from the other direction).
- **[tv_studio v1, `modulate_scale` is a NO-OP on `place_on_top` items]** The desk mics read
  oversized; `modulate_scale` 0.45 → 0.3 changed the render not at all. Cause: the smart-placement
  tournament **height-fits each item to an LLM-chosen fraction of the anchor's height** and then
  clamps its footprint to its tile — both of which override the scale the asset arrived with. → Don't
  spend a build tuning `modulate_scale` on an on-top prop: accept the tournament's sizing, or pin a
  different (smaller-form) mesh. (`modulate_scale` still works normally on FLOOR objects and on
  wall-hung items placed without a target width.)
- **[tv_studio v1, orient a whole equipment LANE with `facing=`, never with a nested group]** v1 built
  the camera + key/fill lights as a `RelativeGroup` (lights via `place_on_left_further` /
  `place_on_right_further`): those verbs bake ±90°, so one light turned its **black dish back** to the
  anchors. → Placed all three as room-level floor objects with `facing="back"` — camera and both
  dishes aim at the set, `no rotation` on every subsequent build. Same conclusion as music_studio's
  console (explicit facing inside the unit / defaults at the walls), stated for a row of gear that
  must all point ONE way: give each piece the room-level `facing`, don't inherit a diagonal verb's
  baked rotation.
- **[greenhouse v1, the "black void" and the "black ceiling" were ONE renderer bug — now FIXED]**
  Six examples (executive_office, dental, retail_store, florist_shop, coffee_shop) had concluded
  *"any opening renders as a black night void — there is no exterior environment"* and built
  workarounds around it (never full-height-glaze; prefer `place_window_standard`; stage a foreground
  object in front of the void; treat an all-black `wall_*.png` as a camera artifact); classroom
  separately concluded *"the black ceiling is the renderer, not a texture."* Both were the SAME
  one-line bug: `_render_interior_view` rendered with `transparent=True` → `film_transparent`, so a
  ray hitting **no geometry** (through a window, or above the hidden ceiling) wrote **alpha 0** and
  flattened to BLACK. The world was never missing — `set_white_world_background()` is called on every
  render path. → Fixed in `IDSDL/renderer/utils.py`: (a) interior views render with an **opaque
  film**; (b) `_setup_interior` raises the sky (`INTERIOR_SKY_STRENGTH`, default 3.0, override with
  `IDSDL_SKY`), because the default world (0.7 grey @ 1.0) *looks* white but is too dim to light
  anything — with (a) alone you get a blown-white pane over a **dark** room. Asset previews and
  `place_on_top` tournaments still render transparent (they want a cutout), so retrieval is untouched.
  **Lesson (the meta one): a limitation that EVERY scene works around and NO scene ever tried to
  reproduce is a bug hypothesis, not a law of physics.** Six examples inherited it as lore. Read the
  renderer before you design around it. **Also note (b) is the ONLY brightness lever that exists:**
  `add_lighting` spends a fixed **500 W split across N fixtures** (`object.py`:
  `per_light_energy = 500.0 / max(1, N)`), so raising `density` buys *more, dimmer* fixtures and can
  never brighten a room. A "bright/sunlit" brief is a SKY problem, not an `add_lighting` problem.
- **[greenhouse v1, room size — apply the SIGNAL, not the NUMBER]** Vote ran `0.88 → 0.82 → 0.7`,
  unidirectional (= signal, per living_room_cozy's vote-train rule), and the render agreed the
  entrance half was bare gravel. But **applying the voted 0.7 would have triggered the locker_room
  bug**: the shell auto-sizes to *fit* three fixed-size `GridGroup` bench rows, so a hard shrink
  pushes them out of their slots into overlaps. → Read the vote as "too empty", not "too big": FILLED
  the bare floor (children_room: fill before shrinking) + a mild `0.9`. Vote decayed to `0.96` ≈
  neutral → declined. **A unidirectional shrink vote on a row-packed room means ADD FURNITURE.**
- **[greenhouse v1, retrieval scale metadata lies on plants too]** The pinned "tall tropical palm"
  (`future/130b1ed4…`) is natively **0.70 m tall** — it would have read as a tabletop plant, not the
  plan's vertical anchor. Caught OFFLINE with `get_whd()` before the first build; fixed by scaling to
  a target HEIGHT uniformly (`obj.scale(obj.get_width()*1.75/obj.get_height())`). Same class as the
  half-scale hospital bed and the toy-sized garage car — **for any uncurated hero, verify a
  real-world dimension with `get_whd()` before you build, not after you look.**
- **[kitchen v1, a bloated CLUSTER — not the item count — is what auto-sizes a cavernous room]**
  `rescale room by 0.79 → 0.80 → 0.80` on a kitchen whose renders showed dead floor. The instinct is
  to reach for `modulate_scale`; the actual culprit was ONE group. The 4 dining chairs were seated
  with `place_circle(4)` at `sparsity=0.2 / jitter=0.35` — they flung out into a ring far wider than
  the rectangular table, and RoomGroup grew the shell to fit that bbox. → Fixed structurally, not by
  rescaling: `place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])` (two down each
  long side — correct for a rectangular table, and a much tighter footprint) at `sparsity=0.05 /
  jitter=0.15`. The room came in dramatically smaller for free. **This generalises hospital_room's
  rule past wall queues: when a room feels too big, look for the footprint culprit — an over-sparse
  seating ring, a `_further` placement, a mis-scaled hero — BEFORE touching `modulate_scale`. The
  occupancy vote tells you THAT the room is wrong, never WHICH group made it wrong.** (Afterwards,
  held per render-wins-early and applied ONE decisive `modulate_scale=0.85` → `no rescale`.)
- **[kitchen v1, deliberately UNDER-shrinking the vote on a fixed-size-row room]** The final vote was
  `0.80`; applied `0.85`. The cook run and the sink return are fixed-size `GridGroup` rows, and a
  shell shrunk below the footprint its placements dictate makes such rows overflow their slots into
  overlaps the solver cannot undo (the locker_room packed-room rule). The floor the vote was reacting
  to is the working aisle around the island — legitimate circulation, which reads as "empty" to an
  occupancy metric (garage, corridor). Result: `no rescale` at 0.85. **Rule: bakery's "pick a value
  near the vote, not above it" holds for rooms of free-standing furniture; a room whose walls carry
  RIGID composed rows should stop SHORT of the vote.**
- **[kitchen v1, the `place_rectilinear` stool-rotation false positive — declined, again]**
  `rotate the kitchen island counter stools by 180` in phase 1. The left-wall render showed both
  stools correctly addressing the island. Declined per bar.md: `place_rectilinear` already gives the
  row a uniform straight facing (`anchor − 180`), so the vote is noise — and "fixing" it with a
  per-stool `face(toward=island)` would actively make it worse (each stool would aim at the island's
  centre POINT and the end stools would fan inward). The vote did not recur. Third scene to hit this;
  treat a rotation vote on a `place_rectilinear` service row as noise by default.
- **[kitchen v1, the loop went clean on a room with two visible defects]** Final build: `no rescale /
  no rotation / no wall overlap`, zero lints — while the glass-front upper cabinets were EMPTY (they
  have glass doors; they read as the fixture, not as a kitchen — jewelry_shop's product rule) and the
  right wall was a blank expanse between the fridge and the pantry. Neither is expressible to any
  constraint: the geometry is flawless, and "an empty display cabinet doesn't say kitchen" is
  semantics. Both were caught at the JUDGE gate by LOOKING. → Stocked the uppers with plate/bowl
  stacks via `place_inside` (building ONE dressed unit and duplicating it — `place_inside` runs its
  sizing tournament per call, so two units built separately get differently-sized crockery), hung a
  framed still-life on the right wall, and scaled up a wicker basket that had rendered doll-sized at
  0.35 m. Reconfirms jewelry_shop: **loop-clean is necessary, never sufficient — the category
  gut-check is yours.**
- **[wine_cellar v1, "warm dim" is a BUDGET problem — no fixture choice can produce a dark room]**
  The prompt's mood was the one unbuildable thing, and every instinct (pick a smaller fixture, drop
  `density`, swap the caged lamp for a flush disc) failed, because neither lever touches brightness:
  `density` is fixture COUNT, and the room was being flooded from the **interior renderer's
  strength-3.0 sky** (`INTERIOR_SKY_STRENGTH`, set because the ceiling is hidden for interior views —
  right for a daylit room, fatal for a cellar). → Two dials, both needed: `os.environ["IDSDL_SKY"] =
  "0.6"` **before importing IDSDL** (the renderer binds it at import), and a NEW `scene.light_budget`
  (`IDSDL/scene.py`, default 500 W so every existing scene is unchanged; `add_lighting` splits it
  across N) set to **90 W** for ~32 m² of stone. Result: stone in shadow, light pooled on the table.
  **Tune ONE dial at a time** — I dropped the sky and raised the wattage in the same build, they
  cancelled exactly, and I nearly concluded the sky override was broken. Generalizes the greenhouse
  note ("brightness is a SKY setting, never `add_lighting`") to its dark mirror: for a DIM room, drop
  the sky *and* the budget. Applies to any bar / cinema / speakeasy / nightclub brief.
- **[wine_cellar v1, TOOLING — MCP `run_scene` renders ignore the program's `IDSDL_SKY`]** The same
  program renders BRIGHT through `mcp__idsdl__run_scene` and DIM through `python workbench.py run
  <prog>` (verified back-to-back at an identical 90 W budget). The warm MCP server has already
  imported the renderer, so `INTERIOR_SKY_STRENGTH` is bound before the program's `os.environ` line
  ever executes — `run_scene` is subprocess-isolated for the BUILD but not for import-time constants.
  → **Build any mood-dependent scene from the SHELL**, or you will chase a mood your renders can
  never show (I burned three ~8-minute builds "fixing" lighting that was already fixed). Sibling of
  the `run_scene` mtime-fallback gotcha; both are reasons to distrust a surprising `run_scene` render.
- **[wine_cellar v1, the on-top prop band is NARROW — bracket it, don't creep]** The decanter/bottle
  on the tasting table: `modulate_scale=0.55` → a ~0.6 m magnum lying across the table; `0.3` →
  invisible specks; **0.4** reads correctly. Two builds, because I bracketed from both sides instead
  of creeping down in 0.05 steps (library's banker's lamp took the slow path). For any small on-top
  prop, jump to a clearly-too-small value on the second try — the readable band is ~0.35-0.45.
- **[wine_cellar v1, a washed-out texture can be a LIGHTING symptom]** The brick rendered pale pink.
  Per the bakery rule I verified the match offline first (`"old red brick wall"` → `c71761a5`, a
  genuine deep-red brick at 0.68) and correctly declined to re-word it — but the conclusion "renderer
  limit, converge" was only half right: dropping the sky from 3.0 to 0.6 restored the deep red. So
  the ladder is now THREE rungs, not two: (1) is the match wrong? (re-word) (2) is the match right but
  the room over-lit? (**drop the sky** — new) (3) only then accept it as a renderer limit.
- **[greenhouse v2, "this looks too much like the flower shop" — the DENSITY GRAIN differentiates two
  scenes that share a layout pattern (Kunal, 2026-07-13)]** v1 reused the florist recipe (mass a prop
  on repeated tables) and so *rendered as the florist shop*: same bones, same read. No VLM signal fired
  — the loop checks geometry, never "is this the right CATEGORY of room" (the jewelry_shop lesson,
  again, and again a USER catch). → Fix: **plant BEDS** — `GridGroup(sparsity=0.0, randomness=0.35)`
  packing 8-12 mixed plants until their bboxes touch, so the foliage interlaces into one THICKET;
  four of them dropped in floor slots. A nursery reads by thickets, a florist by specimens: when two
  categories share a layout pattern, the tie-break is the **density grain of the product**, not more
  of the same prop. Two mechanics worth keeping: (a) `sparsity=0.0` only packs like this because
  GridGroup runs NO overlap solve — a solving group would push the clump back apart; (b) a bed costs
  **one room slot** but holds a dozen plants, so occupancy jumps with **zero growth in the shell** —
  the clean way to fill a room that reads empty but cannot be shrunk (its fixed-size rows would
  overflow their slots).
- **[greenhouse v2, height-fitting a FLAT mesh detonates it]** Normalizing the bed's plants to a common
  0.55 m HEIGHT turned the seed tray (0.30 W x 0.10 H) into a **1.65 m pale-green SLAB** — a uniform
  height-fit multiplies a flat trough by ~5.5x in every axis. → Normalize a mixed-mesh cluster by
  **WIDTH** (`obj.scale(w)`, uniform): footprints become packable while natural height variation
  survives, and that variation is what makes a canopy read grown-in. Rule: **fit by height only for
  things that are TALL (a palm, a shelf); fit by width for anything that might be flat.** (And note
  `obj.scale()` returns `None` — chaining it silently puts `None` in your list.)
- **[kitchen_set v1, THE BLINDED-CAMERA TRAP — a solid-BLACK render that the loop calls clean]**
  A kitchen built on a complete fitted SET (`future/3c2bf09e`, a 2.85 x 3.00 x 2.40 m navy U).
  `RoomGroup` auto-sizes a shell that merely FITS its furniture, so the set's wings touched both
  side walls with zero circulation — and the interior cameras, which sit **on the room centreline
  at 0.55 x ceiling (~1.65 m), just inside each wall** (`renderer/utils.py`: `eye = fz + 0.55*H`,
  `inset = 0.92`), ended up **INSIDE the cabinetry**. The phase-1 front view came back **solid
  black** and the left view was a wall of larder door. **The VLM loop returned `no rescale / no
  rotation / no wall overlap` on that build.** Not a hint, not a noisy vote — silence, on a render
  that was literally a black rectangle. → Fixed with `modulate_scale=1.10`, calibrated BY EYE over
  three cheap phase-1 builds (1.00 = two blind cameras; 1.25 = all clear but a ring of dead floor;
  1.10 = clear + a working aisle). **Two rules.** (a) This is bakery's "a fixture taller than
  ~1.4 m at a wall centre blinds that view" at its extreme — but where bakery at least produced
  hallucinated rotation flags, here it produced NOTHING. **Open all four views yourself, every
  build; a clean feedback string is not evidence that a render exists.** (b) `modulate_scale > 1.0`
  is NOT always the "inflate the room to dodge overlaps" anti-pattern — with no overlaps and a
  single huge hero it is game_room's *the hero's clearance sizes the room*, and it is the correct
  lever.
- **[kitchen_set v1, a shrink vote you must decline PERMANENTLY]** After the fix, `RoomProportions`
  kept voting `rescale room by 0.9` on a render that read correct. → **Declined, and flagged in the
  program so it stays declined**: the vote is asking to go back to the exact size that BLINDS the
  cameras. The occupancy metric cannot see cameras, so on a set-piece scene it is structurally
  wrong, not merely noisy. Cousin of corridor's "the shrink vote never goes quiet on a passage
  room" — but sharper: here obeying it destroys the renders, not just the feel.
- **[kitchen_set v1, the SET-PIECE inverted vibe layer — phase 2 is deliberately EMPTY]** A fitted
  kitchen SET is one mesh bundling cabinets, hob, hood, oven, sink and fridge. **Nothing may be
  placed on, in, or around it** — no `place_on_top`, no `place_inside`, no `place_rug`, and above
  all no `add_lighting` anchored to it (a pendant group anchored to a set spreads fixtures across
  the whole footprint and clips them into the cabinets). Same for a separate breakfast counter: the
  stools AT it are the point, smallwares ON it are not — so pin a **bare-top** counter mesh (the
  best-matching blue island `future/a360edba` has bowls and a jug modelled INTO it). The entire
  decor layer is therefore FLOOR + WALL: rug, floor plant, framed print, window, and the pendant on
  the BAR group. The room reads right BECAUSE the worktops are clean — operating_room's inverted
  vibe layer, now with a second worked example. Gate 2 of the flow was overridden for exactly this
  reason, with the rationale recorded in provenance.
- **[kitchen_set v1, a wrong TEXTURE MATCH and a paled correct match look identical — settle it
  offline]** The floor rendered salmon-pink for `"warm oak wood plank floor"`. Rather than guess a
  new wording and pay 8 minutes per build, resolved the string through `WallTextureRetriever`
  directly and opened the matched `texture.png` (~5 s, office_modern's rule): the match really IS a
  salmon-pink plank, and so is `"medium brown oak wood plank floor"`. A genuine MATCHING bug, not
  bakery's "the retrieval was right and the renderer paled it". → `"dark brown hardwood floor"`
  matches a real warm oak. **Always disambiguate the two failure modes offline before rewording.**
- **[tv_studio v1, "no rotation" does NOT mean things are AIMED right — user catch]** The two studio
  light stands were placed with `facing="back"` and the VLM said `no rotation` on every build; the
  user still saw the dishes pointing past the anchors. `facing=` only squares an object to a WALL —
  from the camera lane's left/right corners, "square to the back wall" still aims a dish 30° wide of
  the talent, and the `RotationConstraint` has no concept of a light's *beam* (it checks seating and
  desk fronts). Same for the laptop, whose screen faced the camera instead of the person using it —
  `place_on_top` seats and sizes a prop but **never aims it**. → `room.face(light, toward=desk)` on
  each stand and `anchor_set.face(laptop, toward=seat_pair)`; both run at the end of compile off the
  settled positions. Lesson: **`facing=` is for wall-squareness, `face()` is for aim.** Anything with
  a beam, a lens, or a screen (lights, cameras, monitors, laptops) needs an explicit `face()` at its
  target, and the clean VLM loop will never tell you it is missing — check it by eye (from the
  room-front camera you should see the laptop's LID).
- **[kitchen_set v2, ALIGNMENT is invisible to the whole loop — a fitted unit must go in a CORNER]**
  v1 placed a complete fitted kitchen SET at `place_on_back_wall_center`. It linted clean, rendered
  clean and converged `no rescale / no rotation / no wall overlap` — and it looked **wrong**: a U-set
  centred on a wall projects BOTH wings into open air, so the kitchen reads as a freestanding block
  dumped on the floor rather than as joinery installed against the building. **The USER caught it;
  nothing in the loop can.** (Kunal, 2026-07-13.) → Rule, by `shape` tag: an **L** goes in the corner
  its leg points into (so the leg lies ALONG a wall); a **U** goes in a corner (back run on one wall,
  one wing flush along the adjoining wall — two runs is the most a U can align); a **straight** run
  can take a wall centre but still reads better cornered. And the U's corollary: the third wing
  CANNOT touch a wall, so give it a job — put a functional group (breakfast counter, dining zone)
  BEYOND it and the exposed wing instantly reads as an open-plan **peninsula dividing cook from eat**
  instead of as a mistake. Windows go on a wall OPPOSITE the unit's corner, so daylight rakes ACROSS
  the cabinetry rather than backlighting it. Generalises past kitchens: **for any wall-hugging
  set-piece, alignment to the architecture is a composition judgement the VLM loop does not make.**
- **[kitchen_set v2, two silent API traps that break a corner placement]** (a) **`facing` is
  mandatory on a corner op.** Omitting it does NOT mean "no rotation" — `facing_to_rotation()` raises
  on `None`, so the `@placemethod` heuristic fills one in, and for a corner it chose `"left"`
  (**-90 deg**), silently spinning the whole U round to open sideways with its back run against the
  wrong wall. Pass `facing="front"` for rotation 0. (b) **Corner ops are never re-pinned flush.**
  They set a flush position from `wall_deltas` on both axes, but `place_on_*_corner` is NOT in
  `WALL_FURNITURE_OPS`, so `_repin_wall_furniture` skips it — and the GradSolver's exploration floor
  walked the set **0.44 m off the back wall** (living_room_cozy's thin-wall drift, now on a hero).
  Fix: `obj.is_static = True` — its gradient is zeroed every step so it never moves, while still
  exerting force on neighbours. Result: 0.000 m gap to both walls, verified in the blend.
- **[kitchen_set v2, a room-size vote you refute with ARITHMETIC, not taste]** With the set static
  and flush in a corner, shrinking the shell slides the walls toward a FIXED hero, so camera
  clearance becomes a closed-form bound: the front camera clears the set iff `W > 2 x set_width`
  (5.70 m) and the left camera clears the wing iff `D > 2 x wing_depth` (5.98 m). The VLM's
  persistent `rescale room by 0.85` gives 5.44 x 6.22 — i.e. **the front view goes solid black.**
  Settled at **0.92** (5.89 x 6.73), a real shrink with margin on both bounds. → **When a hero is
  pinned, compute the modulate_scale floor instead of negotiating with the occupancy metric.** Also:
  the DEPTH bound is why the dining zone exists — a front-row occupant pushes D past 5.98 m, which
  is a cleaner lever than `modulate_scale` (that would inflate the width too, and the width was
  already right). Room size is a consequence of slot occupancy; use the slots.
- **[operating_room v2, a user-supplied glb zip is NOT ingest-ready — three SILENT violations]**
  `hospital.zip` (Sketchfab-style medical glbs) broke the ingest contract three ways, none of
  which ingest complains about: (a) **multi-mesh** — 15 of 18 glbs had many meshes (the
  sterilizer had **143**), and both loaders keep only `imported_objs[0]`, so they would render
  DISASSEMBLED with the rest stranded at the origin; (b) **wild units** — an ENT unit 420 m
  wide; (c) **off-center origins** — the first ingest emitted `[Lint] FLOATS 0.81 m` / `is SUNK
  0.43 m` on every asset. Fixes, all in ONE Blender pass at the SOURCE: `join()` (preserves
  material slots — a trimesh concat STRIPS them → flat white, and a Scene round-trip explodes
  the mesh), uniform-scale to a real-world height, then `origin_set(ORIGIN_GEOMETRY, BOUNDS)` +
  zero the location. Note recentering rewrites the file → **the sha1 ids change → re-pin**.
  Never fix a float with a translate hack in the scene; fix the mesh.
- **[operating_room v2, an ingested asset's CAPTION and SCALE are both VLM guesses — trust
  neither]** The ingest VLM captioned the draped mayo stand a *"blue powder-coated drill press"*,
  the instrument tray a *"trough planter"*, and an operating table a *"blue glass decorative
  sphere"*. Two consequences: a mis-captioned asset is **invisible to NL retrieval** (so pinning
  by id is mandatory, not a preference), and its `scale` — a guess at real-world WIDTH — silently
  RESIZES the mesh (the anesthesia machine loaded 0.86 m tall; a real one is ~1.5 m). Every
  ingested pin gets `get_whd()` + an explicit height fit. Same failure class as the dataset's bad
  `scale` metadata (corridor 2×, children_room 6×) — ingesting does not escape it.
- **[operating_room v2, FILENAMES LIE — the preview is the evidence, and the yield is low]** All
  three `surgical_table*.glb` were draped INSTRUMENT tables, not patient tables (the dataset mesh
  stayed the hero); `c_arm_neurosurgery_operating_table.glb` rendered as a black chair; two glbs
  rendered as unidentifiable blobs. **6 of 20 ingested assets were usable** — a normal yield.
  Build a contact sheet of the ingested previews and eyeball it BEFORE writing placements
  (toy_shop's caption≠mesh rule, now applied to ingest).
- **[operating_room v2, the USER's "not enough relevant assets" diagnosis beat the clean VLM
  loop]** v1 converged fully clean (`no rotation / no wall overlap`, no lints, room vote settled)
  while the anesthesia machine was a med cart and the sterile trays were BATH TOWELS. The loop
  cannot see that — it checks geometry, not whether the props are the right *objects*. Ingesting
  6 real meshes changed the room more than every layout iteration combined. **When a scene is
  "clean but doesn't convince", the answer is usually assets, not placement** (the jewelry_shop
  product rule, escalated: sometimes you must go get the product).
- **[clothing_store v1, THE BIG ONE: an ingested scan's `scale` is a GUESSED WIDTH — big fixtures
  arrive as MINIATURES, and every reflex makes it worse]** The `ShopFixtureRetriever` customs are
  scans of real shop fittings, authored in real metres, but each one's retrieval `scale` (a VLM's
  guess at its width from a preview) is applied on load. For the big ones the guess is *far* too
  small: a **5.27 × 2.25 m clothes-on-hangers merchandising WALL loaded at 0.6 m** (I hung it as wall
  art), the 2.13 × 1.70 m shoe/bag case loaded at 1.6 m wide, the **1.85 m mannequin loaded at
  1.06 m** — a toy-sized person. Then I compounded it twice: (a) **height-normalising** each fixture
  (`sized_h`) preserves the already-shrunken aspect and re-shrinks it — `sized_h` is for TAMING a
  fixture that would tower, and is exactly wrong for one that is already a miniature; (b) the room
  read empty, `RoomProportions` sang *shrink* for five straight builds (0.77 → 0.80 → 0.84 → 0.60 →
  0.88) and I kept obeying with `modulate_scale`. **The floor was empty because the FURNITURE WAS
  TOY-SIZED, not because the box was big** — shrinking the box hides the symptom and locks the bug in.
  → Fix: read the RAW glb extents (`trimesh.load(glb, force='mesh').extents` — NOT `get_whd()`, which
  reports the already-scaled size), pin the true width with a uniform `obj.scale(true_width)`, and let
  `RoomGroup` auto-size (129 m² — a store full of 2 m shop fittings simply IS big). Generalises the
  garage-car / hospital-bed rule ("for any uncurated hero, pin the id AND a real-world dimension")
  with a cheap way to find the number. **USER CATCH — nothing in the loop checks whether furniture is
  the size it is supposed to be.**
- **[clothing_store v1, true-size fixtures trip the wall-centre camera rule constantly]** An interior
  camera sits at each wall's centre at ~1.45 m looking ACROSS the room, so a fixture taller than that
  parked at a wall centre **swallows that camera**: the 2.25 m apparel wall (left-centre) and the
  1.70 m shoe case (right-centre) each rendered one interior view as black geometry, and a 1.85 m
  mannequin at `place_on_front` filled the entire back-wall view. → **Slot big runs to the wall ENDS**
  (`_left`/`_right`), keep the CENTRES for wall-HUNG pieces (flat, and behind the camera) and the
  browsing lane; put a storefront mannequin row at `place_on_front_left`, not `place_on_front`.
  Bakery's ~1.4 m rule at full strength — a retail scene with real fittings will hit it every time.
- **[clothing_store v1, `bottom=` on wall-ADJACENT furniture always trips the floaters lint]**
  `lint_floaters` exempts only true `place_on_wall_*` items (they set `ignore_overlap`); a
  `place_on_<wall>_wall_<pos>(…, bottom=0.9)` shelf is FLOOR furniture lifted off y=0 → `FLOATS
  1.35 m`. So a wall merchandising unit is either **genuinely flat and HUNG**, or **floor-standing** —
  there is no legal middle. (retail_store's `bottom=0.4` shelves would lint today.) And the hang path
  is no escape: `place_on_wall_*` **auto-scales a hung piece to ~0.6 of a wall third**, which blew an
  0.8 m shoe ledge up to **0.38 m deep** → `WARNING: will read as furniture FLOATING in mid-air`. You
  cannot pre-shrink your way out of it; hang only mirrors/canvases/signs.
- **[clothing_store v1, a fixture whose mesh has a GLASS backing hides its own product]**
  `custom/d7cf7f12…` ("grey metal double-rail rack hung with garments") carries a large smoked-glass
  panel that its low-res catalog preview doesn't show; two of them as the centre spine rendered as
  brown glass partitions **tinting their own garments**. No lint, no VLM signal — caught by eye in the
  full render. The jewelry_shop rule ("an empty fixture names the fixture, not the shop") has a
  sharper edge: **a fixture that OCCLUDES its merchandise is worse than no fixture** — swap it.
- **[clothing_store v1, lighting density INVERTS with floor area — a 129 m² datapoint]**
  `density=0.02` on the big true-size shell = **41 discs, starfield** (lint budget ~39) → **0.01** =
  a calm 21. Note this contradicts the lint's own generic hint ("~0.05 for a medium room"): density is
  a COUNT that grows with area, so **bigger room ⇒ LOWER density**. Trust the printed budget. Ladder
  now: café ~0.01 · 50-60 m² shop ~0.015 · **~130 m² retail floor ~0.01**.
- **[clothing_store v1, "warm lighting" is the ENVELOPE, not the fixture]** The brief asked for "warm
  retail lighting", but `add_lighting` has a fixed white budget — greige walls over pale marble
  rendered cool/clinical. `wall_texture="warm sand beige plaster"` + wood table tops carried the
  warmth. (music_studio's "carry the accent with a prop", applied to the shell: you cannot light your
  way to warm.)
- **[clothing_store v1, don't crown a counter whose product is MODELLED IN — check the FREE surface,
  not the footprint]** The cash-wrap scan (`custom/eedaa74b…`) is 1.55 m tall *including* an
  integrated POS screen standing on its counter top, so its usable surface is a narrow strip either
  side of the screen. `checkout.place_on_top([folded stack, handbag])` duly seated props on it anyway:
  `place_on_top` runs a VLM tournament that finds *some* horizontal region and puts items there — it
  has no notion of a surface being ALREADY OCCUPIED or simply too small (the same blindness that
  seated a table lamp on an armchair cushion in living_room_cozy v3). Nothing flagged it; the USER
  did. → Placed the counter **bare** (the mesh's own POS already satisfies the brief's "register").
  **Rule: before any `place_on_top`/`place_inside`, ask what FREE top AREA the anchor actually has —
  a fixture that ships with its product wants nothing added.** Companion to the existing anchor rule
  ("`place_on_top` always targets the group's ANCHOR"): the anchor can be right and the surface still
  wrong.

- **[art_studio v1, `place_on_top` SHATTERS on a SKELETAL anchor — and the loop calls it clean]**
  `easel_unit.place_on_top(canvas)` with an A-frame artist easel as the anchor rendered a
  **postage-stamp canvas parked on the easel's lower crossbar** — on both easels. Cause: an easel has
  no *substantial horizontal region*, only the slivers of its crossbars, so `detect_horizontal_regions`
  tiles a sliver and `TILE_FOOTPRINT_FRAC` clamps the canvas to that microscopic cell. This is the
  documented flat-rug failure (a rug anchor → 0.029 m tiles → 3 cm bean bags) **generalised: an anchor
  with no real TOP — a tripod, an easel, a skeleton, a frame — cannot be stacked on.** `no rotation` /
  `no wall overlap` / zero lints on the build that contained it: the geometry is legal, only the
  semantics are absurd. Caught by EYE in the cheap phase-2 render. → **There is no rescue via a lift**
  (`bottom=` exists only on `place_on_<wall>_wall_<pos>`, never on an anchor-group placement), so
  compose it GEOMETRICALLY instead: stand the canvas on the floor hard against the easel and let the
  A-frame rise behind it — deterministic, no tournament to lose. **Rule: before reaching for
  `place_on_top`, ask whether the anchor HAS a top. If it doesn't, the answer is an adjacency, not a
  stack.** (Companion to living_room_cozy v3's "`place_on_top` always targets the ANCHOR" and
  clothing_store's "check the FREE surface": here the anchor is right, and the surface doesn't exist.)

- **[art_studio v1, ANCHOR A UNIT ON THE PIECE WHOSE FACING CARRIES THE READ]** Having moved the
  canvas off `place_on_top`, v2 anchored the EASEL and hung the canvas off it with
  `place_on_front_adjacent`. The canvas turned its **blank BACK** to the room — because the `*_front*`
  verbs bake a **face-the-anchor** rotation (the seating semantic: a chair in front of a desk turns to
  face it). Flipping it per-asset is a trap: mesh fronts are unnormalised and the two canvases
  disagreed with each other. → **Anchor the CANVAS, hang the easel off its back**
  (`place_on_back_adjacent(easel)`). The piece whose orientation matters is then the anchor, so it
  inherits the room's own `facing=` — the same mechanism that already aimed the leaning canvas row
  correctly — and the near-symmetric A-frame's facing stops mattering. **Rule: when composing a unit,
  anchor it on the piece whose ORIENTATION carries the read, not on the piece that is structurally
  "underneath" it.** No VLM signal fired in either direction (`no rotation` on a canvas facing the
  wall); the render is the only detector.

- **[art_studio v1, "FILL THE FLOOR INSTEAD OF SHRINKING" IS NOT UNIVERSAL — a fill that claims a ROW
  grows the shell]** The shrink vote ran `0.75 / 0.7 / 0.81 / 0.5 / 0.7 / 0.65 / 0.75` — unidirectional,
  so signal — and the standard play is children_room/kindergarten's *fill before shrinking*. **Every
  fill made it worse.** A second composed canvas row grew the shell **5.60 → 6.86 m wide** in a
  front-WALL slot *and* in a corner floor slot alike; parking the supply cart in the `right` FLOOR slot
  forced the middle row to fit easel + table + cart, blowing the width to 6.70 m while the DEPTH
  collapsed to 4.39 m and **jammed the back camera against the table** (all measured off the exported
  floor mesh, not guessed). → The distinction that makes greenhouse's plant-bed work: **a bed is ONE
  object holding a dozen plants, so it costs ONE slot and adds no width. A composed ROW is not free —
  it lands in a row/column the shell must then grow to fit.** So: fill-don't-shrink holds only when the
  fill costs no slot; otherwise SHRINK. Resolution here was one decisive `modulate_scale=0.85`,
  deliberately **short of** the vote (a painter must step BACK to judge a canvas — the open floor is the
  category, as with garage's vehicle lane and corridor's centre lane); the vote decayed to `0.8` and was
  declined. **Corollary: a wall placement costs no floor slot — use the walls when you must add without
  growing.**

- **[art_studio v1, a rotation vote on a ROTATIONALLY SYMMETRIC object is self-identifying noise]**
  `rotate round stool by 180 to face the work table` (twice, one build) on a **round backless stool**
  that was already `face()`d at the table. A round stool has no front — there is nothing to rotate. →
  Declined; it did not recur. Same class as living_room_cozy's phantom accent chairs: when the vote
  names an object that cannot have the defect, the vote is the defect.

- **[laboratory v1, an ingested mesh whose ORIGIN is 118% of its height off-centre — and the
  ingest batch's UNUSED meshes are all still broken]** The microscope — the one prop that makes
  the room a lab — **sank 0.23 m through the bench top**, its base poking out underneath, so at
  room scale it read as **standing on the floor** beside the bench. The reagent bottles seated in
  the SAME `place_on_top` call were flush (bottom = 0.900 = the bench top exactly), and the entire
  VLM loop was clean about it (`no rotation / no wall overlap`, no lints, no warnings) — a sunk
  prop is *geometrically* fine, and "the microscope is inside the table" is semantics. Caught by
  EYE. Root cause: the mesh's geometry sits ENTIRELY ABOVE its origin (y-bounds `+0.444..+1.094`,
  offset **+118%** of its own height), violating the centred-mesh invariant `ingest.py::_copy_centered`
  exists to establish; `place_on_top` seats by an origin it assumes is the bbox centre. Diagnosed in
  ONE offline probe (print the anchor's AABB **top** vs the item's AABB **bottom** — computer_room's
  method) plus a 5-second read of the glb bounds; fixed at the SOURCE in Blender (`origin_set
  ORIGIN_GEOMETRY/BOUNDS` + zero the location — it **preserves material slots**, which a trimesh
  round-trip strips → flat white), written back under the SAME filename so the id, the embedding and
  every pin stay valid (no re-ingest, no re-pin). **The generalizable rule: an ingest batch's UNUSED
  meshes never got its repair pass.** operating_room v2 fixed the multi-mesh/units/origins of the 6
  glbs it shipped; the other 14 sit in `custom/` still broken, and this scene hit TWO of them (the
  gas cart, origin −26% off, floated 0.62 m and tripped a phase-1 `[Lint]` — it is the autoclave
  mesh ingested TWICE, same 2.66 m height, one copy with a broken origin). **When you pin a mesh from
  someone else's ingest, read its glb bounds BEFORE you build.**
- **[laboratory v1, a `0.5` shrink vote that was not about room size at all]** Phase 1 voted
  `rescale room by 0.5` — extreme. Per kitchen v1 (*the occupancy vote tells you THAT the room is
  wrong, never WHICH group made it wrong*) I hunted the footprint culprit instead of reaching for
  `modulate_scale`: the bench `GridGroup` sat at `sparsity=0.3`, flinging four benches into a bbox
  the shell had to grow to fit. Tightening to **0.12** (benches in a real lab stand close) moved the
  vote **0.5 → 0.88 in a single build**, with the shell untouched. Then the usual: held per
  render-wins-early, applied ONE `modulate_scale=0.92` in the final phase — deliberately just SHORT
  of the 0.9 vote, because the centre bench block is a RIGID GridGroup and a shell shrunk below the
  footprint its placements dictate makes fixed-size rows overflow their slots (locker_room/kitchen) —
  and **declined the residual `0.9`** on a render with clear working aisles (bookstore's rule; a
  lab's circulation lane is functional space, like garage's vehicle lane).
- **[laboratory v1, "the dataset has no X" can be false while X sits in the pool — grep `custom/`
  by hand]** A 36-query stress test returned **`0.000` — an EMPTY candidate list, not a bad pick —
  for twelve of the category's identity props** (fume hood, microscope, centrifuge, bunsen burner,
  beakers, flasks, test-tube racks, petri dishes, eyewash…), which reads as "this category is
  unbuildable". It isn't: a real binocular **microscope**, a lab **autoclave** and a **gas-cylinder
  cart** were already in `custom/`, left over from the operating-room `hospital.zip` ingest. They
  score 0.000 because ingested meshes only surface through retrievers that merge the `custom` kind —
  so **a query can score zero against a dataset that contains the object**, and pinning by id is
  mandatory (operating_room v2's rule, now with teeth). **Before concluding a category needs an
  ingest round, grep the custom pool's descriptions by hand.** The two genuinely-absent props were
  handled the two honest ways: the glassware was found by SILHOUETTE (no beaker exists, but *"a set
  of three decorative glass DECANTERS with stoppers"* IS a row of reagent bottles at room scale —
  tv_studio's rule), and the **fume hood, which has no substitute at all** (the top "stainless steel
  cabinet" hit is literally a **barbecue grill**), was NOT faked — the scene was reframed as a
  **bio/analytical lab, the sub-category the library can actually carry**. *Choosing the sub-category
  your assets can support is a legitimate design move, and a better one than shipping a wrong prop*
  (casino's poker-chip rule, taken upstream into the brief).
- **[laboratory v1, the GRID is not the category — the PRODUCT is]** classroom, computer_room and
  laboratory are **the same layout** (a desk/bench unit tiled across the floor); strip the props and
  all three render as the same room. What makes this one a lab is the **microscope + reagent bottles
  on every bench at working height** — jewelry_shop's product rule and greenhouse v2's density-grain
  rule ("when two categories share a layout pattern, the tie-break is the product"). The bench grid
  converged in one iteration; the props took the whole scene. Budget accordingly.

- **[waiting_room v1, a back-centre print behind a reception desk is ALWAYS crossed by the monitor —
  and the fix is ASPECT, not size]** The focal print hung at `place_on_wall_back_center` came back with
  the iMac's white back **bisecting it**. This is structural, not bad luck: wall art mounts centred at
  **~1.5 m**, and a reception counter (1.10 m) with a monitor on it tops out at **~1.6 m**, so *any*
  back-centre art is crossed. **Nothing fires** — the automatic wall-object clearance pass only slides
  **FLOOR** objects out of a wall item's span, never a `place_on_top` item, and there is no `bottom=`
  lift on the wall-HUNG path to raise the art (it exists only on the wall-ADJACENT path). The instinct
  — make the art bigger — is a trap: wall scaling is **uniform**, so widening the PORTRAIT print
  (0.40 x 0.54, aspect 0.74) to 1.4 m would have made it **2.16 m TALL**. → Swapped for a **1.92-aspect
  PANORAMIC** (`hssd/950c82d2`) at `width=1.4`: the monitor now interrupts only a small central strip
  and the artwork reads on both sides and above — a desk in front of a picture, as in a real clinic.
  **Rule: a wall item's ASPECT RATIO is a layout property — check it with `get_whd()` before you hang,
  the same way you check depth (<0.25 m) and whether the frame is empty.** (Same family as prison_cell's
  rejected vision-hatch and tv_studio's un-hangable backdrop: wall items fight your own furniture, and
  the geometry is knowable before the build.)
- **[waiting_room v1, the EMPTY-FRAME trap is not just picture frames — a wall CLOCK can be a blank
  disc]** Adding the clock (the one prop that says *waiting room* — you watch it while you wait), the
  contact sheet showed **6 of the 8 top hits are featureless white DISCS**: no face, no hands, no
  numerals. Shipped, that is a **dinner plate on the wall**, and neither the VLM loop nor any lint would
  ever say so (the geometry of a blank disc is perfect). Only `hssd/e1725f63` has a real face. →
  Generalises office_modern's empty-frame lesson past framed art: **any flat wall category — clocks,
  mirrors, signage, boards — is full of meshes whose FRONT is blank. Eyeball the contact sheet; that IS
  the gate.**
- **[waiting_room v1, "rows of linked chairs" has no mesh — PACK a GridGroup instead]** The hero of the
  prompt was a dataset gap, and both escape routes were wrong: the only genuine multi-seat meshes
  (`hssd/14c4e5a4`, `hssd/61d4e356`) are rows of moulded **cafeteria** chairs, and every "upholstered
  waiting bench / public seating bank" query returns a **domestic three-seat sofa with throw pillows** —
  geometrically fine, categorically absurd in a clinic (prison_cell's floral-curtains rule). →
  Built the bank out of SINGLE chairs and **packed** them: `GridGroup(sparsity=0.05)` runs **no overlap
  solve**, so they stay abutted and read as one linked bank (greenhouse v2's plant-bed trick, applied to
  seating); built ONCE and `2 * bank` duplicated onto both long walls, which also bought the room shape
  for free. **When a repeated fixture doesn't exist as a mesh, ask whether it is just N of a mesh you DO
  have, tiled with the solve turned off.**
- **[waiting_room v1, the plan's material rendered as a BLACK MONOLITH — form factor is an eye catch]**
  The plan asked for a slim glass table; the best glass mesh (`future/fcea3d53`) has dark glass + a dark
  lower shelf and rendered as a **solid black slab** — a heavy monolith in a calm beige clinic, with the
  magazines destined to sit on it. `no rotation / no wall overlap`, no lints: the geometry is perfect and
  *"that reads as a black box"* is semantics. Caught in the **cheap phase-1 loop** and swapped for an
  open-frame walnut top that echoes the reception counter. **Dropped the plan's MATERIAL, kept the plan's
  WARMTH** — the same call as living_room_cozy's corner fireplace (a mesh's form factor is a layout
  property, and phase 1 is where it surfaces) and operating_room's "the plan can be wrong about its own
  category."
- **[waiting_room v1, room size — fill the floor, then stop SHORT of the vote on a row-packed room]**
  `RoomProportions` sat at `0.8 → 0.9 → 0.8 → 0.9` across the phases. Held per render-wins-early, then
  **filled** the bare floor with the pieces the plan already named (palms flanking reception + an entrance
  water cooler) rather than crushing the shell — because the two seat banks are **rigid GridGroup rows**,
  and a shell shrunk below the footprint they dictate makes fixed-size rows overflow their slots
  (locker_room). Applied ONE decisive `modulate_scale=0.95`, deliberately well short of the vote; it
  decayed to `0.95` ≈ neutral → converged. The open centre is also the **walk-up lane to the desk** —
  legitimate circulation that an occupancy metric always reads as "empty" (garage/corridor). Combines
  kindergarten's "fill, don't crush" with kitchen's "a room whose walls carry rigid rows stops short."

- **[closet v1, the shrink vote was RIGHT that the room was wrong and WRONG about the fix]**
  `rescale room by 0.8` held for FOUR straight builds on a walk-in closet that had auto-sized to
  4.48 x **8.15 m** — an eight-metre closet. Obeying it is the locker_room trap (the shell would
  drop under the wall runs' own footprint and overflow them), but declining it as "occupancy noise"
  would have shipped a corridor. Both readings are wrong because the vote cannot localise: the room
  was too LONG, not too big, and the cause was one number — **room DEPTH = 3 wall slots x the
  WIDEST wall item**, and that item was a 2.5 m closet system. → Trimmed the wall items (2.5 -> 1.8 m,
  which shortens the slot grid HONESTLY), filled the dead entry third with a valet rail of clothes
  (kindergarten/greenhouse: *a persistent shrink vote on a wall-packed room means ADD FURNITURE*),
  and applied ONE safe `modulate_scale=0.9` on top. 36.5 m² -> 30.8 m², aisles intact. **Generalises
  kitchen's rule to WALL runs: the occupancy vote tells you THAT the room is wrong, never WHICH
  piece made it wrong — and for a wall-loaded room the culprit is almost always the widest item on
  a wall, because it sets that wall's whole slot pitch.**
- **[closet v1, the residual vote bounced across IDENTICAL builds — declined permanently]** After
  the fix the vote read `0.8 -> 0.9 -> 0.8 -> 0.78` across **re-runs of the same program**. An
  oscillation across repeated builds is measurement noise, not signal (office_modern), and a
  walk-in's dressing aisle is working floor that an occupancy metric always reads as emptiness
  (garage's vehicle lane, corridor's centre lane). Stopped; the render is well-filled.
- **[closet v1, the float lint's OTHER false-positive class: a mesh authored as a WALL unit]**
  `[Lint] FLOATS 0.45 m` (folded-goods shelf) and `FLOATS 0.20 m` (shoe rack) on floor placements.
  Unlike prison_cell's washbasin (a `bottom=` mount the lint simply doesn't exempt), these had no
  `bottom=` at all — they are **wall-mounted meshes I had placed as floor furniture**, and one is
  literally captioned "*floating* black shoe shelf". The lint's stock advice ("off-center mesh
  origin — swap the mesh") is aimed at floor furniture and is wrong here. → Fixed by MOUNTING them:
  the wall-adjacent + `bottom=` path with `ignore_overlap` + `is_static` (the range-hood recipe;
  both are 0.37-0.63 m deep, far past the 0.25 m limit where `place_on_wall_*` would float them as
  art). `lints.py` skips `ignore_overlap` children, so the lint went quiet **because the placement
  became honest**, not because it was silenced. **Rule: before obeying "swap the mesh", ask whether
  the mesh is floor furniture at all — a wall unit floating is a placement bug, not a mesh bug.**
- **[closet v1, uniform scaling couples W to H — so a mesh's ASPECT can be the defect]** The closet
  system (2.50 x 1.93 m, clothes + shoe shelves — a lovely mesh) fitted to the 1.8 m slot the room
  length could afford came out **1.39 m tall**: a stunted run under a blank wall band, facing two
  1.91 m bays. Tall would have meant wide, and wide was what made the room 8 m long. The full VLM
  loop was clean throughout (`no rotation / no wall overlap`, no lints) — the geometry is perfect;
  "this wall looks stunted" is composition. → Swapped it for a third matching wardrobe bay (twin
  floor-to-ceiling runs, as the plan asked). **A mesh whose aspect ratio fights your slot grid is
  the wrong mesh, however good its preview** — the same class as living_room_cozy's corner
  fireplace (form factor is a layout property), and again a look-at-it call, not a signal.
- **[closet v1, the camera rule applied PREVENTIVELY — four clear views on the first build]**
  A walk-in closet is the worst case for the blinded-camera trap (kitchen_set): narrow, with deep
  cabinetry on BOTH long walls. Rather than discover it in a black render, derived it first from
  `renderer/utils.py` — the camera sits at `0.55 x ceiling` height and `0.04 x room_dimension` in
  from the wall OPPOSITE the one it shoots (~0.18 m in a 4.6 m room), so any deep piece at a wall's
  CENTRE contains it. → Designed the wall slots around it: tall bays in the END slots, and each
  long wall's CENTRE slot given a piece under ~1.3 m (folded-goods shelf 1.07 m; shoe rack topping
  out at 0.48 m). Both side views were clear from the first phase-1 build and stayed clear. The low
  centre pieces cost nothing — they are what belongs mid-run in a real closet anyway. **This is what
  the worked examples are FOR: office_modern applied bakery's rule at design time; this applies
  kitchen_set's, with the arithmetic written down so the next narrow room can just use it.**

- **[dining_room v1, the brightness dial FLIPS at phase 3 — it is the light BUDGET, not the sky]**
  The room converged fully clean (`no rotation` / `no wall overlap`, zero lints, size vote 0.99)
  and rendered as a **bright showroom** against a "warm, lived-in" brief. Reached for greenhouse's
  rule ("brightness is a SKY setting, never `add_lighting`") and it did almost nothing. MEASURED
  (mean pixel value of one fixed view): sky 3.0→1.2 moved a PHASE-1 render **139→105**, but sky
  3.0→1.5 moved the FULL render only **197→188**. Cause: phase 1 has no `add_lighting`, so the sky
  IS the light; phase 3 hangs the pendant, whose **fixed 500 W** (`object.py`: 500/N) then dominates
  a ~27 m² room and flattens every surface to near-white. → `scene.light_budget = 180.0` (the dial
  wine_cellar added, reached here from the BRIGHT side) — the pendant became a warm pool over the
  table while the glazed wall still supplied daylight. **Rule: sky is the lever for an unlit or
  glazing-lit room; the moment you hang a fixture, the budget is the lever.** And wine_cellar's
  warning is what kept this legible: tune ONE dial at a time, or they cancel and you conclude the
  lever is broken.
- **[dining_room v1, TOOLING — `IDSDL_SKY` in the program is a no-op under WORKBENCH too, not just MCP]**
  wine_cellar's fix was "the warm MCP server binds the sky at import → build mood scenes from the
  shell." Incomplete, and it cost a full build: `renderer/utils.py` binds `INTERIOR_SKY_STRENGTH` in
  a **class body** at import, and `workbench.py` imports `IDSDL.service` at its own line 30 *before*
  `runpy` executes the program — so `os.environ["IDSDL_SKY"]` inside the program is already too late
  under workbench as well, and the render comes back silently at 3.0 looking like a broken lever.
  → **Export it in the shell**: `IDSDL_SKY=1.5 python workbench.py run <prog>`. (A program-level
  `setdefault` only works for `python <prog>.py` directly, where nothing has imported IDSDL yet.)
  Diagnose it in ~1 min with a phase-1 A/B, not an 8-minute full build.
- **[dining_room v1, a room-size vote that never leaves ±5% is noise, not a train]** `1.05` (Ph2) →
  `0.97` → `0.99` across full builds. → **Declined outright** — no application at all. The vote-train
  rules (living_room_cozy's unidirectional decay, laundromat's persistence) are for votes that
  actually commit to a direction; one that oscillates inside the noise band around neutral is
  casino's declined 1.05, and acting on it would have cost a build to move a room 1%.
- **[dining_room v1, check a wall-art mesh's HEIGHT before you hang it over furniture]** The gallery
  collage is **1.66 m tall**; wall slots centre at y=1.5 m, so its AABB bottom would land at 0.67 m —
  BELOW the 0.85 m buffet standing directly under it, which fires `_enforce_wall_object_clearances`
  and slides the **buffet** sideways off the centre of its own service wall (hospital_room's wardrobe
  mechanic; prison_cell rejected a door hatch on the same arithmetic). Caught OFFLINE with `get_whd()`
  before the first build; pre-scaled the collage to ~0.95 m → blend confirms bottom = 1.28 m, clear.
  **The clearance pass is a LAYOUT force: before hanging anything, compare its AABB bottom against the
  TOPS of the furniture in front of it.**
- **[dining_room v1, the dining-table SET trap defused by the query]** Generic dining/cafe table
  queries return tables with chairs BAKED into the mesh, which double-seats an `AroundGroup` that
  supplies its own ring. → Querying **"a rectangular dark wood dining table, no chairs"** returned six
  bare tables on the contact sheet. Also note the sideboard shortlist skews TALL (the picker's #1 was
  a chest, #2-#4 hutches — all over the ~1.4 m interior-camera eyeline at a wall centre): `browse` for
  a genuinely low buffet and scale it BY HEIGHT (`obj.scale(w*H/h)`) to ~0.85 m.
- **[grocery_store v1, the wall-centre camera rule is TOTAL — a 1.9 m run at a wall centre renders that
  view BLACK, under a perfectly clean feedback string]** v1 placed the stocked gondolas at
  `left_wall_center` (1.93 m) and the glass coolers at `right_wall_center` (2.01 m) — the two obvious
  slots. Both side views came back **pure black**, while the VLM happily reported `no rotation / no wall
  overlap` and a room-size vote. The interior wall-cameras stand at each wall's CENTRE at ~1.4 m, so a
  taller fixture there literally *contains the camera*. The back view survived only because its occupant
  is a **0.93 m** counter — the camera sees over it. bakery found this at 1.6–1.75 m ("swallows the
  view"); this is the same rule at its limit, and it is a **design-time constraint, not a render bug**:
  → **give every wall a centre occupant that is either short (<~1.25 m), or nothing, or an OPENING.** A
  **door is the ideal wall-centre occupant** — it claims no floor, blinds no camera, and its auto-
  clearance keeps the entry lane open. Here the gondolas moved to `back_wall_left/right` **flanking the
  low counter**, which turned out to be strictly better composition anyway (a wall of stocked shelves is
  the money shot from the entrance). ⚠️ `bookstore` hangs **2.1 m** bookcases at `left/right_wall_center`
  and reports clean — almost certainly the same blinded views, never opened. **Open all four PNGs every
  build** (kitchen_set's rule): a clean feedback string is not evidence that a render exists.
- **[grocery_store v1, the shell is the SUM of 5 column maxima — ONE wide group in ONE slot inflates the
  WHOLE room, and the shrink vote GROWS as you chase it]** The plan asked for a "Produce Wall", so I
  built a 3-wide `GridGroup` row of produce tables and dropped it at `front`. The room went to
  **10.4 × 6.6 m** and the shrink vote *grew* — `0.82 → 0.72 → 0.65 → 0.5` — while I kept "fixing" it.
  Cause, straight out of `groups.py:compute_grid_dims`: the room is a **5×5** grid,
  `WIDTH = Σ(max width of each of 5 COLUMNS)` and `DEPTH = Σ(max depth of each of 5 ROWS)` (+0.35
  `CIRCULATION_GAP`; `compute_dims_of_point` swaps w↔d by `facing`, which is why a wall run contributes
  its *depth* to the width). So a 4 m row in the centre column adds **4 m to the room outright**, no
  matter how empty everything else is. → Split it across `front_left`/`front`/`front_right` — **the same
  columns the 2.0 m back-wall gondolas already set** — and it cost the shell **zero**: 7.9 × 6.8 m.
  **Rules: (a) an object placed in a column/row that something wider already occupies is FREE — slot for
  the sum, not for the aesthetics; (b) a wide multi-cluster group in a single slot is coffee_shop's
  cavernous-shell trap, restated arithmetically; (c) the occupancy vote tells you THAT the room is wrong
  and never WHICH slot did it (kitchen's rule) — read `compute_grid_dims` before touching
  `modulate_scale`.**
- **[grocery_store v1, re-check `add_lighting` density AFTER a `modulate_scale`]** `density=0.02` was the
  right bookstore-ladder value for the 54 m² shell, but the final-phase shrink took the room to 43 m² and
  the same density then tripped the deterministic STARFIELD lint (15 fixtures, budget ~13) → **0.012**.
  The fixture count is `1+(max_lights-1)*density` and the *budget* scales with floor area, so **shrinking
  the room silently makes a previously-fine density a starfield.** Lighting is downstream of room size:
  set it last.
- **[grocery_store v1, a shop's produce/perishables have the jewelry_shop problem — the FIXTURES are all
  empty]** The `ShopFixtureRetriever` pool made the *dry* goods free (a genuinely stocked supermarket
  gondola, a wire rack loaded with snack bags, a stocked beverage rack — toy_shop's "the fixture IS the
  product" at full strength, zero crowning). But every produce fixture is a **bare** basket rack, and the
  picker's #1 "crate of fruit" (`hssd/2c751d20…`) renders as a near-empty white BLOB. → **Mass the product**
  (5 fruit crates per low market table). Corollary hit the same build: a **CUDA OOM** (a concurrent build
  shared the GPU) silently dropped `place_on_top` to its AABB fallback, which caps each item at 0.4× the
  anchor height — so a 3-prop table read as clutter. **Massing more items is the fix that survives the
  tournament falling back.**

- **[laundry_room v1, the shell is fixed with SLOTS — and the PLAN already told me which one]** Phase-1
  auto-sized a **4.5 x 3.9 m hall** around 12 m² of furniture (`rescale room by 0.6`). The culprit was not
  the shell scale but the SLOT model: `RoomGroup` sums 5 column-widths + 5 row-depths, and
  `compute_dims_of_point` **swaps w/d by facing** — so a **SIDE-wall item pays its WIDTH in room DEPTH**,
  while a back/front item pays only its (much smaller) depth, and every distinct slot claims its own row.
  Sink, shelf, airer and ironing board sat in FOUR different rows. → Three re-slottings, **zero
  `modulate_scale`**: the sink moved INTO the back-wall run (which the planner brief had *already* asked
  for — "an integrated sink at the counter end"; the plan was describing the cheap layout and I hadn't
  listened), the shelf and airer moved to the two wall-CENTRE slots so they SHARE one row, and the ironing
  board moved to the front wall where its 0.40 m depth pays instead of its 1.20 m width. Vote 0.6 → 0.72 →
  0.80 on structure alone. **Generalises kitchen's "find the footprint culprit": put WIDE things on the
  back/front walls, keep side-wall items thin, give the side walls ONE shared row — and re-read the plan
  before re-slotting, it often names the fix.**
- **[laundry_room v1, `place_inside` cannot carry a category read — the product goes on the LOW anchor]**
  The wire shelf, dutifully stocked with detergent bottles and baskets, rendered as a **bare white bookcase
  with specks on it**. The smart-placement tournament **height-fits each item to a fraction of the ANCHOR's
  height**, so a bottle against a 1.35 m shelf comes out ~0.14 m — invisible from across the aisle.
  **Massing more items does NOT fix it** (each one is just another speck — this is where it differs from
  grocery_store/jewelry_shop, where the anchor was a low table), and `modulate_scale` is a no-op on
  on-top/inside items (tv_studio). → Put the SAME bottles on the **0.9 m folding counter** via
  `place_on_top`: the identical rule now sizes them to a readable ~0.3 m, and they land in the money-shot
  frame. **Restatement of jewelry_shop's product rule: "product at VIEWING HEIGHT" is a fact about the
  ANCHOR, not the camera — the shorter the anchor, the bigger the prop it seats. Stock the tall shelf
  anyway (it is right up close), but never let it carry the read.**
- **[laundry_room v1, the BRIGHT-room mirror of wine_cellar — and an overexposed render is a GARBAGE
  render]** The first full build **blew out to pure white** (the tile floor vanished) the moment phase 3
  added a window and `add_lighting` — a fixed **500 W** budget in an ~11 m² room whose every surface is
  white, on top of the interior sky. Not the fixture (already a flush disc), not the density (0.01 = COUNT,
  not brightness). → **`scene.light_budget = 180.0`**; unlike `IDSDL_SKY` this is a **scene attribute**, so
  it survives the warm MCP server's import-time binding and works through `run_scene`. **A small all-white
  room needs the budget dropped as much as a cellar does.** And the tell: that same blown build emitted
  `rotate door by 90` **twice**, on a door that renders perfectly face-on — the flags **vanished when the
  exposure was fixed, with no layout change**. Bakery's "a garbage view hallucinates rotation flags",
  generalised: **overexposure is a garbage render too. Fix what you can barely read before you believe what
  it tells you.**
- **[laundry_room v1, a room-size vote BELOW the arithmetic floor]** Vote `0.80` at the end of phase 2. But
  the back-wall run is a **rigid `GridGroup` row that cannot compress**, so the shrink has a closed-form
  floor: `WIDTH >= run (3.0) + shelf depth (0.26) + airer depth (0.64) + margin ~= 4.1 m`, i.e.
  `modulate_scale >= 4.1 / 5.03 = 0.82`. **The vote was below its own floor** — obeying it overflows the run
  into the side-wall pieces (locker_room). Applied **0.85**; the vote decayed 0.90 → 0.95 → bounced back to
  0.90 across *identical* builds = measurement noise → declined. **When a wall carries a rigid row, compute
  the floor; don't negotiate with the occupancy metric** (kitchen_set).
- **[grocery_store v1, the miniature-scan trap CONFIRMED on a second scene — and it is what the
  never-quiet shrink vote was really saying]** Independently of clothing_store, three of this scene's
  four `custom/` shop fixtures loaded as **miniatures**, because a scan's retrieval `scale` is a VLM's
  guessed WIDTH applied on load: snack rack **1.44 × 1.80 m authored → 1.00 × 1.25 loaded (31 % small)**,
  promo endcap **1.00 × 1.96 → 0.65 × 1.28 (35 %)**, beverage rack 2.34 × 1.63 → 2.00 × 1.39. Only the
  gondola loaded true. **`get_whd()` cannot detect this** — it reports the already-scaled size, i.e. it
  reports the miniature as fact — so the audit gate's "measure it offline" step passes happily. The only
  witness is the raw mesh: `trimesh.load(p, force="mesh", process=False).extents`. → Pin each back to its
  authored width (`obj.scale(true_width)`). **Diagnostic value: a shrink vote that will not go quiet on a
  room you have already filled is evidence to go re-measure the FURNITURE, not to shrink the shell** —
  obeying it hides the bug and locks it in (clothing_store's exact trap, hit again from the other end).
  **Standing rule: for any `custom/` shop-fixture pin, read the RAW glb extents at audit time.**
- **[fast_food v1, the vote flipped OFF a converged shell — one prop cannot resize a room]** The full
  build returned a clean `no rescale` at `modulate_scale=0.85`. The very next build — **identical except
  for one corner plant added as the vibe layer** — came back `rescale room by 0.9`. Nothing about the
  shell had changed, and a single potted plant cannot make a room 10 % too big, so the delta is the
  occupancy metric's own noise floor, not signal. → **Declined.** Generalizes the bookstore/kindergarten
  oscillation rule to a sharper test: when you can point to *what changed* between two builds and it is
  too small to explain the vote, the vote is noise — don't spend an 8-minute build proving it. (The
  inverse case is [[grocery_store]]'s: a vote that will NOT go quiet on a filled room is real signal, and
  it is telling you to go re-measure the furniture.)
- **[fast_food v1, two wall-opening traps the static lint cannot catch — both cost a full build]**
  (1) **`place_door(wall, position=…)` takes the wall's OWN horizontal thirds — `left|center|right`.**
  There is no `"front"`/`"back"`, on ANY wall. `position="front"` passes the lint (the *kwarg* is real,
  the *value* isn't) and then dies deep inside `RoomGroup.__exit__` → `_register_door_clearances` with a
  bare `ValueError: Label must include one vertical (top/middle/bottom) and one horizontal
  (left/center/right) part` from `wall.py` — a message that names neither the door nor the wall.
  (2) **A floor-to-ceiling window and a door cannot share a wall.**
  `place_window_floor_to_ceiling` registers occupancy on `["left","center","right"]` — **all three slots**
  — and removes the wall entirely. So any "glass storefront" brief (fast food, retail, café) FORCES the
  entry door onto a side wall. Decide that at authoring time; the collision is not what the
  `WallOverlapConstraint` reports on (it stays `no wall overlap` right up until the build throws).

- **[nursery v1, an ALL-WHITE room is an EXPOSURE trap — the loop is silent on it]** The first full
  build came back **blown to pure white**: a big picture window + the default `INTERIOR_SKY_STRENGTH`
  of 3.0, bouncing around a room whose walls, floor, crib, rocker, rug and pouf are *all* white/cream.
  Every surface is a reflector, the room integrates to white, and the pastel envelope — the thing the
  prompt actually asked for — vanishes. Every signal stayed clean (`no rescale` / `no rotation` /
  `no wall overlap`, zero lints), because exposure is not geometry. → `IDSDL_SKY=1.2` restored a daylit
  room whose pastels hold. This is **wine_cellar inverted**: a pale room needs the sky DROPPED for the
  opposite reason a cellar does (nothing absorbs). Rule: **the paler the room, the lower the sky** —
  and brightness is only ever a sky/`light_budget` setting, never `add_lighting` (fixed 500 W / N).
- **[nursery v1, TOOLING — `IDSDL_SKY` works from the SHELL, is IGNORED by MCP `run_scene` (A/B on the
  same file)]** Confirms wine_cellar's gotcha and **corrects** the dining_room README note that says the
  in-program line "is a no-op inside the program under workbench too" — it is not. Identical program,
  only the harness varied: `python workbench.py run …` → correctly exposed, pastels hold; MCP
  `run_scene` → **blown white**. (`sceneprogexec` spawns Blender with `subprocess.run(cmd, cwd=…)` and
  **no `env=`**, so the child inherits `os.environ` and re-imports the renderer fresh — which is why an
  `os.environ.setdefault("IDSDL_SKY", …)` placed *before* `import IDSDL` works under workbench even
  though `INTERIOR_SKY_STRENGTH` is a class attribute bound at import. The warm MCP render path does not
  deliver it.) → **Build any mood/exposure-dependent scene from the SHELL**, and distrust a surprising
  `run_scene` exposure. Sibling of the `run_scene` mtime-fallback gotcha.
- **[nursery v1, a PASTEL wall texture fails twice — and in the OPPOSITE direction to the known trap]**
  `"soft blush pink painted wall"` → **pink bathroom TILES** (a tiled nursery — prison_cell's
  wrong-kind-of-object, at texture level). Reworded to `"plain pale pink painted plaster wall, smooth
  and uniform"` → a genuine **peach paint** swatch… which rendered as strong **SALMON** at room scale,
  i.e. **more** saturated than the swatch — the reverse of bakery/office_modern's "room-scale tiling
  washes dark tones OUT". `"very pale barely-there pink white wall, almost white"` → a desaturated dusty
  blush that holds. → **For a pastel, pick a swatch one notch PALER than the colour you want**, and open
  the matched `texture.png` offline (5 s) before paying for a build.
- **[nursery v1, a BLANK desc in the asset list is a self-identifying junk pick]** The unpinned
  `"a plush stuffed bunny toy"` resolved to a **0.60 × 0.68 × 0.12 m flat slab with an EMPTY
  description** and rendered as a **cardboard box standing on the toy cubby**. The full VLM loop ran
  clean through it (geometry is fine; *"that is not a bunny"* is semantics — kindergarten's crayon-cup
  rule). New, cheap tell: **read the `desc` column of the printed asset list every build — a blank one
  means the pick has no metadata and is almost certainly junk.** Caught by eye in the render; fixed by
  pinning a real pastel plush.
- **[nursery v1, bad PROPORTIONS cannot be scaled away — swap the mesh (vs. bad SCALE, which you fix)]**
  The unpinned `"a small round light wood side table"` came back **1.20 × 0.55 m — a COFFEE table** that
  dwarfed the glider. Scaling cannot rescue it: uniform-scaling to a 0.5 m width yields a 0.23 m height
  (a footstool); height-fitting to 0.5 m yields back a 1.09 m width. **A mesh's aspect ratio is an
  identity, not a parameter.** → Swapped for a genuine pedestal table (0.60 × 0.77) and height-fit it.
  Draw the line clearly against the bad-*scale* family (hospital bed 2.1×, garage car, children_room
  bean bag 5×, corridor cabinets): **a wrongly-SIZED asset is fixed with a uniform `modulate_scale`; a
  wrongly-SHAPED one must be replaced.**
- **[nursery v1, a prop can EXIST and still be UNPLACEABLE — the crib mobile, a real DSL gap]** The most
  iconic nursery prop after the crib. Baby mobiles genuinely exist (a whole `CeilingObjectRetriever`
  pool, six candidates at 0.57–0.68) and **not one can be placed**: `place_on_wall_*` needs a FLAT mesh
  (< ~0.25 m deep) and every mobile is **0.36–2.80 m** deep (a dangly 3-D object by nature — shrinking
  it to fit makes it invisible), while `add_lighting` is the **only** ceiling-hang verb and would make
  the mobile **EMIT** (and dangle ~1.5 m into the room — executive_office's chandelier ban). → Dropped
  it; the crib carries the read regardless. Lesson: at the audit gate, verify a prop is **placeable**,
  not merely **present** — check its DEPTH against the wall-hang limit and ask which verb will carry it.
  **Logged as a DSL gap: there is no verb for a non-luminous ceiling-suspended object**
  (`place_on_ceiling(obj, drop=…)` would unlock mobiles, hanging plants, decorative pendants, fans).
- **[pantry v1, you CANNOT densely stock a tall rack with `place_inside` — adding goods makes it EMPTIER]**
  The whole scene was "floor-to-ceiling shelving stocked with jars, cans, boxes". Six builds of racks
  that rendered as empty bookcases, because the intuition (jewelry_shop's "mass the PRODUCT") inverts
  inside a tall fixture. `place_inside` resizes every item to a tile it derives from the anchor + the
  goods list — the scene has no say (`modulate_scale` is a no-op, tv_studio). Measured by calling
  `tools/planar_regions.solve_placement` directly on the 2.4 m rack: **n=3 → 0.15 m items (reads);
  n=8 → 0.06 m; n=18 → specks; n=36 → invisible, EMPTIER than 6.** Cause: `judge_tile_size` shrinks the
  tile until all n items would fit on ONE shelf board, then resizes every item to it — so a rack's total
  product mass is roughly FIXED and the goods list only chooses how finely it is ground up. Two rules:
  (a) **a FEW substantial goods per rack (~6), never a long list** — adding goods to fix an empty shelf
  is the one move that guarantees it stays empty; (b) **one oversized mesh poisons the whole rack** —
  `judge_tile_size` floors the tile at the LARGEST item's footprint, so a 1.07 m box stack forced ~1 m
  tiles → a single lonely prop per board. Bulk (box stacks, cartons, crates) goes on the FLOOR at its own
  size; conversely keeping ONE basket (0.45 m) in the list *holds the tile floor generous* so the jars
  beside it come out chunky. **Where product actually reads: `place_on_top` on a ~0.9 m counter** — same
  solver, short anchor, believable ~0.2 m jars at viewing height, first try. So put the category cue on
  the COUNTER and the bulk on the FLOOR; a tall rack carries STRUCTURE, not identity. Generalises the
  jewelry_shop lesson: "show the product at viewing height" is not just about eye level, it is about
  picking an anchor whose solver will render the product at a size you can see.
- **[pantry v1, don't trust `run_scene` on a busy box]** The MCP `run_scene` tool returned a *Laboratory*
  scene's report + renders for my pantry build (other users' builds were running concurrently and it
  picked the globally-latest run dir). Two builds were nearly mis-diagnosed off someone else's renders.
  → When the machine is loaded, run `workbench.py run` directly and trust the run_dir IT prints. A report
  whose asset list doesn't match your program is not your build.

- **[closet v1, a wall shelf placed INSIDE a wardrobe — the overlap solver's blind spot, and a new
  core lint (Kunal, 2026-07-13)]** The wall-mounted clothes shelf ended **0.45 m inside** the
  wardrobe bay beside it. Every signal was clean — `no rescale / no rotation / no wall overlap`,
  zero lints — and a **USER** caught it in the render. TWO DSL properties combine to hide it:
  (a) **wall furniture is placed at `row_centers[1..3]`, and those row centres are sized by each
  row's FLOOR occupants, not by the wall items** — this room's back row was shallow (a 4 cm mirror,
  a plant), so its centre sat 1.20 m from the middle row's centre while a 1.8 m bay beside a 1.5 m
  shelf needs 1.65 m; the DSL packs them anyway. (b) The shelf **had** to be `ignore_overlap` (it is
  mounted with `bottom=`; without the flag the 2D solver reads it and the cabinet as interpenetrating
  and shoves them apart along the wall) — but `GradSolver.overlap_pairs`, which backs the residual-
  overlap warning, **filters ignore_overlap items out by construction**. So the flag that makes a
  wall mount possible ALSO makes the object invisible to every overlap check for the rest of the
  build. → **Core fix: `IDSDL/lints.py::lint_embedded_wall_objects`** — a full **3D** AABB test over
  exactly the pairs the solver refuses to look at (every ignore_overlap item vs every other room
  child; parent/child pairs skipped so a `place_on_top` prop on its anchor stays silent). 3D and not
  the solver's 2D footprint, because a shelf ABOVE a console is legal and must stay quiet. It is
  advisory (there is no safe auto-fix: sliding a mounted piece would fight `_repin_wall_furniture`),
  and the message names the three real remedies: different wall slot / different `bottom=` / shrink.
  **Scene fix: dropped the third long item off that wall** (the centre is now empty — which the
  interior camera wanted anyway); three long items on one wall is an ARITHMETIC
  (`(wᵢ+wⱼ)/2 ≤ the row-centre pitch`), never a slot count you can assume.
- **[closet v1, "a fix that changes the numbers by exactly zero" is a falsified hypothesis]** My
  first fix for the embedded shelf was `is_static` on the bays, assuming the GradSolver's exploration
  floor had *drifted* them into it (the living_room_cozy fireplace mechanism — a plausible story, and
  the wrong one). The rebuild came back with a **bit-identical penetration, 0.52 x 1.00 x 0.47 m**.
  Identical to two decimals means the solver never touched those objects, which falsifies the drift
  story outright and points at PLACEMENT, not the solve — where reading `place_on_left_wall_*` found
  the row-centre pitch in a minute. **A rebuild that reproduces a defect to the centimetre is not a
  failed fix, it is a measurement: whatever you just disabled was never the cause.**
- **[fast_food v1.1, three USER catches on a build the VLM loop called clean — and the pattern in them]**
  The converged build returned `no rescale` / `no rotation` / `no wall overlap`, and a human found three
  errors in one glance: (1) the POS **monitor faced sideways** instead of toward the wall its counter
  stands against; (2) every **table towered over its own chairs** (mesh ships 0.96 m — bar height — while
  the chairs are 0.68-0.71 m in TOTAL, because `AddAsset(width=…)` is a SINGLE-AXIS pin that never touched
  the height); (3) the **booths floated off the wall** they are supposed to back (a floor SLOT drifts —
  the slot is a third of the ROOM, not of the wall). All three are now rules in
  [[design_principles]]. **The pattern: every one is a SEMANTIC/ergonomic relationship between two objects
  — screen↔operator, tabletop↔seat, seat-back↔wall — and the VLM constraints check none of them.**
  ObjectProportions judges an object against the ROOM, not against the thing it must work with;
  RotationConstraint fires on gross facing, not on which side of a desk the screen belongs. So: **a clean
  VLM loop is evidence about geometry, never about whether the furniture is USABLE.** Before shipping,
  walk the room as a person: sit at each seat (can you reach the table? is it at your chest?), stand at
  each counter (can you see the screen? can the operator?), lean back in each booth (is the wall there?).
  Same standing as the jewelry_shop "the loop verifies geometry, not category legibility" rule, one level
  down — from "does it read as the category" to "does the furniture work".
