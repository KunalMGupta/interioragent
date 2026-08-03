# InteriorAgent

**An agentic harness for 3D interior design.** Give an AI agent a room to create — it plans
the space, retrieves furniture by describing it in plain language, writes a short scene
program, builds it, looks at the renders, and iterates until the design works. The output is
a real Blender scene you can open, render, and edit.

📖 **Scene-language documentation & visual guide:** <https://interioragent.github.io/docs/>

Everything the agent needs ships in this repo:

- **A live toolbox** — an [MCP server](#1-let-an-agent-drive-mcp) with warm, typed tools for
  asset retrieval, shopping, planning, and building, driven interactively by any MCP client
  (Claude Code, Claude Desktop, …).
- **A design knowledge library** — [`skills/`](skills/README.md): 55+ worked example scenes
  and hundreds of atomic build lessons, organized as a knowledge graph that a retriever
  *reasons* over (no embeddings) to brief the agent before it designs.
- **IDSDL, the scene engine** — a Python DSL where you compose interiors by *design intent*
  ("a sofa with a coffee table in front of it", "chairs around a dining table"): natural-language
  asset retrieval, relational groups, constraint solving, Blender export.
- **A fully autonomous pipeline** — [`main.py`](#2-one-command-fully-automatic): one command
  from text prompt to finished `.blend`, with a VLM critic loop and a design judge.

## Getting started

```bash
git clone https://github.com/KunalMGupta/interioragent.git
cd interioragent
conda create -n interioragent python=3.12 -y && conda activate interioragent   # needs >= 3.11
pip install -r requirements.txt
```

Then three external pieces, in this order (each is the first thing that fails without the
previous one):

**1. Blender 4.5.x** — the build/render engine. [Download](https://www.blender.org/download/)
(4.5.4 is what we test), extract anywhere, and export both paths (put them in your shell
profile), then install the LLM helper into Blender's bundled Python:

```bash
export BLENDER_PATH=/path/to/blender-4.5.4-linux-x64/blender
export BLENDER_PYTHON=/path/to/blender-4.5.4-linux-x64/4.5/python/bin/python3.11
sceneprogexec install sceneprogllm
```

**2. The asset library** — the 3D furniture datasets are not in git; they ship as a single
bundle you extract at the repo root.

> **Dataset terms — read first.** The bundles below repackage assets from
> [3D-FUTURE](https://tianchi.aliyun.com/dataset/98063) (Alibaba) and
> [HSSD](https://huggingface.co/datasets/hssd/hssd-models) (Hab-lab, CC BY-NC), provided
> purely as a convenience for research reproduction. Before downloading, please visit the
> official sources above and accept their respective terms of use — your use of the
> bundled assets is governed by those upstream licenses, not by this repository's license.

```bash
wget https://interioragent-datasets.s3.amazonaws.com/idsdl_datasets_mini.zip
unzip idsdl_datasets_mini.zip -d .
```

- **Quick demo (~14 GB, recommended first)** —
  [`idsdl_datasets_mini.zip`](https://interioragent-datasets.s3.amazonaws.com/idsdl_datasets_mini.zip):
  a curated library of ~3k proven assets (every asset a past build chose or a worked example
  pins). The pipeline runs unchanged — retrieval is simply limited to what's on disk, and the
  tools announce the minimal install.
- **Full library (~75 GB)** —
  [`idsdl_datasets.zip`](https://interioragent-datasets.s3.amazonaws.com/idsdl_datasets.zip):
  all ~29k FutureHSSD assets + the ingested custom library (see `ATTRIBUTIONS.md`).
  Extracting it over a mini install upgrades in place.

**3. An OpenAI API key** — used for retrieval, planning, and the VLM critics:

```bash
export OPENAI_API_KEY="sk-..."
```

That's it — you can now [run a scene](#3-write-scenes-yourself-the-idsdl-library) or connect
an agent.

<details>
<summary><b>Optional setup</b> — asset-shop keys, all environment variables, Docker</summary>

**Asset-shop keys.** Only needed to bring in assets the library does not have
(`python -m IDSDL.shop`, or `SceneProgRoom(..., acquire="mid"|"high")` to let the retriever
fill a measured gap itself — see [skills/acquire-assets](skills/acquire-assets/SKILL.md)).
Put them in `<repo>/.env` (git-ignored, see [`.env.example`](.env.example)) or the environment.
Sketchfab *search* needs no key; only downloading does — without a token the pipeline still
runs, hands you the download links, and picks the files up from `<batch>/inbox/`.

```bash
SKETCHFAB_API_TOKEN=...   # free: sketchfab.com -> Settings -> Password & API
MESHY_API_KEY=...         # only for --source meshy (text-to-3D generation; spends credits)
```

**Environment variables at a glance:**

| Variable | Required? | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | **yes** | retrieval embeddings, planning, VLM captions/critics |
| `BLENDER_PATH`, `BLENDER_PYTHON` | **yes** | where SceneProgExec finds Blender |
| `SKETCHFAB_API_TOKEN` | shop only | downloading Sketchfab assets (search is public) |
| `MESHY_API_KEY` | shop only | text-to-3D generation (`--source meshy`) |
| `IDSDL_SKY` | optional | interior sky strength (default 3.0; ~1.2 for moody/pale rooms; shell-level only) |
| `IDSDL_MINIMAL_RENDERS` | optional | `0` = full per-group renders (default minimal: strip only) |
| `IDSDL_ACQUIRE` | optional | retriever gap-filling dial: `low` (default) / `mid` / `high` |
| `IDSDL_SMART_PLACEMENT`, `IDSDL_LINTS`, `IDSDL_AUTO_CLEARANCES` | optional | escape hatches, on by default — see the docstrings in `IDSDL/` |
| `IDSDL_ROOT`, `WORKBENCH_OUT`, `IDSDL_PYTHON` | optional | path/interpreter overrides for the service, workbench and MCP launcher |

**Docker.** The [`Dockerfile`](Dockerfile) builds an environment image (conda env + Blender
under `/opt`, so a repo mount can't shadow it); the repo — with datasets extracted — is
volume-mounted. The conda + pip path above is the primary supported setup; the image is a
convenience.

```bash
docker build -t interioragent .
docker run -it -v "$PWD":/work -w /work -e OPENAI_API_KEY interioragent bash
```

Maintainers rebuild the dataset bundles with `python tools/make_datasets_bundle.py [--curated]`.

</details>

## Three ways to use it

### 1. Let an agent drive (MCP)

The heart of the harness: a stdio [MCP](https://modelcontextprotocol.io) server
(`IDSDL/service/mcp_server.py`) exposing the asset and scene tooling as warm, typed tools
returning structured data + inline images. An agent designs interactively — browse and pin
assets, read the knowledge catalog, build phase by phase, look at renders, refine — without
cold-reloading the ~687 MB embeddings on every call.

**Claude Code:** just open this repo — [`.mcp.json`](.mcp.json) is discovered on session
start and prompts to approve `interioragent`. Then ask the agent to design a room; the
**howto** tool orients a fresh agent, and **flow_start** walks it through the gated recipe
with mechanically validated evidence at each step. By default the flow runs in **inference
mode** — it ends at the finished `.blend` and treats the knowledge library (`skills/`) as
read-only; pass `teach=true` (or set `IDSDL_TEACH=1`) to append the write-back gate that
distills the scene into `skills/` and grows the library.

**Claude Desktop** (or any client that doesn't launch from the repo root) — point at the
launcher by absolute path; it anchors itself to the repo:

```json
{
  "mcpServers": {
    "interioragent": {
      "command": "/abs/path/to/interioragent/tools/interioragent_mcp.sh",
      "env": {
        "IDSDL_PYTHON": "/abs/path/to/conda/envs/interioragent/bin/python",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

Startup takes ~10–20 s (the embeddings warm once); a missing dataset or key is reported on
stderr with the fix. Long tools (`run_scene`, `shop_run`, `plan`, `ingest_glbs`) take minutes
but run off the event loop, so the server stays responsive throughout — give your client a
generous per-tool timeout, or use the `generate_scene_start/status/result` job tools.

**Verify your install** before pointing a client at it — this speaks the MCP protocol at the
launcher exactly the way a client would, and prints the server's own explanation on failure:

```bash
python3 tools/mcp_smoke.py             # handshake + tool listing + a howto call
python3 tools/mcp_smoke.py --retrieve  # also a real asset retrieval (~20 s)
```

If it fails with a message about the `mcp` package or the conda env, the launcher could not
find your `interioragent` environment — either install deps into it
(`pip install -r requirements.txt`) or set `IDSDL_PYTHON` to the right interpreter.

<details>
<summary><b>The full tool roster</b> — assets, knowledge, generation, guided flow</summary>

**Asset tools:** **retrieve / inspect** (route+resolve a query → candidate contact sheet
inline), **browse** (montage of dataset matches), **reselect / show / pin** (session-memory
picks — instant, no re-retrieval; `pin` → the `AddAsset(asset_id=…)` snippet), **candidates /
gallery / pool_add** (pool curation), **ingest_glbs** (custom-asset ingestion + auto re-warm),
**shop_search / shop_run / shop_apply** (find an asset the library does NOT have on Sketchfab —
or generate one with Meshy — normalize, verify and ingest it, re-warmed so it is retrievable in
the same session; anything the pipeline will not judge alone lands on a `HELP.md` for you).

**Knowledge + generation tools:** **catalog** (the tacit-knowledge index, offline),
**retrieve_context** (reasoning-based trace retrieval → bundle.md for an agent to read before
authoring — this is the agent-as-author path: plan → retrieve_context → write the program
yourself with retrieve/pin → run_scene), **plan** (design brief + collage), **lint_program**
(static API check of a scene program in milliseconds — `run_scene`/`workbench run` refuse to
build on errors), **run_scene** (build+render a DSL program → VLM feedback + room views), and
**generate_scene_start / _status / _result** (the full `main.py` pipeline as a background job —
15–45 min, with live strip previews while it runs).

**Guided-flow tools** — the worked-example recipe as a server-side state machine
(`IDSDL/service/flow.py`): **howto**, **flow_start / flow_status / flow_advance /
flow_override**. Two modes: **inference** (default, 8 gates — plan → retrieve → asset audit →
author → three phased builds → judge — ending at the `.blend`, `skills/` untouched) and
**teach** (`flow_start(prompt, teach=true)`, adding the 9th write-back gate that grows the
knowledge library). Each gate's card says what to do and what evidence to bring back; evidence is
validated mechanically (files exist, program lints clean, FRESH phase-N build report, no
unresolved `[Lint]`/`WARNING` lines) before the next step is revealed, and overrides are
recorded in the flow's provenance. State is file-backed under `tmp/flows/`, so a disconnected
agent resumes exactly where it stopped.

**Credentials:** the warm process snapshots `OPENAI_API_KEY` at launch. If the key rotates
mid-session, call **reload_credentials** (pass the fresh key, or write it to `<repo>/.env` and
call it bare) instead of restarting; LLM-backed tools detect a stale key and point you there
rather than dumping a 401 traceback.

**Verification is mechanical, not aspirational:**
- *Deterministic lints* (`IDSDL/lints.py`): post-compile geometric checks (floor objects
  floating/sunk, lighting starfield) recorded in build feedback, plus `lint_program` — static
  AST validation against the real DSL surface that catches invented verbs/kwargs in
  milliseconds instead of a failed multi-minute build.
- *Phase-gated builds* (`IDSDL/phases.py`): a program gates statements with `if PHASE >= n:`
  (1 anchors / 2 surfaces / 3 walls+mood); `workbench run --phase 1` builds just the floor
  layout in ~1–2 min (vs ~9 full) so layout errors are caught before expensive dressing.
  Non-gated programs are unaffected.

</details>

### 2. One command, fully automatic

```bash
python main.py "a cozy ramen bar with counter seating" --out results/ramen_bar
```

The pipeline (`generator_core/pipeline.py`) encodes the same workflow used to hand-build the
library scenes: **plan** (design brief + reference collage) → **retrieve** (reason over the
knowledge catalog for the right worked examples and lessons) → **asset stress test**
(batch-resolve the shopping list, audit weak picks) → **author** the IDSDL program →
**build + critic loop** (VLM feedback → concrete directives until converged) → **design
judge** (scores the built room against the plan until it clears `--threshold`).

Every run writes full provenance to `<out>/trace.json`, plus `program.py`, `scene.blend`,
and `final_strip.png`.

<details>
<summary><b>Pipeline details</b> — pluggable authors, render policy</summary>

- **Pluggable authors** — default is a single LLM (`--author llm`);
  `--author command --command '<shell cmd>'` delegates authoring to ANY external coding agent
  (Claude Code, Codex, aider, …) via a prepared workspace (`TASK.md` + `scene.py`) — nothing
  is hardcoded to a specific agent.
- **Inner/outer loops** — the critic encodes the `skills/workflow/vlm_feedback.md` playbook
  and iterates up to `--max-inner`; the design judge (strip vs. collage + brief, 0–10) emits
  gap directives until the score clears `--threshold` (default 8.0) or `--max-outer`.
- **Render policy** — builds run minimal by default: the only render per compile is the room
  VLM strip (the single critique channel). Set `IDSDL_MINIMAL_RENDERS=0` for full per-group
  renders + the 8-view interior set (see `IDSDL/render_policy.py`).
- Inspect the knowledge catalog offline: `python -m retriever_core --catalog`.

</details>

### 3. Write scenes yourself (the IDSDL library)

IDSDL is the scene language underneath it all — you can use it directly as a Python library:

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
python first_scene.py     # writes first_scene.blend — open it in Blender
```

| Concept | Entry point | What it does |
|---|---|---|
| **Object registration** | `scene.AddAsset(...)` | Retrieve, scale, rotate, copy, and query 3D assets by description. |
| **Groups** | `RelativeGroup`, `AroundGroup`, `GridGroup`, `RoomGroup` | Arrange objects relationally; groups nest into hierarchies. |
| **Constraints** | gradient + VLM | Refine layouts: overlap, bounds, clearance, access, visibility, proportions. |

Coordinates: the floor is the **XZ plane**, **Y is up**; rooms span `x ∈ [0, WIDTH]`,
`z ∈ [0, DEPTH]` with the back wall at `z = 0`. The
[documentation site](https://interioragent.github.io/docs/) has a full reference with renders
of every feature, and the test suite doubles as a gallery of working examples:

```bash
python tests.py            # list all tests
python tests.py 6          # run one (needs OPENAI_API_KEY + datasets)
python tests.py all        # run everything
```

For day-to-day scene development, `workbench.py` builds/inspects a single program
(`workbench run`, `workbench lint`, `--phase 1` for a fast layout-only build).

## The knowledge library

[`skills/`](skills/README.md) is the harness's memory: 55+ worked example scenes (each a
recipe + a runnable program, indexed by *layout pattern* — a pharmacy pulls the retail_store
skeleton), workflow guides, and hundreds of atomic lessons learned across build iterations.
`retriever_core` organizes it all into a knowledge graph and selects context by **reasoning
over the catalog** — no embeddings — so the agent is briefed with exactly the recipes and
traps relevant to the room it's about to design.

## Interior Planner

`planner_core` is a lighter companion path that generates interior-design **images** (not 3D
geometry): a retrieval-augmented planner that turns a prompt into a photorealistic 2×4 collage
of one coherent room, with conversational editing. The 3D pipeline uses it for design briefs
and reference collages, but it also stands alone:

```python
from planner_core import InteriorPlanner

planner = InteriorPlanner()
result = planner("A gym in San Diego");  result.save("v1.png")
result = planner.edit("make it more minimalist");  result.save("v2.png")
```

<details>
<summary><b>How the planner works</b></summary>

1. **Retrieve** — `SkillsRAG` embeds the prompt and returns the top-k most similar design
   skill cards from `assets/skills.json` (cosine similarity; the `rag_cache.npz` embedding
   cache is built automatically on first run).
2. **Synthesize** — an LLM composes the retrieved cards into one conditioning *skill*
   (design principles, materials, lighting, composition cues).
3. **Render** — an image model turns prompt + conditioning skill into an eight-panel
   editorial collage of a single consistent room.
4. **Edit** — `edit(instruction)` refines the current conditioning skill and re-renders,
   keeping the originally retrieved skills; state is preserved between turns.

Each call returns a `DesignResult` with `.image`, the synthesized `.skill`, the `.retrieved`
cards, and a `.save(path)` helper. `InteriorPlanner(retrieval_top_k=3)` controls retrieval.

</details>

## Repository layout

Two layers: **`IDSDL/` is the scene engine**, and **`generator_core` / `planner_core` /
`retriever_core` are the agentic tier above it**. Dependencies flow one way —
`*_core → IDSDL`, never the reverse.

```
IDSDL/                # THE ENGINE — scene DSL, solver, retrieval, renderer
  scene.py            #   SceneProgRoom — the top-level scene API
  groups.py           #   RelativeGroup / AroundGroup / GridGroup / RoomGroup
  constraints.py      #   gradient + VLM constraints and the layout solvers
  datasets/           #   3D-mesh retrievers over FutureHSSD (data via the bundle)
  shop/               #   asset acquisition (Sketchfab/Meshy -> normalize -> ingest)
  service/            #   MCP server + shared warm core; the integration hub
generator_core/       # SceneGenerator: plan -> retrieve -> author -> build -> critic
planner_core/         # InteriorPlanner (design briefs + collages) + SkillsRAG
retriever_core/       # TraceRetriever — reasons over the knowledge catalog
skills/               # the knowledge library: worked examples + guides + lessons
main.py               # text -> finished scene, fully automatic
workbench.py          # build/inspect a single scene program; day-to-day dev CLI
tests.py              # IDSDL feature test suite (doubles as an example gallery)
tools/                # dev tooling (MCP launcher, docs figures, bundle builder, ...)
```

## About

InteriorAgent is part of the Ph.D. research of **Kunal Gupta** (CSE, UC San Diego) on
codifying design expertise into computational form so generative AI systems can perform
better on creative tasks.

## License

Code and documentation are released under the [MIT License](LICENSE). The vendored
[three.js](https://github.com/mrdoob/three.js) viewer (`IDSDL/vendor/three/`) is MIT-licensed
by the Three.js Authors. The 3D asset datasets (3D-FUTURE, HSSD, custom ingests) are
downloaded separately and are **not** covered by the MIT license — see the dataset-terms
notice in [Getting started](#getting-started) and accept the upstream terms at the official
[3D-FUTURE](https://tianchi.aliyun.com/dataset/98063) and
[HSSD](https://huggingface.co/datasets/hssd/hssd-models) pages before using the bundles.
