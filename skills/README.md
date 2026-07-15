# IDSDL skills

This folder holds two distinct, complementary kinds of knowledge. Don't confuse them.

### A. Scene-generation knowledge base — **start at [SKILLS.md](SKILLS.md)**

How to *use* the DSL to build and iteratively optimize a scene from a prompt
(coarse-to-fine workflow, constraint model, VLM-feedback playbook, per-scene
examples). This is the everyday loop for producing rooms. Layout:

| Path | Purpose |
|---|---|
| [SKILLS.md](SKILLS.md) | entry point — workflow + index (read first) |
| [dsl_reference.md](dsl_reference.md) | the DSL API cheat sheet |
| [workflow/](workflow/) | coarse_to_fine · constraints · vlm_feedback · rendering |
| [examples/](examples/) | per-scene-type recipes (living_room, classroom, kitchen, …) |

This knowledge base is also machine-retrievable — as a KNOWLEDGE GRAPH:
`retriever_core/` parses these files into cards (worked examples, workflow guides,
atomic lessons) plus typed edges (`cites` mined from prose mentions, `applies_to`
from a lesson's `[scene]` prefix, `wiki` from `[[slug]]` links, `read_for`
situation triggers, program/build-log/variant artifacts). An LLM reasons over the
whole catalog listing — examples grouped by layout FAMILY — to select what's
procedurally relevant, and a selected example pulls its `[[slug]]`-linked lessons
along automatically. Used by `main.py` and the MCP `retrieve_context` tool.

The contracts that keep it parseable when writing back:
  * every `examples/<name>.md` starts with frontmatter (`id`/`kind`/`family`/
    `category`/`pattern`, optional `read_for`) — copy a sibling's shape;
  * every decision-log entry in `workflow/vlm_feedback.md` carries a unique
    `{#vlm-<scene>-<topic>}` anchor after its bold prefix (that anchor IS the
    lesson's stable id — never renumber, never reuse);
  * `##` sections in `asset_selection.md` / `design_principles.md` and the
    numbered items in `dsl_gotchas.md` carry `{#...}` anchors the same way;
  * `[[slug]]` links are encouraged — they resolve to anchors and become graph
    edges; a `[[slug]]` with no anchor yet is fine (it marks a lesson worth
    writing, and the catalog reports it).

### B. Codebase-extension playbooks (Claude Code SKILL.md format)

Reusable, agent-runnable playbooks for extending IDSDL **without changing core logic**. Each is a
folder with a `SKILL.md` (name + description front matter, then instructions).

| Skill | Purpose |
|---|---|
| [generate-scene](generate-scene/SKILL.md) | Generate a complete 3D scene from a text prompt, end to end — the plan → retrieve-traces → asset-audit → author → build → critique → judge → write-back playbook (agent-as-author), plus the one-command `main.py` / MCP-job automatic mode. |
| [add-placement-group](add-placement-group/SKILL.md) | Add a new placement group / arrangement motif to `IDSDL/groups_extra.py` — hand-written motifs or integrations of external 3D scene-generation repos (SceneMotifCoder, diffusion/transformer/CNN/LLM models). Validates numerically + via renders. |
| [acquire-assets](acquire-assets/SKILL.md) | Get an asset the library does NOT have: the automatic search-and-ingest pipeline (`IDSDL/shop`) — Sketchfab search → download → Blender normalize → VLM triage → self-verify → ingest, skipping what it can't judge and asking you about the rest (`HELP.md`). Also covers generating assets with Meshy, and the six load-bearing Blender fixes. |
| _add-constraint_ | _(planned)_ Add a new optimization constraint without touching core. |

## Using a skill

These live in the project repo as documentation/playbooks. To make one auto-discoverable by Claude
Code, copy or symlink its folder into `.claude/skills/`, e.g.:

```bash
ln -s "$(pwd)/skills/add-placement-group" .claude/skills/add-placement-group
```

The agent can also just be pointed at the relevant `SKILL.md` directly.
