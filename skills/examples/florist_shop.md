# Florist shop — worked example

A charming **flower shop / florist boutique**, built from the planner target "Sun-Kissed Florist".
The reference for a **retail room whose identity comes from MASSING one abundant prop** (bouquets)
across repeated display surfaces — and for **opening a scene with a retrieval stress test** to decide
what the dataset can and can't give you. Read alongside `../workflow/asset_selection.md`.

## Status
Built as `scenes/florist_shop.py` (seed=48). `florist_shop_v1.py` is that same program, phase-gated
(2026-07-13), lint-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record) (the six bare bloom tables voted a huge shell shrink, as predicted — ignored).

## Prompt(s) this covers
- "a flower shop" / florist / flower market / bloom boutique.

## Open with a retrieval STRESS TEST (this is why the example exists)
The category screamed asset-gap risk ("flower displays"), so before writing a placement I ran the real
agentic retrieval over ~36 flower-shop queries (`scene.prefetch_assets(...)` then `AddAsset` each,
printing chosen id + similarity + best-in-shortlist) and eyeballed the risky ones with `browse`. The
verdict reshaped the whole build:
- **The dataset is RICH in vase-bouquet arrangements & wrapped bundles** (tulips/ranunculus/peonies/
  roses/hydrangeas/calla lilies) — 20+ at 0.47–0.56 sim. Also solid: glass display cabinets, plant
  stands, potted trees/ferns, shop/bar counters, POS, track lights, jute rugs, round mirrors, sun art.
- **One true GAP: a galvanized bucket brimming with loose cut stems** — the classic storefront look.
  Zinc containers exist but no florist bucket; queries resolve to arrangements-in-pots, and there is
  **no `place_inside` fix** (blooms are vase-arrangements, not loose stems).
