"""HELP.md — the pipeline's way of asking for help, and reading the answer back.

Deliberately the same shape as `tools/review_board.py`: a generated markdown file with one
section per asset, each ending in a block the user edits in place. Regenerating never destroys an
answer already written. The only difference is that a scene review block is free prose, while
this one has four fields the pipeline actually parses — because the answer here has to drive
Blender, not a human.

    python -m IDSDL.shop board shops/<batch>             # (re)generate HELP.md
    python -m IDSDL.shop board shops/<batch> --pending   # what is still unanswered
    python -m IDSDL.shop apply shops/<batch>             # act on the answers

An asset lands here for one of two very different reasons, and the board says which:
  * ASK   — the VLM was not confident (front ambiguous, size a guess). A human glance settles it.
  * SKIP  — mechanically unusable (several objects in one file, not an interior object, broken
            geometry). Listed so nothing disappears silently: override it if we were wrong.
"""
import json
import re
from pathlib import Path

ANSWER_HEADER = "#### Your call — edit the block below"
TEMPLATE = """```
action: {action}
front:  {front}
size:   {size}
anchor: {anchor}
```"""


def asset_dirs(batch: Path):
    return sorted(d for d in batch.iterdir() if d.is_dir() and (d / "meta.json").exists())


def load(d: Path):
    return json.loads((d / "meta.json").read_text())


def save(d: Path, meta):
    (d / "meta.json").write_text(json.dumps(meta, indent=1))


