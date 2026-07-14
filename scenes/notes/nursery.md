# Nursery

Built & VLM-clean: `scenes/work/nursery.py` (seed=12). Recipe: [skills/examples/nursery.md](../../skills/examples/nursery.md).

- **Pattern:** Four walls, four jobs — crib hero (+ art above) / dresser changing station (+ mirror) /
  glider nook on a rug under the window / low cubby by the door; middle left open as the play floor
- **Jitter/randomness:** RoomGroup randomness=0.15, modulate_scale=0.8 (auto-sized to 31 m² — a hall;
  vote decayed 0.75 → 0.9 → 0.95 → 0.9 = converged, and the last mild vote was answered by FILLING the
  floor with a toy basket, not by shrinking onto the play space)
- **Exposure:** `IDSDL_SKY=1.2` — an all-white room BLOWS OUT at the default sky of 3.0 (white walls +
  white floor + white crib/rocker/rug = every surface a reflector). **Build from the SHELL**
  (`python workbench.py run scenes/work/nursery.py`); MCP `run_scene` ignores the sky override and
  renders it blown white (A/B verified on the identical file).
- **Review first:** the pastel wall texture (a naive "blush pink painted wall" matches pink TILES; a
  "pale pink plaster" matches a peach that renders SALMON — pick a swatch one notch paler, and open the
  matched `texture.png` offline first); and every unpinned prop's `desc` column in the asset list — a
  BLANK desc is a junk pick (the "plush bunny" was a 0.12 m flat cardboard slab that rendered as a box
  on the cubby, with the whole VLM loop clean).
- **Asset-gap risk:** LOW for furniture — cribs, nursery gliders, changing dressers, kid cubbies, knit
  poufs, shag rugs, plushes, baskets and pastel prints all exist and are good. **The crib MOBILE is a
  hard gap:** the meshes exist (a whole `CeilingObjectRetriever` pool) but are UNPLACEABLE — 0.36–2.80 m
  deep, far past the ~0.25 m wall-hang limit, and `add_lighting` is the only ceiling-hang verb, which
  would make the mobile EMIT and dangle into the room. Wants a `place_on_ceiling(obj, drop=…)` verb.
