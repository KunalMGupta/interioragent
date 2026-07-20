"""Planar-region detection sandbox (prototype for place_on_top / place_inside).

Given a base object mesh, find the upward-facing flat regions you could place small
objects on (tabletops, each shelf of a bookcase, a cabinet's interior floor, ...), and
write a GLB with a translucent colored slab dropped on each region so you can eyeball the
detection in any local GLB viewer.

This is deliberately standalone — it does NOT touch the IDSDL placement code. Once region
detection is robust here, we wire it into place_on_top.

Usage:
    python tools/planar_regions.py --list
    python tools/planar_regions.py --object coffee_table          # built-in example
    python tools/planar_regions.py --object bookshelf --place vase book
    python tools/planar_regions.py --glb /path/to/asset.glb --out regions.glb

Frame: dataset GLBs are Y-up (the IDSDL convention), so "up" is +Y. Regions are reported
in the raw mesh frame (the same frame as SceneProgObject.vertices).
"""
import argparse
import math
import os
import re
import sys

import numpy as np
import trimesh

_DATASET = os.path.join(os.path.dirname(__file__), "..", "IDSDL", "datasets", "futurehssd")

# A few hand-picked base objects + small items to experiment with.
EXAMPLES = {
    # base furniture
    "coffee_table": "future/0d3e3b3c-3f1a-47ee-8566-1052cb8635b6",
    "dining_table": "future/5b3eb52a-e3ed-4f13-bcb7-2564bf39d34b",
    "bookshelf":    "future/a9be5d5c-61d1-4a86-a95f-4a6074ccb6a8",
    "bookshelf2":   "future/50785bdc-dbdb-48fc-a636-f5cd9804a74e",
    "cabinet":      "future/4046df2a-6909-49a0-8ff0-b5661da39be0",
    "marble_cabinet": "future/628f0512-9454-40ee-b65b-d3e253cc9227",
    # small things to place on/in them (a range of real heights: lamp tall -> tureen short)
    "table_lamp":  "future/f5d74060-ae91-44d2-8435-f587692b6b4d",
    "desk_clock":  "future/1b39938c-f776-4866-8370-3a08ea4d1425",
    "potted_plant": "hssd/d97a5f104f7d0acaa9fb3cd559eacc7d79c21a83",
    "centerpiece": "hssd/c0d63b78aebfb4cb9dfd70c8b512f156511d120f",
    "tureen":      "hssd/a67b6d7ab7b6a46e1c347a818dcd19663577fee8",
}

_META_PATH = os.path.join(os.path.dirname(__file__), "..", "IDSDL", "datasets", "assets", "futurehssd.json")
_META = None


def describe(model):
    """Look up an asset's text description (for the LLM to reason about), or '' ."""
    global _META
    if _META is None:
        import json
        try:
            _META = json.load(open(_META_PATH))
        except OSError:
            _META = {}
    return _META.get(model, {}).get("description", "")

PALETTE = [
    [231, 76, 60, 130], [46, 204, 113, 130], [52, 152, 219, 130],
    [241, 196, 15, 130], [155, 89, 182, 130], [26, 188, 156, 130],
    [230, 126, 34, 130], [149, 165, 166, 130],
]

# When an item is placed on a tile, its footprint is uniformly shrunk to at most this fraction of
# the tile's WxD, leaving a margin so it doesn't touch the cell walls (see build_candidate).
TILE_FOOTPRINT_FRAC = 0.9


def model_to_path(model):
    """Resolve a 'future/<id>' or 'hssd/<id>' model id (or a raw path) to a GLB path."""
    if os.path.exists(model):
        return model
    kind, mid = model.split("/", 1)
    sub = {"future": "3D-FUTURE-models", "hssd": "HSSD-models"}[kind]
    return os.path.join(_DATASET, sub, mid + ".glb")


def load_mesh(path):
    """Merged single mesh for geometry analysis (matches IDSDL's force='mesh')."""
    return trimesh.load(path, force="mesh", process=False)


# ----------------------------------------------------------------------------------------
# Detection
# ----------------------------------------------------------------------------------------
def _xz_overlap(a, b, gap):
    """Do two [min(3), max(3)] boxes overlap (or sit within `gap`) in the X/Z plane?"""
    for ax in (0, 2):
        if a[1][ax] + gap < b[0][ax] or b[1][ax] + gap < a[0][ax]:
            return False
    return True


def _union(a, b):
    return [np.minimum(a[0], b[0]), np.maximum(a[1], b[1])]


def detect_horizontal_regions(mesh, up=(0, 1, 0), normal_tol=0.9, min_area=0.01,
                              height_tol=0.01, merge_gap=0.005):
    """Return a list of upward-facing flat regions, largest first.

    Each region: {y, bbox:[min(3),max(3)], width, depth, area, n_facets}. ``y`` is the
    surface height (top of the region), ``bbox`` its full extent in the raw mesh frame.

    Strategy: trimesh groups coplanar+adjacent faces into ``facets``; we keep the facets
    whose normal points up and whose area clears ``min_area``, then merge facets that lie
    at the same height and overlap in X/Z (so a tabletop split into several coplanar
    pieces, or a shelf tessellated into strips, reads as one region).
    """
    up = np.asarray(up, float)
    up = up / np.linalg.norm(up)

    cands = []
    facets = mesh.facets
    if len(facets):
        fnormals = mesh.facets_normal
        fareas = mesh.facets_area
        for faces, normal, area in zip(facets, fnormals, fareas):
            if normal @ up < normal_tol or area < min_area:
                continue
            verts = mesh.vertices[np.unique(mesh.faces[faces].ravel())]
            lo, hi = verts.min(0), verts.max(0)
            cands.append({"y": float(hi @ up), "bbox": [lo, hi], "area": float(area),
                          "n_facets": 1})
    else:
        cands = _fallback_face_clusters(mesh, up, normal_tol, min_area, height_tol)

    # greedy merge of same-height, overlapping candidates
    merged = []
    for r in sorted(cands, key=lambda x: -x["area"]):
        for m in merged:
            if abs(m["y"] - r["y"]) <= height_tol and _xz_overlap(m["bbox"], r["bbox"], merge_gap):
                m["bbox"] = _union(m["bbox"], r["bbox"])
                m["area"] += r["area"]
                m["n_facets"] += r["n_facets"]
                break
        else:
            merged.append(dict(r))

    for m in merged:
        lo, hi = m["bbox"]
        m["width"] = float(hi[0] - lo[0])
        m["depth"] = float(hi[2] - lo[2])
    return sorted(merged, key=lambda x: -x["area"])


