# IDSDL skills

Reusable, agent-runnable playbooks for extending IDSDL **without changing core logic**. Each skill
is a folder with a `SKILL.md` (name + description front matter, then instructions), following the
Claude Code skill format.

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
