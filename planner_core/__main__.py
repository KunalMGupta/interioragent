"""
One-shot CLI for the InteriorPlanner.

    python -m planner_core "a cozy reading living room" [--out DIR] [--top-k 3]

Writes four predictable files into the output directory so the result can be
consumed without writing Python each time:

    plan.png        the 2x4 design collage (open it to see the look)
    skill.txt       the synthesized conditioning skill (dense design brief)
    retrieved.json  the top-k reference skills that fired (RAG provenance)
    prompt.txt      the prompt, for provenance

Must run under the project env, e.g.
    /opt/conda/envs/interioragent/bin/python -m planner_core "..."
"""
import argparse
import json
import re
import sys
from pathlib import Path

from .planner import InteriorPlanner


def _slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:max_len] or "plan"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="planner_core",
        description="Generate an interior-design plan (collage + conditioning skill) for a prompt.",
    )
    ap.add_argument("prompt", help="natural-language room description")
    ap.add_argument("--out", "-o", default=None,
                    help="output directory (default: tmp/plan_<slug>)")
    ap.add_argument("--top-k", type=int, default=3,
                    help="number of reference skills to retrieve (default: 3)")
    ap.add_argument("--refine", action="store_true",
                    help="refinement mode: generate an IMPROVED target from current renders "
                         "(+ prior target + skills) instead of a fresh plan")
    ap.add_argument("--renders", nargs="+", default=None,
                    help="current scene render(s) for --refine (e.g. a collection collage)")
    ap.add_argument("--prior", nargs="+", default=None,
                    help="optional prior design target image(s) for --refine")
    ap.add_argument("--instruction", default=None,
                    help="optional refinement focus for --refine")
    args = ap.parse_args(argv)

    out = Path(args.out) if args.out else Path("tmp") / f"plan_{_slug(args.prompt)}"
    out.mkdir(parents=True, exist_ok=True)

    planner = InteriorPlanner(retrieval_top_k=args.top_k)
    if args.refine:
        if not args.renders:
            ap.error("--refine requires --renders (current scene render paths)")
        result = planner.refine(args.renders, prior_paths=args.prior,
                                instruction=args.instruction, prompt=args.prompt)
        img_name = "refined_target.png"
    else:
        result = planner.generate(args.prompt)
        img_name = "plan.png"

    img_path = out / img_name
    result.save(str(img_path))
    (out / "skill.txt").write_text(result.skill.strip() + "\n")
    (out / "retrieved.json").write_text(json.dumps(result.retrieved, indent=2))
    (out / "prompt.txt").write_text(args.prompt + "\n")

    print(f"prompt:    {args.prompt}")
    print(f"out_dir:   {out}")
    print(f"image:     {img_path}")
    print(f"skill:     {out / 'skill.txt'}")
    print(f"retrieved: {out / 'retrieved.json'}  (top-{args.top_k})")

    print("\n--- retrieved reference skills ---")
    for r in result.retrieved:
        score = r.get("score", 0.0)
        cat = r.get("category", "?")
        ctx = str(r.get("context", "")).replace("\n", " ")[:90]
        print(f"  [{score:.3f}] ({cat}) {ctx}")

    print("\n--- synthesized conditioning skill ---")
    print(result.skill.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
