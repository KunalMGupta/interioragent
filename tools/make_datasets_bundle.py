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
    python tools/make_datasets_bundle.py --curated       # the MINI demo bundle (see below)

--curated builds idsdl_datasets_mini.zip: only the PROVEN assets — every id a past build
actually chose (the .cache/retrieval_seed_*.json caches) or that a worked example / scene
program pins — with a FILTERED index (futurehssd.npz subset), their preview images, the
wall-texture library, and a MINIMAL_LIBRARY.md marker. The pipeline runs unchanged against
it: the library simply IS what's on disk (retrievers hide indexed ids with no mesh).
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile
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


_MESH_ROOTS = {
    "future": "IDSDL/datasets/futurehssd/3D-FUTURE-models",
    "hssd": "IDSDL/datasets/futurehssd/HSSD-models",
    "custom": "IDSDL/datasets/custom/models",
}
_IMG_ROOTS = {
    "future": "IDSDL/datasets/futurehssd/3D-FUTURE-images",
    "hssd": "IDSDL/datasets/futurehssd/HSSD-images",
}


def _proven_ids() -> set:
    """Every asset id a past build chose (seed caches) or a program pins.
    Customs count only if seeded/pinned — the demo carries proven identity
    assets, not the whole ingest history."""
    ids = set()
    for p in glob.glob(os.path.join(ROOT, ".cache/retrieval_seed_*.json")):
        ids.update(re.findall(r'"((?:hssd|future|custom)/[A-Za-z0-9_-]+)"', open(p).read()))
    for pat in ("skills/examples/*_v*.py", "scenes/**/*.py"):
        for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
            ids.update(re.findall(r'["\']((?:hssd|future|custom)/[A-Za-z0-9_-]{6,})["\']',
                                  open(p).read()))
    return ids


def _curated_plan(staging: str):
    """Return [(arcname, abs_src)] for the mini bundle + the proven-id census."""
    import numpy as np

    proven = _proven_ids()
    entries, kept = [], []
    for mid in sorted(proven):
        kind, _, key = mid.partition("/")
        mesh = os.path.join(_MESH_ROOTS.get(kind, ""), key + ".glb")
        if not os.path.exists(os.path.join(ROOT, mesh)):
            continue                      # stale cache id — drop silently
        kept.append(mid)
        entries.append((mesh, os.path.join(ROOT, mesh)))
        img_root = _IMG_ROOTS.get(kind)   # custom previews are git-tracked already
        if img_root:
            img = os.path.join(img_root, key + ".png")
            if os.path.exists(os.path.join(ROOT, img)):
                entries.append((img, os.path.join(ROOT, img)))

    # filtered index: the npz subset for exactly the kept future/hssd ids
    src = np.load(os.path.join(ROOT, "IDSDL/datasets/assets/futurehssd.npz"))
    keep = set(kept)
    mask = np.array([str(m) in keep for m in src["all_models"]], dtype=bool)
    np.savez(os.path.join(staging, "futurehssd.npz"),
             all_embeddings=src["all_embeddings"][mask],
             all_models=src["all_models"][mask])
    entries.append(("IDSDL/datasets/assets/futurehssd.npz",
                    os.path.join(staging, "futurehssd.npz")))
    # everything else untracked in datasets/assets ships whole: the FULL metadata json
    # (7.5 MB; harmless for absent ids, and pins get clean errors) and the support meshes
    # the retriever registry loads EAGERLY at build time (canvas.obj/glb for the Painting
    # generator, cherry_blossom.glb — a mini install without them can't even warm).
    adir = os.path.join(ROOT, "IDSDL/datasets/assets")
    for f in sorted(os.listdir(adir)):
        rel = f"IDSDL/datasets/assets/{f}"
        if f.startswith(".") or f == "futurehssd.npz" or not os.path.isfile(os.path.join(adir, f)):
            continue
        entries.append((rel, os.path.join(ROOT, rel)))

    # the wall-texture library + caches (small, needed by any textured scene)
    for rel in ("IDSDL/datasets/futurehssd/3D-FRONT-texture",
                "IDSDL/assets/wall_textures_embeddings.npz", "assets/rag_cache.npz"):
        abs_p = os.path.join(ROOT, rel)
        if os.path.isdir(abs_p):
            for dp, _, fs in os.walk(abs_p):
                for f in sorted(fs):
                    a = os.path.relpath(os.path.join(dp, f), ROOT)
                    entries.append((a, os.path.join(ROOT, a)))
        elif os.path.exists(abs_p):
            entries.append((rel, abs_p))

    n_base = int(mask.sum())
    n_custom = sum(1 for m in kept if m.startswith("custom/"))
    marker = os.path.join(staging, "MINIMAL_LIBRARY.md")
    with open(marker, "w") as f:
        f.write(f"""# Minimal (curated demo) asset library

This install carries the CURATED subset: {len(kept)} proven assets
({n_base} FutureHSSD + {n_custom} custom) — every asset a past build actually
chose or a worked example pins — instead of the full ~29k library.

Everything works normally; retrieval is simply limited to what is on disk.
Expect the retrieval stress test to report more gaps than the lessons mention —
substitute by silhouette (the lessons teach how) rather than fighting a gap,
or install the full bundle / set SKETCHFAB_API_TOKEN and use the asset shop.
""")
    entries.append(("IDSDL/datasets/MINIMAL_LIBRARY.md", marker))
    return entries, kept


def main(argv=None):
    ap = argparse.ArgumentParser(prog="make_datasets_bundle")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--index-only", action="store_true",
                    help="skip the mesh/image trees; index + caches only")
    ap.add_argument("--curated", action="store_true",
                    help="build the mini demo bundle (proven assets only)")
    args = ap.parse_args(argv)

    if args.curated:
        out = os.path.join(ROOT, args.out or "idsdl_datasets_mini.zip")
        tracked = _tracked()
        with tempfile.TemporaryDirectory() as staging:
            entries, kept = _curated_plan(staging)
            entries = [(a, s) for a, s in entries
                       if a not in tracked or s.startswith(staging)]
            total = sum(os.path.getsize(s) for _, s in entries)
            print(f"curated: {len(kept)} proven assets, {len(entries)} files, {total/1e9:.2f} GB")
            if args.dry_run:
                return 0
            with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
                for arc, src in entries:
                    z.write(src, arcname=arc)
            print(f"bundle: {out} ({os.path.getsize(out)/1e9:.2f} GB)")
            print("share it with: unzip idsdl_datasets_mini.zip -d <repo-root>")
        return 0
    args.out = args.out or "idsdl_datasets.zip"

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
