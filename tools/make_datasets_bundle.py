"""Build the single shareable datasets bundle (idsdl_datasets.zip).

Everything asset-retrieval needs that is NOT in git, in one artifact — the
FutureHSSD index + meshes + preview images, the ingested custom-library
meshes, and the regenerable caches — so a user does exactly one download:

    unzip idsdl_datasets.zip -d <repo-root>

Git-tracked files are excluded automatically (the repo is the source of truth
for those; a stale bundle must never clobber them on extract). Big binaries
are STORED, not deflated — glb/npz/png don't compress and it keeps the build
fast.

    python tools/make_datasets_bundle.py --dry-run       # what would ship, with sizes
    python tools/make_datasets_bundle.py --out idsdl_datasets.zip
    python tools/make_datasets_bundle.py --index-only    # skip the mesh/image trees (~70 GB)
"""
import argparse
import os
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (path relative to repo root, why it ships)
MANIFEST = [
    ("IDSDL/datasets/assets", "retrieval index: futurehssd.npz/.json"),
    ("IDSDL/datasets/futurehssd", "3D-FUTURE + HSSD meshes and preview images (the big one)"),
    ("IDSDL/datasets/custom/models", "ingested custom-library meshes (see ATTRIBUTIONS.md)"),
    ("IDSDL/assets/wall_textures_embeddings.npz", "wall-texture matching cache (regenerable)"),
    ("assets/rag_cache.npz", "planner RAG cache (regenerable)"),
]

INDEX_ONLY_SKIP = {"IDSDL/datasets/futurehssd", "IDSDL/datasets/custom/models"}


def _tracked() -> set:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    return set(out.stdout.splitlines())


def _files_for(entry: str):
    abs_path = os.path.join(ROOT, entry)
    if os.path.isfile(abs_path):
        yield entry
    elif os.path.isdir(abs_path):
        for dirpath, _, files in os.walk(abs_path):
            for f in sorted(files):
                yield os.path.relpath(os.path.join(dirpath, f), ROOT)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="make_datasets_bundle")
    ap.add_argument("--out", default="idsdl_datasets.zip")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--index-only", action="store_true",
                    help="skip the mesh/image trees; index + caches only")
    args = ap.parse_args(argv)

    tracked = _tracked()
    total, plan = 0, []
    for entry, why in MANIFEST:
        if args.index_only and entry in INDEX_ONLY_SKIP:
            continue
        if not os.path.exists(os.path.join(ROOT, entry)):
            print(f"  ! missing on this machine, skipped: {entry}  ({why})")
            continue
        size = 0
        files = [f for f in _files_for(entry) if f not in tracked]
        for f in files:
            size += os.path.getsize(os.path.join(ROOT, f))
        total += size
        plan.append((entry, why, files, size))
        print(f"  + {entry}: {len(files)} file(s), {size/1e9:.2f} GB  — {why}")
    print(f"TOTAL: {total/1e9:.2f} GB")

    if args.dry_run:
        return 0

    out = os.path.join(ROOT, args.out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        done = 0
        for entry, _, files, size in plan:
            for f in files:
                z.write(os.path.join(ROOT, f), arcname=f)
            done += size
            print(f"  wrote {entry} ({done/1e9:.2f}/{total/1e9:.2f} GB)")
    print(f"bundle: {out} ({os.path.getsize(out)/1e9:.2f} GB)")
    print("share it with: unzip idsdl_datasets.zip -d <repo-root>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
