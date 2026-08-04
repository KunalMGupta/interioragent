"""Build-and-render driver for the docs figures.

Each figure is a (name, build_fn, mode) triple registered in FIGURES. build_fn
receives a fresh seeded SceneProgRoom and composes the scene exactly like the code
snippet shown in the docs (with asset_id pins where the natural-language pick is
poor). The scene is exported to a scratch .blend and rendered by studio_render.py.

Run from the repo root:
    python tools/docs_figures/harness.py <figure> [figure ...]
    python tools/docs_figures/harness.py --all
"""
import os
import subprocess
import sys

os.environ.setdefault("IDSDL_SMART_SCALE", "0")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

SCRATCH = os.environ.get(
    "DOCS_FIG_SCRATCH", os.path.join(REPO, "tmp", "docs_figures"))
OUT = os.environ.get(
    "DOCS_FIG_OUT", os.path.join(SCRATCH, "out"))
BLENDER = os.environ.get(
    "BLENDER_PATH", os.path.join(REPO, "blender-4.5.4-linux-x64", "blender"))
STUDIO = os.path.join(REPO, "tools", "docs_figures", "studio_render.py")

SEED = 7


def _load_env():
    envf = os.path.join(REPO, ".env")
    if os.path.exists(envf):
        for line in open(envf):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _stub_vlm_constraints():
    """Docs figures must be deterministic: VLM proportion passes become no-ops."""
    from IDSDL import constraints

    constraints.ObjectProportionsConstraint.compute_gradients = (
        lambda self: "no rescale")
    constraints.RoomProportionsConstraint.compute_gradients = (
        lambda self: "no rescale")


def build_and_render(name, build_fn, mode="group", views=("persp", "top"),
                     seed=SEED):
    from IDSDL.scene import SceneProgRoom

    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    _stub_vlm_constraints()

    blend = os.path.join(SCRATCH, f"{name}.blend")
    scene = SceneProgRoom(name, seed=seed)
    build_fn(scene)
    scene.export(blend)

    cmd = [BLENDER, "--background", blend, "--python", STUDIO, "--",
           OUT, name, mode, ",".join(views)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or "wrote" not in r.stdout:
        sys.stderr.write(r.stdout[-3000:] + "\n" + r.stderr[-3000:] + "\n")
        raise RuntimeError(f"studio render failed for {name}")
    for v in views:
        print(f"OK {name}_{v}.png")


def main():
    _load_env()
    from tools.docs_figures import figures  # registers FIGURES

    args = sys.argv[1:]
    if not args:
        print(__doc__)
        print("known figures:", ", ".join(sorted(figures.FIGURES)))
        return
    names = sorted(figures.FIGURES) if args == ["--all"] else args
    failed = []
    for n in names:
        spec = figures.FIGURES[n]
        try:
            build_and_render(n, spec["build"], spec.get("mode", "group"),
                             spec.get("views", ("persp", "top")),
                             spec.get("seed", SEED))
        except Exception as e:
            print(f"FAIL {n}: {e}")
            failed.append(n)
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
