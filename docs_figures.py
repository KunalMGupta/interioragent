"""
Build dedicated minimal example scenes for the documentation and render each from
a top-down (floor-plan) and a perspective view.

Usage:
    python docs_figures.py <fig_name> [<fig_name> ...]
    python docs_figures.py all
    python docs_figures.py group:reg          # all figures whose name starts with "reg_"

Each figure function builds and returns a configured SceneProgRoom. The driver exports
it to docs/assets/scenes/blend/<name>.blend and renders:
    docs/assets/scenes/<name>_top.png
    docs/assets/scenes/<name>_persp.png
"""
import os
import sys

from IDSDL.scene import SceneProgRoom
from IDSDL.groups import BasicRoomGroup
from IDSDL.renderer.renderer import SceneRenderer

SEED = 42


class ConstraintRoom(BasicRoomGroup):
    """BasicRoomGroup that runs user-supplied constraint hooks before grad_optimize."""

    def __init__(self, scene, WIDTH, DEPTH, HEIGHT, hooks=None, name=None):
        self._hooks = hooks or []
        super().__init__(scene, WIDTH=WIDTH, DEPTH=DEPTH, HEIGHT=HEIGHT, name=name)

    def compile(self):
        self.reset_compile_state()
        self.clear_constraints()
        for op in self.operations:
            op.execute()
        self.OverlapConstraint()
        self.OutOfBoundsConstraint()
        for hook in self._hooks:
            hook(self)
        self.grad_optimize()
        self.finalize_compile()
        self.is_frozen_group = True
        self.last_compile_report = self.make_compile_report()
        return self.last_compile_report


def _raw(name, specs):
    """Build a scene with objects at given (description, position, rotation) — no optimization."""
    scene = SceneProgRoom(name, seed=SEED)
    objs = []
    for desc, pos, rot in specs:
        o = scene.AddAsset(desc)
        o.set_location(*pos)
        o.set_rotation(rot)
        objs.append(o)
    scene.bind(objs)
    return scene
BLEND_DIR = "docs/assets/scenes/blend"
OUT = "docs/assets/scenes"

renderer = SceneRenderer(resolution_x=900, resolution_y=900, samples=16, verbose=False)


# ===========================================================================
# Object registration figures (no group compile -> fast, no VLM)
# ===========================================================================

def reg_single():
    scene = SceneProgRoom("reg_single", seed=SEED)
    sofa = scene.AddAsset("a modern 3-seat sofa")
    sofa.set_location(0, 0, 0)
    scene.bind(sofa)
    return scene


def reg_scaling():
    scene = SceneProgRoom("reg_scaling", seed=SEED)
    default = scene.AddAsset("a modern 3-seat sofa")
    modulated = scene.AddAsset("a modern 3-seat sofa", modulate_scale=0.5)
    width_only = scene.AddAsset("a modern 3-seat sofa", width=0.5)
    depth_only = scene.AddAsset("a modern 3-seat sofa", depth=0.5)
    default.set_location(0, 0, 0)
    modulated.set_location(3, 0, 0)
    width_only.set_location(6, 0, 0)
    depth_only.set_location(9, 0, 0)
    scene.bind([default, modulated, width_only, depth_only])
    return scene


def reg_copies():
    scene = SceneProgRoom("reg_copies", seed=SEED)
    chair = scene.AddAsset("a cozy lounge chair")
    chairs = 4 * chair
    for i, c in enumerate(chairs):
        c.set_location(i * 1.2, 0, 0)
    scene.bind(chairs)
    return scene


def reg_rotation():
    scene = SceneProgRoom("reg_rotation", seed=SEED)
    table = scene.AddAsset("a round wooden coffee table")
    c_default = scene.AddAsset("a cozy lounge chair")
    c_rotated = scene.AddAsset("a cozy lounge chair")
    c_facing = scene.AddAsset("a cozy lounge chair")
    table.set_location(0, 0, 0)
    c_default.set_location(-2, 0, 2)
    c_rotated.set_location(0, 0, 2)
    c_rotated.set_rotation(90)
    c_facing.set_location(2, 0, 2)
    c_facing.face_towards(table)
    scene.bind([table, c_default, c_rotated, c_facing])
    return scene


