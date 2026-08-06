"""SceneGenerator — the end-to-end text→scene pipeline.

    prompt
      └─ 1. PLAN      planner_core: design brief + reference collage
      └─ 2. RETRIEVE  retriever_core: reasoning-based context bundle (recipes/lessons)
      └─ 3. AUDIT     asset stress test: batch-resolve the shopping list, flag gaps
      └─ 4. AUTHOR    a pluggable Author writes the IDSDL program (one file, 3 phases)
      └─ 5. BUILD     workbench run → room VLM strip + textual VLM feedback
      └─ 6. INNER     Critic (encodes the vlm_feedback playbook) → directives → revise
                      → rebuild, until converged or --max-inner
      └─ 7. OUTER     DesignJudge scores the built room AGAINST THE PLAN (strip vs
                      collage + brief) → gap directives → revise → rebuild,
                      until score ≥ threshold or --max-outer

Every step writes artifacts to the run directory; trace.json records the whole
provenance (signature, selected traces, audit, per-iteration feedback→directives,
judge scores).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .authors import Author, AuthorTask, LLMAuthor

ROOT = Path(__file__).parent.parent

# Condensed from skills/workflow/vlm_feedback.md — the how-to-act policy.
_CRITIC_POLICY = """
You are the build critic for an IDSDL interior scene. You see the interior render
strip (back|front|left|right walls) and the textual VLM feedback from the compile.
Decide whether the build has converged, and if not, emit concrete program directives.

Policy (learned from many builds — follow it):
- The render is the arbiter. Feedback text is a hint, not a command; if the strip
  looks right, decline the suggestion.
- Object rescale: act decisively once (edit modulate_scale/width), not in tiny steps.
  VLM magnitudes are directional, not literal (a suggested 0.5 usually means ~0.8).
- Room rescale: only act if the room genuinely reads empty/cramped in the strip.
  NEVER shrink (modulate_scale < 1.0) a room whose walls are loaded with fixed-size
  runs — that causes overflows; if it feels empty, add furniture instead.
- "OVERLAP ... room is likely TOO SMALL" warnings: prefer REMOVING or SHRINKING the
  colliding furniture (name which items) — especially when the brief wants a small/cozy
  room. Enlarging the room is the last resort; never fight the solver.
- If the room reads cavernous/sparse, the cause is the PLACEMENTS, not the shell: the
  RoomGroup auto-sizes to fit every occupied floor slot, so direct the author to
  consolidate into fewer slots and shrink hero widths — a rescale directive cannot fix
  a footprint that the placements dictate.
- Rotation feedback is a weak smoke alarm: act ONLY if the mis-orientation is visible
  in the strip; place_desk_chair/WorkstationGroup units are correct by construction.
- Wall overlap: move one item to a different wall/slot; don't shrink art to dodge.
- Lighting: a ceiling that reads as a grid/band of fixtures → cut add_lighting density
  DECISIVELY (halve it, or drop room-level lighting entirely and keep only the zone
  pendants; big rooms want ~0.05 or less); giant glowing globes / blown-out white →
  use a flat flush-mount fixture query, never a chandelier/pendant with drop. If the
  same lighting complaint repeats across revisions, the previous cut was too timid —
  give an exact density value.
- Windows render as black voids (no exterior env): prefer place_window_standard; if a
  huge void dominates, shrink the window or stage an object in front of it.
- Converge, don't chase: if feedback oscillates or only trivial suggestions remain
  (a ±5% rescale, a declined rotation), declare converged.

Directives must be concrete, program-level edits ("set RoomGroup modulate_scale=0.85",
"pin the coffee table to a bare-top mesh — current pick has chairs baked in",
"reduce add_lighting density on the room group to 0.08"), not vague advice.

Respond with ONLY a JSON object: {"converged": true/false, "directives": ["..."],
"notes": "<one line on what you saw>"}
"""

_JUDGE_SYSTEM = """
You judge how well a BUILT 3D interior matches its DESIGN TARGET.
Image 1 is the built room: an interior render strip (back|front|left|right walls).
Image 2 (if present) is the design target: a photorealistic reference collage.
You also get the user prompt and the design brief.

Score the build 0-10 against the design intent (NOT against photorealism — the build
is a 3D asset scene and will look CG; judge content, not rendering quality):
- Category legibility: does the room instantly read as what was asked? Product/props
  at viewing height name a shop; empty fixtures don't.
