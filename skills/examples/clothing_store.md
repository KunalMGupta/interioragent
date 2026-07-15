---
id: example:clothing_store
kind: example
family: retail-spine-loop
category: "apparel boutique (fashion)"
pattern: "TRUE-SIZE SHOP FITTINGS"
read_for:
  - "READ FOR ANY SCENE BUILT ON INGESTED FIXTURES. Also: the persistent \"shrink the room\" vote was a symptom of toy-sized furniture, not a big box"
---
> **Digest (from the pattern index):** **TRUE-SIZE SHOP FITTINGS** — an ingested scan's retrieval `scale` is a GUESSED WIDTH that miniaturises big fixtures (a 5.27 × 2.25 m merchandising wall loads at 0.6 m; a 1.85 m mannequin at 1.06 m), and height-normalising them compounds it — measure the raw glb extents, pin the true width, and let the shell come out big (129 m²). **READ FOR ANY SCENE BUILT ON INGESTED FIXTURES.** Also: the persistent "shrink the room" vote was a symptom of toy-sized furniture, not a big box; keep both wall CENTRES clear of tall fixtures (they swallow that wall's interior camera); `bottom=` on wall-adjacent furniture always trips the floaters lint; a rack whose mesh has a smoked-glass backing HIDES its own garments


# Clothing store — worked example ("true-size shop fittings; the fixture list IS the room")

A warm-industrial apparel boutique. Same **retail spine + perimeter loop** bones as
`retail_store.md` / `bookstore.md`, but this build exists to record a different lesson, and it is
the one that decided the whole scene:

> **The ingested shop scans arrive MINIATURISED, and every instinct you have (height-normalise the
> fixture, shrink the room to match) makes it worse.** Read the raw glb extents and pin the true
> width. A clothing store is a room full of 2 m shop fittings — let the shell come out big.

Program: `clothing_store_v1.py` (seed 13). Built via the guided flow (`flow_start`).

## Prompt(s) this covers
- "a clothing store", "an apparel/fashion boutique", "a fashion retail interior", "a menswear /
  womenswear shop". (For a generic shop/showroom start at `retail_store.md`; for books
  `bookstore.md`; for jewelry `jewelry_shop.md`.)

## Plan summary
Planner → **"Warm-Industrial Boutique: Central Focal Island with Perimeter Merchandising"**: a
central display island organising the main aisle, modular perimeter rails + wooden shelving, a
footwear ledge along the outer wall, a leaning full-length mirror, a rear fitting-room cluster,
a checkout defining the service zone, front-window mannequins. Palette: warm neutrals, light wood,
marble-look floor, black hardware, greenery softening the industrial fixtures.

## THE LESSON — an ingested scan's `scale` is a GUESSED WIDTH, not its real size
The `ShopFixtureRetriever` customs are scanned real shop fittings, authored in real metres. But each
one's retrieval `scale` (a VLM's guess at its width, from a preview render) is applied on load — and
for big fixtures the guess is *far* too small. Measured against the raw glb:

| Fixture | RAW glb (W×H×D) | loads at | I then made it |
|---|---|---|---|
| clothes-on-hangers merchandising wall `custom/12fd8ace…` | **5.27 × 2.25 × 0.71** | 0.60 m wide | a 0.6 m wall trinket |
| shoe/bag/accessory case `custom/c53de778…` | **2.13 × 1.70 × 1.43** | 1.6 m wide | 1.0 m tall (`sized_h`) |
| denim shelving unit `custom/459328e0…` | 1.85 × 2.20 × 0.50 | 1.2 m wide | 1.6 m tall |
| grid rack of jackets `custom/45c9b0bb…` | 2.05 × 2.00 × 0.86 | 1.6 m wide | 1.5 m tall |
| dressed mannequin `custom/0f626c5d…` | 0.70 × **1.85** × 0.45 | **1.06 m tall** | 1.72 m |
| cash-wrap w/ integrated POS `custom/eedaa74b…` | 1.10 × 1.55 × 0.73 | ok | ×0.85 = 1.32 m |

Two compounding mistakes, both mine and both natural:
1. **Height-normalising a fixture (`sized_h`) on top of the bad width** — it preserves the (already
   shrunken) aspect and just re-shrinks it. `sized_h` is right for *taming* a fixture (a rail that
   would tower); it is exactly wrong for a fixture that is already a miniature.
