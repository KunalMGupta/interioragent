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


_VLM_ORIG = {}


def _vlm_classes():
    from IDSDL import constraints
    return (constraints.ObjectProportionsConstraint,
            constraints.RoomProportionsConstraint)


def _stub_vlm_constraints():
    """Docs figures must be deterministic: VLM proportion passes become no-ops."""
    for cls in _vlm_classes():
        _VLM_ORIG.setdefault(cls, cls.compute_gradients)
        cls.compute_gradients = lambda self: "no rescale"


def _live_vlm_constraints(log):
    """VLM-demo figures run the REAL constraint and record its verdicts in `log`."""
    for cls in _vlm_classes():
        orig = _VLM_ORIG.setdefault(cls, cls.compute_gradients)

        def wrapped(self, _orig=orig):
            r = _orig(self)
            log.append(f"[{type(self).__name__}] {r}")
            return r

        cls.compute_gradients = wrapped


def build_and_render(name, build_fn, mode="group", views=("persp", "top"),
                     seed=SEED, vlm=False):
    from IDSDL.scene import SceneProgRoom

    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    vlm_log = []
    prev_minimal = os.environ.get("IDSDL_MINIMAL_RENDERS")
    if vlm:
        _live_vlm_constraints(vlm_log)
        # minimal-render mode skips the anchor-group VLM critique entirely
        os.environ["IDSDL_MINIMAL_RENDERS"] = "0"
    else:
        _stub_vlm_constraints()

    try:
        blend = os.path.join(SCRATCH, f"{name}.blend")
        scene = SceneProgRoom(name, seed=seed)
        build_fn(scene)
        scene.export(blend)
    finally:
        if vlm:
            if prev_minimal is None:
                os.environ.pop("IDSDL_MINIMAL_RENDERS", None)
            else:
                os.environ["IDSDL_MINIMAL_RENDERS"] = prev_minimal
    if vlm:
        with open(os.path.join(OUT, f"{name}_vlm.txt"), "w") as f:
            f.write("\n".join(vlm_log) + "\n")

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
                             spec.get("seed", SEED), vlm=spec.get("vlm", False))
        except Exception as e:
            print(f"FAIL {n}: {e}")
            failed.append(n)
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
