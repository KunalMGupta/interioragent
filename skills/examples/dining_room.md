# Family dining room — worked example

Scene: `scenes/work/dining_room.py` (seed=6), planner-driven **"Warmth-Centered Family Dining
Ensemble"**, built via the guided 9-gate flow. The **table-hub** pattern in its residential home
key. Converged `no rotation` / `no wall overlap` / zero lints, with the room-size vote decaying
1.05 → 0.97 → 0.99 (declined as noise). Five builds: 1 phase-1, 1 phase-2, 3 full (two of which
were the MOOD hunt below — the layout never moved after phase 1).

**BUILD IT AS:** `IDSDL_SKY=1.5 python workbench.py run scenes/work/dining_room.py` — see the
sky/budget lesson; a default-sky render of this program is not the scene.

## Prompt this covers
- "a (warm / family / formal) dining room": a rectangular table ringed with chairs, a set table,
  a sideboard/buffet, a chandelier, a rug, a window with drapes.

## Layout pattern — meeting_room's table hub, domesticated
This is `meeting_room.md` with the presentation wall swapped for a SERVICE wall. Copy that
skeleton; the four walls each still get a job:
- **CENTER = the table hub** — a dark trestle table stretched to `width=2.2` with a rectilinear
  ring of 8 upholstered chairs (3 per long side + 1 each end), `AroundGroup(sparsity=0.1,
  jitter=0.25)`, on a rug at `size=0.8`, lit by ONE drum pendant (`density=0`).
- **BACK = the service wall** — the low buffet at `place_on_back_wall_center` (default facing =
  into the room), a framed photo gallery hung above it, plant + floor lamp in the two corners.
- **LEFT = daylight** — `place_window_floor_to_ceiling` + cream drapes. **RIGHT** = a landscape.
  **FRONT** = the door.

## The one thing that makes it read as a DINING room: SET THE TABLE
A table + chairs is furniture; a table + chairs + **plates, glasses and a centerpiece** is a
dining room. This is jewelry_shop's product rule on a domestic surface — and it is only safe
because all three props were **verified to exist** at the audit gate (stacked dinner plates
0.85-0.88, a wine-glass/decanter set, a floral centerpiece in a white vase). Do not `place_on_top`
a dining prop you have not seen: the dataset has no per-seat *place setting*, and asking for one
returns something else (the kindergarten crayon-cup trap).

**Honest DSL limit:** `place_on_top` rows its items across the anchor's CENTRE, so the table reads
as being LAID (a central stack of plates + glassware) rather than as 8 discrete covers, which is
what the planner's collage shows. There is no DSL verb for "one prop in front of each seat". Don't
fake it with a prop that isn't a place setting.

## Lessons this scene encodes

