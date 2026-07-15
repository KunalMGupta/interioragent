---
id: example:bookstore
kind: example
family: retail-spine-loop
category: "indie bookstore"
pattern: "Retail spine + perimeter loop, book edition"
---
> **Digest (from the pattern index):** **Retail spine + perimeter loop, book edition** — stocked honey bookcase runs on both long walls (library's twin runs) + a centre spine of **double-sided face-out book displays** framing the aisle (retail rail pattern) + a hero new-releases table massed with book stacks; pastel pin-for-palette reading nook; checkout `facing="back"` sees the door. Teaches "the pre-stocked fixture IS the product" at full strength + a ~56 m² lighting-density point (0.015, not 0.04) + decaying-rescale-vote-equals-converged


# Bookstore — worked example ("Curved Spine Bookstore", guided 9-gate flow)

A warm indie bookstore: honey-timber stocked bookcase runs on both long walls, a **central
browsing spine of double-sided face-out book displays** framing the centre aisle, a
"new releases" hero display table massed with book stacks, a **pastel reading nook**
(dusk-pink + mint barrel chairs around a round timber table on a rug), a wooden book cart,
and a checkout counter by the storefront door. Blend of three skeletons: retail_store's
**central spine + perimeter loop**, toy_shop's **pre-stocked shop fixtures carry the
identity**, and library's **long-wall shelf runs**. Built via the guided flow
(`flow_start`), converged in 2 full renders. Program: `bookstore_v1.py` (seed 21).

## Prompt(s) this covers
- "a bookstore" / bookshop / indie book store / book shop.

## Plan summary
Planner → **"Curved Spine Bookstore: Transparent Entry, Warm Shelving, and Cozy Browsing
Nooks"**: glass storefront + entry anchor, a central curved double-sided shelving spine
choreographing circulation toward a distant focal display, warm honey timber shelving with
integrated shelf lighting, pastel-upholstered browsing/seating pockets on soft rugs, book
cart, wayfinding signage. Palette: light honey wood, cream envelope, pastel sage/blush
accents, books as the colour.

## Pinned assets (gate-3 audit; every mesh eyeballed or reused from a verified scene)
| Role | id | note |
|---|---|---|
| Wall shelf run (×6) | `hssd/2db50fb1…` | light honey bookcase, WELL-STOCKED + lower cabinet — the palette-perfect wall unit |
| Spine display (×4) | `hssd/7b9c92c0…` | true **double-sided face-out book display**, light wood, filled with colourful covers |
| Display table | `hssd/e7b54862…` | retail_store's wood-top + black-frame table (hero "new releases") |
| Checkout counter | `hssd/7379d887…` | curved reception desk = cash-wrap (3rd reuse) |
| POS | `hssd/9dbca041…` | shrink to 0.35; `room.rotate(pos, 180)` to face the customer |
| Focal book stand | `hssd/f3a8d459…` | angled stand FULL of colourful books (back-wall focal) |
| Nook chairs | pink `hssd/d4c936c5…`, mint `future/18d02c7b…` | **pin-for-palette** — the pastel read hangs on them |
| Nook table | `hssd/d4bff730…` | natural wood round side table |
| Book cart | `hssd/458fbf1e…` | rustic wooden bookcase on wheels — reads as a shop book cart |
| Book stacks | `hssd/55a5fd86…` + generic "a stack of hardcover books" | the PRODUCT prop, massed on every surface |
| Neon sign | `custom/d5884fb5…` | toy_shop's glowing sign, back wall |

Gaps worked around (no ingest): no purpose-built cash-wrap (reception desk, as ever); no
true "gondola bookshelf" (the double-sided face-out display is better — it comes stocked);
no curved/arched spine meshes (straight face-out rows carry the choreographed-aisle idea).

## THE layout: retail spine + perimeter loop, book edition
- **Long walls = stocked bookcase runs**: `GridGroup.place_row(3 × WALL_SHELF)` per side,
  height-normalised to 2.1 m via `sized_h`, placed `place_on_left/right_wall_center` with
  **facing omitted** (heuristic faces them into the room).
- **Centre field = spine rows**: 2 × double-sided face-out displays per row (`sized_h` 1.35 m),
  `place_on_left`/`place_on_right` with **`facing="left"`** so the rows run front↔back and
  frame the centre aisle (retail rail pattern, verbatim).
- **Centre = hero table** massed with book stacks + a grounding rug; **back = book cart** in
  the aisle + the **focal book stand on the back wall** (visible from the entry) + neon above.
- **Back-left = the pastel nook** as ONE `AroundGroup` (round table anchor, `place_arc` the two
  chairs, explicit `face()` each at the table, rug, small book stack on top).
- **Front-right = checkout** `facing="back"` so the cash-wrap sees the door (toy_shop pattern);
  door front-right, standard window front-center.

## VLM feedback we hit and how we resolved it
- **`rescale room by 0.75` (Ph1) → `0.8` (Ph2)** → held per render-wins-early, applied ONE
  decisive `modulate_scale=0.85` in the final phase → vote decayed to `0.9` and stayed there
  across two full builds with a well-filled render → **declined the residual** (converge-don't-
  chase; a decaying vote = converging, per executive_office).
- **`[Lint]` 35 ceiling fixtures on 56 m² = STARFIELD** (budget ~17) at `density=0.04` — I had
  treated 0.04 as "medium room" but 56 m² is coffee-shop-plus, not retail-hall. → **0.015** →
  lint gone, calm ceiling. Rule refined: ~50-60 m² wants 0.015-0.02, not 0.04.
- `no rotation` / `no wall overlap` every phase — clean by construction (facing omitted on wall
  runs, explicit `face()` in the nook, window on a slot the door doesn't claim).

## What worked / gotchas
- **A bookstore is toy_shop's lesson at full strength: the fixture IS the product.** Both the
  wall bookcase and the spine display come pre-stocked with book meshes, so the room reads
  "bookstore" with zero crowning. Browse specifically for "filled with books" and eyeball that
  the shelves are actually loaded.
- **The double-sided face-out display (`hssd/7b9c92c0…`) is the bookstore spine unit.** There is
  no double-sided *spine-out* gondola in the dataset; the face-out kids' display reads as the
  new-releases browsing spine and shows colour to both aisles. Slight children's-bookshop skew —
  acceptable; flag if the brief says "antiquarian".
- **Storefront + track lighting are renderer no-gos** (black-void + chandelier lessons): standard
  pane with the checkout staged in front, flush discs at low density instead.
- Guided-flow note: the phase-1 gate caught nothing here because the skeleton was copied from
  three converged examples — pattern reuse collapses the loop (jewelry_shop lesson, again).

## Manual constraints used
- None. Auto overlap/bounds + door clearance + `CategoryClearanceConstraint` (counter front)
  sufficed.
