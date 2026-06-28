# Asset selection (agentic retrieval)

`AddAsset(query)` shortlists candidates by embedding similarity, then a **VLM picks by
looking at each candidate's preview render** (not just its text description). This is what
stops "a small desk lamp" returning a workstation. See [dsl_reference.md](../dsl_reference.md)
for the API.

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

## Ingesting new assets (grow the library)
Drop in `.glb` files from anywhere and make them first-class retrieval assets:
```bash
python -m IDSDL.ingest <zip-of-glbs> [--category <pool>] [--manifest manifest.json]
```
**Contract: supply the glbs correctly scaled and oriented** — Y up, front facing +Z, width
along X, real-world metres. The tool does **not** re-orient or re-unit meshes (a render-based
VLM can describe but can't reliably fix arbitrary mesh geometry; mis-oriented assets won't
place right even with correct metadata). Per glb it generates a stable `custom/<sha1>` id, a
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
