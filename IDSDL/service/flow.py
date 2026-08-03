"""Guided scene-generation flow — the worked-example recipe as a server-side state machine.

Two modes. INFERENCE (default): 8 gates ending at the judged, converged .blend —
skills/ is read-only, the run leaves no trace in the knowledge base. TEACH
(flow_start(prompt, teach=True), or IDSDL_TEACH=1): a 9th WRITE BACK gate
distills the scene into skills/ to grow the library.

Any agent connected to the MCP server can build a scene the way the 26 worked
examples were built, without having read the repo: ``flow_start(prompt)`` returns
step 1's card (what to do, the exact commands, what evidence to bring back);
``flow_advance(flow_id, evidence)`` validates the evidence MECHANICALLY where
possible (files exist, lint clean, fresh phase-N report, no unresolved lint/
warning lines) and only then reveals the next step. ``flow_override`` records a
deliberate exception and advances anyway — gates guide, they don't imprison, but
every override is written into the provenance trace.

State is file-backed (tmp/flows/<flow_id>/state.json): a disconnected agent —
or a different agent — resumes exactly where the flow stopped.
"""
import json
import os
import re
import time
import uuid

from IDSDL.service.core import REPO_ROOT

_FLOWS_DIR = os.path.join(REPO_ROOT, "tmp", "flows")

# lines in vlm_feedback that block a build gate until fixed or overridden
_BLOCKING = re.compile(r"\[Lint\]|WARNING", re.IGNORECASE)


# ---------------------------------------------------------------------------
# the nine steps
# ---------------------------------------------------------------------------

