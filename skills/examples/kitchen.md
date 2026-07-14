# Kitchen — worked example

> ## BUILD A KITCHEN ON ONE COMPLETE FITTED KITCHEN UNIT SET. DO NOT ASSEMBLE ONE FROM PARTS.
>
> A kitchen is one of the **trickiest** scenes in the library, and the trick is entirely in the
> asset choice. Take **recipe A** below. It is not a preference — it is the recipe.
> (Kunal, restated 2026-07-13, after recipe B was built and shipped in ignorance of it.)
>
> **The four standing rules:**
> 1. **Use the full kitchen unit SET** — one mesh with the cabinets, hob, hood, oven, sink and
>    usually the fridge/dishwasher already in it. Don't struggle to assemble one yourself.
> 2. **NEVER place anything on, in, or around the set.** No `place_on_top`, no `place_inside`,
>    no `place_rug`, no `add_lighting` anchored to it. Placement onto a bundled set is a
>    nightmare. Do not attempt it.
> 3. **A separate sit-at counter is allowed ONLY if the set has no `island`** (check the tag —
>    only 3 of 68 units have one). And rule 2 applies to that counter too: **nothing on it.**
> 4. **Fill the remaining gaps (fridge/dishwasher/…) from the component ANNOTATIONS**, not by
>    guessing — `IDSDL/datasets/assets/kitchen_components.json`. Often there is no gap at all.
> 5. **ALIGN THE UNIT TO THE WALLS — put it in a CORNER, never a wall centre.** A fitted kitchen
>    is *joinery*: every run of it that can touch a wall, must. See the next section — this is
>    what separates a kitchen that looks installed from one that looks dropped in the room.

## The ALIGNMENT rules — read the `shape` tag, then pick the corner (Kunal, 2026-07-13)

**The mistake to avoid:** `place_on_back_wall_center(kitchen)` lints clean, renders clean, converges
VLM-clean — and looks *wrong*. A U-set centred on a wall projects **both** wings into open air; an
L-set centred on a wall leaves its leg jutting into the room. The unit reads as a freestanding block
someone dumped in the middle of the floor, not as cabinetry installed against the building. No
constraint and no VLM signal will ever tell you this. It is pure composition, and it is on you.

| `shape` | where it goes | why |
|---|---|---|
| **L** (14/68) | the CORNER the leg points into — leg on the right ⇒ **back-right corner** | the leg then lies ALONG the side wall instead of jutting out |
| **U** (4/68) | a CORNER: back run on one wall, one wing flush ALONG the adjoining wall | two runs is the most a U can align. The **third wing is then an exposed PENINSULA** |
| **straight** (49/68) | a wall centre *works*, but a corner still reads better | joinery starts at a wall |

**The U's corollary — the exposed wing needs a JOB.** Two of a U's three runs touch walls; the third
cannot. Left alone it looks like a mistake. Place a **functional group BEYOND it** (a breakfast
counter, a dining zone) and the same wing instantly reads as an **open-plan peninsula dividing cook
from eat** — which is exactly what a real open kitchen is. This is not decoration; it is what makes
the corner placement legible.

**Windows go on a wall OPPOSITE the unit's corner.** Unit in the back-right corner ⇒ window on the
**LEFT** wall. Daylight then rakes ACROSS the cabinetry and models it; a window behind or beside the
unit just backlights it into a silhouette.

### Two API traps that will silently break the alignment

```python
room.place_on_back_right_corner(kitchen, facing="front")   # BOTH of these matter
kitchen.is_static = True
```

1. **You MUST pass `facing` explicitly.** Omitting it does NOT mean "no rotation":
   `facing_to_rotation()` *raises* on `None`, so the `@placemethod` heuristic fills one in — and for
   a corner it chose `"left"` (**−90°**), which spun the whole U round to open sideways and put its
   back run against the wrong wall. `facing="front"` = rotation 0 = the mesh's own orientation.
