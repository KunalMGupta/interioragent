"""
Per-asset front-orientation correction cache.

Assets from the datasets carry no canonical "front" — each mesh is authored
facing an arbitrary direction, while the DSL's rotation logic (face_towards,
facing=, place methods, wall-facing) assumes front = +z. So some assets render
rotated wrong (e.g. a desk whose working side ends up facing away).

This cache records a per-asset correction angle (degrees about the vertical
axis), keyed by the asset's stable id (its mesh filename stem). The correction is
added at serialization time only (see SceneProgObject.get_state_info), so the DSL
geometry stays in the canonical frame and only the exported/rendered mesh is
rotated to match.

Populate it incrementally: when you find an asset that renders backwards, record
its correction and every future scene that uses it is fixed automatically:

    python -m IDSDL.front_cache set <asset-id-or-mesh-path> <degrees>
    python -m IDSDL.front_cache get <asset-id-or-mesh-path>
    python -m IDSDL.front_cache list
"""
import json
import os
from pathlib import Path

_CACHE_PATH = Path(__file__).parent / "datasets" / "front_offsets.json"
_cache = None


def _load():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_CACHE_PATH.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            _cache = {}
    return _cache


def asset_id(mesh_path) -> str:
    """Stable id for an asset: its mesh filename stem (e.g. the model hash)."""
    return os.path.splitext(os.path.basename(str(mesh_path)))[0]


def front_offset_for(mesh_path) -> float:
    """Correction angle (degrees) for the asset at mesh_path, 0.0 if none recorded."""
    if not mesh_path:
        return 0.0
    return float(_load().get(asset_id(mesh_path), 0.0))


def set_offset(mesh_path_or_id, degrees) -> dict:
    """Record (and persist) a correction for an asset. Returns the full cache."""
    cache = _load()
    cache[asset_id(mesh_path_or_id)] = float(degrees) % 360.0
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True))
    return cache


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="IDSDL.front_cache",
                                 description="Per-asset front-orientation corrections.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set", help="record a correction angle for an asset")
    s.add_argument("asset"); s.add_argument("degrees", type=float)
    g = sub.add_parser("get", help="show an asset's correction")
    g.add_argument("asset")
    sub.add_parser("list", help="list all recorded corrections")
    args = ap.parse_args(argv)

    if args.cmd == "set":
        set_offset(args.asset, args.degrees)
        print(f"{asset_id(args.asset)} -> {float(args.degrees) % 360.0}")
    elif args.cmd == "get":
        print(f"{asset_id(args.asset)} -> {front_offset_for(args.asset)}")
    elif args.cmd == "list":
        cache = _load()
        if not cache:
            print("(no corrections recorded)")
        for k, v in sorted(cache.items()):
            print(f"  {k} -> {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
