# Library — worked example ("Grand Public Library Reading Room")

Built end-to-end coarse-to-fine from the planner target (`tmp/library/plan/plan.png`). The working
program is `scenes/work/library.py` (seed=36). Read alongside `../workflow/coarse_to_fine.md`. This
is the reference for a **symmetric-corridor reading hall**: twin bookcase runs on the long walls +
a communal reading-table column down the centre. It also carries a **retrieval stress-test** kickoff
and the **`add_lighting` fixture-size ↔ count coupling** lesson.

## Prompt(s) this covers
- "a library" / public reading room / academic reading hall / study hall.

## Plan summary
Planner → **"Grand Public Library Reading Room — Warm Wood, Layered Light, Symmetry."** Twin
FLOOR-TO-CEILING walnut bookcases line the two long walls to form a legible CORRIDOR; a long
communal READING TABLE runs down the centre axis, ringed with wooden chairs, each table wearing
**green banker's lamps** under soft warm pendants; a cosy **leather ARMCHAIR nook** sits by a grand
arched window (the focal end); a librarian **REFERENCE desk** anchors the entrance. Palette: walnut/
oak, dark brass, **green** (lamps + upholstery), a patterned wool rug, linen curtains, leather.
Light is layered: window daylight + pendants + banker's lamps. (This is the executive_office's
"Library-Backbone" look scaled up to a public hall — retrieval risk is LOW.)

