# Lobby (corporate reception) — worked example ("Polished Corporate Lobby: Reception Anchor + Open Lounge")

## Status

Status: **built & VLM-clean pre-retrofit** (`scenes/lobby.py`, seed=13, converged over 6 render
passes — final compile `no rescale` / `no rotation` / `no wall overlap`).
[`lobby_v1.py`](lobby_v1.py) is that same program **phase-gated** (2026-07-13): `lint_program`-clean,
layout / pinned ids / seed / comments preserved verbatim.

**The retrofit has NOT been re-rendered.** No phase has been built since the gates went in, so the
phase-1 / 2 / 3 splits are **unverified** — the gating is a mechanical transcription of a converged
build, not a re-validated one. Treat the phase contract below as *intended*, and expect the first
`--phase 1` run to be the thing that confirms it. (`bedroom` hit exactly this and found that a
phase-1 room votes differently from the full room it was cut from — see
[Lesson 5 there](bedroom.md).)

## Prompt(s) this covers
- "a (corporate / hotel / office) lobby / reception / waiting area": a reception desk + a lounge of
  sofas & armchairs around a coffee table, tall plants, big art, floor-to-ceiling windows, a wall TV.
- Reach for [`waiting_room.md`](waiting_room.md) instead when the ask is a *clinic* waiting room —
  rows of linked chairs rather than a lounge cluster. It inherits this file's reception bones and
  swaps the lounge out; see the cross-link note at the end of the layout section.

## Plan summary (from the planner)
**"Polished Corporate Lobby: Reception Anchor + Open Lounge."** A reception desk anchoring the
service end; an open waiting lounge of sofas and armchairs around a coffee table; tall greenery; a
large colourful focal artwork; floor-to-ceiling glazing; a wall-mounted TV; warm flush disc lighting.
Palette: polished stone + warm wood + greige. The plan's stated goal — "clear sightlines, no
bottlenecks" — is what drives the entire layout, and it is the one thing v1 got wrong.

