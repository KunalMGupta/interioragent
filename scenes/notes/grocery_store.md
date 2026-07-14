# Grocery Store

- **Status:** BUILT & VLM-clean — `scenes/work/grocery_store_v1.py` (seed=23), 7.35 x 6.80 m = 50 m²
  at `modulate_scale=0.9`; final compile `no rotation` / `no wall overlap` / zero [Lint] lines.
  Full worked recipe in `skills/examples/grocery_store.md`. Supersedes the 30-line draft that was
  never built (its `place_grid` aisles + `PileGroup` produce + cart-as-light-anchor were all wrong —
  the draft is kept as a signpost documenting its own bugs).
- **Pattern:** a **produce-first shop**, from the planner's "Produce-First Warm-Industrial Grocery".
  BACK wall = the money shot from the door: two blocks of PRE-STOCKED gondolas flanking a service
  counter (+POS, neon OPEN sign above). LEFT wall = the cold chain (4 glass-door coolers) split
  around the entrance. RIGHT wall = the low stocked racks (beverage + snack). CENTRE = the
  merchandising hub table. FRONT = three produce tables massed with fruit against a glazed storefront.
- **THE identity move — the fixtures ARE the product (toy_shop/bookstore at full strength):** the
  `ShopFixtureRetriever` pool has a genuinely STOCKED supermarket gondola
  (`custom/d79cf88b…`, natively 1.00 x 1.93 x 0.38 = real fixture size, no scaling), a chrome wire rack
  already loaded with snack bags (`custom/781de2d1…`), a stocked beverage rack (`custom/0dbd08c1…`) and
  a Borges-branded tinned-food promo rack (`custom/e6b832f2…`). Zero crowning needed. But every produce
  FIXTURE is EMPTY (the 3-tier veg rack `hssd/1c63318d…` has bare baskets) → **produce is MASSED as
  product** on low market tables (jewelry_shop/bakery rule), 5 crates per table.
- **THE layout lesson — a ~1.9-2.0 m wall run at a wall CENTRE blinds that wall's camera.** v1 put the
  gondolas at `left_wall_center` and the coolers at `right_wall_center`; both side views rendered pure
  BLACK (the ~1.4 m interior cameras stand at each wall's centre — bakery's rule, at full strength).
  Fix = office_modern's, applied at design time: **keep the wall CENTRES empty.** The gondolas moved to
  `back_wall_left/right` flanking the 0.93 m counter (short enough for the back camera to see over), the
  coolers to `left_wall_left/right` — and the **DOOR** took the empty left-wall centre, because an
  opening claims no floor and blinds no camera. NB `bookstore` hangs 2.1 m shelves at its wall centres
  and reports clean — suspect its side views were degraded unnoticed.
- **THE sizing lesson — the shell is the SUM of 5 column maxima, so a wide group in ONE slot inflates
  the WHOLE room.** A 3-wide produce ROW dropped at `front` (the centre column) added its entire 4 m
  width outright → 10.4 x 6.6 m and a shrink vote that GREW to 0.5 as I "fixed" it. Splitting it into
  `front_left`/`front`/`front_right` — the same columns the back-wall gondolas already pay for — cost
  the shell NOTHING and landed 7.9 x 6.8. Read `compute_grid_dims` before fighting `modulate_scale`:
  **place a piece in a column something wide already occupies and it is free.**
- **Room size converged at `modulate_scale=0.9` (43 m²) and the residual 0.8 is declined PERMANENTLY**
  (arithmetic, not taste — kitchen_set): the gondola run is a rigid 2.02 m GridGroup in a 2.18 m
  column, so anything below ~0.93 overflows it into the counter. What the metric scores as "empty" is
  the central shopper aisle = the plan's "broad central axis". Same false positive as garage/corridor.
- **Asset gaps (worked around, no ingest):** NO supermarket **shopping cart** (best hit is a pink
  personal granny-trolley → SKIPPED rather than ship an off-theme prop, warehouse's signage rule); no
  conveyor checkout (the 0.93 m white/wood counter + POS is the cash-wrap, retail_store's rule); every
  "refrigerator" hit is a DOMESTIC kitchen fridge except `hssd/cae4c608…` (the bakery's slim glass-door
  display fridge — repeat it 4x and it IS a chiller run).
- **THE ASSET TRAP — the custom shop-fixture scans load as MINIATURES, and `get_whd()` CANNOT see it.**
  Each `custom/` scan is authored in real metres, but its retrieval `scale` is a **VLM's guess at its
  width**, applied on load — so raw-vs-loaded: snack rack **1.44 x 1.80 -> 1.00 x 1.25 (31% small)**,
  promo endcap **1.00 x 1.96 -> 0.65 x 1.28 (35% small)**, beverage rack **2.34 x 1.63 -> 2.00 x 1.39**;
  only the gondola loaded true. `get_whd()` reports the ALREADY-SCALED size, so it reports the miniature
  as fact — you must read the raw glb (`trimesh.load(p, force="mesh").extents`). **This is what the
  never-quiet shrink vote was actually telling me: the FURNITURE was toy-sized, not the room too big.**
  Fixed by pinning each back to its authored width. Same class as clothing_store's merchandising wall.
- **Mesh traps caught at AUDIT (all offline via `get_whd()`):** the Häagen-Dazs shop freezer
  `future/83abfae5…` loads at **0.15 m** (scale metadata lies); `hssd/7379d887…`, the reused "checkout
  counter", is only **0.60 m** tall; the VLM's #1 produce pick `hssd/2c751d20…` ("kids' wooden fruit set
  in a crate") renders as a near-empty **WHITE BLOB** (caption≠mesh); `custom/eb9d3e7b…` wooden crate has
  a native **depth of 1.96 m**. All four dropped before the first build.
- **Lighting:** `density=0.02` tripped the STARFIELD lint (15 fixtures on 43 m², budget ~13) → **0.012**.
  The fixture count scales with the SHRUNKEN floor, so re-check density after a `modulate_scale`.
- **Textures (verified offline against `wall_textures_embeddings.npz` before building):** "polished grey
  concrete floor" 0.633, "warm light grey plaster wall" 0.627, "white drop ceiling" 0.434 (a real white
  grid tile = the plan's ceiling rhythm). The plan's turquoise accent has no texture — dropped rather
  than smuggled into a wall string (classroom rule); the beverage rack's blue base carries it instead.
