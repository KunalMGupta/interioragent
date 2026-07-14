"""CLI for the trace retriever.

    python -m retriever_core "<prompt>" [--plan path/to/skill.txt] [--out DIR]
    python -m retriever_core --catalog          # print the catalog listing (offline)
"""
import argparse
import sys
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="retriever_core")
    ap.add_argument("prompt", nargs="?", help="the scene prompt")
    ap.add_argument("--plan", default=None, help="path to a planner brief (skill.txt) to condition on")
    ap.add_argument("--out", default=None, help="output dir for bundle.md + selection.json")
    ap.add_argument("--no-programs", action="store_true", help="omit polished program sources from the bundle")
    ap.add_argument("--catalog", action="store_true", help="print the catalog listing and exit (offline)")
    args = ap.parse_args(argv)

    from retriever_core import KnowledgeCatalog, TraceRetriever

    catalog = KnowledgeCatalog()
    if args.catalog:
        print(catalog.listing())
        return 0
    if not args.prompt:
        ap.error("prompt is required (or use --catalog)")

    plan = Path(args.plan).read_text() if args.plan else None
    retriever = TraceRetriever(catalog)
    bundle = retriever.retrieve(args.prompt, plan=plan,
                                include_programs=not args.no_programs)

    print(f"\n--- procedural signature ---\n{bundle.procedural_signature}")
    print(f"\n--- reasoning ---\n{bundle.reasoning}")
    print(f"\n--- selection ---")
    print(f"examples : {bundle.examples}")
    print(f"workflow : {bundle.workflow_docs}")
    print(f"lessons  : {len(bundle.lessons)} -> {bundle.lessons}")

    if args.out:
        path = bundle.save(args.out)
        print(f"\nwrote {path} ({len(bundle.markdown)/1000:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
