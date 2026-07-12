"""Knowledge catalog — a deterministic, structured index of every tacit-knowledge
trace in the repo: worked example recipes, workflow guides, atomic lessons, and
the polished scene programs behind the recipes.

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
    "hair_salon": ["scenes/work/salon_pretty.py", "scenes/hair_salon.py"],
    "kitchen": ["scenes/work/kitchen_eatin.py"],
}


@dataclass
class Card:
    id: str            # stable id the selector uses, e.g. "example:restaurant"
    kind: str          # "example" | "workflow" | "lesson"
    title: str         # one line, shown in the catalog listing
    summary: str       # one-two lines of what it teaches (catalog listing)
    path: str | None = None       # source file (relative to repo root)
    body: str | None = None       # full text for the bundle (lessons carry it inline)
    extras: dict = field(default_factory=dict)  # example cards: program/note paths


def _read(rel: str) -> str:
    return (ROOT / rel).read_text()


def _first_paragraph(text: str) -> str:
    for block in text.split("\n\n"):
        block = block.strip()
        if block and not block.startswith("#"):
            return re.sub(r"\s+", " ", block)
    return ""


def _resolve_program(name: str) -> str | None:
    candidates = [f"scenes/work/{name}.py"]
    candidates += PROGRAM_ALIASES.get(name, [])
    candidates += [f"scenes/{name}.py"]
    for rel in candidates:
        if (ROOT / rel).is_file():
            return rel
    return None


class KnowledgeCatalog:
    """Builds and renders the full card catalog from the repo's markdown."""

    def __init__(self, root: Path = ROOT):
        self.root = Path(root)
        self.cards: list[Card] = []
        self._build()

    # ------------------------------------------------------------------
    # building

    def _build(self):
        self._add_examples()
        self._add_workflow_docs()
        self._add_vlm_feedback_lessons()
        self._add_asset_selection_lessons()
        self._add_cross_cutting_lessons()

    def _add_examples(self):
        """Worked-example recipes from skills/examples/, summarized by the
        pattern catalogue in its README (the procedural index)."""
        readme = _read("skills/examples/README.md")
        section = None
        # worked rows have 3 columns (name|category|pattern); early rows only 2
        row_re = re.compile(r"\|\s*\[([^\]]+)\.md\]\([^)]*\)\s*\|([^|]*)\|(?:(.*)\|)?")
        for line in readme.splitlines():
            if line.startswith("## "):
                low = line.lower()
                if "worked" in low:
                    section = "worked"
                elif "early" in low:
                    section = "early"
                else:
                    section = None
                continue
            m = row_re.match(line.strip())
            if not m or section is None:
                continue
            name, category, pattern = (
                (g or "").strip() for g in m.groups())
            rel = f"skills/examples/{name}.md"
            if not (self.root / rel).is_file():
                continue
            extras = {"status": section}
            program = _resolve_program(name)
            if program:
                extras["program"] = program
            note = f"scenes/notes/{name}.md"
            if (self.root / note).is_file():
                extras["note"] = note
            summary = f"[{category}] {re.sub(r'[*]', '', pattern)}"
            if section == "early":
                summary += " (EARLY SKELETON — thin, use for rough shape only)"
            self.cards.append(Card(
                id=f"example:{name}", kind="example", title=name,
                summary=re.sub(r"\s+", " ", summary), path=rel, extras=extras,
            ))

    def _add_workflow_docs(self):
        for f in sorted((self.root / "skills/workflow").glob("*.md")):
            rel = f"skills/workflow/{f.name}"
            text = f.read_text()
            title = f.stem
            heading = re.match(r"#\s*(.+)", text)
            if heading:
                title = heading.group(1).strip()
            self.cards.append(Card(
                id=f"workflow:{f.stem}", kind="workflow", title=title,
                summary=_first_paragraph(text)[:220], path=rel,
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

    def _add_vlm_feedback_lessons(self):
        """Each decision-log entry in vlm_feedback.md is an atomic lesson:
        [scene] feedback -> action -> result, with the generalizable rule."""
        text = _read("skills/workflow/vlm_feedback.md")
        m = re.search(r"^## Decision log.*?$", text, flags=re.M)
        if not m:
            return
        log = text[m.end():]
        for i, bullet in enumerate(self._iter_top_bullets(log)):
            bullet = bullet.strip()
            if not bullet.startswith("**"):
                continue
            title_m = re.match(r"\*\*(.+?)\*\*", bullet, flags=re.S)
            title = re.sub(r"\s+", " ", title_m.group(1))[:110] if title_m else bullet[:110]
            # the bold prefix is often just "[scene, topic]" — add a body snippet
            # so the selector can judge relevance from the listing alone
            rest = re.sub(r"\s+", " ", bullet[title_m.end():] if title_m else bullet)
            snippet = rest.strip(" —-→:")[:130]
            self.cards.append(Card(
                id=f"lesson:vlm/{i}", kind="lesson",
                title=f"{title} {snippet}".strip(),
                summary=title, path="skills/workflow/vlm_feedback.md", body=bullet,
            ))

    def _add_asset_selection_lessons(self):
        """Each '##' section of asset_selection.md is a retrieval lesson/playbook."""
        text = _read("skills/workflow/asset_selection.md")
        parts = re.split(r"^## ", text, flags=re.M)
        for part in parts[1:]:
            title, _, body = part.partition("\n")
            title = title.strip()
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]
            self.cards.append(Card(
                id=f"lesson:asset/{slug}", kind="lesson", title=title,
                summary=_first_paragraph(body)[:200],
                path="skills/workflow/asset_selection.md",
                body=f"## {title}\n{body.strip()}",
            ))

    def _add_cross_cutting_lessons(self):
        """The numbered cross-cutting DSL issues from scenes/NOTES.md."""
        try:
            text = _read("scenes/NOTES.md")
        except FileNotFoundError:
            return
        m = re.search(r"^## Cross-cutting.*?$", text, flags=re.M)
        if not m:
            return
        section = text[m.end():]
        end = re.search(r"^## ", section, flags=re.M)
        if end:
            section = section[:end.start()]
        for i, item in enumerate(re.split(r"^\d+\.\s", section, flags=re.M)[1:]):
            item = item.strip()
            title_m = re.match(r"\*\*(.+?)\*\*", item, flags=re.S)
            title = re.sub(r"\s+", " ", title_m.group(1))[:110] if title_m else item[:110]
            self.cards.append(Card(
                id=f"lesson:dsl/{i}", kind="lesson", title=title,
                summary=title, path="scenes/NOTES.md", body=item,
            ))

    # ------------------------------------------------------------------
    # access

    def by_id(self, card_id: str) -> Card | None:
        for c in self.cards:
            if c.id == card_id:
                return c
        return None

    def of_kind(self, kind: str) -> list[Card]:
        return [c for c in self.cards if c.kind == kind]

    def listing(self) -> str:
        """The compact organized catalog the selector LLM reasons over in full."""
        out = ["# Knowledge catalog", ""]
        out.append("## Worked example recipes (pick by LAYOUT PATTERN, not by name)")
        for c in self.of_kind("example"):
            out.append(f"- `{c.id}` — {c.summary}")
        out.append("")
        out.append("## Workflow guides")
        for c in self.of_kind("workflow"):
            out.append(f"- `{c.id}` — {c.title}: {c.summary}")
        out.append("")
        out.append("## Atomic lessons (feedback→action decisions, retrieval traps, DSL gotchas)")
        for c in self.of_kind("lesson"):
            out.append(f"- `{c.id}` — {c.title}")
        return "\n".join(out)

    def card_text(self, card: Card, include_program: bool = True) -> str:
        """Full text of a card for the context bundle."""
        parts = [f"### {card.id}"]
        if card.kind == "example":
            parts.append(_read(card.path))
            note = card.extras.get("note")
            if note:
                parts.append(f"\n#### Build log ({note})\n" + _read(note))
            program = card.extras.get("program")
            if include_program and program:
                parts.append(f"\n#### Polished program ({program})\n```python\n"
                             + _read(program) + "\n```")
        elif card.body:
            parts.append(card.body)
        elif card.path:
            parts.append(_read(card.path))
        return "\n".join(parts)
