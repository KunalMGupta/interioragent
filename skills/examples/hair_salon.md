# Hair salon — worked example ("Luxe Row-Station Salon Spine")

The first scene built end-to-end with the **asset-first kickoff** *and* a **new placement group**,
and the reference example for the three-phase build in `../workflow/coarse_to_fine.md`. It is also
the library's only worked example of a **custom motif group** (`MirrorStationGroup`, in
`IDSDL/groups_extra.py`) — most of that module has no example coverage at all, so read
[Lesson 1](#lesson-1--when-a-relationship-is-unrepresentable-it-earns-a-group-mirrorstationgroup)
even if you are not building a salon.

Read alongside `../workflow/coarse_to_fine.md`, `../workflow/asset_selection.md` (the kickoff), and
`../add-placement-group/SKILL.md` (the group).

## Status

Status: **built & iterated as `scenes/hair_salon.py` (seed=77)** — asset-first kickoff, five ingested
glbs, layout fixed off render feedback (see the VLM section, which is real and was recorded).
[`hair_salon_v1.py`](hair_salon_v1.py) is that program **phase-gated** (2026-07-13):
`lint_program`-clean, layout / pinned ids / seed / comments preserved byte-for-byte where the gate
did not touch them.

**It has NOT been re-run or re-rendered since the retrofit, so the phase splits are UNVERIFIED.**
No claim is made here that phase 1, 2 or 3 builds — only that the program lints and that the gating
is a mechanical transcription of the phase map the original program's own docstring already carried.
The original build's final "clean" verdict, its render-pass count, and its per-pass votes were never
written down beyond the four items below; do not read this file as a converged-render record.

**Which program was promoted:** `scenes/hair_salon.py`. `scenes/work/salon_pretty.py` is the *same
program* — `diff` shows only the scene name (`HairSalonPretty`), the export name
(`salon_pretty.blend`) and the comment wording; identical seed, identical pins, identical placement
calls. The `.md`'s old code excerpts were copied from `salon_pretty.py`, so its lessons describe both.
`scenes/hair_salon.py` was chosen because it is the later of the two and already annotates every
statement with the phase it belongs to — the retrofit is that annotation made mechanical.

## Prompt(s) this covers
- "a pretty hair salon" / styling-row salons, barbershops, blow-dry bars, nail bars.
- Anything with a **repeated station whose fixture is on the wall** — gym mirror walls, vanity runs,
  dressing rooms, grooming benches (see [`locker_room.md`](locker_room.md), which inherits the group).

## Plan summary (from the planner)
"Luxe Row-Station Salon Spine." Palette **blush + brass + concrete**. The room wants to be **wide and
shallow** (real salons are). The hero is a **styling row**: a line of identical stations along one
long wall, each = a chair facing a wall mirror with a console under it. The opposite long wall carries
the **reception** and a blush-velvet **waiting nook**; the two short walls stay light (backwash row,
retail shelf, and both openings).

## The layout idea: MOTIF-GROUP SPINE — a repeated custom station, rowed and seated FLUSH on the long wall

The pattern is: **build the unit that the room is made of, once, as a group; row it; press the row
into the wall.** `computer_room` and `classroom` do this with an existing group; hair_salon is the
case where **no existing group could express the unit** and one had to be written (Lesson 1). That is
what makes it the reference for motif builds.

The second half of the pattern is that **the room's shape falls out of where you put the mass**. The
`RoomGroup` sizes each wall from what sits on it, so:

| Wall | Job | Why |
|---|---|---|
| back (**long**) | the styling row — 5 stations, flush | the hero; five mirrors in a line is the one image that says *salon* |
| front (**long**) | reception (left) + waiting nook | the opposing long load — **this is what keeps the room wide**, not a dial |
| left (short) | retail shelf (front end, by reception) + the **door** | kept light on purpose |
| right (short) | the backwash pair (center/front) + the **window** | light, and deliberately *away* from the styling row: a client lying back into a bowl is a separate zone |
| centre | **open** | the working floor between the row and the desk |

Load the two long walls, keep the two short walls light → wide and shallow. Load all four evenly and
you get a square room and a salon that reads like a waiting area.

## Pinned assets (audited previews)

| Role | id | Why pinned |
|---|---|---|
| styling chair | `custom/59a3f803…` | an **ingested** glb (no barber chair exists in the pool). Pinned because the visual picker kept drifting to a **low tub chair** for "a salon styling chair"; the pin fixed it durably |
| waiting tub chair | `hssd/3b522b2a…` | pinned in the source build; **the reason was never recorded**. It is the only seat carrying the blush of the palette, which is the likely motive — treat the pin as load-bearing until someone re-renders without it |

Everything else in the program is retrieved **by query** through the curated `HairSalonRetriever`
pool (`assets/hair_salon.json`, 186 assets kept of 493), which merges a **general-furniture
fallback** so a query like "a blush accent chair" still reaches the general pool when the salon pool
lacks it. Note the consequence: **four of the five ingested customs (backwash, arched mirror, neon
sign, retail shelf) are NOT pinned** — they reach the scene only by winning their query. That is a
fragility, not a design (see Possible refinements).

## Asset gaps

The salon is the sharpest case in the library of "**the iconic fixtures of a commercial category are
exactly the ones the home-furniture dataset lacks**" (the audit is in `scenes/work/hair_salon.md`):

- **Barber / styling chair** — *absent*. Queries fall back to dining / office / massage / medical
  chairs; rewording ("barber chair with hydraulic base and headrest") does **not** rescue it — a
  confirmed recall gap, not a phrasing gap. → **ingested**.
- **Backwash / shampoo unit** — *absent*. The pool has a bare basin, or a medical exam chair, never
  the combined unit. → **ingested**.
- **Ornate arched mirror, neon sign, retail display shelf** → **ingested** (the last two are
  cross-category: casino wants neon too).
- **Hooded / bonnet dryer** — *absent, and still absent.* It was on the backlog and never landed;
  the scene simply does without it.
- **Reception desk** — present but the picker *rejected* it: the correct curved reception desk
  (`hssd/7379d88…`, sim 0.674, **rank 1**) was dropped for a plain flat-top office desk (0.469), by
  over-applying the "no raised second surface" desk rule — even though "reception" is a documented
  exception in `asset_selection.md`. The program works around it by **scaling the chosen desk up to
  ≥2.2 m wide** rather than pinning. *Always view the #1 preview, not just the chosen one — a pin is
  often one rank away.*
- **Retail shelf** — the general retriever returns a **wall-mounted floating bracket** shelf, but the
  scene places it as floor furniture (`place_on_left_wall_left`). Match the asset's **mounting class**
  to the placement verb or it floats.

## Lesson 1 — when a relationship is unrepresentable, it earns a group: `MirrorStationGroup`

"A mirror on the wall + a chair facing it + a console under it" could not be said in the DSL:
wall-mounting was `RoomGroup`-only and `RelativeGroup` is floor-only. That is the bar for a new group
— **not** "this scene is fiddly", but *this relationship cannot be expressed*. It generalised
immediately (gym treadmill + mirror, vanity + mirror, dressing rooms), which is the second half of
the bar. See `../add-placement-group/SKILL.md`.

**How it works.** It builds one station in a local frame whose **+Z is the viewing axis**: the anchor
faces +Z, and the mirror / counter / shelf sit on the +Z (wall) side facing back at the anchor. Drop
N of them into a `GridGroup` row, place the row flush on a wall, and every station arrives correct.

| Slot | Meaning |
|---|---|
| `set_anchor(obj)` | **required** — the floor item (chair / treadmill / vanity) |
| `place_mirror(m, height=…, width_ratio=…)` | **required** — sized to the *station width* (uncapped), not to a wall-third |
| `place_counter(c)` | optional console under the mirror; **capped to `COUNTER_MAX_HEIGHT` = 1.0 m** (a styling counter is desk-height, not a bar table) |
| `place_shelf(s, items=[…])` | optional thin floating shelf (≤0.30 m) with decor seated on it |
| `place_beside(o, side="right")` | optional side slot — the rolling trolley / dresser |

Two behaviours worth knowing because you cannot get them any other way:
- **It auto-fits under the ceiling.** The whole station's top is held at/under `max_top` (2.7 m by
  default, under a ~3 m ceiling) — the mirror is shrunk if a tall console pushed it up. This is the
  fix for the "mirror top breaches the ceiling" vote below.
