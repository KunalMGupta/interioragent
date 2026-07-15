---
id: example:greenhouse
kind: example
family: rows-runs-corridors
category: "greenhouse / conservatory"
pattern: "Daylit glazed nave — twin bench runs lining floor-to-ceiling glass + a centre bench spine;"
read_for:
  - "READ FOR ANY WINDOW OR \"bright\"/\"sunlit\" BRIEF: the \"black window void\" and the \"black ceiling\" were ONE renderer bug (transparent film) and are now FIXED — glaze freely, the old void workarounds are obsolete; and brightness is a SKY setting, never `add_lighting` (fixed 500 W / N)"
---
> **Digest (from the pattern index):** **Daylit glazed nave** — twin bench runs lining floor-to-ceiling glass + a centre bench spine; identity by MASSING potted plants (no potting-bench/seed-tray/soil-bag mesh exists). **READ FOR ANY WINDOW OR "bright"/"sunlit" BRIEF: the "black window void" and the "black ceiling" were ONE renderer bug (transparent film) and are now FIXED — glaze freely, the old void workarounds are obsolete; and brightness is a SKY setting, never `add_lighting` (fixed 500 W / N)**


# Greenhouse / glass conservatory — worked example

Status: **built & VLM-clean** (`scenes/work/greenhouse.py`, seed=52). Final compile: `rescale room by
0.95` (declined — neutral), `no rotation`, `no wall overlap`, no lints.

This is the reference for a **daylit glazed room** — and it is the scene that found and fixed the
**"black window void"**, a renderer bug that ~6 prior scenes had accepted as a law of nature.
Read it before building anything with a window, a glass wall, or a "bright/sunlit" brief.

## Prompt(s) this covers
- "a greenhouse" / glass conservatory / plant nursery / potting shed / orangery.
- More broadly: **any scene whose brief says *bright*, *sunlit*, or *daylight*.**

## THE BIG ONE: the "black void" is a bug, not a renderer limit — it is FIXED

Six examples (executive_office, dental_office, retail_store, florist_shop, coffee_shop, classroom)
independently concluded that *"any opening renders as a black night void — there is no exterior
environment"* and built elaborate workarounds: never full-height-glaze a wall, prefer
`place_window_standard` over `_picture`, stage a mannequin/plant in front of the void, accept an
all-black `wall_*.png` as "a camera artifact". The classroom example separately concluded *"the black
ceiling is the renderer, not a texture — don't burn iterations re-wording `ceiling_texture`."*

**Both were the same one-line bug.** `_render_interior_view` called
`setup_renderer(..., transparent=True)` → `render.film_transparent = True`. A transparent film records
**zero alpha wherever no geometry is hit**, so every window opening and the (deliberately hidden)
ceiling flattened to **BLACK** in the saved PNG. The world was never missing — every render path calls
`set_white_world_background()` and always has.

Two coupled fixes, both in `IDSDL/renderer/utils.py`:

1. **Opaque film for interior views** (`_render_interior_view`: `transparent=False`). The sky is now
   visible through glazing and above the hidden ceiling. Asset previews / `place_on_top` tournaments
   still render transparent — they *want* a cutout — so retrieval and the VLM picker are untouched.
2. **Raise the sky for interior views** (`_setup_interior`: `INTERIOR_SKY_STRENGTH`, default 3.0,
   overridable with `IDSDL_SKY`). The default world (0.7 grey @ strength 1.0) *reads* white on camera
   but is only 0.7 radiance, so it lights almost nothing — fixing (1) alone gives you a blown-white
   pane above a **dim** room ("dark barn with bright windows"). This is also the **only brightness
   lever that exists**: `add_lighting` spends a **fixed 500 W split across N fixtures**
   (`object.py: per_light_energy = 500.0 / max(1, N)`), so `density` only ever buys you *more, dimmer*
   fixtures — it can never make a room brighter.