STEPS = [
    {
        "key": "plan",
        "title": "PLAN — get the design target",
        "card": """Produce the design plan for the prompt.
  Command : (from the repo root) PYTHONPATH=. python -m planner_core "<prompt>" --out tmp/<run>/plan
  (or the MCP `plan` tool)
Read skill.txt and look at plan.png: extract anchors, secondary items, wall/decor,
palette, lighting mood. The plan image is the target every later judgement
compares against.
EVIDENCE: {"plan_dir": "<dir containing skill.txt (+ plan.png)>"}""",
    },
    {
        "key": "retrieve",
        "title": "RETRIEVE — reason over the knowledge catalog",
        "card": """Retrieve procedurally-similar recipes/lessons (NOT by category name).
  Command : (from the repo root) PYTHONPATH=. python -m retriever_core "<prompt>" --plan <plan_dir>/skill.txt --out tmp/<run>/ctx
  (or the MCP `retrieve_context` tool)
Then READ the returned bundle.md IN FULL — matched recipes, their programs, and
the atomic lessons selected for this scene.
EVIDENCE: {"bundle": "<path to bundle.md>"}""",
    },
    {
        "key": "audit",
        "title": "AUDIT ASSETS — eyeball before placements",
        "card": """Resolve your shopping list BEFORE writing placements and eyeball every mesh
you pin (caption != mesh; this is the #1 late-caught failure class).
  Commands: workbench inspect "<query>"  (candidates + previews)
            workbench browse "<query>"   (montage)
  (or the MCP `inspect` / `browse` / `show` tools)
Verify the category's IDENTITY props exist (the pastries, the gems...). If a key
fixture is missing, mass the product instead of shipping an empty fixture.
EVIDENCE: {"pins": {"<ROLE>": "<dataset/id>", ...},
           "previews_eyeballed": true,
           "notes": "<missing assets + what you substituted>"}""",
    },
    {
        "key": "author",
        "title": "AUTHOR — write the PHASE-GATED program",
        "card": """Write the scene program following the matched recipe's skeleton, gated on
IDSDL/phases.py (see skills/examples/coffee_shop_v1.py for the canonical form):
  PHASE 1: floor anchors, composed stations, doors, the RoomGroup shell
  PHASE 2: place_on_top / place_inside dressing
  PHASE 3: wall art, windows, lighting, mood
Hard rules (violated most often): room size is a CONSEQUENCE — few floor slots,
modest hero widths, never modulate_scale>1.0 to dodge overlaps; product at
viewing height; wall-hung = flat only (<0.25 m deep); add_lighting density
0.01-0.02 small room. Lint it yourself first:
  Command : workbench lint <program>.py   (or the MCP `lint_program` tool)
EVIDENCE: {"program": "<path to program .py>"}  (gate re-lints it)""",
    },
    {
        "key": "build1",
        "title": "BUILD PHASE 1 — verify the floor layout (~1 min)",
        "card": """Build ONLY the anchors and check the layout before anything expensive:
  Command : workbench run <program>.py --phase 1
  (or the MCP `run_scene` tool with phase=1)
Look at the strip: room size right? overlaps? clearances working? orientation?
Fix and rebuild phase 1 until clean — this loop is cheap, use it.
EVIDENCE: {"run_dir": "<tmp/<run> of the accepted phase-1 build>"}  ("latest" works)
Gate: fresh report with phase=1 and NO [Lint]/WARNING lines (or override).""",
    },
    {
        "key": "build2",
        "title": "BUILD PHASE 2 — dress the surfaces",
        "card": """Add the place_on_top / place_inside layer on the verified layout:
  Command : workbench run <program>.py --phase 2
Check the strip: product at viewing height, stocked shelves, nothing floating,
items sized to their surfaces.
EVIDENCE: {"run_dir": "<tmp/<run> of the accepted phase-2 build>"}  ("latest" works)
Gate: fresh report with phase=2 and NO [Lint]/WARNING lines (or override).""",
    },
    {
        "key": "build3",
        "title": "BUILD PHASE 3 — walls, lighting, mood + converge",
        "card": """Full build; then apply the vlm_feedback playbook (render is the arbiter, ONE
decisive change per iteration, converge don't chase):
  Command : workbench run <program>.py
If exactly one object floats while neighbours rest, interrogate the exported
blend (bottom = loc_z - dims_z/2): off-center mesh origin means SWAP the mesh.
EVIDENCE: {"run_dir": "<tmp/<run> of the CONVERGED full build>"}  ("latest" works)
Gate: fresh report with phase=3 and NO [Lint]/WARNING lines (or override).""",
    },
    {
        "key": "judge",
        "title": "JUDGE — against the plan, then the vibe layer",
        "card": """Compare the strip to plan.png: does it instantly read as the category? Are the
plan's identity elements present? Then add the VIBE layer (stocked shelves, menu/
signage, one warm accent seat, warm envelope, greenery — see
skills/examples/coffee_shop.md) and rebuild if you added anything.
The VLM loop converging is necessary, NOT sufficient — gut-check legibility
yourself, as a human would.
EVIDENCE: {"score": <0-10 your honest design-match score>,
           "legible": true,
           "notes": "<what carries the category; what you added for vibe>"}""",
    },
    {
        "key": "writeback",
        "title": "WRITE BACK — grow the knowledge base",
        "card": """Distill what you learned so the next scene benefits:
  - skills/examples/<name>.md   (recipe: layout idea, gotchas, feedback log)
    START IT WITH FRONTMATTER (id/kind/family/category/pattern) — the catalog
    reads the frontmatter, see any sibling example for the shape
  - skills/examples/<name>_v1.py (the converged program, beside it)
  - add a one-line row to skills/examples/README.md (the human index)
  - append feedback->action entries to skills/workflow/vlm_feedback.md,
    each with a unique `{#vlm-<scene>-<topic>}` anchor after the bold prefix
EVIDENCE: {"example_md": "<path>", "program_copy": "<path>"}""",
    },
]

_STEP_INDEX = {s["key"]: i for i, s in enumerate(STEPS)}


def _steps(state):
    """The step list for this flow's mode. INFERENCE (default) stops at the
    converged, judged build — skills/ is read-only, nothing is written back.
    TEACH mode appends the WRITE BACK gate that grows the knowledge base."""
    return STEPS if state.get("teach", True) else STEPS[:-1]


def _title(state, i):
    steps = _steps(state)
    return f"{i + 1}/{len(steps)} {steps[i]['title']}"