- **It stands the mirror `MIRROR_WALL_OFFSET` (0.05 m) proud of the wall.** A wall-coplanar mirror
  shows no reflection and vanishes into the paint; standing it proud makes the glass read and casts a
  soft shadow.

**`place_mirror` is required before compile** (the group raises otherwise) — which is why, in the
phase-gated program, the mirror is **ungated**. It is not wall decor; it *is* the station.

> A **row of mirrors alone** needs no group — `place_on_wall_freeform("back_wall", mirrors)` already
> spaces and scales N wall mirrors. The group is for the chair+console+mirror *relationship*.

**Inherited by [`locker_room.md`](locker_room.md)**, which sharpens it: a plain
`place_on_wall_left_center` mirror is capped to a **wall-third**, so over a two-vanity grooming run it
covers only one sink — `MirrorStationGroup` sizes its mirror to the anchor instead, so a mirror lands
over *each* vanity. Read its **facing exception** too: because the mirror sits on the station's +Z
side, the row takes `facing=<the wall it sits on>` — which is exactly why this scene passes
`facing="back"` on the back wall (the opposite of what plain furniture wants).

## Lesson 2 — the room's ASPECT RATIO is a consequence of which walls you load

Nothing in this program asks for a wide room. It comes out wide because both **long** walls carry a
long load (5 stations / reception + nook) and both **short** walls carry almost nothing. The
`RoomGroup` auto-sizer sums what each wall is holding; the room shape is a *consequence of asset
distribution*, not a separate dial.

