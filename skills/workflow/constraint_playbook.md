---
id: workflow:constraint_playbook
kind: reference
role: "Per-asset-category clearance tables — FROZEN 2026-07-14"
---

# Constraint playbook — WHICH constraints for WHICH assets (FROZEN)

> **STATUS: FROZEN — reviewed with Kunal 2026-07-14. The §5 questions were decided and the
> agreed promotions are now live in `default_constraints.py` (operating/exam table 1.2 all,
> pool/billiards 1.3 all, game tables 0.5 all). The rules below are harvested from every
> worked example (40 lessons' "Manual constraints used" sections + every `add_clearance` in
> the corpus + the auto tables), plus the 2026-07-14 category batch builds. §5 now records
> the frozen decisions rather than open questions; reopen only with a new signed-off change.**

Companion to [`constraints.md`](constraints.md), which explains the MECHANISMS (auto gradient
constraints / author verbs / advisory text). This file is the other axis: given an ASSET or a
SITUATION, what do you impose?

## 0. The decision ladder (read this before adding anything)

The corpus's loudest fact: **30 of 40 worked examples ship with ZERO manual constraints.**
The autos (overlap, bounds, door clearance, category clearances, wall-object occlusion,
wall repinning, ceiling auto-height) carry ordinary rooms. Work down this ladder and stop at
the first rung that solves it:

1. **Geometry first.** A guaranteed relationship is COMPOSED, not constrained: the bar's
   service aisle is a rigid `RelativeGroup` gap, the warehouse forklift aisle is the room's
   own thirds, bakery's staff aisle is station composition. If two things must ALWAYS hold a
   spacing, put them in one group with that spacing baked in.
2. **The right group second.** Chairs that must face a table = `AroundGroup`; a monitor that
   must face its operator = `WorkstationGroup`; a mirror over a chair = `MirrorStationGroup`;
   an island positioned by a kitchen's shape = `KitchenIslandGroup`. Groups make the
   relationship structural; constraints only ask the solver nicely.
3. **The auto layer third** — check §1: it may already cover you (a "reception desk" already
   gets 0.9 m front clearance from its description keywords; a door already clears 0.9 m).
4. **A manual verb LAST**, when a *usage* needs space no group expresses and no keyword
   matches — and then use the earned values in §2.

## 1. What you get FREE (the auto layer)

| Auto | What / how much | Source |
|---|---|---|
| Overlap | no 2D interpenetration (`ignore_overlap` opts out) | every group compile |
| Bounds | stay inside the room | RoomGroup |
| Door clearance | ~0.9 m clear at every doorway | per `place_door` |
| Category clearance | keyword-matched on the DESCRIPTION: service/transaction counters **0.9 front**; display cases/vitrines **0.75 front**; operating/exam table **1.2 all**; pool/billiards table **1.3 all**; game tables (foosball, poker, air hockey, table tennis) **0.5 all**; door/drawer storage (wardrobe, cabinet, dresser, bookshelf, sideboard, lockers…) **0.6 front**; appliances (fridge, oven, range, washer…) **0.9 front**; fireplace **0.8 front**; piano **0.9 front** | `IDSDL/default_constraints.py` (first match wins; author `add_clearance` stacks, larger wins) |
| Wall-object occlusion | tall floor furniture slid out of a wall-hung object's span | per `place_on_wall_*` |
| Wall repin | wall-adjacent furniture snapped back flush after the solve | `_repin_wall_furniture` |
| Ceiling | HEIGHT rises to the tallest asset (never clips); late over-growers auto-shrunk | `init_dims` + `_warn_over_height` (2026-07-14) |
| Bathroom sets | vanity mount height/width from type tags; toilet = complete set | `_apply_vanity_metadata` |

## 2. Earned MANUAL rules by asset category (every value shipped in a converged scene)

The verb: `room.add_clearance(obj, distance=D, dir=...)` with `dir` ∈ `front | front_back |
front_sides | all`. Also `room.add_access(a, b)` (keep a NEAR b) and
`room.add_visibility(source, target)` (keep the sightline open) — see §3.

