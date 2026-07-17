"""Five-scene validation of the support-stability pass (IDSDL/stability.py)
through the REAL placement pipeline (VLM tournament + stabilize).

Scenes chosen for edge pressure:
  1. nightstand_cluster — three props crowd a small top (sibling-blocked moves)
  2. counter_service    — bowls + teapot on the 0.33 m-deep ramen counter (the
                          shallow support where tournament edge tiles overhang)
  3. shelf_display      — place_inside a tall bookshelf (interior mode)
  4. cabinet_stock      — place_inside a bar cabinet (interior mode, mixed sizes)
  5. desk_props         — three mid-size props on a writing desk

Per scene: build the group, report every placed object's footprint-support
ratio vs the anchor, render a corner view. PASS if no object is below 0.75
(hard floor — the pass guarantees improvement, not the threshold, when a
sibling blocks the full move) and objects below 0.90 are counted as warnings.

Run:
  set -a && source /work/.env && set +a
  BLENDER_PATH=/work/blender-4.5.4-linux-x64/blender PYTHONPATH=/work \
    /opt/conda/envs/interioragent/bin/python tools/stability_scenes_test.py
"""
import os
import sys
sys.path.insert(0, "/work")

import trimesh

from IDSDL.scene import SceneProgRoom
from IDSDL.stability import STABLE_OVERLAP, _fp, overlap_ratio
from IDSDL.vlm_scale import _baked
from tools.scale_solver import render_corner
from tools.planar_regions import _GLB2BLEND, glb_to_blend

OUT = "/work/tmp/stabscenes"
NIGHTSTAND = "hssd/830e2ed47548d8372294609fe7eeca11fb384b29"
TLAMP = "hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed"
COUNTER = "hssd/b1c9d7321512686e02f2d0be978056456479e14c"
RAMENBOWL = "hssd/e823268a535d8d7aaaf7db9e7cf769c689e7b4f0"
TEAPOT = "hssd/bbf4aa8262d369bc6b16a1669d7acf4c2a4d7b89"

HARD_FLOOR = 0.75
results = []


def build_scene(name, anchor_spec, prop_specs, mode):
    scene = SceneProgRoom(f"stab_{name}", seed=42)
    anchor = scene.AddAsset(anchor_spec[0], asset_id=anchor_spec[1])
    props = [scene.AddAsset(q, asset_id=p) for q, p in prop_specs]
    with scene.RelativeGroup() as g:
        g.set_anchor(anchor)
        if mode == "on_top":
            g.place_on_top(props)
        else:
            g.place_inside(props)
    return anchor, props


def render(name, anchor, props):
    sc = trimesh.Scene()
    for i, o in enumerate([anchor] + props):
        for j, geom in enumerate(_baked(o).dump()):
            sc.add_geometry(geom, geom_name=f"o{i}_{j}")
    glb = os.path.join(OUT, f"{name}.glb")
    sc.export(glb)
    render_corner(glb_to_blend(glb, OUT), os.path.join(OUT, f"{name}.png"), sc.bounds)


def run(name, anchor_spec, prop_specs, mode):
    print(f"\n=== {name} ({mode}) ===")
    anchor, props = build_scene(name, anchor_spec, prop_specs, mode)
    sfp = _fp(anchor.get_aabb())
    rows = []
    for o in props:
        r = overlap_ratio(_fp(o.get_aabb()), sfp)
        flag = "ok  " if r >= STABLE_OVERLAP else ("warn" if r >= HARD_FLOOR else "FAIL")
        print(f"  {flag} {str(o.description)[:44]:44s} support {r:.2f}")
        rows.append((str(o.description), r))
    render(name, anchor, props)
    results.append((name, rows))


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "_glb2blend.py"), "w") as f:
        f.write(_GLB2BLEND)

    run("nightstand_cluster",
        ("a classic dark wood nightstand", NIGHTSTAND),
        [("a classic urn table lamp with a pleated shade", TLAMP),
         ("a small potted succulent plant", None),
         ("a white ceramic coffee mug", None)],
        "on_top")
    run("counter_service",
        ("a long rustic warm wood bar counter with a paneled front", COUNTER),
        [("a ceramic ramen noodle bowl with chopsticks", RAMENBOWL),
         ("a ceramic ramen noodle bowl with chopsticks", RAMENBOWL),
         ("a small ceramic teapot", TEAPOT)],
        "on_top")
    run("shelf_display",
        ("a tall wooden bookshelf", None),
        [("a flower vase with flowers", None),
         ("a stack of books", None)],
        "inside")
    run("cabinet_stock",
        ("a home bar cabinet", None),
        [("a stainless steel cocktail shaker", None),
         ("a wine bottle", None)],
        "inside")
    run("desk_props",
        ("a wooden writing desk", None),
        [("a small metal desk lamp", None),
         ("a desk telephone", None),
         ("a desk globe on a stand", None)],
        "on_top")

    print("\n================ summary ================")
    worst, warns, fails = 1.0, 0, 0
    for name, rows in results:
        for desc, r in rows:
            worst = min(worst, r)
            warns += (HARD_FLOOR <= r < STABLE_OVERLAP)
            fails += (r < HARD_FLOOR)
    n = sum(len(r) for _, r in results)
    print(f"{n} placed objects across {len(results)} scenes; "
          f"worst support {worst:.2f}; {warns} warnings (<0.90), {fails} below {HARD_FLOOR}")
    print(f"renders in {OUT}/")
    print("PASS" if fails == 0 else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