[`laundry_room.md`](laundry_room.md) is the transferable statement of this and should be read next:
it works out the actual arithmetic (the sizer sums column-widths and row-depths, and a **side-wall**
item pays its *width* in room *depth*), and it shows the failure mode — scattering pieces across four
rows auto-sized a hall twice the size of its furniture. [`corridor.md`](corridor.md) is the extreme
version: both long walls loaded, short walls bare, and the empty centre lane *is* the room.

`modulate_scale=0.92` here is a **nudge**, not the mechanism — it went 0.78 → 0.92 late, to answer a
"room reads a touch empty" note. Reach for the slots first, the dial second.

## Lesson 3 — flush, not gapped: seat a wall row with `place_on_*_wall_*` + `facing=`, never `place_on_*`

The **#1 layout fix in this scene.** `room.place_on_back(spine)` leaves a wall-row-deep gap between
the row and the wall — and because the station mirrors live at the row's back plane, they end up
**floating in mid-air a foot off the wall**. `room.place_on_back_wall_center(spine, facing="back")`
seats the row ON the wall.

And **`facing=` already does two jobs — do not stack `room.face()` on top of it.** It sets the
rotation *and* tells the auto-sizer how deep the back-wall row is. The original program carried a
post-layout `room.face(spine, toward="back_wall")` that merely re-snapped the same orientation; it
was removed. (`locker_room` states the general rule: long rows go flush-on-wall or down the centre,
never `place_on_<side>`.)

## Lesson 4 — a deterministic group should set `self.vlm_solver = None`

Each `MirrorStationGroup` is hand-laid-out and auto-fitting: identical every time, with no proportion
decision left to make. The per-instance VLM proportion check therefore **rendered the same station
five times** and starved the render budget of the views you actually wanted. Disabling it inside the
group cut the build from **~35 renders to ~15**. The room-level VLM still vets the whole scene.

If you write a group whose layout is fully determined by its inputs, turn its solver off. If you write
one that makes a judgement call, leave it on.

## Lesson 5 — the ingest trap: an off-center mesh sinks into the floor

