# Art studio / painter's loft — worked example

## §0 v2 — REBUILT ON INGESTED EASELS. Read this before the rest.

**One correct mesh deleted ~40 lines of workaround.** `art_done.zip` (2026-07-13) brought three real
**2.00 m floor easels** — one holding a painted landscape (`custom/fa1ed245`), one a blank canvas
(`custom/3ae58737`), one bare (`custom/f65f7c3d`). Everything §1–§2 below fought simply evaporated:

| v1 had to… | v2 |
|---|---|
| hunt by SILHOUETTE past the picker's **kids' crayon easel** | `AddAsset(asset_id=EASEL_ART)` |
| height-fit 1.00 m → 1.65 m (the only real easel was a *tabletop* one) | loads at a true 2.00 m |
| discover `place_on_top` **shatters on a skeletal A-frame** (postage-stamp canvases) | the canvas is IN the mesh |
| stand the canvas on the FLOOR against the easel (no lift exists on anchor placements) | — |
| anchor the unit on the CANVAS to stop the verb showing its blank BACK | — |

**The rule (operating_room's, escalated): when the VLM loop is clean and the room still doesn't
convince, the answer is ASSETS, not placement — and a growing pile of workarounds IS the signal
that the asset is wrong.** The workarounds below are still worth reading: they are what you do
while the ingest does not exist, and §2/§3 generalise well past easels.

**Two v2-specific things:**
- **The 2.00 m easels are kept OUT of the left wall's CENTRE slot** (`back_left` + `front_left`).
  Interior cameras sit at each wall's centre at ~1.4 m; v1's 1.65 m easels already loomed there, and
  2.00 m would blind the view outright and hallucinate rotation flags (bakery).
- **Two ingested meshes REJECTED at the contact sheet** (filenames lie; the preview is the evidence):
  `canvas_stretcher` renders as a grey tapered **monolith**, not a canvas; `easel_stool_and_canvases`
  is flat-shaded **stylised** red/blue art that clashes with a photoreal room. 11/13 usable.
- **The ingest fix pass silently no-ops without `parent_clear`** — see workflow/vlm_feedback.md.
  The glTF importer parents meshes to EMPTIES, so zeroing an object's *local* location changes
  nothing in world space, and every asset comes out exactly as off-centre as it went in.

---

Status: **built & VLM-clean** (`scenes/art_studio.py`, seed=13; v1: 6× phase-1, 1× phase-2, 1× full;
v2: 1× phase-1, 1× full — `no rotation` / `no wall overlap` / no lints, room vote converged at 0.82
against `modulate_scale=0.85`).
Final compile: `no rotation`, `no wall overlap`, no `[Lint]`/`WARNING` lines; the room-size vote
decayed to `0.8` after one decisive `modulate_scale=0.85` and was declined. Supersedes the
29-line auto-generated draft (a `place_circle` of 4 easels), which was never built.

## Prompt(s) this covers
- "an art studio", "a painter's loft/atelier", "a studio with easels".
- More broadly: **any workshop room whose identity is a TOOL-IN-USE plus the WORK it produces**
  (a pottery studio, a sculptor's workshop, a tailor's atelier). The lesson that transfers is
  §1 below: the tool is usually a dataset gap, and the picker's rank-1 will be its *toy* version.

## Plan summary
Planner → **"North-Light Painter's Loft"**: one hero painting zone worked in daylight — an upright
easel holding a canvas, an expansive paint-splattered worktable with brushes/palettes within arm's
reach, a wall of north-facing glazing, canvases leaning against calm white walls, warm-wood shelving
and a rolling cart of paints. Concrete floor, jute rug, architect lamp. Note the planner's brief is
a *different and better* room than the old draft's ring of easels — read the plan, don't inherit.

## The layout: work zone ON the glass, storage backbone opposite
The studio procedural signature (same skeleton as executive_office/office_modern, re-cut for daylight):
- **LEFT (long, GLAZED)** = the north light: `place_window_floor_to_ceiling` + the two EASELS standing
  in it, turned to face the room so the cameras see the canvases. Lining furniture along a wall you
  also glaze is established (greenhouse's bench runs on the glass).
- **CENTRE** = the hub: work table + painter's stool + the paint still life on top + jute rug + the
  ceiling lighting hung off this group (`RoomGroup` has no lighting method).
- **RIGHT (long)** = the storage backbone: the shelf in the wall's **LEFT** slot (it is 1.60 m —
  above the ~1.4 m interior camera, so the CENTRE must stay clear: office_modern's preventive
  application of the bakery blinded-view rule) + the supply cart, with one finished painting hung
  in the free centre slot.
- **BACK (short)** = the leaning wall: a packed `GridGroup` row of four canvases.
- **FRONT (short)** = the door.

Shell auto-sizes to **5.60 × 4.97 m** (27.8 m²) at `modulate_scale=1.0` — a real loft.

## §1 THE HERO IS A GAP, AND THE PICKER'S RANK-1 IS ITS TOY VERSION (the big one)
The dataset has **no floor-standing artist easel holding a canvas**. Query
`"a wooden artist easel with a canvas on it"` and the visual picker confidently returns
`future/fc0b2119` — **a KIDS' easel holding a crayon drawing of a sunny house**. Similarity is fine,
the caption is fine, the geometry is fine. It would have made this room read as a **kindergarten**,
and *no constraint in the loop can see that* (the kindergarten crayon-cup lesson at full strength).
The rest of the pool is whiteboard easels, chalkboard easels and **tripod plant stands**.

→ **Hunt by SILHOUETTE** (tv_studio's rule): `browse` past the captions and pin
`hssd/5e19cedd…`, the one true bare wood A-frame. **Show the rank-1 big before you trust it** —
at contact-sheet size the crayon drawing reads as "a colourful canvas"; at `show(n, big=True)` it is
unmistakably a child's.

**SCALE TRAP on the same asset:** it is natively **0.50 W × 1.00 H** — its caption ("table easel")
was *literal*. Unscaled it reads as a toy beside a 0.76 m table. Height-fit uniformly to 1.65 m
(`obj.scale(w * 1.65 / h)`). Same audit raised the table 0.63 → 0.76 m. **Measure every hero with
`get_whd()` offline before the first build** — greenhouse palm / hospital bed / garage car, again.

## §2 `place_on_top` SHATTERS ON A SKELETAL ANCHOR — and there is no vertical lift to fall back on
The obvious way to get a canvas onto the easel is `easel_unit.place_on_top(canvas)` with the easel as
anchor. **It fails, and it fails silently.** An A-frame easel has no substantial horizontal region —
only the slivers of its crossbars — so the surface-region tiler tiles a sliver, clamps the canvas to
that microscopic cell (`TILE_FOOTPRINT_FRAC`), and both easels render a **postage-stamp canvas parked
on the lower crossbar**. This is the flat-rug failure class (a rug anchor → 0.029 m tiles → 3 cm bean
bags), generalised: **`place_on_top` needs a real top; a skeleton, a tripod or an A-frame has none.**
The VLM loop said `no rotation / no wall overlap`, no lints — geometry is legal, only the semantics
are absurd. **Caught by EYE in the cheap phase-2 render.**

There is no rescue via a lift: **`bottom=` exists only on the wall-adjacent path**
(`place_on_<wall>_wall_<pos>`), never on an anchor-group placement. So the fix is **geometric, not a
stacking op** — stand the canvas on the FLOOR hard against the easel and let the A-frame rise behind
it. Head-on that is exactly what a canvas up on an easel looks like, and it is deterministic (no
tournament to lose). It makes the canvas phase-1 floor geometry.

### §2b ANCHOR THE UNIT ON THE PIECE WHOSE FACING MATTERS
First attempt: anchor the easel, `place_on_front_adjacent(canvas)`. The canvas showed the room its
**blank back** — because the `*_front*` verbs bake a **face-the-anchor** rotation (the seating
semantic: a chair in front of a desk turns to face it). Flipping it per-asset is a trap, because mesh
fronts are unnormalised and the two canvases disagreed.

→ **Anchor the CANVAS and hang the easel off its back** (`place_on_back_adjacent(easel)`). The one
piece whose orientation matters is then the anchor, so it inherits the room's own `facing=` — the
same mechanism that already aims the leaning row correctly. The easel is a near-symmetric A-frame, so
its facing is a non-issue, and its ledge ends up against the canvas, where it belongs. Rule:
**when composing a unit, anchor it on the piece whose ORIENTATION carries the read, not on the piece
that is structurally "underneath".**

## §3 CANVASES LEANING ON A WALL: there is no mesh, so use the geometry you have
A canvas *is* a flat upright slab (d = 0.02 m). Stand several as **FLOOR objects** in a packed
deterministic `GridGroup` row and place the row flush to the wall — it reads exactly as canvases
lined up against it. Mixed heights (1.15 / 0.85 / 1.05 / 0.95 m) + `randomness=0.3` on the gaps makes
it a working stack, not a CAD array.

```python
lean = [fit_height(scene.AddAsset(q, asset_id=cid), h) for q, cid, h in (...)]
with scene.GridGroup(sparsity=0.04, randomness=0.3) as canvas_stack:
    canvas_stack.place_row(lean)
room.place_on_back_wall_center(canvas_stack)     # a composed group, flush to the wall
```
Four canvases for **one** placement, and at ~1.15 m they stay under the ~1.4 m camera, so the back
view is never blinded. **Verify each canvas carries REAL artwork** — the office_modern empty-frame
trap (a blank frame and a reversed front look identical from behind).

## §4 "FILL THE FLOOR INSTEAD OF SHRINKING" ONLY WORKS WHEN THE FILL IS FREE
The shrink vote ran `0.75 / 0.7 / 0.81 / 0.5 / 0.7 / 0.65 / 0.75` — never flipping, so **signal**
(living_room_cozy's vote-train rule) — and the standard answer is children_room/kindergarten's *fill
the floor before shrinking*. **It backfired here, and the mechanism is worth knowing.** Adding a
second canvas stack grew the shell **5.60 → 6.86 m wide** — in a front-WALL slot *and* in a corner
floor slot alike (both measured off the exported floor mesh). Parking the cart in the `right` FLOOR
slot instead blew the width to 6.70 m and collapsed the depth to 4.39 m, **jamming the back camera
against the table**.

> **The greenhouse plant-bed is free because it is ONE object holding a dozen plants — it occupies a
> single slot and adds no width. A composed ROW is not free: it lands in a row/column the shell must
> then grow to fit.** So *fill-don't-shrink* is not universal advice — it holds only for fills that
> cost no slot. When your fill would claim a row, shrink instead.

Resolution: dropped the fill, kept the known-good 5.60 × 4.97 shell, and applied **one decisive
`modulate_scale=0.85`** — deliberately **short of** the vote, because a painter must **step back** to
judge a canvas and that open floor IS the category (garage's vehicle lane, corridor's centre lane,
operating_room's sterile ring). Vote decayed to `0.8` ≈ converging → declined. **A wall placement
costs no floor slot; use the walls when you must add without growing.**

## Asset gaps (MED risk — resolved by substitution; two ingest candidates)
| Want | Dataset reality | What to do |
|---|---|---|
| floor easel **with a canvas** | none — rank-1 is a **kids' crayon easel**; rest are whiteboard/chalkboard easels + tripod plant stands | pin the bare A-frame `hssd/5e19cedd…`, height-fit to 1.65 m, stand a real canvas against it. **#1 INGEST CANDIDATE** |
| paint-stocked shelving | none | a warm-wood bookcase with shelves modelled **FULL** (`hssd/2db50fb1…`) — art books are plausible in a loft, and a filled fixture reads as *used*. **#2 ingest candidate** |
| brushes / palette / paint tubes | **REAL and excellent** — `future/4a9dc3a5…`, a genuine painter's still life (brushes in a glass jar + palette + tubes on a cloth) | **this is the PRODUCT** — it is what makes the table read *painted-at* rather than staged (jewelry_shop's rule) |
| rolling supply cart | **REAL** — `future/10d2a1e8…`, shelves already **LOADED** | use it; a stocked fixture beats an empty one |
| canvases with real artwork | **RICH** | pin several; check each carries actual art, not a blank |
| paint-splattered floor texture | none | plain `"smooth cool grey concrete floor"` — don't chase a texture the library lacks (corridor) |

## VLM feedback we hit and how we resolved it
- **Room size — one decisive application, then decline the decay.** Seven unidirectional shrink votes
  (0.5–0.81) whose *magnitude* bounced. Held through phases 1–2 (render-wins-early), applied ONE
  `modulate_scale=0.85` **short of** the vote (functional open floor), vote decayed to `0.8` →
  declined. Obeying the 0.5 would have given a **2.8 × 2.5 m closet**.
- **`rotate round stool by 180 to face the table` (×2, one build)** → **declined as noise**: the stool
  is a *round backless* stool — it has no front — and it was already `face()`d at the table. A
  rotation vote on a rotationally-symmetric object is self-identifying noise (living_room_cozy's
  phantom-object class). It did not recur.
- **`no rotation` / `no wall overlap` / zero lints on every other build** — clean by construction:
  `facing` omitted on all wall placements (the heuristic faces them into the room), the tall shelf
  kept out of the wall CENTRE, door and hung art in disjoint slots, and the canvas row deterministic.

## The two failures the loop never saw (both caught by EYE)
1. The **postage-stamp canvases** on the easel crossbars (§2) — `no rotation`, no lints, converged.
2. The **kids' crayon easel** (§1) — would have shipped a kindergarten. Caught at the AUDIT gate, at
   the cost of one `show(n, big=True)`.

Both are the jewelry_shop meta-lesson: **loop-clean is necessary, never sufficient — the category
gut-check is yours.**

## Manual constraints used
- `room.add_clearance(shelf, distance=0.6, dir="front")` — standing/reach space at the shelves.
  Door clearance and wall-object clearance are automatic.