- **Decision:** build the florist read by **massing vase-bouquets** on repeated display tables instead
  of buckets. (User's call: dataset-only now; ingest a bucket-of-blooms glb later to hit the exact look.)

The lesson: a stress test turns "HIGH asset-gap risk, unknown" into a concrete build plan — *what the
dataset gives cheaply* (mass it) vs *the 1–2 meshes worth ingesting* (name them, move on).

## Plan summary
Warm wood + cream + blush/green: **honey-oak floor, cream plaster walls, rustic display tables,
colorful bouquets everywhere.** A **checkout/wrapping counter** hub on the back wall (POS + a wrapped
bundle) flanked by potted trees under a **sunburst "sun" wall art**; a **glass display cabinet** and a
**tall plant** on the left; **bloom tables + a round mirror + the entry door** on the right; a
**floor-to-ceiling storefront window** on the front with bloom tables in the display bay; a **hero
bloom table** in the centre. Six matching bloom tables (~25 bouquets) carry the identity.

## Assets (all pinned; audited previews)
| Role | id | note |
|---|---|---|
| Blooms (×6 variety) | `hssd/69930e5f…`, `e731fbf0…`, `53317cc2…`, `232e1b60…`, `997ce68f…`, `aac9ddbf…` | vase-bouquets: tulips / ranunculus+roses / peonies / hydrangeas / mixed tulips / pink+purple. Rotate them so each cluster is mixed. |
| Wrapped bundle | `hssd/0f26b905…` | red rose bundle, **no vase** — the "fresh-cut for sale" cue on the counter |
| Checkout counter | `hssd/7499145e…` | traditional wooden counter (flat top; `04e08479…`/`e4524262…` toy market STALLS with buckets are the closest florist-bucket look but toy-scaled) |
| Glass cabinet | `hssd/d3fd1b00…` | warm oak glass display cabinet — fill it (`place_inside` + blooms on top) or it reads bare |
| Display table (×6) | `hssd/f72c0e86…` | rustic console; reused as every bloom table. Reads a touch low/bench-like but masses well |
| Potted trees | `future/82d06f8e…` (leafy), `hssd/9d6f7ffc…` (olive), `future/244c96f3…` (fern) | greenery framing the counter + a left-wall accent |
| POS / sun art / mirror | `hssd/9dbca041…` / `hssd/b93304c7…` / `hssd/5ee88522…` | POS on the counter; sunburst art = the plan's "sun" motif; ornate round mirror |

## THE identity lesson: mass ONE abundant prop, don't hunt for the hero mesh
A flower shop's identity is *lots of flowers*, and the dataset's flowers are **vase-bouquets**, not
loose-stem buckets. So the build is **composition, not a single hero asset**: a reusable `bloom_table`
(a display table + a LIST of bouquets via `place_on_top`, which distributes the list along the top),
duplicated six times around the shop. Density *is* the design — the user's one note on v2 was "add a
few more tables and flowers," and going 4→6 tables / ~16→~25 bouquets is what tipped it from "boutique
with some flowers" to "flower shop." When the dataset is thin on the literal hero (buckets) but thick
on a related prop (bouquets), lean all the way into the prop.

## Program
[`florist_shop_v1.py`](florist_shop_v1.py) — phase 1 the floor anchors (the six bare bloom tables, the
counter, the cabinet, the door), phase 2 the identity layer (the bouquets massed via `place_on_top` /
`place_inside`, plus the potted greenery), phase 3 the storefront window, wall decor and lighting.
`workbench run skills/examples/florist_shop_v1.py --phase 1` builds the layout alone in ~1–2 min.

## Asset traps that wrecked v1 (all in retrieval, not layout)
- **The black-wire "tiered plant stand" (`9ae7a2c2…`) is a trap.** It renders as a GIANT glossy-black
  étagère, scaled huge; `place_on_top` fits its bouquets to that width → giant tulips, and it so fills
  the right-wall camera that `wall_right.png` came out **pure black**. Fix: dropped it; used low
  matching **rustic display tables** — controlled scale, dense, on-brand.
- **A small round plinth (`cbc857cb…`) dwarfs its blooms** (renders as a low floor disc; bouquets fit
  to it are tiny). Prefer a table-height surface for a bloom display.
- **The "wooden wall shelf" (`770eae5e…`) ships with BOOKS baked into the mesh** — wrong for a florist.
  Dropped it. If you need wall storage, pick a bare shelf or one that carries vases.
> General rule these share: an asset's *preview* can hide a scale/material/baked-prop surprise that
> only shows at room scale. When a pinned prop misbehaves, suspect the **mesh**, not the placement.

## Storefront window + door, and the all-black wall render
`place_window_floor_to_ceiling("front_wall")` gives a real shopfront, but it **occupies all three
front-wall slots**, so the **door must go on a SIDE wall** (`place_door("right_wall", "left")`). The
window's unlit exterior renders **black** — expected. Corollary: a `room_views/wall_*.png` that is
**entirely black is a camera artifact, not a defect**, whenever that wall carries the window or the
door — the interior camera shoots straight through the glass/opening to the black exterior. **Verify
that wall from a `corner_*` view instead** (here `corner_3` showed the door + mirror + bloom table fine).

## VLM feedback we hit and how we resolved it
- **v1/v2 "rescale room by 0.82 → 0.69 → 0.5"** — occupancy-driven, and it *fell* as we added tables.
  Held `modulate_scale=1.0` throughout (per the locker-room rule: ignore occupancy rescale on a
  furniture-packed room; the density is the goal). No overlaps resulted.
- **"rotate POS terminal to face the customer"** (v3) — minor; `place_on_top` doesn't orient items.
  Left as-is (barely visible); would need per-item facing if it mattered.
- Everything else stayed **"no rescale" / "no wall overlap" / no over-height** across all three builds.

## What worked / gotchas
- **Reuse ONE composed unit `N` times** (`bloom_table`) — six matching tables read as a cohesive retail
  display; repetition is realistic in a shop, not a flaw.
- **Fill glass furniture.** An empty display cabinet reads bare; `place_inside` a few bouquets + a
  couple on top (its glass also picks up nice reflections of the mirror/sun art).
- **`place_on_front` + `place_on_front_left`** put two tables in the storefront bay without a wall
  slot — floating front placements are fine for compact single items (unlike a long ROW; see the
  locker-room lesson).
- Ceiling: `add_lighting("a recessed ceiling downlight", density=0.12)` — flush fixture, per the rule.

## Manual constraints used
- None required; auto overlap/bounds + wall-flush placements sufficed even at ~30 objects.