def top_surfaces(regions, area_frac=0.5, band=0.02):
    """The usable TOP surface(s) for place_on_top: the HIGHEST *substantial* region(s).

    detect_horizontal_regions sorts by AREA, but the largest region is NOT necessarily the top —
    a nightstand/dresser often has a big internal or lower shelf with more area than its real top,
    and picking that sinks on-top items into the body. So: keep regions with >= `area_frac` of the
    max area (usable, not slivers), then take the highest of those plus any coplanar within `band`
    metres. Returns [] for empty input.

    Coplanar-within-`band` regions are the SAME physical surface (a thin tabletop whose underside
    carries upward-facing normals, or a slightly recessed inset), so we **snap them all to the
    highest plane** (`top_y`). Otherwise the caller (region_tiles/build_candidate) seats items at
    each region's own y and an item landing on the lower coplanar face sinks up to `band` metres
    into the top — the exact "monitor sunk into the desk" bug on desks modelled with a 2 cm-thick top.
    """
    if not regions:
        return []
    max_area = max(r["area"] for r in regions)
    substantial = [r for r in regions if r["area"] >= area_frac * max_area]
    top_y = max(r["y"] for r in substantial)
    out = []
    for r in substantial:
        if top_y - r["y"] <= band:
            r = dict(r)
            r["y"] = top_y          # snap the near-coplanar band to the true top plane
            out.append(r)
    return out


def _fallback_face_clusters(mesh, up, normal_tol, min_area, height_tol):
    """When a mesh has no clean facets, bin up-facing faces by height."""
    dots = mesh.face_normals @ up
    keep = np.where(dots > normal_tol)[0]
    if len(keep) == 0:
        return []
    heights = (mesh.triangles_center[keep] @ up)
    order = np.argsort(heights)
    keep, heights = keep[order], heights[order]
    out, start = [], 0
    for i in range(1, len(keep) + 1):
        if i == len(keep) or heights[i] - heights[start] > height_tol:
            grp = keep[start:i]
            area = float(mesh.area_faces[grp].sum())
            if area >= min_area:
                verts = mesh.vertices[np.unique(mesh.faces[grp].ravel())]
                out.append({"y": float(verts.max(0) @ up), "bbox": [verts.min(0), verts.max(0)],
                            "area": area, "n_facets": 1})
            start = i
    return out


# ----------------------------------------------------------------------------------------
# Visualization
# ----------------------------------------------------------------------------------------
def region_slab(region, color, thickness=0.012, lift=0.002, shrink=0.0):
    """A thin translucent box covering a region's X/Z extent, sitting on its surface."""
    lo, hi = region["bbox"]
    w = max(hi[0] - lo[0], 1e-3) * (1 - shrink)
    d = max(hi[2] - lo[2], 1e-3) * (1 - shrink)
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    box = trimesh.creation.box(extents=[w, thickness, d])
    box.apply_translation([cx, region["y"] + lift + thickness / 2, cz])
    box.visual.face_colors = color
    return box


def tile_region(region, tile, gap=0.04, thickness=0.01, lift=0.004):
    """Split a region into a near-uniform grid of tiles, each at most `tile` on a side.

    Returns a list of (center_xz, (w, d)) and the per-region grid as colored slabs. ceil
    keeps every tile <= `tile` (the 2x-largest-asset bound); tiles are inset by `gap` so
    boundaries read in a viewer.
    """
    lo, hi = region["bbox"]
    regW, regD = float(hi[0] - lo[0]), float(hi[2] - lo[2])
    nx, nz = max(1, math.ceil(regW / tile)), max(1, math.ceil(regD / tile))
    tw, td = regW / nx, regD / nz
    tiles = []
    for i in range(nx):
        for j in range(nz):
            cx = lo[0] + (i + 0.5) * tw
            cz = lo[2] + (j + 0.5) * td
            checker = (i + j) % 2
            color = ([46, 204, 113, 150] if checker else [52, 152, 219, 150])
            box = trimesh.creation.box(extents=[max(tw * (1 - gap), 1e-3), thickness,
                                                max(td * (1 - gap), 1e-3)])
            box.apply_translation([cx, region["y"] + lift + thickness / 2, cz])
            box.visual.face_colors = color
            tiles.append((box, (i, j)))
    return tiles, (nx, nz, tw, td)


def build_tiles_visual(path, regions, tile):
    """Original asset + every planar region segmented into a tile grid. Returns (scene, info)."""
    scene = trimesh.load(path)
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)
    info = []
    for ri, r in enumerate(regions):
        tiles, (nx, nz, tw, td) = tile_region(r, tile)
        for box, (i, j) in tiles:
            scene.add_geometry(box, geom_name=f"tile_{ri}_{i}_{j}")
        info.append({"region": ri, "nx": nx, "nz": nz, "tw": tw, "td": td, "count": nx * nz})
    return scene, info


def build_visual(path, regions, thickness=0.012):
    """Original asset + a colored slab per region, as one trimesh.Scene."""
    scene = trimesh.load(path)
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)
    for i, r in enumerate(regions):
        scene.add_geometry(region_slab(r, PALETTE[i % len(PALETTE)], thickness),
                           geom_name=f"region_{i}")
    return scene


def item_footprint(path):
    """(width_x, depth_z, height_y) of a small object in the raw mesh frame."""
    m = load_mesh(path)
    lo, hi = m.bounds
    return float(hi[0] - lo[0]), float(hi[2] - lo[2]), float(hi[1] - lo[1])


