"""Per-run workspaces — one self-contained directory per generated scene.

Before this, a run's artifacts scattered: the plan under ``tmp/plan_<slug>`` (keyed by
prompt, so two agents on the same prompt collided), the retrieval bundle under
``tmp/<run>/ctx``, each build in its own ``tmp/<run>``, the flow's state under
``tmp/flows/<id>``, and the exported .blend wherever the program's ``scene.export``
pointed — usually the shared repo root. Nothing tied them together, and concurrent
agents overwrote each other's files.

A workspace fixes both problems at once. Every run gets

    runs/<timestamp>_<slug>/
        meta.json        prompt, id, created, git sha
        WORKFLOW.md      what the agent actually did, written at the end
        program.py       the final program
        plan/            plan.png, skill.txt, retrieved.json
        ctx/             the retrieved workflow bundle
        build/           per-build report.json + feedback.txt
        renders/         room views / VLM strips
        blends/          exported .blend files

and builds execute with the workspace as their working directory, so cwd-relative
exports land inside it instead of in the repo root. N agents can then run N scenes
concurrently without touching each other's files, and every run is reviewable on its
own afterwards.

Root defaults to <repo>/runs; override with IDSDL_RUNS_ROOT (e.g. a scratch disk).
"""
import json
import os
import re
import shutil
import subprocess
import time

from IDSDL.service.core import REPO_ROOT

SUBDIRS = ("plan", "ctx", "build", "renders", "blends")


def runs_root():
    return os.environ.get("IDSDL_RUNS_ROOT") or os.path.join(REPO_ROOT, "runs")


def _slug(text, max_len=40):
    s = re.sub(r"[^a-z0-9]+", "_", (text or "run").lower()).strip("_")
    return s[:max_len] or "run"


def _git_sha():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def new_run(prompt, root=None, agent=None):
    """Create and return a fresh workspace for `prompt`.

    The timestamp prefix keeps runs sorted and unique; a counter suffix guards the
    case of two agents starting the same prompt within the same second.
    """
    base = root or runs_root()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(base, f"{stamp}_{_slug(prompt)}")
    n = 1
    while os.path.exists(path):
        n += 1
        path = os.path.join(base, f"{stamp}_{_slug(prompt)}_{n}")
    for d in SUBDIRS:
        os.makedirs(os.path.join(path, d), exist_ok=True)
    meta = {"id": os.path.basename(path), "prompt": prompt, "agent": agent or "",
            "created": time.strftime("%Y-%m-%d %H:%M:%S"), "git": _git_sha()}
    with open(os.path.join(path, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    return path


def latest_run(root=None):
    base = root or runs_root()
    if not os.path.isdir(base):
        return None
    runs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
    # Sort by NAME, not mtime: names carry a zero-padded creation timestamp, whereas
    # mtime makes whichever run was last *written into* look like the newest — so
    # adopting a build into an earlier run would hijack "latest".
    return os.path.join(base, max(runs)) if runs else None


def sub(ws, name):
    p = os.path.join(ws, name)
    os.makedirs(p, exist_ok=True)
    return p


def adopt_build(ws, result):
    """Pull a `core.run_scene` result's artifacts into the workspace.

    Copies rather than moves: the original tmp/<run> stays valid for anything already
    holding those paths (the flow's evidence checks, an agent's earlier tool result).
    """
    landed = {"report": None, "renders": [], "blends": []}
    run_dir = result.get("run_dir")
    if run_dir:
        src = run_dir if os.path.isabs(run_dir) else os.path.join(REPO_ROOT, run_dir)
        tag = os.path.basename(src.rstrip("/")) or "build"
        dst = sub(ws, os.path.join("build", tag))
        for name in ("report.json", "feedback.txt"):
            s = os.path.join(src, name)
            if os.path.exists(s):
                shutil.copy2(s, os.path.join(dst, name))
                if name == "report.json":
                    landed["report"] = os.path.join(dst, name)
    for png in result.get("room_views") or []:
        if os.path.exists(png):
            d = os.path.join(sub(ws, "renders"), os.path.basename(png))
            shutil.copy2(png, d)
            landed["renders"].append(d)
    blend = (result.get("report") or {}).get("blend") or (result.get("report") or {}).get("export")
    if blend:
        b = blend if os.path.isabs(blend) else os.path.join(REPO_ROOT, blend)
        if os.path.exists(b):
            d = os.path.join(sub(ws, "blends"), os.path.basename(b))
            shutil.copy2(b, d)
            landed["blends"].append(d)
    return landed


def write_summary(ws, steps=None, notes=None):
    """Write WORKFLOW.md — what this run did, in the order it happened.

    `steps` is a list of {step, detail, evidence} dicts (the flow's trace maps onto
    this directly); `notes` is free text appended at the end.
    """
    meta = {}
    mp = os.path.join(ws, "meta.json")
    if os.path.exists(mp):
        meta = json.load(open(mp))

    def _n(d):
        p = os.path.join(ws, d)
        return len(os.listdir(p)) if os.path.isdir(p) else 0

    lines = [f"# {meta.get('prompt') or os.path.basename(ws)}", ""]
    lines += [f"- **run** `{meta.get('id', os.path.basename(ws))}`",
              f"- **started** {meta.get('created', '')}",
              f"- **code** `{meta.get('git', '')}`" if meta.get("git") else "",
              ""]
    if steps:
        lines += ["## What happened", ""]
        for i, s in enumerate(steps, 1):
            lines.append(f"{i}. **{s.get('step', '?')}** — {s.get('detail', '')}".rstrip())
            ev = s.get("evidence")
            if ev:
                lines.append(f"   - evidence: `{ev}`")
        lines.append("")
    lines += ["## Artifacts", "",
              f"- program: `program.py`" if os.path.exists(os.path.join(ws, "program.py"))
              else "- program: *(not captured)*",
              f"- plan: {_n('plan')} file(s) in `plan/`",
              f"- retrieved workflows: {_n('ctx')} file(s) in `ctx/`",
              f"- builds: {_n('build')} in `build/`",
              f"- renders: {_n('renders')} in `renders/`",
              f"- blends: {_n('blends')} in `blends/`", ""]
    if notes:
        lines += ["## Notes", "", notes, ""]
    out = os.path.join(ws, "WORKFLOW.md")
    with open(out, "w") as f:
        f.write("\n".join(l for l in lines if l is not None))
    return out
