---
id: example:prison_cell
kind: example
family: subtractive
category: "prison / jail cell"
pattern: "The SUBTRACTIVE room — austerity IS the design"
---
> **Digest (from the pattern index):** **The SUBTRACTIVE room — austerity IS the design** (the one category the coffee_shop vibe layer would destroy): bunk on a long wall + open sanitaryware IN the sleeping room (the unambiguous cue) + one hard desk, bare concrete, nothing soft. Teaches **how to hang BARS over a window** (`place_on_wall_freeform` keeps a fence panel at its own width and claims no slot, and its `wall_height/2` mount coincides with the standard window's pane centre — so the black-void limit becomes an ASSET: darkness behind bars); forced out a core `IDSDL/window.py` fix (**`curtain=None` still drew the DEFAULT drape — no way to author a bare window**, silently draping 7 other scenes); "a phase-2 `place_on_top` gated OUTSIDE its `with` block never runs — the count still increments, the loop stays clean, the prop is just GONE"; the `bottom=` wall-mount false-positive in the float lint; and check a wall object's AABB bottom against nearby furniture tops before hanging it


# Prison cell — worked example

Status: **built & VLM-clean** ("Containment Core", `scenes/work/prison_cell.py`, seed=11).
Final full build: `no rescale / no rotation / no wall overlap` at `modulate_scale=0.7`.
Built through the guided flow (flow_0712_220758_8f99), entirely via the MCP tools.

## Prompt(s) this covers
- "a prison cell", "a jail cell", "a holding cell", and by extension any **austere
  single-occupancy institutional room** (a monastic cell, a barracks bunk room, a
  ship's cabin) — the pattern is bed + open sanitaryware + one hard surface, nothing soft.

## The pattern: a SUBTRACTIVE room — austerity IS the design
Every other example in this catalogue asks *what do I add to make this read?* A cell asks the
opposite. The coffee_shop vibe recipe (a warm accent seat, greenery, a warm envelope, stocked
shelves) would **actively destroy** this category: each soft object drags it toward a spartan
dorm. Ship it bare — no rug, no curtain, no plant, no warm accent, no wall art beyond a basin
mirror. The one prop on the desk (a stack of paperbacks) is the *only* personal property and it
carries the whole "someone lives here" note.

## What actually makes it read as a cell (identity props, in order)
1. **BARS on the window.** Without them this is a bedroom. See the bar-hanging recipe below.
2. **A TOILET AND BASIN IN THE SLEEPING ROOM.** The most unambiguous cue in the set — only a cell
   puts open sanitaryware beside a bed. Put them on ONE wall (a shared plumbing chase).
3. **A steel-framed BUNK with thin flat mattresses**, its 2 m run along a long wall.
4. Bare grey concrete floor + walls, a hard flush ceiling panel, and a small, tight shell.

## Layout (few floor slots — the shell is a consequence of them)
- **LEFT (long)**: the bunk hero, its 2.0 m run along the wall → 1 item.
- **RIGHT (long)**: the hygiene corner — toilet + wall-hung basin sharing a chase → 2 items.
- **BACK (short)**: the desk + stool unit, directly under the barred window.
- **FRONT (short)**: the door. The centre aisle from door to window stays EMPTY — that lane is
  the category, not dead space (garage/corridor rule).

## Pinned assets (audited previews + `get_whd()` verified offline)
| Role | id | native w×h×d | note |
|---|---|---|---|
| Bunk (hero) | `hssd/0b750370480e2a26bfedafd6b5298f28d6074e70` | 2.00×1.52×0.90 | white metal bunk, ladder + thin mattresses; true scale, no fix |
| Toilet | `hssd/0c4ab4d4ccdc801b4093f10a9aa9c0bfd08ab584` | 0.40×0.83×0.70 | plain white close-coupled |
| Basin | `hssd/3f0778f68a489d3995e2e3f13d13e4a90fb500a8` | 0.50×0.54×0.40 | wall-hung, exposed trap → `bottom=0.40` |
| Desk | `hssd/709745fbd3cc41050840793cdf67e73995e27270` | 1.20×0.75×0.61 | flat-top + drawer pedestal |
| Stool | `hssd/502ce37cd7bad20d9ff7a7fe64914dab16a8d7c6` | 0.45×0.43×0.34 | low, backless |
| **Window bars** | `hssd/1370b0fb20e3fb98e25a86c30291ee80177bb20e` | 1.20×1.17×0.12 | a **steel fence panel** — the identity prop |

## THE RECIPE: how to hang bars over a window
There is no window-grille asset. A near-square **fence panel** (5 vertical bars, depth 0.12 m <
`WALL_HUNG_MAX_DEPTH` 0.25) is one, and it lands on the pane if you use the right verb:

```python
room.place_window_standard("back_wall", position="center")      # NO curtain kwarg → bare (see fix below)
bars = scene.AddAsset("a black steel panel of vertical bars", asset_id=BARS)
bars.scale(0.95)                                                 # uniform: match the ~0.94 m pane
room.place_on_wall_freeform("back_wall", [bars])
```
Three mechanics make this work — all three matter:
- **`place_on_wall_freeform`, NOT `place_on_wall_<wall>_center`.** The slot verb caps a wall
  object's width at `0.6*(WIDTH/3)`, far too narrow to cover the pane. Freeform keeps the panel at
  its **own** width (up to 50% of the wall) — so you pre-scale it to the pane yourself.
- **The heights coincide by construction.** Freeform mounts at `wall_height/2`; a standard window's
  `'middle'` partition is centred at `2.40 − 3·exp(−0.4·H)` — both ≈ 1.5 m at a 3 m wall. So the
  bars land ON the pane with no fiddling. (The slot verbs mount at a fixed 1.5 m too.)
- **Freeform registers NO wall slot**, so the bars raise no `WallOverlap` against the very window
  they are meant to cover. The build stayed `no wall overlap` throughout.

**The window is the one opening you cannot get wrong.** Bars work under EITHER renderer regime:
in this build the pane came back **bright** (the working tree carries an uncommitted
`IDSDL/renderer/utils.py` change — interior views now render on an OPAQUE film, so openings show
the lit world background instead of the old black void), and it reads as hard daylight through
bars, matching the planner's collage. If that change is reverted and the void returns, *darkness
behind bars* reads as a night-time cell — also right. A cell is the one room where the black-void
limit costs you nothing.

## Gotchas this scene minted
- **`curtain=None` did NOT mean "no curtain" — a CORE BUG this scene found and fixed.**
  `place_window_standard(wall, pos)` defaults to `curtain=None`, but `Window.add_window_standard`
  called `add_curtain(None)` **unconditionally**, and `add_curtain` falls back to the DEFAULT
  patterned drape mesh when given no texture — so there was **no way to author an undressed
  window**. It put cream floral curtains on a prison cell (and silently on every scene that omits
  the kwarg: retail/jewelry/toy storefronts, wine_cellar, pantry, warehouse). `add_window_picture`
  in the same file already had the correct guard — `add_window_standard` never got it. **Fixed in
  core** (`IDSDL/window.py`): return early with no curtain when `curtain_texture` is falsy.
  The identical latent bug remains in `add_window_floor_to_ceiling` — left alone deliberately,
  since fixing it changes the shipped renders of gym/dental_office/florist_shop/game_room.
  *Meta-lesson: no VLM constraint fires on "this room has the wrong KIND of object in it." The
  curtains were geometrically perfect. Only looking at the render catches a category violation.*
- **A phase-2 `place_on_top` gate must live INSIDE its group's `with` block.** I wrote
  `if PHASE >= 2: desk_unit.place_on_top(books)` *after* the block exited. A group compiles on
  `__exit__`, so the op registered too late and **never ran**: the books silently never entered the
  scene, the desk rendered bare — and the object COUNT in report.json still incremented (6), the VLM
  loop stayed clean, no lint fired. Found only by reading the exported `.blend` (the books existed
  as an un-instanced template at the origin). Gate inside the block, as `coffee_shop_v1` does, and
  **verify a phase-2 prop by eye (zoom the render), never by the object count.**
- **The float lint has a false-positive class: `bottom=` wall-mounts.** `[Lint] 'washbasin' FLOATS
  0.40 m` fired on every build — that 0.40 is precisely my `place_on_right_wall_left(sink,
  bottom=0.40)`. A wall-hung basin is *supposed* to float; `IDSDL/lints.py` tests AABB-bottom ≈ 0
  and doesn't exempt `bottom=` placements, so **any correctly wall-mounted basin/vanity trips it**.
  Don't take the lint's advice and swap the mesh. (Worth exempting `bottom=` items in core.)
- **The rejected idea, and why.** The weakest element is the DOOR (`place_door` uses a fixed
  *domestic wooden* door mesh, so the front view reads barracks). The obvious fix — a barred vision
  hatch hung in the door's own wall slot — was designed and then **rejected on geometry**: a slot
  wall object centres at y=1.5 m, putting its AABB bottom (~1.22 m) BELOW the bunk's top (1.52 m),
  which makes the automatic wall-object-clearance pass slide the **bunk** sideways along the front
  wall, off its wall and into the middle of the cell (the hospital_room wardrobe mechanic). Not
  worth wrecking a converged layout. **Check a wall object's AABB bottom against the tops of nearby
  floor furniture BEFORE hanging it.**

## Asset gaps (ingest candidates, in priority order)
1. **A stainless prison toilet/sink COMBO unit** — the fixture that would nail the category. Does
   not exist: every "stainless steel toilet" hit is a toilet BRUSH or a domestic ceramic bowl
   (the dataset is home-furniture biased, exactly as the catalog warns for institutional fixtures).
   Substituted a plain white toilet + wall-hung basin, adjacent, as one plumbing wall.
2. **A steel cell door** (solid, with a vision slot / food hatch), and/or a barred sliding gate.
   `place_door`'s mesh is fixed, so this needs a door-mesh hook, not just an ingest.
3. A grey-steel institutional bunk (the white/cream mesh reads a touch IKEA).

## VLM feedback we hit and how we resolved it
- `rescale room by 0.69` (Ph1) → `0.69` (Ph2): **unidirectional and undecayed**, and the shell had
  auto-sized to 4.0×5.1 m — a dormitory, not a cell. Per the vote-train rule, that is signal: one
  decisive `modulate_scale=0.7` **at** the vote (bakery: pick at it, not above it) → ~2.8×3.6 m.
  Shrinking below 1.0 is safe HERE (laundromat, not locker_room): the room is genuinely sparse and
  no fixed-size wall run overflows its slot.
- `rescale room by 1.1` (post-shrink) → **declined**: a flip ACROSS neutral immediately after one
  decisive application is the converge signal (music_studio/classroom). It then settled to
  `no rescale` on its own.
- `rotate desk by 180` (once) → **declined by eye**: the render shows the desk's knee-hole and its
  stool correctly facing the room; 180° would drive the working front INTO the wall. Did not recur.
  (The familiar desk-rotation noise class.)
- Clean by construction all the way through: `no rotation` / `no wall overlap` on **every** build —
  explicit `face(stool, toward=desk)` inside the unit, `facing` omitted on all wall placements (the
  heuristic already turns each piece into the room), the door and the wall fixtures in disjoint
  slots, and the bars on a freeform mount that claims no slot.

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed.
