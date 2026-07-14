# Retrofit verification notes (2026-07-13)

All 52 worked examples now ship a phase-gated `<name>_v1.py`. Every one is `lint_program`-clean,
but **only `bedroom_v1.py` and `bar_v1.py` have been BUILT since the gating retrofit** (phase 1,
both verified clean). The remaining 20 retrofits are the queue:
`bathroom casino children_room computer_room dental_office executive_office florist_shop game_room
garage gym hair_salon jewelry_shop library lobby locker_room meeting_room restaurant retail_store
toy_shop warehouse` — run each with `workbench run skills/examples/<name>_v1.py --phase 1`
(~1–4 min each; needs the GPU — CPU Blender is impractically slow).
This file is the checklist for the verification round: the judgement calls the retrofit had to
make, the issues it flagged, and what a build must confirm for each scene.

**Read first — the partial-build rule (minted by bedroom's phase-1 rebuild):** a room-size vote on
a phase-1/2 build is voting on a room that does not exist yet. Bedroom converged VLM-clean at
`modulate_scale=0.8` on the full build, then voted `rescale room by 1.4` at phase 1. During this
round, read only the layout signals at phases 1–2 (`no rotation`, `no wall overlap`, per-object
`no rescale`) and ignore the shell verdict. Full entry: `../workflow/vlm_feedback.md` (bedroom).

For every scene below, the baseline check is the same: the phase-1 floor solve should reproduce
the original build's layout, and the phase-3 build should reproduce the original scene. Items
listed per scene are *in addition* to that.

## Lesson/program contradictions to reconcile (lessons were deliberately NOT edited)
- **computer_room** — the lesson claims "applied a 1.1 room enlarge (VLM asked 1.2 twice)", but the
  program ships `modulate_scale=1.0` and git history never contained 1.1. One of them is wrong;
  decide which and fix that one.
- **retail_store** — the lesson still quotes `modulate_scale=0.9` and `density=0.08`; the source
  program ended at `1.2` / `0.06` after the "more spacious" feedback. The lesson also records the
  POS rotate-180 vote as DECLINED, but the source later applies `room.rotate(pos, 180)`.

## Cross-scene flags (found while retrofitting, unconfirmed)
- **gym** — the reception desk `hssd/7379d887…` is the same mesh grocery_store measured at
  **0.60 m** and rejected as a checkout counter; gym never height-pins it. Run `get_whd()` and
  eyeball the render.
- **lobby** — the back-centre focal art (`width=1.8`) sits directly behind the reception counter:
  candidate for the art-crosses-the-monitor collision waiting_room documents, which produces **no
  VLM signal**. Check the blend.
- **hair_salon** — `scenes/work/salon_pretty.py` is the same program as `scenes/hair_salon.py`
  (only the scene/export names differ). Delete one.
- Possibly-stale post-renderer-fix workarounds (greenhouse fixed the window void 2026-07-12):
  bathroom's black back-wall window note; lobby's `curtain=None` rationale; game_room's
  floor-to-ceiling window.

## Per-scene notes
- **bar** — **phase-1 PASSED (2026-07-13)**: `no rotation`, `no wall overlap`; the phase-2 corner
  palm did not disturb the solve. Shell vote `rescale 1.1` ignored per the partial-build rule
  (full build had converged at 0.95).
- **bathroom** — original "reads a touch tight" observation still open.
- **bedroom** — phase 1 verified; **phases 2–3 not re-run**. Declined the phase-1 `rescale 1.4` vote.
- **casino** — judgement calls: stool row kept in phase 1 (it sets the bar slot's depth); chandelier
  + ambient fill moved to phase 3 (mood layer) though the old docstring said phase 2. Windowless:
  early-phase renders are dark by construction — don't chase it.
- **children_room** — `3 *` basket duplication moved inside the cubby `with` block (mirrors
  bedroom's `2 * ns`); untested at runtime. Rug + ceiling light moved to P2/P3 vs the source
  docstring's phase 1.
- **computer_room** — (see contradiction above.)
- **dental_office** — instrument cart + admin workstation kept in phase 1 (floor mass) though the
  source docstring called them "Phase 2 — details". `prefetch_assets` added (source had none).
- **executive_office** — orange accent chair kept in phase 1 (floor mass) vs the source docstring's
  "phase 2 — secondary".
- **florist_shop** — phase 1 renders six BARE bloom tables (the massed bouquets are the phase-2
  identity layer). Expected; don't chase it.
- **game_room** — no VLM history was ever logged (this example's biggest hole). Two hypotheses to
  test: the tall back-bar cabinet may blind the back-wall camera (would explain the declined
  rotation-vote storm), and the window post-void-fix.
- **garage** — roller shutter left UNGATED (a floor-occupying opening; the car noses at it).
  Lighting moved to phase 3 vs the source docstring's phase 2.
- **gym** — promoted `gym_mega.py` (the reference variant; `gym.py`/`gym_large.py` are smaller
  cuts). Two pins have no audit note (`hssd/f87c00e6…` seated row, `hssd/1fa8df7c…` incline press).
  This is the library's only `place_mirror_full_wall` demonstration. (Desk-height flag above.)
- **hair_salon** — mirror ungated (`MirrorStationGroup._layout()` raises without `place_mirror`).
  Pendants moved 2→3; receptionist chair kept in phase 1 (it sets the reception cluster's depth).
  4 of 5 ingested customs win by query, unpinned — fragile to pool drift.
- **jewelry_shop** — phase-1 storefront pedestals render as BARE plinths (busts are phase-2
  massing). Expected.
- **library** — corner plant gated to phase 2, so the phase-1 nook corner looks unbalanced. Expected.
- **locker_room** — shower stalls at phase 3 per the source docstring, but they are FLOOR-standing:
  the phase-1 shell auto-sizes without them and will differ from the full build. Confirm the
  phase-3 layout matches the original. Mirror ungated (same reason as hair_salon).
- **meeting_room** — water cooler phase 1 (floor anchor) while the plant is phase 2; both shared a
  corner block in the source.
- **restaurant** — olive tree moved to phase 2 → the phase-1 back-left corner has one fewer
  occupant. "a small stack of white restaurant plates" is used but absent from the source's own
  `prefetch_assets` list (preserved as-is).
- **retail_store** — perimeter wall merch treated as phase-1 anchors (it is the perimeter loop,
  i.e. layout), only decor/window/lighting at phase 3. `room.rotate(pos, 180)` is skipped at
  phase 1 (the POS doesn't exist yet). (See contradiction above.)
- **toy_shop** — `display_table()` now takes a thunk so its props are only retrieved at phase 2;
  one structural deviation from the source, same phase-3 scene. `rotate(pos, 180)` skipped at
  phase 1.
- **warehouse** — `PALLET` and `BOXES_GRAY` are pinned in the source but never used by any
  `AddAsset` (preserved; no why-comment possible). Shutter + exit sign at phase 3.