# ---------------------------------------------------------------------------
# state persistence
# ---------------------------------------------------------------------------

def _flow_path(flow_id):
    return os.path.join(_FLOWS_DIR, flow_id, "state.json")


def _load(flow_id):
    path = _flow_path(flow_id)
    if not os.path.isfile(path):
        raise KeyError(f"no such flow: {flow_id} (flow_start creates one; "
                       f"existing: {sorted(os.listdir(_FLOWS_DIR)) if os.path.isdir(_FLOWS_DIR) else []})")
    with open(path) as f:
        return json.load(f)


def _save(state):
    d = os.path.join(_FLOWS_DIR, state["flow_id"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "state.json"), "w") as f:
        json.dump(state, f, indent=2)


def _card(state):
    steps = _steps(state)
    i = state["current"]
    if i >= len(steps):
        run = (state.get("context") or {}).get("run_build3", "")
        where = f"\nConverged build (scene.blend + strip): {run}" if run else ""
        tail = ("" if state.get("teach", True) else
                "\n(Inference mode: the knowledge write-back gate was skipped — skills/ "
                "stays untouched.\n If this scene is worth adding to the library, re-run "
                "with flow_start(prompt, teach=true).)")
        return (f"FLOW COMPLETE — all {len(steps)} gates passed for: {state['prompt']!r}{where}\n"
                f"Provenance: {_flow_path(state['flow_id'])}{tail}")
    step = steps[i]
    lines = [f"flow {state['flow_id']} — step {_title(state, i)}",
             f"prompt: {state['prompt']!r}", ""]
    # step-scoped context gathered from earlier evidence
    ctx = state.get("context", {})
    if ctx.get("plan_dir") and step["key"] != "plan":
        lines.append(f"your plan   : {ctx['plan_dir']} (keep plan.png open)")
    if ctx.get("bundle") and step["key"] not in ("plan", "retrieve"):
        lines.append(f"your bundle : {ctx['bundle']} (the retrieved recipes/lessons)")
    if ctx.get("program") and _STEP_INDEX[step["key"]] > _STEP_INDEX["author"]:
        lines.append(f"your program: {ctx['program']}")
    if len(lines) > 3:
        lines.append("")
    lines.append(step["card"])
    lines.append("")
    lines.append("Submit evidence with: flow_advance(flow_id, evidence) — or "
                 "flow_override(flow_id, reason) to pass this gate deliberately.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gate validation — mechanical wherever possible
# ---------------------------------------------------------------------------

def _fresh_report(run_dir, since):
    """Load run_dir/report.json, requiring it newer than the step's start."""
    rp = os.path.join(REPO_ROOT, run_dir) if not os.path.isabs(run_dir) else run_dir
    rp = os.path.join(rp, "report.json")
    if not os.path.isfile(rp):
        return None, f"no report.json under {run_dir} (was it a `workbench run`?)"
    if os.path.getmtime(rp) < since:
        return None, (f"{rp} predates this step — submit a build made AFTER the "
                      f"step started (stale evidence is the oldest trick)")
    with open(rp) as f:
        return json.load(f), None


def _validate(step_key, evidence, state):
    """Return a list of failure strings (empty = gate passes)."""
    ev = evidence or {}
    errs = []
    since = state["step_started"]

    if step_key == "plan":
        d = ev.get("plan_dir", "")
        if not d or not os.path.isfile(os.path.join(d, "skill.txt")):
            errs.append(f"plan_dir must contain skill.txt (got {d!r})")

    elif step_key == "retrieve":
        b = ev.get("bundle", "")
        if not b or not os.path.isfile(b):
            errs.append(f"bundle path does not exist: {b!r}")
        elif os.path.getsize(b) < 1000:
            errs.append(f"{b} is suspiciously small — did retrieval fail?")

    elif step_key == "audit":
        pins = ev.get("pins") or {}
        if not isinstance(pins, dict) or not pins:
            errs.append("pins must be a non-empty {ROLE: dataset/id} mapping")
        if ev.get("previews_eyeballed") is not True:
            errs.append("previews_eyeballed must be true — eyeball EVERY pinned "
                        "mesh preview first (caption != mesh)")

    elif step_key == "author":
        p = ev.get("program", "")
        if not p or not os.path.isfile(p):
            errs.append(f"program path does not exist: {p!r}")
        else:
            from IDSDL.lints import lint_program_file
            lint = lint_program_file(p)
            errs.extend(f"lint: {e}" for e in lint)
            src = open(p).read()
            if "current_phase" not in src:
                errs.append("program is not phase-gated (import "
                            "IDSDL.phases.current_phase and gate phases 2/3) — "
                            "the next three gates build it phase by phase")

    elif step_key in ("build1", "build2", "build3"):
        want = {"build1": 1, "build2": 2, "build3": 3}[step_key]
        run_dir = ev.get("run_dir", "")
        if run_dir == "latest":
            # convenience: resolve the newest run — the freshness check below
            # still guarantees it was built after this step started
            import glob as _glob
            reports = sorted(_glob.glob(os.path.join(REPO_ROOT, "tmp", "*", "report.json")),
                             key=os.path.getmtime, reverse=True)
            run_dir = os.path.dirname(reports[0]) if reports else ""
            ev["run_dir"] = run_dir   # record the resolved dir in provenance
        if not run_dir:
            errs.append('run_dir required ("latest" resolves the newest run)')
        else:
            report, err = _fresh_report(run_dir, since)
            if err:
                errs.append(err)
            else:
                got = report.get("phase")
                if got != want:
                    errs.append(f"report says phase={got}, this gate needs a "
                                f"phase-{want} build (workbench run --phase {want})")
                fb = report.get("vlm_feedback", "") or ""
                blocking = [l for l in fb.splitlines() if _BLOCKING.search(l)]
                if blocking:
                    errs.append("build has unresolved lint/warning lines — fix "
                                "them (or flow_override with your reasoning):\n  "
                                + "\n  ".join(blocking[:6]))

    elif step_key == "judge":
        if not isinstance(ev.get("score"), (int, float)):
            errs.append("score (0-10, your honest design-match number) required")
        if ev.get("legible") is not True:
            errs.append("legible must be true — the human gut-check ('does it "
                        "instantly read as the category?') is the gate")
        if not (ev.get("notes") or "").strip():
            errs.append("notes required: what carries the category + vibe additions")

    elif step_key == "writeback":
        md, py = ev.get("example_md", ""), ev.get("program_copy", "")
        if not md or not os.path.isfile(md):
            errs.append(f"example_md does not exist: {md!r}")
        if not py or not os.path.isfile(py):
            errs.append(f"program_copy does not exist: {py!r}")
        readme = os.path.join(REPO_ROOT, "skills", "examples", "README.md")
        if md and os.path.isfile(md):
            if not open(md).read().startswith("---\n"):
                errs.append(f"{md} has no frontmatter — start it with "
                            "'---\\nid: example:<name>\\nkind: example\\n...' "
                            "(the catalog reads the frontmatter; copy a sibling's shape)")
            if os.path.isfile(readme):
                stem = os.path.splitext(os.path.basename(md))[0]
                if stem not in open(readme).read():
                    errs.append(f"add a '{stem}' row to skills/examples/README.md "
                                f"(the human index)")

    return errs


def _absorb_context(state, step_key, evidence):
    """Carry useful evidence forward into later step cards."""
    ctx = state.setdefault("context", {})
    for k in ("plan_dir", "bundle", "program", "run_dir"):
        if evidence.get(k):
            ctx[k if k != "run_dir" else f"run_{step_key}"] = evidence[k]


# ---------------------------------------------------------------------------
# public API (wrapped by the MCP tools)
# ---------------------------------------------------------------------------

def flow_start(prompt, teach=False):
    """teach=False (INFERENCE, the default) runs the 8 gates that end at the
    judged .blend and never touches skills/. teach=True (or IDSDL_TEACH=1 in
    the environment) adds the 9th WRITE BACK gate that grows the knowledge
    base — use it when a scene is being built TO teach the library."""
    teach = bool(teach) or os.environ.get("IDSDL_TEACH", "") == "1"
    flow_id = f"flow_{time.strftime('%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    state = {"flow_id": flow_id, "prompt": prompt, "created": time.time(),
             "teach": teach, "current": 0, "step_started": time.time(),
             "history": [], "context": {}}
    _save(state)
    return _card(state)


