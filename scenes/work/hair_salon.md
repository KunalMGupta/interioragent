# Asset-retrieval audit — hair_salon

Scene: `scenes/hair_salon.py`. Method: one `workbench.py inspect` per query, chosen
pick judged by its `preview:` PNG (not similarity alone). Scene file NOT edited.

| query | retriever | chosen pick (desc) | sim | verdict | fix |
|---|---|---|---|---|---|
| a salon styling chair | FutureHSSDAssetRetriever | Korean-style dressing chair, white upholstered, plain legs (`future/8532900d-80b9-4b80-b225-386ff5e34484`) | 0.524 | MISSING | INGEST a styling chair (no pedestal-base salon chair in pool; reword to "barber chair…" only returns office/massage chairs) |
| a salon hair washing basin chair | FutureHSSDAssetRetriever | chrome console washstand with ceramic basin, no chair (`hssd/611fc9b02118a2cfa0ce1b83b723062a4e6de291`) | 0.437 | MISSING | INGEST a salon backwash unit (recline chair + shampoo bowl); dataset has only a bare basin or a medical exam chair, never the combined unit |
| a modern salon reception desk | CountersRetriever | plain light-wood office desk/table, flat top on metal legs (`hssd/3a6b88510159019ae1f7326acb83ce317fa44caa`) | 0.469 | WEAK | PIN `hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860` — a real curved reception desk, top-ranked (0.674) but rejected by the picker |
| a salon product display shelf | FutureHSSDAssetRetriever | wall-mounted floating bracket shelves w/ decor props (`future/f0edc500-f5a7-4d22-bdb3-d474e94329eb`) | 0.515 | WEAK | PIN `hssd/dec28234dd4886042b5b1a3563cbb942471692cd` — freestanding retail display unit with compartments; floor-standing, suits `place_on_right_wall_center` |
| a large salon wall mirror | MirrorRetriever | elegant large ornate-framed wall mirror (`hssd/48d67a6b6d88964f83f687c253d1177b17a0359b`) | 0.667 | GOOD | — (requested twice; both placements draw from same good pool) |

## Ingestion backlog

1. **Salon styling chair** — a professional salon/barber styling chair: upholstered
   seat + backrest on a single central hydraulic pedestal base (round chrome
   footplate), with a footrest, optionally a headrest. Look: black/leatherette modern
   barber chair. Must face +Z (front of seat toward +Z). Width ≈ 0.65 m.
   - Stopgap until ingested: pin the massage recliner `hssd/feb130d3499f00724fa2263e3552d1c70dac6582` (closest silhouette in pool; a reclining lounge chair, not ideal but reads as a treatment chair better than a dining chair).

2. **Salon backwash / shampoo unit** — a reclining shampoo chair joined to a ceramic
   wash basin with a neck rest at the back; the chair faces away from the bowl so the
   client lies back into it. Look: white/grey salon backwash station, chrome fittings.
   Must face +Z (the seated client faces +Z; bowl at the −Z/back end). Width ≈ 0.75 m.
   - Stopgap: none clean. The current pick is a standalone basin on legs (no chair); the medical exam chair `future/e6e2fcd9-...` is a chair with no basin. Neither is right — this one really needs ingestion.

## Routing notes

- **CountersRetriever (reception desk)** holds the correct curved reception desk
  (`7379d8...`, sim 0.674, top-ranked) but the visual picker dropped it for a plain
  flat-top office desk. Per `asset_selection.md`, "reception" is an **explicit
  exception** to the no-raised-second-surface rule — the picker isn't honoring it for
  this query. Either pin the id, or extend the `visual_llm` exception handling so a
  query literally naming "reception" keeps the raised-counter desk. Pool is fine; this
  is a picker-prompt gap, not a recall gap.
- **MirrorRetriever** pool is healthy — multiple large wall mirrors, top pick correct.
  No action.
