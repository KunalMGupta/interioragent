"""Tests for the support-stability pass (IDSDL/stability.py).

Part 1 — pure AABB math, no Blender/LLM:
  a. an overhanging object is pulled back to >= threshold support
  b. an object WIDER than the support gets best-effort centered
  c. a nudge that would hit a sibling takes the largest collision-free fraction
  d. already-stable objects are untouched
  e. objects at different heights don't block each other (no vertical overlap)

Part 2 — DSL smoke (fallback path, IDSDL_SMART_PLACEMENT=0, no LLM): place a
lamp on a nightstand, drag it half off the edge, re-run stabilize_objects, and
verify support ratio + seat. Renders before/after for eyeballing.

Run:
  BLENDER_PATH=/work/blender-4.5.4-linux-x64/blender PYTHONPATH=/work \
    IDSDL_SMART_PLACEMENT=0 /opt/conda/envs/interioragent/bin/python tools/stability_test.py
"""
import os
import sys
sys.path.insert(0, "/work")
os.environ.setdefault("IDSDL_SMART_PLACEMENT", "0")

import numpy as np

from IDSDL.stability import (STABLE_OVERLAP, _fp, overlap_ratio,
                             solve_stability, stabilize_objects)

FAILURES = []


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        FAILURES.append(name)


def box(cx, y0, cz, w, h, d):
    return np.array([[cx - w / 2, y0, cz - d / 2], [cx + w / 2, y0 + h, cz + d / 2]])


def pure_tests():
    print("[pure AABB tests]")
    support = box(0, 0, 0, 1.0, 0.8, 0.6)   # 1.0 x 0.6 tabletop

    # a. overhanging object pulled back
    obj = box(0.55, 0.8, 0, 0.3, 0.3, 0.3)  # half off the +x edge
    (dx, dz), = solve_stability(support, [obj])
    fp = _fp(box(0.55 + dx, 0.8, 0 + dz, 0.3, 0.3, 0.3))
    check("overhang recovered", overlap_ratio(fp, _fp(support)) >= STABLE_OVERLAP,
          f"(ratio {overlap_ratio(fp, _fp(support)):.2f}, dx {dx:+.3f})")

    # b. wider-than-support object centered
    obj = box(0.9, 0.8, 0, 1.6, 0.3, 0.3)
    (dx, dz), = solve_stability(support, [obj])
    check("oversized centered", abs((0.9 + dx) - 0.0) < 1e-6, f"(dx {dx:+.3f})")

    # c. sibling blocks the full move -> largest collision-free fraction
    hang = box(0.55, 0.8, 0, 0.3, 0.3, 0.3)      # needs dx=-0.2 for full support
    wall = box(0.15, 0.8, 0, 0.3, 0.3, 0.6)      # sibling occupying the middle
    moves = solve_stability(support, [hang, wall])
    dxh = moves[0][0]
    check("partial move, no collision", -0.2 < dxh < 0.0, f"(dx {dxh:+.3f})")
    moved = _fp(box(0.55 + dxh, 0.8, 0, 0.3, 0.3, 0.3))
    from IDSDL.stability import _collides
    check("no sibling intersection", not _collides(moved, [_fp(wall)]))
    check("sibling untouched", moves[1] == (0.0, 0.0))

    # d. stable object untouched
    obj = box(0.1, 0.8, 0, 0.3, 0.3, 0.3)
    (dx, dz), = solve_stability(support, [obj])
    check("stable untouched", (dx, dz) == (0.0, 0.0))

    # e. different heights don't block (lamp over low tray)
    hang = box(0.55, 0.8, 0, 0.3, 0.3, 0.3)
    low = box(0.15, 0.0, 0, 0.3, 0.3, 0.6)       # on the floor, no y overlap
    moves = solve_stability(support, [hang, low])
    check("no block across heights", abs(moves[0][0] + 0.2) < 0.06,
          f"(dx {moves[0][0]:+.3f}, want ~-0.2)")


def dsl_test():
    print("[DSL fallback smoke]")
    import trimesh
    from IDSDL.scene import SceneProgRoom
    from IDSDL.vlm_scale import _baked
    from tools.scale_solver import render_corner
    from tools.planar_regions import _GLB2BLEND, glb_to_blend

    OUT = "/work/tmp/stabtest"
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "_glb2blend.py"), "w") as f:
        f.write(_GLB2BLEND)

    scene = SceneProgRoom("stabtest", seed=42)
    ns = scene.AddAsset("a classic dark wood nightstand",
                        asset_id="hssd/830e2ed47548d8372294609fe7eeca11fb384b29")
    lamp = scene.AddAsset("a classic urn table lamp with a pleated shade",
                          asset_id="hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed")
    with scene.RelativeGroup() as g:
        g.set_anchor(ns)
        g.place_on_top([lamp])

    def render(tag):
        sc = trimesh.Scene()
        for i, o in enumerate((ns, lamp)):
            for j, geom in enumerate(_baked(o).dump()):
                sc.add_geometry(geom, geom_name=f"o{i}_{j}")
        glb = os.path.join(OUT, f"{tag}.glb")
        sc.export(glb)
        render_corner(glb_to_blend(glb, OUT), os.path.join(OUT, f"{tag}.png"), sc.bounds)

    def ratio():
        return overlap_ratio(_fp(lamp.get_aabb()), _fp(ns.get_aabb()))

    check("fallback placement stable", ratio() >= STABLE_OVERLAP, f"(ratio {ratio():.2f})")

    # drag the lamp half off the +x edge, then stabilize
    w = float(ns.get_aabb()[1][0] - ns.get_aabb()[0][0])
    lamp.translate(w * 0.55, 0, 0)
    r_before = ratio()
    render("overhang")
    n = stabilize_objects(ns, [lamp], log=print)
    r_after = ratio()
    render("stabilized")
    check("overhang detected", r_before < 0.7, f"(ratio {r_before:.2f})")
    check("nudged back", n == 1 and r_after >= STABLE_OVERLAP,
          f"(ratio {r_before:.2f} -> {r_after:.2f})")
    gap = float(lamp.get_aabb()[0][1] - ns.get_aabb()[1][1])
    check("still seated", abs(gap) < 0.02, f"(gap {gap:+.3f})")
    print(f"  renders in {OUT}/ (overhang.png, stabilized.png)")


def main():
    pure_tests()
    dsl_test()
    print("\nPASS" if not FAILURES else f"\nFAIL: {FAILURES}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
