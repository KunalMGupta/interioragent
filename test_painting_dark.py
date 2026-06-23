"""
Regression test for the 'paintings come out all dark' bug.

The Painting generator textures a canvas and concatenates it with a frame mesh. If the frame
is plain (trimesh's default gray), concatenation bakes that gray into the merged material and
darkens the image -- and AddAsset reloads paintings with force="mesh", which re-triggers the
same corrupting merge. This test stubs the image model with a known BRIGHT image and asserts
the texture is still bright after the real force="mesh" load path.

Run:  python test_painting_dark.py
"""
import numpy as np
import trimesh
from PIL import Image

from IDSDL.datasets import retrievers

BRIGHT = (220, 40, 40)          # vivid red input
MIN_MEAN = 150                  # a bright painting should stay well above this


class _StubLLM:
    def __call__(self, query):
        return Image.new("RGB", (512, 512), BRIGHT)


def texture_mean(glb_path):
    # Load exactly the way AddAsset does.
    m = trimesh.load(glb_path, force="mesh", process=False)
    vis = m.visual
    mat = getattr(vis, "material", None)
    img = None
    if mat is not None:
        img = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)
    assert img is not None, f"painting lost its texture on load (visual={type(vis).__name__})"
    return np.asarray(img.convert("RGB")).reshape(-1, 3).mean(axis=0)


def main():
    p = retrievers.Painting()
    p.llm = _StubLLM()
    path, _ = p("a vivid solid red painting")

    mean = texture_mean(path)
    print(f"input mean   : {np.array(BRIGHT, dtype=float)}")
    print(f"loaded mean  : {mean.round(1)}  (red channel {mean[0]:.0f}, threshold {MIN_MEAN})")

    assert mean[0] >= MIN_MEAN, (
        f"painting is too dark: red channel {mean[0]:.0f} < {MIN_MEAN} "
        f"(texture darkened during concatenate/load)"
    )
    print("PASS: painting texture stays bright through the force=\"mesh\" load path")


if __name__ == "__main__":
    main()
