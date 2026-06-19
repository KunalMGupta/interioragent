"""
Render results/*.blend files into documentation visuals.

Usage:
    python render_docs.py top  test06_around_circle           # top-down (floor-plan) view
    python render_docs.py persp test06_around_circle          # single perspective view
    python render_docs.py both test05_around_rectilinear      # both views

Outputs go to docs/assets/scenes/<name>_top.png / <name>_persp.png
"""
import os
import sys

from IDSDL.renderer.renderer import SceneRenderer

RESULTS = "results"
OUT = "docs/assets/scenes"

# Lightweight settings — EEVEE, modest resolution, few samples (fast, good enough for docs)
renderer = SceneRenderer(resolution_x=900, resolution_y=900, samples=16, verbose=False)


def render(name, mode):
    os.makedirs(OUT, exist_ok=True)
    blend = os.path.join(RESULTS, f"{name}.blend")
    if not os.path.exists(blend):
        raise FileNotFoundError(blend)

    if mode in ("top", "both"):
        out = os.path.join(OUT, f"{name}_top.png")
        renderer.render_from_top(blend, out)
        print(f"  wrote {out}")

    if mode in ("persp", "both"):
        # render_from_corners writes 4 views; keep the first as the hero perspective
        tmp = [os.path.join(OUT, f"{name}_persp_{i}.png") for i in range(4)]
        renderer.render_from_corners(blend, tmp)
        # keep corner 0 as the canonical perspective, drop the rest
        os.replace(tmp[0], os.path.join(OUT, f"{name}_persp.png"))
        for t in tmp[1:]:
            if os.path.exists(t):
                os.remove(t)
        print(f"  wrote {os.path.join(OUT, f'{name}_persp.png')}")


if __name__ == "__main__":
    mode = sys.argv[1]
    for name in sys.argv[2:]:
        print(f"[{name}] {mode}")
        render(name, mode)
