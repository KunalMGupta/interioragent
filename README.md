# InteriorAgent — IDSDL

**An Interior-Design-aware Scene Description Language for composing structured 3D indoor scenes.**

IDSDL lets you describe interiors at the level of *design intent* — "a sofa with a coffee
table in front of it", "chairs around a dining table", "paintings spread across the back
wall" — instead of hand-placing meshes by coordinate. You write a short Python program; IDSDL
retrieves assets from natural-language descriptions, arranges them with spatial groups,
resolves the layout with geometric and vision-language constraints, and exports a Blender
`.blend` scene.

📖 **Full documentation & visual guide:** <https://interioragent.github.io/docs/>

This repository contains four complementary components:

- **IDSDL** — a structured language that builds explicit **3D scenes** (geometry you can open and render in Blender). *Documented below and on the docs site.*
- **InteriorPlanner** (`planner_core/`) — a retrieval-augmented **design-image** generator that turns a text prompt into a photorealistic interior collage and supports conversational editing. *See [Interior Planner](#interior-planner-planner_core).*
- **TraceRetriever** (`retriever_core/`) — reasoning-based (no embeddings) retrieval over the repo's tacit-knowledge library: worked example recipes, workflow guides and atomic build lessons, selected by **procedural similarity** to the requested room. *See [Text→scene generation](#textscene-generation-mainpy).*
- **SceneGenerator** (`generator_core/` + `main.py`) — the end-to-end **text→3D-scene** pipeline: plan → retrieve traces → asset stress test → author the DSL program (pluggable authors) → build → VLM-critic loop → design-match judging. *See [Text→scene generation](#textscene-generation-mainpy).*

---

## Why IDSDL

- **Natural-language assets** — `scene.AddAsset("a modern 3-seat sofa")` retrieves a matching 3D model.
- **Relational placement** — group abstractions (relative, around, grid, room) express layouts the way designers think.
- **Hierarchical composition** — build a furniture cluster once, then place it as a single unit; groups nest and optimize level by level.
- **Automatic refinement** — constraints resolve overlaps, keep objects in bounds, preserve clearances/sightlines, and sanity-check proportions with a VLM.
- **Blender output** — every scene exports to `.blend` for rendering or further editing.

## Installation

```bash
# 1. Clone
git clone https://github.com/KunalMGupta/interioragent.git
cd interioragent

# 2. Environment
conda create -n interioragent python=3.12 -y
conda activate interioragent

# 3. Python dependencies
pip install numpy matplotlib trimesh scipy tqdm sceneprogllm
```

A few external pieces are required:

- **SceneProgExec** — runs the Blender export/render pipeline. Follow the setup at
  <https://github.com/KunalMGupta/SceneProgExec> (this also wires up Blender). Then make
  `sceneprogllm` available inside Blender's bundled Python:
  ```bash
  sceneprogexec install sceneprogllm
  ```
- **Asset datasets** — the large 3D furniture datasets are **not** included in this repo
  and must be downloaded separately for asset retrieval to work.
  1. Download `datasets.zip` from
     [this OneDrive link](https://ucsdcloud-my.sharepoint.com/:u:/g/personal/k5gupta_ucsd_edu/IQA-MyG8SVWHQq4bWCD7amCmAWr9R9hyxe8e6udYgZNZ_TI?e=aX7HBn).
  2. Extract it into `IDSDL/` so that the data lands at `IDSDL/datasets/assets/` and
     `IDSDL/datasets/futurehssd/`:
     ```bash
     unzip datasets.zip -d IDSDL/
     ```
  These directories are git-ignored, so they will not be committed.
- **OpenAI API key** — used for asset retrieval and the VLM constraints:
  ```bash
  export OPENAI_API_KEY="sk-..."
  ```

## Quick start

```python
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("first_scene", seed=42)

# Group a sofa and coffee table into a reusable seating unit
with scene.RelativeGroup() as seating:
    sofa  = scene.AddAsset("a modern gray sofa")
    table = scene.AddAsset("a wooden coffee table")
    seating.set_anchor(sofa)
    seating.place_on_front(table)

# Place the unit into an automatically sized room
with scene.RoomGroup() as room:
    room.place_on_center(seating, facing="front")

scene.export("first_scene.blend")
```

```bash
python first_scene.py     # writes first_scene.blend
```

Open the result in Blender, or render it with the helpers in `render_docs.py`.

## Core concepts

| Concept | Entry point | What it does |
|---|---|---|
| **Object registration** | `scene.AddAsset(...)` | Retrieve, scale, rotate, copy, and query 3D assets. |
| **Groups** | `RelativeGroup`, `AroundGroup`, `GridGroup`, `RoomGroup` | Arrange objects relationally; groups nest into hierarchies. |
| **Constraints** | gradient + VLM | Refine layouts: overlap, bounds, clearance, access, visibility, proportions. |

See the [documentation](https://interioragent.github.io/docs/) for a full reference with
top-down and perspective renders of every feature.

## Repository layout

```
IDSDL/
  scene.py          # SceneProgRoom — the top-level scene API
  object.py         # SceneProgObject — base object, transforms, geometry queries
  groups.py         # RelativeGroup / AroundGroup / GridGroup / RoomGroup /
                    #   BasicRoomGroup / SentenceASCIIGenerator
  constraints.py    # gradient + VLM constraints and the layout solvers
  wall.py           # walls, floor, ceiling
  door.py, window.py# architectural openings
  renderer/         # Blender rendering helpers
  datasets/         # asset retrievers (large data fetched separately)
  assets/           # bundled door / window / curtain / wall-texture assets
planner_core/       # InteriorPlanner — RAG-based design-image generator
  planner.py        #   generate() + edit() over an LLM image model
  rag.py            #   SkillsRAG — embedding retrieval over the skills library
assets/             # planner data: skills.json (rag_cache.npz built on first run)
tests.py            # IDSDL feature test suite
docs_figures.py     # builds the documentation example scenes and renders them
render_docs.py      # render any results/*.blend from top-down / perspective views
build_preview.py    # generate a standalone HTML preview of the docs
```

## Running the tests

The test suite doubles as a gallery of working examples (each test builds and exports a scene).

```bash
python tests.py            # list all tests
python tests.py 6          # run one
python tests.py 1 2 5      # run several
python tests.py all        # run everything
```

Tests need `OPENAI_API_KEY` set and the datasets installed.

## Interior Planner (`planner_core`)

`InteriorPlanner` is a separate, lighter-weight path that generates **interior-design images**
(not 3D geometry) from a text prompt. It is retrieval-augmented: a library of design "skill
cards" is embedded and searched, the most relevant cards are synthesized into a single
conditioning description, and an image model renders a photorealistic **2×4 collage** of one
coherent room. You can then refine the design conversationally, with state preserved between
turns.

### Extra setup

`planner_core` reuses `sceneprogllm` and your `OPENAI_API_KEY` (set above), and additionally
needs:

```bash
pip install tqdm
```

Its data lives in `assets/`:
- `skills.json` — the design skills library (committed).
- `rag_cache.npz` — cached embeddings of the skills. This is **not** committed; it is built
  automatically the first time you run the planner (a one-time embedding pass over
  `skills.json`) and reused afterwards.

### Quick start

```python
from planner_core import InteriorPlanner

planner = InteriorPlanner()

# Initial generation
result = planner("A gym in San Diego")
result.save("v1.png")

# Iterative edits — design state is preserved between calls
result = planner.edit("make it more minimalist, remove most equipment")
result.save("v2.png")

result = planner.edit("add large windows with ocean views")
result.save("v3.png")
```

### How it works

1. **Retrieve** — `SkillsRAG` embeds the prompt and returns the top-k most similar skill cards from `skills.json` (cosine similarity over the cached embeddings).
2. **Synthesize** — an LLM composes the retrieved cards into one reusable conditioning *skill* (design principles, materials, lighting, composition cues).
3. **Render** — an image model turns the prompt + conditioning skill into an eight-panel editorial collage of a single consistent room.
4. **Edit** — `edit(instruction)` refines the current conditioning skill and re-renders, keeping the originally retrieved skills.

Each `generate`/`edit` returns a `DesignResult` with `.image`, the synthesized `.skill`, the
`.retrieved` cards, and a `.save(path)` helper.

| Call | Description |
|---|---|
| `InteriorPlanner(retrieval_top_k=3)` | Construct the planner (loads the skills library + embedding cache). |
| `planner(prompt)` / `planner.generate(prompt)` | Generate a fresh design; resets state. |
| `planner.edit(instruction)` | Refine the current design; raises if nothing has been generated yet. |
| `DesignResult.save(path)` | Save the generated image. |

## Notes

- Coordinate system: the floor is the **XZ plane** and **Y is up**; rooms span
  `x ∈ [0, WIDTH]`, `z ∈ [0, DEPTH]`, with the back wall at `z = 0`.
- Large datasets, generated `.blend`/render outputs, and the documentation site are excluded
  from this repo (see `.gitignore`); the docs live at
  [interioragent/docs](https://github.com/interioragent/docs).

## Text→scene generation (`main.py`)

One command turns a prompt into a `.blend` scene, encoding the same workflow used to
hand-build the library scenes (see `skills/SKILLS.md`):

```bash
python main.py "a cozy ramen bar with counter seating" --out results/ramen_bar
```

Pipeline (`generator_core/pipeline.py`):

1. **Plan** — `planner_core` produces a design brief + reference collage.
2. **Retrieve** — `retriever_core` selects context by **reasoning over the whole
   knowledge catalog** (no embeddings): the worked example recipes (indexed by *layout
   pattern*, so a pharmacy pulls the retail_store skeleton), the workflow guides, and
   the atomic lessons likely to fire (lighting density, window voids, retrieval SET
   traps, …). Inspect the catalog offline: `python -m retriever_core --catalog`.
3. **Asset stress test** — the shopping list is batch-resolved against the warm
   retriever and audited (similarity + chosen mesh), so the author pins/rewords weak
   picks before writing any placement.
4. **Author** — a pluggable `Author` writes the IDSDL program. Default is a single
   LLM (`--author llm`); `--author command --command '<shell cmd>'` delegates to ANY
   external coding agent (Claude Code, Codex, aider, …) via a prepared workspace
   (`TASK.md` + `scene.py`) — nothing is hardcoded to a specific agent.
5. **Build + inner loop** — each build produces the room VLM strip + textual VLM
   feedback; a **critic** that encodes the `skills/workflow/vlm_feedback.md` playbook
   turns feedback into concrete program directives until converged (`--max-inner`).
6. **Outer loop** — a **design judge** scores the built room against the plan
   (strip vs. collage + brief, 0–10) and emits gap directives until the score clears
   `--threshold` (default 8.0) or `--max-outer` is exhausted.

Every run writes full provenance to `<out>/trace.json` (procedural signature, selected
traces, asset audit, per-iteration feedback→directives, judge scores) plus
`program.py`, `scene.blend`, `final_strip.png`.

**Render policy:** builds run under the minimal render policy by default — the only
render per compile is the room VLM strip (the single critique channel). Set
`IDSDL_MINIMAL_RENDERS=0` for full per-group renders + the 8-view interior set
(see `IDSDL/render_policy.py`).

## MCP server (warm, typed tools for agents)

`IDSDL/service/mcp_server.py` is a stdio [MCP](https://modelcontextprotocol.io) server that
exposes the asset/scene tooling as **warm, typed tools returning structured data + inline
images** — so an agent (e.g. Claude Code) drives the asset-discovery loop without cold-reloading
the ~687 MB embeddings on every CLI call. The shared logic lives in `IDSDL/service/core.py`
(warm singletons: base retriever, router, planner); the workbench CLI uses the same core.

Setup:
```bash
/opt/conda/envs/interioragent/bin/pip install mcp        # one-time dependency
```
Registration is `/.mcp.json` (project-scoped; Claude Code discovers it on session start and
prompts to approve `idsdl`). Requires `OPENAI_API_KEY` in the environment **at launch** — the
warm process snapshots it. If the key rotates mid-session, call the **reload_credentials**
tool (pass the fresh key, or write `OPENAI_API_KEY=...` to `/work/.env` and call it bare)
instead of restarting; LLM-backed tools also detect a stale key and point you there rather
than dumping a 401 traceback.

Tools (`mcp__idsdl__*`): **retrieve / inspect** (route+resolve a query → candidate contact sheet
inline), **browse** (montage of dataset matches), **reselect / show / pin** (session-memory picks
— instant, no re-retrieval; `pin` → the `AddAsset(asset_id=…)` snippet), **candidates / gallery /
pool_add** (pool curation), **ingest_glbs** (custom-asset ingestion + auto re-warm), **plan**
(design brief + collage) and **run_scene** (build+render a DSL program → VLM feedback + room views).

Knowledge + generation tools: **catalog** (the tacit-knowledge index, offline),
**retrieve_context** (reasoning-based trace retrieval → bundle.md for an agent to read before
authoring a scene — this is the agent-as-author path: plan → retrieve_context → write the
program yourself with retrieve/pin → run_scene), **lint_program** (static API check of a scene
program in milliseconds — `run_scene`/`workbench run` refuse to build on errors), and
**generate_scene_start / _status / _result** (the full main.py pipeline as a background job —
takes 15–45 min, so it is job-based with live strip previews while it runs).

Guided-flow tools — the 9-gate recipe as a server-side state machine (`IDSDL/service/flow.py`):
**howto** (orientation card for a fresh agent), **flow_start / flow_status / flow_advance /
flow_override**. Each gate's card says what to do and what evidence to bring back; evidence is
validated mechanically (files exist, program lints clean, FRESH phase-N build report, no
unresolved `[Lint]`/`WARNING` lines) before the next step is revealed, and overrides are
recorded in the flow's provenance. State is file-backed under `tmp/flows/`, so a disconnected
agent resumes exactly where it stopped.

### Iterative verification (lints + phases)

Two mechanisms make "verify early, cheap" mechanical rather than aspirational:
- **Deterministic lints** (`IDSDL/lints.py`): post-compile geometric checks (floor objects
  floating/sunk, lighting starfield) recorded in the build's VLM feedback, plus `lint_program`
  — a static AST validation of a program against the real DSL surface that catches invented
  verbs/kwargs in milliseconds instead of a failed multi-minute build. `workbench lint`,
  `workbench run` (pre-build), the MCP `lint_program` tool and the generation pipeline all use it.
- **Phase-gated builds** (`IDSDL/phases.py`): a program gates its statements with
  `if PHASE >= n:` (1 anchors / 2 surfaces / 3 walls+mood); `workbench run --phase 1` then
  builds just the floor layout in ~1–2 min (vs ~9 for a full build) so layout errors are caught
  before any expensive dressing. Non-gated programs are unaffected (default = build everything).
  The generation pipeline runs phase-1/2 gate builds on every freshly authored program.

## About

InteriorAgent-IDSDL is part of the Ph.D. research of **Kunal Gupta** (CSE, UC San Diego) on
codifying design expertise into computational form so generative AI systems can perform better
on creative tasks.