Retrieval was strong for the lounge and the decor (0.6–0.83 across the board) and **thin exactly where
the hero lives**: one wooden reception desk at 0.69, no marble, no corporate signage. A low top score
on the hero is itself the finding — see [Asset gaps](#asset-gaps).

## The layout idea: RECEPTION ANCHOR + an OFF-CENTRE LOUNGE (the walk-up lane)

The **single-room, zoned** pattern — the same bones as
[`executive_office.md`](executive_office.md) (storage backbone + work/lounge zones), retuned for a
room whose users are *strangers walking in*. Two zones, one lane between them.

| Wall / slot | Job |
|---|---|
| back **third** | the reception **hero** — a `WorkstationGroup` with an **inverted** desk, dropped with `place_on_back`, **not** `place_on_back_wall` |
| back wall | the colourful focal artwork behind reception; the lamp-lit **console vignette** in the left corner; a tall plant in the right |
| left wall | floor-to-ceiling glazing — **the only wall with no furniture**, so it stays the light wall |
| right wall | the quiet wall: greenery beside the lounge + a secondary B&W print |
| front wall | the entrance. Door **left** (moved off-centre to clear the TV), TV centre, water cooler in the left corner |
| front-**right** | the waiting lounge cluster |
| centre | **deliberately open** — and it is not empty floor, it is the **walk-up lane** |

**The move that makes it read: the lounge is pushed to `place_on_front_right`, not `place_on_center`.**
v1 centred it, and the lounge *walled the reception desk off behind the seating* — you had to weave
between two sofas to reach the person you came to talk to. Front-right leaves an open **diagonal
walk-up** from the entrance to the desk. A lobby is a room you *cross*; a layout that is beautiful in
plan and unwalkable in practice has failed the brief.

This is why the open centre must survive the shrink votes. An occupancy metric reads a circulation
lane as "empty floor" every single time — the same misread [`corridor.md`](corridor.md) and
[`garage.md`](garage.md) have to defend against, and the reason `modulate_scale` landed at **0.9**
rather than the 0.8 the VLM asked for.

**Inheritance.** [`waiting_room.md`](waiting_room.md) is this file's closest relative and takes the
reception half wholesale — `WorkstationGroup` + `set_rotation(180)` + `place_on_back(facing="back")`,
the flanking greenery, the focal print behind the desk. What it does **not** inherit is the lounge:
it swaps the `AroundGroup` cluster for two packed `GridGroup` seat banks on the long walls, and that
single substitution is what turns a *lounge* into a *waiting room*. It also **repays the debt** with a
lesson this file did not know it needed — see [the panoramic-art footnote](#gotchas-inherited-back-from-waiting_room).

## Pinned assets (audited previews)

| Role | id | Why pinned |
|---|---|---|
| reception desk **(hero)** | `custom/cffdedd8…` | **ingested** — wood frame + dark marble panels. Nails the "polished stone + warm wood" palette the pool could not serve |
| sofa | `hssd/05206ad5…` (0.82) | pinned to **dodge sectionals** — the generic sofa query keeps returning L-shapes, which `place_rectilinear` cannot use |
| armchair | `future/1c8dfc96…` | grey bouclé tub accent chair |
| coffee table | `future/40860cf0…` | + `width=0.95` (VLM voted the first one ×0.8) |
| side table | `future/76d7a78e…` (0.76) | the console vignette's anchor |
| tall plant | `hssd/08d9ae37…` (0.83) | |
| rug | `hssd/249bbdc7…` | pinned **flat** — avoids the upright-slab `place_rug` warning |
| focal art | `hssd/5e9d4d4d…` | large colourful abstract — the stand-in for the signage gap |
| secondary art | `hssd/2b54eedde…` | B&W abstract, right wall |
| wall TV | `future/ad98c113…` (0.67) | |
| water cooler | `hssd/b77968f3…` | **auto-scale metadata is bad** → must pass `width=0.35` or it arrives wrong-sized |
| table lamp | `hssd/487fc518…` | modern black cylinder |
| books | `hssd/d0e0f0b5…` | reused on both the coffee table and the console |

## Asset gaps
- **Reception desk — the hero, and the pool has one (wooden, 0.69, no marble).** Filled by
  **ingest**; see the lesson below.
- **Branded signage / corporate logo — 0.44–0.52, and left UNFILLED.** There is no clean corporate
  logo mesh and no per-wall texture path to fake one. The "focal wall" is a large colourful abstract
  instead. Honest outcome: *the plan asked for branding and the scene does not have branding.* An
  agent rebuilding this should not waste a gate hunting for it.
- Everything else the plan asked for exists. Feed reusable gaps into
  [`../workflow/creative_asset_gaps.md`](../workflow/creative_asset_gaps.md).

## Lesson 1 — a desk with a monitor on it → use `WorkstationGroup`, stop patching `face()`

**The lesson this example exists for.** "Monitor seated on a desk, facing the wrong way" recurred for
**three renders** while the reception was a hand-rolled `RelativeGroup` + `place_on_top(computer)` +
a per-scene `face()`. The VLM kept voting `rotate desktop computer by 180`, and
`face(computer, toward="<wall>")` was fragile twice over: the all-in-one mesh's *geometric* front is
opposite its *screen*, and facing toward a **wall** snapped inconsistently as the group drifted under
the solver. It appeared fixed in v4 — then **regressed in v5** the moment the group shifted.

**Fix once and for all: build the desk unit as a `WorkstationGroup`.** It seats the computer with the
DSL's own `place_on_top` and then faces the screen at the **chair** — an actual object, not a wall —
deterministically, every build. v6 came back fully `no rotation`.

> *Recurring facing votes on a desk monitor are not a rotation bug. They are a "you used the wrong
> group" bug. Reach for `WorkstationGroup`.*

[`computer_room.md`](computer_room.md) generalises the same group into a grid of eight stations, and
[`executive_office.md`](executive_office.md) uses it for the single power desk. This file supplies
the twist neither of them needs:

## Lesson 2 — a reception desk is an INVERTED workstation

`WorkstationGroup` assumes a **normal** desk: the working front (+Z) faces the operator, so the nice
front and the operator are on the *same* side. A reception desk is the exact opposite — the **display
front (the marble transaction counter) faces the customers**, while the **staff and the monitor sit
behind it**. Two moves reconcile it, and both are needed:

```python
with scene.WorkstationGroup() as reception:
    desk = scene.AddAsset("a modern reception desk with a marble front", asset_id=DESK, width=2.2)
    desk.set_rotation(180)                     # marble -> customers; open staff side becomes +Z
    reception.set_anchor(desk)
    reception.place_chair(scene.AddAsset("a black leather office task chair on casters"), gap=True)
...
room.place_on_back(reception, facing="back")   # operator to the back wall -> receptionist faces the room
```

1. **`desk.set_rotation(180)` on the anchor.** An anchor's own rotation is a **local offset that rides
   along** when the group is later rotated for `facing=` — so it survives placement instead of being
   overwritten. This is the general property that makes "pre-rotate the anchor" a safe idiom at all.
2. **`place_on_back(..., facing="back")`, NOT `place_on_back_wall`.** A wall-flush desk leaves the
   receptionist standing **inside the wall**. `place_on_back` puts the desk in the back *third* and
   leaves staff floor behind it. Same "power layout" as `executive_office.md`'s `facing="back"`.

Result: marble → customers, screen → staff (customers see the monitor's back, exactly as in a real
lobby), chair tucked behind. [`waiting_room.md`](waiting_room.md) lifts this pair of moves unchanged.

## Lesson 3 — `AroundGroup.place_rectilinear` IS the waiting cluster

Two 3-seat sofas on the long sides + two accent armchairs on the short sides, around a coffee-table
**anchor**, in **one call** — and every seat is auto-faced inward. No per-seat `face()`, no manual
symmetry bookkeeping:

```python
with scene.AroundGroup(sparsity=0.4, jitter=0.3) as lounge:
    lounge.set_anchor(scene.AddAsset("a low minimalist wood coffee table", asset_id=COFFEE, width=0.95))
    lounge.place_rectilinear(longer_side1=[sofa_a], longer_side2=[sofa_b],
                             shorter_side1=[chair_a], shorter_side2=[chair_b])
```

Two things make it work in practice:
- **The anchor is the table**, so the phase-2 `place_on_top` (vase + books) and the `place_rug` land
  on/under the *table* — not on a sofa cushion. That is the [`living_room_cozy.md`](living_room_cozy.md)
  v3 trap (`place_on_top` **always** targets the group's anchor), and the reason the gate must sit
  **inside** the `with` block.
- **The sofas must be pinned straight.** A retrieved "sofa" is very often a **sectional**, and an
  L-shape on a rectilinear long side breaks the symmetry the pattern is entirely made of.

Because the seats auto-face inward, a VLM vote to "rotate the front sofa toward the coffee table" is
**noise** — see the declined votes below.

## Lesson 4 — asset-first kickoff: stress-test retrieval, THEN ingest the hero

This is the reference example for **running a retrieval stress test before writing any layout code**.
Retrieve every planned asset, read the top similarity *and* look at the visual pick:

| Asset | sim | verdict |
|---|---|---|
| sofa / plant / side table / vase / reception chair / lamp | 0.72–0.83 | strong |
| coffee table / armchair / art / rug / flush light / wall TV / books | 0.57–0.71 | usable (rugs always land ~0.6) |
| water cooler | 0.62 | usable — but the **auto-scale metadata is bad** → set `width=0.35` |
| **reception desk** | 0.69 | **one wooden option, no marble → ingest gap** |
| **branded signage / logo** | 0.44–0.52 | **gap, left unfilled** |

The score is a *retrieval* score, not a *fitness* score: 0.69 on the desk was not "good enough", it
was "one mesh, and it is the wrong material for the entire palette". **The hero is where a thin
library hurts most, and it is the only place worth paying an ingest for.**

The user supplied three `.glb`s → ingested with:

```
python -m IDSDL.ingest reception_tables.zip --manifest m.json
```

The manifest overrides `description` (which **drives the retrieval embedding** — this is the lever
that makes an ingested mesh findable), plus `placement=floor` and `scale` = real-world width in m.
Hero pinned = **`custom/cffdedd8…`** (wood frame + dark marble panels); two alternates (curved,
L-shaped) ingested alongside it.

**Verify the ingest PREVIEW before you trust the scale.** The auto-rendered preview — not the vertex
bbox — is what tells you the mesh is right. Full procedure in
[`../workflow/asset_ingest.md`](../workflow/asset_ingest.md).

## Lesson 5 — `add_lighting` count math: `N = 1 + (max_lights − 1) × density`

…where `max_lights ≈ ceiling_area / fixture_footprint`. A **small** flush disc at `density=0.2` in a
big lobby exploded to **~250 dots** in the ceiling. Both halves of the fix are needed:

1. **Enlarge the fixture** — `modulate_scale=2.2` grows the footprint, which *shrinks* `max_lights`.
2. **Drop the density** — `0.03`.

→ a clean ~9-fixture grid. **Energy is a fixed 500 W split across N**, so fewer fixtures is **not**
dimmer — the instinct to keep the count high "for brightness" is exactly backwards.

And steer the **mesh** by wording, not by hope: `"square LED panel"` retrieved a *spotlight on an arm*;
`"flat round LED flush mount"` retrieved the clean disc. Mirrored into
[`../workflow/vlm_feedback.md`](../workflow/vlm_feedback.md) as `[[lighting-footprint]]`.

## Program

[`lobby_v1.py`](lobby_v1.py) — the converged `scenes/lobby.py`, phase-gated.

| Phase | Builds | Why it is separate |
|---|---|---|
| 1 | the reception `WorkstationGroup` (desk + chair), the lounge cluster, the console anchor, the room shell + walls, **the door** | cheap (~1–2 min). This is where the *zoning* is validated: is the walk-up lane actually clear? |
| 2 | surface + floor dressing — the computer + desk plant, the vase/books on the coffee table, the rug, the lamp+books on the console, the tall plants, the entrance water cooler | the identity layer |
| 3 | the focal + secondary art, the wall TV, the floor-to-ceiling glazing, `add_lighting` | the mood layer |

`workbench run skills/examples/lobby_v1.py --phase 1` builds the layout alone.

Two conventions worth naming, because both are load-bearing:
- **The door is UNGATED** — it runs in phase 1. Its automatic clearance *shapes the floor solve*, so
  deferring it to phase 3 would change the very layout phase 1 exists to validate. (Its `position="left"`
  is also not cosmetic: it clears the front-centre TV.)
- **Every `place_on_top` gate sits INSIDE its `with` block.** Gated outside, the op is never recorded
  on the group — the loop stays clean, the counts still increment, and the prop is simply **GONE**.

## What worked / gotchas
- **`place_on_back`, never `place_on_back_wall`, for a staffed desk.** Repeated because it is the
  single most copyable line in the file.
- **The console vignette: give an accent table a JOB.** A bare side table in a corner reads as a
  mistake. Side table + lamp + books = a deliberate lamp-lit vignette. Cheap, and it fills a dead
  corner without adding another piece of furniture to the walk-up lane.
- **Floor-to-ceiling window: `curtain=None`.** *(As recorded at build time:)* with no exterior
  environment the pane was a black night void, and every curtain/blind query rendered as **billowing
  ghost drapes**. Bare glazing read as a clean glass curtain wall (mullions + dark glass).
  ⚠️ **This may now be stale.** [`waiting_room.md`](waiting_room.md) records a **2026-07-12 renderer
  fix** after which `place_window_*(curtain=None)` gives real daylight and "the old black-night-void
  workarounds are obsolete". This scene has not been re-rendered since. The `curtain=None` call is
  still correct; the *reason* in the comment may no longer be.
- **Pin the rug FLAT** — an upright-slab rug mesh trips a `place_rug` warning.
- **`modulate_scale=0.9`**, arrived at by *declining half* of a `rescale room by 0.8` vote. See below.

### Gotchas inherited back from `waiting_room`
[`waiting_room.md`](waiting_room.md) built the same reception anchor and found a trap this scene has
but never diagnosed: **a back-centre print behind a reception desk is ALWAYS crossed by the monitor.**
Wall art centres at ~1.5 m; a counter (1.10 m) with a monitor on it tops out at ~1.6 m. Nothing
flags it — the automatic wall-object clearance pass only slides **floor** objects out of a wall
item's span, never a `place_on_top` item, and there is no `bottom=` lift on the wall-hung path.
The fix is **aspect, not size** (wall scaling is uniform, so widening a portrait print just makes it
taller): hang a **panoramic**.

This file's focal art is hung `place_on_wall_back_center` at `width=1.8` directly behind the desk, so
it is a **candidate for exactly that collision**. It was never reported as a defect in the six render
passes — but the collision produced **no VLM signal in `waiting_room` either**, which is precisely
why it went unnoticed there for a whole version. **Check it by eye on the next render.** Flagged
honestly rather than silently "fixed": changing the pin would be re-designing a scene this retrofit
is not authorised to re-render.

## VLM feedback we hit and how we resolved it
The loop that produced `scenes/lobby.py`, as recorded at build time (six passes):

| # | Vote | Action | Result |
|---|---|---|---|
| v1 | `rescale room by 0.9` | `modulate_scale` 1.15 → 1.0 | accepted |
| v2 | `rescale coffee table by 0.8` | `width` 1.2 → **0.95** | accepted |
| v3 | `rotate computer / chair by 180` | patched with a room-level `face(..., toward=wall)` | *appeared* fixed in v4 |
| v4 | `rotate the front sofa to face the coffee table` | **DECLINED as noise** | the rectilinear sofas already face the table in **every** render — the seats are auto-faced inward by `place_rectilinear`, so the vote is describing something that is not true. Same noise vote [`executive_office.md`](executive_office.md) declined |
| v5 | the v3 facing fix **REGRESSED** when the group shifted | rebuilt reception as a `WorkstationGroup` (Lesson 1) | v6 fully `no rotation` |
| v5 | `rescale room by 0.8` (the corner lounge left the centre "empty") | **half-declined** → `modulate_scale` 1.0 → **0.9** | the "empty" centre is the walk-up lane. Shrinking to 0.8 would have closed the lane to buy an occupancy number |
| v6 | — | — | **converged**: `no rescale` / `no rotation` / `no wall overlap` |

Two of these are worth reading as a pair. **v3→v5 is the cost of patching a symptom** — two renders
spent on a `face()` hack that a structural group would have made impossible. **v4 and the v5 room vote
are refuted votes**, and the arithmetic that refutes them is different in each case: v4 contradicts
what `place_rectilinear` provably does, and the room vote contradicts what the *plan* asked for
("clear sightlines, no bottlenecks"). A vote that argues with the brief loses.

**Lighting and the window void are VLM-blind** — neither the ~250-dot ceiling nor the ghost drapes
produced any vote. They were caught by *looking*. (The general rule
[`waiting_room.md`](waiting_room.md) states outright: geometry is perfect, so the loop is silent;
"that reads wrong" is semantics, and semantics is an eye catch.)

**Not carried over:** no VLM pass has been run against the **phase-gated** program. Nothing in the
table above was re-observed after the retrofit.

## Manual constraints used
**None.** Automatic overlap/bounds + `CategoryClearanceConstraint` on the reception desk + the door's
auto-clearance were sufficient. The clear diagonal walk-up from the entrance to the desk — the plan's
"clear sightlines, no bottlenecks" — is achieved **by zoning** (`place_on_front_right`), not by a
constraint. That is the cheaper move and it is worth reaching for first.

## Possible refinements (not blocking)
- **Run the gated program.** Phase 1 first — it is the cheap check that the walk-up lane survives, and
  it is the only claim in this file that has not been verified since the retrofit. Expect the phase-1
  and phase-2 rooms to look under-filled and expect a shrink vote; per [`bedroom.md`](bedroom.md), a
  room-size vote on a half-dressed room is voting on a room that does not exist yet.
- **Check the focal art against the desk monitor** (see the inherited gotcha above). If it is crossed,
  the fix is a panoramic pin, not a bigger print.
- **Re-examine `curtain=None`** against the 2026-07-12 renderer fix. The call is probably still right;
  the *comment* explaining it is probably now wrong.
- **The signage gap is still open.** A corporate lobby without a logo is the one place this scene
  visibly misses its brief.