- **Chairs route to the general FutureHSSDAssetRetriever**, whose pool has no salon /
  barber styling chair and no backwash unit. Rewording ("barber chair with hydraulic
  base and headrest") did not surface one — confirmed recall gap, not a phrasing gap.
  Fix is ingestion, not routing. (Matches NOTES.md issue #3: salon fixtures are
  commercial props the home-furniture-biased dataset lacks.)
- **Product display shelf** routes to the general retriever and returns a *wall-mounted*
  floating shelf, but the scene places it as floor furniture against a wall
  (`place_on_right_wall_center`) — a bracket shelf would appear to float. A freestanding
  display unit (`dec28234…`) exists in the shortlist and is the right placement class.

## Lessons

1. Salon-specific seating (styling chairs, backwash units) is absent from the dataset;
   queries fall back to dining/office/massage/medical chairs. Treat as ingestion
   targets up front rather than expecting a reword to rescue them.
2. The picker can reject a perfectly-named, top-ranked asset (the curved reception
   desk) by over-applying the "no raised second surface" desk rule — even though
   "reception" is a documented exception. Always view the **#1** preview, not just the
   chosen one; a PIN is often one rank away.
3. Match the asset's mounting class to the placement verb: a floating/wall-mounted
   shelf picked for a `place_on_*_wall_*` (floor-against-wall) slot will float. Prefer
   freestanding units for floor placements.
4. Similarity is a weak signal here: the GOOD mirror (0.667) and the WEAK office desk
   (0.469) sit far apart, but the WEAK floating shelf (0.515) and a correct freestanding
   unit (0.539) are nearly tied — recall ordering didn't decide correctness; the preview did.

---

# Pool curation analysis (from your selection.json — 186 kept of 493)

Method: re-ran each of the 79 candidate prompts (top-8) and intersected with your kept
set; then clustered the 186 kept assets by description and spot-checked previews.

## Well covered by the curated pool (NO ingestion needed)
- **Mirrors** (33): wall / floor / ornate / full-length — strong.
- **Styling stations**: dressing tables with mirror + drawers (e.g. `future/876a92e6…`) — good stand-in (wall-mount, chair in front).
- **Stools**: dressing-table stools, adjustable swivel stools.
- **Tool trolleys / carts** (9+): multi-drawer metal trolleys, tool chests on wheels.
- **Reception**: a real curved reception desk `hssd/7379d8877fb6…` (confirmed).
- **Retail display**: glass display cabinets, tiered shelves, wall bookcases.
- **Checkout**: touchscreen POS + digital kiosk stand + rolling counter.
- **Waiting**: 2-seat sofas, lounge armchairs, a wooden bench; magazine racks; coffee/side tables.
- **Support**: storage/display cabinets, towel trolleys (bath dressers/mesh racks), mini fridges, coat racks, plants/vases, chandeliers/pendants, framed art / gallery sets, wall clocks, trash bins.

## TRUE GAPS — additional assets required (ingestion backlog)
1. **Barber / salon styling chair** — *HIGH (defining object)*. Dataset has only recliners/
   dressing/swivel/office chairs (e.g. `hssd/433dc0e4…` is a bulky cinema recliner). Need: an
   upholstered seat+back on a single **chrome hydraulic pedestal** with a chrome footrest ring.
   Face +Z. Width ~0.65 m.
2. **Backwash / shampoo unit** — *HIGH*. Only standalone bathroom basins/pedestal sinks kept;
   no integrated wash chair. Need: a reclining shampoo chair joined to a **ceramic neck-rest
   basin** behind the headrest. Client reclines toward +Z, bowl at −Z. White/grey + chrome.
   Width ~0.75 m, depth ~1.2 m.
3. **Hooded / bonnet dryer** — *MED–HIGH*. Completely absent (only a hooded bathrobe false-
   matched). Need: a standing salon **hood dryer** — chair/pedestal with a large dome hood over
   the head, chrome stem + base. Face +Z. Width ~0.6 m. (Optional: a rollerball/infrared
   processor on a stand.)
4. **Salon signage** — *MED (decor)*. Only a generic "Welcome" script sign exists. Need a
   **neon/illuminated salon sign** and/or a wall-mounted **price/service menu board** (thin
   wall panel, faces +Z, width ~1.0–1.2 m). Cross-category: casino needs neon signage too.

## Net
Curated pool of 186 covers ~85% of a believable salon. The 3 functional gaps (barber chair,
backwash unit, hood dryer) are the iconic salon equipment and the dataset genuinely lacks them
→ they must be ingested as user-supplied .glb. Signage is a softer, cross-category gap.