def flow_status(flow_id):
    state = _load(flow_id)
    done = [f"  [x] {_title(state, h['step_index'])}"
            + (f"  (OVERRIDDEN: {h['override']})" if h.get("override") else "")
            for h in state["history"]]
    return ("\n".join(done) + ("\n" if done else "")) + "\n" + _card(state)


def flow_advance(flow_id, evidence):
    state = _load(flow_id)
    if state["current"] >= len(_steps(state)):
        return _card(state)
    step = _steps(state)[state["current"]]
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except json.JSONDecodeError:
            return ("evidence must be a JSON object — see the EVIDENCE line of "
                    "the step card:\n\n" + _card(state))
    errs = _validate(step["key"], evidence, state)
    if errs:
        return (f"GATE NOT PASSED — {step['title']}:\n"
                + "\n".join(f"  - {e}" for e in errs)
                + "\n\nFix and re-submit, or flow_override(flow_id, reason) if "
                  "you are deliberately deviating.")
    state["history"].append({"step_index": state["current"], "step": step["key"],
                             "evidence": evidence, "ts": time.time()})
    _absorb_context(state, step["key"], evidence)
    state["current"] += 1
    state["step_started"] = time.time()
    _save(state)
    return "GATE PASSED.\n\n" + _card(state)


def flow_override(flow_id, reason):
    state = _load(flow_id)
    if state["current"] >= len(_steps(state)):
        return _card(state)
    if not (reason or "").strip():
        return "an override needs a real reason — it is recorded in provenance."
    step = _steps(state)[state["current"]]
    state["history"].append({"step_index": state["current"], "step": step["key"],
                             "evidence": None, "override": reason,
                             "ts": time.time()})
    state["current"] += 1
    state["step_started"] = time.time()
    _save(state)
    return f"OVERRIDE RECORDED for {step['key']} ({reason!r}).\n\n" + _card(state)


