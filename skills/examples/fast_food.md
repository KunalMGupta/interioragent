# Fast food / burger joint — worked example

Status: **built & VLM-clean** ("Backlit Menus, Fixed Booths, Bold Red-Yellow Identity",
`scenes/work/fast_food_v1.py`, seed=47). Converged full build: `no rescale` / `no rotation` /
`no wall overlap`, no `[Lint]` lines, at `modulate_scale=0.85`. Built through the guided 9-gate
flow (flow_0713_025725_afb6): one phase-1 layout iteration, one phase-2 pass, one full build,
one vibe rebuild.

## Prompt(s) this covers
- "a fast food shop", "a burger joint", "a QSR dining area", "a food-court unit". Scale the
  counter run + add booth units for a bigger store.

## Plan summary (from the planner)
Right-hand service counter with backlit digital menu boards on a red wall, linear pendant task
light, a self-order kiosk; fixed booths opposite; a field of wood four-tops; bar-height stools
along the window; speckled terrazzo floor; bright ceiling + warm seating glow; red-and-yellow
brand blocking; a tall corner plant.

## The layout idea: zoned single room (restaurant.md's skeleton, QSR edition)
Restaurant's bar-wall/banquette-wall/cluster-field, with the bar replaced by a service line:
- **BACK = the SERVICE LINE.** Counter (`width=3.0`, hero) + the self-order KIOSK composed at its
  left as ONE rigid station (`RelativeGroup.place_on_left`) → one floor slot, and the queue lane in
  front of it is geometric, not a soft clearance (the bar.md rigid-station rule).
- **LEFT = the BOOTH RUN.** Booth bench backing the wall + a bare pedestal table + a facing red
  chair; built once, duplicated. Placed `facing="right"` so the bench backs the wall.
- **RIGHT = the DRINK STATION.** A short (`width=1.5`) run of the SAME counter mesh carrying the
  drink machine + cups, with the red dome-lid waste bin composed at its right — one station, one
  slot ("bus your tray where you refill your drink"). The TALL Coca-Cola cooler goes in the
  **back-right corner**, never a wall center (the bakery ~1.4 m camera-height rule).
- **CENTER = the dining field.** Two 4-tops: bare black pedestal table + a 2-red/2-yellow chair ring.
- **FRONT = the glass storefront** (floor-to-ceiling).

## Pinned assets (previews eyeballed at gate 3)
| Role | id | note |
|---|---|---|
| Service counter | `custom/cffdedd8d354e346e510f227b4a6bc5b65dc3dcb` | long solid-front counter (0.87); reused at `width=1.5` as the drink console |
| Self-order kiosk | `hssd/8cf3b150fceea0aed2af3f73b0f68839c4f41147` | black touchscreen kiosk — a pure QSR cue, found under a *checkout counter* query |
| **Burger + fries** | `hssd/e9b4c087f46bf372c890cf074de55fe974092378` | **THE identity prop** — takeaway carton; mass it on every table + the counter |
| Popcorn + soda | `hssd/02c784e528d209e63cfeb98944ae483256338bc5` | red/white striped box + coke bottle |
| Coca-Cola cooler | `hssd/595c9e233d3e72bb23b7cfa22a5cc3e2523a1350` | red/white; the drink zone's anchor + half the palette |
| Drink machine | `hssd/58074cda1782f1631517f10cebd5eb9fb9edc38d` | retro red/white; the soda-fountain substitute |
| Booth bench | `future/56f963cd-9ff6-48af-bd68-1db9411b1e6c` | restaurant's booth; GRAY — the one weak link (see gaps) |
| Table | `hssd/5fa9eb631ea0ea89463b1c7b36ad8537310903fb` | BARE black square pedestal — no SET trap |
| Red chair | `future/bc34a9bf-a55d-4044-b0a5-fab42919886c` | molded, sled legs |
| Yellow chair | `future/89aa99b8-c388-4baa-b029-7a754cdd24dd` | molded; matches the red chair's form |
| Menu band | `hssd/79b224535ddd7ecdff06a86f9d17d98c08536592` + `hssd/29a27d5893f1b3383204673903f1a385588e02ef` | yellow 'Milkshake' product sign + ILLUMINATED 'DINER' sign |
| Waste bin | `hssd/9523913c4c8438a9c184e378e101a8ac7ff067fe` | red dome-lid — the tray station |
| Diner print | `hssd/20af5e18cc65ec1537972cf28ba2bed7f4936c81` | red booths + checker floor, over the booth run |

## What worked / gotchas
- **THE MISSING FIXTURE IS THE WHOLE CATEGORY — and none of the three exist.** No backlit menu
  board, no soda fountain, no fixed booth-and-table unit is in the dataset. The scene still reads,
  because each was substituted rather than shipped empty (jewelry/bakery product rule):
  menu board → a **yellow product sign + an illuminated DINER sign** as the lit band over the
  counter; soda fountain → the **red Coca-Cola cooler + a retro drink machine on a counter run**;
  booth unit → **bench + bare table + facing chair** composed as one RelativeGroup. What actually
  makes a viewer say "burger joint" is none of the fixtures — it is the **takeaway burger-and-fries
  carton massed at viewing height**. Without it this room is a red cafeteria.
