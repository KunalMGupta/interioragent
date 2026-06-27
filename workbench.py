"""
Scene workbench — run a DSL scene program and surface everything needed to
iterate on it in one place:

  * the per-run scratchpad directory (tmp/<run_id>/)
  * the VLM textual feedback collected during compile (otherwise write-only on
    scene.vlm_feedback and never seen)
  * an index of every render produced this run, with paths to open/inspect

Usage:
    python workbench.py run path/to/scene_program.py
    python workbench.py report                 # re-print the latest run's saved report

Run under the project env:
    PYTHONPATH=/work /opt/conda/envs/interioragent/bin/python workbench.py run scene.py

The program is executed as a normal script (its `scene.export(...)` etc. run as
written). Afterwards the workbench finds the SceneProgRoom in its namespace and
reports. It also writes feedback.txt and report.json into the run directory so
`report` can re-show the latest run without recomputing.
"""
import argparse
import glob
import json
import os
import runpy
import sys


def latest_run_dir():
    dirs = sorted(glob.glob("tmp/2*"), key=os.path.getmtime)
    return dirs[-1] if dirs else None


def _find_scene(ns):
    from IDSDL.scene import SceneProgRoom
    scenes = [v for v in ns.values() if isinstance(v, SceneProgRoom)]
    return scenes[-1] if scenes else None


def _collect(scene):
    run_dir = getattr(scene, "run_dir", None)
    feedback = (getattr(scene, "vlm_feedback", "") or "").strip()
    renders = []
    if run_dir and os.path.isdir(run_dir):
        renders = sorted(
            glob.glob(os.path.join(run_dir, "**", "*.png"), recursive=True)
        )
    return {
        "scene": getattr(scene, "name", "?"),
        "run_dir": run_dir,
        "counts": {
            "objects": len(getattr(scene, "objects", [])),
            "walls": len(getattr(scene, "walls", [])),
            "wall_objects": len(getattr(scene, "wall_objects", [])),
            "ceiling_lights": len(getattr(scene, "ceiling_lights", [])),
        },
        "vlm_feedback": feedback,
        "renders": renders,
    }


def _persist(report):
    run_dir = report["run_dir"]
    if not run_dir or not os.path.isdir(run_dir):
        return
    with open(os.path.join(run_dir, "feedback.txt"), "w") as f:
        f.write(report["vlm_feedback"] + "\n")
    with open(os.path.join(run_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)


def _print(report):
    bar = "=" * 70
    print(f"\n{bar}\n WORKBENCH REPORT — scene '{report['scene']}'\n{bar}")
    print(f" run_dir : {report['run_dir']}")
    c = report["counts"]
    print(f" scene   : {c['objects']} objects, {c['walls']} walls, "
          f"{c['wall_objects']} wall-objects, {c['ceiling_lights']} ceiling-lights")

    print("\n--- VLM FEEDBACK (collected this compile) ---")
    if report["vlm_feedback"]:
        print(report["vlm_feedback"])
    else:
        print("(none — no VLM constraint produced feedback, or no group with VLM "
              "constraints compiled)")

    print("\n--- RENDERS ---")
    if report["renders"]:
        for p in report["renders"]:
            print(f"  {p}")
    else:
        print("(none found under run_dir)")
    print(bar + "\n")


def cmd_run(program_path):
    program_path = os.path.abspath(program_path)
    if not os.path.isfile(program_path):
        print(f"[workbench] no such program: {program_path}", file=sys.stderr)
        return 1
    print(f"[workbench] running {program_path} ...")
    ns = runpy.run_path(program_path, run_name="__main__")
    scene = _find_scene(ns)
    if scene is None:
        print("[workbench] no SceneProgRoom instance found in program namespace.",
              file=sys.stderr)
        return 1
    report = _collect(scene)
    _persist(report)
    _print(report)
    return 0


def cmd_report():
    run_dir = latest_run_dir()
    if not run_dir:
        print("[workbench] no runs under tmp/.", file=sys.stderr)
        return 1
    path = os.path.join(run_dir, "report.json")
    if not os.path.isfile(path):
        print(f"[workbench] latest run {run_dir} has no report.json "
              f"(was it produced by `workbench run`?).", file=sys.stderr)
        return 1
    with open(path) as f:
        _print(json.load(f))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="workbench")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a scene program and report")
    r.add_argument("program", help="path to a scene .py program")
    sub.add_parser("report", help="re-print the latest run's saved report")
    args = ap.parse_args(argv)

    if args.cmd == "run":
        return cmd_run(args.program)
    if args.cmd == "report":
        return cmd_report()
    return 2


if __name__ == "__main__":
    sys.exit(main())
