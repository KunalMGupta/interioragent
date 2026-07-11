# Retail store — worked example (apparel boutique, "central rail spine + branded service wall")

A modern apparel/clothing boutique. Its defining moves: a **central merchandising spine** —
two double-sided garment rails flanking a low display table down the middle of the floor —
plus **perimeter merchandising** on the side walls (wall shelf + shoe display + a framed rack
+ a fitting mirror), a **branded service wall** at the back (checkout/cash-wrap under a store
sign), and a **front-window mannequin display**. Varied display heights (floor mannequins,
mid-height rails, low table) build depth. Reach for this for "a store / shop / boutique /
retail / showroom". Read alongside `../workflow/asset_selection.md` (this scene began with a
retrieval **stress test**) and `../workflow/vlm_feedback.md`.

## Prompt(s) this covers
- "a retail store", "a clothing / apparel store", "a boutique", "a shop", "a showroom".

## Plan summary
Planner → **"Branded Focal Wall with Layered Boutique Flow"**: a branded back wall as the
backbone with the cash-wrap in front (back-of-house service zone); a central circulation
spine framed by parallel double-sided rails preserving open sightlines; perimeter
merchandising for an outer loop; a front-window mannequin focal point; layered directional
light. Palette: warm-gray/greige walls, concrete floor, matte-black metal fixtures + warm
wood tops, clothing colour as the accent.

## Retrieval stress test FIRST (this scene's kickoff — do it for any new category)
Before pinning anything, sweep the whole asset vocabulary for **availability** so you know
the dataset can carry the scene. Cheap because it's embedding-only (no VLM pick):
```python
from IDSDL.service import core as svc
for q in QUERIES:                       # ~30 brainstormed category items
    m = svc.browse(q, n=3)["manifest"]  # whole-dataset cosine, fast (~1s each)
    print(q, m[0]["similarity"], m[0]["desc"])   # flag top-1 < 0.30 as a GAP
```
Result for retail: **zero hard gaps** — every one of 34 queries had a ≥0.39 top-1. Strong
(>0.55): garment rails, wall shelving, shoe shelves, mannequins, mirrors, track spots,
folded-clothes stacks, display tables, glass showcases, plants. **Soft spots that a
substitute covers (no ingest):** checkout counter (0.47 → returns **reception desks**; a
reception/service counter reads as a cash-wrap); "cash register" (0.40 → weak wording, but
the **POS touchscreen** mesh exists — query "point of sale terminal", 0.59); "store sign"
(0.49 → a neon/"Welcome" sign, on-brand); "shopping basket" (0.50, minor). Then verify the
**visual** pick + pin durable ids for the true heroes with `retrieve` (the stress test is
availability only; embedding recall ≠ a good mesh).

## Pinned assets (asset-first kickoff)
- **Double-sided rail (spine)** `future/a419b5a4-4bfe-4e04-a3f3-7c7e3e9fcd17` — the VLM's #1
  for "clothing rail" is often a coat *valet*; this true two-arm freestanding rack is #4.
- **Framed boutique rack (perimeter)** `future/a3e8bf5a-c3dd-4211-bdda-483818d9d354`.
- **Wall merch shelf** `hssd/76ae9b47590b35c68e8ab908e4641d523f083b0c` (folded-on-top + hanging-below).
- **Shoe shelf** `hssd/e9597e32600022ebbae20264d1fed4b7d6b89b37`.
- **Checkout counter** `hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860` (curved wood-front reception/cash-wrap).
- **Mannequin** `hssd/852f2364cdc28fde3b302da61a8d2e09d3d18a15` (full-body standing; scale 0.5 = human height).
- **Display table** `hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f` (wood top + black metal frame — on-brand).
- **Folded sweaters** `future/c17aa2e4-30f4-482a-badc-1c04309e487b` (on-top prop).
- **Glass showcase** `hssd/be0ea104f86eedb2424627de3e52a32af8d19c02` (oak/glass accessory cabinet).

