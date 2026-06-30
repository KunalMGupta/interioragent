"""Smoke test: smart place_on_top inside the DSL, then render the DSL objects to verify
the world-frame transform mapping (solver result -> DSL setters)."""
import os
import sys
sys.path.insert(0, "/work")

import trimesh

from IDSDL.scene import SceneProgRoom
from IDSDL import vlm_placement
from IDSDL.renderer.renderer import SceneRenderer

OUT = "/work/tools/out"
TABLE = "future/0d3e3b3c-3f1a-47ee-8566-1052cb8635b6"
LAMP = "future/f5d74060-ae91-44d2-8435-f587692b6b4d"
PLANT = "hssd/d97a5f104f7d0acaa9fb3cd559eacc7d79c21a83"


def main():
    scene = SceneProgRoom("placetest", seed=42)
    table = scene.AddAsset("a modern wooden coffee table", asset_id=TABLE)
    lamp = scene.AddAsset("a modern table lamp", asset_id=LAMP)
    plant = scene.AddAsset("a potted plant in a white vase", asset_id=PLANT)

    with scene.RelativeGroup() as area:
        area.set_anchor(table)

    ok = vlm_placement.place_smart(area, table, [lamp, plant], "on_top", log=print)
    print("smart placement returned:", ok)
    for o in (lamp, plant):
        loc = o.get_location()
        print(f"  {o.description[:30]:30s} loc=({loc[0]:.3f},{loc[1]:.3f},{loc[2]:.3f}) "
              f"h={o.get_height():.3f}")

    # Verify mapping: render the DSL objects' WORLD meshes head-on.
    sc = trimesh.Scene()
    for nm, obj in [("table", table), ("lamp", lamp), ("plant", plant)]:
        v = obj.get_world_transform().transform_points(obj.vertices)
        sc.add_geometry(trimesh.Trimesh(vertices=v, faces=obj.faces, process=False),
                        geom_name=nm)
    glb = os.path.join(OUT, "dsl_verify.glb")
    sc.export(glb)
    from tools.planar_regions import render_front
    render_front(glb, os.path.join(OUT, "dsl_verify.png"), OUT, res=512, samples=12)
    print("wrote", os.path.join(OUT, "dsl_verify.png"))


if __name__ == "__main__":
    main()
