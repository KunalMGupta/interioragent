"""Deterministic lints — cheap, render-free checks for the failure classes that
history shows get caught LATE (from a 6-minute build's renders) when they could be
caught in milliseconds.

Two independent layers:

1. ``run_room_lints(room)`` — post-compile geometric lints, called by
   ``RoomGroup.compile`` after the solve settles (same station as
   ``_warn_over_height`` / ``_warn_overlaps``). Advisory only: they print and append
   to ``scene.vlm_feedback`` so the workbench report surfaces them; they never move
   anything. Disable with ``IDSDL_LINTS=0``.
   - floater/sunk: a floor object whose AABB bottom is off the floor (the classic
     off-center-mesh-origin trap — the fix is usually to SWAP the mesh).
   - lighting starfield: ceiling-fixture count far beyond the room's area budget
     (an ``add_lighting`` density an order of magnitude too high).

2. ``lint_program(source)`` — static AST validation of a scene program against the
   REAL API surface (introspected, not hand-listed): unknown methods on scene /
   group / asset variables and unknown keyword arguments. Catches invented verbs
   (``place_on_left_adjacent``) and invented kwargs (``add_lighting(asset_id=...)``,
   ``AroundGroup(modulate_scale=...)``) before a build is ever attempted.
"""
import ast
import difflib
import inspect
import os


def lints_enabled() -> bool:
    return os.environ.get("IDSDL_LINTS", "1") != "0"


# ---------------------------------------------------------------------------
# 1. post-compile geometric lints
# ---------------------------------------------------------------------------

FLOAT_TOL = 0.05          # m — floor objects should rest within this of y=0
LIGHTS_PER_M2_CAP = 0.3   # fixtures per m^2 of floor beyond which it's a starfield
LIGHTS_MIN_CAP = 8        # never flag small absolute counts
EMBED_TOL = 0.05          # m — penetration on ALL THREE axes before it's a real intersection


def _label(obj):
    return (getattr(obj, "retrieval_query", None) or getattr(obj, "name", None)
            or obj.__class__.__name__)


def lint_floaters(room, tol=FLOAT_TOL):
    """Flag room-level floor children whose AABB bottom is off the floor.

    Floor furniture (and frozen groups of it) is placed resting on y=0; a bottom
    above that means the object will render hovering (typically an off-center mesh
    origin — swap the mesh rather than compensate), below it means it is sunk into
    the floor. Exempt: wall-MOUNTED items, which hang at height by design (they are
    room children too, marked ignore_overlap by _place_on_wall — so ignore_overlap
    children are skipped, which floor furniture never sets), ceiling lights, door
    proxies, and scene.wall_objects (doors/windows/curtains). NOTE: this trusts the
    asset's own AABB; a mesh whose AABB disagrees with its render geometry can
    still float (verify in the blend)."""
    scene = getattr(room, "scene", None)
    wall_items = {id(w) for w in getattr(scene, "wall_objects", []) or []}
    msgs = []
    for c in getattr(room, "children", []):
        if getattr(c, "is_proxy", False) or getattr(c, "is_light", False) \
                or getattr(c, "ignore_overlap", False) or id(c) in wall_items:
            continue
        try:
            bottom = float(c.get_aabb()[0, 1])
        except Exception:
            continue
        if bottom > tol:
            msgs.append(f"'{_label(c)[:48]}' FLOATS {bottom:.2f} m above the floor "
                        f"(AABB bottom should be ~0). Usual cause: off-center mesh "
                        f"origin — swap the mesh, don't compensate.")
        elif bottom < -tol:
            msgs.append(f"'{_label(c)[:48]}' is SUNK {-bottom:.2f} m into the floor "
                        f"(AABB bottom should be ~0).")
    return msgs


def lint_lighting(room):
    """Flag a ceiling-fixture count far beyond the room's area budget.

    add_lighting places 1+(max_lights-1)*density fixtures, and max_lights scales
    with room area / fixture footprint — so a density that reads "small" (0.05) can
    still mean dozens of fixtures. A calm room wants well under ~0.3 fixtures/m^2."""
    lights = list(getattr(getattr(room, "scene", None), "ceiling_lights", []) or [])
    n = len(lights)
    if n == 0:
        return []
    area = float(getattr(room, "WIDTH", 0.0)) * float(getattr(room, "DEPTH", 0.0))
    if area <= 0:
        return []
    cap = max(LIGHTS_MIN_CAP, int(round(area * LIGHTS_PER_M2_CAP)))
    if n <= cap:
        return []
    return [f"{n} ceiling fixtures on a {area:.0f} m^2 room is a STARFIELD "
            f"(area budget ~{cap}). Count = 1+(max_lights-1)*density: use density "
            f"0.01-0.02 for a small room, ~0.05 for a medium one."]


def _ancestry(obj):
    """ids of obj and every ancestor (an on-top prop's parent chain reaches its anchor)."""
    out, p = set(), obj
    while p is not None and id(p) not in out:
        out.add(id(p))
        p = getattr(p, "parent", None)
    return out