# ===========================================================================
# RelativeGroup figures
# ===========================================================================

def rel_basic():
    scene = SceneProgRoom("rel_basic", seed=SEED)
    with scene.RelativeGroup() as g:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        table = scene.AddAsset("a rectangular wooden coffee table")
        chair_l = scene.AddAsset("a cozy lounge chair")
        chair_r = scene.AddAsset("a cozy lounge chair")
        g.set_anchor(sofa)
        g.place_on_front(table)
        g.place_on_left(chair_l)
        g.place_on_right(chair_r)
    scene.bind(g)
    return scene


def rel_corners():
    scene = SceneProgRoom("rel_corners", seed=SEED)
    with scene.RelativeGroup() as g:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        n1 = scene.AddAsset("a small wooden nightstand with a drawer")
        n2 = scene.AddAsset("a small wooden nightstand with a drawer")
        n3 = scene.AddAsset("a small wooden nightstand with a drawer")
        n4 = scene.AddAsset("a small wooden nightstand with a drawer")
        g.set_anchor(bed)
        g.place_on_back_left(n1)
        g.place_on_back_right(n2)
        g.place_on_front_left(n3)
        g.place_on_front_right(n4)
    scene.bind(g)
    return scene


def rel_further():
    scene = SceneProgRoom("rel_further", seed=SEED)
    with scene.RelativeGroup() as g:
        table = scene.AddAsset("a rectangular wooden coffee table")
        near = scene.AddAsset("a cozy lounge chair")
        far = scene.AddAsset("a tall floor lamp")
        g.set_anchor(table)
        g.place_on_left(near)
        g.place_on_left_further(far)
    scene.bind(g)
    return scene


def rel_top_rug():
    scene = SceneProgRoom("rel_top_rug", seed=SEED)
    with scene.RelativeGroup() as g:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        lamp = scene.AddAsset("a modern table lamp with a white shade")
        g.set_anchor(bed)
        g.place_on_back_right(nightstand)
        g.place_on_top(lamp)
        g.place_rug("a soft neutral area rug", size=0.9)
    scene.bind(g)
    return scene


# ===========================================================================
# AroundGroup figures
# ===========================================================================

def around_rectilinear():
    scene = SceneProgRoom("around_rectilinear", seed=SEED)
    with scene.AroundGroup() as g:
        table = scene.AddAsset("a large rectangular dining table with a dark wood finish")
        chair = scene.AddAsset("an elegant dining chair with a cushioned seat")
        g.set_anchor(table)
        g.place_rectilinear(longer_side1=3 * chair, longer_side2=3 * chair,
                            shorter_side1=2 * chair, shorter_side2=2 * chair)
    scene.bind(g)
    return scene


def around_circle():
    scene = SceneProgRoom("around_circle", seed=SEED)
    with scene.AroundGroup() as g:
        table = scene.AddAsset("a round wooden coffee table")
        chair = scene.AddAsset("an upholstered accent chair")
        g.set_anchor(table)
        g.place_circle(objects=4 * chair)
    scene.bind(g)
    return scene


def around_arc():
    scene = SceneProgRoom("around_arc", seed=SEED)
    with scene.AroundGroup(sparsity=0.5) as g:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        chair = scene.AddAsset("a cozy lounge chair")
        g.set_anchor(sofa)
        g.place_arc(objects=3 * chair)
    scene.bind(g)
    return scene