2. **Answering the resulting emptiness with `modulate_scale < 1`.** The `RoomProportions` vote sang
   *shrink* the entire build (0.77 → 0.80 → 0.84 → 0.60 → 0.88) and I kept obeying it. The floor was
   empty because the FURNITURE WAS TOY-SIZED, not because the box was big. Shrinking the box hides
   the symptom and locks in the bug.

**The fix** — a `native(obj, true_width)` helper that uniform-scales to the raw glb width (constants
carry the measured extents, so the program documents the real sizes):
```python
def native(obj, true_width):
    obj.scale(true_width)      # uniform: sets WIDTH, so H and D come out real too
    return obj

W_HANGER_WALL = 5.27   # 5.27 x 2.25 x 0.71 — a full apparel WALL, floor-standing
W_SHOE_CASE   = 2.13   # 2.13 x 1.70 x 1.43
```
Measure with `trimesh.load(glb, force='mesh').extents` — **not** `get_whd()`, which reports the
already-scaled size. Then let `RoomGroup` auto-size: this room lands at **129 m²**, which is simply
what these fittings need. **Generalise: for any ingested/uncurated hero, pin the id AND a real-world
dimension** (garage car, hospital bed — same rule, now with a cheap way to find the true number).

## Pinned assets (gate-3 audit; every mesh eyeballed)
| Role | id | note |
|---|---|---|
| Apparel WALL (hero run) | `custom/12fd8ace…` | 5.27 m of hanging clothes + folded stacks + jeans. **Floor-standing** (0.71 m deep) — never wall-hung |
| Shoe/bag/accessory case | `custom/c53de778…` | shoes, handbags, sunglasses modelled in |
| Denim shelving unit | `custom/459328e0…` | stacked jeans |
| Grid rack | `custom/45c9b0bb…` | perforated grid + four jackets |
| Framed rack | `future/a3e8bf5a…` | retail_store's perimeter rack |
| Garment rail ×6 (spine) | `future/a419b5a4…` | retail_store's double-sided rail — 1.57 m native, hung with dresses |
| Display table ×2 | `hssd/e7b54862…` | retail_store's wood+black-frame table; `sized_h(0.75)` = hand height |
| Cash-wrap | `custom/eedaa74b…` | **POS modelled into the mesh** — no separate register needed, and **place it BARE** (see gotchas) |
| Mannequins ×3 | `custom/0f626c5d…` (dressed), `custom/cd7e4e9c…` (blazer dress form), `custom/f226189c…` (parka outfit) | DRESSED, not the bare `hssd/852f2364…` |
| Folded stacks | `custom/ca90cc08…`, `future/c17aa2e4…`, `custom/3dcb3733…` | the product on the tables |
| Fitting bay | screen `hssd/3d780643…` + mirror `hssd/2603ceec…` + a bench | no changing-cubicle mesh exists — compose one |
| Handbag | `future/aa8e5dc9…` | on the case + the cash-wrap |

**REJECTED — `custom/d7cf7f12…`** ("grey metal double-rail rack hung with garments"): the mesh carries
a large **smoked-glass backing panel** its low-res catalog preview doesn't show. Two of them as the
spine rendered as brown glass partitions **tinting their own garments** — the fixture HIDES the
product, the exact failure `jewelry_shop.md` warns about. No lint, no VLM signal; caught by eye in the
full render. Spine reverted to the `future/a419b5a4…` rails.

## THE layout (spine + perimeter, apparel edition)
- **Centre spine**: two `GridGroup` rows of **three** rails each, `place_on_left`/`place_on_right`
  with `facing="left"` so they run front↔back and frame the aisle; the hero **island** (display
  table massed with folded stacks, on a rug) between them; a **second folded table** set back.
  (Two rails per side left the floor thin — a shop is read by the MASS of its merchandise.)
- **Left wall** = the hero apparel run: the 5.27 m merchandising wall + the grid rack.
- **Right wall** = the **fitting bay** (screen + full-length mirror + bench as ONE `RelativeGroup`,
  placed as a wall unit) + the shoe/bag case.
- **Back wall** = the service/brand wall: cash-wrap centred under the glowing sign, framed rack and
  denim unit flanking.
- **Front** = the storefront: three DRESSED mannequins in one `GridGroup` row at `place_on_front_left`
  (NOT front-centre — see below), a **standard** window pane, the door, an olive tree.

