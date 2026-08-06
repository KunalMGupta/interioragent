
from sceneprogexec import SceneProgExec

class SceneRenderer:
    def __init__(self, resolution_x: int = 1920, resolution_y: int = 1080, samples: int = 100, frame_rate: int = 30, num_frames: int = 360, cuda: bool = True, verbose=False):
        self.script = f"""
from utils import *
worker = SceneRendererWorker({resolution_x}, {resolution_y}, {samples}, {frame_rate}, {num_frames}, {cuda})
"""
        import os
        package_path = os.path.dirname(os.path.abspath(__file__))
        self.exec = SceneProgExec(caller_path=package_path)
        self.verbose = verbose

    def run(self, script):
        # Every render in IDSDL funnels through here, so this is where the
        # cross-process GPU budget is enforced: many agents may BUILD in parallel
        # (build is ~30x longer than render and is CPU/network bound), but only a
        # bounded number may have Blender on a card at once. No-op unless gating is
        # configured — see IDSDL/gpu_gate.py.
        from IDSDL.gpu_gate import gpu_slot
        import os as _os
        with gpu_slot("SceneRenderer") as gpu:
            if gpu is None:
                self.exec(script, verbose=self.verbose)
                return
            prev = _os.environ.get("CUDA_VISIBLE_DEVICES")
            _os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
            try:
                self.exec(script, verbose=self.verbose)
            finally:
                if prev is None:
                    _os.environ.pop("CUDA_VISIBLE_DEVICES", None)
                else:
                    _os.environ["CUDA_VISIBLE_DEVICES"] = prev

    def render(self, path, output_path, location=None, target=None):
        script = f"""
{self.script}
worker.render("{path}", "{output_path}", location={location}, target={target})
"""
        self.run(script)

    def render_from_corners(self, path, output_paths):
        script = f"""
{self.script}
worker.render_from_corners("{path}", {output_paths})
"""
        self.run(script)
    
    def render_from_edge_midpoints(self, path, output_paths):
        script = f"""
{self.script}
worker.render_from_edge_midpoints("{path}", {output_paths})
"""
        self.run(script)

    def render_360(self, path, output_path):
        script = f"""
{self.script}
worker.render_360("{path}", "{output_path}")
"""
        self.run(script)

    def render_from_front(self, path, output_path):
        script = f"""
{self.script}
worker.render_from_front("{path}", "{output_path}")
"""
        self.run(script)
    
    def render_from_top(self, path, output_path):
        script = f"""
{self.script}
worker.render_from_top("{path}", "{output_path}")
"""
        self.run(script)

    # ---- Interior views for RoomGroup scenes ----

    def render_interior_walls(self, path, output_paths):
        """Four interior wall-facing views [back, front, left, right]."""
        script = f"""
{self.script}
worker.render_interior_walls("{path}", {output_paths})
"""
        self.run(script)

    def render_interior_corners(self, path, output_paths):
        """Four high 3/4 interior corner views (ceiling removed)."""
        script = f"""
{self.script}
worker.render_interior_corners("{path}", {output_paths})
"""
        self.run(script)

    def render_room(self, path, output_dir):
        """Render a full interior set (4 walls + 4 corners) into output_dir."""
        script = f"""
{self.script}
worker.render_room("{path}", "{output_dir}")
"""
        self.run(script)

    def render_views(self, path, specs):
        """Render arbitrarily-framed views (per-group detail shots for a collection
        collage). `specs`: list of {{out, cam, target, lens?}} dicts (framing done by
        the caller). One scene load, N cameras."""
        import json
        script = f"""
{self.script}
import json
specs = json.loads(r'''{json.dumps(specs)}''')
worker.render_views("{path}", specs)
"""
        self.run(script)

# renderer = SceneRenderer(resolution_x=512, resolution_y=512, samples=5)
# renderer.render_from_corners("/Users/kunalgupta/Documents/opttool2.blend", ["/Users/kunalgupta/Documents/packages/sceneprogrenderer/output1.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output2.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output3.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output4.png"])
# renderer.render_360("/Users/kunalgupta/Documents/opttool2.blend", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output.mp4")
# renderer.render_from_edge_midpoints("/Users/kunalgupta/Documents/opttool2.blend", ["/Users/kunalgupta/Documents/packages/sceneprogrenderer/output1.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output2.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output3.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output4.png"])
# renderer.render("/Users/kunalgupta/Documents/opttool2.blend", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output.png")