# ----------------------------------------------------------------------------------------
# Auto-resize on-top items (LLM reasons about relative heights), then place_on_top
# ----------------------------------------------------------------------------------------
def _parse_fracs(resp, n, max_frac):
    """Parse the LLM's '<index>: <fraction>' lines; default + clamp missing/out-of-range."""
    fracs = [None] * n
    for line in str(resp).splitlines():
        m = re.match(r"\s*(\d+)\s*[:=]\s*([0-9]*\.?[0-9]+)", line)
        if m:
            idx, val = int(m.group(1)), float(m.group(2))
            if 0 <= idx < n:
                fracs[idx] = val
    return [max(0.05, min(max_frac, (0.25 if f is None else f))) for f in fracs]


def llm_height_fractions(base_desc, items, max_frac=1.2, use_llm=True,
                         base_dims=None, item_dims=None):
    """Ask an LLM for each on-top item's height as a fraction of the base height.

    Mirrors ObjectProportionsConstraint's free-text approach: one call sees every item so
    it can reason about RELATIVE heights (a lamp taller than a clock). The LLM is told to
    reason from real-world proportions and bias to the upper, realistic end (decor on a low
    base is often as tall as the base or taller), capped at max_frac of the base height.
    ``items`` is a list of (model_id, description). ``base_dims`` is the base mesh's
    (width, depth, height) in metres and ``item_dims`` an optional list of each item's
    NATURAL (width, depth, height) — giving the LLM real dimensions (not just text) so it
    reasons about true relative size (e.g. a lamp on a short nightstand is still ~0.5-0.7 m).
    Returns one fraction each.
    """
    n = len(items)
    if not use_llm or n == 0:
        return [min(max_frac, 0.8)] * n
    from sceneprogllm import LLM
    sys = f"""You are a sizing assistant for interior scenes. You are given a BASE object and a list
of SMALLER objects to be placed ON TOP of it. For each object choose a realistic display
HEIGHT, expressed as a fraction of the BASE object's height.

Reason from real-world proportions and be GENEROUS — decorative objects on furniture are
usually substantial, not tiny. On a LOW base (a coffee table, cabinet, sideboard) a table
lamp, vase, or potted plant is frequently about as tall as the base itself, sometimes
taller; a centerpiece is a good chunk of the base height. Do not underestimate.

A SMALL base does NOT imply small decor. A nightstand or side table is only ~0.5-0.6 m tall,
but a table lamp on it is still ~0.5-0.7 m — i.e. a fraction near or ABOVE 1.0. Use the real
DIMENSIONS provided (width x depth x height, in metres, for the base and for each item's natural
size) to judge true relative size, not just the names; let a wide/deep base footprint tell you the
piece is substantial.

Rules:
- Fractions must be between 0.1 and {max_frac:.2f} (a value near 1.0 means about as tall as the base).
- Preserve realistic RELATIVE order: a lamp / vase / plant is taller than a bowl, tureen, or clock.
- Prefer the upper part of the plausible range rather than guessing small.
- Output exactly one line per object, in order, formatted as: <index>: <fraction>
- Output nothing else."""
    llm = LLM(system_desc=sys)
    base_line = base_desc + (f"  [size ~ {base_dims[0]:.2f}w x {base_dims[1]:.2f}d x {base_dims[2]:.2f}h m]"
                             if base_dims else "")
    rows = []
    for i, (_, d) in enumerate(items):
        nd = item_dims[i] if (item_dims and i < len(item_dims) and item_dims[i]) else None
        rows.append(f"{i}: {d}" + (f"  [natural ~ {nd[0]:.2f}x{nd[1]:.2f}x{nd[2]:.2f} m]" if nd else ""))
    prompt = (f"BASE object: {base_line}\nObjects to place on top (index: description):\n"
              f"{chr(10).join(rows)}\n\nGive the height fraction for each index.")
    return _parse_fracs(llm(prompt), n, max_frac)


