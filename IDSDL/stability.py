"""Support-stability pass for placed objects (place_on_top / place_inside).

The VLM placement tournament judges visibility and being-on-the-right-surface,
not physics — an edge tile can win with the object half off the support, where
in reality it would fall. This pass runs AFTER placements are confirmed: any
object whose XZ footprint overlaps the support's footprint below a threshold is
nudged by the MINIMAL translation that restores support, but never so far that
it intersects a sibling — the move is line-searched down and, if even a small
step collides, the object stays where the tournament put it.

Pure AABB math, no renders, no LLM — cheap enough to run on every placement.
"""
import numpy as np

# Footprint overlap ratio (object area covered by the support) at or above
# which an object counts as stably supported.
STABLE_OVERLAP = 0.90
# Sibling footprints may touch; intersection AREA above this fraction of the
# smaller footprint counts as a collision.
COLLISION_FRAC = 0.02
LINE_SEARCH = (1.0, 0.85, 0.7, 0.55, 0.4, 0.25, 0.12)


def _fp(aabb):
    """(xmin, zmin, xmax, zmax) footprint of a world AABB [[min],[max]]."""
    return (float(aabb[0][0]), float(aabb[0][2]),
            float(aabb[1][0]), float(aabb[1][2]))


def _area(fp):
    return max(0.0, fp[2] - fp[0]) * max(0.0, fp[3] - fp[1])


def _inter(a, b):
    return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))


def overlap_ratio(fp, support):
    """Fraction of fp's area covered by the support footprint."""
    a = _area(fp)
    return _area(_inter(fp, support)) / a if a > 1e-9 else 1.0


def _shift(fp, dx, dz):
    return (fp[0] + dx, fp[1] + dz, fp[2] + dx, fp[3] + dz)


def _clamp_move(fp, support):
    """Minimal (dx, dz) that brings fp inside the support (centers any axis
    where fp is wider than the support — the best achievable)."""
    def axis(lo, hi, slo, shi):
        if hi - lo > shi - slo:
            return (slo + shi) / 2 - (lo + hi) / 2
        if lo < slo:
            return slo - lo
        if hi > shi:
            return shi - hi
        return 0.0
    return (axis(fp[0], fp[2], support[0], support[2]),
            axis(fp[1], fp[3], support[1], support[3]))


def _collides(fp, others):
    for o in others:
        inter = _area(_inter(fp, o))
        if inter > COLLISION_FRAC * max(1e-9, min(_area(fp), _area(o))):
            return True
    return False


def _y_overlaps(a, b):
    return a[0][1] < b[1][1] - 1e-4 and b[0][1] < a[1][1] - 1e-4


def solve_stability(support_aabb, obj_aabbs, threshold=STABLE_OVERLAP):
    """Return per-object (dx, dz) nudges restoring support stability.

    support_aabb: world AABB of the support (anchor); obj_aabbs: world AABBs of
    the placed objects. Objects are processed worst-ratio-first and see the
    already-moved positions of the others; a move is only taken at the largest
    line-search fraction that improves the ratio without colliding with any
    sibling whose vertical range overlaps.
    """
    support = _fp(support_aabb)
    fps = [_fp(a) for a in obj_aabbs]
    moves = [(0.0, 0.0)] * len(obj_aabbs)
    order = sorted(range(len(fps)), key=lambda i: overlap_ratio(fps[i], support))
    for i in order:
        r0 = overlap_ratio(fps[i], support)
        if r0 >= threshold:
            continue
        dx, dz = _clamp_move(fps[i], support)
        if abs(dx) < 1e-6 and abs(dz) < 1e-6:
            continue
        siblings = [fps[j] for j in range(len(fps))
                    if j != i and _y_overlaps(obj_aabbs[i], obj_aabbs[j])]
        for t in LINE_SEARCH:
            cand = _shift(fps[i], t * dx, t * dz)
            if overlap_ratio(cand, support) > r0 and not _collides(cand, siblings):
                moves[i] = (t * dx, t * dz)
                fps[i] = cand
                break
    return moves


def stabilize_objects(anchor, objs, threshold=None, log=None):
    """Apply solve_stability to DSL objects placed on/in ``anchor`` (in-place).

    Returns the number of objects moved. Frames: called at compile time, when
    the group's parent is identity — world AABBs and local translate() agree,
    the same assumption the place_* machinery itself relies on.
    """
    if not objs:
        return 0
    threshold = STABLE_OVERLAP if threshold is None else threshold
    support = anchor.get_aabb()
    aabbs = [o.get_aabb() for o in objs]
    moved = 0
    for o, a, (dx, dz) in zip(objs, aabbs, solve_stability(support, aabbs, threshold)):
        if abs(dx) < 1e-6 and abs(dz) < 1e-6:
            continue
        before = overlap_ratio(_fp(a), _fp(support))
        o.translate(dx, 0.0, dz)
        after = overlap_ratio(_fp(o.get_aabb()), _fp(support))
        moved += 1
        if log:
            log(f"  [stability] {str(o.description)[:40]!r} nudged "
                f"({dx:+.3f}, {dz:+.3f}) m; support {before:.2f} -> {after:.2f}")
    return moved
