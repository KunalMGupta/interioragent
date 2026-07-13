# clothing_store — notes

**File:** `skills/examples/clothing_store_v1.py` (seed 13) · **Status:** built & clean 2026-07-13
(`clothing_store_v1.blend`, 129 m², 54 objects, 21 ceiling fixtures). Full recipe:
`skills/examples/clothing_store.md`. Built via the guided 9-gate flow.
(The old stub `scenes/clothing_store.py` — grid racks + a pile table + a floor-to-ceiling storefront —
was never built; it predates the ingested shop scans and the storefront-void lesson.)

**Pattern:** retail **spine + perimeter loop**, apparel edition — two `GridGroup` rows of three
garment rails (`facing="left"`, front↔back) framing a hero display island of folded stacks on a rug,
a second folded table set back; a 5.27 m floor-standing **merchandising WALL** of clothes on hangers
as the left-wall hero run + a grid rack; a **fitting bay** (screen + full-length mirror + bench, one
`RelativeGroup`) and the shoe/bag/accessory case on the right wall; the **service wall** at the back
(cash-wrap with an integrated POS under a glowing sign, framed rack + denim unit flanking); three
DRESSED mannequins at the storefront in front of a standard window pane. Warm sand-beige envelope,
light-marble floor, black hardware, clothing as the colour.

**The lesson this scene exists for — TRUE-SIZE SHOP FITTINGS.** An ingested scan's retrieval `scale`
is a **VLM-guessed WIDTH**, and for big fixtures it is far too small: the merchandising wall
(5.27 × 2.25 × 0.71 m) loaded at **0.6 m**; the shoe case (2.13 × 1.70) at 1.6 m wide; the mannequin
(1.85 m tall) at **1.06 m**. Height-normalising them (`sized_h`) only compounds the shrink, and the
resulting empty floor made `RoomProportions` beg for a smaller room for five straight builds — the
wrong fix, since the box was never the problem. → Read the RAW glb extents
(`trimesh.load(glb, force='mesh').extents`, **not** `get_whd()`, which reports the already-scaled
size), pin the true width via a uniform `obj.scale(true_width)` (see the `native()` helper + the `W_*`
constants), and let the shell come out big. **Caught by the user; invisible to every lint and VLM check.**

**Other gotchas (detail in the example + workflow/vlm_feedback.md):**
- **The cash-wrap is placed BARE — don't `place_on_top` a counter whose product is modelled in.** Its
  1.55 m height already includes an integrated POS on the top, leaving a narrow free strip; crowning
  it piles props onto a surface that isn't there. Check the anchor's FREE top area (not its
  footprint) before any `place_on_top` — the tournament will happily seat items on a surface that is
  already occupied or too small.
- **Keep both wall CENTRES clear of tall fixtures** — the interior camera sits there at ~1.45 m and a
  2 m fitting swallows that whole view (two views came back as black geometry). Big runs go to the
  wall ENDS; the storefront mannequin row goes to `place_on_front_left`, not `place_on_front`.
- **`bottom=` on wall-adjacent furniture always trips the floaters lint** (only true `place_on_wall_*`
  items are exempt) — a wall merch unit is either genuinely flat and hung, or floor-standing. And
  `place_on_wall_*` auto-scales a hung piece up to ~0.6 of a wall third, so an 0.8 m shoe ledge became
  0.38 m deep → "floating furniture" warning. Dropped it.
- **REJECTED `custom/d7cf7f12…`** — its mesh has a smoked-glass backing panel (invisible in the
  catalog preview) that tints and hides its own hanging garments. A fixture that occludes its
  merchandise is worse than no fixture.
- **Lighting density inverts with area:** 0.02 → 41 discs = starfield on 129 m² (budget ~39); 0.01 → 21.
- **"Warm lighting" is the envelope** — `add_lighting`'s budget is fixed white; the warm sand-beige
  plaster + wood tops carry it.

**Distinct from** `retail_store.py` (the generic boutique skeleton, built before the ingested shop
scans existed and still on `bottom=`-mounted wall shelves) — this is the true-size, real-fixture
rebuild of the same pattern.
