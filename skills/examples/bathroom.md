---
id: example:bathroom
kind: example
family: set-piece-hero
category: "spa master bath"
pattern: "Set-assets + width-only scaling + overlap handling for bundled sets"
---
> **Digest (from the pattern index):** Set-assets + width-only scaling + overlap handling for bundled sets


# Bathroom (spa master bath) — worked example

Status: built as `scenes/work/bath_spa.py`. [`bathroom_v1.py`](bathroom_v1.py) is that program **phase-gated** (2026-07-13): `lint_program`-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record).

The scene that taught **asset/fixture QUALITY** — not layout — is where the work lives. Unlike the
salon (which needed ingests + a new placement group), the bathroom dataset was already rich; the hard
part was that bathroom **fixtures are "set assets" with unreliable scale metadata**. Read alongside
`../workflow/asset_selection.md` ("Set assets") and `../workflow/coarse_to_fine.md`.

## Prompt / plan
"a pretty / spa-style master bathroom." Planner (ALWAYS run it first — `idsdl__plan`) returned: white
marble **grounded with warm wood + brass**, freestanding oval tub under a window as the hero with a
**statement brass chandelier**, walk-in glass shower, **warm-wood double vanity** with brass mirror,
ferns/eucalyptus + candles + plush towels. Skipping the planner gives a generic 3-piece bath.

## Asset kickoff finding: rich library, so the work was fixtures not ingests
Catalogued the category (browse): tubs, glass showers, double vanities, brass mirrors, toilets,
linen towers, towel ladders, plants, candles, botanical art — **all abundant**. So: **no ingests, no
new pool needed** for coverage (user confirmed via gallery). The asset-first payoff here was the
*finding* "we can move straight to placements," then everything below.

## Layout (coarse-to-fine, long strips on long walls)
Two heroes (tub, vanity) face each other on the two LONG walls (each gets a generous wall); shower +
toilet take the SHORT walls. Tub under a window on the back wall, brass chandelier over it.

## The fixture lessons (the actual content) — see `set-assets-and-scaling` memory
1. **Scale metadata is broken for bathroom fixtures** — a pinned tub resolved to **0.2 m long**. Fix
   by enforcing real size, but **scale UNIFORMLY by width** (`_fit_width`: set width, scale all axes
   by one factor) so the mesh keeps its proportions. NEVER scale axes independently (distorts
   sinks/drawers). `obj.scale(w)` is buggy on pre-scaled assets — use a captured-whd factor.
2. **"Set assets": vanities & toilets are bundled COMPLETE SETS**, retrieved + placed as ONE unit:
   - **Vanity** bundles its **own wall mirror** (mesh spans cabinet→sink→mirror, ~1.6 m tall) → do
     NOT add separate mirrors (they overlap it). Also **don't `place_on_top` a vanity** (complex top;
     decor sits unreliably) — instead retrieve a vanity variant that already bundles decor.
     Type-tagged (`tools/build_vanity_tagger.py` → `vanity_types.json`): floating/single/double/
     extra_wide → real width + floor-vs-wall mount, applied TRANSPARENTLY inside `AddAsset`
     (`SceneProgRoom._apply_vanity_metadata`) — the program just `AddAsset`s a vanity and places it
     (no import/helper; `place_on_*_wall_*` auto-reads `obj.mount_bottom`).
   - **Toilet** bundles cistern + flush buttons + TP holder + brush; uniform in size, so **one
     consistent scale** (we used ~1.5× the metadata width) and **no per-asset tagging**. Curated
     pool `bathroom_toilet_set.json` + `BathroomToiletSetRetriever` (registered; removed "toilet"
     from the generic bathroom retriever so it routes there).
3. **`bottom=` wall-mount** — added to all 12 `place_on_*_wall_*` methods so floating vanities /
   wall-hung units sit at a mounted height instead of floor-aligning.
4. **Rugs must be modelled FLAT** (thin in height). Many "bath mat" picks are authored UPRIGHT (thin
   in depth); `place_rug` scales width+depth and the upright height survives as a giant slab — and
   the export is yaw-only so it can't be tilted down. `place_rug(desc, size, asset_id=)` now pins a
   verified-flat rug + warns when the chosen rug isn't flat.
5. **`WallOverlapConstraint` now checks ACTUAL geometry** (`check_geometric_overlap`, 5 mm margin),
   not just slot buckets — it caught a wall mirror/art interpenetrating the toilet that the slot
   check (counts >1 per wall/slot) silently missed.

## Palette gotcha
An all-white-marble room **blows out to white** under window daylight (every surface high-albedo).
Fix = a **saturated mid-tone wall** (we used soft sage — also the brief's accent) + grey marble
floor, exactly the salon's blush-walls trick. Pull `modulate_scale` down so the room isn't a bright
empty box.

## Status / open
Working scene `scenes/work/bath_spa.py` (seed=21). Full rebuild 2026-07-13 closed the two old
open items:
- **The back-wall window now renders as a bright curtained pane** — the black-void limitation
  was fixed in the renderer (greenhouse, 2026-07-12); the workaround note is retired.
- **"Reads a touch tight" is the DESIGN, and the build agrees it's at the edge:** the rebuild
  voted `rescale 1.1` and warned two floor overlaps — but both are the corner palm/towel
  ladder standing 0.14 m onto the edge of the tub group's FLAT BATH MAT (the benign flat-rug
  AABB class; nothing interpenetrates in the render). `modulate_scale=0.72` stays: a spa bath
  must feel enclosed. Read past exactly these two warnings; if the room is ever re-iterated,
  1.1 is the first knob.

## Program

[`bathroom_v1.py`](bathroom_v1.py) — phase 1 the tub + vanity heroes, toilet, floor anchors, walls and door; phase 2 the tub caddy, candles and fern, bath mat, palm and towel ladder; phase 3 the brass drum chandelier, botanical print and window.

`workbench run skills/examples/bathroom_v1.py --phase 1` builds the layout alone in ~1–2 min.