- Completeness: are the brief's anchors, secondary items and decor present?
- Layout & proportions: zones, circulation, furniture sizes, room shape.
- Palette & materials: floor/wall/textile families roughly match the target.
- Composition: does it feel like a designed, finished room (lighting, wall decor)?

Score ≥ 8 means "ship it". List the gaps that most hurt the score as concrete,
buildable directives (add/remove/replace/rescale/re-place items, change textures) —
NOT camera or render-quality notes.

Respond with ONLY a JSON object:
{"score": <float>, "verdict": "<one sentence>", "gaps": ["<directive>", ...]}
"""


def _parse_json_block(text: str) -> dict:
    text = str(text).strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in: {text[:200]!r}")
    return json.loads(text[start:end + 1])


@dataclass
class BuildResult:
    ok: bool
    run_dir: str | None
    feedback: str
    strip: str | None          # the room VLM strip (the critique image)
    renders: list
    stderr_tail: str


class SceneGenerator:
    def __init__(self, author: Author | None = None, model_name: str = "gpt-5",
                 python: str = sys.executable, max_inner: int = 3, max_outer: int = 2,
                 judge_threshold: float = 8.0, stress_test: bool = True,
                 stress_cap: int = 30, plan_top_k: int = 3):
        self.author = author or LLMAuthor(model_name=model_name)
        self.model_name = model_name
        self.python = python
        self.max_inner = max_inner
        self.max_outer = max_outer
        self.judge_threshold = judge_threshold
        self.stress_test = stress_test
        self.stress_cap = stress_cap
        self.plan_top_k = plan_top_k
        self._critic = None
        self._judge = None
        self._lister = None

    # ------------------------------------------------------------------ LLMs

    def _get_critic(self):
        if self._critic is None:
            from sceneprogllm import LLM
            self._critic = LLM(system_desc=_CRITIC_POLICY, response_format="text",
                               model_name=self.model_name)
        return self._critic

    def _get_judge(self):
        if self._judge is None:
            from sceneprogllm import LLM
            self._judge = LLM(system_desc=_JUDGE_SYSTEM, response_format="text",
                              model_name=self.model_name)
        return self._judge

    # ------------------------------------------------------------------ steps

    def _plan(self, prompt: str, out: Path) -> dict:
        from planner_core import InteriorPlanner
        planner = InteriorPlanner(retrieval_top_k=self.plan_top_k, model_name=self.model_name)
        result = planner(prompt)
        plan_png = out / "plan.png"
        result.save(str(plan_png))
        (out / "skill.txt").write_text(result.skill)
        return {"brief": result.skill, "plan_png": str(plan_png)}

    def _retrieve(self, prompt: str, brief: str, out: Path):
        from retriever_core import TraceRetriever
        bundle = TraceRetriever(model_name=self.model_name).retrieve(prompt, plan=brief)
        bundle.save(out)
        return bundle

    def _shopping_list(self, prompt: str, brief: str) -> list[str]:
        from sceneprogllm import LLM
        lister = LLM(
            system_desc="You produce asset shopping lists for a 3D interior scene. "
                        "Each entry is one retrieval query: a specific object with "
                        "style/material/color (e.g. 'a tall dark wood back bar cabinet "
                        "with shelves of liquor bottles'). Anchors first, then secondary "
                        "surface items, then wall/ceiling decor. No room-level entries. "
                        "Only shop for discrete FURNITURE and PROPS the library can hold: "
                        "wall/floor/ceiling FINISHES (paneling, wainscot, brick, tiles, "
                        "backsplashes) are place_walls texture strings, NOT assets; light "
                        "fixtures are add_lighting queries, NOT assets (never LED strips); "
                        "skip architectural trim (foot rails, inlays, cove details) and "
                        "micro-utensils (cutlery, chopsticks, dispensers) — a home-furniture "
                        "dataset will substitute a wrong-kind object at a plausible score. "
                        "Prefer fewer, self-contained pieces (a stocked display cabinet) "
                        "over many tiny parts to assemble.",
            response_format="list", model_name=self.model_name)
        items = lister(f"User prompt: {prompt}\n\nDesign brief:\n{brief}\n\n"
                       f"List the asset queries the scene needs (max {self.stress_cap}).")
        return [str(x).strip() for x in items][: self.stress_cap]

    # Below this similarity a pick is suspect even when the desc sounds plausible.
    # 0.30 let a balcony railing ship as a "foot rail" (0.52) and a wall panel as
    # "floor tiles" (0.46) — the ramen_bar postmortem. Descs at 0.44-0.55 were
    # consistently wrong-kind objects.
    STRESS_WEAK_SIM = 0.45

    def _flag_mismatches(self, results: list[dict]) -> None:
        """One batch LLM pass over the audit table: mark rows where the CHOSEN asset
        is a different KIND of object than the query asked for (a candlestick for
        'chopstick holders'). A similarity number alone never catches these; the
        desc text does. Best-effort — the audit survives without it."""
        try:
            from sceneprogllm import LLM
            judge = LLM(
                system_desc="You audit retrieval results for a 3D asset library. For "
                            "each numbered row (query -> chosen asset description), "
                            "answer whether the chosen asset is fundamentally a "
                            "DIFFERENT KIND of object than the query requested "
                            "(railing for a foot rail, wall panel for floor tiles, "
                            "candlestick for a chopstick holder). Style/color/material "
                            "differences are NOT mismatches. Respond with JSON: "
                            '{"mismatched": "<comma-separated row numbers, e.g. '
                            '\'0, 3, 5\', or \'none\'>"}',
                response_format="json",
                response_params={"mismatched": "str"},
                model_name=self.model_name)
            table = "\n".join(f"{i}. {r['query']!r} -> {r['desc']!r}"
                              for i, r in enumerate(results) if r.get("model"))
            resp = judge(table)
            raw = resp["mismatched"] if isinstance(resp, dict) else resp.mismatched
            for i in {int(x) for x in re.findall(r"\d+", str(raw))}:
                if 0 <= i < len(results):
                    results[i]["mismatch"] = True
        except Exception:
            pass

    def _stress_test(self, queries: list[str], out: Path, log) -> str:
        """Batch-resolve every query against the warm router; audit table à la
        skills/workflow/asset_selection.md (sim | query | chosen desc)."""
        from IDSDL.service import core as svc
        svc.warm()
        results = []
        for i, q in enumerate(queries):
            try:
                d = svc.retrieve(q)
                cands = d.get("candidates") or []
                c = next((c for c in cands if c.get("chosen")), cands[0] if cands else {})
                sim = c.get("similarity") or 0.0
                row = {"query": q, "sim": sim, "model": c.get("model"),
                       "desc": (c.get("desc") or "")[:80],
                       "weak": bool(sim < self.STRESS_WEAK_SIM)}
            except Exception as e:
                row = {"query": q, "sim": 0.0, "model": None,
                       "desc": f"RETRIEVAL ERROR: {e}", "weak": True}
            results.append(row)
            log(f"  [{i+1}/{len(queries)}] {row['sim']:.3f}  {q[:52]:<52}  -> {row['desc']}")
        self._flag_mismatches(results)
        rows = []
        for r in results:
            flag = ""
            if r.get("mismatch"):
                flag = "  << WRONG KIND (the chosen mesh is a different object — reword, pin, or DROP)"
            elif r["weak"]:
                flag = "  << WEAK (reword or pin)"
            rows.append(f"{r['sim']:.3f}  {r['query']:<52}  -> {r['model']}  {r['desc']}{flag}")
        (out / "stress_test.json").write_text(json.dumps(results, indent=2))
        table = "sim    query" + " " * 49 + "-> chosen\n" + "\n".join(rows)
        weak = sum(r["weak"] for r in results)
        bad = sum(bool(r.get("mismatch")) for r in results)
        table += (f"\n\n{len(results) - weak - bad}/{len(results)} resolved cleanly; "
                  f"{weak} weak; {bad} wrong-kind.")
        if bad or weak:
            table += ("\nDo NOT place a WRONG KIND pick as-is: reword the query "
                      "(name the object class, not the room), pin a browsed id, or drop "
                      "the item — a tidy arrangement of wrong objects still reads wrong.")
        return table

    def _lint_gate(self, task, program_src: str, log, max_tries: int = 2) -> str:
        """Static-lint the authored program (IDSDL/lints.py) and have the author fix
        API-surface errors BEFORE any build is attempted — milliseconds instead of a
        failed multi-minute build. Gives up after max_tries (the build then surfaces
        whatever remains; workbench also refuses to run on lint errors)."""
        from IDSDL.lints import lint_program
        for _ in range(max_tries):
            errors = lint_program(program_src)
            if not errors:
                return program_src
            log(f"      lint: {len(errors)} API error(s) — revising without a build")
            for e in errors:
                log(f"        {e}")
            directives = ["Static lint found API errors (no build was attempted). "
                          "Fix exactly these:"] + errors
            program_src = self.author.revise(task, program_src, directives)
        return program_src

    _BLOCKING = re.compile(r"\[Lint\]|WARNING", re.IGNORECASE)

    def _phase_gates(self, task, program_src: str, out: Path, version: int,
                     log, trace, save_trace):
        """Cheap staged validation of a freshly authored program: build phase 1
        (anchors, ~1 min) then phase 2 (surfaces), and have the author fix any
        crash or blocking [Lint]/WARNING findings before the expensive full build
        — layout errors get caught for the price of a phase-1 build instead of a
        full one. One retry per phase; skipped entirely for non-gated programs.
        Returns (program_src, version)."""
        if "current_phase" not in program_src:
            log("      program is not phase-gated — skipping phase gates")
            return program_src, version
        for ph in (1, 2):
            for attempt in (0, 1):
                path = out / f"program_v{version}.py"
                path.write_text(program_src)
                log(f"[5/7] phase-{ph} gate build v{version}...")
                build = self._build(path, out, f"v{version}_p{ph}", log, phase=ph)
                crashed = not build.ok and build.run_dir is None
                blocking = [] if crashed else \
                    [l for l in (build.feedback or "").splitlines()
                     if self._BLOCKING.search(l)]
                trace["iterations"].append(
                    {"version": version, "phase_gate": ph, "ok": build.ok,
                     "run_dir": build.run_dir, "blocking": blocking,
                     "crashed": crashed})
                save_trace()
                if not crashed and not blocking:
                    log(f"      phase-{ph} gate: clean")
                    break
                if attempt == 1:
                    log(f"      phase-{ph} gate still unresolved — proceeding "
                        f"(the full build will surface it)")
                    break
                directives = (
                    [f"The program crashed in a phase-{ph} build. Fix the error:\n"
                     + build.stderr_tail] if crashed else
                    [f"The phase-{ph} layout build produced blocking findings — "
                     f"fix exactly these:"] + blocking)
                log(f"      phase-{ph} gate: "
                    + ("crash" if crashed else f"{len(blocking)} blocking finding(s)")
                    + " — revising...")
                version += 1
                program_src = self.author.revise(
                    task, program_src, directives,
                    images=([build.strip] if build.strip else None))
                program_src = self._lint_gate(task, program_src, log)
        return program_src, version

    def _build(self, program: Path, out: Path, tag: str, log,
               phase: int | None = None) -> BuildResult:
        """Run the program via the workbench in a subprocess; collect the report
        written by THIS run (mtime-newer-than-start, so a failed build can never
        surface another run's report — the run_scene mtime-fallback gotcha).
        `phase` builds a phase-gated program only up to that phase (IDSDL/phases.py)."""
        start = time.time()
        env = {**os.environ, "PYTHONPATH": str(ROOT)}
        cmd = [self.python, str(ROOT / "workbench.py"), "run", str(program)]
        if phase is not None:
            cmd += ["--phase", str(phase)]
        # Build inside THIS run's own directory. Scene programs write a cwd-relative
        # tmp/ and export cwd-relative .blend files, so building from the repo root
        # (a) collides when several runs build concurrently and (b) fails outright
        # when the repo's tmp/ is not writable — which is how five parallel runs
        # each burned their revision budget "fixing" a PermissionError.
        build_cwd = out / "build_cwd"
        build_cwd.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            cmd,
            cwd=build_cwd, env=env, capture_output=True, text=True, timeout=3600,
        )
        (out / f"build_{tag}.log").write_text(
            proc.stdout + "\n--- stderr ---\n" + proc.stderr)

        report, run_dir = None, None
        # Take the run directory this build printed rather than the newest report
        # on disk: with concurrent runs the mtime scan can return another run's
        # report, silently attributing someone else's scene to this build.
        m = re.search(r"run_dir\s*[:=]\s*(tmp/\S+)", proc.stdout + "\n" + proc.stderr)
        if m:
            rp = build_cwd / m.group(1) / "report.json"
            if rp.exists() and rp.stat().st_mtime >= start:
                report = json.loads(rp.read_text())
                run_dir = str(rp.parent)
        if report is None:
            for rp in sorted(build_cwd.glob("tmp/*/report.json"), key=os.path.getmtime,
                             reverse=True):
                if rp.stat().st_mtime >= start:
                    report = json.loads(rp.read_text())
                    run_dir = str(rp.parent)
                    break

        if report is None:
            tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-25:])
            log(f"  build failed (no report). tail:\n{tail}")
            return BuildResult(False, None, "", None, [], tail)

        # report paths are relative to the cwd the build ran in
        renders = [str((build_cwd / r).resolve()) if not os.path.isabs(r) else r
                   for r in report.get("renders", [])]
        strips = [r for r in renders if "vlm_views" in r and "combined" in r]
        strip = max(strips, key=os.path.getmtime) if strips else None
        return BuildResult(
            ok=proc.returncode == 0, run_dir=run_dir,
            feedback=report.get("vlm_feedback", ""), strip=strip,
            renders=renders, stderr_tail="\n".join(proc.stderr.splitlines()[-15:]),
        )

    def _criticize(self, build: BuildResult) -> dict:
        images = [build.strip] if build.strip else None
        raw = self._get_critic()(
            "VLM feedback from the compile:\n"
            + (build.feedback or "(none)")
            + ("\n\n(no render strip available — judge from the text only)"
               if not images else ""),
            image_paths=images)
        d = _parse_json_block(raw)
        return {"converged": bool(d.get("converged")),
                "directives": [str(x) for x in d.get("directives", [])],
                "notes": str(d.get("notes", ""))}

    def _judge_design(self, build: BuildResult, plan_png: str | None,
                      prompt: str, brief: str) -> dict:
        images = [p for p in [build.strip, plan_png] if p]
        raw = self._get_judge()(
            f"User prompt: {prompt}\n\nDesign brief:\n{brief}\n\n"
            "Judge the built room (image 1) against the design target"
            + (" (image 2)." if plan_png else " described by the brief."),
            image_paths=images or None)
        d = _parse_json_block(raw)
        return {"score": float(d.get("score", 0.0)),
                "verdict": str(d.get("verdict", "")),
                "gaps": [str(x) for x in d.get("gaps", [])]}

    # ------------------------------------------------------------------ run

    def run(self, prompt: str, out_dir: str | Path, seed: int = 42,
            scene_name: str | None = None, log=print) -> dict:
        out = Path(out_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        trace: dict = {"prompt": prompt, "seed": seed, "iterations": []}

        def save_trace():
            (out / "trace.json").write_text(json.dumps(trace, indent=2))

        # 1. plan
        log("[1/7] planning (brief + reference collage)...")
        plan = self._plan(prompt, out)
        trace["brief"] = plan["brief"]
        log(f"      design plan: {plan['plan_png']}  (open it — this is the target)")
        save_trace()

        # 2. retrieve
        log("[2/7] retrieving traces (reasoning over the knowledge catalog)...")
        bundle = self._retrieve(prompt, plan["brief"], out)
        trace["procedural_signature"] = bundle.procedural_signature
        trace["retrieved"] = bundle.selection
        log(f"      examples: {bundle.examples}; lessons: {len(bundle.lessons)}")
        save_trace()

        # 3. asset stress test
        audit = ""
        if self.stress_test:
            log("[3/7] asset stress test (batch retrieval audit)...")
            queries = self._shopping_list(prompt, plan["brief"])
            audit = self._stress_test(queries, out, log)
        else:
            log("[3/7] asset stress test skipped (--skip-stress)")
        trace["asset_audit"] = audit
        save_trace()

        # 4. author
        name = scene_name or re.sub(r"[^A-Za-z0-9]+", "", prompt.title())[:24] or "Scene"
        task = AuthorTask(prompt=prompt, brief=plan["brief"],
                          context_md=bundle.markdown, asset_audit=audit,
                          out_blend=str(out / "scene.blend"),
                          scene_name=name, seed=seed)
        plan_png = plan.get("plan_png")
        plan_img = [plan_png] if plan_png and os.path.exists(plan_png) else []

        def revise_images(build):
            return ([build.strip] if build and build.strip else []) + plan_img

        log("[4/7] authoring the scene program (with the plan image)...")
        program_src = self.author.write(task, images=plan_img or None)
        program_src = self._lint_gate(task, program_src, log)
        version = 0

        # Phase gates: validate the floor layout (phase 1, ~1 min) and the surface
        # dressing (phase 2) of the fresh program before any full build — layout
        # errors cost a phase-1 build to catch instead of a full one.
        program_src, version = self._phase_gates(task, program_src, out, version,
                                                 log, trace, save_trace)
        program_path = out / f"program_v{version}.py"
        program_path.write_text(program_src)

        best = {"score": -1.0, "program": None, "build": None}
        outer_reports = []
        # the last build that actually produced a scene + strip, with the program
        # that built it — judging and final artifacts must come from THIS, never
        # from a later revision that crashed before building
        last_good = {"program": None, "build": None}

        for outer in range(self.max_outer + 1):
            # 5/6. build + inner critic loop
            for inner in range(self.max_inner + 1):
                log(f"[5/7] building v{version} (outer {outer}, inner {inner})...")
                build = self._build(program_path, out, f"v{version}", log)
                it = {"version": version, "outer": outer, "inner": inner,
                      "ok": build.ok, "run_dir": build.run_dir,
                      "feedback": build.feedback, "strip": build.strip}
                if not build.ok and build.run_dir is None:
                    # program crashed before producing anything — send the
                    # traceback back to the author
                    directives = [
                        "The program crashed before building. Fix the error:\n"
                        + build.stderr_tail]
                    it["directives"] = directives
                    trace["iterations"].append(it); save_trace()
                    if inner == self.max_inner:
                        break
                    log("      program error — revising...")
                    version += 1
                    program_src = self.author.revise(task, program_src, directives)
                    program_src = self._lint_gate(task, program_src, log)
                    program_path = out / f"program_v{version}.py"
                    program_path.write_text(program_src)
                    continue  # crash revise: no images (nothing was built)

                last_good = {"program": program_src, "build": build}
                log("[6/7] critic (room VLM strip + feedback)...")
                review = self._criticize(build)
                it["critic"] = review
                trace["iterations"].append(it); save_trace()
                log(f"      converged={review['converged']}  {review['notes']}")
                if review["converged"] or inner == self.max_inner:
                    break
                version += 1
                program_src = self.author.revise(task, program_src,
                                                 review["directives"],
                                                 images=revise_images(build) or None)
                program_src = self._lint_gate(task, program_src, log)
                program_path = out / f"program_v{version}.py"
                program_path.write_text(program_src)

            # 7. outer design judgement — always of the last SUCCESSFUL build
            if last_good["build"] is None:
                log("[7/7] no successful build to judge — skipping judgement")
                break
            log("[7/7] judging the build against the design target...")
            verdict = self._judge_design(last_good["build"], plan.get("plan_png"),
                                         prompt, plan["brief"])
            outer_reports.append(verdict)
            trace["judgements"] = outer_reports; save_trace()
            log(f"      score {verdict['score']:.1f}/10 — {verdict['verdict']}")

            if verdict["score"] > best["score"]:
                best = {"score": verdict["score"], **last_good}
                # Snapshot the blend NOW: scene.blend is a fixed path every later
                # build overwrites, and unlike program/strip it can't be re-emitted
                # from `best` at the end — without this, a lower-scored final
                # revision ships as scene.blend under the best version's score.
                blend = out / "scene.blend"
                if blend.exists():
                    shutil.copy2(blend, out / "scene_best.blend")

            if verdict["score"] >= self.judge_threshold or outer == self.max_outer:
                break
            log(f"      below threshold {self.judge_threshold} — revising for gaps...")
            version += 1
            program_src = self.author.revise(task, last_good["program"],
                                             verdict["gaps"],
                                             images=revise_images(last_good["build"]) or None)
            program_src = self._lint_gate(task, program_src, log)
            program_path = out / f"program_v{version}.py"
            program_path.write_text(program_src)

        # emit the best JUDGED successful version (else the last good build)
        (out / "program.py").write_text(best["program"] or last_good["program"]
                                        or program_src)
        final_build = best["build"] or last_good["build"] or build
        if final_build and final_build.strip and os.path.exists(final_build.strip):
            shutil.copy(final_build.strip, out / "final_strip.png")
        # restore the best-judged blend over whatever the LAST build left behind
        best_blend = out / "scene_best.blend"
        if best["build"] is not None and best_blend.exists():
            shutil.copy2(best_blend, out / "scene.blend")
            best_blend.unlink()
        trace["final"] = {
            "score": best["score"],
            "program": str(out / "program.py"),
            "blend": str(out / "scene.blend"),
            "plan": plan_png,
            "run_dir": final_build.run_dir if final_build else None,
        }
        save_trace()
        log(f"\ndone — score {best['score']:.1f}/10; artifacts in {out}")
        log(f"  design plan : {plan_png}")
        log(f"  built strip : {out / 'final_strip.png'}")
        log(f"  scene       : {out / 'scene.blend'}")
        return trace
