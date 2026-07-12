# Coffee shop / café — worked example

Status: **built & VLM-clean** ([coffee_shop_v1.py](coffee_shop_v1.py), seed=7;
agent-authored, 4 builds to converge incl. the vibe layer). Final compile:
`rescale room by 0.97` (declined as noise), one declined POS-rotation flag,
`no wall overlap`, 6 flush lights + counter pendants.

## Prompt this covers
- "a small cozy coffee shop with an espresso counter, a pastry display and a few tables"

## The layout idea: compact service spine + 2-top field + window bench
Slot economy is THE lesson for a "small/cozy" brief: **3 occupied floor slots** + wall
pieces, modest hero widths — the RoomGroup shell then comes out café-sized by construction.
- **BACK = rigid counter station** (bar.md pattern, one slot): counter (2.4 m) anchor,
  light-oak bookshelf back-bar composed BEHIND, the cream **dessert cart** composed at its
  LEFT — one unit, geometric barista aisle. Auto category-clearance gives the counter its
  0.9 m customer aisle.
- **Identity = PRODUCT at viewing height** (jewelry_shop lesson, works for food too):
  espresso machine + POS + 3-tier cake stand + sponge cake + donut trio + takeaway-cup set
  massed ON the counter via one `place_on_top([...])`; a cup + open donut box on every
  cafe table. No pastry-display-case mesh exists in the dataset (best hits are branded
  ice-cream freezers / china cabinets) — massed pastries + the dessert cart carry the
  category instead, and read better than an empty case would.
- **LEFT + CENTER = 2-top clusters** — bare pedestal pub table + two papercord chairs
  (`place_circle`, jitter 0.35, `face()` each chair) + jute rug; built ONCE, `2 * unit`.
- **FRONT WALL = cream upholstered bench** (`place_on_front_wall_center`, 2.0 m) +
  standard window with cafe curtains (left) + door (right). Vintage print on the left wall.

## The VIBE layer (what turns "correct" into "coffee shop")
The geometry above converged clean but read sterile. Four additions carried the atmosphere
(user-driven; now the default checklist for any café/shop):
1. **Stock the service shelves** — `place_inside([tea/coffee/sugar jars, bean jar, branded
   mug, cup])` on the back-bar + a trailing pothos `place_on_top`. A dressed back-bar is
   the service-wall analogue of "product names the shop".
2. **Menu signage** — the vintage espresso chalkboard (`hssd/dc704bb0…`, placement=walls,
   genuinely flat) hung `place_on_wall_back_center` above the counter.
3. **A warm accent seat** — caramel leather armchair + side table + brass floor lamp as ONE
   RelativeGroup nook (`place_on_right(nook, facing="left")`); the saturated accent against
   the neutral palette is what makes the room feel inhabited.
4. **Warmer envelope** — sand-beige walls instead of flat cream. (Texture strings are
   embedding-matched: "medium brown oak floor" still rendered light — acceptable here since
   the plan wanted light oak anyway; force darker floors with plainer color words.)

## Skeleton program
See [coffee_shop_v1.py](coffee_shop_v1.py) — the canonical form (constants block of
eyeball-verified pinned ids → stocked counter station → duplicated 2-top → nook →
RoomGroup shell).

## What worked / gotchas
- **Eyeball EVERY pinned mesh preview first** (caption≠mesh): "window bench" retrieved a
  dark bench+overhead-cabinet wall unit; "back-bar shelving system" retrieved two small
  FLOATING wall shelves. Both caught from previews before any build.
- **Floating mesh trap — `hssd/66b84f2b…` (walnut storage bench) has an off-center mesh
  origin**: wall-placed it hovers ~0.6 m up, and its self-reported AABB disagrees with the
  render geometry, so even an AABB-based floor-snap leaves it ~0.3 m off the floor. A
  dataset-mesh analogue of the ingest recentering lesson. **Don't fight it — swap the
  mesh** (`hssd/a5faa788…`, cream tufted bench, rests perfectly).
- **`add_lighting` density on a café-sized room: 0.05 is still a STARFIELD (~24-26
  fixtures); 0.01 gave a calm 6.** The count is `1+(max_lights-1)*density`, so sub-0.02
  is the right range for one small room. Refines the retail-store area-scaling lesson
  downward.
- Only front/back have `place_on_*_adjacent` variants on RelativeGroup — sides are plain
  `place_on_left/right`.
- The custom dessert cart (`custom/424f59…`, cream canopy + gold) is a palette-perfect
  café identity piece — composed into the station so it travels with it.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.88` (v0) → applied a single decisive `modulate_scale=0.9`; follow-up
  builds gave `0.95` = within-noise, declined (converge-don't-chase).
- `no rotation` / `no wall overlap` every build — `place_circle` + `face()` and the slot
  discipline kept geometry clean from v0.

## Manual constraints used
- None. Door auto-clearance + the category-default counter clearance (0.9 m front,
  auto-registered from `IDSDL/default_constraints.py`) covered circulation.
