# Restaurant

- **Status:** BUILT & essentially VLM-clean — `scenes/work/restaurant.py` (seed=37). Full worked
  recipe in `skills/examples/restaurant.md`. (Supersedes the thin pre-workflow `scenes/restaurant.py`.)
- **Plan:** planner headline "Moody Warm Bistro" — intimate 2-top clusters + banquette perimeter +
  a bar zone, warm cognac/olive/charcoal palette, brick accent, layered amber light.
- **Pattern:** zoned single room. BACK wall = a rigid **bar station** (counter + a customer-side stool
  row + a tall back-bar hutch composed BEHIND it, so the bartender aisle is geometric, per the
  [[bar-scene-status]] lesson). LEFT wall = a **banquette run** (high-back booths + café tables +
  facing tub chairs). CENTER/RIGHT = **2-top dining clusters** (bare round table + two cognac tub
  chairs, `AroundGroup.place_circle(2)`, jittered, dressed with a place-setting + candle via
  `place_on_top`; some lit by a single warm pendant). Entrance = host-stand podium by the door;
  service = a sideboard station (POS + plates). Brick fireplace anchors the right wall; olive-drape
  window; chandelier over center.
- **Stress test FIRST (user-requested):** resolved a 47-item wishlist via a `prefetch_assets`+`AddAsset`
  script that prints chosen model id + similarity per query. 47/47 resolved, **none < 0.30** → restaurant
  is a furniture-rich, low-risk category, **no ingest**. Only weak key asset (back-bar) fixed by a query
  rephrase (routes to `CabinetandShelfRetriever`). Full technique now in `workflow/asset_selection.md`.
- **Retrieval traps hit & fixed (reusable):**
  (1) **cafe/dining SET trap** — "a small round dining table" returned a table+chairs SET with baked-in
  folding chairs, which DOUBLE-seated each 2-top on top of my own tub chairs. Fix = pin a **BARE**
  pedestal table (`future/aaea6776…`) or query "…no chairs".
  (2) **palette + scale** — the generic tub-chair query gave clinical WHITE lounge chairs, oversized vs
  the small tables. Fix = pin a **cognac** leather tub armchair (`future/2548400f…`) at
  `modulate_scale=0.82` (dining scale, not lounge).
- **Heroes (pinned):** bar counter `hssd/b1c9d732…` (width=3.2), back-bar hutch `hssd/d13be689…`, bar
  stool `hssd/d10ff3f7…`, booth `future/56f963cd…`, cognac tub chair `future/2548400f…`, bare round
  table `future/aaea6776…`, host-stand podium `hssd/2fa15bc3…` (no true host stand exists; podium is the
  best substitute).
- **Rotation noise:** the VLM keeps flagging "rotate chair/booth to face the table" even after
  `place_circle` + `g.face(c, toward=t)`. Declined as noise — same weak-smoke-alarm lesson as
  bar/dining/salon; the render shows correct facing pairs.
- **Scale/jitter:** RoomGroup modulate_scale 0.8 (VLM asked −0.8 from 0.9; converged clean),
  randomness 0.2, max_height 3.4; AroundGroup jitter 0.4.
- **Kunal revision (2026-07-06):** (1) chairs were bulky LOUNGE tubs (W1.0×D0.97) → swapped to a sleek
  taupe curved-back DINING armchair `future/1805382c…` (W0.5×D0.53), matching the reference tone/shape.
  (2) bar stool mesh is 1.25 m tall vs a 0.67 m counter → `_fit_height()` caps each stool at 0.7 m.
  (3) two clusters had interpenetrated — a real GradSolver bug (snap→clamp could re-create an overlap):
  fixed in `IDSDL/constraints.py` (`GradSolver._settle` alternates snap↔clamp, ends in-bounds) +
  `RoomGroup._warn_overlaps` post-compile check that flags residual overlaps as "room too small". See
  [[roomgroup-overlap-settle]].
