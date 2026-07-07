# Asset selection (agentic retrieval)

`AddAsset(query)` shortlists candidates by embedding similarity, then a **VLM picks by
looking at each candidate's preview render** (not just its text description). This is what
stops "a small desk lamp" returning a workstation. See [dsl_reference.md](../dsl_reference.md)
for the API.

## Scene kickoff: assets BEFORE placements (do this first, every new scene)

Most of a believable scene is having the right *meshes* available. Settle the asset library for
the category **before** you write a single placement — placement work on a thin asset set just
produces a tidy arrangement of wrong objects. The repeatable process (proven on the hair salon):

1. **Map out every asset the scene could reasonably want.** Brainstorm 50–100 candidate items
   for the category (a salon: styling chairs, backwash units, mirrors, trolleys, reception desk,
   retail shelf, dryers, towels, products, waiting seating, …). Breadth first; prune later.
2. **Catalogue what we already have.** Query each against the dataset and **`browse`** the
   results — see what genuinely exists vs. what's missing or weak. Build a **specialized category
   retriever pool** from the good hits (over-generate → curate by eye; see "Building / curating a
   category pool" below). A scene category almost always earns its own pool.
3. **Identify the 5–10 *high-impact missing* assets — and have the user source them.** Don't try
   to force the dataset to cover everything. Pick the **small number of key meshes that unblock
   the scene** (the ones with no acceptable substitute — e.g. a real backwash unit, a barber
   styling chair, a neon sign). Ask the user to download high-quality free `.glb`s online, fix
   orientation/scale, and hand them over to **ingest** (`python -m IDSDL.ingest <zip>`; see below).
   Five well-chosen ingested assets beat fifty mediocre dataset picks.
4. **Only now design the placements.** With the library solid, lay out the scene. If an
   *arrangement relationship* isn't expressible in the DSL, consider a new placement group
   (`skills/add-placement-group/SKILL.md` → "Step 0: do you actually need one?"); otherwise use
   existing groups creatively.

Worked end-to-end in [../examples/hair_salon.md](../examples/hair_salon.md).

## Batch retrieval stress test (do this right after the asset map)
Before writing any placement, **route the whole candidate list at once and audit it** — a cheap way
to answer "are most of the assets actually available?" up front (a library asked exactly this). Loop
the warm router over ~40 queries and print `sim | query | chosen-desc`; the descriptions alone tell
you what genuinely exists vs. what routes to the wrong thing. Warm the singletons ONCE per process so
all 40 share the 687 MB embedding load:
```python
from IDSDL.service import core as svc
svc.warm()
for q in QUERIES:                       # your 40 candidate object descriptions
    d = svc.retrieve(q)                 # routes + visual-picks, no seeded-cache pollution
    c = next((c for c in d["candidates"] if c["chosen"]), (d["candidates"] or [{}])[0])
    print(f"{c.get('similarity',0):.3f}  {q:<48}  {c.get('desc','')[:60]}")
```
It runs serially behind the router lock (~15 s/query → ~10 min for 40) — kick it off in the
background. Then, for the handful that came back wrong or low-sim, do a **second pass**: reword the
query (describe the object + material, not the room) and copy the chosen model's preview
(`svc.candidate_preview(model)`) to eyeball it. Read the previews as images before pinning. Worked
end-to-end in [../examples/library.md](../examples/library.md) (32/40 on-target; the 5 gaps were all
rewordings or skippable props, no ingest). This is the fast, thorough alternative to inspecting one
query at a time. (`scene.prefetch_assets(QUERIES)` then `AddAsset` per query, reading
`obj.retrieval_candidates`, is an equivalent one-scene variant — restaurant, 47/47.)

Three failure modes the audit catches that a similarity number ALONE won't (read the `desc`/preview):
- **Off-theme at a decent score** — a restaurant "dessert case" came back a branded ice-cream freezer
  at 0.57. Skip or reword; don't ship it.
- **A weak KEY asset is usually POOL-ROUTING, not recall** — reword to name the class the right
  retriever owns: restaurant back-bar "…shelving unit…" (generic shelving, 0.49) → "a tall back bar
  CABINET with shelves of liquor bottles" → `CabinetandShelfRetriever`, a real hutch (0.62).
- **The SET trap** — a generic "a small round dining table" / "a cafe table" often returns a table with
  chairs BAKED into the mesh; if a group supplies its own seating that double-seats it. Pin a BARE piece
  or add "no chairs". (Inverse of the [[set-assets-and-scaling]] idea — here the set is what to avoid.)

## Inspect & override (the feedback loop)
- **See a pick:** `python workbench.py inspect "<query>"` → prints the contact-sheet path
  (open it), the `VLM decision` (`chose #N: <reason>`), and the ranked candidates with
  preview paths. Add `--render` to render the top finalists in-engine.
- **Browse the dataset by hand:** `python workbench.py browse "<query>" [--n 24] [--text]`
  → a labeled montage PNG of many matching assets (semantic by default; `--text` for an
  offline substring match) plus a manifest of `idx → model id → desc`. Grab ids to pin
  (`AddAsset(..., asset_id=...)`).
- **Every object carries provenance:** `obj.retrieval_query`, `obj.retrieval_candidates`
  (`{model, path, scale, preview, desc, similarity, chosen}`), `obj.retrieval_model`. A run
  through `workbench.py run` lists them per asset.
- **Override:** `AddAsset(query, asset_id="hssd/<id>")` pins a specific asset (durable,
  recompile-safe) — the preferred fix. Or `scene.reselect_asset(obj, i_or_model)` for a
  post-hoc swap (then recompile).

## Baked-in selection preferences (hard rules in the picker)
The visual picker (`IDSDL/datasets/retrievers.py`, `visual_llm`) enforces these so you
rarely have to override:

- **Simplicity / placeability over a closer-looking type match.** Prefer minimalistic
  pieces with ONE clean primary surface — they are easy to place objects on and to fit.
- **Desks & tables — single flat top.** A raised **hutch, back shelf, upper cabinet, shelf
  tower, cubbies, or any second stacked surface is DISQUALIFYING** for a generic query
  ("desk", "teacher's desk", "office/writing/computer desk", "study table"). Pick a simple
  flat-top desk (a top on legs, optionally with drawers). Multi-surface desks wreck on-top
  placement (writing surface vs hutch ledge — the classroom lesson) and look cluttered.
- **Exception:** honor a complex form ONLY when the query literally names one — *hutch*,
  *secretary*, *reception*, *dresser*, *vanity*, *desk with storage on top*.

### Reference examples (`IDSDL/datasets/futurehssd/HSSD-images/<id>.png`)
- **AVOID** `11c27a0b2950b3a3e9431128cd452ac7cbdf35c1` — hutch + side cubbies (multi-surface).
- **GOOD** `b5281b81131311b05c3707d977da166addba8661` — bare flat top on legs;
  `c6ee2a801e720442092ed6497935cc067158e761` — flat top with simple drawers.

## Performance
- **Embeddings load once.** `futurehssd.npz` (~700 MB) and the metadata json are loaded a
  single time and shared across all retrievers (was loaded per-retriever → ~12 s / ~13.6 GB
  at import; now ~2 s / ~0.7 GB). Automatic.
- **Parallel prefetch.** Retrieval is network-bound (embedding + routing + visual VLM per
  query, ~15-20 s each uncached), so resolving a scene's assets one-by-one is slow on a
  cold cache. Call once up front to resolve them concurrently and warm the cache:
  ```python
  scene.prefetch_assets([ ...all asset descriptions... ])   # ~5x faster than serial
  # then your normal AddAsset(...) calls hit the warm cache
  ```
  Needs a seeded scene. A missed/extra entry is harmless (that AddAsset just resolves
  normally). Only helps the first (uncached) build — repeat builds hit the cache anyway.

## Retriever pools (routing) — mind category gaps
A query is first routed to a category retriever, each of which searches a **curated id
pool**, not the whole dataset. So an asset absent from the routed pool can never be picked,
even if it exists. Worked example: chalkboards used to route to `WallArtRetriever` (decor:
paintings/posters/stickers) and the real board was only in the general pool → never chosen.
Fixed by adding **`PresentationFixtureRetriever`** (pool `assets/presentation_fixtures.json`):
functional classroom/meeting/lab fixtures — boards (chalk/white/black/bulletin/cork),
easels, projectors, projection screens, podiums/lecterns, wall maps/globes, wall TVs/displays.
If a *type* of object keeps coming back wrong, suspect a **pool gap**: `browse` (base pool)
vs the actual routed pick will reveal it; the fix is a new/expanded category pool, not a
better prompt. (Dataset is thin on some: ~2 podiums, ~2 lab benches.)

**`DesktopWorkstationRetriever`** (pool `assets/desktop_workstation.json`) is the on-top layer for
a desk/computer workstation: computer monitors and **all-in-one desktop sets** (an iMac-style mesh
bundles the keyboard+mouse — the dataset has essentially no standalone keyboard/mouse, so query
"a desktop computer" to get all three), laptops, desk/task lamps, pen cups and organizers, small
desk plants, books, frames, desk phones. Built with the `candidates desktop → clean → pool` flow
(`CANDIDATE_PROMPTS["desktop"]` over-generates; a conservative description filter drops desk/chair
combos and speakers/mics that "desk lamp"/"monitor stand" queries drag in). Pair it with
`WorkstationGroup` (see `../add-placement-group/SKILL.md` and `../examples/dental_office.md`). Note
it overlaps `TableTopDecorRetriever` (generic table decor) — the router prefers this one for
desk/computer queries because its description names the workstation items explicitly.

## "Set assets" — bundled categories (vanities, toilets)
Some categories are **complete sets** in the mesh and must be retrieved + placed as ONE unit, never
as separable parts: a vanity = cabinet+sink+counter; a toilet = bowl+cistern+flush-buttons+TP-holder.
Don't query for a bare seat / sink / toiletries — they only exist inside the set. Each earns a
**curated pool + specialized retriever** (`BathroomVanityUnitRetriever` / `BathroomToiletSetRetriever`):
gallery the whole category, curate the good complete sets, save as a pool json, add a retriever class
(mirror an existing one), register it in `FUTURE_HSSD_ASSET_RETRIEVERS`, and **remove that category
from the generic retriever's description/examples** so the LLM router sends it to the specialist.

Two scaling rules for these (and bathroom fixtures generally — their `scale` metadata is unreliable):
- **Resize by UNIFORM width-only** (set target width, scale all axes by the same factor) so the mesh's
  own proportions are preserved — never scale axes independently (it distorts sinks/drawers). Note
  `obj.scale(w)` mis-fires on pre-scaled assets; use a captured-whd uniform factor (`_fit_width`).
- Some sets bundle peripherals that inflate the bbox (toilet TP-holder/cistern) so the visible piece
  reads small → scale up ~1.5×. If a category is **uniform in size** (toilets), one consistent scale
  covers all → no per-asset tagging; if sizes/placement vary (vanities), hand-TAG them
  (`tools/build_vanity_tagger.py` → `vanity_types.json`, applied transparently by `AddAsset` via
  `SceneProgRoom._apply_vanity_metadata`). Floating/wall-hung sets
  mount via the `bottom=` kwarg now on every `place_on_*_wall_*` method.

## Ingesting new assets (grow the library)
Drop in `.glb` files from anywhere and make them first-class retrieval assets:
```bash
python -m IDSDL.ingest <zip-of-glbs> [--category <pool>] [--manifest manifest.json]
```
**Contract: supply the glbs correctly scaled and oriented** — Y up, front facing +Z, width
along X, real-world metres. The tool does **not** re-orient or re-unit meshes (a render-based
VLM can describe but can't reliably fix arbitrary mesh geometry; mis-oriented assets won't
place right even with correct metadata).

> **Ingest centers the mesh (don't fight it, but know why).** Ingest now recenters each glb's
> bounding box to the origin on copy (`_copy_centered` in `IDSDL/ingest.py`). This matters: the
> runtime floor-aligns by aabb *bottom*, but some room-level passes assume the mesh **origin sits
> at its bbox center** — a mesh authored with an off-center origin lands **sunk into or floating
> above the floor** (the salon barber chair was −0.186 m / +0.186 m by placement path; exactly its
> mesh's off-center y × scale). Centering on ingest removes the ambiguity. If you hit a
> sink/float clip on an *already-ingested* asset, recenter its glb in place:
> `m=trimesh.load(p,force='mesh',process=False); m.apply_translation(-(m.bounds[0]+m.bounds[1])/2); m.export(p)`. Per glb it generates a stable `custom/<sha1>` id, a
Blender preview render, metadata (a VLM captions the preview → `description`/`placement`/
`freetop`/`on_top_or_inside` and the `scale` = real-world width), and an embedding; it
registers them in `IDSDL/datasets/custom/{models,images}/` + `custom.json` + `custom.npz`. The
retriever auto-concatenates these (the `custom` kind in `retrievers.py`), so ingested assets
are routed/ranked/previewed/picked/`AddAsset`-loaded exactly like dataset assets. Parallel
(`--workers`), idempotent (sha1 dedup). A `manifest.json` (`{"<file.glb>": {"description":...,
"scale":..., "placement":...}}`) overrides any field; `--category` appends the ids to a pool.

## Building / curating a category pool (the reliable way)
Pools are best built by **over-generating then hand-curating**, not by trusting one search:

1. **Over-generate candidates** — `python workbench.py candidates <category> [--topk 10]`
   runs many prompts (in `CANDIDATE_PROMPTS` in `workbench.py`) against the FULL dataset,
   top-`topk` each, and writes the deduped union as a json id-list (e.g. 100 prompts × 10 →
   ~220 unique for `presentation`).
2. **Curate by eye** — `python workbench.py gallery <that.json>` writes a self-contained
   **selection HTML** (base64 previews, no server). Download it, open locally, click the
   assets to KEEP (filter box + keep-all/clear help), then Download `selection.json` (a JSON
   array of kept ids).
3. **Finalize** — that array becomes the pool json (`assets/<category>.json`) the retriever
   loads. `gallery <pool>` / `gallery all` re-open any pool or the whole dataset for review.

This is how the category pools should be grown — curation over automatic search.

## When it still picks wrong
1. `workbench.py inspect "<query>"` to see the shortlist + reasoning.
2. If a good asset is in the list but unpicked → pin it: `AddAsset(..., asset_id=...)`.
3. If the **shortlist itself** lacks a good option → rephrase the query (more specific /
   simpler), or pin a known-good id. Embedding recall, not the visual pick, is the limit there.

> Extending the rules: the preferences live in the `visual_llm` system prompt in
> `retrievers.py`. Add new lessons there (and here) the same way — a short, explicit hard
> rule plus the rationale.