def resize_and_place_on_top(base_path, base_desc, item_models, max_frac=1.2,
                            region_frac=1 / 3, use_llm=True):
    """Place items on the base's top surface, each LLM-resized to frac * base height.

    Height comes from LLM relative-height reasoning (capped at max_frac of the base
    height). A footprint cap then keeps each item's width/depth <= region_frac (default
    1/3) of the LARGEST planar region — the actual usable surface, not the whole bounding
    box — so items can't overhang and a few fit side by side. Items are distributed along
    and rest on that region. Returns (scene, report).
    """
    base = load_mesh(base_path)
    blo, bhi = base.bounds
    Hb = float(bhi[1] - blo[1])
    N = len(item_models)

    # The usable TOP surface (highest substantial region, NOT the largest — which can be a lower
    # shelf) is where on-top items rest; size + place items against it.
    regions = detect_horizontal_regions(base)
    tops = top_surfaces(regions)
    if tops:
        top = max(tops, key=lambda r: r["area"])
        rlo, rhi = top["bbox"]
        regW, regD, surf_y = float(rhi[0] - rlo[0]), float(rhi[2] - rlo[2]), float(top["y"])
        x0, x1, zc = float(rlo[0]), float(rhi[0]), float((rlo[2] + rhi[2]) / 2)
    else:
        regW, regD, surf_y = float(bhi[0] - blo[0]), float(bhi[2] - blo[2]), float(bhi[1])
        x0, x1, zc = float(blo[0]), float(bhi[0]), float((blo[2] + bhi[2]) / 2)
    # items sit in a ROW across the width → each shares ~1/N of the width but may use most of the
    # depth. A single item (N=1) is barely capped, which fixes tiny lamps/decor on small surfaces.
    cap_w, cap_d = (regW / max(N, 1)) * 0.85, regD * 0.85

    descs = [describe(m) or os.path.basename(model_to_path(m)) for m in item_models]
    base_dims = (float(bhi[0] - blo[0]), float(bhi[2] - blo[2]), Hb)
    item_dims = [item_footprint(model_to_path(m)) for m in item_models]
    fracs = llm_height_fractions(base_desc, list(zip(item_models, descs)), max_frac, use_llm,
                                 base_dims=base_dims, item_dims=item_dims)

    scene = trimesh.load(base_path)
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)

    report = []
    for i, (model, desc, frac) in enumerate(zip(item_models, descs, fracs)):
        item = trimesh.load(model_to_path(model))
        if isinstance(item, trimesh.Scene):
            item = trimesh.util.concatenate(item.dump())
        ilo, ihi = item.bounds
        h_raw = max(float(ihi[1] - ilo[1]), 1e-6)
        target_h = frac * Hb
        s = target_h / h_raw
        item.apply_scale(s)

        ilo, ihi = item.bounds
        iw, idd = float(ihi[0] - ilo[0]), float(ihi[2] - ilo[2])
        extra = min(1.0, cap_w / iw if iw > 0 else 1.0, cap_d / idd if idd > 0 else 1.0)
        if extra < 1.0:
            item.apply_scale(extra)
            s *= extra
            ilo, ihi = item.bounds

        x = x0 + (i + 1) * (x1 - x0) / (N + 1)
        cx, cz2 = (ilo[0] + ihi[0]) / 2, (ilo[2] + ihi[2]) / 2
        item.apply_translation([x - cx, surf_y - ilo[1], zc - cz2])
        scene.add_geometry(item, geom_name=f"ontop_{i}")

        flo, fhi = item.bounds
        report.append({"model": model, "desc": desc, "frac": frac,
                       "target_h": target_h, "final_h": float(fhi[1] - flo[1]),
                       "fw": float(fhi[0] - flo[0]), "fd": float(fhi[2] - flo[2])})
    return scene, {"Hb": Hb, "regW": regW, "regD": regD, "surf_y": surf_y,
                   "cap_w": cap_w, "cap_d": cap_d, "items": report}


# ----------------------------------------------------------------------------------------
# Candidate placements + front-render + VLM tournament selection
# ----------------------------------------------------------------------------------------
def resized_items(base_path, base_desc, item_models, max_frac=1.2, region_frac=1 / 3,
                  use_llm=True, descs=None):
    """LLM-resize each item (height + footprint cap), returning regions + resized meshes.

    Returns (regions, items) where each item is {model, desc, mesh, w, d, h}; ``mesh`` is the
    scaled item (un-placed). Shares the sizing logic of resize_and_place_on_top. ``descs``
    overrides the metadata lookup (used when items are GLB paths, e.g. from the DSL).
    """
    base = load_mesh(base_path)
    blo, bhi = base.bounds
    Hb = float(bhi[1] - blo[1])
    N = len(item_models)
    regions = detect_horizontal_regions(base)
    if regions:
        top = max(regions, key=lambda r: r["area"])
        rlo, rhi = top["bbox"]
        regW, regD = float(rhi[0] - rlo[0]), float(rhi[2] - rlo[2])
    else:
        regW, regD = float(bhi[0] - blo[0]), float(bhi[2] - blo[2])
    # N-aware footprint cap (see resize_and_place_on_top): single items aren't over-shrunk.
    cap_w, cap_d = (regW / max(N, 1)) * 0.85, regD * 0.85

    if descs is None:
        descs = [describe(m) or os.path.basename(model_to_path(m)) for m in item_models]
    base_dims = (float(bhi[0] - blo[0]), float(bhi[2] - blo[2]), Hb)
    item_dims = [item_footprint(model_to_path(m)) for m in item_models]
    fracs = llm_height_fractions(base_desc, list(zip(item_models, descs)), max_frac, use_llm,
                                 base_dims=base_dims, item_dims=item_dims)

    items = []
    for model, desc, frac in zip(item_models, descs, fracs):
        mesh = trimesh.load(model_to_path(model))
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(mesh.dump())
        lo, hi = mesh.bounds
        mesh.apply_scale(frac * Hb / max(float(hi[1] - lo[1]), 1e-6))
        lo, hi = mesh.bounds
        iw, idd = float(hi[0] - lo[0]), float(hi[2] - lo[2])
        extra = min(1.0, cap_w / iw if iw > 0 else 1.0, cap_d / idd if idd > 0 else 1.0)
        if extra < 1.0:
            mesh.apply_scale(extra)
        lo, hi = mesh.bounds
        items.append({"model": model, "desc": desc, "mesh": mesh,
                      "w": float(hi[0] - lo[0]), "d": float(hi[2] - lo[2]),
                      "h": float(hi[1] - lo[1])})
    return regions, items


def judge_tile_size(regions, largest, n, coarse=2.0, floor=1.0):
    """Tile size for judging: largest tile in [floor, coarse]x asset that still yields >= n
    tiles on the biggest region, so all n items CAN sit on the top surface. Floors at the
    asset size (1x) to avoid overlap; if even that can't fit n, returns the floor (max tiles).
    """
    if not regions:
        return largest * coarse
    top = max(regions, key=lambda r: r["area"])
    lo, hi = top["bbox"]
    W, D = float(hi[0] - lo[0]), float(hi[2] - lo[2])
    count = lambda t: max(1, math.ceil(W / t)) * max(1, math.ceil(D / t))
    hi_t, lo_t = largest * coarse, largest * floor
    if count(hi_t) >= n:
        return hi_t
    steps = 40
    for s in range(steps + 1):                      # scan down; take the largest tile fitting n
        t = hi_t - (hi_t - lo_t) * s / steps
        if t > 0 and count(t) >= n:
            return t
    return lo_t