| Asset / situation | Constraint | Why | Shipped in |
|---|---|---|---|
| **Operating / treatment table** | `1.2, all` — ⚙️ NOW AUTO | staff circulate 360° | operating_room |
| **Pool / billiards table** | `1.3, all` — ⚙️ NOW AUTO | full cue draw on every side — this clearance is what SIZES the room; place the hero + clearance first | game_room |
| **Casual game tables** (foosball, poker, air hockey) | `0.5, all` — ⚙️ NOW AUTO | players stand around | game_room |
| **Cardio machines** (treadmill row) | `0.5, front_back` | mount/dismount at both ends | gym_mega |
| **Weight benches** | `0.4, all` | plates + spotter | gym_mega |
| **Strength machines** | `0.55, front_sides` | operator + pass-by | gym_mega |
| **Reception desk** (when the keyword auto isn't enough) | `0.8, front_sides` | queue + walk-around — Kunal's canonical example | gym_mega |
| **Locker banks** | `0.8, front` | open door + a person changing | gym_mega |
| **Dresser / console vignette** | `0.6, front` | drawer pull; matches the storage auto but explicit when the description won't keyword-match (e.g. "styled console") | nursery, kitchen_eatin |
| **Open shelving being browsed** | `0.6, front` | standing/reach space | art_studio |
| **Anything a door must swing PAST** | `add_clearance(nearest_obj, dir="front")` | guaranteed swing space beyond the auto door band | garage (recommended) |

**Anti-rules (documented "None needed" classes)** — do NOT add constraints for: aisles that
are really zones (compose them), chair↔table spacing inside a group (the group owns it),
wall-flush runs (repin owns it), circulation in single-hero rooms (door auto + overlap
suffice). Every constraint you add is another force in the solve — unneeded ones slow
convergence and fight `is_static` heroes.

## 3. The relationship verbs (rarer, higher leverage)

- `add_visibility(sofa, tv)` — keeps the sightline corridor clear (axis-aligned). Use for:
  TV ↔ primary seating, projector ↔ screen, stage ↔ audience front row. (Living_room lesson
  lists it as the natural add if a TV enters; verified in `_door_clearance_test`.)
- `add_access(obj, target, min_dist, max_dist)` — keeps obj WITHIN a band of target: nightstand
  at a bed, printer cart at a desk, side table at an armchair. Prefer a `RelativeGroup` when
  the pairing is rigid; `add_access` when the solver should keep freedom.

## 4. Composition laws that act like constraints (not solver forces — YOUR job)

These never appear in the constraint list but bind harder than anything in it:
- Tall (>1.4 m) pieces never at wall CENTRES (cameras live there) — corners / left / right slots.
- A wall-flush run needs `run ≤ W/2 − 0.3` when its inner end is full-height (kitchen.md).
- Floor mass is NEVER phase-gated past phase 1 (`_VERIFY_NOTES.md` rule).
- The hero + its clearance goes down FIRST; the ring fills around it (game_room).
- `is_static` heroes exert force but don't move — pair every corner-op hero with it.

## 5. FROZEN DECISIONS (reviewed with Kunal, 2026-07-14)

Each of the original open questions was decided. The conservative through-line: promote only
clearances with a clean keyword signature and a context-independent need; for everything else,
the corpus's loudest fact holds — **30 of 40 scenes ship zero manual constraints, so add
nothing the autos already carry.**

1. **Promote to auto — DONE.** Three graduated into `DEFAULT_CLEARANCES`: operating/exam table
   `1.2 all`, pool/billiards `1.3 all`, game tables (foosball/poker/air hockey/table tennis)
   `0.5 all`. Held back: treadmill/bike (`front_back` need is real but keyword-noisy) and
   locker (stays at `0.6 front` via the storage keyword — no evidence 0.8 is wanted everywhere).
   The known cost is accepted: a pool table in a *showroom* now gets 1.3 m it may not want —
   opt out per-scene with `RoomGroup(auto_clearances=False)` or a tighter manual `add_clearance`.
2. **Beds — NO RULE.** The room-size vote handles bed entry space empirically (bedroom
   converged clean on defaults). A `0.6 front_sides` force would fight `is_static` bed heroes
   for no measured benefit.
3. **Chair pull-back — NO RULE.** Chairs stay inside their groups with no reserved pull-back
   space; a scene that genuinely needs it adds a manual clearance. A group-level reservation
   was considered and rejected as over-constraining for tight dining rooms.
4. **Auto visibility — NO.** `add_visibility` stays opt-in. Auto-registering on any TV+sofa
   pair false-positives too often (a TV on a bedroom dresser is not a viewing axis). It remains
   the documented first manual add when a real sightline exists (§3).
5. **Direction vocabulary — KEEP + DOCUMENTED.** `front_sides`/`front_back` are retained and
   now appear in the DSL reference `add_clearance` entry (both are shipping in converged scenes).
6. **Toilets/vanities — NO RULE.** The stress test `ba_powder_compact` (jewel-box tight)
   converged clean on the autos, so no `toilet: front` rule is warranted.
7. **Group-level clearances — NO, stays room-level.** `CategoryClearanceConstraint` fires at
   the room level only. Intra-group spacing is composition's job (ladder rung 1); firing
   clearances inside a group double-counts against its composed gaps and slows the solve.
