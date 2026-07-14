# Gym — worked example ("Big-Box Fitness Floor")

## Status

`Status:` **phase-gated retrofit, lint-clean, NOT re-rendered.**
[`gym_v1.py`](gym_v1.py) is `scenes/work/gym_mega.py` (seed=21) with phase gates added on
2026-07-13 — same layout, same pinned ids, same seed, same comments. It passes
`workbench lint` (`lint: clean`). **It has not been built or rendered since the retrofit, so
the phase splits are unverified**: nobody has yet confirmed that phase 1 alone produces the
zone map, or that phases 2–3 only *add* to it.

The **pre-retrofit** `scenes/work/gym{,_large,_mega}.py` were built and recorded as VLM-clean
(commit `e9a901b`, which also landed the DSL support these scenes needed: `place_mirror_full_wall`,
`RoomGroup(max_height=)`, the `front_back` / `front_sides` clearance directions, and bare
floor-to-ceiling glass). **No vote log survives** — see [VLM feedback](#vlm-feedback-we-hit-and-how-we-resolved-it).

Three gyms of increasing scale live in `scenes/work/`: `gym.py` (a boutique studio, seed=8),
`gym_large.py` (one of each zone, seed=11), and `gym_mega.py` (a Planet-Fitness-scale club,
seed=21). **`gym_mega.py` is the one promoted here** — it is the scene every lesson below was
actually minted on, and the only one with the full zone set (spin grid, machine bank, reception,
massage lounge, amenities). The other two are useful as *smaller cuts of the same pattern*: if
your brief is a boutique studio, `scenes/work/gym.py` is the same zoning with one wall's worth of
equipment, and it is not promoted only because it teaches nothing the mega scene does not.

## Prompt(s) this covers
- "a large commercial gym / health club: cardio machines, free weights, a machine circuit, a spin
  studio, a functional training area, a mirrored wall, and a reception desk."
- Scales down cleanly to "a boutique fitness studio" (drop zones, keep the zoning).

## Plan summary (from the planner)
"Big-Box Fitness Floor" — a Planet-Fitness-scale club. Black rubber flooring + a green functional
turf patch, exposed grey industrial ceiling, warm-white plaster walls, **one full mirrored wall**,
**floor-to-ceiling glass on the opposite wall**, navy + gold branding, a staffed reception at the
entrance. Zones: cardio, free weights, machines, functional/turf, spin, reception, amenities.

## The layout idea: LARGE PERIMETER MULTI-ZONE (zone first, then fill)

**Name the zones before you place a single asset.** A large gym is not a room with equipment in
it — it is a set of **functional zones**, and the only way to get a coherent floor is to assign
each zone to a *region* (one of the four walls, the centre, or a corner) and then fill that region.
Scatter machines one-by-one and you get a warehouse of orphans.

This is the **large** end of the catalogue's layout spectrum, and it is what you reach for when a
brief has *more programme than walls*:

| Wall / region | Zone | Why it is that zone |
|---|---|---|
| **right** | **GLASS + cardio run** — 8 treadmills at the glass, 8 ellipticals behind, all facing out | cardio is the longest-dwell, most boring activity in the building, so it gets the only view. The wall is glazed **because** the cardio is there. |
| **left** | **MIRROR + weight training** — the machine bank (back-left) plus power rack / dumbbell rack / plate tree / benches | lifters check form ⇒ the free weights get the mirror. Machines and free weights stay **together**; split them and the floor scatters. |
| **back** | **SPIN studio** — bikes in a 3×2 grid facing in | spin is the one zone that is naturally a *block* of identical units, so it is the one zone that is a grid rather than a row. |
| **centre** | **FUNCTIONAL turf** — plyo box, kettlebells, medicine balls, sandbag on a green turf rug | the middle of a gym must stay open and rearrangeable, so it gets the lowest, cheapest zone. |
| **front** | **ENTRY** — reception desk (backed to the wall, facing *in*), massage lounge, amenities corner, lockers, brand art, door | the arrival sequence; everything a member touches before they train. |

**Inherits:** the grid-of-identical-units machinery from
[`computer_room.md`](computer_room.md)'s *repeated-unit grid* (the spin studio and the cardio run
are that grid, twice, at different aspect ratios), and the "the centre object's clearance sizes the
room" instinct from [`game_room.md`](game_room.md).
**New here:** zoning as the *primary* design act — `computer_room` has one repeated unit and one
feature wall; a big gym has **seven zones competing for four walls**, and the pattern is the
allocation, not any single group. `grocery_store` and `library` solve the same "more programme than
walls" problem on a perimeter; this is the version where the *centre* is a zone too.

