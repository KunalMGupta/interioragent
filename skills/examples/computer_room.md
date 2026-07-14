# Computer room — worked example ("Front-Facing Modular Computer Lab")

## Status

Status: **built & converged as `scenes/computer_room.py`** (seed=11) — the original full build was
rotation-clean, no wall overlap, room proportions converged (`no rescale` / `no rotation` at every
level). [`computer_room_v1.py`](computer_room_v1.py) is that program **phase-gated** (2026-07-13):
a **retrofit only** — same layout, same pinned ids, same seed=11. It is **`lint_program`-clean**,
and it has **NOT been re-rendered since the retrofit**, so *the phase splits are unverified*: no
phase-1, phase-2 or phase-3 build has been run against the gated file. Treat the phase boundaries
as a proposal that still needs one `--phase 1` build to confirm.

## Prompt(s) this covers
- "a modern computer lab / workstation room: rows of desks each with a desktop computer and
  monitor, ergonomic office task chairs, a large wall-mounted whiteboard, a server rack, open
  storage shelving, cool blue-grey anti-static flooring, bright ceiling lighting, a window with
  blinds."

## Plan summary (from the planner)
"Front-Facing Modular Computer Lab Grid" (planner target `tmp/cr_run/plan/plan.png`): modular desk
bays facing a front instructional wall (large display + low whiteboard); **teal privacy screens**
between stations; a server rack anchoring the back wall with open equipment shelving; cool blue-grey
anti-static floor, brushed metal + teal accents; bright diffuse ceiling lighting; a window with
blinds.

Retrieved skills were all strong "Classroom computer-lab" frames (**0.69–0.77**) — the library
covers this shape well, which is itself the finding: this is a *known* pattern, and the interesting
work was all in the assets and the facing, not in the layout.

## The layout idea: REPEATED-UNIT GRID + a focal TEACHING WALL

