# Gym — asset retrieval audit

Scene file: `scenes/gym.py`. Audited 2026-06-27. No scene edits made.
Each verdict was made by viewing the chosen asset's `preview:` PNG, not similarity alone.

| query | retriever | chosen pick (desc) | sim | verdict | fix |
|---|---|---|---|---|---|
| a treadmill exercise machine | GymEquipmentRetriever | Modern black treadmill with an LED console (`hssd/fdd91608c418ead483b7a0bbd78a82a6306f36d0`) | 0.627 | GOOD | — |
| a flat weight training bench | GymEquipmentRetriever | Sturdy black gym bench, flat design (`hssd/0391f7b149076276d028060971ae3d197619f196`) | 0.752 | GOOD | — |
| a rubber gym floor mat | FutureHSSDAssetRetriever (general) | Black gym mat, simple rectangular design (`hssd/cc45171d0d70742f0730eeeda8ebffdbf956854f`) | 0.660 | GOOD | — |
| a large exercise stability ball | GymEquipmentRetriever | Bright blue exercise ball, smooth ribbed (`future/1c463b4e-688d-4b52-8811-0c3658526ea3`) | 0.600 | GOOD | — |
| a weight rack with dumbbells | GymEquipmentRetriever | Black metal dumbbell rack, two rows of weights (`hssd/f7109eaad4235fd4db456ca184f9f458a3611421`) | 0.688 | GOOD | — |
| a large gym wall mirror | MirrorRetriever | Large rectangular wall mirror, black frame (`hssd/37df562f7e34d2635ffacf543f58422b49e1732e`) | 0.605 | GOOD | — |

Counts: **GOOD 6 / WEAK 0 / MISSING 0.**

The HIGH asset-gap risk flagged in `scenes/notes/gym.md` and NOTES.md issue #3
("treadmills... most likely to come back wrong") does **not** materialize for this
scene. The `gym_equipment` curated pool (167 ids) plus the `mirrors` pool (269 ids)
cover every query, and routing lands every gym-specific query in `GymEquipmentRetriever`.
This category was clearly already curated to remove the risk — a good outcome.

## Ingestion backlog

None. Every query returned a correct, usable asset. No glb ingestion needed for the
gym scene as written.

## Routing notes

- **5 of 6 queries route to `GymEquipmentRetriever`** (treadmill, bench, stability ball,
  dumbbell rack) — its `examples` list literally includes treadmill, weight bench, dumbbells,
  yoga mat, so embedding-router recall is reliable for these.
- **"a large gym wall mirror" → `MirrorRetriever`** (pool `mirrors.json`, 269 ids). Correct:
  the word "mirror" dominates routing, and the gym scene mounts it via
  `place_on_wall_right_center` (wall-mounted fixture), which matches a wall mirror. The chosen
  mirror is landscape/large-format, appropriate for a gym wall.
- **"a rubber gym floor mat" → general `FutureHSSDAssetRetriever`, NOT `GymEquipmentRetriever`.**
  Despite the GymEquipment examples listing "yoga mat", the router sent the floor-mat query to
  the base pool. It still returned three good black rubber mats (the base pool contains them),
  so no harm here — but it's a latent routing inconsistency: a thinner mat sub-pool or a
  differently-worded query could expose a gap. Worth noting that gym mats are NOT guaranteed
  to be inside the curated gym pool; they were recalled from the full dataset.
- The dumbbell rack is placed with `place_on_left_wall_center` (floor furniture against a wall)
  and the mirror with `place_on_wall_right_center` (mounted on the wall) — both consistent with
  the floor-vs-mounted distinction in NOTES.md issue #6.

## Lessons

1. **A curated pool neutralizes a flagged risk.** NOTES flagged gym machines as HIGH risk, but
   the pre-built `gym_equipment.json` (167 ids) made every machine query GOOD. Curation, not
   prompt engineering, is what de-risked this category — exactly the asset_selection.md thesis.
2. **Routing is keyword-dominated and mostly correct, but not pool-consistent.** "mirror"
   reliably hits `MirrorRetriever`; "gym ... mat" went to the general pool even though the gym
   pool advertises "yoga mat". When a sub-type lives in BOTH the curated pool and the base pool,
   the pick can still be good, but you can't assume the curated pool was used — verify with
   `inspect`, which prints the retriever name.
3. **Judge by preview, not similarity.** The stability ball (sim 0.600) and mirror (sim 0.605)
   are the lowest-scoring picks but are visually perfect; the bench (sim 0.752) is highest. Low
   absolute similarity within a tightly-curated pool is normal and not a quality signal.
4. **The gym pool is deep enough to spare overrides.** Each query had 5+ on-target candidates,
   so no PIN/REWORD was needed. If varying the scene seed, any of the top picks would be a safe
   manual swap.
