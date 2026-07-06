# Warehouse

- **Status:** BUILT & VLM-clean, **v2 with ingested gear** — `scenes/work/warehouse.py` (seed=31). Full
  worked recipe in `skills/examples/warehouse.md`.
- **Pattern:** the racking IS the structure. Two loaded rack WALLS (each a butted `GridGroup.place_row`
  of racks) on the room's BACK and CENTER thirds → the room's own thirds give a WIDE forklift aisle
  between them. Back wall faces FRONT + center wall faces BACK, so BOTH loaded faces flank that one
  aisle = a proper double-loaded aisle. The open FRONT third = a working loading DOCK: a **forklift**
  (hero, front-left) flanked by traffic cones, a staged row of crates/boxes + a parked pallet jack, a
  packing bench with a gas cylinder. Roller-shutter dock door + green EXIT sign on the front wall;
  personnel door on the right wall; a rusty factory boiler + tanks in the back-right corner.
- **Hero assets:** loaded industrial rack `hssd/44935cd7…` (best "pallet rack" in the set), workbench
  `hssd/81ad56ba…`, boxes `hssd/71e625e1…`. **Ingested custom gear** (see
  [[ingested-warehouse-office-assets]]): forklift `custom/96aaadef…`, pallet jack `custom/ac9be2e8…`,
  traffic cone `custom/3d013e88…`, roller shutter `custom/77209bcb…`, exit sign `custom/e750dc69…`, gas
  cylinder `custom/ebe6d0a7…`, wooden crate `custom/eb9d3e7b…`, factory tanks `custom/58ad2b42…`.
- **-Z-front gotcha (custom vehicles):** the ingested forklift/pallet-jack GLBs have their front on -Z,
  so `facing` reads flipped. Place the forklift facing `"front"` (not "back"); park the pallet jack in a
  `GridGroup` row (rotation 0 = correct) rather than a facing-based slot. VLM "rotate X by 180" catches it.
- **Aisle layout gotcha:** `place_grid`'s inter-row gap is capped at `sparsity·depth` (~0.6 m for
  shallow racks) — too tight for a forklift aisle. Build each rack row as a butted `place_row` line and
  place the lines in distinct RoomGroup slots so the room's thirds supply the wide aisle.
- **Lighting:** `add_lighting(..., modulate_scale=)` is the fixture-SIZE lever. Over a big/high ceiling
  tiny fixtures read as a starfield of dots; scale them ~2.4× at low density (0.02) → visible linear
  high-bays. (Extends the bar SINGULAR-query lesson.)
- **`place_on_top` gotcha:** DON'T place boxes on a flat PALLET — `_fit_on_top` sizes the box to the
  pallet's near-zero thickness and it vanishes. Use floor box-stacks (the asset already reads as stacked
  cardboard), or a thick anchor (the workbench packing station works fine — real height).
- **Asset-gap risk:** HIGH (home-furniture dataset). Accepted compromises: rack's baked load renders
  cyan/teal (complete-mesh → can't recolor); NO forklift (only toy trucks); NO real signage (a "hazard
  sign" query returned a pirate skull-and-crossbones flag). Follow-up = ingest a forklift + black pallet
  rack GLB if a stricter look is wanted.
- **Scale/jitter:** RoomGroup modulate_scale 0.85 (proportion signal oscillated 1.0→0.7→1.2; settle
  mid, render is arbiter), randomness 0.05, max_height 5.0; rack rows sparsity 0.05.
