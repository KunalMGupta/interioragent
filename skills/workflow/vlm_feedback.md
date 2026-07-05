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