**Consequences for every scene, not just this one:**
- **You may now glaze freely.** `place_window_floor_to_ceiling` tiles a real mullion frame across the
  wall and *removes* the wall (`groups.py:1977`) — structurally a glass wall. It now reads as daylight.
- The retail/executive "small pane + foreground object" void workarounds are **obsolete**. Keep them
  only as composition choices, not as damage control.
- **Deliberately moody rooms** (bar, wine_cellar, music_studio, casino) were tuned under the old dim
  sky. If one now reads washed out, set `IDSDL_SKY=0.7` for that build — don't re-tune its lighting.

## Asset reality: there is no potting bench, no seed tray, and no bag of soil
The dataset is home-furniture-biased and every literal greenhouse fixture is missing. The **florist
massing lesson** is the whole build:

| Want | Dataset reality | What to do |
|---|---|---|
| potting bench | none | a **rustic wooden console WITH A LOWER SHELF** (`hssd/291a6b41…`) — the right *form* (table-height top, storage under). Native 1.20×0.70×0.43 → `scale(1.6)` = a real ~0.93 m bench |
| seedling tray | none | `hssd/37ee3df8…`, a **low trough of grass** — reads as a seed tray on a bench |
| bag of soil | none (the burlap sack `future/c1ebb64b…` renders as a **PILLOW**) | drop it; use the **green fabric grow bag** `hssd/2cc7a3e1…` on the floor |
| terracotta pot (empty) | none | terracotta-*potted plants* are plentiful — they carry the terracotta tone anyway |
| tall tropical | **RICH** (0.73–0.76) | pin + **SCALE UP** (see below) |
| watering can | **REAL** (`hssd/8e8089c9…`, 0.72) | a signature prop — use it |
| garden tools | **REAL** (`hssd/0071f864…`, 0.67) | a wooden board with rake/fork/spade/broom, **0.06 m deep = genuinely flat** → a legitimate `place_on_wall_*` hang. The plan's "tool wall", for free |

**SCALE TRAP — the "tall tropical palm" is natively 0.70 m TALL.** Its retriever `scale` metadata lies.
Left alone it reads as a tabletop plant, not a vertical anchor. Scale by HEIGHT, uniformly:
`obj.scale(obj.get_width() * 1.75 / obj.get_height())`. (Same class as the hospital bed at half scale
and the toy-sized garage car: **for any uncurated hero, verify a real-world dimension with
`get_whd()` before the first build.**)

## v2 — PLANT BEDS: how a nursery stops looking like a florist shop (Kunal, 2026-07-13)

v1 followed the florist recipe faithfully — mass a prop on repeated tables — and therefore **came out
looking like the florist shop**. Kunal's call: a nursery doesn't read by tidy specimens on furniture,
it reads by **THICKETS** — small pockets where plants are packed shoulder-to-shoulder into one mass of
foliage. This is the differentiator, and it generalizes: *when two categories share a layout pattern,
the tie-break is usually the **density grain** of the product, not more of the same prop.*

**`GridGroup` is the tool, and `sparsity=0.0` is the trick.** A GridGroup is deterministic (it runs no
overlap solve), so a near-zero sparsity packs items until their bounding boxes touch and the **foliage
interlaces** into a single canopy. In any solving group the overlap gradient would fight that back
apart. `randomness≈0.35` jitters the gaps so the block reads grown-in, not CAD.

```python
_BED_MIX = [_PLANT_LU, _PLANT_TC, _SUCCUL, _GRASS, _PLANT_PA, _SEEDTRAY, _PLANT_FL, _TRAY_BLK]

def plant_bed(n=12, cols=4, sparsity=0.0):
    plants = []
    for _ in range(n):
        p = scene.AddAsset("a potted green plant", asset_id=_BED_MIX[i % len(_BED_MIX)])
        p.scale(0.42)                      # normalize by WIDTH — see the slab trap below
        plants.append(p)
    with scene.GridGroup(sparsity=sparsity, randomness=0.35) as bed:
        bed.place_grid(plants, cols=cols)
    return bed

room.place_on_front_left(plant_bed(12, cols=4))   # each bed = ONE floor slot
room.place_on_right(plant_bed(12, cols=4))        # so the shell does NOT balloon
```

