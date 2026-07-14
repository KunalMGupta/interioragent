# Asset retrieval audit — operating_room

Scene: `scenes/operating_room.py` (6 retrieved assets). Verdicts from inspecting each
query and **viewing the chosen preview PNG**, not similarity alone.

| query | retriever | chosen pick (desc) | sim | verdict | fix |
|---|---|---|---|---|---|
| a surgical operating table | FutureHSSDAssetRetriever | Modern composition medical examination table (`future/51434359-427d-4f35-b2f2-f2ad9b875b2e`) | 0.50 | GOOD | — narrow padded top on a central pedestal/mobile base; reads as a real procedure table |
| an anesthesia machine cart | FutureHSSDAssetRetriever | Metal hospital bed w/ blue mattress (`future/280e7e5e-...`) — only 1 candidate, text fallback | 0.40 | MISSING | REWORD to "a tall medical equipment trolley with drawers on wheels" → returns a 6-drawer steel trolley (`hssd/b00f7a0bea75c3a7834d0c4397945c2bbe6e6381`), a usable stopgap. True anesthesia machine absent → INGEST. |
| a surgical instrument cart | FutureHSSDAssetRetriever | White iron rolling cart w/ tray shelves on wheels (`hssd/491b7091a828edecf83eaa865059e3a680d0d728`) | 0.46 | GOOD | — clean 3-tier rolling tray cart; correct form for an OR instrument/Mayo cart |
| a stainless steel surgical supply cabinet | CabinetandShelfRetriever | Black wood-accent display cabinet w/ books & vases (`future/f1affa24-...`) | 0.41 | WEAK | PIN `hssd/3a2fd60fc421b402f4bfd365fd2a7accfa6ce4b1` (tall gray metal 2-door glass-front cabinet — reads as a glass medical cabinet). Reword "tall gray metal storage cabinet with glass doors" lifts sim to ~0.73 but picker drifts to a wood-textured unit, so PIN is more reliable. |
| a stainless steel scrub sink station | BathroomVanityUnitRetriever | White wall-mounted vanity w/ sink + mirror (`future/fceb092a-...`) — only 1 candidate, text fallback | 0.43 | WEAK | PIN `hssd/f06b92490816c0ae1d22b0e979718e475b8903a0` (freestanding gray/steel utility sink on legs w/ faucet). Reword to "freestanding stainless steel utility sink with faucet" mis-routes to BathroomFurnitureAndMiscellaneous → all bathtubs (worse), so REWORD rejected; use PIN. |
| a wall-mounted surgical vitals monitor | PresentationFixtureRetriever | (zero candidates — empty pool, text fallback returned nothing) | — | WEAK | REWORD to "a wall-mounted flat screen display monitor" → PresentationFixtureRetriever now returns slim wall flat-screens (`hssd/52676f400fb7e2b9181f70a0fa1f53eb686a05b4`). A generic display, not a clinical vitals monitor, but usable. |

Counts: **GOOD 2, WEAK 3, MISSING 1.**

## Ingestion backlog

- **Anesthesia machine** — tall mobile cart: rectangular column with a top-mounted ventilator
  display/monitor, gas flowmeter tubes, a vaporizer block, and several small drawers, all on
  a wheeled base; mostly white/grey clinical plastic. Must face **+Z** (display/controls
  front). Real-world width ~**0.7 m**.
  - (Optional companion, only WEAK today) A true **patient vitals monitor**: a small wall- or
    arm-mounted screen showing ECG/SpO2 waveforms with a clinical bezel and side buttons,
    facing **+Z**, width ~**0.35 m**. Current fix uses a generic flat-screen TV instead.

## Routing notes

- **"a stainless steel scrub sink station" → BathroomVanityUnitRetriever** returned a single
  domestic wall-mounted vanity (with mirror), and the reworded "utility sink" variant
  re-routed to **BathroomFurnitureAndMiscellaneousRetriever** which returned only bathtubs.
  A freestanding clinical utility sink *does* exist in the base pool
  (`hssd/f06b92490816c0ae1d22b0e979718e475b8903a0`) but neither sink-pool surfaces it. Correct
  fix is to PIN it; longer-term CURATE a sink/wash-station entry into a fixtures pool.
- **"a wall-mounted surgical vitals monitor" → PresentationFixtureRetriever returned ZERO
  candidates.** That pool is documented to contain wall TVs/displays, but the clinical wording
  ("surgical vitals monitor") has no embedding recall against it. Rewording to "wall-mounted
  flat screen display monitor" makes the same retriever return good flat-screens — so the
  retriever is right, the *query wording* was the failure.
- The first three queries all route to the generic **FutureHSSDAssetRetriever** (no medical
  category pool exists). The two best stopgaps (medical trolley, instrument cart) are only
  reachable there.

## Lessons

1. **Clinical jargon kills embedding recall.** "anesthesia machine", "scrub sink station",
   "surgical vitals monitor" each returned ≤1 candidate (text fallback). Rewording to the
   asset's *generic furniture form* ("medical equipment trolley with drawers", "flat screen
   display monitor") restored full, well-ranked shortlists. Describe the shape, not the
   medical function.
2. **A populated, correctly-routed pool can still return nothing** if the query embeds far
   from every pool item (the vitals-monitor case). When `inspect` shows 0–1 candidates +
   "text fallback", suspect a wording/recall gap before assuming the object is absent — a
   `browse` of generic terms quickly distinguishes the two.
3. **PIN beats REWORD when rewording re-routes to a worse pool.** The scrub-sink reword
   jumped retrievers (vanity → bathtubs). When `browse` already shows a confirmed good id,
   pin it directly rather than chasing a query that the router may bounce elsewhere.
4. **Medical carts/cabinets read fine as their generic cousins.** Rolling tray carts pass as
   instrument carts and gray glass-door metal cabinets pass as supply cabinets — but machines
   with integrated electronics (anesthesia unit, true vitals monitor) have no analog and must
   be ingested.
5. **Confirm "exam vs operating table" by eye, not description.** The chosen table is
   *described* as an examination table yet its pedestal/mobile base makes it a credible
   operating table — the visual picker's preview check is what salvaged it.
