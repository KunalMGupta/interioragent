# InteriorAgent — IDSDL

**An Interior-Design-aware Scene Description Language for composing structured 3D indoor scenes.**

IDSDL lets you describe interiors at the level of *design intent* — "a sofa with a coffee
table in front of it", "chairs around a dining table", "paintings spread across the back
wall" — instead of hand-placing meshes by coordinate. You write a short Python program; IDSDL
retrieves assets from natural-language descriptions, arranges them with spatial groups,
resolves the layout with geometric and vision-language constraints, and exports a Blender
`.blend` scene.

📖 **Full documentation & visual guide:** <https://interioragent.github.io/docs/>

This repository contains two complementary components:

- **IDSDL** — a structured language that builds explicit **3D scenes** (geometry you can open and render in Blender). *Documented below and on the docs site.*
- **InteriorPlanner** (`planner_core/`) — a retrieval-augmented **design-image** generator that turns a text prompt into a photorealistic interior collage and supports conversational editing. *See [Interior Planner](#interior-planner-planner_core).*

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

## About

InteriorAgent-IDSDL is part of the Ph.D. research of **Kunal Gupta** (CSE, UC San Diego) on
codifying design expertise into computational form so generative AI systems can perform better
on creative tasks.
