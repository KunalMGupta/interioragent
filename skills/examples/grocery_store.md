---
id: example:grocery_store
kind: example
family: retail-spine-loop
category: "grocery store / supermarket"
pattern: "Produce-first shop — and the two STRUCTURAL rules every scene needs."
---
> **Digest (from the pattern index):** **Produce-first shop — and the two STRUCTURAL rules every scene needs.** Identity is free (the `ShopFixtureRetriever` gondola/snack/beverage racks ship STOCKED — toy_shop at full strength), so the work is elsewhere. (1) **A ~1.9–2.0 m run at a wall CENTRE blinds that wall's camera** — the interior cameras stand at each wall centre at ~1.4 m, so v1's `left/right_wall_center` gondolas+coolers rendered both side views pure BLACK *under a totally clean feedback string*. Design the wall centres EMPTY (office_modern): gondolas moved to `back_wall_left/right` **flanking a 0.93 m counter the camera sees OVER** (and that's the money shot from the door), and the **DOOR takes the empty left-wall centre** — an opening claims no floor and blinds no camera. (2) **The shell is the SUM of 5 column maxima** (`compute_grid_dims`), so one wide group in one slot inflates the WHOLE room: a 3-wide produce row at `front` added its entire 4 m to the width (10.4 × 6.6 m) and made the shrink vote GROW to 0.5 as I chased it — re-slotting the tables into the columns the gondolas already paid for cost **nothing**. Also: every produce FIXTURE is empty → mass the product; the residual shrink vote is refuted with **arithmetic** (a rigid 2.02 m run in a 2.18 m column); re-check `add_lighting` density AFTER a `modulate_scale`


# Grocery store / supermarket — worked example ("Produce-First Warm-Industrial Grocery")

Status: **built & VLM-clean** (`skills/examples/grocery_store_v1.py`, seed=23, built through the guided
9-gate flow `flow_0713_025612_66b3`: 4 phase-1 layout builds + 1 phase-2 + 3 full). Final compile:
**`no rotation` / `no wall overlap` / no `[Lint]`/WARNING lines**, at `modulate_scale=0.9`
(**7.35 × 6.80 m = 50 m²**), with a residual `rescale room by 0.8` **declined by arithmetic** (below).

This is the shop example that is really about **two structural rules the whole catalogue needs**:
where a tall wall run may stand (the camera), and how the RoomGroup shell actually computes its size
(the 5×5 column SUM). Read alongside `toy_shop.md` / `bookstore.md` (pre-stocked fixtures),
`jewelry_shop.md` (show the product), and `office_modern.md` (empty wall centres).

## Prompt(s) this covers
- "a grocery store" / supermarket / corner shop / green grocer / mini-market / bodega.
  Scale the gondola blocks + chiller run for a bigger supermarket.

## Plan summary (from the planner)
**"Produce-First Warm-Industrial Grocery"**: a Produce Wall of timber crates bursting with fruit as
the entry magnet; a broad central axis front→back; a light-wood/black-metal merchandising table as a
demo hub; perimeter refrigerated bays; left-side open shelving; branding behind the service counter.
Palette: polished concrete, warm timber, black metal, glass, turquoise accents.

## Retrieval stress test FIRST — and the two gaps it found
38 queries, embedding-only (`svc.browse`) → **0 hard gaps** (every top-1 ≥ 0.40). But similarity is
availability, not quality — the two findings that shaped the build came from *reading the meshes*:
- **The fixtures come PRE-STOCKED** (`ShopFixtureRetriever`, which explicitly spans GROCERY): a real
  stocked supermarket gondola, a wire rack loaded with snack bags, a stocked beverage rack, a branded
  tinned-food promo rack. This is toy_shop's lesson at full strength — **the shelves ARE the product**,
  and the room reads "grocery" with zero crowning.
- **Every produce FIXTURE is EMPTY** (the 3-tier veg rack's baskets are bare) — the jewelry_shop
  empty-fixture trap. So produce is **MASSED as product** (5 crates per table) on low market tables.

## Pinned assets (all previews eyeballed; all dims measured offline with `get_whd()`)
| Role | id | note |
|---|---|---|
| **Gondola ×4** | `custom/d79cf88b…` | THE identity asset: a genuinely STOCKED supermarket shelf. Native **1.00 × 1.93 × 0.38** = real fixture size, **no scaling needed** |
| Cooler ×4 | `hssd/cae4c608…` | the bakery's slim glass-door display fridge (0.60 × 2.01 × 0.65). Repeat it → a chiller run |
| Beverage rack | `custom/0dbd08c1…` | multi-tier, stocked with bottles, blue base (2.00 × 1.39 × 0.34) |
| Snack rack | `custom/781de2d1…` | chrome wire, stocked with snack bags (1.00 × 1.25 × 0.47) |
| Promo endcap | `custom/e6b832f2…` | Borges-branded tinned-food rack (0.65 × 1.28) |
| Market table ×4 | `hssd/e7b54862…` | retail_store's wood-top + black-frame table — the plan's exact material. SQUAT (1.20 × 0.47) |
| Service counter | `hssd/67b505c2…` | the bakery/laundromat white base + wood top — a TRUE 0.93 m counter |
| POS / neon | `hssd/9dbca041…` / `custom/d5884fb5…` | POS on the counter; the neon reads "OPEN" above it |
| Produce | `hssd/51cc5969…` (fruit crate), `hssd/2f3e604c…` (apple crate), `hssd/f1baec5e…` (grapes), `hssd/205483105e…` (pears), `hssd/c097e81e…` (leafy greens) | the massed product |

## THE asset trap: the custom shop-fixture scans load as MINIATURES — and `get_whd()` cannot see it
Every `custom/` scan in the `ShopFixtureRetriever` pool is authored in **real metres**, but its
retrieval `scale` is a **VLM's guess at its width**, and that guess is applied on load. Raw glb extents
vs. what actually loaded:

| fixture | authored (raw glb) | loaded | |
|---|---|---|---|
| gondola | 0.93 × 1.80 | 1.00 × 1.93 | ok |
| snack rack | 1.44 × **1.80** | 1.00 × 1.25 | **31 % SMALL** |
| promo endcap | 1.00 × **1.96** | 0.65 × 1.28 | **35 % SMALL** |
| beverage rack | 2.34 × 1.63 | 2.00 × 1.39 | 15 % small |

**`get_whd()` reports the already-SCALED size, so it reports the miniature as fact.** The only way to
see it is the raw mesh: `trimesh.load(path, force="mesh", process=False).extents`. Fix = pin each back
to its authored width with a uniform `obj.scale(true_width)`.

This is the real story behind this scene's never-quiet shrink vote: **the room kept reading "empty"
because the FURNITURE was toy-sized, not because the box was too big** — and every reflex (obey the
vote, shrink the shell) hides the bug and locks it in. Identical to `clothing_store`'s 5.27 m
merchandising wall that loaded at 0.6 m. **For any `custom/` shop fixture: check the raw extents.**

**AVOID (all caught at audit, before the first build):**
- `future/83abfae5…` Häagen-Dazs shop freezer — **loads at 0.15 m**; its scale metadata lies.
- `hssd/7379d887…` the reused "checkout counter" — only **0.60 m** tall (a low reception desk). Use the
  0.93 m service counter for a shop that needs a real counter height.
- `hssd/2c751d20…` "kids' wooden fruit set in a crate" — **the VLM's #1 produce pick**, and it renders
  as a near-empty **white blob**. caption ≠ mesh.
- `custom/eb9d3e7b…` wooden crate — native **depth 1.96 m** (a spread mesh).
- **No supermarket shopping cart exists** (best hit: a pink personal granny-trolley) → skipped, rather
  than ship an off-theme prop (warehouse's signage rule).

## THE layout lesson: a ~1.9–2.0 m wall run at a wall CENTRE blinds that wall's camera
v1 did the obvious thing — the gondolas at `left_wall_center`, the coolers at `right_wall_center` —
and **both side views rendered pure BLACK.** The interior wall cameras stand at each wall's centre at
~1.4 m, so a fixture taller than that, placed at that centre, contains the camera. (bakery found this
at 1.6–1.75 m; here it is total.) The back view was fine only because its occupant is a **0.93 m**
counter — the camera sees over it.

**The fix is compositional, not a hack — design the wall CENTRES empty** (office_modern's rule):

| wall | left slot | **centre** | right slot |
|---|---|---|---|
| back | gondolas ×2 | **service counter (0.93 m — camera sees OVER it)** | gondolas ×2 |
| left | coolers ×2 | **the DOOR** — an opening claims no floor and blinds no camera | coolers ×2 |
| right | beverage rack | **empty** | snack rack |
| front | — | full-height glazed storefront | — |

Putting the gondolas on the BACK wall was the upgrade, not the compromise: flanking the counter, they
are **the money shot from the entrance**, and they cost width the room was already paying for.

> Cross-check: `bookstore.md` hangs 2.1 m bookcase runs at `left/right_wall_center` and reports clean.
> Given this build, suspect its side views were degraded and nobody opened them. **Open all four views
> every build** (kitchen_set's rule) — a clean feedback string is not evidence that a render exists.

## THE sizing lesson: the shell is the SUM of 5 column maxima — a wide group in ONE slot inflates it all
`RoomGroup.compute_grid_dims` walks a **5×5** grid: `WIDTH = Σ (max width in each of 5 columns)`,
`DEPTH = Σ (max depth in each of 5 rows)`, +`CIRCULATION_GAP` (0.35). `compute_dims_of_point` swaps
w↔d by `facing`, so a wall run contributes its DEPTH to the width and its WIDTH to the depth.

Consequences, both hit here:
- I built the plan's "Produce Wall" as a 3-wide `GridGroup` row and dropped it at `front` — the CENTRE
  column. That column's max jumped to ~4 m and **added 4 m to the room outright**: 10.4 × 6.6 m, with a
  shrink vote that GREW (0.82 → 0.72 → 0.65 → **0.5**) the harder I chased it. This is coffee_shop's
  slot economy stated exactly: *a wide multi-cluster group in a single slot forces a cavernous shell.*
- The fix is free real estate: the three produce tables (1.25 m) went to `front_left` / `front` /
  `front_right` — the **same columns the 2.0 m back-wall gondolas already set** — so they cost the shell
  **nothing** and the room landed at 7.9 × 6.8.

**Rule: before reaching for `modulate_scale`, place the piece in a column something wide already
occupies — there it is free. The occupancy vote tells you THAT the room is wrong, never WHICH slot did it.**

## Skeleton program
```python
scene = SceneProgRoom("GroceryStore", seed=23)

def run(units, sparsity=0.02):                       # a butted wall run (deterministic)
    with scene.GridGroup(sparsity=sparsity, randomness=0.0) as g:
        g.place_row(units)
    return g

def market_table(h, w, d):                           # the table mesh is SQUAT (1.20 x 0.47, w:h=2.5)
    o = scene.AddAsset("a wooden display table with a black metal frame", asset_id=TABLE)
    o.scale(o.get_width() * h / o.get_height())      # uniform to target HEIGHT ...
    o.scale_only_width(w); o.scale_only_depth(d)     # ... then take w/d back (bakery squat recipe)
    return o                                         # a height-fit alone blows it to 1.79 m wide

aisle_a, aisle_b = (run(2 * scene.AddAsset("a supermarket gondola shelf stocked with grocery products",
                                           asset_id=GONDOLA)) for _ in range(2))
chill_a, chill_b = (run(2 * scene.AddAsset("a glass door refrigerated display case",
                                           asset_id=COOLER)) for _ in range(2))

with scene.RelativeGroup() as produce:               # MASS the product — 5 crates, not 3 props
    produce.set_anchor(market_table(h=0.70, w=1.25, d=0.70))
    if PHASE >= 2:
        produce.place_on_top([fruit_crate, apple_crate, fruit_crate2, grapes, pears])
produce_l, produce_c, produce_r = 3 * produce        # build ONCE, duplicate (design_principles)

with scene.RoomGroup(modulate_scale=0.9, randomness=0.08) as room:
    room.place_walls(floor_texture="polished grey concrete floor",
                     ceiling_texture="white drop ceiling",
                     wall_texture="warm light grey plaster wall")
    room.place_on_back_wall_left(aisle_a)            # gondolas FLANK the counter: the money shot,
    room.place_on_back_wall_center(service)          # and the 0.93 m counter keeps the camera alive
    room.place_on_back_wall_right(aisle_b)
    room.place_on_left_wall_left(chill_a)            # cold chain split around the entrance
    room.place_on_left_wall_right(chill_b)
    room.place_on_right_wall_left(beverage_rack)     # right CENTRE deliberately empty (camera)
    room.place_on_right_wall_right(snack_rack)
    room.place_on_center(hub)
    room.place_on_front_left(produce_l)              # FREE: the columns the gondolas already pay for
    room.place_on_front(produce_c)
    room.place_on_front_right(produce_r)
    if PHASE >= 3:
        room.place_on_wall_back_center(neon)                        # branding over the LOW counter
        room.place_window_floor_to_ceiling("front_wall", curtain=None)   # glaze freely (greenhouse)
        room.place_door("left_wall", position="center")             # the entrance IS the camera gap
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.012)
```

## VLM feedback we hit and how we resolved it
- **Both side views BLACK (phase 1)** with a perfectly clean `no rotation / no wall overlap` string →
  the wall-centre camera rule above. **The feedback never mentioned it.** Only opening the PNGs did.
- **A shrink vote that GREW while I shrank the room** (`0.82 → 0.72 → 0.65 → 0.5`) → it was never a
  "too big" signal, it was *sparse + mis-slotted*. Root-caused to the 5×5 column sum (above), not to
  `modulate_scale`. Once the produce moved into paid-for columns and the floor was filled (kindergarten:
  **fill, THEN shrink**), ONE decisive `modulate_scale=0.9` took 54 → 43 m².
- **Residual `rescale room by 0.8` at 43 m² → DECLINED permanently, by arithmetic** (kitchen_set's rule):
  the gondola run is a rigid **2.02 m** `GridGroup` in a **2.18 m** column, so any scale below ~0.93
  shrinks the slot under the run and overflows it into the counter — an overlap the solver cannot undo
  (locker_room). We are already at that floor. And the "empty" floor the metric is scoring is the central
  **shopper aisle** — the plan's own "broad central axis / wide walkways". Same false positive as
  garage / corridor / kitchen.
- **`[Lint]` 15 ceiling fixtures on 43 m² = STARFIELD** (budget ~13) at `density=0.02` → **0.012**.
  Note the count scales with the *shrunken* floor: **re-check lighting density after a `modulate_scale`.**
- **CUDA OOM during a phase-2 `place_on_top`** (another build shared the GPU) → the smart-placement
  tournament silently fell back to the AABB path, which caps an item at 0.4× the anchor height, so the
  produce came out small and sparse. Massing MORE items per table (3 → 5) is the robust answer either way.

## What worked / gotchas
- **The glazed storefront renders as DAYLIGHT, not a black void** — retail_store's "never full-height-
  glaze a shop front" rule is **obsolete** (greenhouse fixed the transparent-film bug). Glaze freely.
- **A door is the perfect occupant for a wall centre you must keep camera-clear**: it claims no floor,
  blinds no camera, and its auto-clearance keeps the entry lane open — which doubles as the plan's
  central axis.
- The turquoise accent the plan asked for has **no texture in the library** → dropped rather than
  smuggled into a wall string (classroom's rule); the beverage rack's blue base carries it instead.

## Manual constraints used
- None. Auto overlap/bounds + door clearance + `CategoryClearanceConstraint` (the counter's 0.9 m
  customer aisle, matched off its description) sufficed.