The ingested chair and backwash were authored off-center and sat **0.186 m sunk into the floor**.
Off-center mesh origin ⇒ floor sink/float is the **#1 ingest trap**. Ingest now auto-centers (see
`asset_selection.md` → ingest contract), and `IDSDL/lints.py`'s `lint_floaters` catches the residue
post-compile — its advice is the right one: **swap the mesh, don't compensate.**

The sibling trap, if you ingest a *scan* rather than a modelled prop, is in
[`clothing_store.md`](clothing_store.md): the retrieval `scale` on an ingested asset is a **guessed
width**, which silently miniaturises large fixtures.

## Lesson 6 — when the render LOOKS wrong, verify numerically before you "fix" it

"The stations look like they're in the middle of the room / overlapping" — they were not. It was a
**corner-perspective illusion**, which a wide-shallow room is especially good at producing. A numeric
dump (mirror z ≈ 0, no AABB overlap) proved the geometry was right, and the "fix" was to change
nothing. A wrong fix applied to a correct layout is how a converged scene gets broken.

## Lesson 7 — the canonical coarse-to-fine build, and how the gate transcribes it

This is the scene `coarse_to_fine.md` was written from. The three passes, and what each one is *for*:

- **Phase 1 — major assets, proportions.** Only the big pieces, distributed to force the room shape
  (Lesson 2). *Check:* the room is visibly wide/shallow; the 5 stations sit flush (no floating
  mirrors); no overlap — **verified numerically**, not by eye (Lesson 6). Every layout bug in this
  scene's history was caught here.
- **Phase 2 — surface & floor detail.** What sits on / beside the anchors: the per-station trolley
  (`place_beside`), the on-desk vase, the plant beside the desk, the magazine rack, the rug under the
  nook. *Check:* nothing floats or clips; small-item proportions clean.
- **Phase 3 — walls, decor, openings.** The fashion portrait, the neon sign, the window + curtain.
  Cheapest impact, last — but note it is this layer that makes the room read as a **beauty** salon
  rather than a barbershop. *Check:* `WallOverlapConstraint` (art not colliding with door/window).

Two places the gated program **deviates** from the original's own phase note, and why:

1. **The brass pendants (`add_lighting`) moved from phase 2 → phase 3.** `add_lighting` is the mood
   layer by the phase convention in `IDSDL/phases.py`, and lighting is not a floor-solve input.
2. **The receptionist chair stayed in phase 1**, though the original listed it as a phase-2 detail. It
   is a *floor anchor*: it sets the reception cluster's depth on the front long wall, and that
   footprint is what holds the room wide (Lesson 2). Deferring it would change the phase-1 room.

The door is likewise **ungated** — its automatic clearance shapes the floor solve, so building it in
phase 3 would mean phase 1 validated a layout that the final room does not have.

## Lesson 8 — the palette is three texture strings and one pin

"Blush + brass + concrete" survives entirely in: `floor_texture="polished concrete floor"`,
`wall_texture="soft blush pink"`, the *word* "brass" inside three retrieval queries (pendant, side
table, magazine rack), and the pinned blush velvet chair. There is no palette API — **the strings are
the palette**, and the cheapest identity in the whole program.

*Unverified caveat, flagged honestly:* [`nursery.md`](nursery.md) later found that a pastel wall
texture fails in two different ways — "blush pink wall" renders as pink **tiles**, and "pale pink
plaster" renders **salmon**. This scene's string is `"soft blush pink"`, one word away, and its build
recorded no complaint about it. I have **not re-rendered**, so I cannot tell you whether this string
lands or whether the original build simply never questioned it. If you rebuild, look at the wall.

## Program

[`hair_salon_v1.py`](hair_salon_v1.py) — phase 1 the floor anchors (the 5-station spine flush on the
back wall, the backwash pair, the retail shelf, the reception desk + receptionist, the waiting nook's
table and blush pair, the walls and the door); phase 2 the surface dressing (per-station trolleys,
the plant, the on-desk vase, the magazine rack, the rug); phase 3 the wall decor (fashion portrait,
neon sign), the window + curtain, and the two brass pendants.