def around_sparsity_dense():
    scene = SceneProgRoom("around_sparsity_dense", seed=SEED)
    with scene.AroundGroup(sparsity=0.0) as g:
        table = scene.AddAsset("a round wooden coffee table")
        chair = scene.AddAsset("an upholstered accent chair")
        g.set_anchor(table)
        g.place_circle(objects=4 * chair)
    scene.bind(g)
    return scene


def around_sparsity_sparse():
    scene = SceneProgRoom("around_sparsity_sparse", seed=SEED)
    with scene.AroundGroup(sparsity=1.0) as g:
        table = scene.AddAsset("a round wooden coffee table")
        chair = scene.AddAsset("an upholstered accent chair")
        g.set_anchor(table)
        g.place_circle(objects=4 * chair)
    scene.bind(g)
    return scene


# ===========================================================================
# GridGroup figures
# ===========================================================================

def grid_row():
    scene = SceneProgRoom("grid_row", seed=SEED)
    with scene.GridGroup(sparsity=0.4) as g:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        g.place_row(5 * chair)
    scene.bind(g)
    return scene


def grid_grid():
    scene = SceneProgRoom("grid_grid", seed=SEED)
    with scene.GridGroup(sparsity=0.5) as g:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        g.place_grid(6 * chair, cols=3)
    scene.bind(g)
    return scene


def grid_rectilinear():
    scene = SceneProgRoom("grid_rectilinear", seed=SEED)
    with scene.GridGroup(sparsity=0.3) as g:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        g.place_rectilinear(width1=4 * chair, width2=4 * chair,
                            depth1=2 * chair, depth2=2 * chair)
    scene.bind(g)
    return scene


def grid_arc():
    scene = SceneProgRoom("grid_arc", seed=SEED)
    lectern = scene.AddAsset("a wooden lectern or podium")
    with scene.GridGroup(sparsity=0.4) as g:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        g.place_arc(6 * chair, towards=lectern)
    lectern.set_location(0, 0, 0)
    scene.bind([g, lectern])
    return scene


def grid_randomness():
    scene = SceneProgRoom("grid_randomness", seed=SEED)
    with scene.GridGroup(sparsity=0.5, randomness=0.9) as g:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        g.place_grid(9 * chair, cols=3)
    scene.bind(g)
    return scene


# ===========================================================================
# RoomGroup figures
# ===========================================================================

def room_grid_points():
    scene = SceneProgRoom("room_grid_points", seed=SEED)
    center = scene.AddAsset("a round wooden coffee table")
    bl = scene.AddAsset("a tall floor lamp")
    br = scene.AddAsset("a tall floor lamp")
    fl = scene.AddAsset("a medium indoor potted plant")
    fr = scene.AddAsset("a medium indoor potted plant")
    with scene.RoomGroup() as room:
        room.place_on_center(center, facing="front")
        room.place_on_back_left_corner(bl, facing="front")
        room.place_on_back_right_corner(br, facing="front")
        room.place_on_front_left_corner(fl, facing="back")
        room.place_on_front_right_corner(fr, facing="back")
    return scene


def room_walls():
    scene = SceneProgRoom("room_walls", seed=SEED)
    sofa = scene.AddAsset("a modern 3-seat sofa")
    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_walls(floor_texture="light oak wood floor",
                         ceiling_texture="smooth white ceiling",
                         wall_texture="warm off-white painted wall")
        room.place_door("right_wall", position="right")
        room.place_window_picture("left_wall")
    return scene


def room_wall_art():
    scene = SceneProgRoom("room_wall_art", seed=SEED)
    sofa = scene.AddAsset("a modern 3-seat sofa")
    painting = scene.AddAsset("a large abstract painting in a dark frame")
    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_wall_back_center(painting)
    return scene


# ===========================================================================
# Hierarchical / parent-child figures
# ===========================================================================