Interior zones that are whole rows/grids of machines use `GridGroup.place_grid(units, cols=N)`
placed on a **floor** position (`place_on_back_left`, `place_on_right`, …) — **not** the perimeter
`place_on_*_wall_*` calls. A zone that is a grid is floor furniture that happens to be near a wall.

## Pinned assets (audited previews, verdicts made from the preview PNG — not similarity)
The retrieval audit is `scenes/work/gym.md` (2026-06-27, 6 queries: **GOOD 6 / WEAK 0 / MISSING 0**).

| Role | id | Why pinned |
|---|---|---|
| treadmill | `hssd/fdd91608…` | black treadmill with an LED console; audited GOOD (sim 0.627) |
| flat bench | `hssd/0391f7b1…` | sturdy black flat bench; audited GOOD (sim 0.752 — the *highest* sim in the audit) |
| dumbbell rack | `hssd/f7109eaa…` | black metal rack, two rows of dumbbells; audited GOOD (sim 0.688) |
| elliptical | `future/1f79b924…` | the pool's one credible cross-trainer; doubles as the rowing-erg stand-in |
| upright bike | `hssd/b3ef9e90…` | the spin grid's unit |
| lat pulldown | `future/96bb6aab…` | pinned for the **weight stack** — the generic query returns bare frames |
| pec deck / ab crunch / cable tower | `hssd/54064415…` / `hssd/b16e1cc9…` / `hssd/ac2b117a…` | the selectorized bank |
| seated row / incline press | `hssd/f87c00e6…` / `hssd/1fa8df7c…` | mega-scene only; **no audit note was recorded for these two** |
| power rack | `hssd/b46437ac…` | squat rack **with** barbell; also the leg-press stand-in |
| plate tree | `hssd/fb933386…` | loaded, so it reads as a working rack |
| plyo box / kettlebell / med ball / sandbag | `hssd/2f2b6ebd…` / `hssd/c3bb69cc…` / `hssd/33adf260…` / `hssd/b98b86e3…` | the turf zone; the sandbag is the battle-rope stand-in |
| reception desk | `hssd/7379d887…` | curved reception front desk. **Cross-check:** `grocery_store_v1.py` measured this same mesh at **0.60 m** and rejected it as a *checkout counter* — as a low reception desk it is the right shape, and `bookstore`/`library` pin it too. It is **not** height-pinned here (see refinements). |
| massage recliner | `hssd/e129e1f4…` | the lounge zone |
| water cooler / trash | `hssd/b77968f3…` / `hssd/141dd97f…` | both **height-pinned** with `_fit_height` — see the prop-scaling lesson |
| lockers | `future/902f9b5b…` | black 3-door bank |
| feature art | `future/9c5ac3d9…` | navy + gold geometric — the *branded/neon gym signage* queries are weak, so the brand wall is carried by abstract art |

**The pool is deep.** `NOTES.md` flagged gym machines as a HIGH asset-gap risk; the curated
`gym_equipment` pool (167 ids) neutralised it, and every query in the audit landed GOOD.
5 of 6 queries route to `GymEquipmentRetriever`; **"a rubber gym floor mat" routes to the general
retriever instead**, even though the gym pool advertises "yoga mat" — a latent routing
inconsistency worth knowing before you assume the curated pool was used. Verify with `inspect`,
which prints the retriever name.

## Asset gaps
GOOD in the pool: treadmill, upright bike, elliptical, dumbbell rack/tree, flat & incline bench,
power/squat rack (+ barbell), plate tree, barbell + plates, lat pulldown, pec/chest & ab-crunch
machines, cable tower, plyo box, kettlebell, medicine ball, stability ball, sandbag, punching bag,
lockers, water cooler, massage chair, reception desk, trash can.

**MISSING** (use the stand-in):

| Missing | Stand-in used |
|---|---|
| rowing ergometer | elliptical |
| leg press | power rack |
| Smith machine | incline bench press |
| battle rope | sandbag |
| branded / neon gym signage | **weak** — abstract navy+gold feature art instead |

No ingestion was needed for this scene.