def lint_embedded_wall_objects(room, tol=EMBED_TOL):
    """Flag a wall-mounted / ignore_overlap object INTERSECTING another object in 3D.

    THE SOLVER'S BLIND SPOT. Every overlap check in the room is 2D-footprint AND drops
    ignore_overlap items: `GradSolver.overlap_pairs` (which backs the residual-overlap
    warning) filters them out by construction, the gradient solve never pushes them, and
    `_snap_overlaps` / `_clamp_to_bounds` skip them too. That flag is *necessary* on
    wall-mounted pieces — a shelf lifted with `bottom=` is registered as floor furniture, so
    without it the 2D solver sees a shelf and the cabinet beneath/beside it as interpenetrating
    and shoves them apart along the wall (and on a stacked run, shoves the stack apart). But
    the flag is a blanket exemption: once set, NOTHING ever looks at that object again, so a
    floor cabinet is free to drift along the wall straight INTO a mounted shelf and no signal
    fires. Seen in closet v1: a wall-mounted clothes shelf ended 0.45 m inside a wardrobe bay
    while the whole VLM loop reported `no rescale / no rotation / no wall overlap`.

    So: check exactly the pairs the solver refuses to. Full 3D AABB (a shelf ABOVE a console
    is legal and must stay silent — that is the whole reason the 2D test can't be reused), and
    only pairs where at least one party is ignore_overlap. Parent/child pairs are skipped: a
    `place_on_top` prop is *supposed* to intersect the anchor it rests on.

    Advisory, like every lint here — there is no safe auto-fix (sliding a mounted piece would
    fight `_repin_wall_furniture`, and shrinking it is the author's call). The fix is in the
    program: move one to a different wall slot, change its `bottom=`, mark the drifting floor
    piece `is_static`, or shrink it."""
    scene = getattr(room, "scene", None)
    wall_items = {id(w) for w in getattr(scene, "wall_objects", []) or []}   # doors/windows/curtains

    def eligible(c):
        return not (getattr(c, "is_proxy", False) or getattr(c, "is_light", False)
                    or id(c) in wall_items)

    children = [c for c in getattr(room, "children", []) if eligible(c)]
    ignored = [c for c in children if getattr(c, "ignore_overlap", False)]
    msgs, seen = [], set()
    for a in ignored:
        anc_a = _ancestry(a)
        for b in children:
            if a is b or id(b) in anc_a or id(a) in _ancestry(b):
                continue
            key = tuple(sorted((id(a), id(b))))
            if key in seen:
                continue
            try:
                (ax0, ay0, az0), (ax1, ay1, az1) = a.get_aabb()
                (bx0, by0, bz0), (bx1, by1, bz1) = b.get_aabb()
            except Exception:
                continue
            ox = float(min(ax1, bx1) - max(ax0, bx0))
            oy = float(min(ay1, by1) - max(ay0, by0))
            oz = float(min(az1, bz1) - max(az0, bz0))
            if ox <= tol or oy <= tol or oz <= tol:
                continue          # no 3D intersection (a shelf over a console lands here)
            seen.add(key)
            both = getattr(b, "ignore_overlap", False)
            msgs.append(
                f"'{_label(a)[:36]}' (wall-mounted/ignore_overlap) is EMBEDDED IN "
                f"'{_label(b)[:36]}'{' (also ignore_overlap)' if both else ''} — they "
                f"interpenetrate {ox:.2f}x{oy:.2f}x{oz:.2f} m (w x h x d). ignore_overlap "
                f"items are invisible to the overlap solver, so NOTHING pushed them apart. "
                f"Fix in the program: move one to a different wall slot, change its bottom= "
                f"height, mark the floor piece is_static (it drifted), or shrink one of them.")
    return msgs


def run_room_lints(room):
    """Run all geometric lints; print + record in scene.vlm_feedback. Returns msgs."""
    if not lints_enabled():
        return []
    msgs = lint_floaters(room) + lint_lighting(room) + lint_embedded_wall_objects(room)
    if not msgs:
        return []
    text = "\n".join(f"[Lint] {m}" for m in msgs)
    print(text)
    scene = getattr(room, "scene", None)
    if scene is not None and hasattr(scene, "vlm_feedback"):
        scene.vlm_feedback += ("\n" if scene.vlm_feedback else "") + text
    return msgs


# ---------------------------------------------------------------------------
# 2. static program lint (AST vs the real API surface)
# ---------------------------------------------------------------------------