def hier_nested():
    """A dining AroundGroup and a sofa RelativeGroup, both placed inside a RoomGroup —
    each inner group is frozen and optimized as a single unit at the room level."""
    scene = SceneProgRoom("hier_nested", seed=SEED)
    with scene.AroundGroup() as dining:
        table = scene.AddAsset("a large rectangular dining table")
        chair = scene.AddAsset("an elegant dining chair")
        dining.set_anchor(table)
        dining.place_rectilinear(longer_side1=2 * chair, longer_side2=2 * chair)
    with scene.RelativeGroup() as seating:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        coffee = scene.AddAsset("a rectangular wooden coffee table")
        seating.set_anchor(sofa)
        seating.place_on_front(coffee)
    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating, facing="front")
        room.place_on_front_wall_center(dining, facing="back")
    return scene


# ===========================================================================
# Constraint figures (before / after) — gradient constraints, no VLM
# ===========================================================================

_OVERLAP_SPECS = [
    ("a modern 3-seat sofa", (2.3, 0, 2.5), 0),
    ("a rectangular wooden coffee table", (2.5, 0, 2.5), 0),
    ("a cozy lounge chair", (2.7, 0, 2.5), 0),
]


def con_overlap_before():
    return _raw("con_overlap_before", _OVERLAP_SPECS)


def con_overlap_after():
    scene = SceneProgRoom("con_overlap_after", seed=SEED)
    sofa = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    chair = scene.AddAsset("a cozy lounge chair")
    with BasicRoomGroup(scene, WIDTH=6.0, DEPTH=5.0, HEIGHT=3.0) as room:
        room.place([sofa, table, chair],
                   positions=[p for _, p, _ in _OVERLAP_SPECS],
                   rotations=[0, 0, 0])
    return scene


def con_outofbounds_before():
    return _raw("con_outofbounds_before",
                [("a modern 3-seat sofa", (4.6, 0, 2.5), 0),
                 ("a cozy lounge chair", (2.5, 0, 2.5), 0)])


def con_outofbounds_after():
    scene = SceneProgRoom("con_outofbounds_after", seed=SEED)
    sofa = scene.AddAsset("a modern 3-seat sofa")
    chair = scene.AddAsset("a cozy lounge chair")
    with BasicRoomGroup(scene, WIDTH=5.0, DEPTH=5.0, HEIGHT=3.0) as room:
        room.place([sofa, chair], positions=[(4.6, 0, 2.5), (2.5, 0, 2.5)], rotations=[0, 0])
    return scene


_CLEAR_SPECS = [("a modern 3-seat sofa", (2.5, 0, 1.5), 0),
                ("a rectangular wooden coffee table", (2.5, 0, 2.0), 0)]


def con_clearance_before():
    return _raw("con_clearance_before", _CLEAR_SPECS)


