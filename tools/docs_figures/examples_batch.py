"""Build (phase 1) and render the docs worked-examples gallery.

Each curated example program is built via workbench.py in its own scratch dir
(programs export a cwd-relative blend), then rendered with the studio look.

Run from the repo root:
    python tools/docs_figures/examples_batch.py [name ...]     # default: all
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from tools.docs_figures import harness   # noqa: E402

EXAMPLES = [
    "bedroom_v1", "living_room_v1", "kitchen_l_v1", "dining_room_v1",
    "bakery_v1", "media_room_v1", "study_room_v1", "classroom_v1",
    "hair_salon_v1", "gym_v1", "greenhouse_v1", "bookstore_v1",
]

STUDIO = os.path.join(REPO, "tools", "docs_figures", "studio_render.py")


def one(name):
    import re
    prog = os.path.join(REPO, "skills", "examples", f"{name}.py")
    # Build from the driver's own cwd: the Blender exec layer resolves paths
    # against a shared working directory, so every client must use the same one.
    build_dir = os.getcwd()
    with open(prog) as f:
        m = re.search(r'scene\.export\(\s*["\']([^"\']+\.blend)["\']', f.read())
    blend = os.path.join(build_dir, m.group(1) if m else f"{name}.blend")
    if not os.path.exists(blend):
        env = dict(os.environ)
        env.setdefault("IDSDL_SMART_SCALE", "0")
        env["PYTHONPATH"] = REPO + os.pathsep + env.get("PYTHONPATH", "")
        r = subprocess.run(
            [sys.executable, os.path.join(REPO, "workbench.py"), "run",
             prog, "--phase", "1"],
            cwd=build_dir, env=env, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(blend):
            raise RuntimeError(f"build failed for {name}:\n"
                               + r.stdout[-2000:] + "\n" + r.stderr[-2000:])
    r = subprocess.run(
        [harness.BLENDER, "--background", blend, "--python", STUDIO,
         "--", harness.OUT, f"example_{name}", "room", "persp"],
        capture_output=True, text=True)
    if r.returncode != 0 or "wrote" not in r.stdout:
        raise RuntimeError(f"render failed for {name}:\n"
                           + r.stdout[-2000:] + "\n" + r.stderr[-2000:])
    print(f"OK example_{name}_persp.png")


def main():
    harness._load_env()
    os.makedirs(harness.OUT, exist_ok=True)
    names = sys.argv[1:] or EXAMPLES
    failed = []
    for n in names:
        try:
            one(n)
        except Exception as e:
            print(f"FAIL {n}: {e}")
            failed.append(n)
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
