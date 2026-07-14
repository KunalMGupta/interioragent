#!/usr/bin/env python3
"""Render 4-view interior strips for a list of .blend scenes into a review batch dir.

Usage: python tools/batch_strips.py <batch_dir> <scene_name>=<blend_path> [...]
For each scene: renders [back, front, left, right] interior views via SceneRenderer,
stitches them horizontally into <batch_dir>/<scene_name>/strip.png.
(meta.json for each scene is written separately by the batch driver.)
"""
import os
import sys

from PIL import Image
from IDSDL.renderer.renderer import SceneRenderer


def main():
    batch = sys.argv[1]
    renderer = SceneRenderer(resolution_x=640, resolution_y=480, samples=48, verbose=False)
    for spec in sys.argv[2:]:
        name, blend = spec.split("=", 1)
        outdir = os.path.join(batch, name)
        os.makedirs(outdir, exist_ok=True)
        views = [os.path.join(outdir, f"_{v}.png") for v in ("back", "front", "left", "right")]
        print(f"[strips] {name}: {blend}", flush=True)
        try:
            renderer.render_interior_walls(blend, views)
            imgs = [Image.open(v) for v in views if os.path.exists(v)]
            if not imgs:
                print(f"[strips] {name}: NO VIEWS RENDERED", flush=True)
                continue
            h = min(i.height for i in imgs)
            imgs = [i.resize((int(i.width * h / i.height), h)) for i in imgs]
            strip = Image.new("RGB", (sum(i.width for i in imgs), h), "white")
            x = 0
            for i in imgs:
                strip.paste(i, (x, 0))
                x += i.width
            strip.save(os.path.join(outdir, "strip.png"))
            for v in views:
                if os.path.exists(v):
                    os.remove(v)
            print(f"[strips] {name}: OK", flush=True)
        except Exception as e:
            print(f"[strips] {name}: FAILED {e}", flush=True)


if __name__ == "__main__":
    main()
