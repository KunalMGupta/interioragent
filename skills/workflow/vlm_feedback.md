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