def con_clearance_after():
    scene = SceneProgRoom("con_clearance_after", seed=SEED)
    sofa = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    hooks = [lambda r: r.ClearanceConstraint(sofa, distance=0.8, dir="front")]
    with ConstraintRoom(scene, WIDTH=5.0, DEPTH=5.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([sofa, table], positions=[(2.5, 0, 1.5), (2.5, 0, 2.0)], rotations=[0, 0])
    return scene


_ACCESS_SPECS = [("a queen-sized bed with a wooden frame", (2.5, 0, 2.5), 0),
                 ("a small wooden nightstand with a drawer", (4.5, 0, 2.5), 0)]


def con_access_before():
    return _raw("con_access_before", _ACCESS_SPECS)


def con_access_after():
    scene = SceneProgRoom("con_access_after", seed=SEED)
    bed = scene.AddAsset("a queen-sized bed with a wooden frame")
    nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
    hooks = [lambda r: r.AccessConstraint(bed, nightstand, min_dist=0.05, max_dist=0.25, dir="sides")]
    with ConstraintRoom(scene, WIDTH=5.0, DEPTH=5.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([bed, nightstand], positions=[(2.5, 0, 2.5), (4.5, 0, 2.5)], rotations=[0, 0])
    return scene


_VIS_SPECS = [("a modern 3-seat sofa", (2.5, 0, 1.0), 0),
              ("a flat-screen television on a low stand", (2.5, 0, 4.5), 180),
              ("a medium indoor potted plant", (2.5, 0, 2.8), 0)]


def con_visibility_before():
    return _raw("con_visibility_before", _VIS_SPECS)


def con_visibility_after():
    scene = SceneProgRoom("con_visibility_after", seed=SEED)
    sofa = scene.AddAsset("a modern 3-seat sofa")
    tv = scene.AddAsset("a flat-screen television on a low stand")
    plant = scene.AddAsset("a medium indoor potted plant")
    hooks = [lambda r: r.VisibilityConstraint(sofa, tv)]
    with ConstraintRoom(scene, WIDTH=5.0, DEPTH=6.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([sofa, tv, plant],
                   positions=[(2.5, 0, 1.0), (2.5, 0, 4.5), (2.5, 0, 2.8)],
                   rotations=[0, 180, 0])
    return scene


def ascii_hi():
    scene = SceneProgRoom("ascii_hi", seed=SEED)
    with scene.SentenceASCIIGenerator() as ascii_gen:
        plant = scene.AddAsset("a small succulent plant")
        ascii_gen.place(plant, "HI")
    scene.bind(ascii_gen)
    return scene


FIGURES = {
    # registration
    "reg_single": reg_single, "reg_scaling": reg_scaling,
    "reg_copies": reg_copies, "reg_rotation": reg_rotation,
    # relative
    "rel_basic": rel_basic, "rel_corners": rel_corners,
    "rel_further": rel_further, "rel_top_rug": rel_top_rug,
    # around
    "around_rectilinear": around_rectilinear, "around_circle": around_circle,
    "around_arc": around_arc,
    "around_sparsity_dense": around_sparsity_dense,
    "around_sparsity_sparse": around_sparsity_sparse,
    # grid
    "grid_row": grid_row, "grid_grid": grid_grid,
    "grid_rectilinear": grid_rectilinear, "grid_arc": grid_arc,
    "grid_randomness": grid_randomness,
    # room
    "room_grid_points": room_grid_points, "room_walls": room_walls,
    "room_wall_art": room_wall_art,
    # hierarchy
    "hier_nested": hier_nested,
    # ascii
    "ascii_hi": ascii_hi,
    # constraints (before / after)
    "con_overlap_before": con_overlap_before, "con_overlap_after": con_overlap_after,
    "con_outofbounds_before": con_outofbounds_before, "con_outofbounds_after": con_outofbounds_after,
    "con_clearance_before": con_clearance_before, "con_clearance_after": con_clearance_after,
    "con_access_before": con_access_before, "con_access_after": con_access_after,
    "con_visibility_before": con_visibility_before, "con_visibility_after": con_visibility_after,
}


def build_and_render(name):
    os.makedirs(BLEND_DIR, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    scene = FIGURES[name]()
    blend = os.path.join(BLEND_DIR, f"{name}.blend")
    scene.export(blend)
    top = os.path.join(OUT, f"{name}_top.png")
    renderer.render_from_top(blend, top)
    corners = [os.path.join(OUT, f"{name}_persp_{i}.png") for i in range(4)]
    renderer.render_from_corners(blend, corners)
    os.replace(corners[0], os.path.join(OUT, f"{name}_persp.png"))
    for c in corners[1:]:
        if os.path.exists(c):
            os.remove(c)
    print(f"[{name}] done")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["all"]:
        targets = list(FIGURES)
    elif len(args) == 1 and args[0].startswith("group:"):
        prefix = args[0].split(":", 1)[1]
        targets = [n for n in FIGURES if n.startswith(prefix)]
    else:
        targets = args
    for name in targets:
        try:
            build_and_render(name)
        except Exception as e:
            import traceback
            print(f"[{name}] FAILED: {e}")
            traceback.print_exc()