def region_tiles(regions, tile):
    """All candidate tiles across every region: {cx, cz, w, d, y, region}."""
    tiles = []
    for ri, r in enumerate(regions):
        lo, hi = r["bbox"]
        regW, regD = float(hi[0] - lo[0]), float(hi[2] - lo[2])
        nx, nz = max(1, math.ceil(regW / tile)), max(1, math.ceil(regD / tile))
        tw, td = regW / nx, regD / nz
        for i in range(nx):
            for j in range(nz):
                tiles.append({"cx": lo[0] + (i + 0.5) * tw, "cz": lo[2] + (j + 0.5) * td,
                              "w": tw, "d": td, "y": float(r["y"]), "region": ri})
    return tiles


def _weighted_sample(values, k, rng):
    """Pick k distinct tile indices, probability proportional to each tile's value."""
    idxs = list(range(len(values)))
    if k >= len(idxs):
        return idxs
    chosen, pool, weights = [], idxs[:], [max(v, 1e-6) for v in values]
    for _ in range(k):
        total = sum(weights)
        r = rng.uniform(0, total)
        acc = 0.0
        for j, w in enumerate(weights):
            acc += w
            if r <= acc:
                chosen.append(pool.pop(j))
                weights.pop(j)
                break
    return chosen


def build_candidate(base_path, items, chosen_tiles, rng, return_placements=False):
    """Place each item on its chosen tile (random yaw + in-tile jitter); return a Scene.

    With return_placements, also returns per-item placement dicts (base-mesh frame):
    {model, desc, x, z, surface_y, yaw, w, h, d} — what the DSL caller applies to objects.
    """
    base = trimesh.load(base_path)
    scene = base if isinstance(base, trimesh.Scene) else trimesh.Scene(base)
    placements = []
    for k, (it, t) in enumerate(zip(items, chosen_tiles)):
        mesh = it["mesh"].copy()
        yaw = rng.uniform(0, 2 * math.pi)
        mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw, [0, 1, 0]))
        # Clamp the item's footprint to its assigned tile: an item's WxD must never exceed the
        # identified tile (compartment/cell) size, or it overflows the cubby/shelf it sits in.
        # resized_items caps footprint against the LARGEST region, which for a multi-compartment
        # cabinet is far bigger than the small cell an item actually lands on. We measure the
        # rotated footprint (so it's aligned with the tile axes) and shrink UNIFORMLY to fit,
        # keeping TILE_FOOTPRINT_FRAC as a margin so items don't touch the cell walls. For a
        # normal tabletop (tile >= item) this is a no-op.
        lo, hi = mesh.bounds
        iw, idd = float(hi[0] - lo[0]), float(hi[2] - lo[2])
        fit = min(1.0,
                  (t["w"] * TILE_FOOTPRINT_FRAC) / iw if iw > 1e-9 else 1.0,
                  (t["d"] * TILE_FOOTPRINT_FRAC) / idd if idd > 1e-9 else 1.0)
        if fit < 1.0:
            mesh.apply_scale(fit)
        lo, hi = mesh.bounds
        cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
        ox = rng.uniform(-1, 1) * max(0.0, (t["w"] - (hi[0] - lo[0])) / 2) * 0.7
        oz = rng.uniform(-1, 1) * max(0.0, (t["d"] - (hi[2] - lo[2])) / 2) * 0.7
        mesh.apply_translation([t["cx"] + ox - cx, t["y"] - lo[1], t["cz"] + oz - cz])
        scene.add_geometry(mesh, geom_name=f"ontop_{k}")
        if return_placements:
            flo, fhi = mesh.bounds
            placements.append({
                "model": it["model"], "desc": it["desc"], "yaw": float(yaw),
                "x": float((flo[0] + fhi[0]) / 2), "z": float((flo[2] + fhi[2]) / 2),
                "surface_y": float(flo[1]), "w": float(fhi[0] - flo[0]),
                "h": float(fhi[1] - flo[1]), "d": float(fhi[2] - flo[2])})
    return (scene, placements) if return_placements else scene


_GLB2BLEND = """import bpy, sys
glb, blend = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
bpy.ops.wm.save_as_mainfile(filepath=blend)
"""


def glb_to_blend(glb_path, workdir):
    """CPU-bound gltf import -> .blend (no GPU). Safe to run at high concurrency."""
    import subprocess
    script = os.path.join(workdir, "_glb2blend.py")  # written once before the pool starts
    blend = os.path.splitext(glb_path)[0] + ".blend"
    bl = os.environ.get("BLENDER_PATH", "blender")
    subprocess.run([bl, "-b", "-P", script, "--", glb_path, blend],
                   check=True, capture_output=True)
    return blend


def smart_placement_uses_gpu():
    """Choose the device for the many tiny, concurrent placement previews.

    ``auto`` preserves the existing GPU path except on macOS.  Cycles/Metal is
    faster for substantial room renders, but three independent Blender workers
    contending for one Apple GPU made 384px/8-sample previews stall for up to
    120 seconds in testing.  CPU avoids that Metal contention while retaining
    the existing three-way workload; normal room/final renders still use Metal.
    """
    value = os.environ.get("IDSDL_SMART_PLACEMENT_DEVICE", "auto").strip().lower()
    if value == "cpu":
        return False
    if value == "gpu":
        return True
    if value != "auto":
        raise ValueError(
            "IDSDL_SMART_PLACEMENT_DEVICE must be one of: auto, cpu, gpu"
        )
    return sys.platform != "darwin"


def render_blend(blend_path, png_path, res=640, samples=16):
    """Strict front render for a small smart-placement candidate.

    A fresh SceneRenderer/SceneProgExec per call avoids racing on the shared instance's
    log_path/tmp_exec_path.
    """
    from IDSDL.renderer.renderer import SceneRenderer
    SceneRenderer(resolution_x=res, resolution_y=res, samples=samples,
                  cuda=smart_placement_uses_gpu()).render_from_front(blend_path, png_path)
    return png_path


def render_front(glb_path, png_path, workdir, res=640, samples=16):
    """Convenience single-shot GLB -> front PNG (used for the one final render)."""
    return render_blend(glb_to_blend(glb_path, workdir), png_path, res, samples)


