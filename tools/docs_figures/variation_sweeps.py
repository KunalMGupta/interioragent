"""Whole-scene sparsity/jitter sweep strips for the docs Groups page.

Each strip re-builds the SAME seeded scene at three knob values and renders the
perspective studio view; the three panels are then composited into one labeled
arrow strip (composites.sweep style) so ONLY the swept dial differs across panels.

Run from the repo root (sequential renders, one blender at a time):
    CUDA_VISIBLE_DEVICES=1 python tools/docs_figures/variation_sweeps.py [strip ...]
With no args every strip in STRIPS is built.

Outputs land in tmp/docs_figures/sweeps/out (own subdir: never collides with the
figures.py harness outputs in tmp/docs_figures/out).
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# Own scratch/out tree, claimed BEFORE harness import (harness reads these at import).
# Falls back beside the repo when tmp/ is not writable (it is root-owned on some hosts).
def _scratch_root():
    tmp = os.path.join(REPO, "tmp")
    if os.access(tmp, os.W_OK) or (
            not os.path.exists(tmp) and os.access(REPO, os.W_OK)):
        return os.path.join(tmp, "docs_figures", "sweeps")
    alt = os.path.join(os.path.expanduser("~"), ".cache",
                       "interioragent_docs_figures", "sweeps")
    print(f"[sweeps] {tmp} not writable; using {alt}")
    return alt


os.environ.setdefault("DOCS_FIG_SCRATCH", _scratch_root())
os.environ.setdefault(
    "DOCS_FIG_OUT", os.path.join(os.environ["DOCS_FIG_SCRATCH"], "out"))

# IDSDL needs both at import time; default to the repo-local Blender like harness does.
_BL = os.path.join(REPO, "blender-4.5.4-linux-x64")
os.environ.setdefault("BLENDER_PATH", os.path.join(_BL, "blender"))
os.environ.setdefault(
    "BLENDER_PYTHON", os.path.join(_BL, "4.5", "python", "bin", "python3.11"))

from tools.docs_figures import composites, harness  # noqa: E402


# ------------------------------------------------------------------
# Scene builders — one seeded scene each; the knob is the only variable
# ------------------------------------------------------------------

def dining_jitter(scene, jitter):
    """Six chairs around a dining table; jitter buys the pulled-out-chair look."""
    with scene.AroundGroup(jitter=jitter) as dining:
        table = scene.AddAsset(
            "a large rectangular dining table with a dark wood finish")
        chair = scene.AddAsset("an elegant dining chair with a cushioned seat")
        dining.set_anchor(table)
        dining.place_rectilinear(
            longer_side1=2 * chair, longer_side2=2 * chair,
            shorter_side1=1 * chair, shorter_side2=1 * chair,
        )
    scene.bind(dining)


def classroom_sparsity(scene, sparsity):
    """Classroom rows of chairs; sparsity opens the aisles. (Chairs, not desks:
    flat-topped desks at sparsity=0 pack edge-to-edge into what reads as one
    continuous slab, which looks broken rather than tightly packed. Dark chair per
    the docs review: white chairs read poorly on the light studio background.)"""
    with scene.GridGroup(sparsity=sparsity) as classroom:
        chair = scene.AddAsset("a dark wooden dining chair")
        classroom.place_grid(9 * chair, cols=3)
    scene.bind(classroom)


def _bedroom_rel(scene, **kw):
    """RelativeGroup bed + two nightstands (place_on_left / place_on_right)."""
    with scene.RelativeGroup(**kw) as rel:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        rel.set_anchor(bed)
        rel.place_on_left(scene.AddAsset("a small wooden nightstand with a drawer"))
        rel.place_on_right(scene.AddAsset("a small wooden nightstand with a drawer"))
    scene.bind(rel)


def bedroom_rel_jitter(scene, jitter):
    """Jitter slides each nightstand in its slot and yaws it off square."""
    _bedroom_rel(scene, jitter=jitter)


def bedroom_rel_sparsity(scene, sparsity):
    """Sparsity steps each nightstand away from the bed (gap scale + an
    extent-proportional push, so the widening is visible at arm's length)."""
    _bedroom_rel(scene, sparsity=sparsity)


def stack_jitter(scene, jitter):
    """StackGroup crates; jitter slides each level within the footprint below.

    Rendered but NOT embedded in groups.md: the retrieved crate mesh is itself a
    twin stack of crates, so 4 levels read as ~8 floating crates at high jitter —
    the RelativeGroup bedroom strips demonstrate the third group family instead."""
    with scene.StackGroup(jitter=jitter) as stack:
        crate = scene.AddAsset("a wooden storage crate")
        stack.place_stack(4 * crate)
    scene.bind(stack)


# ------------------------------------------------------------------
# Strip registry
# ------------------------------------------------------------------

STRIPS = {
    "sweep_scene_dining_jitter": {
        "build": dining_jitter, "label": "AroundGroup(jitter=…)",
        "values": (0.0, 0.4, 0.8),
    },
    "sweep_scene_classroom_sparsity": {
        "build": classroom_sparsity, "label": "GridGroup(sparsity=…)",
        "values": (0.0, 0.4, 0.8),
    },
    "sweep_scene_bedroom_rel_jitter": {
        "build": bedroom_rel_jitter, "label": "RelativeGroup(jitter=…)",
        "values": (0.0, 0.4, 0.8),
    },
    "sweep_scene_bedroom_rel_sparsity": {
        "build": bedroom_rel_sparsity, "label": "RelativeGroup(sparsity=…)",
        "values": (0.0, 0.4, 0.8),
    },
    "sweep_scene_stack_jitter": {
        "build": stack_jitter, "label": "StackGroup(jitter=…)",
        "values": (0.0, 0.4, 0.8),
    },
}


def run_strip(name, spec, view="persp"):
    panels = []
    for v in spec["values"]:
        tag = f"{name}_{v:.1f}".replace(".", "")
        harness.build_and_render(
            tag, lambda s, v=v: spec["build"](s, v),
            mode=spec.get("mode", "group"), views=(view,), seed=harness.SEED)
        panels.append((f"{tag}_{view}", f"{v:.1f}"))
    composites.sweep(harness.OUT, harness.OUT, name, spec["label"], panels)


def main():
    harness._load_env()
    # IDSDL writes its per-run scratch to ./tmp relative to the cwd; run from our
    # own scratch root so a read-only repo tmp/ never blocks the build.
    os.makedirs(harness.SCRATCH, exist_ok=True)
    os.chdir(harness.SCRATCH)
    args = sys.argv[1:]
    names = args or sorted(STRIPS)
    failed = []
    for n in names:
        try:
            run_strip(n, STRIPS[n])
        except Exception as e:
            print(f"FAIL {n}: {e}")
            failed.append(n)
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