Three things that make this work:
- **A bed costs ONE room slot** but fills it with a dozen plants — so you get a big jump in occupancy
  with **no growth in the shell** (the RoomGroup sizes from slot occupancy, not object count). This is
  the clean answer to a "too empty" room that you *can't* shrink (see the room-size note below).
- **Normalize the bed by WIDTH (`scale(w)`), never by height.** The mix contains flat troughs — the
  seed tray is 0.30 W × 0.10 H — and `_fit_height(0.55)` multiplies one of those ~5.5× into a **1.65 m
  pale-green SLAB** that eats the whole bed. (Built it, saw it, fixed it.) A common width keeps every
  footprint packable while natural height variation is preserved, and that variation is exactly what
  makes a canopy read as grown-in rather than as a shelf of identical product.
- **`obj.scale()` returns `None`** — never chain it (`AddAsset(...).scale(0.42)` puts `None` in your list).
- Beds are **floor anchors → phase 1**, not phase-2 dressing: they size the room.

## The layout: a nave — twin bench runs on the glass + a centre spine
Same family as library's symmetric corridor, but the "walls" the runs line are **walls of glass**:
- **LEFT + RIGHT (long, GLAZED)** = twin bench runs, each a butted `GridGroup.place_row` of 3 bench
  units, placed `place_on_left/right_wall_center` with **`facing` omitted** (the heuristic faces them
  into the room). Loading both long walls is what makes the room read as a deep nave.
  Glazing a wall you also line with furniture is fine and established (gym does it).
- **CENTRE** = the hero spine: `GridGroup.place_grid([...], cols=1)`, a column of benches down the axis.
- **BACK (short, solid)** = the "shed" end — the potting station (watering can + tool box on top), the
  hung tool board, a tall tropical in each corner. Keep this bench LOW (~0.93 m): a fixture taller than
  the ~1.4 m interior camera at a wall centre **blinds that view and triggers a phantom rotation
  storm** (bakery lesson).
- **FRONT (short, solid)** = the door.

## Textures: verify the match, don't guess the wording
The texture library has **ZERO glass textures** (1391 descriptions, 0 hits) — so a glazed look can
*only* come from real glazing, never from `wall_texture`. Checked by embedding candidate strings
directly against `IDSDL/assets/wall_textures_embeddings.npz` (the bakery method) before building:
- ✅ `"coarse grey gravel and pebble ground"` → matches the library's **one true gravel** texture (0.591).
- ❌ `"gravel and stone path floor"` (the old v1 draft's wording) → matches a **DRY STONE WALL**.
- Caveat: the gravel still renders as fairly flat grey at room scale. The *match* is right, so this is a
  renderer/tiling limit, not a wording problem → **converge, don't chase** (bakery).

## VLM feedback we hit and how we resolved it
- **Room size: `0.88 → 0.82 → 0.7`, unidirectional.** Never flipped ⇒ signal, not noise
  (living_room_cozy's vote-train rule). But **applying the voted 0.7 would have been the locker_room
  bug**: the shell auto-sizes to *fit* three fixed-size `GridGroup` bench rows, and shrinking well
  below 1.0 pushes them out of their slots into overlaps. → One decisive change instead: **fill the
  bare floor** (children_room: fill before shrinking) with grow bags, pots and a third palm at the
  entrance, plus a mild `modulate_scale=0.9`. Vote decayed to **0.96/0.95 ≈ neutral** → declined, done.
- **`no rotation` / `no wall overlap` from the first build to the last** — by construction: `facing`
  omitted on every wall placement, the bench runs are deterministic rows, the tool board is genuinely
  flat, and the door sits on a wall no glazing claims.

## Manual constraints used
- None. The bench rows are deterministic; door clearance is automatic; the aisles are geometric
  (the room's own slots), not a `ClearanceConstraint`.
