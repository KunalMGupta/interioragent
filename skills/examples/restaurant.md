---
id: example:restaurant
kind: example
family: zoned-multi-zone
category: "bistro dining room"
pattern: "Zoned single room — bar wall + banquette wall + a field of 2-top clusters;"
---
> **Digest (from the pattern index):** **Zoned single room** — bar wall + banquette wall + a field of 2-top clusters; opens with a retrieval STRESS TEST; cafe-SET retrieval trap


# Restaurant / bistro dining room — worked example

Status: **built & essentially VLM-clean** (`scenes/work/restaurant.py`, seed=37). Final compile:
`no rescale`, `no room-rescale`, `no wall overlap`; only the noisy `RotationConstraint` remained
(declined). Built asset-first (a retrieval STRESS TEST before any placement) then coarse-to-fine.
Built as `scenes/work/restaurant.py`; `restaurant_v1.py` is that program phase-gated (2026-07-13),
lint-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record) — after UNGATING the olive tree (floor mass; the phase-2 gate shrank the phase-1 shell into dining-cluster overlaps, then re-ran clean).

## Prompt this covers
- "an upscale but warm sit-down restaurant / bistro: several dining tables with chairs, booth/
  banquette seating along a wall, a bar with back-bar shelving + stools, a host stand at the entrance,
  a service station, pendant + chandelier lighting, plants, wall art, wood floors, moody warm palette."

## Plan summary (from the planner)
"Moody Warm Bistro": intimate dining clusters + banquette-first perimeter, candlelit tables with
glassware, plush curved-back chairs, a continuous bar with bentwood stools + back-bar shelving, a
discreet host stand + service station, greenery at the edges, layered amber light (pendants of varying
heights + a key chandelier). Palette: cognac, olive, taupe, charcoal; warm wood floor, brick accent.

## Step 0 — the retrieval STRESS TEST (do this for a new category; the user asked for it here)
Restaurant is furniture-rich, so instead of ingesting we **proved coverage first**. Wrote a throwaway
script (a one-off stress script, not kept): a ~50-item wishlist → `scene.prefetch_assets(list)` (one
concurrent warm-up) → `AddAsset` each → print the chosen `obj.retrieval_model`, its candidate
`similarity`, and the chosen `desc`; summarize by source and flag any `< 0.30`. Result: **47/47
resolved, none < 0.30** → no ingest needed. This is the fast, quantitative version of the asset-first
"catalogue what we have" step (now written up in `../workflow/asset_selection.md`).

Two things the stress test surfaced, both fixed WITHOUT ingest:
- **The one weak key asset (back-bar, 0.495)** — "a back bar shelving unit with liquor bottles" routed
  to generic shelving. **Rephrasing to "a tall back bar cabinet with shelves of liquor bottles" routes
  to `CabinetandShelfRetriever`** and returns a real dark-wood bottle hutch (`hssd/d13be689…`, 0.62).
  A pool-routing fix, not a prompt-polish fix — the [[asset_selection]] "pool gap" lesson.
- **No true "host stand" exists** — best substitute is the presentation podium (`hssd/2fa15bc3…`).

## The layout idea: zoned single room (bar wall + banquette wall + cluster field)
- **BACK wall = the bar**, built exactly like `bar.md`'s **rigid bar station** so the bartender aisle
  is geometric, not a soft clearance: counter (anchor) + a customer-side stool ROW
  (`AroundGroup.place_rectilinear(longer_side1=stools)`, uniform facing — do NOT `face()` them) +
  a tall back-bar hutch composed BEHIND via `RelativeGroup.place_on_back`.
- **LEFT wall = a banquette run** — a `RelativeGroup(booth → table on front → tub chair on front-further,
  faced back at the booth)`, placed on the wall `facing="right"` so the booth backs the wall.
- **CENTER/RIGHT = 2-top dining clusters** — the money shot. A BARE round table + two cognac tub chairs
  `place_circle(2)`, jittered, dressed with `place_on_top([place-setting, candle])`; light some with a
  single warm pendant (`add_lighting(density=0)`).
- Entrance = a host-stand podium by the door; service = a sideboard (POS + plates on top). Brick
  fireplace anchors the right wall (warm focal), greenery in the corners, chandelier over center.

## Program

[`restaurant_v1.py`](restaurant_v1.py) — phase 1 builds the floor anchors (the rigid bar station, the
banquette run, the 2-top cluster field, the host stand, the fireplace, the door), phase 2 the surface
dressing (place settings + candles on each 2-top, the POS + plates on the service sideboard, the corner
olive tree), phase 3 the wall decor (fireplace poster, landscape), the window and all the lighting.