## Lesson 1 — for a big scene, plan ZONES first, then fill them
The headline. Assign zones to the room's regions (the 3×3 floor grid + the four walls) **before**
placing anything; then each zone is a `GridGroup`/`RelativeGroup` dropped into its region. This is
what makes a 40-object gym legible instead of a machine warehouse, and it generalises: whenever the
programme has more parts than the room has walls, zone it. (`grocery_store` does this with the
perimeter cold chain vs the centre hub; `library` with twin shelf runs vs a centre table column.)

The corollary that catches people: **a zone that is a block of machines belongs on a floor slot,
not a wall slot.** `place_on_back_left(machines, facing="front")` — the grid is furniture. The
`place_on_*_wall_*` calls are for the individual pieces that genuinely back onto the wall (the
power rack, the dumbbell rack, the plate tree).

## Lesson 2 — cardio faces the view (and in a 2-row grid, the SECOND row lands against the wall)
People want something to look at while they run, so the cardio run lines the glass wall **facing
out**. Treadmills nearest the glass (best view while running), ellipticals in the row behind.

The mechanical trap: in a 2-row `place_grid`, the **second** grid row is the one that lands against
the wall. So you list the **back-row asset first**:

```python
cardio_units = (8 * scene.AddAsset("an elliptical cross-trainer cardio machine", asset_id=ELLIPTICAL)
                + 8 * scene.AddAsset("a treadmill exercise machine", asset_id=TREADMILL))
with scene.GridGroup(sparsity=0.4, randomness=0.08) as cardio:
    cardio.place_grid(cardio_units, cols=8)
room.place_on_right(cardio, facing="right")
```

Get the order backwards and the ellipticals get the view and the treadmills stare at them.

## Lesson 3 — the FULL-WALL MIRROR is a real reflection, and it is a wall, not a prop
**The only demonstration of `place_mirror_full_wall` in the library** — if you need a mirrored wall
(gym, dance studio, hair salon, boutique fitting room), this is the example to copy.

`room.place_mirror_full_wall("left_wall")` covers an entire wall with one reflective surface: a true
Cycles mirror (`IDSDL/mirror.py` builds a thin panel with a metallic / ~0-roughness PBR material).
Three things follow from how it is built, all of which will bite you otherwise:

1. **It does not cut the wall.** Unlike a window it leaves the wall intact — a mirror *hangs* on it.
2. **It claims all three wall slots.** Mount nothing else on that wall (`_register_wall_occupancy`
   takes `["left", "center", "right"]`). Floor furniture *along* the wall is fine and expected —
   the power rack, dumbbell rack and plate tree all sit in front of it. Floor-vs-mounted is a
   different axis.
3. **Do NOT approximate it by tiling mirror props** with `place_on_wall_freeform` on a left/right
   wall. That path sizes flat objects by their **depth**, so a ~5 cm-thick mirror prop collapses to
   nothing. The retrieved "gym wall mirror" prop (`hssd/37df562f…`, audited GOOD) is a *fine object*
   and a *bad mirrored wall* — the boutique `scenes/work/gym.py` still carries a stale docstring
   describing "three large mirrors tiled across the wall (`place_on_wall_freeform`)"; its code calls
   `place_mirror_full_wall`, which is what the tiling hack was replaced by.

## Lesson 4 — dynamic room height: tall equipment needs `RoomGroup(max_height=…)`
Room HEIGHT is normally **clamped to 3.0 m**. Tall racks and machines — and any wall decor above
them, like a clock over a locker bank — then clip the ceiling, and *no constraint catches it*
(the room auto-sizes WIDTH/DEPTH from the footprint; HEIGHT is not part of the footprint solve).

