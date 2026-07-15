# Bakery — worked example

Status: **built & VLM-clean** ("Glassfront Bakery with Brick Anchor and Blue Mullion
Rhythm", `skills/examples/bakery_v1.py`, seed=12). Final compile: `no rotation / no wall
overlap / rescale room by 0.98` (noise, declined) at `modulate_scale=0.78`. Built
through the guided 9-gate flow (flow_0712_171017_e837), four phase-1 layout iterations
+ one full-build convergence pass + one user iteration (v1.1 below).

## Prompt(s) this covers
- "a bakery", "a patisserie / boulangerie", "a bread shop", "a bakery cafe with a
  pastry counter and window seating". Scale the counter run + add 2-tops for a bigger
  bakery-café.

## Plan summary (from the planner)
Street-facing glassfront bakery: a full-height blue-mullioned glass storefront; a
central pastry display in a white service spine (croissants/breads the focal); a
horizontal brick service counter anchoring circulation; stainless open shelving +
industrial textures behind; a blue branding backdrop; slim light-wood window-bar
seating along the glass; warm amber targeted lighting over the pastry zone.

## The layout idea: service wall + glass-front perch (coffee_shop × retail hybrid)
A bakery is a **service-spine shop** (coffee_shop's cousin) whose seating hugs the
STOREFRONT, not the floor. 3 floor slots + walls:
- BACK: the service wall = white counter with warm wood top (`width=2.4`) beside a
  stocked mid-height industrial wire rack, composed as ONE rigid station
  (`RelativeGroup.place_on_back_left(shelf)` — diagonal offset, staff aisle baked in).
  **The counter top IS the pastry display**: no glass display-case mesh exists (best
  hits: an empty white cabinet, a Häagen-Dazs freezer, a china cabinet — and the
  promising "light oak display rack with circular products" is a PIZZA rack up close);
  massed product substitutes (jewelry/coffee_shop lesson): two tiered pastry stands +
  sponge cake + rustic bread board + takeaway cups + espresso machine + POS in one
  `place_on_top([...])`.
- FRONT: the window bar = rustic wood console (`width=2.4`) + 3 round-seat wooden
  stools, one AroundGroup (`place_rectilinear(longer_side1=stools)`, default facing —
  bar.md rule), placed with **`place_on_front_wall_center` so the ledge hugs the
  glass** (a front SLOT placement left it drifting mid-floor). Standard window with
  DEEP BLUE curtains (the plan's blue rhythm) + door front-right.
- LEFT-CENTER: one coffee_shop 2-top (pedestal pub table + papercord chairs + jute
  rug + cup/donut box).
- Walls: French blue menu chalkboard behind the counter (the blue brand backdrop),
  'Bread' tin clock left, bread/wine still-life right. Corner plant.
- Lighting: black dome pendant over the counter group (singular, density 0.15) +
  flush LED fill at 0.01.

## Pinned assets (audited previews)
| Role | id | note |
|---|---|---|
| Service counter | `hssd/67b505c2cfc433bc4ffe39250cafda3951d91939` | white base + warm wood top ("white service spine"); rests flat (laundromat) |
| Wire rack | `custom/71bda402b67456713f4f06f422bb8bb8ce1455da` | industrial grey; squat mesh — see height gotcha |
| Window bar | `hssd/f72c0e86085c6b6f48b82d47d5066248be8b7c4a` | rustic warm wood console, stretch `width=2.4` |
| Stool ×3 | `hssd/5cbddc4215af577a945d42dae708197b48a6a14e` | round seat, three legs; `modulate_scale=0.85` to perch under the console |
| Pendant | `hssd/b1c964b529d36176ec5a13f5b325262dfdd7f217` | black dome, short drop, SINGULAR |
| Pastry stands | `hssd/351f165d…` (3-tier) + `hssd/1c2885ea…` (sponge cake) | the pastry-display mass |
| Bread board | `hssd/92fc2ee204fda4be19d08b79f79f68fc87e9afaa` | rustic sliced-bread set — the literal bread prop |
| Bread bin | `hssd/27584d59cc4fe564020ed5d65dbb5762d0638404` | cream + beech lid, shelf stock |
| Wicker basket | `future/c96d2ee0-8593-42b8-bcc3-bd9e4476b49d` | fabric liner, shelf stock |
| French blue board | `hssd/a8fe5f34c49c3e11bd9f5ef3380b5e7efef943e2` | FLAT wall sticker; French text = boulangerie + the blue brand wall |
| Display fridge | `hssd/cae4c60830bba615ff533dc23ffee6e6e5c7d14e` | slim glass-door upright; the bakery drinks/cake fridge (v1.1) |
| Espresso / POS / takeaway / cup / donuts / 2-top table+chair | coffee_shop pins | see coffee_shop.md |

## What worked / gotchas
- **The camera-height ceiling for wall-center fixtures.** The interior wall cameras sit
  at ~1.4–1.5 m at each wall's center; a fixture taller than that near ANY wall center
  swallows that wall's whole interior view (three phase-1 builds hit this at rack
  heights 1.6–1.75). Fix: keep wall-center fixtures ≤ ~1.25 m (mid-height also matched
  the plan's bread shelving) or offset them off the centerline.
- **Squat-mesh scaling.** The wire rack's native aspect is w:h ≈ 1.45; a pure uniform
  `scale()` to rack height blew it to ~2.5 m wide/deep. Recipe: uniform-scale to target
  height, then `scale_only_width/depth` to real fixture dims — single-axis distortion is
  invisible on an open wire frame.
- **Window bar = wall placement, not a front slot.** `place_on_front(group)` left the
  ledge drifting mid-floor (door clearance + jitter push a front-slot group around);
  `place_on_front_wall_center(group)` pins the console to the glass with the stool row
  on the room side, correct by the default wall-facing heuristic. No `face()` on the
  row (bar.md straight-row rule) — `no rotation` every build after.
- **Texture strings match, the RENDERER pales them.** "warm red brick"/"red brick"/the
  caption-exact wording ALL retrieve genuine red-brick textures (verified by embedding
  the queries against `IDSDL/assets/wall_textures_embeddings.npz` and opening the
  winning png) — but at room scale under the light budget the wall renders pale blush
  with faint coursing. If a texture looks wrong, CHECK THE MATCH before rewording;
  when the match is right, it's a renderer limit — converge, don't chase wordings.
- **Bakery-prop coverage:** bread board / bread bins / tiered pastry stands / donuts /
  cakes exist and read well; NO pastry display case, NO bread-filled basket, NO
  baguette mesh (logged as ingest candidates for a stricter boulangerie).
- **Skipped the coffee_shop "warm accent armchair" vibe item deliberately** — this
  plan specifies slim light-wood seating at the glass; blue curtains + French board
  carry the character instead.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.87→0.85→0.8→0.77` (Ph1 iterations) `→0.76` (Ph2) `→0.75` (full)
  → held per render-wins-early, then ONE decisive `modulate_scale=0.78` in the final
  phase → `0.92`, then `0.95` = noise, declined. Sparse-room shrink (laundromat rule)
  converged in one step.
- One phase-1 build flagged `rotate stool/chair/counter/console...` ×8 on a layout that
  read correct in every view (rectilinear row + place_circle+face are correct by
  construction) → declined as noise; the flags vanished once the wall-camera occlusion
  was fixed — **a garbage interior view makes the RotationConstraint hallucinate**.
- `no wall overlap` every build: window front-LEFT, door front-RIGHT, art on three
  different walls, board hung over the LOW rack (laundromat art-over-low-run).

## Manual constraints used
- None. Door auto-clearance + counter category clearance covered circulation; the
  staff aisle is geometric (station composition), not a ClearanceConstraint.

## v1.1 — user iteration (same build, two fixes)
- **"The table with the three stools looks smaller than the seats"** → widened the
  window-bar ledge to `width=2.8` + `scale_only_depth(0.5)` (a plank-top console takes
  single-axis depth invisibly). The ledge now reads as a real bar top over its stools.
- **"Add a refrigerator — the bakery looks a bit empty"** → pinned the slim glass-door
  display fridge `hssd/cae4c60830bba615ff533dc23ffee6e6e5c7d14e` ("a tall glass door
  display refrigerator" routes to ShopFixtureRetriever, top pick) and placed it
  `place_on_right_wall_left` — lands at the back-right corner beside the counter's end,
  exactly where a bakery drinks/cake fridge belongs. Deliberately OFF the wall center
  (the ~1.4 m camera-height ceiling above). Room-size vote went 0.95 → 0.98 with the
  extra fill = fully converged.

## Possible refinements (not blocking)
- Ingest a real glass pastry display case + a baguette basket for a stricter read.
- The 'Bread' tin clock resolves to a generic mint kitchen clock at render; pin a
  bolder bakery sign if one is ingested.
- A second 2-top on the right would fill a larger-footprint variant.
