# Laboratory (research / teaching wet lab) — worked example

Status: **built & VLM-clean** (`scenes/work/laboratory_v1.py`, seed=27, `laboratory_v1.blend`).
Built coarse-to-fine from the shell. Final build: `no rotation` / `no wall overlap`, zero lints;
the residual `rescale room by 0.9` was declined (see below).

## Prompt(s) this covers
- "a laboratory / research lab / science lab / wet lab / teaching lab / school science room".

## The layout idea: computer_room's GRID wearing operating_room's CLINICAL DISCIPLINE
A near-square room whose floor is a repeated bench unit and whose perimeter does the work:

- **CENTRE = four BENCH UNITS** in a 2x2 `GridGroup`. One unit = bench + stool + (phase 2) a
  microscope and a set of reagent bottles. Built ONCE and duplicated `4 * bench_unit`, so the
  `place_on_top` tournament runs once and all four benches come out identical (design_principles).
- **BACK wall** = sterile/storage: the autoclave (left) + a tall glass-door reagent cabinet
  (right), **stocked** via `place_inside`.
- **LEFT wall** = wet bench: the long stainless sink counter (centre, 0.92 m — low enough to hold
  a wall centre) + a two-cylinder gas bank, under the window.
- **RIGHT wall** = hazmat/cold: the yellow flammables cabinet + the lab refrigerator.
- **FRONT wall** = entry: the door, a rolling trolley, and the whiteboard hung between them.
- **Inverted vibe layer** (operating_room): no rug, no plants, no warm accent. A lab earns its read
  by being hard and bare; the only colour is *functional* — the yellow safety cabinet, the orange
  gas cylinders, the red waste bin.

## The lesson this scene exists for: the GRID is not the category — the PRODUCT is
Classroom, computer_room and laboratory are **the same layout**: a desk/bench unit tiled across the
floor facing a teaching wall. Strip the props and all three render as the same room. What makes this
one a lab is the **microscope + reagent bottles on every bench, at working height** — jewelry_shop's
product rule, and greenhouse v2's density-grain rule ("when two categories share a layout pattern,
the tie-break is the product, not more of the same fixture"). Budget your effort accordingly: the
bench grid took one iteration, the props took the whole scene.

## Asset reality: the dataset has the FURNITURE and almost none of the SCIENCE
A 36-query retrieval stress test (`tmp/lab_stress.py`) — the asset_selection.md kickoff, and the
single highest-value hour of this build. **Twelve of the category's identity props return NOTHING
AT ALL** (empty candidate list, sim `0.000`, not merely a bad pick):

> fume hood · eyewash station · microscope · centrifuge · bunsen burner · hot-plate stirrer ·
> beaker · flask set · test-tube rack · petri dishes · slide box · lab safety sign

Three moves rescued the scene; each is reusable:

1. **The science was already in the dataset — as `custom/` meshes nobody could retrieve.** The
   operating-room `hospital.zip` ingest left a real binocular **microscope**, a real lab
   **autoclave** and a **gas-cylinder cart** in the pool. `"a laboratory microscope"` scores
   **0.000** against a dataset that *contains a microscope* — ingested meshes are only reachable
   through retrievers that merge the `custom` kind, so **pinning by id is mandatory, not a
   preference** (operating_room v2). *Before concluding a category is unbuildable, grep the custom
   pool by hand.*
