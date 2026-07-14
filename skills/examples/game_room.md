# Game room — worked example ("Central Play Nexus")

A moody home game room / rec lounge built entirely by **composition** — no new DSL, no asset
ingestion. The `GameEquipmentRetriever` pool is deep enough to cover every game piece off the shelf,
which is why this example is about *layout* rather than about assets.

## Status

`Status:` the original program (`scenes/work/game_room.py`, seed=17) was **built and VLM-iterated** —
the lighting fix in [Lesson 2](#2-add_lightings-footprint-is-the-groups-bounding-box--keep-the-group-compact)
and the declined rotation votes in [Lesson 5](#5-vlm-orientation-notes-are-noisy--verify-then-override)
both came out of real renders. **The vote log itself was never written down** (see
[VLM feedback](#vlm-feedback-we-hit-and-how-we-resolved-it)).

[`game_room_v1.py`](game_room_v1.py) is that program **phase-gated** (2026-07-13):
`lint_program`-clean, layout / pinned ids / seed / comments preserved. It has **NOT been re-rendered
since the retrofit — the phase splits are UNVERIFIED.** No phase-1, phase-2 or phase-3 build has been
run against the gated file. Treat the phase contract below as *intent*, not as a result.

## Prompt(s) this covers
- "a moody home game room / rec lounge: a pool table, an arcade corner, a bar, a big TV and a sofa,
  foosball, a poker table and a dartboard."

## Plan summary (from the planner)

**"Central Play Nexus."** Billiards is the social hero at the centre of the room, with the other
amusements arranged as *zones* ringed around it: a bar hub, an arcade corner, a media/lounge zone, a
foosball station at the window and a poker corner. Moody walnut / charcoal / brass palette, a green
feature wall behind the bar, dark stone-tile floor. `modulate_scale=0.9`, `randomness=0.08`.

## The layout idea: HERO-IN-THE-MIDDLE, ZONES RINGED AROUND IT

A rec room is the same "plan the zones first, then fill them" problem as [`gym.md`](gym.md), but with
a single **social hero in the middle** instead of perimeter rows. The hero is a table you play from
all four sides, so it *cannot* go on a wall — and once it is in the middle, **its clearance is what
sizes the room** and every other zone settles into the space that clearance reserves.

This is the pattern [`casino.md`](casino.md) inherits (a card hub in the middle, rows on the long
walls — there the *ring of chairs* is the clearance, so it needs no explicit constraint), that
[`operating_room.md`](operating_room.md) inherits as *hero-in-the-middle, sterile* (the 1.2 m sterile
ring is a cue-stroke clearance by another name), and that [`kindergarten_v1.md`](kindergarten_v1.md)
borrows for its zoned play floor.

| Wall / slot | Job |
|---|---|
| **centre** | **BILLIARDS** — the 8-ft pool table on a bordered rug, one pendant directly above. Played from every side → it owns the middle, and its 1.3 m all-round clearance sizes the floor. |
| **back** | the **BAR** social hub: counter + back-bar bottle cabinet + a straight 3-stool row, facing into the room. Gallery photos and a colourful painting above it. |
| **back-right corner** | the **ARCADE**: two upright cabinets, backs to the wall, screens into the room. Two cabinets in a row want a corner — no circulation cost. |
| **left** | **MEDIA / LOUNGE**: wall TV over a low console; leather sofa **facing the wall**, flanked by two velvet armchairs angled into a coffee-table cluster. |
| **right** | the **WINDOW**, with **FOOSBALL** in front of it — the players get the view. The only wall with nothing stored or seated *on* it, so it stays the daylight source. |
| **front-left** | **POKER**: walnut card table + four chairs, each faced at the table. |
| **front** | the entry **door (centre** — you walk in at the hero), the trophy cabinet (left), the wall **dartboard** (right), whose throwing lane runs into the deliberately empty front-right quadrant. |

"Foosball players face the window" is [`gym.md`](gym.md)'s *cardio-faces-the-view* rule generalised:
**a station whose user stands still for a long time gets pointed at whatever is worth looking at** —
the window for foosball, the TV for the sofa.

## Pinned assets (audited previews)

| Role | id | Why pinned |
|---|---|---|
| pool table | `hssd/988e19a9…` | 8-ft espresso frame, **green felt** — the only recorded per-pin rationale, and the right one: the felt is what makes the hero read as *billiards* rather than as a table. |
| foosball | `hssd/99c18325…` | classic wooden foosball table |
| arcade cabinet | `hssd/3873f4b8…` | upright retro cabinet; duplicated `2 *` |
| dartboard | `hssd/8b1f720d…` | wall cabinet, doors open |
| poker table | `hssd/81f092c5…` | walnut card table with a padded rail — the *same* flat-top table [`casino.md`](casino.md) pins as its blackjack substitute |
| bar counter | `hssd/96aa481c…` | home bar counter, `width=2.8` |
| back-bar cabinet | `future/f92b65d2…` | glass-door bottle cabinet, `width=2.4` |
| bar stool | `hssd/d10ff3f7…` | wooden stool with a backrest; `3 *` |
| sofa | `future/c9856517…` | vintage brown leather three-seat |
| armchair | `hssd/bf96d2cc…` | **green velvet** — the accent colour of the palette; `2 *` |
| TV | `hssd/52676f40…` | slim black flat-screen, wall-hung |
| media console | `future/12b76671…` | low dark-wood console (low on purpose — see the refinements) |
| trophy cabinet | `hssd/80bfb59e…` | dark-wood glass display cabinet |

**Honesty note:** only the pool table's pin carries a recorded reason. The rest are pinned because
they are the meshes the shipped scene was validated on — and because an unpinned pick is **not**
stable across runs even at a fixed seed ([`jewelry_shop.md`](jewelry_shop.md)'s rule; the velvet
armchair here is exactly the colour-carrying prop that rule says you must pin).

## Asset gaps

**One, and it is minor:** a dedicated **wall cue rack** — no visual match in the pool. **Dropped**
rather than substituted; a cue rack is small enough that its absence does not stop the room reading
as a billiards room. Everything else the plan asked for exists off the shelf:
`GameEquipmentRetriever` covers pool table (green felt — *and* a purpose-built billiards pendant
light in the same pool), foosball, upright arcade cabinet, air hockey, wall dartboard cabinet, poker
table. Furniture comes from the usual retrievers (bar counter, back-bar bottle cabinet, wooden bar
stools, leather sofa, green-velvet armchairs, slim wall TV, low media console, glass display
cabinet).

This is a **deep-pool room** — worth knowing, because the sibling patterns are not:
[`casino.md`](casino.md) has to substitute its hero table entirely, and
[`operating_room.md`](operating_room.md) has to ingest.

## The lessons this scene mints

### 1. The hero's clearance sizes the room
The pool table gets `add_clearance(pool_table, distance=1.3, dir="all")` — enough to draw a cue on
every side. **That single all-round clearance is what actually drives the room's footprint**; the
other zones settle into the space it reserves. Put the hero and its clearance down first and let the
ring fill in around it.

The generalisation: **when a hero is used from all sides, the room's size is a property of the hero's
working envelope, not of the furniture count.** The corollary is that a `modulate_scale > 1.0` on
such a room is *not* the "inflate the shell to dodge overlaps" anti-pattern — it is this rule, and
it is the correct lever (a point `../workflow/vlm_feedback.md` makes by name, citing this scene).
[`operating_room.md`](operating_room.md) is the same rule with a sterile ring instead of a cue
stroke; [`casino.md`](casino.md) is the case where the ring of chairs *is* the clearance and no
explicit constraint is needed.

### 2. `add_lighting`'s footprint is the GROUP's bounding box — keep the group compact
Pendant lighting over a group **scatters if the group's bounding box is big**, because the count is
spread across the group's footprint.

First pass placed the 3 bar stools with `place_on_front_left / _front / _front_right` — spread in
**both x and z** — and used `density=0.25`. Result: **~15 globes strung in a line across the whole
back of the room.** Fix, in two parts: a compact **straight** stool row via
`AroundGroup.place_rectilinear(longer_side1=stools)`, and `density≈0.18` → a tight cluster of ~5
globes directly over the counter. (Same pattern as [`bar.md`](bar.md)'s straight bar-line.)

Rules of thumb this leaves you:
- for a **pendant cluster over one piece**, keep that piece's group tight and the density low (~0.15–0.2);
- `density=0` gives **exactly one** fixture — used here for the billiards pendant over the hero;
- the count is `N = 1 + (max_lights - 1) * density`, and it is a **count**, not a brightness.

### 3. `face(child, toward=target)` is how you seat a cluster
Chairs placed with `place_on_left/right/front/back` inherit the anchor's rotation and **face
outward**. To seat them *at* something — the armchairs toward the coffee table, the poker chairs
toward the poker table — call `group.face(chair, toward=table)` **inside** the group. Loop it for a
whole set:

```python
for _ch in poker_chairs:
    poker.face(_ch, toward=poker_table)
```

This is the general rule [`living_room_cozy.md`](living_room_cozy.md) and
[`hospital_room.md`](hospital_room.md) both relearn: **side/arc/further placements orient sideways by
default — aim seating at the cluster anchor explicitly.** Doing it by construction is also what keeps
the VLM's rotation channel quiet (see Lesson 5); see [`classroom.md`](classroom.md) for the
`place_desk_chair` version of "make orientation correct by construction, not by chasing votes."

### 4. A bar is ONE rigid station: back-bar *behind* the counter
```python
with scene.RelativeGroup() as bar:
    bar.set_anchor(bar_line)                 # counter + its stool row
    bar.place_on_back(back_bar_cabinet)      # bottle cabinet behind the whole line
```
`RelativeGroup.place_on_back` **bakes a fixed service aisle** between the bottle cabinet (against the
wall) and the counter — more reliable than a clearance constraint fighting the stool overlap. The
station then travels as one unit and gets placed at the back wall with a single `place_on_back(bar,
facing="front")`. Same station shape as [`bar.md`](bar.md); [`casino.md`](casino.md) reuses it for
its bar wall.

Note the composition: `bar_line` (an `AroundGroup`: counter anchor + straight stool row) is itself
the **anchor** of the outer `RelativeGroup`. Groups nest, and the outer group's relative verbs act on
the whole inner group.

### 5. VLM orientation notes are noisy — verify, then override
The VLM **flip-flopped** between "rotate the armchairs" and "rotate the poker chairs" across renders,
and repeated **"rotate bottom chair" four identical times** — even though `face()` had already angled
every seat correctly, which the render confirmed. **All declined.**

Rule: **treat repeated or contradictory rotation notes as noise once the image shows the seats are
right.** The rotation check is a weak smoke alarm, not an authority — your own look at the render is
the arbiter. This scene is one of the datapoints behind the repo-wide version of that rule in
[`../workflow/vlm_feedback.md`](../workflow/vlm_feedback.md) ("Rotation: don't trust the VLM for it —
use deterministic structure"), and it pairs with the inverse warning: a *self-identifying* rotation
storm (votes naming objects that don't exist, or votes on a garbage camera view) is noise, but a
rotation problem you can **see** must be fixed with `face()`, never argued with.

### 6. This room's identity lives in PHASE 1 — so its phase 2 is nearly empty
Minted by the phase-gating retrofit (2026-07-13), and **structural, not rendered** — see Status.

Sort this scene's statements into the standard phases and something falls out: **the game pieces are
all floor anchors.** Pool table, foosball, arcade cabinets, poker table and chairs, sofa, bar,
trophy cabinet — every object that *names* the room is phase 1. Phase 2 (`place_on_top` / rugs /
plants) contains exactly **one** statement: the billiards rug. Phase 3 is real but is pure *mood* —
wall art, the TV, the dartboard, the window, three lighting layers.

Two consequences worth carrying to the next rec-room-shaped scene:
- **The cheap phase-1 build is worth an unusual amount here.** In a room whose identity is dressing
  (a shop, a bakery), a phase-1 render tells you little; here it is ~90% of the finished room, so a
  layout error is both cheap to catch *and* the only kind of error that matters.
- **Do not "fill" phase 2 to make it look balanced.** A near-empty surface phase is a legitimate
  shape — the *inverted vibe layer* [`operating_room.md`](operating_room.md) and
  [`prison_cell.md`](prison_cell.md) name explicitly. The one thing you must get right is the
  **gate's position**: the rug's `if PHASE >= 2:` sits **inside** the `with billiards` block. A
  `place_on_top`/`place_rug` gated *outside* its block registers after the group has compiled on
  `__exit__` and **silently never runs** — clean lint, clean VLM loop, missing prop
  ([`prison_cell.md`](prison_cell.md)'s bug).

## Program

[`game_room_v1.py`](game_room_v1.py) — **phase 1** the whole zone ring (billiards hero + its
clearance, bar station with its stools, arcade row, lounge, poker, foosball, media console, trophy
cabinet, walls, door); **phase 2** the billiards rug, and nothing else; **phase 3** the wall layer
(photo grid, painting, wall TV, dartboard), the floor-to-ceiling window, and all three lighting
layers (billiards pendant, bar pendant cluster, ambient fill).

`workbench run skills/examples/game_room_v1.py --phase 1` builds the layout alone in ~1–2 min.

| Phase | Builds | Why it is separate |
|---|---|---|
| 1 | every floor anchor + the shell + the door | cheap; and in *this* room it is nearly the whole scene |
| 2 | the billiards rug | deliberately thin — the identity is already down (Lesson 6) |
| 3 | wall decor, window, lighting | the mood layer: moody walnut/charcoal/brass |

The **door is ungated** — it runs in phase 1 because its automatic clearance shapes the floor solve,
so deferring it would change the layout you validated. Same reasoning keeps the **bar stools** and
the **clearances** in phase 1: both are floor geometry the shell is sized around.

**Caveat (repeated because it matters):** the gated file has not been re-rendered. The phase split
above is the intent encoded in the program, not an observed result.

## What worked / gotchas

- **Composition all the way down.** No ingestion, no new DSL, no `get_whd()` fixups — five zones,
  each a group, each placed with one verb. When the pool is deep, spend your effort on the layout.
- **Every game piece retrieved cleanly** from a plain descriptive query ("a classic upright retro
  arcade video game cabinet", "an 8-foot billiards pool table with green felt and wooden frame").
  Contrast the categories that *don't* exist ([`casino.md`](casino.md)'s green-felt blackjack table)
  — a game *room* is one of the best-served room types in the pool.
- **The pendant light for the pool table is in the same pool as the pool table** ("a billiards table
  hanging light fixture with three shades over a pool table") — a purpose-built fixture, so
  `density=0` gives you the one right lamp in the one right place.
- **`facing=` at the wall slots does the orienting**, and `face()` inside the groups does the seating.
  The two are different tools: `facing=` snaps a group to a wall's direction; `face(obj, toward=…)`
  aims one child at an arbitrary target.
- Palette: **hunter-green walls, dark stone-tile floor, walnut/charcoal/brass.** The green velvet
  armchairs carry the accent as *props* — which is the durable way to hold a palette accent
  ([`classroom.md`](classroom.md): an accent the texture library can't express belongs on a prop, not
  smuggled into the wall string).

## VLM feedback we hit and how we resolved it

**Only partially recorded — this is a real gap in the example.** The original build predates the
convention of logging the loop, so there is **no vote train, no per-phase seed record, and no count
of render passes.** Do not read a convergence story into this file that isn't here. Two episodes
*were* preserved in the program's comments and in the previous version of this lesson, and they are
the two below.

| Feedback | Action | Result |
|---|---|---|
| Bar pendants rendered as **~15 globes strung across the back of the room** (`density=0.25` over a stool group spread in x *and* z) | Rebuilt the stools as one compact straight row (`place_rectilinear`) and dropped density to `0.18` | A tight cluster of ~5 globes directly over the counter (Lesson 2) |
| `RotationConstraint` flip-flopped "rotate the armchairs" ↔ "rotate the poker chairs", and emitted **"rotate bottom chair" four identical times** | **Declined all of them** — the render showed every seat correctly angled by `face()` | The layout was already right; the votes were noise (Lesson 5) |

**Not recorded, and therefore not claimed:** any `RoomProportions` vote train (the shipped
`modulate_scale=0.9` has no recorded justification), any `ObjectProportions` or `WallOverlap`
history, the number of render passes, or whether the build ever converged to a fully clean sheet.
**If you rebuild this scene, log the votes** — and mirror the notable ones into
[`../workflow/vlm_feedback.md`](../workflow/vlm_feedback.md).

## Manual constraints used

Three, all `Clearance`, all of them working space the defaults don't know about:

| Constraint | Why the default wasn't enough |
|---|---|
| `add_clearance(pool_table, distance=1.3, dir="all")` | **the cue stroke.** A pool table needs a full cue's draw on all four sides; nothing in the geometry says so. This is the constraint that sizes the room (Lesson 1). |
| `add_clearance(foosball, distance=0.5, dir="all")` | standing room for the players around the table. |
| `add_clearance(poker_table, distance=0.5, dir="all")` | a clear approach around the table — the chairs pull *out*, and their placed footprint doesn't reserve that. |

The door's clearance comes free from `CategoryClearanceConstraint`; the bar's service aisle comes
from the group structure, not a constraint (Lesson 4).

## Possible refinements (not blocking)

- **Run the gated program at each phase.** Phases 1, 2 and 3 of [`game_room_v1.py`](game_room_v1.py)
  have not been rendered since the retrofit. Until they are, the phase contract is unverified and
  Lesson 6 rests on reading the program, not on a render.
- **Log the VLM loop on that rebuild** — the missing vote history is the single biggest hole in this
  example (see above).
- **Check the back-wall interior camera.** The back-bar bottle cabinet is a *tall* piece near the
  back wall, and the interior wall cameras sit at ~1.4–1.5 m at each wall's centre: a fixture taller
  than that at a wall centre blinds its view **and** can hallucinate rotation flags on a correct
  layout ([`bakery.md`](bakery.md)). This scene's declined rotation storm (Lesson 5) is at least
  *consistent* with that failure mode — **unverified**, but it is the first thing to look at on a
  rebuild. If the view is blind, the fix is the one [`bakery.md`](bakery.md) prescribes: move the
  tall piece off the wall centre, not shrink the room.
- **The window.** The program uses `place_window_floor_to_ceiling("right_wall")`. The old "black
  window void" that made full-height glazing unusable was a **renderer bug and is fixed**
  ([`greenhouse.md`](greenhouse.md)) — so the foosball wall should glaze cleanly now. It has not been
  re-rendered to confirm it.
- **A wall cue rack** remains the one asset gap — an ingest candidate if anyone wants the billiards
  corner to read completely.
- The **air-hockey table** exists in `GameEquipmentRetriever` and is unused. A sixth zone would need
  the room to grow; the hero's clearance (Lesson 1) is the dial that decides whether it fits.
