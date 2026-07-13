# Fast Food

- **Status:** BUILT & VLM-clean — `scenes/work/fast_food_v1.py` (seed=47). Full worked recipe in
  `skills/examples/fast_food.md`. (Supersedes the thin pre-workflow `scenes/fast_food.py`, which
  additionally has a latent build error: it puts a floor-to-ceiling window AND the door on the front
  wall, and the window claims all three of that wall's slots.)
- **Plan:** planner headline "Backlit Menus, Fixed Booths, Bold Red-Yellow Identity" — service counter
  with backlit menu boards + kiosk, fixed booths opposite, four-top field, drink station, terrazzo
  floor, red-and-yellow brand blocking, a tall corner plant.
- **Pattern:** zoned single room, restaurant's skeleton in QSR form. BACK = the **service line**
  (counter + self-order kiosk composed as ONE rigid station → a geometric queue lane). LEFT = the
  **booth run** (bench backing the wall + its own bare table + a facing red chair, built once and
  duplicated). RIGHT = the **drink station** (a short run of the same counter carrying the drink
  machine + cups, red tray bin composed at its right; the TALL Coca-Cola cooler in the back-right
  CORNER, never a wall center). CENTER = two **4-tops** (bare black pedestal table + a 2-red/2-yellow
  molded chair ring). FRONT = the **glass storefront**, which forces the door onto a side wall.
- **The category's real lesson:** every defining FIXTURE is missing from the dataset — no backlit menu
  board, no soda fountain, no fixed booth-and-table unit — and the room still reads, because what names
  a burger joint is the **takeaway burger-and-fries carton massed at viewing height** on every table and
  the counter, not its fixtures. Substitutes: menu board → yellow product sign + illuminated DINER sign;
  fountain → Coca-Cola cooler + retro drink machine.
- **Heroes (pinned):** counter `custom/cffdedd8…` (also the drink console at width=1.5), kiosk
  `hssd/8cf3b150…`, burger+fries `hssd/e9b4c087…` (THE identity prop), Coke cooler `hssd/595c9e23…`,
  drink machine `hssd/58074cda…`, booth `future/56f963cd…`, bare table `hssd/5fa9eb63…`, red chair
  `future/bc34a9bf…`, yellow chair `future/89aa99b8…`, menu band `hssd/79b22453…` + `hssd/29a27d58…`,
  red tray bin `hssd/9523913c…`.
- **Retrieval traps hit:** (1) the rank-1 "yellow fiberglass chair" `hssd/a21c5079…` renders as a **cream
  ROCKING chair** — caught in the phase-1 render, swapped. (2) `hssd/2c2b7183…` looks like a yellow menu
  banner in the montage; at full size it is a **green "Vintage" guitar sign**. (3) `custom/d5884fb5…`
  (neon sign) previews as a **blank white rectangle** (empty-frame trap). Zoom a sign's preview before pinning.
- **Scale/jitter:** RoomGroup modulate_scale 0.85 (0.87→0.85 vote, applied once in the final phase →
  `no rescale`), randomness 0.15; AroundGroup sparsity 0.05 / jitter 0.15 (at 0.2/0.35 the chair rings
  drifted off their tables).
- **Textures:** verified OFFLINE against `wall_textures_embeddings.npz` before building — "solid bright red
  smooth uniform wall" → a true solid deep red (0.672), where the naive "bright red painted wall" → BRICK
  (0.499); "grey speckled terrazzo floor tiles" → real terrazzo (0.701). `place_walls` takes ONE wall
  texture, so the walls carry the red and the PROPS carry the yellow.
- **Kunal revision (2026-07-13) — three fixes the clean VLM loop missed, all now general rules in
  `skills/workflow/design_principles.md`:** (1) the POS **monitor faced sideways** → a service/reception
  desk is worked from the WALL side, so its screen faces the wall the desk stands against and the customer
  sees its back (`room.face(pos, toward="back_wall")`; `place_on_top`'s tournament optimizes position, not
  semantic orientation). (2) **tables towered over their chairs** — the mesh ships **0.96 m (BAR height)**
  vs chairs **0.68-0.71 m TOTAL**, because `AddAsset(width=…)` is a **single-axis** pin that never touched
  the height → `_fit_height(table, 0.75)` (uniform). (3) the **booths floated off the wall** — a floor SLOT
  is a third of the ROOM, not of the wall, and jitter/the solve drift it → `place_on_left_wall_left/right`.
  The pattern: all three are object↔object ERGONOMIC relationships (screen↔operator, tabletop↔seat,
  seat-back↔wall) that no VLM constraint checks. Post-fix `rotate chair to face table` ×6 and
  `rescale room by 0.9` both declined as noise (rings are correct by construction; the shell had just
  returned `no rescale` at that size).
- **Asset-gap risk:** MED — the one high-value ingest is a **red vinyl booth** (the only booth mesh is gray,
  so the booths read as banquette benches); after that, a real backlit menu board.
