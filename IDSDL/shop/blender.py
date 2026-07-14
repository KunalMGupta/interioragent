"""Host side of the Blender jobs: write a config, run bl_job.py in Blender, read the result.

Blender is launched as a plain subprocess rather than through SceneProgExec (which the rest of
IDSDL uses) for two reasons that both matter when jobs run in parallel: SceneProgExec writes its
wrapper script and log NEXT TO the script it is given, so N threads sharing one bl_job.py would
clobber each other's files; and it does not capture stdout, so a Blender traceback from a bad
model would be lost in the interleaved noise instead of landing in that job's own log. We keep
its Blender-path convention (BLENDER_PATH), so nothing else changes.
"""
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bl_job.py")
TIMEOUT = 900          # a 300 MB scan can take minutes to import; anything past this is a hang


def blender_bin():
    b = os.environ.get("BLENDER_PATH") or shutil.which("blender")
    if not b or not os.path.exists(b):
        raise RuntimeError("BLENDER_PATH is not set and no `blender` on PATH")
    return b


def run_job(cfg):
    """One Blender job. Never raises for a bad model — a failure comes back as a result dict with
    ok=False and an `error` slug, because 'this file is broken' is a normal, expected outcome of
    pointing a pipeline at the open internet."""
    job_dir = cfg["out_dir"]
    os.makedirs(job_dir, exist_ok=True)
    mode = cfg["mode"]
    cfg_path = os.path.join(job_dir, f"cfg_{mode}.json")
    cfg["result"] = os.path.join(job_dir, f"result_{mode}.json")
    if os.path.exists(cfg["result"]):
        os.remove(cfg["result"])
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=1)

    cmd = [blender_bin(), "--background", "--factory-startup", "--python", SCRIPT, "--", cfg_path]
    log = os.path.join(job_dir, f"blender_{mode}.log")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        with open(log, "w") as f:
            f.write(p.stdout or "")
            f.write("\n--- stderr ---\n")
            f.write(p.stderr or "")
    except subprocess.TimeoutExpired:
        return {"mode": mode, "ok": False, "error": "blender_timeout", "log": log}

    if not os.path.exists(cfg["result"]):
        return {"mode": mode, "ok": False, "error": "blender_crashed", "log": log}
    with open(cfg["result"]) as f:
        res = json.load(f)
    res["log"] = log
    return res


def run_jobs(cfgs, workers=3):
    """Blender is heavy (each job is a whole process importing a mesh); 3 wide is the sweet spot
    on one box — more just swaps."""
    if not cfgs:
        return []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(run_job, cfgs))