## Skeleton program
```python
scene = SceneProgRoom("RetailStore", seed=42)

with scene.RelativeGroup() as checkout:                       # cash-wrap + POS + bags on top
    checkout.set_anchor(scene.AddAsset("a retail checkout counter service desk", asset_id=COUNTER))
    checkout.place_on_top([scene.AddAsset("a point of sale touchscreen terminal"),
                           scene.AddAsset("a paper retail shopping bag")])

with scene.RelativeGroup() as table:                          # spine centrepiece + rug
    table.set_anchor(scene.AddAsset("a low wooden display table with a black metal frame", asset_id=DISPLAY_TABLE))
    table.place_on_top([scene.AddAsset("a stack of folded sweaters", asset_id=FOLDED),
                        scene.AddAsset("a stack of folded shirts in muted colours")])
    table.place_rug("a large flat neutral wool area rug", size=0.9)

with scene.RoomGroup(modulate_scale=0.9, randomness=0.1) as room:   # 0.9 acts on 'rescale 0.9' + tightens empty floor
    room.place_walls(floor_texture="polished concrete floor", ceiling_texture="white", wall_texture="warm light greige")
    # service wall
    room.place_on_back_wall_center(checkout, facing="front")
    room.place_on_back_wall_left(scene.AddAsset("an oak and glass display showcase cabinet", asset_id=SHOWCASE), facing="front")
    # central spine: two double-sided rails (facing="left" runs them front-back) framing the table
    room.place_on_left(scene.AddAsset("a double-sided clothing rail", asset_id=SPINE_RAIL), facing="left")
    room.place_on_center(table)
    room.place_on_right(scene.AddAsset("a double-sided clothing rail", asset_id=SPINE_RAIL), facing="left")
    # front-window display: three mannequins
    for slot in (room.place_on_front_left, room.place_on_front, room.place_on_front_right):
        slot(scene.AddAsset("a full-body standing clothing mannequin", asset_id=MANNEQUIN), facing="front")
    room.place_on_back_right_corner(scene.AddAsset("a large potted indoor plant"))
    # perimeter merch (wall-hung shelves: bottom= sets mount height)
    room.place_on_left_wall_center(scene.AddAsset("a wall retail shelf with folded clothes and a hanging rod", asset_id=WALL_MERCH), facing="right", bottom=0.4)
    room.place_on_left_wall_left(scene.AddAsset("a wall shoe display shelf", asset_id=SHOE_SHELF), facing="right", bottom=0.4)
    room.place_on_right_wall_center(scene.AddAsset("a black-framed boutique clothing rack", asset_id=FRAMED_RACK), facing="left")
    room.place_on_right_wall_right(scene.AddAsset("a full-length freestanding floor mirror"), facing="left")
    room.place_on_wall_back_center(scene.AddAsset("a neon store brand sign with glowing tube lettering"))
    room.add_lighting("a flat round LED flush mount ceiling light", density=0.08)   # LOW — a big floor tiles many
    room.place_window_standard("front_wall", position="center")   # NOT floor-to-ceiling (wall-sized void)
    room.place_door("right_wall", position="right")
scene.export("retail_store.blend")
```

## What worked / gotchas
- **Central-spine layout on the RoomGroup 5×5 grid.** Two double-sided rails at `place_on_left`
  / `place_on_right` with **`facing="left"`** (rotates each long rail to run front-to-back so
  they're parallel and frame the aisle), a display table at `place_on_center` between them, and
  the three window mannequins across the front row. This is the reusable "merchandising band
  across the middle + perimeter loop" recipe for any shop/showroom.
- **LIGHTING density scales with FLOOR AREA, not just the count knob.** `density=0.3` — fine in a
  small office — tiled **~40 flush discs into a dense ceiling grid** on this large retail floor.
  Dropped to **0.08** for a clean ~5. Rule: `add_lighting` density is a fixture *count*, and the
  count grows with room footprint, so a **big room wants density ~0.05–0.1**. (Still a FLUSH
  fixture, never a chandelier/track rig — see `executive_office.md`.)
- **A storefront window is the WORST case of the black-void limit.** `place_window_floor_to_ceiling`
  on the front wall rendered a **wall-sized pure-black void** (no exterior env). Switched to
  `place_window_standard(..., position="center")` — a modest pane — and staged the **mannequins in
  front of it as the window display**; now it reads as an evening storefront. For retail, never
  full-height-glaze the front wall; use a standard pane + a mannequin foreground.
- **Checkout counter = a reception/service desk.** The dataset has no purpose-built cash-wrap, but
  the `CountersRetriever` returns curved reception desks + bar counters; the curved wood-front
  reception desk reads perfectly as a boutique cash-wrap (put the POS + bags on top).
- **`run_scene` mtime-fallback trap.** `mcp__idsdl__run_scene` reports whichever `report.json` is
  newest by mtime across **all** `tmp/*` dirs, so if your build **errors before writing its report**
  (or another run finished more recently) it surfaces a *different scene's* renders — I got a full
  **garage** back for a retail program. Tell by the printed **asset list**; when it doesn't match
  your program, re-run directly (`python workbench.py run <prog>`) to see the true build/error.

## VLM feedback we hit and how we resolved it
- render 1: storefront black void + ~40-disc ceiling grid → `place_window_standard` + density 0.08.
- render 2: `rescale room by 0.9` (one vote; floor visibly empty) → applied `modulate_scale=0.9`.
  `rotate checkout counter / POS to face customer` → **declined** (ambiguous: a back-wall cash-wrap
  facing into the store already faces approaching customers).
- render 3: `no rescale / no rotation / no wall overlap` everywhere → **converged**, stopped.

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed. (`bottom=0.4` on the two left-wall shelves is
  a mount-height arg, not a constraint.)
