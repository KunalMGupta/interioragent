#!/usr/bin/env python3
"""Assemble a reviewable scene board (REVIEW.md) from a batch of built scenes.

Mechanism (agreed 2026-07-14): batches of scenes for user-facing categories are built under
`reviews/<batch>/`, one subdirectory per scene containing:
    meta.json   — {"title", "category", "brief", "program", "verdict", "notes"?}
    strip.png   — the 4-view interior strip from the scene's final build
This script renders them into `reviews/<batch>/REVIEW.md`, one section per scene with an EMPTY
**Feedback** block. Review flow: Kunal writes feedback directly under each scene's "Feedback"
heading (plain markdown, anything goes), commits or just saves; the next working session runs
`python tools/review_board.py <batch> --pending` to list scenes whose feedback block is still
empty, and works through the non-empty ones -> fixes -> folds durable findings into
skills/examples lessons.

Usage:
    python tools/review_board.py reviews/2026-07-14            # (re)generate REVIEW.md
    python tools/review_board.py reviews/2026-07-14 --pending  # list scenes with no feedback yet

Regeneration PRESERVES any feedback already written: existing "#### Feedback" block contents are
carried over into the regenerated file (keyed by scene directory name).
"""
import json
import re
import sys
from pathlib import Path

FEEDBACK_HEADER = "#### Feedback (Kunal — write anything below this line)"
EMPTY_MARK = "_(no feedback yet)_"


def scene_dirs(batch: Path):
    return sorted(d for d in batch.iterdir() if d.is_dir() and (d / "meta.json").exists())


def existing_feedback(batch: Path):
    """Parse REVIEW.md (if present) -> {scene_dir_name: feedback_text}."""
    review = batch / "REVIEW.md"
    if not review.exists():
        return {}
    text = review.read_text()
    out = {}
    # sections start with '## <n>. <title>  <!-- scene:<dirname> -->'
    for m in re.finditer(r"<!-- scene:(?P<key>[^>]+?) -->(?P<body>.*?)(?=\n## |\Z)",
                         text, flags=re.S):
        body = m.group("body")
        if FEEDBACK_HEADER in body:
            fb = body.split(FEEDBACK_HEADER, 1)[1].strip()
            fb = re.sub(r"^-+\s*$", "", fb, flags=re.M).strip()
            if fb and fb != EMPTY_MARK:
                out[m.group("key").strip()] = fb
    return out


def generate(batch: Path):
    kept = existing_feedback(batch)
    lines = [
        f"# Scene review board — {batch.name}",
        "",
        "One section per scene: the brief it was built to, the build verdict, the 4-view strip,",
        "and a **Feedback** block that is YOURS — write anything under it (looks wrong / wrong",
        "vibe / wrong furniture / approve). A later session collects every non-empty block,",
        "acts on it, and folds the durable findings into `skills/examples/`.",
        "",
    ]
    for i, d in enumerate(scene_dirs(batch), 1):
        meta = json.loads((d / "meta.json").read_text())
        lines += [
            f"## {i}. {meta['title']}  <!-- scene:{d.name} -->",
            "",
            f"- **Category:** {meta.get('category', '?')}",
            f"- **Program:** `{meta.get('program', '?')}`",
            f"- **Build verdict:** {meta.get('verdict', '?')}",
        ]
        if meta.get("notes"):
            lines.append(f"- **Notes:** {meta['notes']}")
        lines += [
            f"- **Brief:** {meta.get('brief', '')}",
            "",
            f"![strip]({d.name}/strip.png)",
            "",
            FEEDBACK_HEADER,
            "",
            kept.get(d.name, EMPTY_MARK),
            "",
        ]
    (batch / "REVIEW.md").write_text("\n".join(lines))
    print(f"wrote {batch / 'REVIEW.md'} ({len(scene_dirs(batch))} scenes, "
          f"{len(kept)} feedback blocks preserved)")


def pending(batch: Path):
    kept = existing_feedback(batch)
    for d in scene_dirs(batch):
        status = "HAS FEEDBACK" if d.name in kept else "pending"
        print(f"{status:12s} {d.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    batch = Path(sys.argv[1])
    if not batch.exists():
        sys.exit(f"no such batch dir: {batch}")
    if "--pending" in sys.argv:
        pending(batch)
    else:
        generate(batch)