2. **You MUST pin it with `is_static`.** A corner op sets a flush position from `wall_deltas` on
   both axes — but corner ops are **not** in `WALL_FURNITURE_OPS`, so unlike a
   `place_on_<wall>_wall_*` piece they are **never re-pinned flush after the solve**. The
   GradSolver's exploration floor duly walked the set **0.44 m off the back wall**
   (living_room_cozy's thin-wall drift, now on a hero). `is_static` zeroes its gradient every step
   so it stays exactly where you put it, while still *exerting* force on its neighbours.

Measured result (`kitchen_set_v2`): set at x=[3.55, 6.40] with the right wall at 6.40 and
y=[0.00, −2.99] with the back wall at 0 — **gap to both walls: 0.000 m.**

### Verify the mesh's shape yourself — rasterise it, don't trust the caption

The `shape` tag tells you L/U/straight, but not **which way the U opens** or **which side the L's leg
is on**, and you need both to choose the corner. Project the mesh's vertices onto the XZ plane:

```python
m = trimesh.load(obj.mesh_path, force='mesh', process=False)
x, z = m.vertices[:, 0], m.vertices[:, 2]      # DSL: x = width, z = depth, y = up
# bin into a small grid and print '#' / '.' — the U/L is immediately readable
```
For `future/3c2bf09e` this printed a solid back run at z-min with two wings running to z-max — i.e.
the open side is **+z**, which under rotation 0 faces the room front. That single check is what told
me the back-right corner (rather than back-left) would land the right wing along the right wall.

## Pick the set from the annotations — this is the whole game

`IDSDL/datasets/assets/kitchen_components.json` hand-tags all **68** units in the
`kitchen_set` pool (the `KitchenUnitRetriever` pool, `assets/kitchen_set.json`) with
`components` + `shape`. **Rank by completeness and the choice makes itself** — do not text-query
for a set and hope:

```python
import json, collections
c = json.load(open('IDSDL/datasets/assets/kitchen_components.json'))
for k, v in sorted(c.items(), key=lambda kv: -len(kv[1]['components']))[:10]:
    print(len(v['components']), v['shape'], k, sorted(v['components']))
```

Component vocabulary and how rare each is (68 units):
`base_cabinets` 68 · `countertop` 64 · `sink` 62 · `cooktop` 57 · `wall_cabinets` 56 ·
`oven` 34 · `range_hood` 25 · `microwave` 14 · `dishwasher` 8 · **`fridge` 5** · **`island` 3**.
Shapes: straight 49 · L 14 · U 4.

So `fridge` and `island` are the scarce tags, and they are exactly the two that change your
program: a set without a fridge means you must add one; a set **with** an island forbids a
separate counter (rule 3). The top of the ranking:

| # comps | shape | id | note |
|---|---|---|---|
| **11** | U | `future/7f4cdaf8-255d-4660-b890-900a0e31a8f7` | the only 11/11 — everything **+ an island**. Take this and add NOTHING but a dining table |
| **10** | U | `future/3c2bf09e-eb79-4a8f-a3f4-36446e9ea656` | **the one this scene uses** — navy; everything except an island, so a separate counter is legal |
| 8 | straight | `future/4253258a-c066-4ccd-a126-f67b1cead6a5` | complete straight run **incl. fridge** — the safest shape (see the camera trap below) |
| 8 | straight | `hssd/168286ceb4f9758dc69789c4d41b5238e0c2c817` | warm wooden, microwave not fridge |

---

# Recipe A — one complete fitted set  ← **USE THIS ONE**

The kitchen that taught: **use ONE complete fitted kitchen set, don't assemble separate pieces.**
Kitchens are the strongest "set asset" category — even more than the bathroom vanity/toilet sets
(see `../workflow/asset_selection.md` "Set assets" and `set-assets-and-scaling`).

## Prompt / plan
"A spacious, beautiful modern eat-in island kitchen." Planner (ALWAYS run it first): sage handleless
cabinetry, a white waterfall-stone island with bar seating, integrated appliances + statement hood,
brass globe pendants, a casual dining nook. Working scene: `scenes/work/kitchen_eatin.py`.

## The core lesson: ONE complete set, not glued-together pieces
A **complete fitted kitchen set** is a single mesh that bundles base + wall cabinets ("vanity"), the
cooktop/stove, the chimney/hood, *sometimes* a fridge, AND a separate island/countertop. Pick ONE good
comprehensive set as the backbone and add only the genuine GAPS (island/stools/dining nook, maybe a
fridge). (First pass assembled pieces and looked incoherent; Kunal redirected to the single set.)

**Finding the set — hand-label its components.** Browse "complete fitted kitchen set … with island",
curate a pool (`assets/kitchen_set.json`, already a `KitchenUnitRetriever`), then label what each unit
bundles with the component tagger (`tools/build_kitchen_tagger.py` → `datasets/assets/
kitchen_components.json`: multi-select chips base/wall cabinets, cooktop, oven, range_hood, sink,
fridge, island, …). The labels tell you which set is most complete and exactly what's left to add.

## Sizing: cabinetry MAXES OUT the room height (floor-to-ceiling)
Room interior HEIGHT is hard-clamped to **3.0 m** (`RoomGroup`: `self.HEIGHT = min(max(heights+2,3),3)`).
Scale a kitchen set by **HEIGHT** (`_fit_height` uniform, target ~2.9–3.0 m), **NOT** `_fit_width` —
width-fitting a tall run overshoots and pokes the mesh THROUGH the ceiling (the bug we hit). Tall
oven/pantry columns also go floor-to-ceiling. Fridges read small at "real" width → size generously.

## A complete set is ONE mesh — you CANNOT edit it at part level
You can't recolor the uppers, restyle just the island, or move the bundled cooktop. The only lever is
to **swap the whole set** for a different complete set that already has the look you want. If a
planner/refine target asks for (e.g.) sage fronts but the set has black uppers, re-browse the pool and
swap the pinned `asset_id` — don't try to "edit" it.

## Lighting on a bundled-island set
The island is inside the set mesh, so a pendant group can only anchor to the WHOLE set — `add_lighting`
then spreads pendants across the full footprint and some clip the floor-to-ceiling cabinets, while
N×500 W area-lights blow the room out. `add_lighting` splits a fixed energy budget across N now (so
count no longer overexposes), but **render, then flag any OOB / overlap** rather than shipping it. A
clean pendant trio over just the island isn't reliably placeable on a bundled-island set.

## Status
`scenes/work/kitchen_eatin.py` — built around one complete set `future/a3cead55` (cabinets + cooktop
+ oven + sink + island with bar stools), floor-to-ceiling; added fridge, styled console (with
`add_clearance` front clearance), bare picture window, clock, pendant lighting. Not yet promoted to
`scenes/kitchen.py`.

---

# Recipe A, worked end-to-end — "Navy Anchor Kitchen, open-plan"

Status: **built & converged** — `scenes/work/kitchen_set_v2.py` + `kitchen_set_v2.py` beside this
file, seed=3. Final: `no rotation / no wall overlap`, no `[Lint]`/WARNING lines, at
`modulate_scale=0.92`. Room 5.9 × 6.7 × 3.0 m. Set = `future/3c2bf09e` (10/11 comps, navy U).

> **v1 (`kitchen_set_v1.py`) is kept only as the counter-example.** It put the same set at
> `place_on_back_wall_center`, converged VLM-clean, and looked like a kitchen dropped in a field.
> v2 is the same scene, corner-aligned. If you are copying a skeleton, copy **v2**.

## The layout — corner-aligned U + an open-plan zone beyond the peninsula
Set-piece hero (dental_office's pattern), aligned per the rules at the top of this file:
- **back-right corner**: the U-set. Back run on the back wall, right wing flush along the right
  wall, **left wing exposed as the peninsula**.
- **centre**: the breakfast counter + a 3-stool row — the functional group *beyond* the peninsula.
- **front row**: the dining zone — the second open-plan group (and it earns its keep geometrically,
  see the camera bounds below).
- **left wall**: the window — *opposite* the unit's corner.
- back-left corner: a floor palm. Front wall: door + one framed print.

```python
kitchen = scene.AddAsset("...", asset_id=KITCHEN_SET)
kitchen.scale(kitchen.get_width() * 2.4 / kitchen.get_height())   # scale BY HEIGHT (below)
kitchen.is_static = True                       # corner ops are never re-pinned — see the traps above

counter = scene.AddAsset("...", asset_id=COUNTER)      # legal: this set has no `island` tag
with scene.AroundGroup(sparsity=0.12, jitter=0.15) as bar:
    bar.set_anchor(counter)
    bar.place_rectilinear(longer_side1=3 * scene.AddAsset("...", asset_id=STOOL))
    bar.add_lighting("a warm brass dome pendant light", density=0.12)   # on the BAR, never the set
    bar.place_rug("a patterned woven runner rug", size=0.9)

with scene.AroundGroup(sparsity=0.05, jitter=0.15) as dining:          # the open-plan second zone
    dining.set_anchor(scene.AddAsset("...", asset_id=TABLE, width=1.4))
    dining.place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])

with scene.RoomGroup(modulate_scale=0.92, randomness=0.0) as room:
    room.place_on_back_right_corner(kitchen, facing="front")   # facing is MANDATORY (see traps)
    room.place_on_center(bar, facing="front")                  # beyond the exposed left wing
    room.place_on_front(dining, facing="back")
    room.place_on_back_left_corner(plant, facing="front")
    room.place_window_standard("left_wall", position="center", curtain="...")  # OPPOSITE the corner
```

## THE TRAP THIS BUILD FOUND: a full-height set BLINDS the interior cameras

The single most important thing on this page after "use the set".

`RoomGroup` auto-sizes a shell that merely **fits** its furniture. A fitted set is a
**2.85 × 3.00 × 2.40 m block** — so the auto-sized room has the set's wings touching both side
walls and *zero* circulation. And the interior cameras sit **on the room centreline, at
0.55 × ceiling ≈ 1.65 m, just inside each wall** (`renderer/utils.py: eye = fz + 0.55*H`,
`inset = 0.92`) — so they end up **INSIDE the cabinetry**. Phase-1 v1: the front view came back
**solid black** and the left view was a **wall of larder door**.

**No VLM signal sees this.** The loop returned `no rescale / no rotation / no wall overlap` on the
build with a solid-black view. This is bakery's "a fixture taller than ~1.4 m at a wall centre
blinds that view" rule at its extreme — and there, at least, it produced hallucinated rotation
flags. Here it produced *nothing*. **Only your eye catches it: open all four views, every build.**

**Corner-aligning the set (v2) fixes the composition and MOST of the cameras at once** — a corner op
lands in the OUTERMOST grid column (`compute_grid_dims`), so the hero stops straddling the
centreline where the cameras sit. v1 needed `modulate_scale=1.10` purely to buy camera clearance;
v2 needs no inflation at all and still shrinks to **0.92**.

But it converts the trap into a **computable bound**. With the set `is_static` and flush in the
back-right corner, shrinking the shell slides the walls toward a *fixed* hero, so:

```
front camera clears the set   <=>  W > 2 x set width   = 5.70 m
left  camera clears the wing  <=>  D > 2 x wing depth  = 5.98 m
```

| `modulate_scale` | W × D | verdict |
|---|---|---|
| 1.00 | 6.40 × 7.32 | clear, but roomy |
| **0.92** | **5.89 × 6.73** | **clear, with margin on both bounds** ✅ |
| 0.90 | 5.76 × 6.59 | the hard floor — no margin left |
| 0.85 *(what the VLM asks for)* | 5.44 × 6.22 | **FRONT VIEW GOES SOLID BLACK** |

**So the persistent `rescale room by 0.85` vote is DECLINED, permanently, and the reason is
arithmetic, not taste.** Compute the bound; don't negotiate with the occupancy metric, which cannot
see cameras. And note the depth bound is *why* the dining zone exists: a front-row occupant is what
pushes D past 5.98 m, which is a cleaner lever than inflating with `modulate_scale` (that would
grow the width too, and the width was already right).

> **Corollary — prefer a `straight` set (49 of 68) when you can.** A straight run is ~0.6 m deep,
> so it never traps a camera and imposes no depth bound at all. The U's 3 m-deep wings are what
> caused all of the above. Take the U only when you actually want the wrap.

## Other gotchas from this build
- **Scale the set BY HEIGHT, never by width.** Room HEIGHT is hard-clamped to **3.0 m**
  (`RoomGroup.max_height`, groups.py:1287); width-fitting a tall fitted run overshoots and pokes
  the mesh **through the ceiling**. Idiom: `obj.scale(obj.get_width() * H / obj.get_height())`.
  Native 2.40 × 2.02 × 2.52 → at H=2.4: 2.85 × 3.00 footprint.
- **Pick a BARE-TOP counter mesh.** The best-matching blue island (`future/a360edba`) has bowls and
  a jug **modelled into the mesh** — that violates the no-smallwares rule by proxy. `hssd/f8b8235c`
  (navy, bare marble top, 1.50 × 0.90 × 0.60) is the one to pin.
- **Phase 2 is EMPTY, and that is correct.** Nothing on the set, nothing on the counter. The whole
  vibe layer is FLOOR + WALL: rug, floor palm, framed print, window, and the pendant anchored to
  the **bar group** (never the set — a pendant group anchored to a set spreads fixtures across the
  entire U footprint and clips them into the cabinets). This is operating_room's **inverted vibe
  layer**: the room reads right *because* the worktops are clean.
- **`add_lighting` fixture came back a ~1.2 m DRUM shade** that dominated the ceiling. It takes no
  `asset_id` (corridor's lint), so the size lever is its third arg: `modulate_scale=0.4`.
- **Floor texture: "warm oak" and "medium brown oak" both embed to a genuinely SALMON-PINK plank.**
  Verified **offline** by resolving the string through `WallTextureRetriever` and opening the
  matched `texture.png` — 5 s, versus an 8-min build per guess (office_modern's rule). So this was
  a *matching* bug, not the renderer washing a correct match out (bakery's opposite case, which
  looks identical). `"dark brown hardwood floor"` matches a real warm oak.
- **You cannot fix the set's colours.** Its larder column renders taupe, not navy, and both
  worktops are dark where the plan wanted light. A set is ONE mesh — the only lever is swapping the
  whole set. Don't try to edit it.

---

# Recipe B — the MODULAR run (works, but do not reach for it first)

> **Read the box at the top of this file before using this recipe.** B exists because it was built
> before recipe A was found, and it does converge VLM-clean — but it took ~5 builds and a bespoke
> hood-mounting mechanic to reach what recipe A gets in one asset. **Use B only when the plan
> dictates a palette/layout no set in the pool can give you.**
>
> **Retrieval gap, logged twice (2026-07-12 and 2026-07-13):** on BOTH kitchen prompts,
> `retrieve_context` failed to surface this file — it chose bar+laundromat the first time and
> dental_office+bathroom+bar the second. So the reasoner will not hand you the set recipe. If you
> are building a kitchen, come here first; more generally, **`browse`/`catalog` for an existing
> recipe for your category before trusting the reasoner's selection.**

Status: **built & VLM-clean** ("Warm Marble Kitchen with Blue Panel Rhythm", `scenes/work/kitchen_v1.py`
+ `kitchen_v1.py` beside this file, seed=11). Final compile: `no rescale / no rotation / no wall
overlap`, no `[Lint]`/WARNING lines, at `modulate_scale=0.85`. Built through the guided 9-gate flow
(flow_0712_220546_f777): two phase-1 layout builds, one phase-2, two full builds. Room 4.38 × 5.77 × 3.0 m.

## Prompt(s) this covers
- "a kitchen", "a family kitchen with an island", "an eat-in / open-plan kitchen". Drop the dining
  cluster for a pure galley; keep it for a prep-to-dine brief.

## Plan summary (from the planner)
"Warm Marble Kitchen with Blue Panel Rhythm and Social Prep-to-Dine Flow": cream walls, light wood and
marble surfaces with a DARK cabinetry run for depth; a range with glass-front upper cabinetry; a blue
tile backsplash and tall blue paneling; a marble counter with a brass faucet under a generous window;
a light-wood dining corner; brass pendants over the work zone; greenery and tactile props.

## The layout idea: a CONTINUOUS RUN on the long wall + a facing work anchor
A kitchen is procedurally a straight service line plus an island (the bar's counter/back-bar spine, the
laundromat's one-heavy-wall machine run). Six floor slots:

- **BACK (hero) wall** — the cook run as ONE rigid `GridGroup` row: base cab | range | base cab, at
  `sparsity=0.02` so the modules touch and read as one continuous counter, not three pieces standing
  near each other. `place_on_back_wall_center(cook_run)`.
- **ABOVE the run** — the chimney hood + two glass-front uppers, as a SECOND `GridGroup` row mounted up
  the wall (the mechanic below). Both rows are symmetric about their own centre and go in the same wall
  slot, so the hood lands dead over the range (verified in the blend: hood x=2.08, range x=2.08).
- **CENTRE** — the island (the same walnut base cab, `width=1.8`) + a 2-stool row + the pendants.
- **LEFT wall** — the sink RETURN (the short L leg), under a standard window.
- **RIGHT wall** — the storage block: fridge in the back slot, blue pantry in the front slot.
- **FRONT** — the dining cluster; door in the front-right slot.

## Pinned assets
The dataset covers kitchens **WELL** — contrary to the catalog's "appliances are a likely gap" warning.
Ranges, hoods, fridges, islands, base/upper cabinets and sink units all have strong dedicated meshes,
and so do all the identity props.

| Role | id | note |
|---|---|---|
| Base cab / island | `hssd/559f21c7f5628a83b31d616e90bdcc02e7744731` | walnut shaker + **WHITE MARBLE top** = the plan's whole palette in one mesh. Used ×6 |
| Sink unit | `hssd/048d80c36ddc6ac63785ca08ccf231431195717c` | wood cabinet + built-in steel basin + faucet — a SET |
| Range | `hssd/4e74376ca5c86ab82bd86383f3551ab23f2d6c34` | stainless, black glass door; 0.60 × 0.90 × 0.64 |
| Hood | `hssd/3904b36e135441d887b1328d7fae230b6fcb875e` | stainless chimney; `scale(0.75)` ≈ the range's width |
| Fridge | `future/a266bc1f-0685-3080-beeb-b09d60a4f5ca` | side-by-side, visible handles + dispenser — legible at distance |
| Pantry | `hssd/722d9b8b0d8ad98e8798840b918121d2c126fa26` | captioned "tall **gray**" — renders **BLUE-GREY paneled**. This is the plan's blue accent |
| Upper cab | `hssd/4c911c25364d1cbb37493ecfaa6b889d931c78ac` | walnut, two GLASS doors — stock it |
| Stool | `hssd/609af80af4fb45e772a2109a7a4876b73601fb6b` | light wood slat-back, h=1.23 |
| Dining table | `future/9ff76d8d-af20-493d-a17c-a4aaaa94114a` | light oak, **BARE top** (no baked-in chairs — the SET trap) |
| Dining chair | `hssd/24fd37914321b915b9503d25add09332900a8d61` | light wood classic |
| Pendant | `hssd/bf898898fd1d92bc217a8b8943d178589c2b316f` | vintage brass dome |
| Props | fruit bowl `hssd/51a22c69…`, utensil crock `hssd/xxxx112ab20a…`, blender `hssd/a88edd11…`, canisters `hssd/221f50f3…`, pitcher `hssd/59d54ccb…`, herb `future/15b3e770…`, plates `hssd/3db8975f…`, bowls `hssd/e14232e0…` | every kitchen identity prop EXISTS — mass them |

## The one hard mechanic: mounting a HOOD and UPPER CABINETS
This is what a kitchen needs that no other example had, and the naive paths both fail:

- `place_on_wall_*` (wall-HUNG) is **FLAT-only**. A hood (0.47 m deep) or an upper cabinet (0.45 m)
  hung that way renders as furniture floating in mid-air. This is why the **laundromat build simply
  dropped its planned uppers** — but a kitchen cannot drop its hood; the range/hood silhouette IS the
  reads-as test.
- The right tool is the wall-ADJACENT path with the **`bottom=` lift** —
  `place_on_<wall>_wall_<pos>(obj, bottom=1.50)` (the warehouse exit-sign / retail wall-shelf mechanic)
  — which mounts a deep mesh up the wall at a real height.
- **But that path registers the piece as FLOOR furniture**, so the 2D-footprint `OverlapConstraint`
  sees the hood and the range *beneath* it as interpenetrating and shoves them apart along the wall.
  Two flags fix it, and both are needed:
  - `obj.ignore_overlap = True` — skipped by the gradient, `_snap_overlaps`, `_clamp_to_bounds` and
    `_warn_overlaps`. A 2D clash with the thing you are mounted ABOVE is not a real one.
  - `obj.is_static = True` — grad zeroed every solver step, so the action sampler's **exploration
    floor** cannot random-walk it along the wall (the living_room_cozy thin-wall-furniture drift; a
    hood is the worst case — small footprint, open space in front).
  - `_repin_wall_furniture` still snaps it flush and **preserves the Y lift** (it only translates in
    x/z), so it stays pinned above the range.

```python
hood = scene.AddAsset("a stainless steel chimney range hood", asset_id=HOOD)
hood.scale(0.75)                       # ~ the range's own width, not a canopy over the whole run
with scene.GridGroup(sparsity=0.02) as upper_row:
    upper_row.place_row([upper_l, hood, upper_r])
for _u in (upper_row, upper_l, hood, upper_r):
    _u.ignore_overlap = True
    _u.is_static = True
...
    room.place_on_back_wall_center(upper_row, bottom=1.50)   # SAME slot as the run below it
```

**Mount the uppers as ONE ROW, not three separate wall placements.** The back wall is wider than the
2.8 m run, so uppers dropped in the wall's `left`/`right` slots hang out past the run's ends, floating
over bare floor. A row centred on the same wall slot as the run lands the hood over the range and the
uppers over the base cabinets. (`GridGroup` extends `SceneProgObject`, so it can be wall-placed with
`bottom=` like any object.)

## What worked / gotchas
- **One mesh, six placements — this is what kills the "mismatched styles" objection to recipe B.**
  The walnut+marble base cab IS the run (`width=1.1` ×2), the return (native ×2), and the island
  (`width=1.8`). `width=` lengthens without raising the counter — a uniform scale to 1.8 m wide would
  make the island absurdly TALL (the bar-counter rule).
- **A narrow SET asset can't be widened — flank it instead.** The sink unit is natively only **0.60 m**
  wide and placed alone read as a lost little side cabinet. It can't be scaled: uniform to a counter
  width makes it 1.5 m TALL, and a width-only stretch distorts the basin (the set-asset scaling rule).
  The fix is **compositional** — put base cabs either side of it in a `GridGroup` row and it reads as a
  continuous counter *with a sink in it*, which is what a real kitchen is. That row became the
  L-return the procedural signature sanctions. **This is the general answer to recipe A's "scale
  fights" warning: compose around a mis-sized module, don't rescale it.**
- **`place_on_top` on a RUN, not a module.** `place_on_top` always targets the group's ANCHOR, so anchor
  a `RelativeGroup` on the whole `sink_run` GridGroup — the props then spread along the continuous
  counter instead of piling on one cabinet.
- **Stock the glass uppers.** Their doors are GLASS; left empty they name the fixture, not the kitchen
  (the jewelry_shop product rule; the plan asks for dishes on show). Build ONE dressed unit and
  duplicate it — `place_inside` runs its sizing tournament PER CALL, so two units built separately get
  differently-sized crockery (design_principles). The dishes are children of the cabinet, and
  `get_world_transform()` composes parent transforms, so they **ride up the wall with it** when the row
  is mounted at `bottom=`.
- **The blue accent is a PROP, not a texture.** No blue-tile backsplash mesh or texture exists, and an
  accent clause in a wall-texture string dominates the embedding and recolours all four walls
  (classroom v1). The pantry mesh — captioned "tall gray", rendering blue-grey paneled — carries it
  (music_studio's rule). Honest gap: the plan's "blue panel rhythm" is weaker than drawn.
- **Tall pieces off the wall CENTRES.** Fridge and pantry went in the right wall's back/front slots: the
  interior cameras sit at ~1.4–1.5 m at each wall's centre and a taller fixture there blinds the view
  AND corrupts the constraints judged from the strip (bakery v1).
- Appliance clearance came **free** from `CategoryClearanceConstraint` — no manual clearance anywhere.

## VLM feedback we hit and how we resolved it
- **`rotate the kitchen island counter stools by 180` (Ph1) — DECLINED.** The left-wall view showed both
  stools correctly addressing the island. Same `place_rectilinear` false positive **bar.md** declined:
  the verb already gives the row a uniform straight facing (`anchor − 180`), and a per-stool
  `face(toward=island)` would aim each at the island's centre POINT and fan them inward. The vote did
  not recur. Render is the arbiter.
- **`rescale room by 0.79 → 0.80 → 0.80` — the cause was a bloated CLUSTER, not the item count.** v1
  seated the 4 dining chairs with `place_circle(4)` at `sparsity=0.2 / jitter=0.35`: they flung out into
  a ring far wider than the table, and THAT footprint auto-sized a cavernous shell with dead floor.
  Fixed structurally with `place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])` — two
  down each long side, correct for a RECTANGULAR table and a much tighter footprint — at
  `sparsity=0.05 / jitter=0.15`. **This generalises hospital_room's rule beyond wall queues: when a room
  feels too big, find the footprint culprit before reaching for `modulate_scale`.** Then held per
  render-wins-early and applied ONE decisive `modulate_scale=0.85` in the final phase → `no rescale`.
- **Chose 0.85 over the voted 0.80 deliberately.** The cook run and the sink return are FIXED-SIZE
  `GridGroup` rows; shrinking a shell below the footprint its placements dictate makes such rows
  overflow their slots into overlaps the solver cannot undo (the locker_room packed-room rule). The
  "empty" floor the vote reacts to is the working aisle around the island — the same
  legitimate-circulation-reads-as-empty effect as garage and corridor.
- **The full VLM loop went clean while the room still had two real defects** (empty glass cabinets, a
  blank right wall) — the jewelry_shop "converged is necessary but NOT sufficient" law again. Both were
  caught at the JUDGE gate by looking, not by a constraint, and fixed in the vibe layer (dishes inside
  the uppers; a framed still-life on the right wall; the wicker basket, which had rendered doll-sized at
  0.35 m, at `modulate_scale=1.6`).

## Manual constraints used
- **None.** Auto overlap/bounds + door clearance + the appliance/cabinet `CategoryClearanceConstraint`
  sufficed. The hood/upper mounting is geometric (`bottom=` + `ignore_overlap` + `is_static`), not a
  constraint — the bar's "geometry, not a clearance constraint, for a guaranteed relationship" rule.

## Possible refinements (not blocking)
- Walls and floor render washed-out near-white rather than warm cream / light oak. The texture match
  itself is correct, so this is the known room-scale-tiling + light-budget wash-out (bakery v1) — a
  renderer limit, not a wording bug. Don't burn iterations rewording it.
- No blue-tile backsplash and no open wooden shelf-over-range mesh exist — ingest candidates.
- Dishwasher and wall-microwave have no obvious meshes; the run reads complete without them.
