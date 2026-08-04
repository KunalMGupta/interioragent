"""Solver-trajectory videos for the docs.

Hooks GradSolver.compute_gradients to snapshot every object's world transform at
the top of each optimization step (plus the final settled state), exports the
finished blend, then replays the snapshots as keyframes in a headless Blender
render (anim_render.py) straight to H.264 MP4.

Run from the repo root:
    python tools/docs_figures/video.py <video> [video ...]
    python tools/docs_figures/video.py --all
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from tools.docs_figures import harness   # noqa: E402  (paths, .env, VLM stub)
from tools.docs_figures import figures   # noqa: E402

ANIM = os.path.join(REPO, "tools", "docs_figures", "anim_render.py")

FPS = 15
MAX_MOVE_FRAMES = 90       # subsample longer trajectories down to this
LEAD_HOLD = 12             # frames holding the initial layout
TAIL_HOLD = 22             # frames holding the settled layout

# Each video replays the SAME program as the matching docs figure.
VIDEOS = {
    "vid_overlap":     {"fig": "con_overlap_after", "view": "top"},
    "vid_outofbounds": {"fig": "con_outofbounds_after", "view": "top"},
    "vid_clearance":   {"fig": "con_clearance_after", "view": "top"},
    "vid_access":      {"fig": "con_access_after", "view": "top"},
    "vid_visibility":  {"fig": "con_visibility_after", "view": "top"},
    "vid_hierarchical": {"fig": "hier_nested", "view": "persp"},
}


def _leaf_objects(node):
    kids = getattr(node, "children", None)
    if kids:
        for c in kids:
            yield from _leaf_objects(c)
    else:
        yield node


def _state(obj):
    t, r, _ = obj.get_state_info()
    return [float(t[0]), float(t[1]), float(t[2]), float(r)]


def capture(name, spec):
    from IDSDL.scene import SceneProgRoom
    from IDSDL import constraints as C

    harness._stub_vlm_constraints()
    raw = []          # list of {id(leaf): [x, y, z, rot]} — leaves inherit group motion

    orig = C.GradSolver.compute_gradients

    def hooked(solver):
        snap = {}
        for o in solver.objects:
            for leaf in _leaf_objects(o):
                snap[id(leaf)] = _state(leaf)
        raw.append(snap)
        return orig(solver)

    C.GradSolver.compute_gradients = hooked
    try:
        fig_spec = figures.FIGURES[spec["fig"]]
        scene = SceneProgRoom(name, seed=fig_spec.get("seed", harness.SEED))
        fig_spec["build"](scene)
        raw.append({id(o): _state(o) for o in scene.objects})   # final settled state
        blend = os.path.join(harness.SCRATCH, f"{name}.blend")
        scene.export(blend)
    finally:
        C.GradSolver.compute_gradients = orig

    # Export names instances by scene.objects index — remap identity -> index.
    ids = [id(o) for o in scene.objects]
    # Keep only full-scene solves (the room level); child-group solves cover a
    # fraction of the leaves and would render as a confusing partial prologue.
    full = [s for s in raw if sum(1 for i in ids if i in s) >= 0.9 * len(ids)]
    frames = [[snap.get(i) for i in ids] for snap in (full if len(full) >= 3 else raw)]

    if len(frames) < 3:
        raise RuntimeError(f"{name}: solver produced only {len(frames)} snapshots "
                           "— nothing worth animating")
    if len(frames) > MAX_MOVE_FRAMES:
        step = len(frames) / MAX_MOVE_FRAMES
        frames = [frames[int(i * step)] for i in range(MAX_MOVE_FRAMES - 1)] + [frames[-1]]
    return blend, frames


def render(name, spec):
    os.makedirs(harness.SCRATCH, exist_ok=True)
    os.makedirs(harness.OUT, exist_ok=True)
    blend, frames = capture(name, spec)

    data = {
        "fps": FPS,
        "lead_hold": LEAD_HOLD,
        "tail_hold": TAIL_HOLD,
        "view": spec.get("view", "top"),
        "frames": frames,
    }
    frames_json = os.path.join(harness.SCRATCH, f"{name}_frames.json")
    with open(frames_json, "w") as f:
        json.dump(data, f)

    out_mp4 = os.path.join(harness.OUT, f"{name}.mp4")
    cmd = [harness.BLENDER, "--background", blend, "--python", ANIM, "--",
           frames_json, out_mp4]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or "wrote" not in r.stdout:
        sys.stderr.write(r.stdout[-3000:] + "\n" + r.stderr[-3000:] + "\n")
        raise RuntimeError(f"anim render failed for {name}")
    # Blender may append the frame range to the movie filename — normalize it.
    if not os.path.exists(out_mp4):
        import glob
        hits = sorted(glob.glob(os.path.join(harness.OUT, f"{name}*.mp4")))
        if not hits:
            raise RuntimeError(f"no mp4 produced for {name}")
        os.replace(hits[-1], out_mp4)
    print(f"OK {name}.mp4  ({len(frames)} solver frames)")


def main():
    harness._load_env()
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        print("known videos:", ", ".join(sorted(VIDEOS)))
        return
    names = sorted(VIDEOS) if args == ["--all"] else args
    failed = []
    for n in names:
        try:
            render(n, VIDEOS[n])
        except Exception as e:
            print(f"FAIL {n}: {e}")
            failed.append(n)
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
