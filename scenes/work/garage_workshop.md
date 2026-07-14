# Garage — asset retrieval audit

Scene file: `scenes/work/garage_workshop.py` (seed=9). Audited 2026-07-05 by viewing each pick's
preview PNG, not similarity alone. Planner target: `tmp/garage/plan/`.

| query | retriever | chosen pick (desc) | verdict | fix |
|---|---|---|---|---|
| a modern silver SUV car | FutureHSSDAssetRetriever (general) | Blue Range Rover Evoque, sleek (`hssd/5f4a…36d0`) | GOOD (pinned) | pin id + `width=1.85` |
| an industrial wooden-top workbench | FutureHSSDAssetRetriever | Wood-top work table on a simple frame (`hssd/1070…68aa`) | GOOD (pinned) | `modulate_scale=0.8` |
| a wide black steel rolling tool chest | FutureHSSDAssetRetriever | Black tool chest, many drawers + wheels (`hssd/67bc…90ed`) | GOOD (pinned) | — |
| a tall white metal storage cabinet | Cabinet/CaseGoods | Tall white 2-door cabinet (`future/07cce174…`) | GOOD (pinned) | ×2 as a run |
| a heavy-duty open steel garage shelving unit | Cabinet/Shelf | Open 5-shelf steel utility unit (`hssd/9f04…0195`) | GOOD (pinned) | end of storage run |
| a pegboard tool panel full of hand tools | (general) | Blue tool panel loaded with hand tools (`hssd/3ec1…d54b4`) | GOOD (pinned) | mount `wall_right_center`, above bench |
| a round metal shop workshop stool | (general) | Industrial metal barstool | GOOD | in work-zone cluster |
| a round industrial wall clock | ClockRetriever | Vintage round metal-frame clock | GOOD | — |
| a black rubber car tyre | (general) | tyre (cache hit) | GOOD | StackGroup ×3, corner |
| a corrugated metal roll-up garage shutter door | (ingested custom) | grey roller shutter + rusty valance (`custom/77209…49fb`) | GOOD (pinned) | **floor-against-wall**, `width=2.05` |
| a wooden shipping pallet + a cardboard storage box | (general) | pallet + dark plastic bins | OK | PileGroup; "cardboard" skews to dark bins |

Counts: **GOOD 9 / OK 1 / MISSING 0.**

### The roll-up shutter (garage vehicle door) — placement matters
The ingested shutter (`custom/77209…49fb`, `placement="wall"`, ~2.0 W × 2.76 H m, portrait) is the
vehicle door. Two gotchas:
- **Place it FLOOR-against-wall (`place_on_front_wall_center`), NOT hung-on-wall
  (`place_on_wall_front_center`).** The hung method is for ART: it caps wall objects to ~0.2× the
  wall width and floats them at mid-wall height (`_place_on_wall` → `target_width = min(.., WIDTH/3*0.6)`,
  `y = mid-level`), so the shutter came out small and floating like a window. Floor-against-wall
  stands it on the floor at full height — a real garage door.
- **Fit the height to the 3 m ceiling.** At the default width (scale 2.6) the portrait mesh is
  2.6 × 1.38 ≈ 3.6 m tall and punches through the ceiling. Width pins uniform-scale, so pick width
  from the target height: `width = target_H / 1.38`. Final: `width=2.174` → exactly 3.0 m tall, a
  floor-to-ceiling garage door. (Aspect from the glb: `trimesh` bounds = 2.0 × 2.76 × 0.24.)
- **Two doors on two walls.** The shutter is on the front wall; the man-door was moved to the BACK
  wall (`place_door("back_wall","left")`). A pedestrian door + a vehicle door on the same wall reads
  wrong. WallOverlap stays clean because they're on different walls.

### Bench-top tools — a real dataset gap (don't force them)
The v1 build tried `place_on_top([toolbox, vise])` on the bench and both came back wrong:
- **"a red portable metal tool box"** → the picker returns the **black tool chest** again (it prefers a
  drawered-chest shape); no small red carry toolbox exists (other hits are coolers / storage cubes).
- **"a heavy metal bench vise"** → returns whole **workbenches** (e.g. "workbench with a vise and 8
  hooks"); there is **no standalone vise** mesh.
So v2 drops bench-top tools entirely — the **pegboard is the tool display** and the bench stays clean.
Log both (small carry toolbox, standalone bench vise) as ingest candidates if garages recur.

## Asset-gap notes (for a future `garage`/`automotive` pool)
- **Cars are the big gap.** There is **no** car retriever or curated pool — "car" queries route to
  the generic `FutureHSSDAssetRetriever`, whose top hits are ~50% TOY cars (ride-ons, VW toys, a
  rabbit-driver toy). Recall for real cars is thin (best sims ~0.44). **Always pin a specific real
  car id and pass `width=1.85`.** Good real picks from `browse "a car automobile vehicle"`:
  `5f4a14a4…` (blue SUV, used here), `c56b1556…` (white SUV), `5cd043b5…` (grey SUV),
  `ccdac06a…` (silver sedan, desc mentions a "garage setting" — check for baked background).
  If garages become common, a curated `vehicles.json` pool + retriever is the right fix.
- **Bench vices and red portable toolboxes are thin** — the visual picker falls back to a wooden
  block / a black chest. Pin if a scene needs them specifically.
- Everything else (workbench, tool chest, tall cabinets, pegboard, stool, ladder, clock, tyres) had
  a strong on-target pick from the base pool — no ingestion needed for this scene.

## Routing notes
- Pegboard "…full of hand tools" recalls well from the base pool and reads as a tool spine when
  wall-mounted; the loaded (blue) panel beats the sparse white pegboards for visual read.
- Tall white cabinet routed to the cabinet/case-goods pool and returned several good tall 2-door
  units — placing two as a `2 * AddAsset` run gives a matched storage wall.