`workbench run skills/examples/hair_salon_v1.py --phase 1` is intended to build the layout alone in
~1–2 min. **Intended** — see Status: the gated program has not been run.

Note the station **mirrors are in phase 1**, not phase 3. `MirrorStationGroup.place_mirror()` is
required before compile, and the mirror's ceiling auto-fit is one of the things phase 1 exists to
check. A station without its mirror is not a cheaper station; it is a `ValueError`.

## What worked / gotchas

- **Long strips on long walls = wide room.** (Lesson 2.)
- **Flush, not gapped** — `place_on_back_wall_center(spine, facing="back")`. (Lesson 3.)
- **`facing=` already does the job; `room.face()` on top of it is redundant.** Don't stack both.
- **Per-station = one `MirrorStationGroup`, rowed by `GridGroup`.** An earlier attempt (chair anchor +
  `place_on_front_adjacent(counter)` inside a `RelativeGroup`) made the **chairs vanish**. The
  dedicated group lays each station out deterministically and survives the row + flush placement.
- **Pin the hero the picker drifts on** (the styling chair) — and pin it by *id*, not by rewording.
- **Scale the reception desk up to a floor (`≥2.2 m`) rather than trusting the pick.** The desk is the
  one object a client walks up to; a 1.4 m office table under a fashion portrait reads as an
  afterthought. `get_whd()` → factor → three `scale_only_*` calls, proportionally.
- `GridGroup(sparsity=0.4)` for the spine: stations need elbow room between them; a tight row reads
  as a bench.

## VLM / layout feedback we hit and how we resolved it

**This is the recorded loop — four items, and it is all that was written down.** No vote counts, no
per-pass render log and no final "clean" verdict were kept. That is a gap in this example, and the
reason the Status line above will not claim convergence.

| feedback | action | result |
|---|---|---|
| "mirror top breaches the ceiling" (a tall console had pushed the mirror to ~3 m) | fixed **in the group**, not the scene: console capped to desk height + mirror shrunk so its top ≤ `max_top` (≈2.7 m under a 3 m ceiling) | every station now fits under any standard ceiling, in every scene that uses the group |
| "chair sunk into floor (−0.186 m)" | off-center ingested mesh → recentered the glb | ingest now auto-centers; `lint_floaters` catches the class (Lesson 5) |
| "stations look like they're in the middle of the room / overlapping" | **declined.** A numeric dump (mirror z ≈ 0, no AABB overlap) proved the geometry correct — a corner-perspective illusion in a wide-shallow room | nothing changed; the vote was wrong (Lesson 6) |
| "room reads a touch empty" | `modulate_scale` 0.78 → 0.92 (a smaller room for the same furniture) | minor; accepted |

Worth noticing that the two *accepted* votes were both fixed **inside the group / the ingest
contract**, not inside the scene — a motif group is where a fix becomes permanent for every scene
that borrows it.

## Manual constraints used

**None.** The automatic overlap/bounds constraints plus the group's deterministic layout sufficed.
The door's clearance comes free from `CategoryClearanceConstraint`.

## Possible refinements (not blocking)

- **Run the gated program at each phase and record what happens.** Phases 1–3 are untested since the
  retrofit; this is the one thing standing between this example and a clean Status line.
- **Pin the four unpinned ingested customs** (backwash, arched mirror, neon sign, retail shelf). They
  currently reach the scene only by winning their retrieval query against a merged fallback pool — a
  drifting picker silently swaps a salon for a bathroom.
- **Pin the curved reception desk** (`hssd/7379d88…`, rank 1, rejected by the picker) and drop the
  `≥2.2 m` scale-up, or keep both. Unverified which asset the query resolves to *now* — the audit in
  `scenes/work/hair_salon.md` predates the curated pool.
- **The hood dryer never landed.** It is the third iconic salon fixture and the room does without it;
  ingesting one would strengthen the styling row's flank.
- **Look at the blush wall** (Lesson 8) and at what the "retail product display shelf" query actually
  returns — the audit says a *wall-mounted* bracket shelf, which would float in a floor slot.