## Kickoff: a RETRIEVAL STRESS TEST before any placement
The user's ask — "first make sure most assets are available" — is a reusable habit. Before writing
placements, batch-route ~40 candidate library queries through the **warm visual picker** and audit
chosen-desc + similarity, so gaps surface up front (see `../workflow/asset_selection.md` → "Batch
retrieval stress test"). Verdict for a library: **~32/40 on-target**; the dataset covers it well.

Pinned good picks (all eyeballed via preview render):
- **Bookcase** `hssd/b356640d…` — dark walnut, leather-bound books + lower cabinet (the hero; dupe into a row per long wall).
- **Reading table** `hssd/e5c0975d…` — long walnut rectangular top (retrieved via "a long rectangular **dark walnut dining table**", 0.71; the literal "library reading table" query was weak at 0.53 with white legs).
- **Library chair** `hssd/b98286cc…` — black frame + cushioned seat, slat back.
- **Green banker's lamp** `hssd/721b75b4…` — the signature prop; it **exists** (green dome desk lamp). MUST be shrunk (below).
- **Leather armchair** `hssd/613ba909…` — brown tufted, the nook hero.
- **Card catalog** `hssd/14532900…` — dark multi-drawer cabinet (a faithful card-catalog stand-in).
- **Reference desk** `hssd/7379d888…` — curved wooden reception desk.

Gaps, all worked around (no ingest needed): a **librarian reference/circulation desk** ("reference
desk"/"checkout counter" route to a *bookcase* or nothing — reword to **"a curved wooden reception
front desk"**, 0.81); a **rolling library ladder** (none — the bookcase asset already includes a
ladder motif + a step stool covers it); an **OPAC/computer terminal** and **directory signage**
(skip — off-theme prop risk, same as warehouse). None block the scene.

## THE layout: symmetric corridor (twin shelf rows) + a centre table column
Same family as warehouse/locker_room long-rows, but *symmetric*:
- **Bookcase run = `GridGroup.place_row(4 * shelf)` per LONG wall**, placed `place_on_left_wall_center` /
  `place_on_right_wall_center` with **`facing` OMITTED** (the heuristic faces the shelves' open side
  into the room; both walls rendered book-spines-in on the first try). Loading the two long walls is
  what makes the room read as a deep corridor.
- **Communal table = a column of table units down the centre.** Build ONE reading unit as an
  `AroundGroup` (table anchor + `place_rectilinear(3 chairs, 3 chairs)` on the two long sides +
  banker's lamps `place_on_top` + a `place_rug`), then `2 * unit` into a `GridGroup.place_grid(cols=1)`
  and `room.place_on_center(...)`. `place_on_top` runs ONCE on the composed unit (design_principles),
  so both tables get identically-sized lamps for free.
- **Short walls stay light**: reference desk + card catalog + door on the FRONT wall; the arched
  window + the armchair nook + a plant on the BACK wall.

## Working skeleton (final)
```python
scene = SceneProgRoom("Library", seed=36)
_SHELF, _TABLE, _CHAIR = "hssd/b356640d…", "hssd/e5c0975d…", "hssd/b98286cc…"
_LAMP, _REFDESK, _ARMCHR = "hssd/721b75b4…", "hssd/7379d888…", "hssd/613ba909…"

def reading_unit():
    with scene.AroundGroup(sparsity=0.28, jitter=0.35) as u:
        u.set_anchor(scene.AddAsset("a long walnut rectangular reading table", asset_id=_TABLE))
        u.place_rectilinear(longer_side1=3 * scene.AddAsset("a wooden library chair with a cushioned seat", asset_id=_CHAIR),
                            longer_side2=3 * scene.AddAsset("a wooden library chair with a cushioned seat", asset_id=_CHAIR))
        u.place_on_top(2 * scene.AddAsset("a green glass bankers desk lamp", asset_id=_LAMP, modulate_scale=0.3))  # SMALL (0.3)
        u.place_rug("a traditional patterned green and cream wool rug", size=0.9)
    return u
with scene.GridGroup(sparsity=0.4, randomness=0.1) as reading_hall:
    reading_hall.place_grid(2 * reading_unit(), cols=1)                       # two tables, centre column

with scene.GridGroup(sparsity=0.04) as shelves_left:  shelves_left.place_row(4 * scene.AddAsset("a tall wooden bookshelf full of books", asset_id=_SHELF))
with scene.GridGroup(sparsity=0.04) as shelves_right: shelves_right.place_row(4 * scene.AddAsset("a tall wooden bookshelf full of books", asset_id=_SHELF))

with scene.RelativeGroup() as nook:                                          # seat gets a table + its own light (design_principles)
    nook.set_anchor(scene.AddAsset("a cozy brown leather reading armchair", asset_id=_ARMCHR))
    nook.place_on_right(side_tbl)              # round side table + a small book stack (modulate_scale=0.6)
    nook.place_on_back_left(scene.AddAsset("a slender brass floor reading lamp", asset_id=_FLOOR))
    nook.place_rug("a small patterned wool rug", size=0.7)

with scene.RoomGroup(modulate_scale=0.9, randomness=0.12) as room:           # 0.9 after the 1.25<->0.8 oscillation
    room.place_walls(floor_texture="warm herringbone parquet oak wood flooring",
                     ceiling_texture="soft cream plaster ceiling", wall_texture="warm ivory plaster wall")
    room.place_on_center(reading_hall)
    room.place_on_left_wall_center(shelves_left)     # omit facing -> shelves face into the room
    room.place_on_right_wall_center(shelves_right)
    room.place_on_back_left_corner(nook, facing="front")   # nook faces the ROOM, not its side table
    room.place_on_back_right_corner(scene.AddAsset("a tall potted plant with lush green leaves"))
    room.place_on_front(reference, facing="front")         # reference desk+chair OFF the wall (see below)
    room.place_on_front_wall_left(scene.AddAsset("a dark wooden card catalog cabinet with many small drawers", asset_id=_CATALOG))
    room.place_on_right(book_cart)                          # fill the browsing aisle
    room.place_door("front_wall", position="right")
    room.place_window_standard("back_wall", position="center", curtain="floor-length cream linen curtains")
    room.add_lighting("a warm fabric drum pendant ceiling light", density=0.025, modulate_scale=0.4)  # see coupling note
    room.place_on_wall_front_center(scene.AddAsset("a framed classical oil painting portrait in a gold frame"))
    room.place_on_wall_front_left(scene.AddAsset("a large round wall clock with roman numerals"))
    # a few library-themed artworks on the back wall (pre-scale via width= so the mount clears the ceiling)
    room.place_on_wall_back_left(scene.AddAsset("a framed vintage botanical illustration print in a gold frame", width=0.7))
    room.place_on_wall_back_right(scene.AddAsset("a framed antique world map in a wooden frame", width=0.8))
scene.export("library.blend")
```

where the off-wall reference station is:
```python
_ref_desk  = scene.AddAsset("a curved wooden reception front desk", asset_id=_REFDESK, modulate_scale=1.2)
_ref_chair = scene.AddAsset("a brown leather office desk chair")
with scene.RelativeGroup() as reference:
    reference.place_desk_chair(_ref_desk, _ref_chair, gap=True)   # desk + librarian's chair behind it
    reference.face(_ref_chair, toward=_ref_desk)                  # chair turns to the desk
```

## VLM / layout feedback we hit and how we resolved it
- **Banker's lamps came out chair-sized.** `place_on_top` sized the green lamp to ~0.6 m domes that
  dominated the tables (small-prop-on-top oversizing). Fix: `modulate_scale=0.4` on the lamp → a
  believable ~0.4 m banker's lamp. Same fix pattern as any small on-top prop.
- **RoomProportions oscillated 1.25 → 0.8.** Phase-1 (anchors only) read tight → VLM wanted **1.25**;
  I grew to 1.1 and added detail → it flipped to **0.8** (now under-filled). Settled **0.9** and let
  the render arbitrate (occupancy is a call, not the oscillating vote — same as warehouse/bar).
- **`add_lighting` fixture-size ↔ COUNT coupling (the key new lesson).** The drum pendant renders
  ~1.5 m at `modulate_scale=1.0` and drops to table height, so I shrank it to 0.35 — which turned
  **5 pendants into a 35-pendant starfield**. `add_lighting` count ≈ `density · area / footprint`, so
  shrinking the fixture MULTIPLIES the count. Fix: drop `density` in step (0.12 → 0.025 at scale 0.4)
  → ~6 tidy pendants. When you change fixture size, re-tune density the opposite way. (Warehouse used
  the same lever the *other* direction: scale UP + density DOWN for a few big high-bays.)
- **"rotate armchair to face the side table" / "rotate floor lamp to face the chair"** (repeated) →
  **declined** as noise: a reading-nook armchair faces the ROOM, and a slim floor lamp is ~symmetric
  (same call as the executive_office "rotate sofa to face its own end table").
- **"rescale hardcover books by 0.6"** → applied `modulate_scale=0.6` on the nook's book stack.

### Follow-up feedback round (user notes)
- **"lamps too big"** → dropped the banker's lamp `modulate_scale` 0.4 → **0.3** (sits right on a table).
- **"the reference desk is flush to the wall — give it space; add a desk + chair; make it 1.2×."**
  Rebuilt the flush `place_on_front_wall_center(desk)` as an **off-wall desk+chair station**:
  `RelativeGroup.place_desk_chair(desk, chair, gap=True)` (the correct group — anchors the desk, seats
  the librarian on its back, `gap=True` leaves staff circulation), placed as a **floor** group with
  `room.place_on_front(reference, facing="front")` so the desk stands proud of the wall with the chair
  tucked behind it. `modulate_scale=1.2` on the desk. **Facing gotcha:** `place_desk_chair` rotates the
  desk to face the chair, so `facing="back"` pointed the patron panel at the WALL; `facing="front"`
  turns the serving side to the room. Add `reference.face(chair, toward=desk)` so the chair faces the
  desk. The VLM then repeats **"rotate reception desk 180 to face the chair"** — **decline it**: this is
  the *reception exception* — a service counter faces the patrons (the room), not its own staff chair.
- **"add a few library-themed paintings"** → hung a **botanical print** + an **antique world map** on the
  back wall (`place_on_wall_back_left/right`), pre-scaled with `width=` so the mount clears the ceiling
  ([[wall-art-mount-height]]). The long walls are full-height bookcases with no headroom for art, so
  wall art lives only on the two short walls (back = botanical/map, front = portrait/clock).

## What worked / gotchas (summary)
- **Symmetric corridor = twin `place_row` shelf runs on the LONG walls, omit `facing`.** Loading both
  long walls sets the deep-corridor footprint; the heuristic faces the shelves in on the first try.
- **Compose the reading table ONCE (`AroundGroup` + rectilinear chairs + on-top lamps + rug), then
  `N * unit`** into a `GridGroup(cols=1)` centre column — identical tables, one `place_on_top` tourney.
- **"library reading table" is a weak query** (0.53, white legs); **"long rectangular dark walnut
  dining table"** (0.71) is the right retrieval for a communal table. Describe the object + material,
  not the room (same lesson as casino's "don't put 'casino' in the query").
- **"reference/circulation desk" routes to a bookcase** — use **"a curved wooden reception front
  desk."** A reception desk is the correct stand-in for a librarian service desk.
- **A modest `place_window_standard` (not `_picture`)** keeps the focal window from becoming a big
  black night-void (executive_office lesson); a well-lit room hides the small void.
- **Green banker's lamps are the signature cue** — a bare reading table reads generic; the green
  domes + patterned rug make it read "library" instantly. The dataset HAS them; pin + shrink.
