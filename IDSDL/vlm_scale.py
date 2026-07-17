"""VLM proposal/critic relative-scale solve for anchor groups.

Adapter between the DSL and tools/scale_solver.py (see that module and
docs/vlm_placement_and_scale.md for the algorithm and its validation — a
23-scene injected-corruption benchmark). Opt-in per group:

    with scene.AroundGroup(...) as bar:
        bar.set_anchor(counter)
        bar.place_rectilinear(...)
    bar.solve_scales()          # optional post-compile refinement

Cost: ~10-15 textured renders + ~30-45 LLM calls per group (minutes), so it is
NEVER automatic. Disable globally with IDSDL_SMART_SCALE=0 (kill switch for
harness runs). Any failure logs and returns None without touching the scene —
factors are only applied after the whole solve succeeds, then the group is
recompiled so placements re-solve against the new sizes (add_lighting is NOT
re-executed on that recompile: it would retrieve duplicate fixtures; existing
lights are kept where they are, and lights/rugs are exempt from scaling).

Member model: leaf mesh objects are collected recursively (nested composed
groups are walked through) and deduped into members by (mesh_path, current
scale) — symmetric duplicates share one factor. The member containing the
group's anchor gets tight bounds; everything else gets the wide satellite band.
Candidate scenes for the solver scale each instance about its own footprint
center and re-seat it on its support (floor, or the member top it stood on),
with stacked items following a scaling support — approximate contacts, good
enough to judge relative size; the authoritative layout comes from the DSL
recompile afterwards.
"""
import os
import re
import tempfile

import numpy as np
import trimesh

# Satellites search a wide symmetric band (real retrieval errors run 2-3x);
# the anchor member stays tight — the room is solved around its footprint.
SAT_BOUNDS = (0.35, 2.2, 0.70, 1.40)


def smart_scale_enabled():
    return os.environ.get("IDSDL_SMART_SCALE", "1").lower() not in ("0", "false", "no")


def _leaf_objects(node, out):
    for child in getattr(node, "children", []) or []:
        if getattr(child, "vertices", None) is not None:
            out.append(child)
        if getattr(child, "children", None):
            _leaf_objects(child, out)
    return out


def _descendant_groups(node, out):
    for child in getattr(node, "children", []) or []:
        if getattr(child, "children", None):
            out.append(child)
            _descendant_groups(child, out)
    return out


def _slug(desc, taken):
    words = [w for w in re.findall(r"[a-z]+", str(desc).lower())
             if w not in ("a", "an", "the", "of", "with", "and", "in", "on")]
    # first word + head noun (usually last) keeps names readable: "classic_nightstand"
    base = ("_".join([words[0], words[-1]]) if len(words) > 1
            else (words[0] if words else "member"))
    slug, i = base, 2
    while slug in taken:
        slug, i = f"{base}{i}", i + 1
    return slug


def _baked(obj):
    """Object's CURRENT world mesh with materials (textured trimesh Scene)."""
    sc = trimesh.load(obj.mesh_path)
    if not isinstance(sc, trimesh.Scene):
        sc = trimesh.Scene(sc)
    sc.apply_transform(obj.get_world_transform().compute_matrix())
    return sc