## Gotchas (beyond the size lesson)
- **Don't `place_on_top` a counter whose product is already modelled in — check the FREE surface,
  not the footprint.** The cash-wrap's 1.55 m height *includes* an integrated POS sitting on its top,
  so the usable surface is a narrow strip either side of the screen; crowning it (folded stack +
  handbag) piles props onto a surface that isn't there. `place_on_top` is a VLM tournament that will
  find *some* horizontal region and seat items on it — it has no idea the surface is already occupied
  or too small (the same blindness that seated a table lamp on an armchair cushion in
  living_room_cozy v3). This counter is placed **bare**. Rule: before any `place_on_top`, look at the
  anchor's free top AREA; a fixture that ships with its product needs nothing added. (User catch.)
- **Keep BOTH wall CENTRES clear of tall fixtures.** An interior camera sits at each wall's centre at
  ~1.45 m looking across the room, so a fixture taller than that parked there **swallows that camera**
  — the 2.25 m apparel wall (left-centre) and the 1.70 m shoe case (right-centre) each rendered one
  view as black geometry. This is bakery's ~1.4 m rule at full strength, and true-size retail fittings
  trip it constantly. **Slot the big runs to the wall ENDS** (`_left`/`_right`); let the centres carry
  wall-HUNG pieces (flat, and behind the camera) and the browsing lane. Same reason the mannequin row
  went to `place_on_front_left`: a 1.85 m mannequin at front-centre filled the whole back-wall view.
- **`bottom=` on wall-ADJACENT furniture always trips the floaters lint.** `lint_floaters` exempts only
  true `place_on_wall_*` items (they set `ignore_overlap`); a `place_on_<wall>_wall_<pos>(…, bottom=0.9)`
  shelf is FLOOR furniture lifted off the floor → `FLOATS 1.35 m`. So a wall merchandising unit is
  either **genuinely flat and hung**, or **floor-standing**. (retail_store's `bottom=0.4` shelves would
  lint today.) Related: `hssd/76ae9b47…` (retail_store's wall-merch shelf) also has an **off-centre mesh
  origin** — swapped, not compensated (coffee_shop bench rule).
- **`place_on_wall_*` auto-scales a hung piece to ~0.6 of a wall third** — which blew an 0.8 m shoe
  ledge up to **0.38 m deep** → `WARNING: will read as furniture FLOATING in mid-air`. You cannot
  pre-shrink your way out; hang only genuinely flat meshes (mirror, canvas, sign).
- **Lighting density INVERTS with area.** 129 m² at `density=0.02` = **41 discs, starfield** (budget
  ~39) → **0.01** = a calm 21. Extends the retail ladder to a big floor; the lint prints the budget,
  trust it over the remembered ladder (and over the lint's own generic "~0.05 for a medium room" hint).
- **The warmth in "warm retail lighting" is the ENVELOPE, not the fixture.** `add_lighting` has a fixed
  white budget, so greige walls over pale marble render cool/clinical. `wall_texture="warm sand beige
  plaster"` + the wood table tops carry the warmth (music_studio's "carry the accent with a prop", applied
  to the shell).
- **The scans carry real-world branding** (a shop-fitting scan of a real store). Fine for realism; know
  it's there before shipping to a client-facing render.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.77 → 0.80 → 0.84 → 0.60 → 0.88 → 0.80` — **declined, and the vote train was a red
  herring.** The 0.60 spike came when swapping the glass-panel racks emptied the floor; the answer to an
  empty retail floor is MORE PRODUCT (children_room), and the answer to the *persistent* shrink vote was
  TRUE-SIZE FIXTURES. Final: `modulate_scale=1.0` on a 129 m² shell that the render says is right.
- `[Lint] wall shelf FLOATS 1.35 m` → swapped the off-origin mesh (not compensated).
- `[Lint] 41 ceiling fixtures … STARFIELD (budget ~39)` → density 0.02 → 0.01.
- `WARNING: wall-hung shoe shelf is 0.38 m deep` → dropped it; the shoes are visible on the case below.
- `no rotation` / `no wall overlap` every phase — clean by construction: `facing` omitted on all wall
  placements (the heuristic faces them into the room), the fitting bay composed as one faced unit, door
  and window on disjoint front-wall slots.

## Manual constraints used
- None. Auto overlap/bounds + door clearance + `CategoryClearanceConstraint` (the counter's front)
  sufficed.

## Meta-lesson
Three of this scene's four real defects were **invisible to the whole feedback loop** — miniaturised
fixtures, a glass-panelled rack hiding its own garments, a camera buried inside a display case — and one
of them (the sizes) was caught by the **user**, not by me. The VLM constraints verify geometry, the lints
verify floors and ceilings; **nobody checks whether the furniture is the size it is supposed to be.**
Measure the heroes.
