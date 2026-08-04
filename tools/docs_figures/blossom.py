"""Cherry-blossom title walkthrough — the 3DV'26 demo, rebuilt.

Spells the title with SentenceASCIIGenerator out of cherry-blossom trees
(CherryBlossomRetriever supplies the mesh), exports the blend, then renders:

  blossom_title_top.png    still for the docs page
  blossom_walkthrough.mp4  dolly through the forest, crane up to the title reveal

Run from the repo root:
    python tools/docs_figures/blossom.py
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from tools.docs_figures import harness   # noqa: E402

SENTENCE = "InteriorAgent\n3DV\t2026\nVancouver"
# modulate_scale > 1 closes the gaps between per-cell trees -> a fuller canopy
TREE_SCALE = 1.45


def _patch_glyphs():
    """Title cards need crisp letterforms: rasterize each character from a real
    font into the same (points, advance) contract AlphabetGenerator.run returns.
    Rows are kept relative to a shared text box, so baselines and x-heights line
    up across glyphs (and the box padding doubles as natural line spacing)."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from IDSDL import groups as G

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)

    def run(self, ch):
        img = Image.new("L", (32, 24), 0)
        ImageDraw.Draw(img).text((2, 2), ch, fill=255, font=font)
        arr = np.array(img) > 96
        ys, xs = np.nonzero(arr)
        if len(xs) == 0:            # spaces and friends
            return np.zeros((0, 2), dtype=int), 4
        xs = xs - xs.min()
        return np.stack([xs, ys], axis=1), int(xs.max()) + 2

    G.AlphabetGenerator.run = run


def build():
    from IDSDL.scene import SceneProgRoom

    harness._stub_vlm_constraints()
    _patch_glyphs()
    os.makedirs(harness.SCRATCH, exist_ok=True)
    scene = SceneProgRoom("blossom_title", seed=7)
    with scene.SentenceASCIIGenerator() as gen:
        tree = scene.AddAsset("a cherry blossom tree", modulate_scale=TREE_SCALE)
        gen.place(tree, SENTENCE)
    scene.bind(gen)
    blend = os.path.join(harness.SCRATCH, "blossom_title.blend")
    scene.export(blend)
    return blend


def main():
    harness._load_env()
    os.makedirs(harness.OUT, exist_ok=True)
    blend = build()
    script = os.path.join(REPO, "tools", "docs_figures", "blossom_render.py")
    cmd = [harness.BLENDER, "--background", blend, "--python", script, "--",
           harness.OUT]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or "wrote" not in r.stdout:
        sys.stderr.write(r.stdout[-4000:] + "\n" + r.stderr[-4000:] + "\n")
        raise RuntimeError("blossom render failed")
    print("OK blossom_title_top.png + blossom_walkthrough.mp4")


if __name__ == "__main__":
    main()
