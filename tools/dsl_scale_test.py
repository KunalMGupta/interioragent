"""End-to-end smoke test: AnchorGroup.solve_scales() through the real DSL.

Bedroom built the canonical way — nightstand+lamp composed as a nook
(RelativeGroup, place_on_top), two nooks flanking the bed — with the classic
retrieval mis-scale injected via modulate_scale (nightstands 1.45x, lamps 1.7x).
Then g.solve_scales() must walk the nested groups, dedupe the symmetric copies
into shared members, undo the inflation, and recompile so lamps re-seat on the
shrunken nightstands. Renders before/after to /work/tmp/dslscale/.

Run:
  set -a && source /work/.env && set +a
  BLENDER_PATH=/work/blender-4.5.4-linux-x64/blender PYTHONPATH=/work \
    /opt/conda/envs/interioragent/bin/python tools/dsl_scale_test.py
"""
import os
import sys
sys.path.insert(0, "/work")

import trimesh

from IDSDL.scene import SceneProgRoom
from IDSDL.vlm_scale import _baked
from tools.scale_solver import render_corner
from tools.planar_regions import _GLB2BLEND, glb_to_blend

OUT = "/work/tmp/dslscale"
BED = "hssd/bb415be5d1f00f21489c63546acffc44d7c42933"
NIGHTSTAND = "hssd/830e2ed47548d8372294609fe7eeca11fb384b29"
LAMP = "hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed"


def snapshot(group, tag):
    sc = trimesh.Scene()
    from IDSDL.vlm_scale import _leaf_objects
    for i, o in enumerate(_leaf_objects(group, [])):
        for j, g in enumerate(_baked(o).dump()):
            sc.add_geometry(g, geom_name=f"o{i}_{j}")
    lo, hi = sc.bounds
    floor = trimesh.creation.box(
        extents=[float(hi[0] - lo[0]) + 0.6, 0.02, float(hi[2] - lo[2]) + 0.6])
    floor.apply_translation([float(lo[0] + hi[0]) / 2, float(lo[1]) - 0.01,
                             float(lo[2] + hi[2]) / 2])
    sc.add_geometry(floor, geom_name="zfloor")
    glb = os.path.join(OUT, f"{tag}.glb")
    sc.export(glb)
    render_corner(glb_to_blend(glb, OUT), os.path.join(OUT, f"{tag}.png"), sc.bounds)
    print(f"[{tag}] render -> {OUT}/{tag}.png")


def report(group):
    from IDSDL.vlm_scale import _leaf_objects
    for o in _leaf_objects(group, []):
        a = o.get_aabb()
        print(f"  {str(o.description)[:38]:38s} "
              f"{a[1][0]-a[0][0]:.2f}w x {a[1][1]-a[0][1]:.2f}h x {a[1][2]-a[0][2]:.2f}d"
              f"  (bottom y {a[0][1]:+.3f})")


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "_glb2blend.py"), "w") as f:
        f.write(_GLB2BLEND)

    scene = SceneProgRoom("dslscale", seed=7)
    bed = scene.AddAsset("a modern double bed with a wooden frame and a headboard",
                         asset_id=BED)

    def nook():
        ns = scene.AddAsset("a classic dark wood nightstand", asset_id=NIGHTSTAND,
                            modulate_scale=1.45)
        lamp = scene.AddAsset("a classic urn table lamp with a pleated shade",
                              asset_id=LAMP, modulate_scale=1.7)
        with scene.RelativeGroup() as n:
            n.set_anchor(ns)
            n.place_on_top([lamp])
        return n

    nook_l, nook_r = nook(), nook()
    with scene.RelativeGroup() as g:
        g.set_anchor(bed)
        g.place_on_left(nook_l)
        g.place_on_right(nook_r)

    print("BEFORE solve_scales (nightstands 1.45x, lamps 1.7x):")
    report(g)
    snapshot(g, "before")

    best = g.solve_scales(out_dir=OUT)
    print(f"\nsolve_scales returned: {best}")

    print("\nAFTER:")
    report(g)
    snapshot(g, "after")

    if best is None:
        print("FAIL: solver returned None")
        sys.exit(1)
    ns_f = next((f for name, f in best.items() if "nightstand" in name), None)
    lamp_f = next((f for name, f in best.items()
                   if any(w in name for w in ("lamp", "urn", "shade"))), None)
    ok = ns_f and lamp_f and ns_f["s"] < 0.9 and lamp_f["s"] * lamp_f["h"] < 0.9
    print("\nPASS" if ok else "\nWEAK RESULT (factors above; check renders)",
          f"- nightstand {ns_f}, lamp {lamp_f}")


if __name__ == "__main__":
    main()
