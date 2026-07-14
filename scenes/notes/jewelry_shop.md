# Jewelry shop — scene note

**File:** `scenes/jewelry_shop.py` (seed 42) · **Status:** DONE (2026-07-09); VLM-clean at v1 but
**user-corrected** → v2 is the shipped version. Full recipe: `skills/examples/jewelry_shop.md`.

**Pattern:** visible-jewelry display tables + calm vitrine backdrop + consultation cash-wrap. A
cousin of `retail_store` (shop = central piece + perimeter loop + branded service wall).

**Kickoff:** retrieval stress test — 34 jewelry queries, **zero hard gaps**. No ingest. Plus a v2
**prop scan** for literal jewelry (rings/gems/stands).

**Heroes:**
- **Visible jewelry props** massed at viewing height (the identity): gold hand-stand
  (`hssd/20cb1bd8…`), geode (`hssd/3ae595cd…`), agate-on-gold-stand (`hssd/e8540f75…`), glass cloche
  (`hssd/77989676…`), display bust (`hssd/9eed1f0f…`), jewelry boxes (`future/09f5f6ca…`, halved).
- **Display-table island** (`hssd/e7b5486…`, reused) — the hero surface; cash-wrap **counter**
  (`hssd/7379d88…`) + POS + sapphire **stools** (`hssd/670c0ca…`); **emerald armchair**
  (`hssd/1672e0bc…`, pinned for palette); **glass vitrine ×4** (`hssd/80bfb…`) as backdrop only.

**The big lesson (learned over 2 rounds):**
1. **A shop reads by its PRODUCT at viewing height, not its fixtures.** v1 massed EMPTY glass
   vitrines (×6) → read as furniture showroom + congested; VLM went clean and I shipped it, then
   the **user** flagged "too congested / no visible jewelry." v2: mass real jewelry props on
   tables/counter/pedestals + cut vitrines 6→4 + up-scale 0.8→0.9.
2. **The VLM loop verifies geometry, not category legibility or crowding** — human gut-check a retail
   scene before declaring done. Run a second PROP scan (the furniture stress test misses product).
3. **Pool-routing reword:** "display counter" → bar counters; jewelry showcase = glass "display
   cabinet" (`CabinetandShelfRetriever`).
4. **Pin for palette:** the unpinned armchair flipped **pink → emerald across runs at a fixed seed**.
5. **Lighting:** medium room, `density=0.1` over-tiled → 0.06. Resisted the crystal chandelier.
