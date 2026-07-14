"""Text → 3D scene, end to end.

    python main.py "a cozy ramen bar with counter seating" --out results/ramen_bar

Pipeline (see generator_core/pipeline.py):
  plan → retrieve traces (reasoning, no embeddings) → asset stress test →
  author program → build → inner VLM-critic loop → outer design-match loop.

Authors are pluggable:
  --author llm       one strong LLM writes/revises the program (default)
  --author command   ANY external coding agent does, via a shell command run in a
                     prepared workspace (TASK.md + scene.py), e.g.:
                       --command 'claude -p "$(cat TASK.md)" --permission-mode acceptEdits'
                       --command 'codex exec "$(cat TASK.md)"'

Requires OPENAI_API_KEY, the asset datasets under IDSDL/datasets/, and Blender
via SceneProgExec (same requirements as running any scene program).
"""
import argparse
import os
import re
import sys
from pathlib import Path


def main(argv=None):
    # stream progress even when stdout is piped (generate.log, MCP jobs)
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        prog="main.py", description="Generate a 3D interior scene from a text prompt.")
    ap.add_argument("prompt", help="what to build, e.g. 'a cozy ramen bar'")
    ap.add_argument("--out", default=None,
                    help="output dir (default results/<slug>)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--name", default=None, help="scene name (default: from prompt)")
    ap.add_argument("--model", default="gpt-5",
                    help="LLM for planning/retrieval/critique/authoring (default gpt-5)")
    ap.add_argument("--author", choices=["llm", "command"], default="llm")
    ap.add_argument("--command", default=None,
                    help="shell command for --author command ({workspace}/{task_file}/"
                         "{program_file} placeholders available)")
    ap.add_argument("--max-inner", type=int, default=3,
                    help="max VLM-feedback fix iterations per build (default 3)")
    ap.add_argument("--max-outer", type=int, default=2,
                    help="max design-judgement iterations (default 2)")
    ap.add_argument("--threshold", type=float, default=8.0,
                    help="design-match score (0-10) that stops the outer loop")
    ap.add_argument("--skip-stress", action="store_true",
                    help="skip the asset stress test (faster, less grounded)")
    ap.add_argument("--stress-cap", type=int, default=30,
                    help="max queries in the stress test (default 30)")
    args = ap.parse_args(argv)

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set — every stage needs it.", file=sys.stderr)
        return 1

    slug = re.sub(r"[^a-z0-9]+", "_", args.prompt.lower()).strip("_")[:40]
    out = Path(args.out or f"results/{slug}")

    author = None
    if args.author == "command":
        if not args.command:
            ap.error("--author command requires --command '<shell command>'")
        from generator_core import CommandAuthor
        author = CommandAuthor(args.command, workspace=out / "author_workspace")
    else:
        from generator_core import LLMAuthor
        author = LLMAuthor(model_name=args.model)

    from generator_core import SceneGenerator
    gen = SceneGenerator(
        author=author, model_name=args.model,
        max_inner=args.max_inner, max_outer=args.max_outer,
        judge_threshold=args.threshold,
        stress_test=not args.skip_stress, stress_cap=args.stress_cap,
    )
    trace = gen.run(args.prompt, out, seed=args.seed, scene_name=args.name)
    return 0 if trace.get("final", {}).get("score", -1) >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
