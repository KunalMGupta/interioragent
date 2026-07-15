"""Knowledge catalog — a deterministic, structured index of every tacit-knowledge
trace in the repo: worked example recipes, workflow guides, atomic lessons, and
the polished scene programs behind the recipes.

Since 2026-07-15 the catalog is a GRAPH, not just a flat list:
  * nodes  — Cards with STABLE ids. Examples/workflow docs are file-based; the
    atomic lessons carry explicit ``{#slug}`` anchors in their source files, so
    inserting a lesson never renumbers its neighbours.
  * edges  — typed links: ``cites`` (mined from prose name-mentions at build
    time — nobody maintains them by hand), ``applies_to`` (a lesson's [scene]
    prefix), ``program``/``build_log``/``variant`` (an example's artifacts),
    ``wiki`` ([[slug]] links, resolved via anchors + a small alias table), and
    ``read_for`` (situation triggers promoted from the old README advisories).

No embeddings anywhere. The catalog renders to a compact organized listing that
a reasoning LLM reads in full to pick what is procedurally relevant (see
retriever.py). Parsing is deterministic (markdown structure only) so the
catalog needs no cache and never goes stale.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Polished program lookup: worked-example name -> candidate program paths, first
# hit wins. scenes/work/ holds the iterated builds (sometimes under a renamed
# key); the top-level scenes/<name>.py is the fallback.
PROGRAM_ALIASES = {
    "bar": ["scenes/work/bar_lounge.py"],
    "bathroom": ["scenes/work/bath_spa.py"],
    "florist_shop": ["scenes/work/flower_shop.py"],
    "garage": ["scenes/work/garage_workshop.py"],
    "hair_salon": ["scenes/hair_salon.py"],
    "kitchen": ["scenes/work/kitchen_eatin.py"],
}

# [[wiki-slug]] -> card id, for slugs that predate the anchor system. Slugs that
# resolve to neither an anchor nor an alias are "unwritten vocabulary": kept and
# reported (they mark a lesson worth writing), never an error.
WIKI_ALIASES = {
    "asset_selection": "workflow:asset_selection",
    "design_principles": "workflow:design_principles",
    "grocery_store": "example:grocery_store",
    "set-assets-and-scaling": "lesson:asset/set-assets-bundled-categories-vanities-toile",
    "smart-placement": "reference:dsl_reference",
    "workstation-group": "reference:dsl_reference",
}

# Always-on core docs (mirrored in retriever.CORE_DOCS): included in every
# bundle, so the selector must not spend picks on them.
CORE_PATHS = {
    "skills/dsl_reference.md",
    "skills/workflow/coarse_to_fine.md",
    "skills/workflow/design_principles.md",
}


@dataclass
class Card:
    id: str            # stable id the selector uses, e.g. "example:restaurant"
    kind: str          # "example" | "workflow" | "lesson" | "reference"
    title: str         # one line, shown in the catalog listing
    summary: str       # one-two lines of what it teaches (catalog listing)
    path: str | None = None       # source file (relative to repo root)
    body: str | None = None       # full text for the bundle (lessons carry it inline)
    extras: dict = field(default_factory=dict)  # example cards: program/note paths


@dataclass
class Edge:
    src: str           # card id
    rel: str           # cites | applies_to | program | build_log | variant | wiki | read_for
    dst: str           # card id, or for program/build_log a repo-relative path,
                       # or for read_for the trigger phrase itself


def _read(rel: str) -> str:
    return (ROOT / rel).read_text()


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Minimal YAML-subset frontmatter: `key: value`, quoted values, `- ` lists."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    meta, key = {}, None
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val:
                meta[key] = val.strip('"')
            else:
                meta[key] = []
        elif line.strip().startswith("- ") and key and isinstance(meta.get(key), list):
            meta[key].append(line.strip()[2:].strip('"'))
    body = text[end + 4:]
    return meta, body.lstrip("\n")


def _first_paragraph(text: str) -> str:
    for block in text.split("\n\n"):
        block = block.strip()
        if block and not block.startswith(("#", "---")):
            return re.sub(r"\s+", " ", block)
    return ""


_ANCHOR = re.compile(r"\s*\{#([a-z0-9-]+)\}")


def _strip_anchor(text: str) -> str:
    return _ANCHOR.sub("", text)


def _resolve_program(name: str) -> str | None:
    # The polished, phase-gated program is skills/examples/<name>_v<N>.py — highest N wins
    # (see skills/examples/README.md: "the .py is the thing you copy"). The scenes/ paths are
    # the older working drafts, kept as fallbacks for names that never got a _v program.
    def _ver(p):
        m = re.search(r"_v(\d+)\.py$", p.name)
        return int(m.group(1)) if m else 0
    versioned = sorted(ROOT.glob(f"skills/examples/{name}_v*.py"), key=_ver, reverse=True)
    candidates = [str(p.relative_to(ROOT)) for p in versioned]
    candidates += [f"scenes/work/{name}.py"]
    candidates += PROGRAM_ALIASES.get(name, [])
    candidates += [f"scenes/{name}.py"]
    for rel in candidates:
        if (ROOT / rel).is_file():
            return rel
    return None


def _variant_programs(name: str) -> list[str]:
    """Programs in the example's FAMILY beyond its own versions: kitchen ->
    kitchen_set_v3.py, kitchen_l_v1.py (highest version per sub-stem)."""
    best: dict[str, tuple[int, str]] = {}
    for p in ROOT.glob(f"skills/examples/{name}_*_v*.py"):
        m = re.match(rf"{re.escape(name)}_(.+)_v(\d+)\.py$", p.name)
        if not m:
            continue
        stem, ver = m.group(1), int(m.group(2))
        if stem not in best or ver > best[stem][0]:
            best[stem] = (ver, str(p.relative_to(ROOT)))
    return [path for _, path in sorted(best.values())]


class KnowledgeCatalog:
    """Builds and renders the full card catalog + typed edge graph from the
    repo's markdown. Deterministic; safe to rebuild on every load."""

    def __init__(self, root: Path = ROOT):
        self.root = Path(root)
        self.cards: list[Card] = []
        self.edges: list[Edge] = []
        self.unresolved_wiki: dict[str, list[str]] = {}   # slug -> [card ids using it]
        self._anchors: dict[str, str] = {}                # {#slug} -> card id
        self._build()

    # ------------------------------------------------------------------
    # building

    def _build(self):
        self._add_examples()
        self._add_reference_docs()
        self._add_workflow_docs()
        self._add_vlm_feedback_lessons()
        self._add_asset_selection_lessons()
        self._add_dsl_gotcha_lessons()
        self._add_principle_lessons()
        self._build_edges()

    def _add_examples(self):
        """Worked-example recipes: one card per skills/examples/<name>.md,
        described by its own frontmatter (id/category/pattern/family/read_for).
        The README table remains the human index; the frontmatter is the
        machine truth."""
        for f in sorted((self.root / "skills/examples").glob("*.md")):
            if f.name.startswith("_") or f.name == "README.md":
                continue
            name = f.stem
            meta, _ = _parse_frontmatter(f.read_text())
            rel = f"skills/examples/{name}.md"
            extras = {
                "status": "worked",
                "category": meta.get("category", ""),
                "pattern": meta.get("pattern", ""),
                "family": meta.get("family", "other"),
                "read_for": meta.get("read_for", []) or [],
            }
            program = _resolve_program(name)
            if program:
                extras["program"] = program
            variants = _variant_programs(name)
            if variants:
                extras["variants"] = variants
            note = f"skills/examples/logs/{name}.md"
            if (self.root / note).is_file():
                extras["note"] = note
            summary = f"[{extras['category']}] {extras['pattern']}"
            self.cards.append(Card(
                id=f"example:{name}", kind="example", title=name,
                summary=re.sub(r"\s+", " ", summary), path=rel, extras=extras,
            ))

    def _add_reference_docs(self):
        """Top-level references outside workflow/ (today: the DSL reference).
        Core docs ride along in every bundle; they get cards so edges can
        point at them, flagged core so the selector skips them."""
        rel = "skills/dsl_reference.md"
        if (self.root / rel).is_file():
            self.cards.append(Card(
                id="reference:dsl_reference", kind="reference",
                title="IDSDL DSL reference",
                summary="The API reference (always included in every bundle — do not select)",
                path=rel, extras={"core": True},
            ))

    def _add_workflow_docs(self):
        for f in sorted((self.root / "skills/workflow").glob("*.md")):
            rel = f"skills/workflow/{f.name}"
            meta, body = _parse_frontmatter(f.read_text())
            title = f.stem
            heading = re.match(r"#\s*(.+)", body)
            if heading:
                title = _strip_anchor(heading.group(1)).strip()
            summary = meta.get("role") or _first_paragraph(body)[:220]
            extras = {"role_kind": meta.get("kind", "workflow")}
            if rel in CORE_PATHS:
                extras["core"] = True
                summary += " (always included in every bundle — do not select)"
            elif extras["role_kind"] == "collection":
                summary += " (a COLLECTION — select its individual lessons instead)"
            self.cards.append(Card(
                id=f"workflow:{f.stem}", kind="workflow", title=title,
                summary=summary, path=rel, extras=extras,
            ))

    def _iter_top_bullets(self, text: str):
        """Yield top-level '- ' bullets with their continuation lines."""
        current = None
        for line in text.splitlines():
            if line.startswith("- "):
                if current:
                    yield current
                current = line[2:]
            elif current is not None and (line.startswith("  ") or line.strip() == ""):
                current += "\n" + line
            else:
                if current:
                    yield current
                current = None
        if current:
            yield current

    def _slug_of(self, text: str, prefix: str) -> str | None:
        m = re.search(r"\{#(" + re.escape(prefix) + r"-[a-z0-9-]+)\}", text)
        return m.group(1) if m else None

    def _add_vlm_feedback_lessons(self):
        """Each decision-log entry in vlm_feedback.md is an atomic lesson:
        [scene] feedback -> action -> result, with the generalizable rule.
        Identity comes from the entry's {#vlm-...} anchor, so inserting an
        entry never renumbers the rest."""
        text = _read("skills/workflow/vlm_feedback.md")
        m = re.search(r"^## Decision log.*?$", text, flags=re.M)
        if not m:
            return
        log = text[m.end():]
        for i, bullet in enumerate(self._iter_top_bullets(log)):
            bullet = bullet.strip()
            if not bullet.startswith("**"):
                continue
            slug = self._slug_of(bullet, "vlm")
            lesson_id = f"lesson:vlm/{slug[4:]}" if slug else f"lesson:vlm/{i}"
            clean = _strip_anchor(bullet)
            title_m = re.match(r"\*\*(.+?)\*\*", clean, flags=re.S)
            title = re.sub(r"\s+", " ", title_m.group(1))[:110] if title_m else clean[:110]
            rest = re.sub(r"\s+", " ", clean[title_m.end():] if title_m else clean)
            snippet = rest.strip(" —-→:")[:130]
            self.cards.append(Card(
                id=lesson_id, kind="lesson",
                title=f"{title} {snippet}".strip(),
                summary=title, path="skills/workflow/vlm_feedback.md", body=bullet,
                extras={"topic": "vlm", "scene_prefix": title},
            ))
            if slug:
                self._anchors[slug] = lesson_id

    def _add_asset_selection_lessons(self):
        """Each '##' section of asset_selection.md is a retrieval lesson/playbook."""
        text = _read("skills/workflow/asset_selection.md")
        _, body = _parse_frontmatter(text)
        parts = re.split(r"^## ", body, flags=re.M)
        for part in parts[1:]:
            heading, _, rest = part.partition("\n")
            slug = self._slug_of(heading, "asset")
            title = _strip_anchor(heading).strip()
            tail = slug[6:] if slug else re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]
            lesson_id = f"lesson:asset/{tail}"
            self.cards.append(Card(
                id=lesson_id, kind="lesson", title=title,
                summary=_first_paragraph(rest)[:200],
                path="skills/workflow/asset_selection.md",
                body=f"## {title}\n{rest.strip()}",
                extras={"topic": "asset"},
            ))
            if slug:
                self._anchors[slug] = lesson_id

    def _add_dsl_gotcha_lessons(self):
        """The numbered cross-cutting DSL issues from skills/workflow/dsl_gotchas.md."""
        try:
            text = _read("skills/workflow/dsl_gotchas.md")
        except FileNotFoundError:
            return
        _, body = _parse_frontmatter(text)
        for i, item in enumerate(re.split(r"^\d+\.\s", body, flags=re.M)[1:]):
            item = item.strip()
            slug = self._slug_of(item, "dsl")
            lesson_id = f"lesson:dsl/{slug[4:]}" if slug else f"lesson:dsl/{i}"
            clean = _strip_anchor(item)
            title_m = re.match(r"\*\*(.+?)\*\*", clean, flags=re.S)
            title = re.sub(r"\s+", " ", title_m.group(1))[:110] if title_m else clean[:110]
            self.cards.append(Card(
                id=lesson_id, kind="lesson", title=title,
                summary=title, path="skills/workflow/dsl_gotchas.md", body=item,
                extras={"topic": "dsl"},
            ))
            if slug:
                self._anchors[slug] = lesson_id

    def _add_principle_lessons(self):
        """design_principles.md sections as graph nodes. The whole doc is a
        CORE doc (in every bundle), so these cards exist for edges and the
        listing marks them un-selectable."""
        try:
            text = _read("skills/workflow/design_principles.md")
        except FileNotFoundError:
            return
        _, body = _parse_frontmatter(text)
        for part in re.split(r"^## ", body, flags=re.M)[1:]:
            heading, _, rest = part.partition("\n")
            slug = self._slug_of(heading, "principle")
            if not slug:
                continue
            title = _strip_anchor(heading).strip()
            lesson_id = f"lesson:principle/{slug[10:]}"
            self.cards.append(Card(
                id=lesson_id, kind="lesson", title=title,
                summary=title + " (core doc — already in every bundle, do not select)",
                path="skills/workflow/design_principles.md",
                body=f"## {title}\n{rest.strip()}",
                extras={"topic": "principle", "core": True},
            ))
            self._anchors[slug] = lesson_id

    # ------------------------------------------------------------------
    # edges

    def _build_edges(self):
        examples = self.of_kind("example")
        names = {c.title: c.id for c in examples}
        name_re = re.compile(r"\b(" + "|".join(sorted(map(re.escape, names), key=len, reverse=True)) + r")\b")

        # example -> example cites, mined from prose (self-mentions excluded)
        for c in examples:
            body = _read(c.path)
            counts: dict[str, int] = {}
            for m in name_re.finditer(body):
                other = m.group(1)
                if other != c.title:
                    counts[other] = counts.get(other, 0) + 1
            for other, n in sorted(counts.items(), key=lambda kv: -kv[1]):
                self.edges.append(Edge(c.id, "cites", names[other]))
            c.extras["cites"] = [names[o] for o, _ in sorted(counts.items(), key=lambda kv: -kv[1])]
            # artifacts
            if c.extras.get("program"):
                self.edges.append(Edge(c.id, "program", c.extras["program"]))
            for v in c.extras.get("variants", []):
                self.edges.append(Edge(c.id, "variant", v))
            if c.extras.get("note"):
                self.edges.append(Edge(c.id, "build_log", c.extras["note"]))
            for trig in c.extras.get("read_for", []):
                self.edges.append(Edge(c.id, "read_for", trig))

        # lesson -> example applies_to, from the [scene ...] bold prefix
        for c in self.of_kind("lesson"):
            if c.extras.get("topic") != "vlm":
                continue
            m = re.match(r"\[([a-z0-9_]+)", c.summary)
            if m:
                scene = m.group(1)
                target = names.get(scene)
                if not target:
                    # program-family scenes (kitchen_set, kitchen_l) roll up to their example
                    for nm in names:
                        if scene.startswith(nm + "_") or scene == nm:
                            target = names[nm]
                            break
                if target:
                    self.edges.append(Edge(c.id, "applies_to", target))

        # [[wiki]] links from every card's source text
        for c in self.cards:
            text = c.body if c.body else (_read(c.path) if c.path else "")
            for slug in set(re.findall(r"\[\[([\w-]+)\]\]", text or "")):
                dst = self._anchors.get(slug) or WIKI_ALIASES.get(slug)
                if dst:
                    if dst != c.id:
                        self.edges.append(Edge(c.id, "wiki", dst))
                else:
                    self.unresolved_wiki.setdefault(slug, []).append(c.id)

    # ------------------------------------------------------------------
    # access

    def by_id(self, card_id: str) -> Card | None:
        for c in self.cards:
            if c.id == card_id:
                return c
        return None

    def of_kind(self, kind: str) -> list[Card]:
        return [c for c in self.cards if c.kind == kind]

    def links(self, card_id: str, rel: str | None = None) -> list[Edge]:
        return [e for e in self.edges if e.src == card_id and (rel is None or e.rel == rel)]

    def backlinks(self, card_id: str, rel: str | None = None) -> list[Edge]:
        return [e for e in self.edges if e.dst == card_id and (rel is None or e.rel == rel)]

    def listing(self) -> str:
        """The compact organized catalog the selector LLM reasons over in full.
        Examples are grouped by layout FAMILY (the procedural key), each with
        its read-for triggers and top prose-cited relatives."""
        out = ["# Knowledge catalog", ""]
        out.append("## Worked example recipes (pick by LAYOUT PATTERN, not by name; grouped by family)")
        by_family: dict[str, list[Card]] = {}
        for c in self.of_kind("example"):
            by_family.setdefault(c.extras.get("family", "other"), []).append(c)
        for fam in sorted(by_family):
            out.append(f"### family: {fam}")
            for c in by_family[fam]:
                line = f"- `{c.id}` — {c.summary}"
                for trig in c.extras.get("read_for", []):
                    trig = re.sub(r"^READ (FOR|BEFORE)\s*", "", trig, flags=re.I)[:90]
                    line += f" | READ FOR {trig}"
                rel = [self.by_id(i).title for i in c.extras.get("cites", [])[:3]]
                if rel:
                    line += f" | related: {', '.join(rel)}"
                out.append(line)
            out.append("")
        out.append("## Workflow guides and references")
        for c in self.of_kind("workflow") + self.of_kind("reference"):
            out.append(f"- `{c.id}` — {c.title}: {c.summary}")
        out.append("")
        out.append("## Atomic lessons (feedback→action decisions, retrieval traps, DSL gotchas)")
        for c in self.of_kind("lesson"):
            if c.extras.get("core"):
                continue    # principle cards ride along in the core docs
            out.append(f"- `{c.id}` — {c.title}")
        return "\n".join(out)

    def card_text(self, card: Card, include_program: bool = True) -> str:
        """Full text of a card for the context bundle."""
        parts = [f"### {card.id}"]
        if card.kind == "example":
            _, body = _parse_frontmatter(_read(card.path))
            parts.append(body)
            note = card.extras.get("note")
            if note:
                parts.append(f"\n#### Build log ({note})\n" + _read(note))
            program = card.extras.get("program")
            if include_program and program:
                parts.append(f"\n#### Polished program ({program})\n```python\n"
                             + _read(program) + "\n```")
            # graph context: sibling lessons + variants, as pointers not full text
            minted = [e.src for e in self.backlinks(card.id, "applies_to")]
            if minted:
                parts.append("\n#### Lessons minted on this scene (request by id if needed)\n"
                             + "\n".join(f"- `{i}`" for i in minted))
            variants = card.extras.get("variants", [])
            if variants:
                parts.append("\n#### Variant programs\n" + "\n".join(f"- `{v}`" for v in variants))
        elif card.body:
            parts.append(card.body)
        elif card.path:
            _, body = _parse_frontmatter(_read(card.path))
            parts.append(body)
        return "\n".join(parts)