def _parse_block(body):
    """Pull the answer out of a section body. Lenient on purpose — a human typing `size: 1.2m` or
    `ACTION: Drop` in a hurry should still parse."""
    m = re.search(r"```(.*?)```", body, flags=re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.split("#")[0].strip()
        if k in ("action", "front", "size", "anchor") and v:
            out[k] = v
    return out


def read_answers(batch: Path):
    """{key: answer_dict} for every section whose block has been changed from the default."""
    help_md = batch / "HELP.md"
    if not help_md.exists():
        return {}
    text = help_md.read_text()
    out = {}
    for m in re.finditer(r"<!-- asset:(?P<key>[^>]+?) -->(?P<body>.*?)(?=\n## |\Z)", text, flags=re.S):
        a = _parse_block(m.group("body"))
        if not a:
            continue
        act = a.get("action", "").lower()
        # An UNTOUCHED block still reads `action: accept | drop` — the menu, not a choice. Treat
        # any leftover alternation (or a `?`) as unanswered, or `apply` will happily "act on" every
        # asset the user has not looked at yet.
        if not act or "|" in act or act.startswith("?"):
            continue
        out[m.group("key").strip()] = a
    return out


def parse_answer(a, meta):
    """Answer -> (action, plan). Falls back to whatever the VLM proposed for any field the user
    left alone, so 'accept' with nothing else typed means 'your guess was right'."""
    from IDSDL.shop.triage import PANELS

    action = a.get("action", "accept").strip().lower()
    if action.startswith("d"):
        return "drop", {}
    plan = dict(meta.get("plan") or {})
    if a.get("front"):
        m = re.search(r"[1-4]", a["front"])
        if m:
            p = int(m.group(0))
            plan["front_panel"] = p
            plan["rot_deg"] = [0.0, 0.0, PANELS[p][1]]
    if a.get("size"):
        m = re.search(r"[\d.]+", a["size"])
        if m:
            plan["scale_size"] = float(m.group(0))
    if a.get("anchor"):
        plan["scale_axis"] = "x" if a["anchor"].strip().lower().startswith("w") else "z"
    if not plan.get("scale_size") or not plan.get("rot_deg"):
        return "incomplete", plan
    return "accept", plan


def generate(batch: Path):
    kept = read_answers(batch)
    metas = [load(d) for d in asset_dirs(batch)]
    need = [m for m in metas if m["status"] in ("ask", "skip", "failed")]
    done = [m for m in metas if m["status"] == "ingested"]

    lines = [
        f"# Asset shop — {batch.name}",
        "",
        f"**{len(done)} ingested automatically. {len(need)} need you.**",
        "",
        "Each section below shows the four straight-on views (panels 1-4, captioned) and the hero",
        "view. To settle one, edit its block: `action: accept` (with the front panel number and the",
        "real-world size) or `action: drop`. Anything you leave alone keeps the pipeline's own",
        "guess. Then run:",
        "",
        "```bash",
        f"python -m IDSDL.shop apply {batch}",
        "```",
        "",
        "`ASK` = the pipeline was not confident enough to guess. `SKIP` = it judged the file",
        "mechanically unusable (several objects in one file, not an interior object, broken",
        "geometry) — listed anyway so you can overrule it.",
        "",
    ]
    if done:
        lines += ["<details><summary>Ingested automatically (no action needed)</summary>", ""]
        for m in done:
            p = m.get("plan", {})
            lines.append(f"- **{m['key']}** — {m.get('judgment', {}).get('object', '?')} · "
                         f"{p.get('scale_size', '?')} m · `{m.get('asset_id', '?')}`")
        lines += ["", "</details>", ""]

    for i, m in enumerate(need, 1):
        tag = "ASK" if m["status"] == "ask" else ("FAILED" if m["status"] == "failed" else "SKIP")
        j = m.get("judgment") or {}
        p = m.get("plan") or {}
        lines += [
            f"## {i}. {m['key']}  <!-- asset:{m['key']} -->",
            "",
            f"- **Why you:** `{tag}` — {m.get('reason', '?')}",
            f"- **What it looks like:** {j.get('object', '(not analysed)')}",
        ]
        if j.get("concerns"):
            lines.append(f"- **Concerns:** {j['concerns']}")
        if m["candidate"].get("url"):
            lic = m["candidate"].get("license") or "?"
            lines.append(f"- **Source:** [{m['candidate'].get('name', '?')}]"
                         f"({m['candidate']['url']}) · {lic} · {m['candidate'].get('author', '?')}")
        if m.get("dims"):
            d = m["dims"]
            lines.append(f"- **Raw import dims (unscaled):** {d['w_x']} x {d['d_y']} x {d['h_z']}")
        if m.get("needs_download"):
            # Only offer the download route when there is actually a page to send them to: a
            # Meshy candidate that failed on a missing key has no URL, and "open the link" would
            # be pointing at nothing.
            lines.append(f"- **Needs manual download:** open the link above, take the glTF/GLB, "
                         f"and drop it into `{batch}/inbox/` — name it `{m['key']}.glb` to keep "
                         f"its licence and attribution attached."
                         if m["candidate"].get("url") else
                         "- **Needs a key:** this source could not be reached — set its API key in "
                         "`.env` (see skills/acquire-assets/SKILL.md) and re-run.")
        lines += [""]
        if (batch / m["key"] / "strip.png").exists():
            lines += [f"![strip]({m['key']}/strip.png)", ""]
        if (batch / m["key"] / "hero.png").exists():
            lines += [f"<img src=\"{m['key']}/hero.png\" width=\"260\">", ""]
        a = kept.get(m["key"], {})
        lines += [
            ANSWER_HEADER,
            "",
            TEMPLATE.format(
                action=a.get("action", "accept | drop"),
                front=a.get("front", str(p.get("front_panel", "?")) + "   # panel showing the FRONT"),
                size=a.get("size", str(p.get("scale_size", "?")) + "   # metres"),
                anchor=a.get("anchor", p.get("scale_axis") == "x" and "width" or "height"),
            ),
            "",
        ]

    (batch / "HELP.md").write_text("\n".join(lines))
    print(f"wrote {batch / 'HELP.md'} — {len(done)} ingested, {len(need)} need you "
          f"({len(kept)} answer(s) preserved)")


def pending(batch: Path):
    answers = read_answers(batch)
    for d in asset_dirs(batch):
        m = load(d)
        if m["status"] in ("ask", "skip", "failed"):
            print(f"{'ANSWERED' if m['key'] in answers else 'pending ':9s} "
                  f"{m['status']:8s} {m.get('reason', ''):26s} {m['key']}")
