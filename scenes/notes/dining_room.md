# Dining Room

- **Status:** BUILT & VLM-clean — `scenes/work/dining_room.py` (seed=6). Full worked recipe in
  `skills/examples/dining_room.md`. (Supersedes the thin pre-workflow `scenes/dining_room.py`, one
  of the 52 batch category stubs — never individually built.)
- **BUILD AS:** `IDSDL_SKY=1.5 python workbench.py run scenes/work/dining_room.py`. A default-sky
  render of this program is NOT the scene — see the sky/budget note below.
- **Plan:** planner headline "Warmth-Centered Family Dining Ensemble" — a dark rectangular table as
  the hero, a continuous warm-wood palette, a rug defining the dining zone, a sideboard on the
  backdrop, a sculptural pendant over the table + an ambient floor lamp, daylight filtered through
  tall drapes, a curated wall gallery.
- **Pattern:** `meeting_room`'s table hub, domesticated. CENTER = a dark trestle table (`width=2.2`)
  + a rectilinear ring of 8 upholstered chairs (3/long side + 1 each end), `AroundGroup(sparsity=0.1,
  jitter=0.25)`, on a rug (`size=0.8`), under ONE drum pendant (`density=0`). BACK = the SERVICE wall
  (low buffet + photo gallery above it; plant + floor lamp in the corners). LEFT = floor-to-ceiling
  window + cream drapes. RIGHT = a landscape. FRONT = the door.
- **What makes it read as a dining room:** the SET TABLE (plate stack + wine glasses/decanter +
  floral centerpiece) — jewelry_shop's product rule on a domestic surface. All three props were
  verified to exist at the audit gate; the dataset has NO per-seat place setting, and `place_on_top`
  rows items across the anchor's centre, so the table reads as being LAID rather than as 8 covers.
  That is an honest DSL limit — don't fake it with a prop that isn't a place setting.
- **Heroes (pinned):** table `hssd/66602a70…` (BARE dark trestle — "…, no chairs" defuses the SET
  trap), beige upholstered chair `hssd/6c368c15…` (pinned: the chair carries the palette), low
  warm-wood buffet `future/ef3867e2…` (the picker's own top picks were a tall chest + hutches, over
  the ~1.4 m camera eyeline — browsed for a low one, scaled BY HEIGHT to ~0.85 m), flat wool rug
  `hssd/249bbdc…`, gallery collage `future/e2b0dcb4…` (real photo content; the rank-1 sibling
  `future/09f28392…` is BOTH reversed-front and empty-frame), landscape `hssd/4192b936…`,
  centerpiece `hssd/3a30a289…`, plates `hssd/f5440426…`, glassware `hssd/a9d615bc…`.
- **Fixes (both invisible to the VLM loop — it was CLEAN on the broken renders):**
  1. **Bright showroom, not "warm".** The brightness dial FLIPS at phase 3: measured mean pixel
     value, sky 3.0→1.2 moved a phase-1 render 139→105, but sky 3.0→1.5 moved the FULL render only
     197→188 — because `add_lighting`'s fixed **500 W** then dominates a ~27 m² room. Fix =
     `scene.light_budget = 180.0` (sky stays 1.5 for the daylight). Sky is the lever for an unlit
     room; the budget is the lever once a fixture hangs.
  2. **Cool grey walls.** `"warm greige painted wall"` matched a LIGHT GRAY plaster at 0.596 — a
     genuine matching bug, settled offline against `wall_textures_embeddings.npz` in 5 s (never a
     rebuild). `"solid warm beige smooth uniform wall"` → a true beige at 0.744.
  3. **Gallery vs buffet (designed out, never built wrong).** The collage is 1.66 m tall; hung at
     the 1.5 m slot centre its bottom would sit at 0.67 m — below the 0.85 m buffet under it, firing
     the wall-object-clearance pass and sliding the BUFFET off the centre of its own wall. Caught
     with `get_whd()` pre-build; pre-scaled to ~0.95 m → blend confirms bottom 1.28 m.
- **Room-size vote:** `1.05` → `0.97` → `0.99` — never left the ±5% noise band → **declined outright**
  (no application). The layout never moved after phase 1.
- **Clean by construction:** `no rotation` / `no wall overlap` from the first build to the last —
  `place_rectilinear` gives the ring one uniform facing (a per-chair `face()` would fan the end
  chairs inward), and every wall placement omits `facing`.
- **Asset-gap risk:** LOW. No ingest.
- **Verified in the blend** (the loop checks none of these): buffet flush to the back wall (far edge
  at y=0.000), gallery bottom 1.28 m clear of the buffet top, the 3 table props seated at z=0.818 =
  the table top (a phase-2 prop gated outside its `with` block silently never places — prison_cell),
  2 buffet props at 0.850, every floor object bottoming at exactly 0.000.