_JUDGE_RULES = {
    "on_top": "PLACEMENT: STRONGLY prefer the arrangement where every object sits ON THE TOP "
              "surface of the base. Penalise objects on a lower shelf, tucked inside the body, "
              "floating, or hanging off an edge.",
    "inside": "PLACEMENT: STRONGLY prefer the arrangement where the objects are placed INSIDE "
              "the body of the base (on lower/interior shelves), NOT on the very top surface. "
              "Objects sitting on the top surface are bad for this mode.",
}


def vlm_compare(png_a, png_b, item_descs, mode):
    """Ask the VLM which front-view arrangement is better; returns (0 or 1, reason)."""
    from sceneprogllm import LLM
    sys = f"""You are judging two candidate arrangements of small objects placed on a piece of
furniture. Each candidate is shown as a single FRONT-view render: Image 1 is candidate 1,
Image 2 is candidate 2. The objects are: {', '.join(item_descs)}.

Pick the better candidate using these rules, in priority order:
1. VISIBILITY: every object must be clearly visible. Prefer the candidate where all objects
   are fully visible and unoccluded; penalise hidden, overlapping, or clipped objects.
2. {_JUDGE_RULES.get(mode, _JUDGE_RULES['on_top'])}

Respond with winner = 1 or 2 (the better candidate) and a short reason."""
    llm = LLM(system_desc=sys, response_format="json",
              response_params={"winner": "int", "reason": "str"})
    res = llm("Which candidate is better, 1 or 2?", image_paths=[png_a, png_b])
    winner = 0 if int(res.get("winner", 1)) == 1 else 1
    return winner, res.get("reason", "")


def tournament(pngs, item_descs, mode, workers=4, log=print):
    """Single-elimination with parallel per-round VLM evals.

    Returns (winner_index, matches) where ``matches`` is every (loser, winner) pair played
    — the losers feed the tile value update.
    """
    from concurrent.futures import ThreadPoolExecutor
    idxs = list(range(len(pngs)))
    matches, rnd = [], 1
    while len(idxs) > 1:
        pairs = [(idxs[i], idxs[i + 1]) for i in range(0, len(idxs) - 1, 2)]
        bye = idxs[-1:] if len(idxs) % 2 else []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(
                lambda ab: vlm_compare(pngs[ab[0]], pngs[ab[1]], item_descs, mode), pairs))
        nxt = []
        for (a, b), (w, reason) in zip(pairs, results):
            winner, loser = (a, b) if w == 0 else (b, a)
            matches.append((loser, winner))
            log(f"  round {rnd}: cand{a} vs cand{b} -> cand{winner}  ({reason[:60]})")
            nxt.append(winner)
        idxs, rnd = nxt + bye, rnd + 1
    return idxs[0], matches


