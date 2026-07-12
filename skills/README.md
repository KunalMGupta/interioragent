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

This knowledge base is also machine-retrievable: `retriever_core/` parses these files
into a card catalog (recipes indexed by layout pattern, workflow guides, atomic
lessons) and an LLM reasons over the whole catalog to select what's procedurally
relevant for a new prompt — used by `main.py` and the MCP `retrieve_context` tool.
Keep the markdown structures (README tables, decision-log bullets, `##` sections)
intact when writing back so new lessons stay retrievable.

### B. Codebase-extension playbooks (Claude Code SKILL.md format)

Reusable, agent-runnable playbooks for extending IDSDL **without changing core logic**. Each is a
folder with a `SKILL.md` (name + description front matter, then instructions).

| Skill | Purpose |
|---|---|
| [add-placement-group](add-placement-group/SKILL.md) | Add a new placement group / arrangement motif to `IDSDL/groups_extra.py` — hand-written motifs or integrations of external 3D scene-generation repos (SceneMotifCoder, diffusion/transformer/CNN/LLM models). Validates numerically + via renders. |
| _add-constraint_ | _(planned)_ Add a new optimization constraint without touching core. |

## Using a skill

These live in the project repo as documentation/playbooks. To make one auto-discoverable by Claude
Code, copy or symlink its folder into `.claude/skills/`, e.g.:

```bash
ln -s "$(pwd)/skills/add-placement-group" .claude/skills/add-placement-group
```

The agent can also just be pointed at the relevant `SKILL.md` directly.