2. **The glassware was found by SILHOUETTE, not by caption** (tv_studio's rule). No beaker or flask
   exists — but `"a set of three decorative glass DECANTERS with stoppers"` (one amber) is, at room
   scale, exactly a row of reagent bottles. It is the most legible object on the benches.
3. **The fume hood has NO honest substitute, so it was not faked.** The top "stainless steel
   cabinet" hit is literally a **barbecue grill**; the glass-door cabinets are all display hutches.
   Shipping one would be the casino poker-chip trap, so the scene was framed as a **bio/analytical
   lab — the sub-category the library can actually carry** — rather than a chem lab whose hero mesh
   does not exist. **Picking the sub-category your assets can support is a legitimate design move,
   and a better one than a wrong prop.**

### Ingest candidates (in priority order)
**fume hood** (the one true blocker — it alone would make this a chemistry lab), eyewash/safety
shower, centrifuge, benchtop glassware (beakers/flasks/test-tube racks). Five meshes would move this
category from "reads as a lab" to "unmistakable".

## Pinned assets (all measured offline with `get_whd()` before the first build)
| Role | id | note |
|---|---|---|
| Bench (hero unit) | `hssd/81ad56baea5922…` | "extra heavy duty black workbench"; H=0.68 → **height-fit 0.90**. Chosen over three rivals on ASPECT: the top-ranked bench is 1.50 x **0.50** m — coffee-table proportions that a uniform height-fit would blow out to 2.7 m wide |
| Stool | `hssd/3e5b80fa2791…` | black saddle stool on casters; H=0.52 → 0.68 (seat height for a 0.90 m bench) |
| **Microscope** | `custom/d0b407b0d9f1…` | the lab's identity prop. **Mesh had to be REPAIRED — see below** |
| **Reagent bottles** | `hssd/0d16ac77fb67…` | captioned "decorative glass decanters"; IS a row of reagent bottles |
| Autoclave | `custom/aec28f56f031…` | real lab autoclave + two red gas cylinders; H=1.55 → 1.70 |
| Gas cylinders x2 | `custom/ebe6d0a7f2ba…` | a `GridGroup` row, so the pair claims ONE wall slot |
| Instrument tray | `custom/23791b62e98e…` | has CONTENTS. **Not** `custom/c9cbd96a…` (the OR's "instrument tray"), whose preview is an **empty** trough |
| Glass reagent cabinet | `hssd/d898715b817e…` | H=1.36 → 1.90; **`place_inside` it or it reads as furniture** |
| Flammables cabinet | `hssd/9fee5e7b92ed…` | "zinc yellow storage cabinet" — the functional colour accent |
| Sink counter | `hssd/79bf13063599…` | stainless + integrated sink; H=0.58 → 0.92 |
| Fridge / trolley / whiteboard / clock / bin | `hssd/416c68a8…` / `491b7091…` / `1b37271d…` / `e1725f63…` / `9523913c…` | |

## The big gotcha: an ingested mesh whose ORIGIN is 118% of its height off-centre
**The microscope sank 0.23 m through the bench top**, its base poking out underneath, so at room
scale it read as **standing on the floor next to the bench**. The reagent bottles on the *same*
`place_on_top` call seated perfectly (bottom = 0.900 = the bench top exactly).

- **Root cause**: the mesh's geometry sits ENTIRELY ABOVE its origin (y-bounds `+0.444…+1.094`, an
  offset of **+118%** of its own height), violating the invariant `IDSDL/ingest.py::_copy_centered`
  exists to establish. `place_on_top` seats by an origin it assumes is the bbox centre.
- **The whole VLM loop was clean about it** — `no rotation / no wall overlap`, no lints, no
  warnings. A sunk prop is *geometrically* fine; "the microscope is inside the table" is semantics.
  **Caught by eye in the render**, as ever.
- **Diagnosed exactly in one offline probe**, not by guessing: build the single unit and print the
  anchor's AABB **top** against the item's AABB **bottom** (computer_room's method). Then read the
  glb bounds — 5 seconds, and the 118% offset is unmissable.
- **Fixed at the SOURCE** (`tmp/fix_lab_glbs.py`), in Blender, per operating_room's prescription:
  `origin_set(ORIGIN_GEOMETRY, BOUNDS)` + zero the location, which **preserves the material slots**
  a trimesh round-trip would strip (→ flat white). Written back under the **same filename**, so the
  asset id, its embedding and every pin stay valid — no re-ingest, no re-pin.
- **The generalizable lesson — an ingest batch's UNUSED meshes never got the repair pass.**
  operating_room v2 fixed the multi-mesh/units/origins of the 6 glbs it *shipped*; the other 14 are
  still in the pool, still broken. The gas cart (`custom/66cdc7ba…`, origin −26% off, floated
  0.62 m and tripped a phase-1 `[Lint]`) was the second one this scene hit. **When you pin a mesh
  from someone else's ingest, check its glb bounds before you build** — the two failures cost
  exactly one lint and one eye-catch here, and both are 5-second offline checks. (Also: that gas
  cart is the autoclave mesh ingested TWICE — same 2.66 m height, one copy with a broken origin.)

## VLM feedback we hit and how we resolved it
- **`rescale room by 0.5` (phase 1) was NOT a room-size signal.** Per kitchen v1 — *the occupancy
  vote tells you THAT the room is wrong, never WHICH group made it wrong* — I looked for the
  footprint culprit first: the bench `GridGroup` was at `sparsity=0.3`, flinging four benches into
  a bbox the shell had to grow to fit. Tightening to **0.12** (benches in a real lab stand close)
  moved the vote **0.5 → 0.88 in one build**, with no `modulate_scale` touched. Reach for the
  structure before the shell.
- **Room size, final phase**: train `0.5 → 0.88 → 0.9`. Applied ONE decisive
  `modulate_scale=0.92` — deliberately just SHORT of the 0.9 vote, because the centre bench block
  is a rigid `GridGroup` and a shell shrunk below the footprint its placements dictate makes
  fixed-size rows overflow their slots (locker_room/kitchen). The vote **persisted at 0.9** on a
  render showing clear working aisles → **declined the residual** (bookstore's rule: a persisting
  mild vote is noise unless the render agrees it is sparse; and a lab's circulation lane is
  functional space, like garage's vehicle lane).
- **`no rotation` / `no wall overlap` from the first build to the last** — clean by construction:
  `facing` omitted on every wall placement (the default heuristic turns a wall asset into the
  room), tall fixtures kept out of the wall CENTRES (autoclave/cabinets/fridge take corner slots;
  every wall centre is empty or ≤0.95 m, so no interior camera is blinded — bakery's
  rotation-storm rule, applied preventively at design time as office_modern prescribes).
- **The `[RoomGroup] WARNING` on the lab coat was right.** The coat-hook mesh is 0.28 m deep and the
  DSL warned it would "read as furniture FLOATING in mid-air"; the render agreed (a garment hovering
  off the wall). **Dropped it** rather than faking it — wall-hung means genuinely FLAT (<0.25 m), and
  a bare wall centre is *also* the clinical read.

## Manual constraints used
- None. The auto passes covered it: door clearance, `CategoryClearanceConstraint` on the
  cabinets/fridge/appliances, and the grid's own aisles. (The `GridGroup` runs no gradient solve, so
  a hook there would be a no-op anyway — put manual constraints on Relative/Around/Room groups.)
