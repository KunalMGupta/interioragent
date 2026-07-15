"""Knowledge-base contract linter — run after any write-back to skills/.

Checks the invariants the knowledge graph depends on (see skills/README.md):
frontmatter on every example, unique {#slug} anchors on every lesson, all graph
edges resolving, and the catalog building to sane counts. Exit 1 on violations;
unresolved [[wiki]] vocabulary is reported but never fatal (a dangling slug
marks a lesson worth writing).

    python tools/kb_check.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    errs, infos = [], []

    from retriever_core.catalog import KnowledgeCatalog
    cat = KnowledgeCatalog()

    counts = {}
    for c in cat.cards:
        counts[c.kind] = counts.get(c.kind, 0) + 1
    infos.append(f"cards: {counts} | edges: {len(cat.edges)}")
    if counts.get("example", 0) < 54:
        errs.append(f"expected >= 54 example cards, got {counts.get('example', 0)}")
    if counts.get("lesson", 0) < 196:
        errs.append(f"expected >= 196 lesson cards, got {counts.get('lesson', 0)} "
                    "(did an anchor get deleted?)")

    # every example file has frontmatter and a family
    exdir = os.path.join(ROOT, "skills/examples")
    for f in sorted(os.listdir(exdir)):
        if not f.endswith(".md") or f.startswith("_") or f == "README.md":
            continue
        text = open(os.path.join(exdir, f)).read()
        if not text.startswith("---\n"):
            errs.append(f"skills/examples/{f}: missing frontmatter")
        elif "family:" not in text.split("\n---")[0]:
            errs.append(f"skills/examples/{f}: frontmatter has no family")

    # anchors are unique repo-wide (they are the lessons' identities)
    anchors = []
    for dirpath, _, files in os.walk(os.path.join(ROOT, "skills")):
        for f in files:
            if f.endswith(".md"):
                anchors += re.findall(r"\{#([a-z0-9-]+)\}",
                                      open(os.path.join(dirpath, f)).read())
    dupes = sorted({a for a in anchors if anchors.count(a) > 1})
    if dupes:
        errs.append(f"duplicate {{#anchors}}: {dupes}")

    # positional lesson ids mean a lesson lost its anchor
    positional = [c.id for c in cat.cards
                  if c.kind == "lesson" and c.id.rsplit("/", 1)[-1].isdigit()]
    if positional:
        errs.append(f"lessons with positional (anchor-less) ids: {positional}")

    # all edges resolve
    ids = {c.id for c in cat.cards}
    for e in cat.edges:
        if e.rel in ("cites", "applies_to", "wiki") and e.dst not in ids:
            errs.append(f"edge {e.src} -{e.rel}-> {e.dst}: target card missing")
        if e.rel in ("program", "variant", "build_log") and not os.path.exists(
                os.path.join(ROOT, e.dst)):
            errs.append(f"edge {e.src} -{e.rel}-> {e.dst}: file missing")

    if cat.unresolved_wiki:
        infos.append("unwritten [[wiki]] vocabulary (fine, but worth writing): "
                     + ", ".join(sorted(cat.unresolved_wiki)))

    listing = cat.listing()
    infos.append(f"listing renders: {len(listing)} chars")

    for i in infos:
        print("  ·", i)
    if errs:
        print(f"\n{len(errs)} CONTRACT VIOLATION(S):")
        for e in errs:
            print("  !", e)
        return 1
    print("\nknowledge-base contracts: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
