"""Pluggable scene-program authors.

The Author is the component that actually WRITES the IDSDL program. Two
implementations ship:

  * LLMAuthor     — a single LLM call (sceneprogllm); self-contained default.
  * CommandAuthor — delegates authorship to ANY external coding agent via a
                    shell command. The generator prepares a workspace with
                    TASK.md (instructions + full context bundle) and scene.py,
                    runs your command, and reads scene.py back. Nothing is
                    hardcoded to a particular agent: point it at Claude Code,
                    Codex, aider, or your own harness.

        --author command --command 'claude -p "$(cat TASK.md)" --permission-mode acceptEdits'
        --author command --command 'codex exec "$(cat TASK.md)"'

    The command runs with the workspace as cwd; {workspace}, {task_file} and
    {program_file} placeholders are substituted if present.
"""
from __future__ import annotations

import os
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

_AUTHOR_RULES = """
Hard requirements for the program you write:
- One self-contained Python file. Start with `from IDSDL.scene import SceneProgRoom`.
- Create the scene with a FIXED seed: `scene = SceneProgRoom("<Name>", seed=<int>)`.
- Immediately after creating the scene, call `scene.prefetch_assets([...])` with every
  asset description you will use (concurrent retrieval warm-up).
- Structure the program coarse-to-fine AND phase-GATE it (IDSDL/phases.py):
  `from IDSDL.phases import current_phase` then `PHASE = current_phase()` at the top,
  gating the later layers with plain ifs so the harness can build a cheap layout-only
  version first:
    phase 1 (ungated): floor anchors, composed stations, doors, the RoomGroup shell
    `if PHASE >= 2:` place_on_top / place_inside surface dressing
    `if PHASE >= 3:` wall art, windows, lighting, mood decor
  The default build runs everything; later phases must only ADD, never move phase-1
  geometry. (Canonical form: skills/examples/coffee_shop_v1.py.)
- Build repeated composed units ONCE and duplicate with `N * unit`.
- Use the asset audit: for weak/wrong picks, reword the query or pin `asset_id=`;
  pin anything whose colour carries the palette.
- The design brief — and the PLAN IMAGE when one is attached — is the target. Translate
  its zones, signature elements, materials and lighting mood into concrete placements;
  a scene that ignores the plan's identity elements will be rejected by the judge.
- ROOM SIZE IS A CONSEQUENCE, NOT A CHOICE. The RoomGroup auto-sizes the shell to fit
  every occupied floor slot (3x3 grid: width covers the widest row, depth the deepest
  column). A small/cozy room therefore means: occupy FEW floor slots (4-5 max), keep
  hero widths modest (a small-shop counter is 2.2-2.6 m, never 3.5+), and NEVER put a
  wide multi-cluster composed group into a single slot (it stretches the whole room).
  Spreading placements across all nine slots produces a cavernous hall no amount of
  decor can fill. NEVER raise modulate_scale above 1.0 to fix overlaps — remove or
  shrink furniture instead.
- Aim for a FINISHED, well-filled room (occupancy ~0.4), never a sparse one: dress every
  large surface with place_on_top props, put rugs under seating clusters, hang decor on
  empty walls, and MASS the category's identity prop at viewing height (pastries in a
  cafe, bouquets in a florist, merchandise in a shop). More small clusters beat one
  lonely arrangement in an oversized shell.
- Layer the lighting: room-level add_lighting with a FLAT FLUSH fixture at low density,
  plus a pendant/task fixture on the key zone group. A window helps daylight but keep it
  a standard pane.
- Wall-hung methods (place_on_wall_*) are for FLAT art/mirrors/boards only (< 0.25 m
  deep). Anything with real depth (shelving, panels, cabinets) is floor furniture:
  place_on_<wall>_wall_<pos>.
- End with exactly: scene.export(r"{out_blend}")
- Output ONLY the Python program, no prose.
"""

_REVISE_RULES = """
You are revising an existing IDSDL scene program. Apply the directives with the
smallest coherent edit — keep everything that already works (same seed, same pinned
assets unless a directive says otherwise). Output ONLY the full revised program.
"""


@dataclass
class AuthorTask:
    prompt: str
    brief: str                 # planner conditioning skill
    context_md: str            # retriever bundle
    asset_audit: str           # stress-test table (may be empty)
    out_blend: str             # absolute path the program must export to
    scene_name: str = "GeneratedScene"
    seed: int = 42


class Author(ABC):
    """`images` are reference image paths: the design plan collage and (for
    revisions) the current build's room strip — authors that can see should look."""

    @abstractmethod
    def write(self, task: AuthorTask, images: list[str] | None = None) -> str: ...

    @abstractmethod
    def revise(self, task: AuthorTask, program: str, directives: list[str],
               images: list[str] | None = None) -> str: ...


