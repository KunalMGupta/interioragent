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