def _api_surface():
    """Introspect the live classes once: {type_key: (class, allowed_methods)}.

    type_key is one of "scene", "object", or a group-factory name ("RelativeGroup",
    "RoomGroup", ...). Group method sets include the dynamically-bound constraint
    names (ClearanceConstraint etc.), which live on instances, not classes."""
    from IDSDL.scene import SceneProgRoom
    from IDSDL.object import SceneProgObject
    from IDSDL import groups as _groups
    from IDSDL import groups_extra as _extra
    from IDSDL.constraints import CONSTRAINTS

    constraint_names = {c.__name__ for c in CONSTRAINTS}

    def methods(cls, with_constraints=False):
        out = {m for m in dir(cls) if not m.startswith("_")}
        if with_constraints:
            out |= constraint_names
        return out

    surface = {
        "scene": (SceneProgRoom, methods(SceneProgRoom)),
        "object": (SceneProgObject, methods(SceneProgObject, with_constraints=True)),
    }
    for fname, fn in inspect.getmembers(SceneProgRoom, inspect.isfunction):
        if fname.startswith("_"):
            continue
        cls = getattr(_groups, fname, None) or getattr(_extra, fname, None)
        if cls is not None and inspect.isclass(cls):
            surface[fname] = (cls, methods(cls, with_constraints=True))
    return surface


def _kwarg_errors(holder_classes, method_name, call, type_label):
    """Unknown-keyword check for a call: a keyword is flagged only when NO holder
    class accepts it. Skipped entirely if any holder takes **kwargs."""
    valid = set()
    for cls in holder_classes:
        fn = getattr(cls, method_name, None)
        if fn is None:
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return []
        if any(p.kind is inspect.Parameter.VAR_KEYWORD
               for p in sig.parameters.values()):
            return []
        valid |= {n for n in sig.parameters if n not in ("self", "cls")}
    errs = []
    for kw in call.keywords:
        if kw.arg is not None and kw.arg not in valid:
            hint = difflib.get_close_matches(kw.arg, sorted(valid), n=1)
            errs.append(f"line {call.lineno}: {type_label}.{method_name}() has no "
                        f"keyword '{kw.arg}'"
                        + (f" — did you mean '{hint[0]}'?" if hint else
                           f" (accepts: {', '.join(sorted(valid))})"))
    return errs


def lint_program(source, filename="<program>"):
    """Statically validate a scene program against the real API. Returns a list of
    error strings (empty = clean). Purely syntactic/name-level: it types variables
    it can prove (scene = SceneProgRoom(...), `with scene.X() as g`, asset
    assignments, N * group duplication) and stays silent about the rest — no false
    positives on code it can't follow."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        return [f"line {e.lineno}: syntax error: {e.msg}"]

    surface = _api_surface()
    errors = []
    var_types = {}   # var name -> SET of possible type_keys (names get reused
                     # across helper functions, so a flat namespace must validate
                     # against the union of everything the name is bound to)

    def _bind(name, tkey):
        var_types.setdefault(name, set()).add(tkey)

    def type_of_call(call):
        """type_key produced by a call expression, if we can prove it."""
        f = call.func
        if isinstance(f, ast.Name) and f.id == "SceneProgRoom":
            return "scene"
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            owners = var_types.get(f.value.id, set())
            if "scene" in owners:
                if f.attr in surface:          # group factory
                    return f.attr
                if f.attr == "AddAsset":
                    return "object"
        return None

    def check_call(call):
        f = call.func
        if not (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)):
            return
        tkeys = var_types.get(f.value.id)
        if not tkeys:
            return
        allowed = set().union(*(surface[t][1] for t in tkeys))
        classes = [surface[t][0] for t in tkeys]
        label = f.value.id if tkeys <= {"scene", "object"} else "/".join(sorted(tkeys))
        if f.attr not in allowed:
            hint = difflib.get_close_matches(f.attr, sorted(allowed), n=2)
            errors.append(f"line {call.lineno}: {label} "
                          f"({'/'.join(c.__name__ for c in classes)}) has no "
                          f"method '{f.attr}'"
                          + (f" — did you mean {' / '.join(hint)}?" if hint else ""))
            return
        errors.extend(_kwarg_errors(classes, f.attr, call, label))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            t = type_of_call(node.value)
            if t is not None:
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        _bind(tgt.id, t)
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.BinOp) \
                and isinstance(node.value.op, ast.Mult):
            # tt_a, tt_b = 2 * unit  → copies share the unit's type
            operands = (node.value.left, node.value.right)
            src = next((o for o in operands if isinstance(o, ast.Name)
                        and o.id in var_types), None)
            if src is not None:
                for tgt in node.targets:
                    names = tgt.elts if isinstance(tgt, ast.Tuple) else [tgt]
                    for n in names:
                        if isinstance(n, ast.Name):
                            for t in var_types[src.id]:
                                _bind(n.id, t)
        elif isinstance(node, ast.With):
            for item in node.items:
                ctx = item.context_expr
                if isinstance(ctx, ast.Call) and item.optional_vars is not None \
                        and isinstance(item.optional_vars, ast.Name):
                    t = type_of_call(ctx)
                    if t is not None:
                        _bind(item.optional_vars.id, t)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            check_call(node)

    return errors


def lint_program_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return lint_program(f.read(), filename=str(path))
