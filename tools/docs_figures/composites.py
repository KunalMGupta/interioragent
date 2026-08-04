"""Composite figures assembled from the studio renders.

1. rendered_views.png — the four cardinal renders of one object as a labeled strip.
2. methods.png — the object-registration overview: six labeled panels, each a real
   render paired with the API call that produced it.

Usage:  python tools/docs_figures/composites.py <renders_dir> <out_dir>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu"]


def _font(name, size):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def strip(renders_dir, out_dir):
    views = ["front", "right", "back", "left"]
    imgs = [Image.open(os.path.join(renders_dir, f"rendered_views_{v}.png"))
            for v in views]
    w, h = imgs[0].size
    label_h = 64
    canvas = Image.new("RGB", (w * 4 + 3 * 8, h + label_h), "white")
    draw = ImageDraw.Draw(canvas)
    font = _font("DejaVuSans.ttf", 40)
    for i, (im, v) in enumerate(zip(imgs, views)):
        x = i * (w + 8)
        canvas.paste(im, (x, 0))
        tw = draw.textlength(v, font=font)
        draw.text((x + (w - tw) / 2, h + 8), v, fill="#444", font=font)
    out = os.path.join(out_dir, "rendered_views.png")
    canvas.save(out)
    print("wrote", out)


PANELS = [
    ("reg_single_persp", "(a) natural-language retrieval",
     'sofa = scene.AddAsset("a modern gray sofa")'),
    ("reg_rotation_persp", "(b) placement & orientation",
     "set_location(x, y, z) / set_rotation(deg) / face_towards(obj)"),
    ("reg_scaling_persp", "(c) scaling",
     "modulate_scale=0.5 / width=1.1 / depth=0.55"),
    ("reg_copies_persp", "(d) copying & batching",
     "chairs = 4 * chair"),
    ("rendered_views_front", "(e) canonical renders",
     "paths = sofa.render()"),
    ("retrieval_custom_persp", "(f) custom retrievers",
     "class FoodCartRetriever(SceneProgAssetRetrieverBase): ..."),
]


def methods(renders_dir, out_dir):
    pw = 760                      # panel image width
    cols, rows = 3, 2
    title_f = _font("DejaVuSans-Bold.ttf", 30)
    code_f = _font("DejaVuSansMono.ttf", 22)
    pad, cap_h = 26, 96

    tiles = []
    for name, title, code in PANELS:
        im = Image.open(os.path.join(renders_dir, f"{name}.png"))
        ph = int(pw * im.size[1] / im.size[0])
        tiles.append((im.resize((pw, ph), Image.LANCZOS), title, code))
    ph = min(t[0].size[1] for t in tiles)

    cell_w, cell_h = pw + pad, ph + cap_h + pad
    canvas = Image.new("RGB", (cols * cell_w + pad, rows * cell_h + pad), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (im, title, code) in enumerate(tiles):
        r, c = divmod(i, cols)
        x, y = pad + c * cell_w, pad + r * cell_h
        canvas.paste(im.crop((0, 0, pw, ph)), (x, y))
        draw.rectangle([x, y, x + pw, y + ph], outline="#d0d0d0", width=2)
        draw.text((x + 6, y + ph + 12), title, fill="#111", font=title_f)
        code_txt = code
        while draw.textlength(code_txt, font=code_f) > pw - 12 and len(code_txt) > 8:
            code_txt = code_txt[:-2]
        if code_txt != code:
            code_txt += "…"
        draw.text((x + 6, y + ph + 54), code_txt, fill="#666", font=code_f)
    out = os.path.join(out_dir, "methods.png")
    canvas.save(out)
    print("wrote", out)


if __name__ == "__main__":
    renders_dir, out_dir = sys.argv[1], sys.argv[2]
    strip(renders_dir, out_dir)
    methods(renders_dir, out_dir)