### 1. On a room with ONE fixture, the brightness dial is the LIGHT BUDGET, not the sky — MEASURE IT
The room converged VLM-clean but rendered as a **bright showroom**, not "warm, lived-in". The
reflex (greenhouse's "brightness is a SKY setting") is only half the story. Measured, as mean pixel
value of one fixed view:

| build | sky | budget | mean |
|---|---|---|---|
| phase 1 | 3.0 | (no `add_lighting` yet) | 139 |
| phase 1 | 1.2 | — | **105** |
| full | 3.0 | 500 W | 197 |
| full | 1.5 | 500 W | **188** ← the sky barely moved it |
| full | 1.5 | **180 W** | warm, contrasty, done |

The sky is the dominant light **only until phase 3 adds `add_lighting`**. After that, its fixed
**500 W** point light dominates a ~27 m² room and flattens every surface to near-white — so
halving the sky changed a full render by 5%. `scene.light_budget = 180.0` is what let the pendant
read as a warm pool over the table while the glazed wall still supplied daylight. **Rule: sky is
the lever for an UNLIT or glazing-lit room; the budget is the lever the moment you hang a fixture.**
(wine_cellar reached the same dials from the dark side; its "tune ONE dial at a time" warning is
what kept these separable.)

### 2. `IDSDL_SKY` must be exported in the SHELL — setting it in the program is a no-op under workbench TOO
wine_cellar concluded "MCP `run_scene` ignores `IDSDL_SKY`, so build mood scenes from the shell."
That is incomplete and cost a full build here: `renderer/utils.py` binds `INTERIOR_SKY_STRENGTH` in
a **class body** (line ~694) at import time, and `workbench.py` imports `IDSDL.service` at its own
line 30 — *before* `runpy` executes your program. So a program-level `os.environ["IDSDL_SKY"]` is
already too late under **workbench as well as MCP**; the render you get back is still at 3.0 and
looks like the lever is broken. Export it: `IDSDL_SKY=1.5 python workbench.py run <prog>`. (The
`os.environ.setdefault` in the program is kept only for `python scenes/work/dining_room.py`, where
nothing has imported IDSDL yet.)

### 3. A wall-art mesh TALLER than its slot allowance will shove your furniture off its own wall
The gallery collage (`future/e2b0dcb4…`) measures **1.50 × 1.66 m**. Wall slots centre at y=1.5 m,
so hung natively its AABB bottom lands at **0.67 m** — *below* the 0.85 m buffet top standing right
under it. That is precisely the trigger for `_enforce_wall_object_clearances`, which slides the
**floor** piece sideways along the wall to un-occlude the art — i.e. the buffet would have walked
off the centre of its own service wall (hospital_room's wardrobe mechanic; prison_cell rejected a
door hatch for the same reason). Caught with `get_whd()` **before the first build**, fixed by
pre-scaling the collage to ~0.95 m high; the exported blend confirms bottom = **1.28 m**, clear of
the 0.85 m buffet. **Before hanging anything, compare its AABB bottom against the TOPS of the
furniture in front of it.**

### 4. A wrong texture MATCH is a 5-second offline check, never a rebuild
Walls rendered cool grey-white against a "warm" brief. Resolved the string offline against
`IDSDL/assets/wall_textures_embeddings.npz` (office_modern's rule): `"warm greige painted wall"`
matched a **light gray plaster** at 0.596 — a genuine *matching* bug, not the bakery/office_modern
"correct match paled by the renderer". `"solid warm beige smooth uniform wall"` matches a true
beige at **0.744**. Texture strings are matched against CAPTION text — word them like a caption.

### 5. The dining-table SET trap is real, and the query defuses it
"a small round dining table" / "a cafe table" routinely return a table with chairs **baked into the
mesh**, which double-seats a group that supplies its own chairs. Querying **"a rectangular dark wood
dining table, no chairs"** returned six BARE tables. Verify on the contact sheet, not on faith.

### 6. Sideboard picks skew TALL — and a tall piece at a wall centre blinds that camera
The picker's #1 for a sideboard was a tall modern chest and #2-#4 were tall hutches (multi-surface,
and over the ~1.4 m interior-camera eyeline that sits at each wall's centre — bakery's garbage-view
rule). `browse` found a genuinely low buffet (1.50 × 0.67 × 0.35); scaled **by height** to a real
~0.85 m (`obj.scale(w * H / h)`), giving a 1.9 m run that stays far under the camera band. All four
views stayed clear from the first build.

## Asset coverage (all off-the-shelf, no ingest)
Dining tables, upholstered chairs, buffets, drum pendants, dinner plates, glassware, floral
centerpieces, brass floor lamps and plants are all well covered. Pinned for palette/form: table
(`hssd/66602a70…`, bare dark trestle), beige upholstered chair (`hssd/6c368c15…` — pin it, the
chair carries the palette), low warm-wood buffet (`future/ef3867e2…`), the known-flat wool rug
(`hssd/249bbdc…`), the gallery collage **with real photo content** (`future/e2b0dcb4…` — the
living_room_cozy pick; its rank-1 sibling `future/09f28392…` is BOTH reversed-front and
empty-frame), centerpiece, plates, glassware. `add_lighting` takes **no `asset_id`**, so the
pendant query was audited directly until the beige drum shade was its top pick — a fabric drum has
a small emissive area and a short drop, which is what dodges the executive_office sputnik blowout.

Palette: warm beige walls, dark hardwood floor, dark trestle table, cream upholstery, cream linen
drapes, warm brass lamp.

## VLM feedback we hit and how we resolved it
- **Room size** — `1.05` (Ph2) → `0.97` → `0.99`: held per render-wins-early, then **declined
  entirely**. A vote that never leaves ±5% of neutral is noise, not a train (casino's declined 1.05).
  The layout never moved after phase 1.
- **`no rotation` / `no wall overlap` from the first build to the last** — by construction:
  `place_rectilinear` gives the chair ring a uniform straight facing (no per-chair `face()`, which
  would fan the end chairs inward — kitchen v1), and every wall placement omits `facing` so the
  default heuristic turns it into the room.
- **The loop was clean on the bright showroom.** Both real defects this scene — the cool walls and
  the 500 W washout — were invisible to every constraint (geometry was flawless) and were caught by
  LOOKING at the render against the plan. Loop-clean is necessary, never sufficient.
