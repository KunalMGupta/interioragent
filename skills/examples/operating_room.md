# Operating room / surgical suite — worked example

Status: **built & VLM-clean, v2 on an INGESTED surgical kit** ("Sterile Core with Service
Walls", `scenes/work/operating_room_v1.py`, seed=34). Built through the guided flow
(flow_0712_220706_c003), entirely via the MCP tools (post-`reload_credentials`).

**Read the "Ingesting the surgical kit" section below before ingesting ANY user-supplied
zip — it is the most transferable part of this scene.** v1 shipped with the whole clinical
layer faked (a med cart as the anesthesia machine, folded bath towels as sterile trays); the
USER correctly diagnosed the room as asset-starved and supplied `hospital.zip`. v2 replaced
the fakes with real meshes and the room went from "clinical-ish" to unmistakably an OR.

| Layer | v1 (substitute) | v2 (ingested) |
|---|---|---|
| Anesthesia machine | white 3-drawer med cart | **real anesthesia machine** w/ breathing bag |
| Mayo stands | white med carts | **blue-draped instrument tables** |
| Sterile "product" | folded bath towels | **real trays of surgical instruments** |
| Sterile processing | — | **gas sterilizer/autoclave + ultrasound cart** |

## Prompt(s) this covers
- "an operating room / surgical suite / OR", "a hospital theatre", "a sterile procedure room".

## Plan summary (from the planner)
A sterile operating core: central table under twin surgical domes, anesthesia + vitals at the
head, mayo stands with instrument trays, stainless perimeter casework + scrub sink, seamless
resin floor, tiled walls, generous circulation around the table for transfers.

## The layout idea: game_room's hero-in-the-middle, dental_office's clinical discipline
A near-square room whose footprint is set by the **sterile ring**, not by the walls:
- **CENTRE = the STERILE CORE** (`RelativeGroup`, anchor = the operating table): anesthesia
  cart at the HEAD (`place_on_back`), vitals monitor beside it (`place_on_back_right`), two
  draped mayo carts flanking (`place_on_left` / `place_on_right`). One big round dome
  overhead (`add_lighting(density=0)`).
- **`room.add_clearance(or_table, distance=1.2, dir="all")` is what SIZES the room** — a scrub
  team must walk a full loop around the table. Same rule as game_room's cue-stroke clearance.
- **BACK = equipment/head wall**: two tall glass-door supply cabinets (LEFT/RIGHT slots), the
  flat gas-outlet **headwall strip hung between them** — the strongest clinical cue in the room.
- **LEFT = scrub/prep**: the long stainless counter with an integrated sink, linen stacked on it.
- **RIGHT = sterile supply**: stainless instrument trolley + a wall-mounted clinical display.
- **FRONT = the door.** **No windows** — a real OR has none, and an opening renders as a black
  void anyway (executive_office/retail lesson). The one time the renderer limit and reality agree.
- Lighting: the table dome + one flush LED panel pass at `density=0.01`.

## Ingesting the surgical kit (`hospital.zip`) — a raw zip is NOT ingest-ready

A user-supplied zip of Sketchfab-style glbs violated the ingest contract in three separate
ways. **All three are silent** — ingest happily accepts the files and the breakage only shows
up as a wrecked render or a lint, so check them up front:

1. **MULTI-MESH → renders DISASSEMBLED.** 15 of the 18 glbs had many meshes (the sterilizer:
   **143**; the anesthesia machine: 36). Both loaders take `imported_objs[0]` — the *first*
   mesh only — and leave the rest stranded at the origin (`asset_ingest.md`). **Fix: join in
   Blender** (`bpy.ops.object.join()` — it preserves material slots). Do NOT round-trip through
   trimesh: `force="mesh"` drops materials (renders flat WHITE) and a Scene round-trip explodes
   one mesh into many (renders disassembled). The merge belongs at ingest, never in the loader.
2. **WILD UNITS.** The zip shipped an ENT unit **420 m** wide and a dental chair at 40 m. The
   contract wants real metres, and ingest does not re-unit anything. Fix: uniform-scale each to
   a known real-world HEIGHT in the same Blender pass.
3. **OFF-CENTER ORIGINS → floats/sinks.** The first ingest produced
   `[Lint] '<x>' FLOATS 0.81 m` / `is SUNK 0.43 m` on *every* ingested asset. Cause: my merge
   baked each object's world offset into its vertices. **Fix at the SOURCE** —
   `origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')` then zero the location — not with a
   translate hack in the scene, and not with the trimesh recenter snippet (it strips materials).
   Recentering rewrites the file, so the **sha1 ids change** — re-pin after re-ingesting.

Then, after ingest, two more traps:

- **The auto-CAPTION is unreliable — pin by id and trust the PREVIEW.** The ingest VLM called
  the draped mayo stand a *"blue powder-coated drill press"*, the instrument tray a *"trough
  planter"*, and an operating table a *"blue glass decorative sphere"*. Captions this wrong also
  mean the asset is **unreachable by NL retrieval** — pinning is mandatory, not a preference.
- **The auto-SCALE is unreliable** (it is a VLM *guess* at real-world width, and it resizes the
  asset): the anesthesia machine loaded **0.86 m** tall (real: ~1.5 m), the sterilizer 1.55 m
  (real: ~1.7 m). Same class as the dataset's bad `scale` metadata (corridor's 2× cabinets,
  children_room's 6× bean bag). **Measure every ingested pin with `get_whd()` offline, then
  height-fit it.**

**FILENAMES LIE — the preview is the evidence.** All three `surgical_table*.glb` turned out to
be draped *instrument* tables, not patient tables (so the dataset's `future/51434359` stayed the
hero); `c_arm_neurosurgery_operating_table.glb` rendered as a black chair; and two glbs rendered
as unidentifiable blurry blobs. **Of 20 ingested assets, 6 were usable for this scene** — that is
a normal yield. Eyeball the whole contact sheet before writing a single placement.

## Pinned assets (audited previews)
| Role | id | note |
|---|---|---|
| Operating table (hero) | `future/51434359-427d-4f35-b2f2-f2ad9b875b2e` | dark padded top on a stainless pedestal — a **real OR-table silhouette**; ships SHORT (native H=0.53 m) → `modulate_scale=1.5` (UNIFORM) → top at ~0.80 m. **Stayed the hero even after the ingest** — the zip's "surgical tables" were instrument tables |
| Anesthesia machine (ingested) | `custom/e6e171912392d15999e34590299eaab0f78c9de9` | the real thing, breathing bag + screen; loads 0.86 m → `_fit_height(1.50)` |
| Mayo stand ×2 (ingested) | `custom/7db820c55be6991b9b5541b094c4e5fef152f0aa` | blue-draped instrument table; `_fit_height(0.92)` — at 1.05 it OUT-MASSED the patient table |
| Draped back table (ingested) | `custom/c7966f1817cabdecbb6961d40d0ae3586d666bb6` | the larger draped table, on the front wall |
| Surgical instrument tray (ingested) | `custom/c9cbd96abf664f10c79d47f05f0da85c9e438329` | the sterile PRODUCT — `place_on_top` of each mayo stand |
| Gas sterilizer / autoclave (ingested) | `custom/aec28f56f031931bc434b6f1689224d7000cb5ee` | loads 1.55 m → `_fit_height(1.70)` |
| Ultrasound cart (ingested) | `custom/d295f3ed29959a4b8336630adbb8362dff267487` | loads 1.70 m → `_fit_height(1.40)` |
| Gas-outlet headwall | `custom/920037c5376d7f897f7b4b142bea7792e938400d` | prior ingest; FLAT → safe to `place_on_wall_*` |
| Vitals monitor | `custom/475c4c6d50144e1659d7bbc18121378a897d505e` | prior ingest; on a rolling stand |
| Anesthesia cart / mayo carts | `hssd/cc15f4f67e55963a009abe0f4fe10148cb632f2f` | white 3-drawer trolley ×3 (1 at the head + 2 flanking) |
| Supply cabinet ×2 | `hssd/3a2fd60fc421b402f4bfd365fd2a7accfa6ce4b1` | tall grey glass-door metal cabinet; **ships 3.00 m tall** → height-fitted to 2.0 m |
| Scrub/prep counter | `hssd/79bf13063599b7fff88cc250d8fe76a2e46e9683` | commercial stainless counter + integrated sink; H=0.58 → fitted to 0.92 m |
| Instrument trolley | `hssd/381a6e138a9fd613507af6c51fcc9db47271bc25` | stainless multi-compartment wagon |
| Sterile drapes | `hssd/248568c07dbfce7d21987a3af20f72d38d4398b3` | stack of folded white cloth — the OR's "product" |

## What worked / gotchas

- **The dataset has NO surgical dome light and NO anesthesia machine** — confirmed by browse,
  not assumed: "surgical dome light" returns *residential ceiling lamps* (frosted glass, crystal,
  ornate), and "anesthesia machine" returns the vitals monitor + med carts. These are the
  medical-fixture gap the catalog warns about, and they are **the OR's two identity props**.
  Substitutes shipped (user's call, gaps logged as ingest candidates):
  - **dome** → one large FLUSH round luminaire over the table. **Never a pendant**:
    `add_lighting` caps a fixture's height at 1.5 m but pins its origin at the CEILING, so a
    stemmed lamp hangs into the room and its emissive mesh blows the exposure
    (executive_office). A flush disc at `modulate_scale=2.6` reads as a dome.
  - **anesthesia machine** → the white 3-drawer med cart at the head + the vitals monitor
    beside it. The head-of-table *zone* carries the read even when the machine mesh doesn't exist.
- **But an OR table DOES exist** — `future/51434359`, captioned only "medical examination
  table". Reconfirms hospital_room's lesson: **browse before assuming an ingest round is
  needed**; the medical gap is narrower than the catalog's warning suggests. Its caption
  undersells it — eyeball the mesh, don't trust the words.
- **TWO uncurated meshes, two opposite scale bugs, both caught OFFLINE with `get_whd()` before
  the first build**: the hero ships at ~55% (H=0.53 → `modulate_scale=1.5`, UNIFORM) and the
  supply cabinet ships as a **3.00 m giant** (→ `_fit_height(cab, 2.0)`). Measuring the whole
  pin list in one offline pass is the cheapest phase-0 step there is; do it every scene.
- **A too-tall cabinet is also a CAMERA bug, not just a look bug.** Interior wall cameras sit at
  ~1.4–1.5 m at each wall's *centre*, so the 3 m cabinets went to the LEFT/RIGHT slots and the
  ≤1.25 m items (trolley, counter) took the centres — bakery's garbage-view → hallucinated-
  rotation-storm lesson, applied preventively. Result: `no rotation` on every single build.
- **`place_on_top` targets the group ANCHOR — so the mayo stand needs its own group.** Dropping
  `place_on_top(drapes)` into the sterile_core (anchor = the operating table) would have draped
  the linen over the *patient surface*. Built the cart as its own `RelativeGroup`, then
  duplicated with `2 * mayo_unit` so the tournament runs ONCE and both stacks come out identical
  (living_room_cozy v3 + design_principles). Same trick for the scrub counter.
- **The sterile "product" is the drapes.** No surgical-instrument-tray mesh exists (the query
  returns *kitchen cutlery* — a casino-poker-chip trap that would have made the carts read as a
  catering station). Folded white linen is the honest OR analogue and it masses at working
  height on the carts and counter, which is what makes the room read *stocked* rather than
  staged-empty (jewelry_shop's product rule, adapted to a sterile room).
- **The vibe layer is INVERTED for a clinical room.** The usual finishing moves — greenery, a
  warm accent seat, a rug, a warm envelope — would actively *break* an OR. It earns its read by
  being bare: hard resin floor, tile, stainless, no plants. (The planner's brief *did* ask for
  biophilic warmth and daylight; that is where the plan is wrong about its own category, and
  dental_office already taught "clinical rooms want a hard floor — drop the rug".)
- **No windows, deliberately** — the one scene where the black-void renderer limit costs nothing,
  because real ORs are windowless.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.8` (Ph1) → `0.69` (Ph2) → `0.8` (full) → held per render-wins-early →
  applied ONE decisive `modulate_scale=0.85` in the final phase (deliberately a touch ABOVE the
  vote: the 1.2 m sterile ring is *functional* space, and a legitimate circulation lane always
  reads as "empty" to the occupancy metric — garage's vehicle lane, corridor's centre lane) →
  vote decayed `0.9` → `0.97` ≈ neutral = **converged**. Declined the residual.
- `no rotation` / `no wall overlap` / no lints on **every** build, phase 1 → final. Clean by
  construction: `facing` omitted on all wall placements (the heuristic faces the room), tall
  fixtures kept out of wall centres, door and wall items in disjoint slots.
- **The dome being too small was an EYE catch, not a VLM signal** (like corridor's oversized
  cabinets). At `modulate_scale=1.6` the disc read as a downlight; the loop was fully clean and
  said nothing. Bumped to 2.6 → reads as a surgical dome. *No constraint fires on "that fixture
  is too small to be the thing it's supposed to be."*

## Manual constraints used
- `room.add_clearance(or_table, distance=1.2, dir="all")` — the sterile ring; it sizes the room.
  Auto overlap/bounds + door clearance + cabinet category clearances covered everything else.

## Possible refinements (not blocking)
- **Ingest a real surgical dome light and an anesthesia machine** — the two highest-value meshes
  for this category. The dome would also unlock the prompt's *twin* domes: `add_lighting`
  yields exactly one fixture at `density=0`, and `best_grid` squares any higher count, so a
  clean pair of domes is not reachable from the DSL — it needs two placed fixtures.
- A surgeon's stool and a kick bucket would add life without breaking sterility.