`workbench run skills/examples/restaurant_v1.py --phase 1` builds the layout alone in ~1–2 min.

## What worked / gotchas
- **Retrieval SET trap (the big one).** A generic "a small round dining table" (or "…bistro table")
  frequently returns a **cafe SET** — a table with folding chairs baked into the mesh. Put your own tub
  chairs around it and every 2-top is DOUBLE-seated (folding chairs + tub chairs = clutter). **Fix: pin
  a BARE table** (`asset_id=`), or add "no chairs" to the query. Same family as the "set assets" idea in
  [[set-assets-and-scaling]], but here the set is the thing to AVOID. Verify tables by eye in the first
  render — a bare top is what you want under a group that supplies its own seating.
- **Dining chair vs. LOUNGE chair — check the footprint, not just the render.** A "tub/armchair" query
  drifts to *lounge* meshes: the first cognac pick (`future/2548400f…`) measured **W1.0 × D0.97 m** — a
  living-room chair that reads heavy and wrong at a bistro table (Kunal's call). A real dining chair is
  **~0.5 × 0.53 m**. Pin a slim DINING chair (`future/1805382c…`, a taupe curved-back armchair) and
  measure it (`obj.get_whd()`) to confirm. **Match the reference's tone too** — the plan collage was
  muted *taupe*, so the loud cognac was itself a miss; pin for color AND dining scale, both by eye
  against the plan image.
- **Cap a stool's height to its counter.** This bar counter mesh is only **0.67 m tall** (table height),
  but the stool mesh is **1.25 m** — so stools *tower* over the bar. A stool should sit ~0.25 m below the
  counter top (seat ≈ counter − 0.27). Use a `_fit_height(obj, h)` helper (uniform all-dims scale to a
  target total height) to cap each stool at ~0.7 m. **General rule: seat height tracks the surface it
  serves** — measure both the seat and the counter/table, don't trust the mesh's native scale.
- **Measure a pinned asset without the network.** `scene.AddAsset(q, asset_id="…")` + `obj.get_whd()`
  loads the mesh and returns W/H/D *without* triggering the embedding call (which needs API creds) — so
  you can size-check picks from a plain script even when NL retrieval would hang. Used to catch both the
  oversized chair and the towering stool above.
- **Rigid bar station = geometric bartender aisle.** Reused `bar.md` verbatim: compose the back-bar
  BEHIND the counter+stool line in one `RelativeGroup`, don't ask a clearance constraint to open the gap.
- **`place_on_top([...])` dresses a table in one call.** A place-setting mesh (plate+glass+cutlery) plus
  a candle, seated by the VLM tournament — legible and non-floating on a 0.8 m top.
- **`place_on_wall_<wall>_<pos>` = hung art; `place_on_<wall>_wall_<pos>` = floor furniture.** The brick
  fireplace is floor furniture on the right wall; the Casablanca poster hangs ABOVE it — two different
  method families, easy to swap by mistake. Keep the busy back wall (the bar) art-free.

## VLM feedback we hit and how we resolved it
- **`rescale room by 0.8`** (first pass, `modulate_scale=0.9`): the field read sparse. Set 0.8; the
  re-render converged clean (no rescale). Same "act on room size once the fill is settled" rule as bar.
- **`rescale armchair by 0.5`**: real signal that the lounge chairs were too big; took it as "shrink a
  bit," `modulate_scale=0.82` (0.5 would be doll-sized). VLM magnitudes are directional, not literal.
- **Persistent `rotate <chair/booth> to face the table`**: declined as noise even after `place_circle`
  + explicit `g.face(c, toward=t)`. The render shows correct facing pairs; the `RotationConstraint` is a
  weak smoke alarm (same as bar/dining/salon). Don't chase it into a rotation hack.

## Asset gaps (LOW risk — this dataset covers restaurants well)
No ingest. Only genuine gap: **no true host stand** (podium substitute). Minor off-theme picks skipped
rather than shipped: a branded ice-cream "dessert case", whimsical pottery "salt & pepper", a magazine-
filled "bread basket". Everything structural (bar, back-bar, booth, tub chair, tables, fireplace,
chandelier, plants, place settings, poster) is a clean dataset hit.

## Manual constraints used
- None. The door auto-clearance keeps the entrance clear; the bartender aisle is geometric (rigid
  station), not a `ClearanceConstraint`.
