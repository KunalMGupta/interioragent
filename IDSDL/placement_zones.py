"""Per-asset placement-zone annotations.

The AABB-only placement primitives (``place_on_top`` and a future ``place_inside``
/ ``place_on_shelves``) can't tell where an asset's real usable surfaces or interior
cavities are. This store records hand-drawn 3D boxes ("placement zones") per asset so a
later phase can place small objects onto the true top, onto each shelf level, or inside
a cabinet — instead of guessing from the bounding box.

It mirrors :mod:`IDSDL.front_cache`: a per-asset-id JSON keyed by the mesh filename stem
(via ``front_cache.asset_id``), authored through ``asset_browser.py``.

Coordinate frame: zone corners are stored in **raw GLB mesh-local coordinates** — the
exact frame of ``SceneProgObject.vertices`` (the trimesh ``force="mesh"`` baked verts).
Consumers transform a zone's 8 corners with the object's world transform, the same
pipeline ``get_aabb`` uses, so zones track the mesh under any scale/rotation/placement.

Zone schema (one dict per box)::

    {"name": "top",     "kind": "surface",  "min": [x, y, z], "max": [x, y, z]}
    {"name": "shelf_0", "kind": "shelf", "level": 0, "min": [...], "max": [...]}
    {"name": "interior","kind": "interior", "min": [...], "max": [...]}

``kind`` is one of ``surface`` | ``shelf`` | ``interior``; a ``shelf`` is a surface that
also carries an integer ``level``; an ``interior`` is a containing volume.

CLI::

    python -m IDSDL.placement_zones get   <asset-id-or-mesh-path>
    python -m IDSDL.placement_zones list  [--pool <id-list.json>]
    python -m IDSDL.placement_zones clear <asset-id-or-mesh-path>
"""
import json
from pathlib import Path

from IDSDL.front_cache import asset_id

ZONE_KINDS = ("surface", "shelf", "interior")

_CACHE_PATH = Path(__file__).parent / "datasets" / "placement_zones.json"
_cache = None


def _load():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_CACHE_PATH.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            _cache = {}
    return _cache


def _persist():
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(_load(), indent=2, sort_keys=True))


def _validate_zone(zone, i):
    """Normalize one zone dict; raise ValueError on malformed input."""
    if not isinstance(zone, dict):
        raise ValueError(f"zone {i} is not an object")
    kind = zone.get("kind")
    if kind not in ZONE_KINDS:
        raise ValueError(f"zone {i} has invalid kind {kind!r}; expected one of {ZONE_KINDS}")
    out = {"name": str(zone.get("name") or f"{kind}_{i}"), "kind": kind}
    for key in ("min", "max"):
        v = zone.get(key)
        if not (isinstance(v, (list, tuple)) and len(v) == 3):
            raise ValueError(f"zone {i} '{key}' must be a length-3 list, got {v!r}")
        out[key] = [float(c) for c in v]
    if any(out["max"][a] < out["min"][a] for a in range(3)):
        raise ValueError(f"zone {i} has max < min on some axis: {out['min']} .. {out['max']}")
    if kind == "shelf":
        out["level"] = int(zone.get("level", 0))
    return out


def zones_for(mesh_path_or_id):
    """Return the list of zone dicts for an asset (empty list if none recorded).

    This is the read API the placement primitives will call.
    """
    if not mesh_path_or_id:
        return []
    entry = _load().get(asset_id(mesh_path_or_id))
    if not entry:
        return []
    return list(entry.get("zones", []))


def set_zones(mesh_path_or_id, zones):
    """Record (and persist) the full list of zones for an asset, replacing any prior set.

    Pass an empty list to drop the asset's annotation. Returns the stored zone list.
    """
    aid = asset_id(mesh_path_or_id)
    cache = _load()
    validated = [_validate_zone(z, i) for i, z in enumerate(zones or [])]
    if validated:
        cache[aid] = {"zones": validated}
    else:
        cache.pop(aid, None)
    _persist()
    return validated


def has_zones(mesh_path_or_id):
    return bool(zones_for(mesh_path_or_id))


def _pool_ids(pool_path):
    """Read an asset id-list pool JSON; tolerate {list} or {key: [...]} shapes."""
    data = json.loads(Path(pool_path).read_text())
    if isinstance(data, list):
        return list(data)
    ids = []
    for v in data.values():
        if isinstance(v, list):
            ids.extend(v)
    return ids


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="IDSDL.placement_zones",
                                 description="Per-asset placement-zone annotations.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("get", help="show an asset's zones")
    g.add_argument("asset")
    c = sub.add_parser("clear", help="drop an asset's zones")
    c.add_argument("asset")
    ls = sub.add_parser("list", help="list annotated assets (or pool coverage)")
    ls.add_argument("--pool", help="id-list JSON; report which pool ids still need zones")
    im = sub.add_parser("import", help="merge a {id: {zones:[...]}} JSON (from the annotator) into the store")
    im.add_argument("file")
    args = ap.parse_args(argv)

    if args.cmd == "import":
        data = json.loads(Path(args.file).read_text())
        n = 0
        for aid, entry in data.items():
            zones = entry.get("zones", entry) if isinstance(entry, dict) else entry
            saved = set_zones(aid, zones)
            print(f"  {asset_id(aid)} -> {len(saved)} zone(s)")
            n += 1
        print(f"imported {n} asset(s) from {args.file}")
    elif args.cmd == "get":
        print(json.dumps(zones_for(args.asset), indent=2))
    elif args.cmd == "clear":
        set_zones(args.asset, [])
        print(f"cleared {asset_id(args.asset)}")
    elif args.cmd == "list":
        cache = _load()
        if args.pool:
            ids = _pool_ids(args.pool)
            done = [m for m in ids if asset_id(m) in cache]
            todo = [m for m in ids if asset_id(m) not in cache]
            print(f"{len(done)}/{len(ids)} annotated in {args.pool}")
            for m in todo:
                print(f"  needs zones: {m}")
        else:
            if not cache:
                print("(no zones recorded)")
            for k, v in sorted(cache.items()):
                print(f"  {k} -> {len(v.get('zones', []))} zone(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
