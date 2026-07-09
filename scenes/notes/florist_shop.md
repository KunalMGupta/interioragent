# Florist Shop

- **Pattern:** Retail single room, zoned — counter hub (back) + perimeter display walls + storefront
  window; centre hero display table. Blooms MASSED on tiered stands / plinths / table.
- **Jitter/randomness:** RoomGroup randomness=0.1 (kept low; dense retail, hold shape).
- **Planner target:** "Sun-Kissed Florist" — warm wood + cream + brass; blush/green blooms; storefront
  window-first, curved wrapping counter, buckets of blooms, brass track/pendant light, jute rug.

## Retrieval stress test (2026-07-06) — verdict: MOST ASSETS AVAILABLE
Ran real agentic retrieval over 36 flower-shop queries + eyeballed the risky ones. Conclusion:
- **RICH:** vase-bouquet arrangements & wrapped bundles (tulips/ranunculus/peonies/roses/hydrangeas/
  calla lilies) — 20+ good hits at 0.47–0.56 sim. This is the dataset's strength; **mass them** to
  read as a florist's stock. Also solid: glass display cabinet (0.73), tiered/pedestal PLANT stands
  (0.71), potted plants/trees/ferns (0.70–0.78), vases, wooden shelves, shop/bar COUNTERS (0.51),
  POS/cash register (0.57), track light (0.76), brass pendant (0.74), round jute rug (0.72), rustic
  stool (0.79), round mirror (0.75), chalkboard, sunburst wall art (0.62).
- **GAP (the one true miss):** a **galvanized bucket brimming with loose cut stems** — the storefront
  signature. Zinc containers exist (composter/bin/wooden bucket) but no florist bucket; queries
  resolve to arrangements-in-pots. **No place_inside fix** (blooms are vase-arrangements, not loose
  stems). Built around it by massing vase-bouquets instead. Ingest a bucket-of-blooms glb to elevate.
- **Weak:** ribbon-spool rack (→ abstract sculptures, absent), kraft-paper roll (→ a paper bin),
  florist scissors / watering can (wrong type). Minor wrapping-counter dressing; skipped for v1.
- **Serendipity:** "a wooden shop checkout counter" surfaces charming **striped-awning market stalls
  WITH buckets** (children's "market" toy meshes, e.g. `04e08479…`, `e4524262…`) — closest thing to a
  florist bucket display, but toy-scaled; kept as a fallback, led with the clean premium read instead.

## Asset-gap risk: was flagged HIGH — resolved to LOW/MEDIUM
Old note said "HIGH — flower displays." Reality: the dataset covers a florist well via arrangements;
only the loose-stem bucket look is missing. Build now, dataset-only (user call 2026-07-06).

## Build outcome (v2, VLM-clean) — scenes/work/flower_shop.py
Layout: counter hub (back) flanked by olive+fern trees, sun art above; glass cabinet (blooms inside
+ on top) + bloom table + tall plant (left wall); bloom table + entry door + round mirror (right
wall); floor-to-ceiling storefront window (front) with a bloom table in the display bay; hero bloom
table (centre). ~15 bouquets massed on 4 matching rustic display tables = the florist read.
- **v1 lesson — the black wire "tiered plant stand" (`9ae7a2c2…`) is a trap:** it renders as a giant
  glossy-black étagère, scaled huge; place_on_top fit its bouquets to that width → giant tulips, and
  it so filled the right-wall camera that `wall_right.png` came out pure black. Fix: dropped it; used
  low matching **rustic display tables** (`f72c0e86…`) massed with bouquets — controlled scale, dense,
  and reads as a florist. Reuse a `bloom_table(n)` helper (RelativeGroup + place_on_top([bouquet]*n)).
- **v1 lesson — a small round plinth dwarfs its blooms.** `cbc857cb…` renders as a low floor disc;
  bouquets fit to it are tiny. Prefer a table-height surface for a bloom display.
- **v1 lesson — the "wooden wall shelf" (`770eae5e…`) ships with BOOKS baked in** — wrong for a
  florist. Dropped it. (If you need wall storage, pick a bare shelf or a shelf that carries vases.)
- **Storefront:** `place_window_floor_to_ceiling("front_wall")` reads as a real shopfront (exterior is
  unlit → renders black, that's expected). It occupies all 3 wall slots, so the **door must go on a
  side wall** (`place_door("right_wall","left")`). A bloom table in front via `place_on_front_left`.
- **`wall_right.png` all-black is a camera artifact, not a defect** when a wall carries the storefront
  window or the door — the interior cam shoots straight through the glass/opening to black exterior.
  Verify that wall from a corner_* view instead (corner_3 showed door+mirror+bloom table fine).
- Cabinet blooms via `place_inside` (VLM tournament) look good; on-top blooms via place_on_top.
- Downlights via `add_lighting("a recessed ceiling downlight", density=0.12)` (flush-fixture rule).