- **A `place_door` position is `left|center|right` — there is no `"front"`/`"back"`.** They are the
  wall's OWN horizontal thirds, on every wall. `place_door("right_wall", position="front")` raises a
  bare `ValueError: Label must include one vertical … and one horizontal … part` from `wall.py` deep
  inside `RoomGroup.__exit__` → `_register_door_clearances`. **The static lint does NOT catch it**
  (the kwarg is valid, the value isn't) — it costs a full build to find.
- **A floor-to-ceiling window and a door CANNOT share a wall.**
  `place_window_floor_to_ceiling` calls `_register_wall_occupancy(wall, ["left","center","right"])`
  — it claims **all three slots** and REMOVES the wall. A storefront therefore forces the door onto
  a side wall. (The pre-workflow draft `scenes/fast_food.py` puts both on the front wall; it lints
  clean and would collide at build.)
- **`place_on_top` targets the group ANCHOR — so a booth's meal lands on the BENCH CUSHION.** The
  booth unit's anchor is the bench, not the table. Compose the table as its own sub-`RelativeGroup`
  (table = anchor, `place_on_top(burger)`), then `booth.place_on_front(table_unit)`
  (living_room_cozy v3, hit here from the booth side).
- **Slot economy held the shell at QSR scale**: 6 floor slots (station / 2 booths / 2 four-tops /
  drink station) + 2 corners (cooler, plant). Room-shrink vote 0.87 → 0.85 → applied ONCE at the
  final phase → `no rescale`.
- **The palette splits across texture and props.** `place_walls` takes ONE `wall_texture`, so the
  WALLS carry the red and the PROPS carry the yellow (yellow chairs + yellow signage) — the
  music_studio accent-on-a-prop rule, and the reason to pin a yellow chair rather than reword walls.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.87` (Ph1) → `0.85` (Ph2): held through the early phases (render-wins-early),
  then applied ONE decisive `modulate_scale=0.85` in the final phase → `no rescale`. Converged in
  one step, as the laundromat/bakery sparse-room rule predicts.
- `rescale room by 0.9` on the **vibe rebuild** (one corner plant added to an otherwise identical
  build that had just returned `no rescale`) → **declined as noise**. One plant cannot make a room
  10% too big; a vote that flips back and forth around a shell the render says is right = converged
  (bookstore/kindergarten oscillation rule).
- `no rotation` / `no wall overlap` on every build: booths `facing="right"`, wall furniture left on
  the default facing heuristic, art on three different walls, door and storefront on different walls.

## Asset gaps (MED risk — the fixtures are missing, the food is not)
- **No red vinyl booth.** The only booth mesh (`future/56f963cd…`) is GRAY, so the booths read as
  banquette benches. The single highest-value ingest for this category.
- **No backlit menu board, no soda fountain, no fry station, no drink cup with a straw.** All
  substituted above; a real illuminated menu board would sharpen the counter wall most.
- Rejected at audit: `hssd/2c2b7183…` (thumbnail reads as a yellow menu banner; at full size it is
  a GREEN "Vintage" GUITAR sign) and `custom/d5884fb5…` (neon sign — previews as a BLANK white
  rectangle, the office_modern empty-frame trap). **Zoom the preview before pinning a sign.**
- **caption ≠ mesh, caught in the render:** the rank-1 "yellow fiberglass chair"
  (`hssd/a21c5079…`) is a **cream ROCKING chair** with curved runners — wrong colour AND a lounge
  form. Swapped for `future/89aa99b8…` (a true yellow molded chair matching the red one's form).

## v1.1 — user iteration (three fixes the clean VLM loop missed)
The v1 build was fully VLM-clean (`no rescale` / `no rotation` / `no wall overlap`). A human found
three errors immediately. **Every one is a semantic relationship between two objects — screen↔operator,
tabletop↔seat, seat-back↔wall — and no VLM constraint checks any of them.** All three are now general
rules in [../workflow/design_principles.md](../workflow/design_principles.md); they are NOT fast-food facts.

- **"The monitor on the counter should face the back wall."** A service/reception desk is worked from
  the WALL side, so its screen faces the wall the desk stands against and the customer sees its back.
  `place_on_top`'s tournament optimizes position, not semantic orientation, and had left the POS
  broadside to the room. → `room.face(pos_terminal, toward="back_wall")` (wall targets are RoomGroup-only
  and 90°-snapped; applied at the END of compile, so it overrides the baked placement rotation).
- **"The tables are a lot taller than their seats."** The cafe-table mesh ships **0.96 m** — BAR height —
  and the molded chairs are **0.68–0.71 m in TOTAL** (seat ≈ 0.43 m), so the tabletop sat above the chair
  backs. Root cause: `AddAsset(..., width=0.8)` is a **single-axis** pin — it stretched the width and left
  the height alone, so I had never actually set the table's height. → `_fit_height(table, 0.75)` (uniform).
  The mirror of restaurant's bar-stool rule, hit from the table side.
- **"The comfy seats on the left should be against the wall."** The booths were placed in floor SLOTS
  (`place_on_left` / `place_on_front_left`), which left a visible gap behind each bench — a slot is a
  third of the ROOM, not of the wall, and `randomness` + the grad solve drift the group off it. **A booth
  backed by air is not a booth.** → `place_on_left_wall_left` / `place_on_left_wall_right` (wall-adjacent
  verbs pin flush and re-snap after the solve; omit `facing` — the heuristic already turns them inward).

Post-fix build: `no wall overlap`, no `[Lint]` lines; `rotate <chair> to face the table` ×6 returned and
was **declined as noise** (the rings are `place_circle` + `face(toward=table)`, correct by construction —
the render shows every chair addressing its table; the weak-smoke-alarm rule from bar/restaurant/salon),
as was `rescale room by 0.9` (the shell had just returned `no rescale` at this size; wall-pinning the
booths freed floor without changing the shell).

## Manual constraints used
- None. Door auto-clearance + the counter's automatic `CategoryClearanceConstraint` opened the
  queue lane; the kiosk/bin aisles are geometric (station composition).