def build_evolution_image(gen_records, best_png, out_path, title, cols=5, cell=220):
    """Combined image: every candidate render by generation (winners outlined), + the final.

    gen_records: list (per generation) of list of {png, on_top, n, winner}.
    """
    from PIL import Image, ImageDraw, ImageFont
    pad, lh, hh = 3, 22, 28
    font = ImageFont.load_default()
    G = len(gen_records)
    rpg = max(1, math.ceil(len(gen_records[0]) / cols)) if gen_records else 1
    genH = hh + rpg * (cell + lh)
    W, bestH = cols * cell, hh + cell + 40
    M = Image.new("RGB", (W, G * genH + bestH), (15, 15, 15))
    d = ImageDraw.Draw(M)
    for g, recs in enumerate(gen_records):
        gy = g * genH
        win_c = next((i for i, r in enumerate(recs) if r["winner"]), "?")
        d.rectangle([0, gy, W, gy + hh], fill=(40, 40, 55))
        d.text((8, gy + 8), f"GENERATION {g}   winner = cand{win_c}", fill=(200, 210, 255), font=font)
        for c, r in enumerate(recs):
            im = Image.open(r["png"]).convert("RGB").resize((cell - 2 * pad, cell - 2 * pad))
            rr, cc = divmod(c, cols)
            x, y = cc * cell, gy + hh + rr * (cell + lh)
            M.paste(im, (x + pad, y + lh + pad))
            win = r["winner"]
            d.rectangle([x, y, x + cell, y + lh], fill=(20, 60, 20) if win else (28, 28, 28))
            d.text((x + 5, y + 5), f"c{c}  top {r['on_top']}/{r['n']}" + ("  WIN" if win else ""),
                   fill=(120, 240, 120) if win else (210, 210, 210), font=font)
            if win:
                d.rectangle([x + pad, y + lh + pad, x + cell - pad, y + cell - pad],
                            outline=(90, 220, 90), width=3)
    by = G * genH
    d.rectangle([0, by, W, by + hh], fill=(55, 40, 40))
    d.text((8, by + 8), f"CONVERGED FINAL — {title}", fill=(255, 210, 210), font=font)
    if best_png and os.path.exists(best_png):
        b = Image.open(best_png).convert("RGB").resize((cell + 40, cell + 40))
        M.paste(b, ((W - (cell + 40)) // 2, by + hh))
    M.save(out_path)
    return out_path


def generate_and_select(base_path, base_desc, item_models, mode="on_top", k=10,
                        generations=3, decay=0.6, seed=0, max_frac=1.2, use_llm=True,
                        out_dir=".", name="scene", res=640, samples=16, workers=10,
                        render_workers=4, item_descs=None, make_evolution=True, log=print):
    """Tile value-iteration: sample candidates by tile value, tournament, decay losers' tiles.

    Each generation: sample k candidates (tiles drawn proportional to their current value),
    render them in parallel, run a tournament with parallel evals, then multiply the value of
    every tile used by a rejected candidate by ``decay``. Over ``generations`` the values
    converge toward tiles that survive (e.g. top-surface tiles for mode=on_top). The final
    placement greedily takes the highest-value tiles. Returns
    (final_tiles, best_glb, values, placements) where placements are per-item dicts.
    """
    import random
    from concurrent.futures import ThreadPoolExecutor

    regions, items = resized_items(base_path, base_desc, item_models, max_frac=max_frac,
                                   use_llm=use_llm, descs=item_descs)
    if mode == "on_top":
        # only generate candidates on the real TOP surface(s) — not a larger internal/lower shelf,
        # which would sink the item into the base (the largest-area region is often NOT the top).
        regions = top_surfaces(regions) or regions
    n_items = len(items)
    largest = max(max(it["w"], it["d"]) for it in items)
    tile = judge_tile_size(regions, largest, n_items)
    tiles = region_tiles(regions, tile)
    n_top = len(tiles) if mode == "on_top" else sum(1 for t in tiles if t["region"] == 0)
    values = [1.0] * len(tiles)
    rng = random.Random(seed)
    with open(os.path.join(out_dir, "_glb2blend.py"), "w") as f:
        f.write(_GLB2BLEND)
    log(f"  {n_items} items, {len(regions)} region(s), tile={tile:.3f}m -> {len(tiles)} tiles "
        f"({n_top} on top); {generations} gen x {k} candidates (mode={mode}, "
        f"convert_workers={workers}, render_workers={render_workers}, "
        f"render_device={'gpu' if smart_placement_uses_gpu() else 'cpu'})")

    last_winner_glb = None
    gen_records = []
    for gen in range(generations):
        cand_tiles = [_weighted_sample(values, n_items, rng) for _ in range(k)]
        jobs = []
        for c, chosen in enumerate(cand_tiles):
            scene = build_candidate(base_path, items, [tiles[i] for i in chosen], rng)
            glb = os.path.join(out_dir, f"{name}_g{gen}c{c}.glb")
            scene.export(glb)
            jobs.append((glb, os.path.join(out_dir, f"{name}_g{gen}c{c}.png")))
        # Stage 1: CPU glb->blend at full width; Stage 2: GPU render at low width (VRAM-bound).
        with ThreadPoolExecutor(max_workers=workers) as ex:
            blends = list(ex.map(lambda j: glb_to_blend(j[0], out_dir), jobs))
        with ThreadPoolExecutor(max_workers=render_workers) as ex:
            pngs = list(ex.map(lambda bp: render_blend(bp[0], bp[1][1], res, samples),
                               list(zip(blends, jobs))))

        winner, matches = tournament(pngs, [it["desc"] for it in items], mode,
                                     workers=workers, log=log)
        # Credit assignment: a rejected candidate's tiles decay, the winning candidate's
        # tiles are boosted by the same factor. Tiles shared by both sides of a match net
        # out, so only the *distinguishing* tiles move -> values discriminate instead of
        # all collapsing to zero (decay-only does the latter).
        boost = 1.0 / decay
        for loser, winr in matches:
            for ti in cand_tiles[loser]:
                values[ti] *= decay
            for ti in cand_tiles[winr]:
                values[ti] *= boost
        last_winner_glb = jobs[winner][0]
        gen_records.append([
            {"png": jobs[c][1], "n": n_items, "winner": (c == winner),
             "on_top": sum(1 for ti in cand_tiles[c] if tiles[ti]["region"] == 0)}
            for c in range(k)])
        top = sorted(range(len(tiles)), key=lambda i: -values[i])[:n_items]
        log(f"  gen {gen}: winner=cand{winner}; top tiles {top} "
            f"values={[round(values[i], 2) for i in top]}")

    # Final placement: greedily exploit the converged values (highest-value tiles).
    final_tiles = sorted(range(len(tiles)), key=lambda i: -values[i])[:n_items]
    final_scene, placements = build_candidate(base_path, items, [tiles[i] for i in final_tiles],
                                              rng, return_placements=True)
    best_glb = os.path.join(out_dir, f"{name}_best.glb")
    final_scene.export(best_glb)
    best_png = os.path.join(out_dir, f"{name}_best.png")
    render_front(best_glb, best_png, out_dir, res, samples)
    log(f"  CONVERGED: final tiles {final_tiles} -> {best_glb}")
    log(f"  (last tournament winner also at {last_winner_glb})")
    if make_evolution:
        evo = os.path.join(out_dir, f"{name}_{mode}_evolution.png")
        build_evolution_image(gen_records, best_png, evo, f"{name} ({mode})")
        log(f"  evolution image -> {evo}")
    return final_tiles, best_glb, values, placements


def solve_placement(base_glb, base_desc, item_specs, mode="on_top", out_dir=None,
                    name="solve", generations=2, k=8, decay=0.6, seed=0, max_frac=1.2,
                    use_llm=True, res=384, samples=8, workers=10, render_workers=3,
                    make_evolution=False, log=lambda *a: None):
    """Solve a placement for a base mesh and return per-item placements (base-mesh frame).

    ``item_specs`` is a list of (model_id_or_glb_path, description). Returns the per-item
    placement dicts {model, desc, x, z, surface_y, yaw, w, h, d}. Thin wrapper over
    generate_and_select with DSL-friendly defaults (cheaper search, no evolution image).
    """
    import tempfile
    out_dir = out_dir or tempfile.mkdtemp(prefix="vlmplace_")
    models = [s[0] for s in item_specs]
    descs = [s[1] for s in item_specs]
    *_, placements = generate_and_select(
        base_glb, base_desc, models, mode=mode, k=k, generations=generations, decay=decay,
        seed=seed, max_frac=max_frac, use_llm=use_llm, out_dir=out_dir, name=name, res=res,
        samples=samples, workers=workers, render_workers=render_workers, item_descs=descs,
        make_evolution=make_evolution, log=log)
    return placements


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--object", help="built-in example name (see --list)")
    ap.add_argument("--glb", help="path/model-id of a base object (overrides --object)")
    ap.add_argument("--place", nargs="*", default=[], help="small items (example names or ids) to fit-test")
    ap.add_argument("--on-top", nargs="*", default=[], dest="on_top",
                    help="small items to LLM-resize and place on the base's top")
    ap.add_argument("--max-frac", type=float, default=1.2,
                    help="max on-top item height as a fraction of base height")
    ap.add_argument("--no-llm", action="store_true", help="skip the LLM; use a flat default fraction")
    ap.add_argument("--out", help="output GLB (default tools/out/<name>_regions.glb)")
    ap.add_argument("--min-area", type=float, default=0.01, help="min region area m^2")
    ap.add_argument("--normal-tol", type=float, default=0.9, help="cos tol for 'up-facing'")
    ap.add_argument("--judge", action="store_true",
                    help="generate random candidate placements, front-render, VLM-tournament the best")
    ap.add_argument("--mode", choices=["on_top", "inside"], default="on_top",
                    help="judge preference: items on the top surface, or inside the body")
    ap.add_argument("--candidates", type=int, default=10, help="candidate placements per generation")
    ap.add_argument("--generations", type=int, default=3, help="value-iteration generations")
    ap.add_argument("--decay", type=float, default=0.6, help="value multiplier for a rejected tile")
    ap.add_argument("--workers", type=int, default=10,
                    help="CPU workers for glb->blend conversion and VLM evals")
    ap.add_argument("--render-workers", type=int, default=4, dest="render_workers",
                    help="concurrent GPU renders (keep low; VRAM-bound)")
    ap.add_argument("--seed", type=int, default=0, help="random seed for candidate generation")
    ap.add_argument("--res", type=int, default=640, help="render resolution (px, square)")
    ap.add_argument("--samples", type=int, default=16, help="render samples")
    ap.add_argument("--list", action="store_true", help="list built-in examples")
    args = ap.parse_args()

    if args.list:
        for k, v in EXAMPLES.items():
            print(f"  {k:16s} {v}")
        return

    src = args.glb or EXAMPLES.get(args.object) or args.object
    if not src:
        ap.error("give --object NAME or --glb PATH/ID (see --list)")
    path = model_to_path(src)
    name = args.object or os.path.splitext(os.path.basename(path))[0]
    if not os.path.exists(path):
        ap.error(f"not found: {path}")

    mesh = load_mesh(path)
    lo, hi = mesh.bounds
    print(f"object: {name}")
    print(f"  bbox size (W,H,D) = ({hi[0]-lo[0]:.3f}, {hi[1]-lo[1]:.3f}, {hi[2]-lo[2]:.3f}) m")

    regions = detect_horizontal_regions(mesh, normal_tol=args.normal_tol, min_area=args.min_area)
    print(f"  {len(regions)} horizontal region(s) detected:")

    fits = []
    for it in args.place:
        ip = model_to_path(EXAMPLES.get(it, it))
        if os.path.exists(ip):
            w, d, h = item_footprint(ip)
            fits.append((it, w, d))
            print(f"  item '{it}': footprint W,D = ({w:.3f}, {d:.3f}) m")

    for i, r in enumerate(regions):
        line = (f"  [{i}] y={r['y']:.3f}  size(W,D)=({r['width']:.3f},{r['depth']:.3f})  "
                f"area={r['area']:.4f}  facets={r['n_facets']}")
        if fits:
            ok = [it for it, w, d in fits if w <= r["width"] and d <= r["depth"]]
            line += f"  fits: {ok or '-'}"
        print(line)

    out = args.out or os.path.join(os.path.dirname(__file__), "out", f"{name}_regions.glb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build_visual(path, regions).export(out)
    print(f"wrote {os.path.abspath(out)}  (open in any GLB viewer)")

    if args.on_top:
        item_models = [EXAMPLES.get(it, it) for it in args.on_top]
        base_desc = describe(src) or name
        print(f"\nresize + place_on_top ({len(item_models)} item(s), max height {args.max_frac:g}x base):")
        scene, rep = resize_and_place_on_top(path, base_desc, item_models,
                                             max_frac=args.max_frac, use_llm=not args.no_llm)
        print(f"  base height = {rep['Hb']:.3f} m;  largest region (W,D) = "
              f"({rep['regW']:.3f},{rep['regD']:.3f});  footprint cap (W,D) = "
              f"({rep['cap_w']:.3f},{rep['cap_d']:.3f})")
        for it, r in zip(args.on_top, rep["items"]):
            print(f"  {it:14s} frac={r['frac']:.2f}  target_h={r['target_h']:.3f}  "
                  f"final_h={r['final_h']:.3f}  ({r['desc'][:40]})")
        placed = os.path.join(os.path.dirname(out), f"{name}_placed.glb")
        scene.export(placed)
        print(f"wrote {os.path.abspath(placed)}  (open in any GLB viewer)")

        # Segment every region into candidate tiles sized to 2x the largest asset.
        largest = max(max(r["fw"], r["fd"]) for r in rep["items"])
        tile = largest * 2.0
        print(f"\ntile segmentation: largest asset footprint dim = {largest:.3f} m  ->  "
              f"tile <= {tile:.3f} m")
        tscene, tinfo = build_tiles_visual(path, regions, tile)
        total = sum(t["count"] for t in tinfo)
        for t in tinfo:
            print(f"  region {t['region']}: {t['nx']}x{t['nz']} = {t['count']} tiles "
                  f"({t['tw']:.3f} x {t['td']:.3f} m)")
        print(f"  {total} candidate tiles total")
        tiled = os.path.join(os.path.dirname(out), f"{name}_tiles.glb")
        tscene.export(tiled)
        print(f"wrote {os.path.abspath(tiled)}  (open in any GLB viewer)")

        if args.judge:
            print(f"\ncandidate generation + VLM tournament value-iteration "
                  f"(mode={args.mode}, {args.generations} gen x {args.candidates} candidates):")
            generate_and_select(path, base_desc, item_models, mode=args.mode,
                                k=args.candidates, generations=args.generations,
                                decay=args.decay, seed=args.seed, max_frac=args.max_frac,
                                use_llm=not args.no_llm, out_dir=os.path.dirname(out),
                                name=name, res=args.res, samples=args.samples,
                                workers=args.workers, render_workers=args.render_workers)


if __name__ == "__main__":
    main()