def _strip_fences(code: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", code, flags=re.S)
    return (m.group(1) if m else code).strip() + "\n"


class LLMAuthor(Author):
    """Single-LLM program author (the self-contained default)."""

    def __init__(self, model_name: str = "gpt-5", reasoning_effort: str = "high"):
        from sceneprogllm import LLM
        # text mode + own fence stripping: sceneprogllm's "code" format crashes on
        # replies with zero or multiple ``` fences
        self._llm = LLM(
            system_desc="You are an expert author of IDSDL interior-scene programs. "
                        "You follow the provided DSL reference, example recipes and "
                        "lessons exactly; they encode hard-won tacit knowledge.",
            response_format="text",
            model_name=model_name,
            reasoning_effort=reasoning_effort,
        )

    def _task_header(self, task: AuthorTask) -> str:
        return (
            f"User prompt: {task.prompt}\n\n"
            f"Design brief (build THIS look):\n{task.brief}\n\n"
            f"Asset audit (retrieval stress test — sims, chosen meshes, pins to reuse):\n"
            f"{task.asset_audit or '(not run)'}\n\n"
            f"=== CONTEXT BUNDLE (DSL reference, matched recipes, lessons) ===\n"
            f"{task.context_md}\n"
        )

    def write(self, task: AuthorTask, images: list[str] | None = None) -> str:
        query = (
            self._task_header(task)
            + "\n=== YOUR JOB ===\nWrite the complete IDSDL scene program.\n"
            + ("(The attached image is the DESIGN PLAN collage — the target look.)\n"
               if images else "")
            + _AUTHOR_RULES.format(out_blend=task.out_blend)
            + f"\nScene name: {task.scene_name}; seed: {task.seed}."
        )
        return _strip_fences(self._llm(query, image_paths=images or None))

    def revise(self, task: AuthorTask, program: str, directives: list[str],
               images: list[str] | None = None) -> str:
        bullet = "\n".join(f"- {d}" for d in directives)
        query = (
            self._task_header(task)
            + f"\n=== CURRENT PROGRAM ===\n```python\n{program}\n```\n"
            + f"\n=== DIRECTIVES (apply these) ===\n{bullet}\n"
            + ("(Attached images, in order: the CURRENT BUILD's interior strip, then "
               "the DESIGN PLAN collage — close the gap between them.)\n" if images else "")
            + _REVISE_RULES
            + f"\nThe program must still end with: scene.export(r\"{task.out_blend}\")"
        )
        return _strip_fences(self._llm(query, image_paths=images or None))


class CommandAuthor(Author):
    """Delegates authorship to an external coding agent via a shell command."""

    def __init__(self, command: str, workspace: str | Path, timeout: int = 3600):
        self.command = command
        self.workspace = Path(workspace)
        self.timeout = timeout

    def _run(self, task: AuthorTask, task_md: str, program: str | None) -> str:
        self.workspace.mkdir(parents=True, exist_ok=True)
        task_file = self.workspace / "TASK.md"
        program_file = self.workspace / "scene.py"
        task_file.write_text(task_md)
        program_file.write_text(program or "# Write the IDSDL scene program here.\n")

        # Substitute ONLY the three documented placeholders. str.format() would
        # choke on any other brace in the user's command (shell `{}`/`{a,b}`,
        # inline JSON) before the subprocess even runs.
        cmd = self.command
        for key, val in (("{workspace}", self.workspace),
                         ("{task_file}", task_file),
                         ("{program_file}", program_file)):
            cmd = cmd.replace(key, str(val))
        subprocess.run(cmd, shell=True, cwd=self.workspace, timeout=self.timeout,
                       check=True, env={**os.environ})
        result = program_file.read_text()
        if "SceneProgRoom" not in result:
            raise RuntimeError(
                f"external author left no usable program in {program_file}")
        return result

    @staticmethod
    def _image_section(images):
        if not images:
            return ""
        listing = "\n".join(f"- {p}" for p in images)
        return (f"\n## Reference images (open and LOOK at these)\n{listing}\n"
                f"(build strip first if present, then the design-plan collage)\n")

    def write(self, task: AuthorTask, images: list[str] | None = None) -> str:
        md = (
            f"# Write an IDSDL scene program\n\n"
            f"Edit `scene.py` in this directory so it builds the scene below. "
            f"Do not create other entry points; `scene.py` is what gets run.\n\n"
            f"User prompt: {task.prompt}\n\n## Design brief\n{task.brief}\n"
            + self._image_section(images)
            + f"\n## Asset audit\n{task.asset_audit or '(not run)'}\n\n"
            + _AUTHOR_RULES.format(out_blend=task.out_blend)
            + f"\nScene name: {task.scene_name}; seed: {task.seed}.\n\n"
            f"# Context bundle\n{task.context_md}\n"
        )
        return self._run(task, md, None)

    def revise(self, task: AuthorTask, program: str, directives: list[str],
               images: list[str] | None = None) -> str:
        bullet = "\n".join(f"- {d}" for d in directives)
        md = (
            f"# Revise the IDSDL scene program\n\n"
            f"Edit `scene.py` in place to apply the directives with the smallest "
            f"coherent change. Keep the seed and pinned assets unless directed.\n\n"
            f"User prompt: {task.prompt}\n\n## Directives\n{bullet}\n\n"
            f"## Design brief\n{task.brief}\n"
            + self._image_section(images)
            + f"\nThe program must still end with: scene.export(r\"{task.out_blend}\")\n\n"
            f"# Context bundle\n{task.context_md}\n"
        )
        return self._run(task, md, program)
