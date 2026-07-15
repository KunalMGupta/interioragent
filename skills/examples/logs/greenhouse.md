# Greenhouse

- **Status:** BUILT & VLM-clean — `scenes/work/greenhouse.py` (seed=52). Full worked recipe in
  `skills/examples/greenhouse.md`. Supersedes the 30-line v1 draft that was never built.
- **Pattern:** a daylit **nave**. Twin bench runs (butted `GridGroup.place_row` of 3 bench units each)
  line the two LONG walls — which are **glazed floor-to-ceiling** — plus a centre spine of benches
  (`place_grid(cols=1)`). Back (short, solid) wall = the "shed" end: potting station + hung garden-tool
  board + a tall tropical in each corner. Front (short, solid) = the door.
- **v2 — PLANT BEDS (what makes it a nursery and not a florist):** v1 followed the florist recipe
  (mass a prop on repeated tables) and consequently *looked like the florist shop*. Fix = **thickets**:
  `plant_bed()` = `GridGroup(sparsity=0.0, randomness=0.35)` packing 8-12 mixed plants until their
  bboxes touch, so the foliage interlaces into one mass; four beds dropped in floor slots. `sparsity=0`
  only works because GridGroup runs no overlap solve. A bed costs **one room slot** but holds a dozen
  plants → occupancy jumps with no growth in the shell. **Normalize a bed by WIDTH, never height**: a
  height-fit blew the flat seed-tray mesh (0.30 W x 0.10 H) into a 1.65 m pale-green slab.
- **THE headline (matters to every scene, not just this one):** this build found that the **"black
  window void" and the "black ceiling" were ONE renderer bug**, not a renderer limit. Interior views
  rendered with a **transparent film**, so any ray hitting no geometry (through an opening, or above
  the hidden ceiling) wrote alpha 0 → BLACK. Six examples had built workarounds around it. Fixed in
  `IDSDL/renderer/utils.py`: interior views now render **opaque-film** + with a **raised sky**
  (`INTERIOR_SKY_STRENGTH`, default 3.0, override with `IDSDL_SKY`). Glazing now reads as daylight.
  Asset previews / `place_on_top` tournaments still render transparent (they want a cutout), so
  retrieval is untouched. **Deliberately moody scenes (bar, wine_cellar, music_studio, casino) were
  tuned under the old dim sky — spot-check them, and use `IDSDL_SKY=0.7` if one reads washed out.**
- **Brightness has exactly one lever, and it isn't `add_lighting`:** that helper spends a fixed
  **500 W split across N fixtures** (`object.py`), so `density` only ever adds *more, dimmer* lights.
  A "bright/sunlit" brief is a sky problem.
- **Asset-gap risk: HIGH, and resolved by MASSING** (florist lesson). The dataset has **no potting
  bench, no seed tray, no bag of soil, no empty terracotta pot**. Substitutions: a rustic console
  **with a lower shelf** as the bench (`hssd/291a6b41…`, `scale(1.6)` → a real 0.93 m bench height); a
  low trough of grass as the seed tray (`hssd/37ee3df8…`); a green fabric **grow bag**
  (`hssd/2cc7a3e1…`) for the soil sack (the burlap sack `future/c1ebb64b…` renders as a **PILLOW** —
  dropped). What DOES exist and carries the category: **a real stainless watering can**
  (`hssd/8e8089c9…`, 0.72) and **a wooden garden-tool board** with rake/fork/spade/broom
  (`hssd/0071f864…`, 0.67, and 0.06 m deep = genuinely flat → a legitimate `place_on_wall_*` hang).
- **SCALE TRAP:** the "tall tropical palm" (`future/130b1ed4…`) is natively **0.70 m tall** — its
  retriever scale metadata lies. Scale by HEIGHT uniformly
  (`obj.scale(obj.get_width()*1.75/obj.get_height())`) or it reads as a tabletop plant. Same class as
  the half-scale hospital bed / toy-sized garage car.
- **Textures (verified by embedding against `wall_textures_embeddings.npz` BEFORE building):** the
  library has **ZERO glass textures** (1391 descriptions) — a glazed look can only come from real
  glazing. `"coarse grey gravel and pebble ground"` correctly matches the one true gravel texture
  (0.591); the v1 draft's `"gravel and stone path floor"` matches a **DRY STONE WALL**. The gravel
  still renders flat-grey at room scale — the match is right, so that's a renderer limit → converge.
- **Room size:** vote ran `0.88 → 0.82 → 0.7` (unidirectional = signal), but applying 0.7 would have
  overflowed the three fixed-size bench rows out of their slots (locker_room bug). Read it as "too
  empty" instead: filled the bare entrance floor (grow bags, pots, a third palm) + a mild
  `modulate_scale=0.9` → vote decayed to `0.96` ≈ neutral, declined. `no rotation` / `no wall overlap`
  / no lints from the first build to the last.
