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


SWEEPS = [
    ("sweep_around_sparsity", "AroundGroup(sparsity=…)",
     [("around_sparsity_dense_top", "0.0"),
      ("around_sparsity_mid_top", "0.5"),
      ("around_sparsity_sparse_top", "1.0")]),
    ("sweep_around_jitter", "AroundGroup(jitter=…)",
     [("sweep_around_jitter_00_top", "0.0"),
      ("sweep_around_jitter_05_top", "0.5"),
      ("sweep_around_jitter_10_top", "1.0")]),
    ("sweep_grid_sparsity", "GridGroup(sparsity=…)",
     [("sweep_grid_sparsity_00_top", "0.0"),
      ("sweep_grid_sparsity_04_top", "0.4"),
      ("sweep_grid_sparsity_08_top", "0.8")]),
    ("sweep_grid_randomness", "GridGroup(randomness=…)",
     [("sweep_grid_randomness_00_top", "0.0"),
      ("sweep_grid_randomness_05_top", "0.5"),
      ("sweep_grid_randomness_09_top", "0.9")]),
    ("sweep_rings_jitter", "RingsGroup(jitter=…)",
     [("sweep_rings_jitter_00_top", "0.0"),
      ("sweep_rings_jitter_10_top", "1.0")]),
    ("sweep_room_randomness", "RoomGroup(randomness=…)",
     [("sweep_room_randomness_00_top", "0.0"),
      ("sweep_room_randomness_05_top", "0.5"),
      ("sweep_room_randomness_10_top", "1.0")]),
]


def sweep(renders_dir, out_dir, name, param_label, panels):
    """Same configuration re-rendered across parameter values, joined by an arrow."""
    pw = 640
    tiles = []
    for fname, _ in panels:
        im = Image.open(os.path.join(renders_dir, f"{fname}.png"))
        ph = int(pw * im.size[1] / im.size[0])
        tiles.append(im.resize((pw, ph), Image.LANCZOS))
    ph = min(t.size[1] for t in tiles)

    gap, pad, cap_h, arrow_h = 56, 26, 58, 64
    n = len(tiles)
    W = pad * 2 + n * pw + (n - 1) * gap
    H = pad + ph + cap_h + arrow_h + pad
    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)
    val_f = _font("DejaVuSansMono-Bold.ttf", 34) or _font("DejaVuSansMono.ttf", 34)
    lab_f = _font("DejaVuSans-Bold.ttf", 34)

    for i, (im, (fname, val)) in enumerate(zip(tiles, panels)):
        x = pad + i * (pw + gap)
        canvas.paste(im.crop((0, 0, pw, ph)), (x, pad))
        draw.rectangle([x, pad, x + pw, pad + ph], outline="#d0d0d0", width=2)
        tw = draw.textlength(val, font=val_f)
        draw.text((x + (pw - tw) / 2, pad + ph + 10), val, fill="#111", font=val_f)
        if i < n - 1:
            ax = x + pw + gap // 2
            ay = pad + ph // 2
            draw.line([ax - 16, ay, ax + 10, ay], fill="#888", width=6)
            draw.polygon([(ax + 10, ay - 12), (ax + 10, ay + 12), (ax + 24, ay)],
                         fill="#888")

    # arrow spanning the strip with the parameter label
    ay = pad + ph + cap_h + arrow_h // 2
    x0, x1 = pad + pw // 2, W - pad - pw // 2
    draw.line([x0, ay, x1 - 18, ay], fill="#444", width=5)
    draw.polygon([(x1 - 18, ay - 11), (x1 - 18, ay + 11), (x1, ay)], fill="#444")
    tw = draw.textlength(param_label, font=lab_f)
    draw.rectangle([(W - tw) / 2 - 14, ay - 26, (W + tw) / 2 + 14, ay + 26],
                   fill="white")
    draw.text(((W - tw) / 2, ay - 20), param_label, fill="#444", font=lab_f)

    out = os.path.join(out_dir, f"{name}.png")
    canvas.save(out)
    print("wrote", out)


def sweeps(renders_dir, out_dir):
    for name, label, panels in SWEEPS:
        missing = [f for f, _ in panels
                   if not os.path.exists(os.path.join(renders_dir, f"{f}.png"))]
        if missing:
            print(f"skip {name}: missing {', '.join(missing)}")
            continue
        sweep(renders_dir, out_dir, name, label, panels)


if __name__ == "__main__":
    renders_dir, out_dir = sys.argv[1], sys.argv[2]
    strip(renders_dir, out_dir)
    methods(renders_dir, out_dir)
    sweeps(renders_dir, out_dir)