def howto():
    """Orientation card for a fresh agent connecting to the server."""
    inference = STEPS[:-1]
    steps = "\n".join(f"  {n + 1}/{len(inference)} {s['title']}"
                      for n, s in enumerate(inference))
    return f"""InteriorAgent — text -> 3D interior scene, as a guided flow.

This server wraps a Python DSL (IDSDL) that compiles declarative scene programs
into solved, rendered Blender rooms. The best scenes come from a specific
recipe distilled from 55+ worked examples: plan first, retrieve tacit knowledge,
eyeball assets BEFORE placements, then build in verified phases — never write
the whole scene and hope.

START: flow_start("<your scene prompt>") and follow the cards. The gates:
{steps}

TWO MODES. The default is INFERENCE: the flow ends at the judged .blend and the
knowledge library (skills/) is READ-ONLY — do not add or edit files there.
TEACH mode — flow_start(prompt, teach=true), or IDSDL_TEACH=1 — appends a final
WRITE BACK gate ({len(STEPS)}/{len(STEPS)}) that distills the scene into skills/
to grow the library. Only use it when that is the explicit goal of the run.

Each gate validates your evidence mechanically (files, lint, fresh phase-N
reports, no unresolved warnings) before revealing the next card. Deviate
deliberately with flow_override (recorded in provenance). Resume anytime with
flow_status(flow_id) — state survives disconnects.

Key tools while inside the flow: plan, retrieve_context, inspect/browse/show
(asset audit), lint_program (instant API check), run_scene (build; phase=1 for
the cheap layout check). One-command automatic mode instead: generate_scene_start.
The DSL reference: skills/dsl_reference.md (repo root)."""