**There is no hero.** The room is a *field* — one composed unit (desk + chair + computer) tiled
across the floor — and every wall is then given a job defined by *what the seated operators can
see*. This is the parent pattern for [`classroom_v1.md`](classroom_v1.md) ("a classroom is the
computer_room grid with the workstation swapped for a bare desk+chair unit") and for
[`laboratory.md`](laboratory.md) ("computer_room's grid wearing operating_room's clinical
discipline"). [`bedroom.md`](bedroom.md) Lesson 2 states the same *build-one-then-copy* principle at
the scale of a single pair; the grid is that principle scaled up.

| Wall / slot | Job | Why it is that |
|---|---|---|
| **centre** | the 8-station grid (2 rows × 4 cols, aisles) | the room IS the grid; it gets the floor |
| **front** (short) | the instructional focal wall: display centre, whiteboard left, **door right** | the wall the whole grid *looks at* — three slots, no collision |
| **back** (short) | the equipment end: server rack left, open shelving right, clock centre | utility kit belongs *behind* the class, out of the display's sightline |
| **left** (long) | the window (floor-to-ceiling, blinds) — **the only wall with no furniture** | so it stays the daylight source |
| **right** (long) | one circuit-board print | a lab with two blank long walls reads like a corridor |

The generalisation, stated sharply in [`laboratory.md`](laboratory.md): **the grid is not the
category — the PRODUCT on the unit is.** Classroom, computer lab and wet lab are the *same program*.
Swap the thing sitting on the desk and you have swapped rooms. That is why the computers here are a
phase-2 concern and not an afterthought: phase 2 is the layer that *names the room*.

## Pinned assets (audited previews)

| Role | id | Why pinned |
|---|---|---|
| desk | `hssd/5d17aa915ff1…` | `"computer desk"` retrieved a **white marble console table**. Pinned a minimalist white **flat-top** desk by id (`browse` → pick). A flat ~0.75 m top is also what `place_on_top` needs to seat the computer on the *writing surface* rather than on a hutch — `WorkstationGroup` warns if the desk is > 1.05 m tall. |
| server rack | `custom/9f2a77c71313…` | **Ingested.** `server_racking_system.glb` — 0.8 m wide, floor-standing, rack-mounted units + blue/green status LEDs. Ingested with a manifest overriding `description` (that string drives the retrieval embedding, so `"a tall black network server equipment rack"` now hits it #1), `scale` 0.8 m, `placement` floor. |

## Asset gaps

- **Server rack — was a dataset gap, now INGESTED.** No true server rack existed in the base pool
  (best matches ~0.48, generic "industrial cabinets"). v1 shipped a tall black perforated cabinet
  **stand-in**; v2 replaced it with the ingested `custom/9f2a77c7…` above. A clean worked example of
  the asset-first ingest loop: *retrieve → see the score floor → ingest → pin*.
- **Teal privacy screens — no teal asset, deliberately DROPPED.** The plan's teal desk screens have
  no match (only a grey desktop screen `hssd/dedf56aa…` and a blue-grey freestanding divider
  `hssd/1b99ac87…`). Omitted rather than forced into the wrong colour. The same gap bit
  [`classroom_v1.md`](classroom_v1.md) (teal acoustic panels — also dropped). **An accent colour the
  library does not have is a gap, not a wording problem: drop it, do not smuggle it into a texture
  string.**

## Lesson 1 — `place_on_top` SEATS an item but never AIMS it

The single most-inherited lesson from this scene. `place_on_top(monitor)` baked a fixed rotation, so
the 8 monitors faced random directions and the VLM flagged `rotate monitor to face the chair` on
*every* compile. The fix is an explicit `face()` on the single unit **before** `8 * ws`, so all 8
reorient identically.

**Any orientation-sensitive on-top item — monitor, TV, clock, laptop — needs an explicit `face()`.**
The tournament sizes it and seats it; it does not know which way it should look. Inherited verbatim
by [`tv_studio.md`](tv_studio.md) (`anchor_set.face(laptop, toward=seat_pair)`) and by
[`office_modern.md`](office_modern.md).

`WorkstationGroup` now does this for you — `place_computer()` turns the screen to face the operator
once positions have settled — which is exactly why the v2 program uses the group instead of
hand-rolling `place_on_top` + `face()`.

## Lesson 2 — a `place_on_top` sink is a SURFACE bug, not a seating bug

The all-in-one computers seated **~2 cm below** the desktop. The root cause was **not** the DSL's
seating math (which was correct) but the surface picker in `tools/planar_regions.py`: this desk's
thin top slab has its **underside modelled with upward-facing normals**, so `detect_horizontal_regions`
reported two near-coplanar full-size surfaces — the true top at y≈0.75 and a spurious one 2 cm below.
`top_surfaces()` kept **both** (they were within its 2 cm `band`) but left each at its **own y**, so
tournament tiles landing on the lower face seated 2 cm low: invisible on a short pen cup, a visible
*sink* on a tall monitor.

**Fix (general, not per-scene):** `top_surfaces()` now snaps every near-coplanar region to the top
plane (`r["y"] = top_y`). Verified: the computer's bottom moved `0.7303 → 0.7500` (flush).

The reusable part is the **diagnosis method**: a five-line script printing the anchor's AABB *top*
(`desk.get_aabb()[1,1]`) against the item's AABB *bottom* (`computer.get_aabb()[0,1]`) isolates the
gap in seconds — **no render needed**. [`laboratory.md`](laboratory.md) reuses exactly this probe to
catch an ingested microscope whose origin sat 118% of its height off-centre.

**Do not "fix" a sink by nudging the item's y.** Find the surface bug. A y-nudge hides a mesh/normals
defect that will resurface on every other scene that touches the same asset. `[[smart-placement]]`

## Lesson 3 — a `WorkstationGroup` grid faces the OPPOSITE wall from a `place_desk_chair` grid

`WorkstationGroup`'s operator side is local **+Z** (the chair sits in front of the desk at +Z), which
is the *opposite* of the `place_desk_chair` convention. So the intuitive `face(stations,
toward="front_wall")` pointed all 8 operators **away** from the front display — the render showed the
backs of eight screens.

```python
room.place_on_center(stations, facing="front")
room.face(stations, toward="back_wall")   # <- points the SEATED USERS at the FRONT wall
```

**And the VLM cannot help you here.** `RotationConstraint` returned `no rotation` in *both* the
correct and the flipped orientation. The interior render is the only arbiter: the front-wall view
shows either operators' **faces** (correct) or the **backs of their screens** (flipped). Look at it.

The same `+Z`-operator rule is re-stated in [`executive_office.md`](executive_office.md); the
inverted case (a `place_desk_chair` grid, which *does* face toward the front wall) is
[`classroom_v1.md`](classroom_v1.md). Getting these two confused is the single most common way to
build a room where everyone stares at a blank wall.

## Lesson 4 — build the unit ONCE, then `8 * ws`

The station is composed once and duplicated: `stations.place_grid(8 * ws, cols=4)`.

The computer's `place_on_top` therefore runs **one** VLM sizing tournament, on the single unit; `N *`
deep-copies the *realized transforms* (ops are cleared on copy), so all 8 stations are laid out
identically and the tournament runs once, not eight times. Build the eight separately and you pay 8×
for eight subtly *different* desks — the exact failure [`bedroom.md`](bedroom.md) Lesson 2 documents
on a two-nightstand pair, where the two lamps came out different sizes.

`vlm_solver=None` on `WorkstationGroup` is the other half of this: no per-instance proportion render,
which is what makes a grid affordable at all.

## Lesson 5 — use the purpose-built group; don't hand-roll the motif

`WorkstationGroup` (`[[workstation-group]]`) is `set_anchor` (desk) + `place_chair` +
`place_computer` + `place_accessories`. It tucks the operator chair, seats the computer on the *real*
desktop surface via `place_on_top`, turns the screen to face the operator, and caps the desktop at 3
items (`MAX_DESKTOP_ITEMS` — `place_on_top` is only reliable with a few).

`"a desktop computer"` routes to the `DesktopWorkstationRetriever` pool and returns an **all-in-one
screen set** — richer than the bare black monitor a generic query gives you.

v1 of this scene hand-rolled it (`place_desk_chair` + `place_on_top(monitor)` + `face(monitor,
toward=chair)`). That *also* works, and it is what [`classroom_v1.md`](classroom_v1.md) still uses
because a classroom desk has no computer. **When a purpose-built group exists for the motif, use it**
— it carries the traps (Lessons 1 and 2) already solved.

## Lesson 6 — texture strings are embedding-matched: phrase for COLOUR, not jargon

`"cool blue-grey anti-static vinyl flooring"` came back **brown**. Texture strings are embedded
against a *fixed* library, and "anti-static vinyl" landed nearest a **wood** texture. Dropping the
jargon to `"smooth cool grey concrete floor"` hit the grey concrete/vinyl textures.

**A floor or wall rendering the wrong colour is a WORDING bug, not a constraint violation** — no VLM
vote will ever tell you to fix it. Simplify to plain **colour + material** words.
[`classroom_v1.md`](classroom_v1.md) hit the harder version of this (a "teal accent wall" phrase
recoloured *all* walls green), and [`kindergarten_v1.md`](kindergarten_v1.md) inherits the rule.

## Lesson 7 — wall-slot hygiene: every wall gets a job, and only one wall gets three slots

Front wall = display **centre** + whiteboard **left** + door **right**: three slots, no collision.
The window claims **all three** slots of the left wall (`place_window_floor_to_ceiling`), so nothing
else can go there — which is fine, because that wall's job *is* the daylight. Back wall carries the
rack + shelf on the floor and the clock above. `WallOverlap` stayed clean throughout.

Most layout bugs in this family are a wall with **no** job (it ends up blank and the room reads like
a corridor) or a wall with **two** (the door lands under the whiteboard). Assign them explicitly, on
paper, before you place anything.

## Program

[`computer_room_v1.py`](computer_room_v1.py) — **phase 1** the floor anchors (the desk+chair grid,
the back-wall server rack and shelving, the walls, and the door); **phase 2** the surface dressing
(the computer + pen cup seated on each desktop — i.e. the layer that makes it a *computer* lab);
**phase 3** the front-wall display and whiteboard, the clock and print, the window and the ceiling
lighting.

`workbench run skills/examples/computer_room_v1.py --phase 1` builds the layout alone in ~1–2 min.

Two notes on the gating, both structural:

- The **door is ungated** — it runs in phase 1, because its automatic clearance shapes the floor
  solve. Deferring it would change the layout you just validated.
- The **phase-2 gate sits INSIDE the `with scene.WorkstationGroup()` block**, wrapping
  `place_computer` / `place_accessories`. Gated *outside* the block, those ops are never recorded on
  the group — the build stays clean, nothing errors, and the computers are simply **GONE**.

*Honest caveat: the gated file has been linted but not run. The phase boundaries above are the
intent, not a verified result.*

## What worked / gotchas

- **Same bones as classroom / laboratory / office.** A unit → a `GridGroup` → `face()` at the
  teaching wall. If you are building any "rows of people at desks" room, start here and swap the
  product on the desk.
- `GridGroup(sparsity=0.55, randomness=0.3)` gave real circulation aisles between the two rows of
  four. (Compare [`laboratory.md`](laboratory.md), where an *over*-sparse grid at 0.3 provoked a
  bogus `rescale room by 0.5` vote — the shrink vote was really "your grid is too spread out".)
- **The room-size vote — and a discrepancy you should know about.** The build's notes record that the
  VLM asked to enlarge the room (`1.2`, twice) and that a `1.1` was applied *in the final phase only*,
  held through the earlier phases per **render-wins-early**. **But the shipped program carries
  `RoomGroup(modulate_scale=1.0)`** — the enlarge is *not* in the committed source, and no room-size
  vote for this scene appears in `../workflow/vlm_feedback.md`. The program is authoritative; the
  `1.1` claim is unreconciled and I did not re-render to settle it. Flagged in "Possible refinements".
  The transferable half of the lesson is safe and is sharpened by [`bedroom.md`](bedroom.md) Lesson 5:
  **hold room-size votes until a full build** — a half-dressed room always looks too big.
- Wall-mounted items are given explicit `width=` (display 1.8, whiteboard 1.6, print 1.0) rather than
  being left to the retriever's native scale.

## VLM feedback we hit and how we resolved it

Recorded in [`../workflow/vlm_feedback.md`](../workflow/vlm_feedback.md) — five entries, four from
v1 and one from v2. **This is one of the few examples with a real logged loop; do not paraphrase it
away.**

| Feedback | Action | Result |
|---|---|---|
| `rotate monitor to face the chair`, every compile (v1) | **Accepted** — added `face(monitor, toward=chair)` on the single unit *before* `8 * ws` | `no rotation`. → Lesson 1 |
| `rotate desk 180` / `rotate chair to face desk` on a `place_desk_chair` unit (v1) | **DECLINED** — the unit is correct *by construction*; verified by eye | A known false positive on `place_desk_chair` units (same as classroom, children_room). **Don't chase it.** |
| Floor rendered **brown** (v1) | Not a constraint signal at all — a *wording* fix. Rewrote the texture string | Correct grey. → Lesson 6 |
| `RotationConstraint: no rotation` — in **both** the correct and the flipped grid orientation (v2) | **Ignored the VLM entirely**; read the interior render (faces vs screen-backs) and flipped to `face(stations, toward="back_wall")` | Operators aimed at the display. → Lesson 3. *A `no rotation` verdict is not evidence of correct rotation.* |
| "computer desk" → a **white marble console table**; server rack best-match ~0.48; no teal screen (v1) | Pinned the desk by id; **ingested** a real rack; **dropped** the teal accent | → Pinned assets / Asset gaps |

**No VLM pass has been run on the phase-gated retrofit.** Every vote above belongs to the original
un-gated build.

## Manual constraints used

**None.** The automatic door clearance plus the `GridGroup` aisles were sufficient; `WallOverlap`,
`RotationConstraint` and `RoomProportions` all came back clean on the final full compile.

Candidate for v2: `add_clearance(server_rack, dir="front")` — a real lab needs maintenance access to
the front of the rack, and nothing currently guarantees the grid does not creep up to it.

## Possible refinements (not blocking)

- **Run `--phase 1` on [`computer_room_v1.py`](computer_room_v1.py).** The retrofit is lint-clean and
  nothing else. Until someone builds it, "phase 2 seats the computers" is an assertion, not a fact —
  and the phase-2 gate inside the `WorkstationGroup` block is exactly the kind of thing that fails
  silently (see Program).
- **Reconcile `modulate_scale`.** The prose says a `1.1` enlarge was applied in the final phase; the
  source says `1.0`. One of them is wrong. A full build settles it.
- **Add the rack clearance** (above).
- **The teal accent never landed.** It is a genuine asset gap, not a wording problem, so the honest
  route is a textile or a pinned teal object — never a texture string. Logged for
  `../workflow/creative_asset_gaps.md` along with the chip-tray-class "small identity prop that does
  not exist" family.
