# Restaurant / bistro dining room — worked example

Status: **built & essentially VLM-clean** (`scenes/work/restaurant.py`, seed=37). Final compile:
`no rescale`, `no room-rescale`, `no wall overlap`; only the noisy `RotationConstraint` remained
(declined). Built asset-first (a retrieval STRESS TEST before any placement) then coarse-to-fine.

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
script (`scratchpad/stress_restaurant.py`): a ~50-item wishlist → `scene.prefetch_assets(list)` (one
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

## Working skeleton (coarse-to-fine)
```python
scene = SceneProgRoom("Restaurant", seed=37)
BAR_COUNTER="hssd/b1c9d732…"; BACKBAR="hssd/d13be689…"; BARSTOOL="hssd/d10ff3f7…"
BOOTH="future/56f963cd…"; TUBCHAIR="future/2548400f…"          # cognac leather tub chair
ROUND_TABLE="future/aaea6776…"; HOST_STAND="hssd/2fa15bc3…"    # BARE pedestal table; podium
scene.prefetch_assets([ ...all descriptions... ])

# BAR: counter + customer-side stool row + back-bar hutch behind = one rigid station (geometric aisle)
counter = scene.AddAsset("a long wooden restaurant bar counter with a paneled front", asset_id=BAR_COUNTER, width=3.2)
with scene.AroundGroup(sparsity=0.15, jitter=0.2) as bar_group:
    bar_group.set_anchor(counter)
    bar_group.place_rectilinear(longer_side1=4*scene.AddAsset("a wooden bar stool with a backrest", asset_id=BARSTOOL))
    bar_group.add_lighting("a warm amber glass globe pendant light", density=0.2)   # SINGULAR query
backbar = scene.AddAsset("a tall dark wood back bar cabinet with shelves of liquor bottles", asset_id=BACKBAR, width=2.6)
with scene.RelativeGroup() as bar_station:
    bar_station.set_anchor(bar_group); bar_station.place_on_back(backbar)

def two_top(lit=False):                                   # intimate 2-top dining cluster
    with scene.AroundGroup(sparsity=0.2, jitter=0.4) as g:
        t = scene.AddAsset("a small round wooden bistro dining table", asset_id=ROUND_TABLE, width=0.8)  # BARE
        g.set_anchor(t)
        chairs = 2 * scene.AddAsset("a modern leather tub dining armchair", asset_id=TUBCHAIR, modulate_scale=0.82)
        g.place_circle(chairs)
        for c in chairs: g.face(c, toward=t)              # settle the facing (still noisy; render is arbiter)
        g.place_on_top([scene.AddAsset("an elegant table place setting with a plate, wine glass and cutlery"),
                        scene.AddAsset("a lit candle in a small glass votive holder")])
        if lit: g.add_lighting("a warm amber glass globe pendant light", density=0)
    return g

def banquette():                                          # high-back booth + table + facing chair
    with scene.RelativeGroup() as g:
        booth = scene.AddAsset("a high-back upholstered restaurant booth bench", asset_id=BOOTH, width=1.4)
        g.set_anchor(booth); g.place_on_front(scene.AddAsset("a small square bistro dining table", width=0.7))
        chair = scene.AddAsset("a modern leather tub dining armchair", asset_id=TUBCHAIR, modulate_scale=0.82)
        g.place_on_front_further(chair); g.face(chair, toward=booth)
    return g

with scene.RoomGroup(modulate_scale=0.8, randomness=0.2, max_height=3.4) as room:
    room.place_walls(floor_texture="warm walnut herringbone wood floor",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="warm taupe plaster with a rustic exposed brick accent")
    room.place_on_back(bar_station, facing="front")
    room.place_on_back_left_corner(scene.AddAsset("a tall potted indoor olive tree", width=0.9), facing="front")
    room.place_on_back_right_corner(service, facing="front")             # sideboard w/ POS + plates
    room.place_on_left(banq_1, facing="right"); room.place_on_front_left(banq_2, facing="right")
    room.place_on_center(table_c, facing="front"); room.place_on_right(table_r, facing="front")
    room.place_on_front_right(table_fr, facing="front")
    room.place_on_front(scene.AddAsset("a wooden host stand podium", asset_id=HOST_STAND), facing="back")
    room.place_on_right_wall_center(scene.AddAsset("a classic brick fireplace", width=1.6))
    room.place_on_wall_right_center(scene.AddAsset("a large framed vintage Casablanca movie poster"))  # above the fireplace
    room.place_on_wall_front_center(scene.AddAsset("a framed landscape painting"))
    room.place_window_standard("left_wall", position="center", curtain="olive green drapes")
    room.place_door("front_wall", position="right")
    room.add_lighting("an elegant warm dining chandelier", density=0)    # key central fixture
```

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
