---
id: example:casino
kind: example
family: zoned-multi-zone
category: "gaming floor"
pattern: "Large multi-zone — table hub + repeated slot rows + bar"
---
> **Digest (from the pattern index):** Large multi-zone — table hub + repeated slot rows + bar


# Casino — worked example ("Red-Gold Opulent Gaming Floor")

Status: built as `scenes/work/casino.py`. [`casino_v1.py`](casino_v1.py) is that program **phase-gated** (2026-07-13): `lint_program`-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record).

Built end-to-end coarse-to-fine from the planner target (`tmp/casino/plan/plan.png`). Read
alongside `../workflow/coarse_to_fine.md`. The audited asset picks live in
`scenes/work/casino.md`; the working program is `scenes/work/casino.py`.

## Prompt(s) this covers
- "a casino" / gaming floor / card room / slots hall.

## Plan summary
Palette **deep red + gold, ebony + brass**. The hero is a **central blackjack hub** — a felt card
table ringed 360° with **red-velvet swivel seating** under a **grand crystal chandelier**.
**Perimeter rows of slot machines** line the two long walls; a **luxe bar** (counter + stools +
bottles, gilded back-bar mirror) is the secondary anchor on a short wall. **No windows** — an
authentic casino floor is sealed and lit entirely by the chandelier + warm ambient fill, so all
light comes from `add_lighting`, none from daylight. That is a deliberate category rule, not an
omission: don't add a window to a casino.

## Assets — pin the audited good ones, accept two dataset gaps
Audit (`scenes/work/casino.md`) verdicts, with the pins used:
- **Slot machine** `hssd/f06d7023…` — GOOD (an IGT "Mistress of Egypt" cabinet; reads
  unmistakably as a casino slot). Duplicate it into a row per wall.
- **Red velvet swivel chair** `hssd/c4423cf1…` — GOOD, the plan's hero seat (sim 0.75 on
  `"a red velvet tufted swivel armchair with brass base"`; a red tufted swivel — chrome caster
  base, not brass pedestal, but the color/tufting carry it). Pin it; ring the table with `6 *`.
- **Bar counter** `hssd/b1c9d7321…` — GOOD long straight counter, against-wall placeable.
- **Card table** `hssd/81f092c5…` — WEAK: a flat-top **walnut** card table on legs; **no green
  felt** (the dataset has none — pool tables only). Reads as a gaming table and rings fine, so
  it's the working substitute. A real semicircular green-felt blackjack table is the **#1 ingest
  target**.
- **Neon casino sign** — MISSING (no illuminated casino neon in the pool). This plan leans
  **gilded framed art** instead (more faithful to the red-gold opulent look), so no neon is
  needed; it's an optional ingest for a Vegas-neon variant.

> Lesson from the audit that held up: **"casino" as a query adjective hurts** (sparse in the
> dataset → pulls similarity down and can defeat routing). Describe the *object shape* and put the
> theming in material/color words: `"a red velvet tufted swivel armchair"`, not "a padded casino
> chair"; `"a long bar counter"`, not "a long casino bar counter".

## Phase 1 — floor anchors (hub + perimeter slots + bar), layout + proportions
Central hub via `AroundGroup.place_circle` (360° ring, `jitter=0.4` so it reads lived-in); the
grand chandelier is `hub.add_lighting(..., density=0)` (single central fixture). Slots are one
`GridGroup.place_row` per **long** wall, placed with `place_on_left/right_wall_center` and faced
**into the room** (`facing="right"` on the left wall, `facing="left"` on the right wall — a
wall-backed machine's screen points at the room, i.e. toward the *opposite* side). The bar counter
goes flush on the **back** short wall; the door on the **front** short wall. Room came out clean:
`no rescale / no rotation / no wall overlap`, well-filled at `modulate_scale=1.0`.

## Phase 2 — surface & floor details (the bar becomes a bar; lighting)
Rebuild the bar as a `RelativeGroup` anchored on the counter so the props travel with it:
`place_on_top(4 * bottle)`, a **single row of stools** in front, and
`add_lighting("warm recessed ambient ceiling downlights", density=0.02)` for room fill. Place the
whole group with `room.place_on_back_wall_center(bar, facing="front")` — the counter sits flush to
the wall, the stools + bottles project into the room. Upgraded the chandelier query to
`"an ornate gold and crystal chandelier"` for a warmer, more opulent fixture.

> **Stools = one nested row, not `place_on_front_left/front/front_right`.** The three per-corner
> verbs split the stools to the two *ends* of the counter (one on each side) — reads wrong for a
> bar. Instead build the stools as their own `GridGroup.place_row(3 * stool)` and drop that row in
> with `bar.place_on_front(stool_row)`: one contiguous, evenly-spaced line of stools along the
> counter front, all facing it. (General: to line N children up in front of an anchor, place a
> `GridGroup` row, don't enumerate corner verbs.)

> **Gotcha — no `place_on_top` decor without a real mesh.** `hub.place_on_top("a stack of colorful
> casino poker chips")` retrieved a **children's book display rack** (chips/cards/chip-trays don't
> exist in the dataset; "colorful … stack" matched a book rack) and it dominated the hero table.
> Removed it — the felt top reads fine bare. A casino-chip tray is an ingest target. Rule: only
> `place_on_top` an item the dataset actually has; verify the pick, don't assume a small prop exists.

## Phase 3 — walls & decor (gilded art, faithful to the plan)
Slot walls have **no headroom** for wall art (the machines are ~2 m tall in a 3 m room), so hang
art only on the **short** walls: an ornate **gold-framed mirror** on `back-center` (a back-bar
mirror above the counter) and two **gilded framed artworks** on the front (`front-left`,
`front-center`) flanking the `front-right` door — three distinct wall slots, no overlap.

## VLM / layout feedback we hit and how we resolved it
- Phases 1–2: `no rescale / no rotation / no wall overlap` throughout.
- Final `RoomProportions` = **`rescale room by 1.05`** (occupancy a hair over the 0.4 target). A
  ~5% enlarge is within noise and the render reads well-filled — **declined** (render wins /
  converge-don't-chase). Held `modulate_scale=1.0`.

## What worked / gotchas (summary)
- **Long strips on the long walls = correct footprint.** A slot *row* on each long wall + a light
  bar/door on the short walls sizes the room right, same lesson as the salon's styling row.
- **`AroundGroup.place_circle` + `jitter` is the right tool for a gaming hub** (360° engagement);
  the auto overlap solve after jitter keeps chairs from interpenetrating.
- **Face wall-backed machines at the *opposite* wall** (`facing` = the far side), not at their own
  wall, so screens face the room.
- **Casino = no windows**; carry the whole mood on `add_lighting` (a statement chandelier +
  low-density warm fill). Expect Phase-1 renders to look dark until the light pass.
- **Two honest dataset gaps** (green-felt table, casino-chip tray / neon sign) — substituted and
  flagged for ingest rather than forced.

## Program

[`casino_v1.py`](casino_v1.py) — phase 1 the slot rows, the card-table hub with its swivel chairs, the bar counter + stool row, walls and door; phase 2 the liquor bottles on the back-bar; phase 3 the chandelier over the hub, the warm ambient fill and the wall decor (a windowless category — early-phase renders are dark by construction).

`workbench run skills/examples/casino_v1.py --phase 1` builds the layout alone in ~1–2 min.
