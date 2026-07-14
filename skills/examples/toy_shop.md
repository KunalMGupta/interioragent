# Toy shop — worked example

Status: **built as `scenes/toy_shop.py`** (seed=42). [`toy_shop_v1.py`](toy_shop_v1.py) is that
program **phase-gated** (2026-07-13): same layout, same pinned ids, same seed. It is
**`lint_program`-clean**, and it has **NOT been re-rendered since the retrofit**, so *the phase
splits are unverified*.

A bright children's **toy / comic / book shop**, from the planner target "Bright Primary-Play Toy
Store". The reference for **building a shop's identity out of PRE-STOCKED shop fixtures** (the new
`ShopFixtureRetriever`) instead of crowning generic shelves, and for two DSL lessons the build forced
out: a core `object.scale()` fix and **scale-by-height** for fixtures. Read alongside `florist_shop.md`
(mass-one-prop) and `retail_store.md` (spine + perimeter loop).

## Prompt(s) this covers
- "a toy shop" / toy store / kids' toy & comic / book shop.

## Open with a retrieval STRESS TEST
32-query sweep (`IDSDL.service.core.browse`, embedding-only) → **40/40 solid, 0 gaps**. Strong-coverage
category, no ingest needed. Heroes all landed ≥0.65: teddy 0.73, wooden train 0.73, teepee 0.72,
rocking horse 0.68, dollhouse 0.65, ride-on car 0.66. The test's job here was to *confirm* coverage so
the build could go straight to composition.

## Plan summary
White walls, warm-oak laminate floor, bright primary-colour toys as the accent. Zones: a **perimeter
merchandising ring** (pre-stocked toy / comic / book shelves), a **central play island** (round table
+ train + blocks on a concentric rug, flanked by rocking horse + ride-on car), a **teepee reading
corner** + a **bean-bag seating nook**, and a **near-entrance checkout** by the storefront window.

## THE identity lesson: use PRE-STOCKED shop fixtures, don't fake it by crowning empty shelves
v1–v2 hung the "packed with toys" read on generic shelves crowned with a hero toy each — but the pinned
white gondola's mesh actually reads as a **shoe rack**, and a 3.84 m "tall shelf" got auto-clamped into
thin **empty** verticals. The fix was the new **`ShopFixtureRetriever`** (curated shop pool, pool-bonus):
it surfaces fixtures that come **already stocked with the right merchandise** — cartoon toy shelves with
toys on them, a comic rack packed with covers, book/game shelves. The shelves themselves carry the
identity, so most need no crown at all. When a retriever exists for your domain, browse *its* pool and
prefer inherently-stocked fixtures over compose-your-own.

## Assets (all pinned; previews audited — see the caption≠mesh gotcha)
| Role | id | note |
|---|---|---|
| Toy shelf (×3) | `future/1fc1d19b…` | cartoon kids' shelves **pre-stocked with toys**; the primary perimeter unit (1.2×1.49) |
| Comic rack | `custom/61cd8619…` | long shelf packed with colourful comic covers + red base (2.2×1.3×0.48). **Visually verified.** |
| Book/game shelf (×2) | `future/1ecf937a…` | cartoon shelf of book/game covers (1.2×0.94) |
| Book display | `hssd/f3a8d459…` | angled stand full of colourful children's books |
| Figurine tower | `future/b8812342…` | narrow tiered tower of figurines (accent) |
| Play island | table `hssd/4b9ff34f…` + train `future/751feb3c…` + blocks `hssd/6561f279…` on rug `hssd/6f26eb16…` |
| Heroes | rocking horse `future/439cb8bf…`, ride-on `hssd/c9dd11b6…`, teddy `future/3e18ed6d…`, teepee `hssd/19401d9b…` |
| Seating nook | bean bags `hssd/256102db…` (pink), `hssd/0598a08d…` (blue) + floor cushion `hssd/859e59d9…` |
| Checkout | counter `hssd/7379d887…` + POS `hssd/9dbca041…`; neon `custom/d5884fb5…` |

**AVOID:** `custom/91fa23e0…` — captioned "comic-book display cabinet" but its **mesh is a clothing
rack**. `custom/1313330a…` comic wall is **D=1.9 m** (multi-part spread mesh) — juts into the room.

## Program
[`toy_shop_v1.py`](toy_shop_v1.py) — phase 1 the floor anchors (the perimeter merch ring, the play
island and its flanking heroes, the display tables, the teepee/book-display reading corner, the
bean-bag seating cluster, the checkout, the walls and the door), phase 2 the surface dressing (the
shelf crowns, the island's train + blocks, the display-table props, the POS, the rugs), phase 3 the
neon wall sign, the storefront window and the flush-mount lighting.

`workbench run skills/examples/toy_shop_v1.py --phase 1` builds the layout alone in ~1–2 min.

## DSL lessons this build forced out (durable, beyond this scene)
- **`object.scale(target_width)` was wrong for pre-normalised assets.** It set `target/current_width`
  as the *absolute* scale, so any asset shipping a non-1.0 `transform.scale` (e.g. the rocking horse,
  ~0.30 m native) blew up ~10× (→ 3 m). Fixed to apply the factor *relative* to current scale, matching
  `scale_only_width/height/depth`. Symptom to recognise: one asset dwarfs the room.
- **Scale fixtures by HEIGHT, not width** (`sized_h`). Shop shelves vary wildly in native proportion;
  a width target squashes/blows the height. Height targets give a consistent standing look.
- **`place_on_top` breaks on flat surfaces** (rug/pallet): it tiled the rug into a 0.029 m grid → 7396
  tiles → the bean bags shrank to ~3 cm. For floor seating, place items as FLOOR objects + `place_rug`.
  (Same failure class as the warehouse flat-pallet note.)
- **Caption ≠ mesh — always eyeball a pinned fixture's preview.** `91fa23e0`'s metadata said
  "comic-book display cabinet"; its mesh is a clothing rack. Measuring dims is not enough; render/preview.

## VLM feedback we hit and how we resolved it
- rocking horse dwarfs the room → root-caused the `object.scale()` bug (not a per-scene tweak).
- shelves read empty / as shoes → switched to `ShopFixtureRetriever` pre-stocked fixtures.
- "rescale room by 0.88/0.94" → tightened 1.2 → 0.98 (declined the full shrink; kids need floor space).
- ceiling over-packed with fixtures → `add_lighting` density 0.08 → 0.05.
- Note: both early "renders" were **partial** — the build crashed mid-compile on invalid
  `place_on_*_further` RoomGroup methods (those live on RelativeGroup, not RoomGroup), so everything
  after the crash line silently never placed. Validate method names against the actual class before a
  5-min render.
