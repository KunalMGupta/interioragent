"""Bedroom test case for the VLM proposal/critic scale solver (tools/scale_solver.py).

A double bed flanked by two nightstands with a table lamp on each — with the
nightstands DELIBERATELY inflated 1.45x and the lamps 1.7x before the solve, so
factors (1.0, 1.0) reproduce the classic mis-retrieval look (nightstands rivalling
the bed, monster lamps). Success = the solver walks the satellites back to
believable sizes (nightstand top near the mattress, lamp proportionate) without
inflating the bed to compensate.

Run:
  set -a && source /work/.env && set +a
  BLENDER_PATH=/work/blender-4.5.4-linux-x64/blender PYTHONPATH=/work \
    /opt/conda/envs/interioragent/bin/python tools/scale_tournament_test.py

Artifacts in /work/tmp/scaletest: initial.png / final.png (before/after),
evolution.png (every candidate by round, champions outlined), match_log.json
(every pairwise verdict — the proposer's context memory, auditable).

Renders are fully textured 3/4 corner views (see scale_solver.render_corner) —
material cues plus the numeric dims give the judge the most scale signal.
"""
import os
import sys
sys.path.insert(0, "/work")

import numpy as np
import trimesh

from IDSDL.scene import SceneProgRoom
from tools.scale_solver import solve_relative_scales

OUT = "/work/tmp/scaletest"

NIGHTSTAND = "hssd/830e2ed47548d8372294609fe7eeca11fb384b29"
LAMP = "hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed"

# The injected retrieval errors the solver must discover and undo.
NIGHTSTAND_INFLATE = 1.45
LAMP_INFLATE = 1.7

SCENE_DESC = ("a cozy bedroom ensemble: a double bed flanked by two matching "
              "nightstands, with a table lamp on each nightstand")


def bake(obj):
    """Object's world mesh WITH MATERIALS, re-based: centered in x/z, on y=0.

    obj.vertices are the raw GLB vertices — all DSL normalization lives in the
    transform chain — so loading the same GLB as a textured Scene and applying
    get_world_transform() reproduces the geometry exactly, textures intact.
    (Texture cues — wood grain, fabric, shade pleats — carry real scale signal
    for the judge; the earlier all-gray bakes threw that away.)
    """
    sc = trimesh.load(obj.mesh_path)
    if not isinstance(sc, trimesh.Scene):
        sc = trimesh.Scene(sc)
    sc.apply_transform(obj.get_world_transform().compute_matrix())
    lo, hi = sc.bounds
    sc.apply_translation([-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2])
    return sc


def scaled(mesh, f):
    m = mesh.copy()
    m.apply_transform(np.diag([f["s"], f["s"] * f["h"], f["s"], 1.0]))
    return m  # scaling about the origin keeps it centered and floored


def merge(master, member_scene, prefix):
    """Add a (transformed) member Scene's geometry into the master scene."""
    for i, g in enumerate(member_scene.dump()):
        master.add_geometry(g, geom_name=f"{prefix}_{i}")


def main():
    os.makedirs(OUT, exist_ok=True)
    scene = SceneProgRoom("scaletest", seed=42)
    bed_obj = scene.AddAsset("a modern double bed with a wooden frame and a headboard")
    ns_obj = scene.AddAsset("a classic dark wood nightstand", asset_id=NIGHTSTAND)
    lamp_obj = scene.AddAsset("a classic urn table lamp with a pleated shade",
                              asset_id=LAMP)
    print(f"bed asset: {bed_obj.retrieval_model}")

    bed = bake(bed_obj)
    ns = bake(ns_obj)
    ns.apply_scale(NIGHTSTAND_INFLATE)
    lamp = bake(lamp_obj)
    lamp.apply_scale(LAMP_INFLATE)

    def whd(m):
        lo, hi = m.bounds
        return (float(hi[0] - lo[0]), float(hi[1] - lo[1]), float(hi[2] - lo[2]))

    members = [
        {"name": "bed", "desc": "a modern double bed with headboard", "role": "anchor",
         "whd": whd(bed), "mesh": bed},
        {"name": "nightstand", "desc": "a classic dark wood nightstand",
         "role": "satellite", "whd": whd(ns), "mesh": ns,
         "note": "two identical copies flank the bed"},
        {"name": "lamp", "desc": "a classic urn table lamp with a pleated shade",
         "role": "satellite", "whd": whd(lamp), "mesh": lamp,
         "note": "one on each nightstand, must sit believably on its top"},
    ]
    print("starting dims (deliberately mis-scaled satellites):")
    for m in members:
        w, h, d = m["whd"]
        print(f"  {m['name']:11s} {w:.2f}w x {h:.2f}h x {d:.2f}d m")

    def build(factors):
        b = scaled(bed, factors["bed"])
        blo, bhi = b.bounds
        sc = trimesh.Scene()
        merge(sc, b, "bed")
        n0 = scaled(ns, factors["nightstand"])
        nlo, nhi = n0.bounds
        # snug floor: just past the nightstands, so the slab doesn't dominate the
        # scene bounds and push the corner camera back out
        outer_x = (bhi[0] - blo[0]) / 2 + (nhi[0] - nlo[0]) + 0.06
        floor = trimesh.creation.box(
            extents=[2 * outer_x + 0.4, 0.02, (bhi[2] - blo[2]) + 0.6])
        floor.apply_translation([0, -0.01, 0])
        sc.add_geometry(floor, geom_name="floor")
        # flush beside the bed, centers aligned with the headboard end of the bed
        z_ns = blo[2] + (nhi[2] - nlo[2]) / 2
        for side, tag in ((-1, "L"), (1, "R")):
            n = n0.copy()
            x = side * ((bhi[0] - blo[0]) / 2 + (nhi[0] - nlo[0]) / 2 + 0.06)
            n.apply_translation([x, 0, z_ns])
            merge(sc, n, f"nightstand_{tag}")
            l = scaled(lamp, factors["lamp"])
            l.apply_translation([x, nhi[1] - nlo[1], z_ns])
            merge(sc, l, f"lamp_{tag}")
        return sc

    best, match_log = solve_relative_scales(
        members, build, SCENE_DESC, OUT, rounds=3, k=4)

    print("\nfinal dims:")
    for m in members:
        f = best[m["name"]]
        w, h, d = m["whd"]
        print(f"  {m['name']:11s} s={f['s']:.2f} h={f['h']:.2f} -> "
              f"{w * f['s']:.2f}w x {h * f['s'] * f['h']:.2f}h x {d * f['s']:.2f}d m")
    print(f"\n{len(match_log)} pairwise verdicts collected; see {OUT}/match_log.json")


if __name__ == "__main__":
    main()
