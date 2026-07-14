# Retrofit verification round — RESULTS (2026-07-13)

All 52 worked examples ship a phase-gated `<name>_v1.py`. This file was the round's checklist;
it is now the round's RECORD. Every scene below was built with
`workbench run skills/examples/<name>_v1.py --phase 1` on 2026-07-13 (post-restart), reading
only the layout signals per the partial-build rule (a shell `rescale room by X` vote on a
phase-1 build is voting on a room that does not exist yet — full entry:
`../workflow/vlm_feedback.md`, bedroom).

## The round's one new transferable rule
**A FLOOR-standing object gated to phase ≥2 shrinks the phase-1 shell** (the auto-size never
sees its footprint), and in a tight room that pushes phase-1-only content into overlaps the
solver cannot undo. Both failures below were exactly this; both fixed by UNGATING the floor
object (jewelry_shop's plant, restaurant's olive tree). Corner-slot pieces (museum's palms)
are exempt in practice — the shell already reserves their corners. When retrofitting: gate
surfaces and walls, never floor mass.

## Results (22 scenes: 20 queue + bedroom & bar pre-verified)
- bedroom, bar — phase-1 PASSED before the round (see git history).
- bathroom, casino, children_room, florist_shop, game_room, garage, hair_salon, library,
  lobby, locker_room, retail_store, toy_shop, warehouse — **PASS**: `no rotation` /
  `no wall overlap`; shell votes ignored per the partial-build rule. Per-scene notes:
  - children_room: the relocated `3 *` basket duplication built fine.
  - game_room: **no rotation votes at phase 1 with the tall back-bar cabinet present** —
    evidence AGAINST the cabinet-blinds-the-back-camera hypothesis; the original storm likely
    belonged to the full-dressing renders. (Window post-void-fix check still wants one full
    build whenever the GPU is idle.)
  - hair_salon: the styling-chair custom still wins its query unpinned — no pool drift.
  - locker_room: the 0.7 shrink vote is the predicted artifact of the phase-3-gated
    FLOOR-standing shower stalls; the phase-3 layout was verified separately by a full build.
  - retail_store: the two `[Lint] FLOATS` lines are the deliberately wall-mounted shelves
    (`bottom=` mount-height arg per the lesson) — known false positive.
  - toy_shop: both rotate votes checked by eye (counter's curved front correctly faces the
    room; the POS fix was always a phase-2 item).
- computer_room, gym, meeting_room — **PASS, fully clean** (`no rescale / no rotation /
  no wall overlap`).
- dental_office — **PASS**: the 6-vote rotate storm is the lesson's documented every-phase
  RotationConstraint noise; render eyeballed correct.
- executive_office — **PASS**: the accent-chair rotate is the same face-the-lounge-table
  noise class as the lesson's sofa vote; render eyeballed correct.
- restaurant — **FAILED then FIXED**: two overlap pairs among the dining clusters. Cause:
  the olive tree (floor, back-left corner) was gated to phase 2. Ungated; re-run FULLY CLEAN
  (`no rescale / no rotation / no wall overlap`, no warnings).
- jewelry_shop — **RESOLVED: phase-1-only artifact, full build CLEAN.** One counter pair
  overlapped 0.70×0.36 m at phase 1; ungating the phase-2 plant (floor mass) reduced it to
  0.70×0.20 m, and the FULL v1 rebuild came back clean (`no rescale / no rotation / no wall
  overlap`, no overlap warnings) — the deliberately tight 0.88 shell is simply tighter still
  when auto-sized without the phase-3 wall layer. Documented in the lesson as a known
  read-past-it warning at phase 1. Bonus find: the rebuild's lint flagged the 0.06 lighting
  density as a 28-disc starfield on 30 m² — v1 now ships 0.02 (lesson updated).

## Cross-scene flags — resolved
- **gym 0.60 m reception desk**: eyeballed in the (fully clean) phase-1 render — reads as a
  deliberate low check-in counter by the door; the program's audit note stands.
- **hair_salon duplicate**: `scenes/work/salon_pretty.py` deleted (identical code to
  `scenes/hair_salon.py`); catalog entry updated.
- **lobby focal art / locker_room phase-3 layout**: full builds run 2026-07-13 — see the
  round log for the verdicts.
- **Lesson/program contradictions** (computer_room's phantom 1.1, retail_store's stale
  0.9/0.08 + the reversed POS-rotate): both lessons corrected — the program is the record.

## Still open
Nothing. The tail was drained the same day with full builds:
- game_room FULL: fully clean; the floor-to-ceiling window renders bright post-void-fix, the
  historic rotation-storm traced to the front camera sitting inside the CENTRED entry door,
  and the 0.44 m dartboard warning is a documented judgment call (all in game_room.md).
- bathroom FULL: window renders as a bright curtained pane (workaround retired); the two
  overlap warnings are the corner palm/ladder on the flat bath mat's AABB edge — benign,
  documented in bathroom.md with the deliberate 0.72 tightness.
- lobby's `curtain=None` rationale half-retired (void fixed; ghost-drapes half stands).
- resto_kitchen: authored, converged and promoted the same day — the LAST dataset category
  is covered (see resto_kitchen.md).
