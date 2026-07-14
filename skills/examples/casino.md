# Casino — worked example ("Red-Gold Opulent Gaming Floor")

## Status

Status: **built & VLM-clean as the pre-phase program** `scenes/work/casino.py` (seed=29,
`modulate_scale=1.0`), driven coarse-to-fine from the planner target `tmp/casino/plan/plan.png`.
Final compile on that build: `no rescale / no rotation / no wall overlap`.

[`casino_v1.py`](casino_v1.py) is that same program **retrofitted with phase gates** (2026-07-13).
It is **`lint_program`-clean** and preserves the original layout, pins, seed and comments — but it
has **NOT been re-rendered since the retrofit**, so **the phase splits are unverified**: no phase-1,
phase-2 or phase-3 build has been run against the gated file. Nothing below claims a render that was
not run. Two gate assignments moved relative to the original program's own phase notes, and neither
has been checked in a build:

* the **stools** were pulled *back* into phase 1 (they are floor geometry — see
  [Lesson 2](#lesson-2--a-row-of-stools-is-one-nested-row-and-it-belongs-to-the-floor-solve));
* the **chandelier + ambient fill** were pushed *forward* into phase 3, matching the repo-wide
  convention that `add_lighting` is the mood layer.

## Prompt(s) this covers
- "a casino" / "a gaming floor" / "a card room" / "a slots hall".

## Plan summary (from the planner)

"Red-Gold Opulent Gaming Floor." Palette **deep red + gold, ebony + brass**. The hero is a
**central blackjack hub** — a felt card table ringed 360° with **red-velvet swivel seating** under a
**grand crystal chandelier**. **Perimeter rows of slot machines** line the two long walls; a **luxe
bar** (counter + stools + bottles, gilded back-bar mirror) is the secondary anchor on a short wall.
**No windows** — an authentic casino floor is sealed and lit entirely by the chandelier + a warm
ambient fill, so all light comes from `add_lighting` and none from daylight. That is a deliberate
category rule, not an omission: *do not put a window in a casino.*

## The layout idea: CENTRE HUB + PERIMETER ROWS + a BAR wall

The **large multi-zone** pattern: one 360°-engaged hero in the *middle* of the floor, repeated rows
pinned along the *long* walls, and a service anchor on a *short* wall.

| Wall / slot | Job |
|---|---|
| **centre** | the blackjack **hub** — an `AroundGroup.place_circle` ring of 6 velvet swivels around the card table. A gaming table is played from every side, so it *cannot* live against a wall. |
| **left** (long) | a slot bank — a `GridGroup.place_row`, faced **into** the room (`facing="right"`). |
| **right** (long) | the mirror-image slot bank (`facing="left"`). |
| **back** (short) | the **bar**: counter flush to the wall, stool row + bottles projecting into the room, back-bar mirror above. |
| **front** (short) | the entry door (right) + the two gilded artworks. The short walls are the only walls with **headroom** for art. |
| **ceiling** | the chandelier over the hub + a low-density warm fill. This room has **no window**, so the ceiling *is* the light source. |

It inherits the hero-in-the-middle idea from [`game_room.md`](game_room.md) (the hero's own
clearance sizes the room) and the twin-row-on-the-long-walls idea from [`library.md`](library.md) /
[`locker_room.md`](locker_room.md); the bar wall is [`bar.md`](bar.md)'s rigid straight-counter
station. What is new is that the **rows and the hub are the same room**: the perimeter rows buy the
floor's *shape* while the central ring buys its *subject*.

## Pinned assets (audited previews — the audit table is `scenes/work/casino.md`)

| Role | id | Verdict / why pinned |
|---|---|---|
| slot machine | `hssd/f06d7023…` | **GOOD** — a genuine IGT CrystalDual cabinet; reads unmistakably as a casino slot. This is *the* asset that names the room, so it is duplicated `5 *` per wall. |
| red velvet swivel chair | `hssd/c4423cf1…` | **GOOD** — the plan's hero seat (sim 0.75 on *"a red velvet tufted swivel armchair"*). Chrome caster base, not a brass pedestal, but the colour + tufting carry it. |
| bar counter | `hssd/b1c9d7321…` | **GOOD** — a long straight counter, against-wall placeable. Routed correctly to `CountersRetriever`. |
| card table | `hssd/81f092c5…` | **WEAK, pinned anyway** — a flat-top **walnut** card table on legs; **no green felt**. It is a flat square top on legs, so it rings and reads as a *gaming* table. The honest substitute. |

## Asset gaps

Three, all recorded in the audit (`scenes/work/casino.md`), none faked:

1. **Green-felt blackjack table — MISSING.** `GameEquipmentRetriever` holds pool tables, foosball
   and air-hockey plus one walnut "poker table". Substituted with that table; a real semicircular
   green-felt blackjack table is the **#1 ingest target** (spec in the audit: green felt arc, padded
   leather rail, flat dealer side, ~1.8 m wide, facing +Z).
2. **Casino chip tray / poker chips / playing cards — MISSING.** See
   [Lesson 3](#lesson-3--never-place_on_top-a-prop-the-dataset-does-not-have). The hero table is
   therefore left **bare**, which is why phase 2 adds nothing to it.
3. **Neon casino sign — MISSING.** No illuminated casino neon exists in the pool (the literal query
   returned a flat black cursive "Welcome" sign). This plan leans on **gilded framed art** instead —
   more faithful to the *red-gold opulent* brief than neon would have been — so nothing is smuggled
   in. Neon stays an optional ingest for a Vegas-neon variant.

Feed-forward: gaps 1 and 3 are logged with glb specs in `scenes/work/casino.md`; the general rule
they mint is in [Lesson 3](#lesson-3--never-place_on_top-a-prop-the-dataset-does-not-have) and
belongs in [`../workflow/creative_asset_gaps.md`](../workflow/creative_asset_gaps.md).

---

## Lesson 1 — a THEME word in the query is a tax; describe the OBJECT, theme with material

The single most reusable finding of the retrieval audit. **"casino" as a query adjective hurts more
than it helps**: it is sparse in the dataset, so it drags similarity down *and* can defeat category
routing.

| query | what it returned |
|---|---|
| *"a padded casino chair"* | a legless black **floor cushion** (sim 0.497) |
| *"a red velvet tufted swivel armchair"* | the pinned hero seat (sim **0.75**) |
| *"a long casino bar counter"* | routed OK, but the theming bought nothing |
| *"a small casino podium"* | landed in the **general** pool, not the curated `presentation_fixtures` pool — the casino qualifier defeated the router |

**Rule: name the object's *shape*, and put the theming in the material/colour words.** *"a red velvet
tufted swivel armchair"*, not *"a padded casino chair"*. *"a long bar counter"*, not *"a long casino
bar counter"*. This is the same reword instinct [`jewelry_shop.md`](jewelry_shop.md) applies to pool
routing and [`tv_studio.md`](tv_studio.md) / [`art_studio.md`](art_studio.md) generalise into *hunt
the mesh by SILHOUETTE, not by caption*.

Two corollaries from the audit:

* **Trust the preview PNG, never the picker's prose.** The neon-sign pick was justified with "neon
  glow" that is simply not in the image (flat dark-grey cursive script). Open the preview. This is
  [`toy_shop.md`](toy_shop.md)'s *caption ≠ mesh* rule, hit from the other direction: here it was the
  *justification* that lied, not the caption.
* **Seat height is a silent failure mode.** A *"padded chair"* can resolve to a legless floor cushion
  — players would sit *below* the table top, and nothing in the VLM loop or the lints would say a
  word. Name the seat *type* ("dining armchair", "swivel armchair", "bar stool") whenever the seat
  rings a table. [`fast_food.md`](fast_food.md) later mints the general form of this: tabletop↔seat
  is an **ergonomic** relationship that no VLM constraint checks.

## Lesson 2 — a row of stools is ONE nested row, and it belongs to the FLOOR solve

Two halves, both load-bearing.

**(a) One row, not three corner verbs.** `bar.place_on_front_left/front/front_right(stool)` splits the
three stools to the two *ends* of the counter, one on each side — which reads wrong for a bar. Build
them as their own row and drop the row in as a single child:

```python
with scene.GridGroup(sparsity=0.5, randomness=0.1) as stool_row:
    stool_row.place_row(3 * scene.AddAsset("a bar stool with a red cushioned seat"))
with scene.RelativeGroup() as bar:
    bar.set_anchor(scene.AddAsset("a long bar counter", asset_id=BAR_CT))
    bar.place_on_front(stool_row)      # one contiguous, evenly-spaced line along the counter front
```

**General: to line N children up in front of an anchor, place a `GridGroup` row — do not enumerate
corner verbs.** [`waiting_room.md`](waiting_room.md) later pushes the same trick to its limit
(`sparsity=0.05` runs *no* overlap solve, so chairs stay abutted and read as one linked bank).

**(b) The row is phase-1 geometry.** The original program's own phase notes put the stools in phase 2
with the bottles. The retrofit pulls them back into **phase 1**, because a stool row is *floor*
furniture: it adds depth to the bar's slot, and `RoomGroup` auto-sizes the shell from its slot
maxima — so introducing the stools in phase 2 would grow the shell *after* the cheap phase-1 build
had already signed off on it. The phase contract is *later phases only ADD*; adding a **floor**
object still changes the number the shell is computed from. Keep floor furniture in phase 1 and let
phase 2 be genuinely surface-only. (This is the retrofit's one substantive judgement call, and it is
**unverified by a render** — see Status.)

## Lesson 3 — never `place_on_top` a prop the dataset does not have

`hub.place_on_top("a stack of colorful casino poker chips")` retrieved a **children's book display
rack** — chips, cards and chip-trays do not exist in the pool, and *"colorful … stack"* matched a
book rack — and it then **dominated the hero table**, because `place_on_top`'s sizing tournament
scales the prop to the anchor and does not care what the mesh *is*.

It was removed, and the felt top reads fine bare. **Rule: only `place_on_top` an item the dataset
actually has; verify the pick, do not assume a small prop exists.** A missing prop is a *gap to
ingest*, not a query to keep rewording.

This is the seed of a rule several later examples restate at full strength:
[`kindergarten_v1.md`](kindergarten_v1.md) ("a cup of crayons does not exist" — the retriever handed
back a designer pen pot and the VLM loop, which cannot see semantics, said nothing);
[`laboratory.md`](laboratory.md) (twelve identity props returning 0.000 — an *empty candidate list*,
not a bad pick); [`pantry.md`](pantry.md) (one oversized mesh poisons a whole rack's tile size).
The common thread: **the VLM loop verifies geometry, not category legibility.** A wrong prop that
sits flat on a table is a *clean* build.

Note the tension with [`jewelry_shop.md`](jewelry_shop.md)'s product rule (*a shop reads by its
merchandise, so MASS the product*). Both are true, and the casino shows the boundary: **mass the
product only where the product has a mesh.** Here the product-that-reads is the *slot machine* —
massed 5× per wall — and the chips, which have no mesh, are simply left out.

## Lesson 4 — a wall-backed machine faces the OPPOSITE wall

A slot machine's screen must point at the room. `facing` names the side the object *turns toward*, so
a machine on the **left** wall takes `facing="right"` and one on the **right** wall takes
`facing="left"` — the *far* side, never its own wall:

```python
room.place_on_left_wall_center(slots_left,  facing="right")
room.place_on_right_wall_center(slots_right, facing="left")
```

Get this backwards and you build a row of machines showing the room their backs, with `no rotation`
flagged by nobody. Generalises to any screen/display/service fixture pushed against a wall
([`meeting_room.md`](meeting_room.md) hit the same flip on a reversed-front sideboard;
[`tv_studio.md`](tv_studio.md) shows the group-nesting version of the trap — nesting a floor object
in a group bakes a ±90° rotation into it).

## Lesson 5 — long strips on the LONG walls is what sizes the room

The two 5-machine rows go on the **long** walls; the bar and the door take the **short** walls. That
one decision gives the floor its correct rectangular footprint for free — the shell is the sum of its
slot maxima, so a long rigid run on a *short* wall would have squared the room off and left the long
walls under-loaded. Same lesson as [`hair_salon.md`](hair_salon.md)'s styling row and
[`library.md`](library.md)'s twin shelf runs; [`grocery_store.md`](grocery_store.md) states the
arithmetic explicitly (*the shell is the SUM of 5 column maxima*).

Corollary hit in phase 3: **the loaded long walls have no headroom left.** The machines are ~2 m tall
in a 3 m room, so wall art can only go on the short walls — mirror on `back-center` (a back-bar
mirror above the counter), two gilded pieces on `front-left` and `front-center`, flanking the
`front-right` door. Three distinct wall slots, no overlap.

## Lesson 6 — a windowless category: the mood is 100% `add_lighting`

A real casino floor is **sealed**: no clocks, no daylight. So this scene places **no window at all**,
and the entire mood budget goes through `add_lighting`:

* `hub.add_lighting("an ornate gold and crystal chandelier", density=0)` → **exactly one** fixture,
  the grand statement piece, directly over the hero;
* `bar.add_lighting("warm recessed ambient ceiling downlights", density=0.02)` → the low warm fill.

**Consequence for the workflow: expect the phase-1 and phase-2 renders of a windowless room to look
DARK, and do not "fix" it.** Nothing is broken; the light layer is phase 3 by construction. The
inverse of [`greenhouse.md`](greenhouse.md) (where brightness is a *sky* setting and never
`add_lighting`), and the same territory [`wine_cellar.md`](wine_cellar.md) later mapped properly for
any dim brief — read that one first if you are tuning a dim room, since it owns the sky-vs-wattage
arithmetic (`scene.light_budget`, and *tune ONE dial at a time*). The casino predates
`scene.light_budget` and does not set it.

## Lesson 7 — `AroundGroup.place_circle` + jitter is the right tool for a gaming hub

360° engagement is the whole point of a card table, and `place_circle` gives it directly.
`jitter=0.4` breaks the perfect ring so it reads *lived-in* rather than showroom-staged, and the
automatic overlap solve after the jitter keeps the chairs from interpenetrating. Contrast
[`meeting_room.md`](meeting_room.md) / [`dining_room.md`](dining_room.md), where a *rectilinear* ring
is correct because the table is long — circle for a hub, rectilinear for a run.

---

## Program

[`casino_v1.py`](casino_v1.py) — **phase 1** the floor anchors (the hub ring, the two slot rows, the
bar counter + its stool row, the walls, the door); **phase 2** the surface dressing (the liquor
bottles on the bar top — and *nothing* on the hero table, deliberately); **phase 3** the mood layer
(the chandelier, the ambient fill, the back-bar mirror and the two gilded artworks).

`workbench run skills/examples/casino_v1.py --phase 1` builds the layout alone in ~1–2 min.

| Phase | Builds | Why it is separate |
|---|---|---|
| 1 | hub + slot rows + bar counter + stool row + walls + door | cheap; catches layout/scale/facing errors before any dressing. Note **`place_walls` and `place_door` are UNGATED** — the door's automatic clearance shapes the floor solve, so deferring it would change the layout you just validated. |
| 2 | the bar top (`place_on_top` bottles) | thin here **on purpose**: the hero table gets nothing, because the chip tray does not exist (Lesson 3). |
| 3 | chandelier, ambient fill, back-bar mirror, gilded art | the whole mood — a windowless room has no daylight to fall back on (Lesson 6). |

Mechanics worth copying: every gated `place_on_top` / `add_lighting` sits **inside** its group's
`with` block. A group compiles on `__exit__`, so a `place_on_top` gated *outside* the block never
runs — the count still increments, the lints stay clean, and the prop is simply **GONE**
([`prison_cell.md`](prison_cell.md) shipped that bug once). Every asset used only inside a gate is
constructed **inline inside that gate** (`scene.AddAsset(...)` in the call), so no phase-3 asset
orphans into a phase-1 build.

## What worked / gotchas

- **`modulate_scale=1.0` was right.** The two rigid slot rows plus a centre hub genuinely fill the
  floor; this is not a sparse room ([`laundromat.md`](laundromat.md)) and it does not need to shrink.
- **Long rigid runs on the long walls = the correct footprint** (Lesson 5).
- **Face wall-backed machines at the *opposite* wall** (Lesson 4).
- **Casino = no windows** — carry the mood entirely on `add_lighting` (Lesson 6).
- **Two honest dataset gaps** (green-felt table, chip tray / neon sign) — substituted and flagged for
  ingest rather than forced. The scene still reads, because the identity was carried by the asset the
  pool *does* have (the slot machine), massed.
- **The theme word is a tax** — reword before you re-rank (Lesson 1).

## VLM feedback we hit and how we resolved it

Recorded on the **pre-phase** program (`scenes/work/casino.py`), which is the only build that has
been rendered. **Nothing below was re-run against the gated retrofit.**

| feedback | action | result |
|---|---|---|
| Phases 1–2 (coarse-to-fine, un-gated program): `no rescale / no rotation / no wall overlap` throughout | none needed | held |
| Final `RoomProportions`: **`rescale room by 1.05`** — occupancy a hair over the 0.4 target | **DECLINED.** A ~5% enlarge is inside the noise band, and the render read well-filled | held `modulate_scale=1.0`; the build converged clean |
| *(retrieval-loop votes, per-asset)* | see the audit table in `scenes/work/casino.md` | 4 pins, 3 gaps |

The declined 1.05 is the instructive one: a *single*, *small*, *non-repeating* room-size vote on a
**converged full build** is noise, and chasing it is how you end up oscillating. Compare the
vote-train rule ([`living_room_cozy.md`](living_room_cozy.md): *a vote that never flips is signal*;
[`bookstore.md`](bookstore.md): *a decaying rescale vote means converged*) and the phase-aware
sharpening in [`bedroom.md`](bedroom.md) (*a room-size vote on a phase-1 room is voting on a room
that does not exist yet*) — which is exactly why **no phase-1 rescale vote should be actioned on
this gated file** either: at phase 1 the bar is bare and the room is unlit.

**Gap, stated plainly:** the per-phase VLM votes were only ever logged in the summary form above.
There is **no recorded pass-by-pass history** (no seeds, no vote trains, no per-render strings), and
the retrofit did **not** generate any. If you rebuild this scene, log every vote — and mirror the
notable ones into [`../workflow/vlm_feedback.md`](../workflow/vlm_feedback.md).

## Manual constraints used

**None.** No `Clearance` / `Access` / `Visibility` constraint is declared anywhere in the program.
Everything came from the defaults:

- the hub's chair ring gets its spacing from `AroundGroup`'s own overlap solve after the jitter;
- the door's clearance is free from `CategoryClearanceConstraint`;
- the slot rows' spacing is `GridGroup(sparsity=0.35)`.

Worth knowing, because the sibling pattern in [`game_room.md`](game_room.md) *does* need an explicit
clearance ring around its hero. Here the ring of chairs **is** the clearance.

## Possible refinements (not blocking)

- **Run the gated program at each phase.** Phases 1, 2 and 3 of [`casino_v1.py`](casino_v1.py) have
  not been rendered since the retrofit. Until they are, the two moved gates (stools → phase 1,
  lighting → phase 3) are reasoned, not verified — and this file should not claim otherwise.
- **Ingest the green-felt blackjack table** (spec ready in `scenes/work/casino.md`). It is the single
  change that would most improve the read: the hero is currently the one weak pin in the scene.
- **Ingest a chip tray**, and only then reinstate a `place_on_top` on the hub. Not before (Lesson 3).
- **Log the VLM loop on the rebuild.** The pass-by-pass history is missing and cannot be
  reconstructed.
- **Consider `scene.light_budget`** ([`wine_cellar.md`](wine_cellar.md)) on the rebuild. A casino is a
  *dim* room and this program predates the wattage dial, so it is still running the default 500 W
  through a chandelier that ought to be pooling light on the felt.