`RoomGroup(max_height=4.0)`: HEIGHT grows with the **tallest floor object**, clamped to
`[3.0, max_height]`. The default stays 3.0, so every other scene in the repo is byte-identical.
A compile-time `_warn_over_height` check then flags any object whose top *still* pokes through, and
surfaces it in `scene.vlm_feedback` (so the workbench report shows it). There is no auto-fix —
raising the ceiling changes the whole room — so the fix is yours: shrink the asset, or raise
`max_height`. **Any scene with 2 m+ equipment or fixtures should be reaching for this**, not just
gyms (warehouse racking, laboratory fume hoods, a library's tall stacks).

## Lesson 5 — clearances are per-OBJECT (leaf), never per-group
`room.add_clearance(obj, distance, dir)` keeps space around `obj`. **Pass a placed leaf object, not
a group wrapper.** The raytracer keys on `get_children()` (flattened leaves), so handing it a
`GridGroup` / `RelativeGroup` throws `KeyError`. To clear a whole row or grid, loop its units:

```python
for _c in cardio_units:                       # not `cardio`, the GridGroup
    room.add_clearance(_c, distance=0.5, dir="front_back")
```

Per-unit clearance on a row *is* row-level clearance: `front_back` on every treadmill and elliptical
buys the aisle at the glass, the aisle between the two rows, and the aisle behind the run — three
circulation aisles from one loop. The `dir` vocabulary (extended by this scene's commit):

| `dir` | Clears | Use for |
|---|---|---|
| `front` | the facing direction | lockers (changing space), a wardrobe |
| `sides` | the two perpendicular sides | a piece that is entered laterally |
| `all` | front + back + sides | each spin bike ⇒ a clear border around the grid |
| `front_back` | ahead and behind | **rows** — the aisle pattern |
| `front_sides` | front + left + right | a machine you step into and stand at the stack; a reception desk you approach |

And: **reception clearance goes on the DESK leaf, not the reception group.** This is the same
"the clearance is what sizes the floor" idea `game_room` builds its whole room around; here it is
distributed across ~30 leaves instead of concentrated in one hero.

## Lesson 6 — the reception desk backs onto the wall and faces INTO the room
Back the desk against the wall but face it **inward**: `place_on_front_left(reception, facing="back")`,
with the staff chair `place_on_back` of the desk (tucked toward the wall, behind the counter — where
a member never stands). A desk facing the wall reads as broken furniture.

The VLM will want to "rotate the desk 180°" — *that would face it at the wall*. **Override it.** The
orientation is correct, and this is the class of vote you refute with the room's logic rather than
its pixels: the desk's front is where the *member* stands, and the member comes from the door.
(Same shape of argument as `grocery_store`'s declined shrink vote and `bookstore`'s
`facing="back"` checkout that sees the door.)

## Lesson 7 — bare floor-to-ceiling glass beats curtains when the glass IS the amenity
`place_window_floor_to_ceiling(wall)` with no `curtain=` is **bare glass** (the curtain bug that also
affected the picture window is fixed in `IDSDL/window.py`; `curtain=None` is honoured). Cardio
against bare glass reads far better than curtains hiding the view — and in this room the view is
load-bearing: it is *the reason* the cardio is on that wall. Curtain a gym's glass wall and you have
undone Lesson 2. (`bedroom`, by contrast, wants floor-length linen — the difference is whether the
window is a *light source* or an *amenity*.)

## Lesson 8 — pin the real HEIGHT of small props; a pinned id does not pin a size
`AddAsset` derives scale from the **description text**, so a pinned *small* prop (bin, water cooler,
foam roller, potted plant) can still arrive wrong-sized under an unlucky phrasing — a water cooler
rendered **~2.4 m tall** once, with the id already pinned. Pin the real size explicitly:

```python
def _fit_height(obj, target_h):     # uniform scale to a target height (m)
    w, h, d = (float(v) for v in obj.get_whd())
    ...
amenities.set_anchor(_fit_height(scene.AddAsset("a freestanding water cooler dispenser",
                                                asset_id=COOLER), 1.1))
```

The general rule: **pinning an id fixes *which* mesh, never *how big*.** Big furniture usually
carries plausible real-world scale; small props do not, and a prop that is 2× too big is the single
most render-destroying error in a scene.

## Program
[`gym_v1.py`](gym_v1.py) — the retrofit of `scenes/work/gym_mega.py`.

- **Phase 1 — the zone map.** Every zone's floor anchors (cardio grid, spin grid, machine bank,
  free-weight wall, benches, plyo box, reception + staff chair, massage lounge, amenities, lockers),
  `place_walls`, `place_door`, and **all the clearances**. This is where ~all the value of this
  scene is: the zoning, the aisles and the shell are decided here and nowhere else.
- **Phase 2 — deliberately thin.** The turf zone's dressing (kettlebells, medicine balls, sandbag,
  the green turf rug) and the reception plant. **A gym floor is furniture, not tabletop dressing** —
  there is not a single `place_on_top` in the program, which is unusual and correct: gyms have no
  surfaces. If you copy this pattern into a room that *does* have surfaces, phase 2 is where they go.
