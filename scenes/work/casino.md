# Casino — asset retrieval audit

Scene: `scenes/casino.py`. Verdicts from inspecting each `AddAsset(...)` query and
viewing the chosen `preview:` PNG (not similarity alone).

| query | retriever | chosen pick (desc) | sim | verdict | fix |
|---|---|---|---|---|---|
| a colorful slot machine | FutureHSSDAssetRetriever | Modern IGT CrystalDual 27 gaming machine (`hssd/f06d7023a43b441a5c82402fc63b90932a749cb6`) | 0.482 | GOOD | — genuine IGT slot cabinet; correct object |
| a green felt blackjack card table | GameEquipmentRetriever | Walnut "poker table", square, on legs (`hssd/81f092c5722ae67b49104b660bcf3f0fec3c69f0`) | 0.525 | WEAK | INGEST a real green-felt card table; rest of pool is pool/foosball/hockey |
| a padded casino chair | FutureHSSDAssetRetriever | Modern black cushioned **floor chair**, legless (`future/e713f8a9-71e6-4a9e-bea2-1bec09c09ddd`) | 0.497 | WEAK | REWORD → `an upholstered dining armchair with padded seat` (validated, sim 0.66) |
| a small casino podium | FutureHSSDAssetRetriever | Modern gray podium w/ built-in microphone (`hssd/2fa15bc31819eff32a29e592b6a71011266313a3`) | 0.478 | GOOD | usable lectern; see routing note (should route to PresentationFixtureRetriever) |
| a long casino bar counter | CountersRetriever | Modern wooden bar counter, long straight flat top (`hssd/b1c9d7321512686e02f2d0be978056456479e14c`) | 0.515 | GOOD | clean long counter, against-wall placeable |
| a bright neon casino wall sign | FutureHSSDAssetRetriever | Large 'Welcome' retro wall sign, **flat black script** (`hssd/c5046dfe8edc365aa500c43bb357b0a7926dcb48`) | 0.512 | MISSING | INGEST a neon casino sign; no illuminated/neon casino sign in pool |

## Detail on the problem picks

**Blackjack table (WEAK).** GameEquipmentRetriever pool holds pool tables, foosball,
air-hockey, and one "poker table." The chosen poker table's preview is just a walnut
console-style table with a black inset top — no green felt, no recognizable casino
playing surface. It is at least a flat square top on legs, so the scene won't break, but
it does not read as a blackjack/card table. No green-felt card table exists in the pool.

**Padded chair (WEAK).** Picked a legless black floor cushion — wrong sitting height for a
card table (players would be below the table top). Reword to a dining armchair fixes both
the height and the upholstered look; validated query returned proper table-height
upholstered armchairs at sim ~0.66 (vs 0.50), chosen `hssd/cc48920ec3355dff3e8d1a26a7328884e74028e7`.

**Neon sign (MISSING).** Chosen "Welcome" sign preview is flat dark-gray cursive — not
bright, not neon, not casino. The VLM's "neon glow" justification does not match the
image. A reword to `a glowing neon sign with bright lettering` (routes to WallArtRetriever)
surfaced a "DRINK" marquee-bulb sign and a "DINER" red-panel sign — bar-adjacent but not
casino, and the DRINK piece is a freestanding tabletop sign, not wall-mounted. Pool has no
illuminated casino neon. Ingest is the real fix; interim pin is the DINER sign
(`hssd/29a27d5893f1b3383204673903f1a385588e02ef`) if a sign must be wall-mounted now.

## Ingestion backlog (glb specs)

1. **Green-felt blackjack/card table.** Semicircular casino blackjack table: green felt
   playing arc, padded leather rail, dealer side flat, dark wood/black base. Must face +Z
   (dealer side at back, players at the curved +Z front). Real-world width ~1.8 m.
2. **Neon casino wall sign.** Flat wall-mounted sign panel with bright illuminated
   neon-tube lettering (e.g. "CASINO" / "JACKPOT") on a dark backing, saturated emissive
   color. Thin depth (wall fixture). Must face +Z (lettering toward +Z). Real-world
   width ~1.2 m.
   - Optional second: vertical neon casino sign, ~0.6 m wide, for narrower wall slots.
3. *(Optional, lower priority)* **Casino dealer/host podium / pit stand** — a small
   counter-height stand styled for a casino floor, if the generic gray lectern reads too
   plain. ~0.6 m wide, faces +Z.

## Routing notes

- **Podium routes to the general FutureHSSDAssetRetriever, not PresentationFixtureRetriever.**
  asset_selection.md says podiums/lecterns belong to the curated
  `presentation_fixtures` pool. "a small casino podium" still landed in the general pool
  (it happened to find a usable lectern). The casino-specific phrasing likely defeats the
  router. Worth confirming the router keys on "podium/lectern" regardless of qualifier, or
  reword to plain `a podium` / `a lectern` so it hits the curated pool deterministically.
- **Blackjack table → GameEquipmentRetriever** is the right pool, but the pool lacks any
  card/casino table (only pool/foosball/hockey). This is a pool-content gap, not a routing
  gap — fix by ingesting into that category.
- **Bar counter → CountersRetriever** and **slot machine → general pool** both routed and
  picked correctly; no action.
- **Neon sign → general pool** on the literal query, → WallArtRetriever on a reworded
  "neon sign" query. WallArtRetriever is the correct home, but it contains only retro home
  wall signs; ingest the casino neon there.

## Lessons

1. **"casino" as a query adjective hurts more than it helps.** It is sparse in the
   dataset, so it pulls similarity down and can defeat category routing (podium, chair,
   sign). Prefer describing the *object shape* ("upholstered dining armchair", "podium")
   and reserve theming for texture/material words.
2. **Trust the preview over the VLM's prose.** The neon-sign pick was justified with
   "neon glow" that simply isn't in the image (flat black script). Always view the PNG.
3. **Seat height is a silent failure mode.** A "padded chair" can resolve to a legless
   floor cushion that's the wrong height for a table — name the seat type ("dining
   armchair") when it rings a table.
4. **Commercial casino props are dataset gaps (matches NOTES.md issue #3, HIGH risk).**
   Slot machine and bar counter are fine, but the blackjack table and neon casino sign
   have no true match — these are the prime ingestion targets for this category.
