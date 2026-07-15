"""TraceRetriever — reasoning-based retrieval over the knowledge catalog.

No embeddings. The selector LLM reads the ENTIRE organized catalog (it is small
— tens of cards with one-line summaries) together with the prompt and the
planner's brief, reasons about PROCEDURAL similarity, and picks the cards to
pull in full. Procedural similarity means matching by the room's layout
structure — hero anchor, repeated units, zones, perimeter loops, long rows —
not by category name: a pharmacy is procedurally a retail_store, a chapel is a
classroom-like rows-facing-focal-wall room.

Output is a ContextBundle: the always-on core docs (DSL reference, phase plan,
composition defaults) + the selected example recipes with their polished
programs and build logs + the selected workflow guides and atomic lessons.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .catalog import KnowledgeCatalog, ROOT, _read, _parse_frontmatter

# Included in every bundle regardless of selection — the non-negotiable base.
CORE_DOCS = [
    "skills/dsl_reference.md",
    "skills/workflow/coarse_to_fine.md",
    "skills/workflow/design_principles.md",
]

_SELECTOR_SYSTEM = """
You are a retrieval reasoner for a 3D interior-scene generation system (IDSDL).
Given a user prompt (and optionally a design brief from a planner), plus the full
catalog of available knowledge cards, decide which cards a scene author must read
before writing the scene program.

Reason about PROCEDURAL similarity, not surface category names:
- What is the room's layout structure? A single hero set-piece? A repeated unit
  tiled in a grid or rows? A zoned single room? A central spine with a perimeter
  loop? Long runs flush on walls? A cluster field?
- Which worked example teaches the closest layout pattern? A pharmacy is
  procedurally a retail_store; a chapel is a classroom (rows facing a focal
  wall); a wine bar mixes bar + restaurant. Pick 1-2 PRIMARY examples whose
  skeleton the author should copy, and at most 1 secondary for a sub-pattern.
  Prefer worked examples over early skeletons.
- Which atomic lessons will FIRE for this scene? (lighting fixture geometry and
  density, window black-void, retrieval SET traps, product-at-viewing-height for
  shops, place_on_top gotchas, room-rescale timing, rotation noise, ...) Select
  every lesson likely to apply — err on the side of inclusion for lessons; they
  are short.
- Which workflow guides matter beyond the always-included core (the DSL
  reference, the coarse-to-fine phase plan, and design principles are always
  provided — do NOT select those)? asset_selection is almost always relevant for
  a new scene; vlm_feedback when iterating; asset_ingest only if custom meshes
  will be added; rendering rarely.

