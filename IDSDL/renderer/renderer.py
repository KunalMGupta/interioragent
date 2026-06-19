
from sceneprogexec import SceneProgExec

class SceneRenderer:
    def __init__(self, resolution_x: int = 1920, resolution_y: int = 1080, samples: int = 100, frame_rate: int = 30, num_frames: int = 360, cuda: bool = False, verbose=False):
        self.script = f"""
from utils import *
worker = SceneRendererWorker({resolution_x}, {resolution_y}, {samples}, {frame_rate}, {num_frames}, {cuda})
"""
        import os
        package_path = os.path.dirname(os.path.abspath(__file__))
        self.exec = SceneProgExec(caller_path=package_path)
        self.verbose = verbose

    def run(self, script):
        self.exec(script, verbose=self.verbose)

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

# renderer = SceneRenderer(resolution_x=512, resolution_y=512, samples=5)
# renderer.render_from_corners("/Users/kunalgupta/Documents/opttool2.blend", ["/Users/kunalgupta/Documents/packages/sceneprogrenderer/output1.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output2.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output3.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output4.png"])
# renderer.render_360("/Users/kunalgupta/Documents/opttool2.blend", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output.mp4")
# renderer.render_from_edge_midpoints("/Users/kunalgupta/Documents/opttool2.blend", ["/Users/kunalgupta/Documents/packages/sceneprogrenderer/output1.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output2.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output3.png", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output4.png"])
# renderer.render("/Users/kunalgupta/Documents/opttool2.blend", "/Users/kunalgupta/Documents/packages/sceneprogrenderer/output.png")