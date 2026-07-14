# Laundromat — asset retrieval audit

Scene: `scenes/laundromat.py`. Inspected each `AddAsset(...)` query with `workbench.py
inspect`, viewed the chosen pick's preview PNG, and judged the depiction (not just score).

| query | retriever | chosen pick (desc) | sim | verdict | fix |
|---|---|---|---|---|---|
| a front-load washing machine | ApplianceRetriever | future/3948…d054 — modern white front-load washer, circular door + control panel | 0.71 | GOOD | — |
| a commercial clothes dryer | ApplianceRetriever | hssd/c2c1…2888 — white tumble dryer, solid (non-window) door, front controls | 0.49 | WEAK | REWORD → "a white tumble dryer" (still domestic); pool has no commercial glass-door dryer. Cosmetic; accept or INGEST a commercial bank dryer. |
| a molded plastic waiting chair | FutureHSSDAssetRetriever | hssd/f8ab…9bb6 — "modern fuscia pink plastic chair" (reads as a smooth molded blob/stool, no clear seat+back) | 0.57 | WEAK | REWORD → "a stackable plastic side chair with four legs" (validated: improved). |
| a long laundry folding table | CaseGoodsRetriever | hssd/84c6…01af — extendable rectangular dining table, turned legs, wood top | 0.41 | WEAK | REWORD → "a long rectangular work table with a plain flat top" (validated: big improvement — returns a metal folding worktable). |
| a tall snack vending machine | ApplianceRetriever | hssd/595c…1350 — tall red/white Coca-Cola glass-front vending machine | 0.53 | GOOD | — (beverage, not snack/spiral; thin 2-candidate pool but reads correctly as a vending machine) |
| a framed laundry instructions sign | WallArtRetriever | hssd/b15f…49a9 — framed vintage "LAUNDRY ROOM" sign | 0.67 | GOOD | — |

Verdict counts: **GOOD 3, WEAK 3, MISSING 0.**

## Validated rewords (run as the single extra inspect each)
- **waiting chair:** `"a stackable plastic side chair with four legs"` → pool flips from
  random plastic furniture to real stacking chairs (sim 0.58–0.64); chosen = clean white
  stacking plastic chair (hssd/978c…f13f). An Eames-DSR molded chair (hssd/ac30…23fa) is
  also in the shortlist and is the most "waiting-room" of the set — good PIN candidate.
- **folding table:** `"a long rectangular work table with a plain flat top"` → routes to
  the general retriever and returns metal/stainless worktables; chosen = a long metal
  **folding worktable with folding legs** (hssd/3298…5145, sim 0.61). Exactly a laundry
  folding table. Strong improvement over the dining table.

## Ingestion backlog
None strictly MISSING — every query has a usable pick after reword. Optional quality-only
ingest (cosmetic, not required):
- **Commercial laundromat dryer.** Object: free-standing commercial tumble dryer. Look:
  white/stainless body, large round glass window door (matches the washer bank style),
  digital/coin control panel on top. Facing +Z (door front). Width ~0.7 m.
- **Snack vending machine (spiral-coil).** Object: tall snack vending machine. Look: tall
  black/grey cabinet, large glass front showing spiral snack coils, keypad + delivery bin
  at bottom. Facing +Z (glass front). Width ~0.9 m. (Current pick is a beverage cooler.)

## Routing notes
- **"a long laundry folding table" → CaseGoodsRetriever** returned only 2 decorative dining
  tables (sim ~0.41). The correct asset (a metal folding worktable) lives in the **general
  FutureHSSDAssetRetriever** pool and is only reached by rewording to a "work table"
  phrasing. Either reword in the scene, or add folding/utility worktables to the casegoods
  pool / a fixtures pool so "folding table" routes correctly.
- **"a molded plastic waiting chair" → FutureHSSDAssetRetriever** matched on "molded
  plastic" and surfaced a non-chair blob form. The chair vocabulary ("stackable side
  chair") recalls far better in the same pool — recall problem, not a pool gap.

## Lessons
1. **Utilitarian/commercial terms are pool poison.** "laundry folding table", "commercial
   dryer", "snack vending" all under-recall against a home-furniture dataset. Describe the
   generic shape ("rectangular work table, plain flat top"; "tumble dryer") and let the
   commercial flavor go — recall and routing both improve.
2. **"molded plastic" matched material over form** and pulled a seat-less blob. For seating,
   lead with the furniture noun + leg/stack cue ("stackable side chair with four legs");
   the material word can drag the embedding off the object class.
3. **A 2-candidate shortlist is a thin-pool red flag** even when the VLM picks correctly
   (washing-dryer, vending). Fine here, but confirm by eye — the picker can only choose from
   what routing surfaced.
4. **Score ≠ correctness, low score ≠ wrong-but.** The 0.41 dining table was a wrong subtype
   (decorative, not utility) though plausibly "long flat table"; the 0.67 laundry sign and
   0.53 vending machine were genuinely correct. Always look at the preview.