- **Phase 3 — the mood, and the identity.** The full-wall mirror, the bare floor-to-ceiling glass,
  the brand art, the clock, the lighting.

`workbench run skills/examples/gym_v1.py --phase 1` builds the layout alone in ~1–2 min.

**The door is UNGATED** — it runs in phase 1 because its automatic clearance shapes the floor solve,
so deferring it would change the layout you validated. `place_walls` is likewise ungated.

**Honest caveat about the phase 3 split:** the mirror and the glass wall are gated to phase 3, which
means a phase-1 render of this scene shows the zoning inside a *plain plaster box*. That is correct
by the convention (they are wall treatments) but it does mean **phase 1 does not show you the room's
identity** — judge phase 1 on the floor plan and nothing else.

## What worked / gotchas
- `modulate_scale=0.9` on a room this loaded. The mega scene is the one build in the family that is
  genuinely big; the boutique (`gym.py`, 0.85) and large (`gym_large.py`, 0.8) cuts shrink harder.
- `sparsity` per zone, not globally: 0.4 for the cardio grid (tight rows), 0.45 for spin, 0.5 for the
  machine bank and the massage pair.
- Lighting `density=0.008` — `N = 1 + (max_lights − 1) × density`, and a ceiling this large **swarms**
  with fixtures at a normal density. Big room ⇒ *lower* density, which is the opposite of the
  intuition. (Compare `coffee_shop`'s sub-0.02 for a small room: the number tracks the ceiling area,
  not the vibe.)
- The clock goes on the **back** wall, above the spin studio, because the front wall's `right` slot is
  the door's. Wall slots are a budget; the door spends one.
- A real per-wall navy branding wall would need a **per-wall accent texture** — not in the DSL
  (`place_walls` takes one `wall_texture`). The boutique scene flagged this as future work and the
  mega scene works around it with a large feature-art panel.

## VLM feedback we hit and how we resolved it
**Not recorded — and this is a real gap.** The gym family predates the convention of logging the
loop. The pre-retrofit scenes were recorded as VLM-clean, but the votes, the render passes and the
declined feedback were never written down, so the only survivors are the traps that made it into the
program's comments (Lessons 2–8). The one vote the previous version of this file thought worth
warning about is the reception-desk rotation (Lesson 6) — recorded there as a vote to **decline**,
though whether it actually fired, and on which pass, is not logged.

**If you rebuild this scene, log the votes.** Fabricating a history here would be worse than
admitting there isn't one.

## Manual constraints used
`add_clearance` on ~30 leaves — the only example in the catalogue that uses clearance at this
density, and the scene that introduced the `front_back` and `front_sides` directions:

- every treadmill / elliptical: `0.5 m`, `front_back` → the glass aisle, the between-rows aisle, the
  aisle behind the run
- every spin bike: `0.4 m`, `all` → a clear border around the grid
- every strength machine: `0.55 m`, `front_sides` → step in, stand at the stack
- the reception **desk leaf**: `0.8 m`, `front_sides` → an approach
- the locker bank: `0.8 m`, `front` → changing space

The defaults were not enough because a gym's *empty floor is the product*: the aisles are not
leftover space, they are the thing you are placing.

## Possible refinements (not blocking)
- **Build the gated program and verify the phase splits.** Nothing here has been rendered since the
  retrofit. Phase 1 in particular should be checked for: the zone map reproducing, `no rotation`,
  `no wall overlap`, and the clearance aisles surviving the solve.
- **Height-pin the reception desk.** `grocery_store_v1.py` records this exact mesh at **0.60 m**,
  which is low for a reception counter; the gym never `_fit_height`'d it. Worth measuring with
  `get_whd()` and pinning to ~1.05 m if it reads short.
- **Room-size votes on a phase-1 gym are meaningless** — the floor is *supposed* to be mostly aisle,
  so the occupancy metric will read it as empty. See [`bedroom.md`](bedroom.md) Lesson 5; read the
  phase-1 build for layout signal only.
- The branded-signage gap is still open. Neon/branded gym signage retrieves weakly; if someone
  ingests a decent neon logo, the front wall is where it goes.
- `gym.py` (boutique) and `gym_large.py` are **not** phase-gated. If either is ever promoted, they
  should be gated the same way — but they teach nothing new, so the better move is probably to
  delete them and parameterise this one.
