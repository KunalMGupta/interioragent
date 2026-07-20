"""VLM-tournament placement for place_on_top / place_inside, with AABB fallback.

Renders candidate arrangements of small objects on/inside an anchor and uses a VLM
value-iteration tournament (see tools/planar_regions.py) to pick the best, then applies the
winning transforms to the DSL objects. This is the *primary* path; it is heavy (needs
Blender + a render device + OPENAI_API_KEY), so any failure returns False and the caller falls
back to the deterministic AABB placement. Disable globally with env IDSDL_SMART_PLACEMENT=0.
Select the preview device with IDSDL_SMART_PLACEMENT_DEVICE=auto|cpu|gpu.

Frame: at place_* compile time the group's parent is identity, so the anchor's world mesh is
exported as the solver's base frame; the per-item placements come back in that same frame and
are applied with the usual setters (set_location/set_rotation/transform.set_scale), exactly
like the AABB path.
"""
import os
import tempfile

import numpy as np
import trimesh


def smart_enabled():
    return os.environ.get("IDSDL_SMART_PLACEMENT", "1").lower() not in ("0", "false", "no", "")


def _anchor_base_glb(anchor, out_dir):
    """Export the anchor's current world mesh to a GLB (the solver's base frame)."""
    verts = anchor.get_world_transform().transform_points(anchor.vertices)
    mesh = trimesh.Trimesh(vertices=verts, faces=anchor.faces, process=False)
    path = os.path.join(out_dir, "anchor_base.glb")
    mesh.export(path)
    return path


def place_smart(group, anchor, objs, mode, *, generations=2, k=8, seed=42,
                res=384, samples=8, workers=10, render_workers=3, log=None):
    """Try VLM-tournament placement of objs on/in anchor. Returns True on success.

    On success each obj is scaled, rotated, located, flagged ignore_overlap and added as a
    child of ``group`` (mirroring place_on_top's bookkeeping). On any problem -> False.
    """
    log = log or (lambda *a: None)
    if not smart_enabled() or anchor is None:
        return False
    if getattr(anchor, "vertices", None) is None or getattr(anchor, "faces", None) is None:
        return False  # anchor must be a single mesh (groups aren't supported here)
    if not all(getattr(o, "mesh_path", None) for o in objs):
        return False
    try:
        from tools.planar_regions import solve_placement
    except Exception:
        return False

    out_dir = tempfile.mkdtemp(prefix="idsdl_place_")
    try:
        base = _anchor_base_glb(anchor, out_dir)
        anchor_desc = anchor.get_descriptions() or getattr(anchor, "name", None) or "furniture"
        specs = [(o.mesh_path, (o.description or getattr(o, "name", None) or "object"))
                 for o in objs]
        placements = solve_placement(base, anchor_desc, specs, mode=mode, out_dir=out_dir,
                                     name="dsl", generations=generations, k=k, seed=seed,
                                     res=res, samples=samples, workers=workers,
                                     render_workers=render_workers, log=log)
        if len(placements) != len(objs):
            return False
        for obj, p in zip(objs, placements):
            h = obj.get_height()
            if h > 0 and p["h"] > 0:                       # uniform scale to the solved height
                f = p["h"] / h
                cur = obj.transform.scale
                obj.transform.set_scale([cur[0] * f, cur[1] * f, cur[2] * f])
            obj.set_rotation(float(np.degrees(p["yaw"])))
            obj.set_location(p["x"], p["surface_y"] + group.compute_obj_y(obj), p["z"])
            obj.ignore_overlap = True
            group.add_child(obj)
        log(f"  [smart {mode} placement applied to {len(objs)} object(s)]")
        return True
    except Exception as e:
        log(f"  [smart placement failed: {e!r}; falling back to AABB]")
        return False