First, write the procedural signature of the requested room: its hero/anchors,
repetition structure, zones, wall loading (which walls carry long runs and why —
this drives the room's aspect ratio), circulation, and what makes the category
legible (the "reads as" test).
Then select cards BY THEIR EXACT `id` from the catalog.

Respond with ONLY a JSON object (no prose outside it) with exactly these keys:
{
  "procedural_signature": "<the signature paragraph>",
  "primary_examples": ["example:..."],
  "secondary_examples": ["example:..."],
  "workflow_docs": ["workflow:..."],
  "lessons": ["lesson:..."],
  "reasoning": "<why these cards, briefly>"
}
"""


@dataclass
class ContextBundle:
    prompt: str
    plan: str | None
    procedural_signature: str
    reasoning: str
    core_docs: list[str]
    examples: list[str]          # card ids
    workflow_docs: list[str]     # card ids
    lessons: list[str]           # card ids
    markdown: str                # the assembled context document
    selection: dict = field(default_factory=dict)

    def save(self, out_dir: str | Path):
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "bundle.md").write_text(self.markdown)
        (out / "selection.json").write_text(json.dumps({
            "prompt": self.prompt,
            "procedural_signature": self.procedural_signature,
            "reasoning": self.reasoning,
            "examples": self.examples,
            "workflow_docs": self.workflow_docs,
            "lessons": self.lessons,
        }, indent=2))
        return out / "bundle.md"


class TraceRetriever:
    def __init__(self, catalog: KnowledgeCatalog | None = None, model_name: str = "gpt-5"):
        self.catalog = catalog or KnowledgeCatalog()
        self._model_name = model_name
        self._selector = None  # lazy: catalog browsing must work offline

    def _get_selector(self):
        if self._selector is None:
            from sceneprogllm import LLM
            # text mode + self-parsed JSON: sceneprogllm's json mode only
            # supports scalar values, and the selection is mostly lists
            self._selector = LLM(
                system_desc=_SELECTOR_SYSTEM,
                response_format="text",
                model_name=self._model_name,
            )
        return self._selector

    @staticmethod
    def _parse_json(text: str) -> dict:
        text = str(text).strip()
        fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
        if fence:
            text = fence.group(1)
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"selector returned no JSON object: {text[:200]!r}")
        return json.loads(text[start:end + 1])

    # ------------------------------------------------------------------

    def _clean_ids(self, values, kind: str) -> list[str]:
        """Normalize selector output to existing card ids of the right kind."""
        out = []
        for v in values or []:
            v = str(v).strip().strip("`")
            if ":" not in v:
                v = f"{kind}:{v}"
            card = self.catalog.by_id(v)
            if card and card.kind == kind and v not in out:
                out.append(v)
        return out

    def select(self, prompt: str, plan: str | None = None) -> dict:
        """Run the reasoning selection; returns the raw normalized selection."""
        query = f"User prompt: {prompt}\n"
        if plan:
            query += f"\nDesign brief from the planner:\n{plan}\n"
        query += f"\n{self.catalog.listing()}\n"
        raw = self._get_selector()(query)
        if not isinstance(raw, dict):
            raw = self._parse_json(raw)
        primary = self._clean_ids(raw.get("primary_examples"), "example")
        secondary = self._clean_ids(raw.get("secondary_examples"), "example")
        examples = (primary + [e for e in secondary if e not in primary])[:3]

        # Lessons: drop core-flagged picks (their doc is in every bundle anyway),
        # then GRAPH-EXPAND — a selected example's [[wiki]]-linked lessons come
        # along automatically; that link was written because the lesson fires there.
        lessons = [l for l in self._clean_ids(raw.get("lessons"), "lesson")
                   if not (self.catalog.by_id(l).extras or {}).get("core")]
        for ex in examples:
            for e in self.catalog.links(ex, "wiki"):
                dst = self.catalog.by_id(e.dst)
                if dst and dst.kind == "lesson" and not dst.extras.get("core") \
                        and e.dst not in lessons:
                    lessons.append(e.dst)

        return {
            "procedural_signature": str(raw.get("procedural_signature", "")).strip(),
            "reasoning": str(raw.get("reasoning", "")).strip(),
            "examples": examples,
            "workflow_docs": self._clean_ids(raw.get("workflow_docs"), "workflow"),
            "lessons": lessons,
        }

    def retrieve(self, prompt: str, plan: str | None = None,
                 include_programs: bool = True) -> ContextBundle:
        sel = self.select(prompt, plan)
        md = self._assemble(prompt, plan, sel, include_programs)
        return ContextBundle(
            prompt=prompt, plan=plan,
            procedural_signature=sel["procedural_signature"],
            reasoning=sel["reasoning"],
            core_docs=list(CORE_DOCS),
            examples=sel["examples"],
            workflow_docs=sel["workflow_docs"],
            lessons=sel["lessons"],
            markdown=md, selection=sel,
        )

    def _assemble(self, prompt: str, plan: str | None, sel: dict,
                  include_programs: bool) -> str:
        parts = [
            "# Scene-generation context bundle",
            f"\n## Task\nUser prompt: {prompt}",
        ]
        if plan:
            parts.append(f"\n## Design brief (planner)\n{plan}")
        parts.append(f"\n## Procedural signature\n{sel['procedural_signature']}")
        parts.append(f"\n## Why these traces\n{sel['reasoning']}")

        parts.append("\n# Core references (always included)")
        for rel in CORE_DOCS:
            _, body = _parse_frontmatter(_read(rel))
            parts.append(f"\n### {rel}\n{body}")

        if sel["examples"]:
            parts.append("\n# Matched example recipes (copy the closest skeleton, don't start from scratch)")
            for cid in sel["examples"]:
                card = self.catalog.by_id(cid)
                parts.append("\n" + self.catalog.card_text(card, include_program=include_programs))

        if sel["workflow_docs"]:
            parts.append("\n# Workflow guides")
            for cid in sel["workflow_docs"]:
                card = self.catalog.by_id(cid)
                parts.append("\n" + self.catalog.card_text(card))

        if sel["lessons"]:
            parts.append("\n# Lessons likely to fire on this scene")
            for cid in sel["lessons"]:
                card = self.catalog.by_id(cid)
                parts.append(f"\n- **{card.title}**\n{card.body or ''}")

        return "\n".join(parts)