def solve_group_scales(group, rounds=3, k=4, out_dir=None, apply=True,
                       log=print, **solver_kw):
    """Run the scale search on a compiled anchor group. Returns the winning
    factors dict ({member: {'s','h'}}) or None (disabled / failed / nothing to do)."""
    if not smart_scale_enabled():
        return None
    try:
        from tools.scale_solver import solve_relative_scales
    except Exception as e:
        log(f"[solve_scales] solver unavailable ({e!r}); skipping")
        return None

    anchor = getattr(group, "anchor", None)
    objs = [o for o in _leaf_objects(group, [])
            if not getattr(o, "scale_solve_exempt", False)
            and getattr(o, "light_energy", None) is None]  # duplicated fixtures
                                                           # don't inherit the mark
    if len(objs) < 2:
        log("[solve_scales] fewer than two scalable members; skipping")
        return None

    # anchor leaves: the anchor object itself, or every leaf under a group anchor
    anchor_leaves = set()
    if anchor is not None:
        anchor_leaves = ({id(anchor)} if getattr(anchor, "vertices", None) is not None
                         else {id(o) for o in _leaf_objects(anchor, [])})

    # dedupe instances into members
    members, instances, by_key, taken = [], {}, {}, set()
    for o in objs:
        key = (o.mesh_path, tuple(np.round(np.asarray(o.transform.scale, float), 3)))
        if key in by_key:
            instances[by_key[key]].append(o)
            continue
        aabb = o.get_aabb()
        whd = tuple(float(aabb[1][i] - aabb[0][i]) for i in range(3))
        role = "anchor" if id(o) in anchor_leaves else "satellite"
        name = _slug(o.description or o.name, taken)
        taken.add(name)
        by_key[key] = name
        instances[name] = [o]
        members.append({
            "name": name, "desc": str(o.description or o.name), "role": role,
            "whd": whd, "bounds": None if role == "anchor" else SAT_BOUNDS,
        })
    for m in members:
        n = len(instances[m["name"]])
        if n > 1:
            m["note"] = f"{n} identical copies in the arrangement"

    # per-instance bases + support graph from the CURRENT compiled layout
    inst_list = [(m["name"], o) for m in members for o in instances[m["name"]]]
    bases = {}
    for name, o in inst_list:
        sc = _baked(o)
        lo, hi = sc.bounds
        cx, cz, bottom = float(lo[0] + hi[0]) / 2, float(lo[2] + hi[2]) / 2, float(lo[1])
        sc.apply_translation([-cx, -lo[1], -cz])
        bases[id(o)] = {"scene": sc, "cx": cx, "cz": cz, "bottom": bottom,
                        "top": float(hi[1]), "lo": lo, "hi": hi, "name": name}
    floor_y = min(b["bottom"] for b in bases.values())
    for name, o in inst_list:
        b = bases[id(o)]
        b["support"] = None
        if b["bottom"] - floor_y > 0.04:                     # stacked on something
            for name2, o2 in inst_list:
                if o2 is o:
                    continue
                s2 = bases[id(o2)]
                if abs(s2["top"] - b["bottom"]) < 0.06 \
                        and s2["lo"][0] - 0.05 <= b["cx"] <= s2["hi"][0] + 0.05 \
                        and s2["lo"][2] - 0.05 <= b["cz"] <= s2["hi"][2] + 0.05:
                    b["support"] = id(o2)
                    break

    def build(factors):
        sc = trimesh.Scene()
        order = sorted(inst_list, key=lambda no: bases[id(no[1])]["bottom"])
        new_top, new_center = {}, {}
        for i, (name, o) in enumerate(order):
            b = bases[id(o)]
            f = factors[name]
            m = b["scene"].copy()
            m.apply_transform(np.diag([f["s"], f["s"] * f["h"], f["s"], 1.0]))
            h = b["top"] - b["bottom"]
            sup = b["support"]
            if sup is not None and sup in new_top:
                fs = factors[bases[sup]["name"]]["s"]
                scx, scz = new_center[sup]
                cx = scx + (b["cx"] - bases[sup]["cx"]) * fs
                cz = scz + (b["cz"] - bases[sup]["cz"]) * fs
                y = new_top[sup]
            else:
                cx, cz, y = b["cx"], b["cz"], floor_y
            m.apply_translation([cx, y, cz])
            for j, g in enumerate(m.dump()):
                sc.add_geometry(g, geom_name=f"{name}_{i}_{j}")
            new_top[id(o)] = y + h * f["s"] * f["h"]
            new_center[id(o)] = (cx, cz)
        lo, hi = sc.bounds
        floor = trimesh.creation.box(
            extents=[float(hi[0] - lo[0]) + 0.5, 0.02, float(hi[2] - lo[2]) + 0.5])
        floor.apply_translation([float(lo[0] + hi[0]) / 2, floor_y - 0.01,
                                 float(lo[2] + hi[2]) / 2])
        sc.add_geometry(floor, geom_name="zfloor")
        return sc

    desc = getattr(group, "description", None) or (
        "a furniture arrangement: " + "; ".join(
            (f"{len(instances[m['name']])}x " if len(instances[m["name"]]) > 1 else "")
            + m["desc"] for m in members))
    out = out_dir or tempfile.mkdtemp(prefix="idsdl_scale_")

    try:
        best, _ = solve_relative_scales(members, build, desc, out,
                                        rounds=rounds, k=k, log=log, **solver_kw)
    except Exception as e:
        log(f"[solve_scales] solve failed ({e!r}); group left untouched")
        return None

    if not apply:
        return best
    changed = 0
    for m in members:
        f = best[m["name"]]
        if abs(f["s"] - 1.0) < 1e-3 and abs(f["h"] - 1.0) < 1e-3:
            continue
        for o in instances[m["name"]]:
            cur = np.asarray(o.transform.scale, dtype=float)
            o.transform.set_scale([cur[0] * f["s"], cur[1] * f["s"] * f["h"],
                                   cur[2] * f["s"]])
            o.scale_solve_locked = True   # _fit_on_top must not override this size
            changed += 1
    if changed:
        _recompile(group, log)
    log(f"[solve_scales] applied factors to {changed} object(s); artifacts in {out}")
    return best


def _recompile(group, log):
    """Re-solve the group's placements against the new sizes.

    The delayed place_* machinery assumes a group compiles BEFORE it is placed
    (parent frame identity — it mixes world-frame reads with local-frame
    writes), so each nested group is recompiled DETACHED: transform zeroed,
    compile at identity (deepest first), transform restored; the parent's main
    ops then reposition it. add_lighting is skipped (re-executing it would
    retrieve NEW fixtures — existing lights stay), and the VLM placement
    tournament is disabled for the pass (sizes are already solved; the
    deterministic AABB re-seat is all that's needed)."""
    from IDSDL.object import Transform

    def at_identity(g):
        saved = g.transform
        g.transform = Transform()
        if hasattr(g, "anchor_info"):
            g.anchor_info = None            # cached anchor dirs are stale
        g.is_frozen_group = False
        g.is_compiled = False
        g._recompile_skip = {"add_lighting"}
        try:
            g.compile()                     # re-freezes on success
        finally:
            g._recompile_skip = set()
            g.transform = saved
    saved_env = os.environ.get("IDSDL_SMART_PLACEMENT")
    os.environ["IDSDL_SMART_PLACEMENT"] = "0"
    try:
        nested = [g for g in _descendant_groups(group, [])
                  if hasattr(g, "compile")]
        for g in reversed(nested):          # deepest first
            at_identity(g)
        at_identity(group)
    finally:
        if saved_env is None:
            os.environ.pop("IDSDL_SMART_PLACEMENT", None)
        else:
            os.environ["IDSDL_SMART_PLACEMENT"] = saved_env
