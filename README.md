# InteriorAgent — IDSDL

**An Interior-Design-aware Scene Description Language for composing structured 3D indoor scenes.**

IDSDL lets you describe interiors at the level of *design intent* — "a sofa with a coffee
table in front of it", "chairs around a dining table", "paintings spread across the back
wall" — instead of hand-placing meshes by coordinate. You write a short Python program; IDSDL
retrieves assets from natural-language descriptions, arranges them with spatial groups,
resolves the layout with geometric and vision-language constraints, and exports a Blender
`.blend` scene.

📖 **Full documentation & visual guide:** <https://interioragent.github.io/docs/>

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
pip install numpy matplotlib trimesh scipy sceneprogllm
```

A few external pieces are required:

- **SceneProgExec** — runs the Blender export/render pipeline. Follow the setup at
  <https://github.com/KunalMGupta/SceneProgExec> (this also wires up Blender).
- **Asset datasets** — the large 3D furniture datasets are **not** included in this repo.
  Download `datasets.zip` and extract it into `IDSDL/` (so you have `IDSDL/datasets/...`).
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
tests.py            # feature test suite
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
