"""
IDSDL Feature Test Suite
Usage:
    python tests.py            # list all tests
    python tests.py 1          # run test 01
    python tests.py 1 2 5      # run tests 01, 02, 05
    python tests.py all        # run all tests
"""

import sys
import traceback
import numpy as np

from IDSDL.scene import SceneProgRoom
from IDSDL.groups import BasicRoomGroup

SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_positions(label, objs):
    print(f"\n  [{label}]")
    for obj in objs:
        loc  = obj.get_location()
        aabb = obj.get_aabb()
        print(f"    {obj.description}: loc=({loc[0]:.3f}, {loc[2]:.3f})  "
              f"x=[{aabb[0,0]:.2f},{aabb[1,0]:.2f}]  z=[{aabb[0,2]:.2f},{aabb[1,2]:.2f}]")


class ConstraintRoom(BasicRoomGroup):
    """BasicRoomGroup that runs user-supplied constraint hooks before grad_optimize.

    Pass hooks as a list of callables: each receives the room as its argument
    and should call room.SomeConstraint(...) to register it.

    Example:
        hooks = [lambda r: r.ClearanceConstraint(sofa, distance=0.6, dir="front")]
        with ConstraintRoom(scene, WIDTH=5, DEPTH=5, HEIGHT=3, hooks=hooks) as room:
            room.place(...)
    """

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


def header(n, name):
    print(f"\n{'='*60}")
    print(f"TEST {n:02d}: {name}")
    print('='*60)


# ---------------------------------------------------------------------------
# 01  BasicRoomGroup — manual placement + OverlapConstraint + GradSolver
# ---------------------------------------------------------------------------
def _aabbs_overlap_2d(a, b):
    """True if two AABB footprints (XZ plane) intersect."""
    return not (a[1,0] <= b[0,0] or b[1,0] <= a[0,0] or
                a[1,2] <= b[0,2] or b[1,2] <= a[0,2])

def test_01():
    """BasicRoomGroup: manual placement, overlap fully resolved by GradSolver"""
    header(1, "BasicRoomGroup overlap resolution")
    scene = SceneProgRoom("test01", seed=SEED)
    sofa  = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    chair = scene.AddAsset("a cozy lounge chair")

    # Objects start moderately overlapping (1 m apart, but sofa 2 m wide + table 0.8 m wide)
    with BasicRoomGroup(scene, WIDTH=6.0, DEPTH=5.0, HEIGHT=3.0) as room:
        room.place(
            [sofa, table, chair],
            positions=[(1.5, 0, 2.5), (2.5, 0, 2.5), (4.0, 0, 2.5)],
            rotations=[0, 0, 0],
        )

    print_positions("after optimize", [sofa, table, chair])
    assert not _aabbs_overlap_2d(sofa.get_aabb(), table.get_aabb()), \
        "sofa and table still overlap after optimization"
    assert not _aabbs_overlap_2d(sofa.get_aabb(), chair.get_aabb()), \
        "sofa and chair still overlap after optimization"
    assert not _aabbs_overlap_2d(table.get_aabb(), chair.get_aabb()), \
        "table and chair still overlap after optimization"

    scene.export("results/test01_basic_room.blend")


# ---------------------------------------------------------------------------
# 02  RelativeGroup — anchor + place_on_left / right / front / back
# ---------------------------------------------------------------------------
def test_02():
    """RelativeGroup: sofa as anchor, coffee table in front, chairs on sides"""
    header(2, "RelativeGroup basic relative placement")
    scene = SceneProgRoom("test02", seed=SEED)

    with scene.RelativeGroup() as seating:
        sofa    = scene.AddAsset("a modern 3-seat sofa")
        table   = scene.AddAsset("a rectangular wooden coffee table")
        chair_l = scene.AddAsset("a cozy lounge chair")
        chair_r = scene.AddAsset("a cozy lounge chair")
        seating.set_anchor(sofa)
        seating.place_on_front(table)
        seating.place_on_left(chair_l)
        seating.place_on_right(chair_r)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating, facing="front")

    scene.export("results/test02_relative_basic.blend")


# ---------------------------------------------------------------------------
# 03  RelativeGroup — place_on_top (delayed) + place_rug (delayed)
# ---------------------------------------------------------------------------
def test_03():
    """RelativeGroup: lamp placed on top of nightstand; rug placed under bed area"""
    header(3, "RelativeGroup place_on_top + place_rug")
    scene = SceneProgRoom("test03", seed=SEED)

    with scene.RelativeGroup() as nightstand_area:
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        lamp       = scene.AddAsset("a modern table lamp with a white shade")
        nightstand_area.set_anchor(nightstand)
        nightstand_area.place_on_top(lamp)

    with scene.RelativeGroup() as bed_area:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        bed_area.set_anchor(bed)
        bed_area.place_on_back_right(nightstand_area)
        bed_area.place_rug("a soft neutral area rug", size=0.9)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(bed_area, facing="front")

    scene.export("results/test03_relative_top_rug.blend")


# ---------------------------------------------------------------------------
# 04  RelativeGroup — nested groups + object multiplication (1 * group)
# ---------------------------------------------------------------------------
def test_04():
    """RelativeGroup: nightstand_area cloned on both sides of bed with 1*group syntax"""
    header(4, "RelativeGroup nested + object multiplication")
    scene = SceneProgRoom("test04", seed=SEED)

    with scene.RelativeGroup() as nightstand_area:
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        lamp       = scene.AddAsset("a modern table lamp with a white shade")
        nightstand_area.set_anchor(nightstand)
        nightstand_area.place_on_top(lamp)

    with scene.RelativeGroup() as bed_area:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame and a plush mattress")
        bed_area.set_anchor(bed)
        bed_area.place_on_back_left(nightstand_area)
        bed_area.place_on_back_right(1 * nightstand_area)
        bed_area.place_rug("a soft neutral area rug", size=0.9)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(bed_area, facing="front")

    scene.export("results/test04_relative_nested_clone.blend")


# ---------------------------------------------------------------------------
# 05  AroundGroup — place_rectilinear (dining table with chairs)
# ---------------------------------------------------------------------------
def test_05():
    """AroundGroup: dining table with 3 chairs on each long side, 2 on each short side"""
    header(5, "AroundGroup place_rectilinear (dining setup)")
    scene = SceneProgRoom("test05", seed=SEED)

    with scene.AroundGroup() as dining:
        table = scene.AddAsset("a large rectangular dining table with a dark wood finish")
        chair = scene.AddAsset("an elegant dining chair with a cushioned seat")
        dining.set_anchor(table)
        dining.place_rectilinear(
            longer_side1=3 * chair,
            longer_side2=3 * chair,
            shorter_side1=2 * chair,
            shorter_side2=2 * chair,
        )

    with scene.RoomGroup() as room:
        room.place_on_center(dining, facing="front")

    scene.export("results/test05_around_rectilinear.blend")


# ---------------------------------------------------------------------------
# 06  AroundGroup — place_circle (round table with chairs)
# ---------------------------------------------------------------------------
def test_06():
    """AroundGroup: round table with 4 chairs arranged in a full circle"""
    header(6, "AroundGroup place_circle")
    scene = SceneProgRoom("test06", seed=SEED)

    with scene.AroundGroup() as seating:
        table = scene.AddAsset("a round wooden coffee table")
        chair = scene.AddAsset("an upholstered accent chair")
        seating.set_anchor(table)
        seating.place_circle(objects=4 * chair)

    with scene.RoomGroup() as room:
        room.place_on_center(seating, facing="front")

    scene.export("results/test06_around_circle.blend")


# ---------------------------------------------------------------------------
# 07  AroundGroup — place_arc (sofa with chairs in arc in front)
# ---------------------------------------------------------------------------
def test_07():
    """AroundGroup: sofa as anchor, 2 chairs placed in an arc in front"""
    header(7, "AroundGroup place_arc")
    scene = SceneProgRoom("test07", seed=SEED)

    with scene.AroundGroup(sparsity=0.5) as seating:
        sofa  = scene.AddAsset("a modern 3-seat sofa")
        chair = scene.AddAsset("a cozy lounge chair")
        seating.set_anchor(sofa)
        seating.place_arc(objects=2 * chair)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating, facing="front")

    scene.export("results/test07_around_arc.blend")


# ---------------------------------------------------------------------------
# 08  GridGroup — place_row (single row of chairs)
# ---------------------------------------------------------------------------
def test_08():
    """GridGroup: 4 chairs placed in a single row"""
    header(8, "GridGroup place_row")
    scene = SceneProgRoom("test08", seed=SEED)

    with scene.GridGroup() as row:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        row.place_row(4 * chair)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(row, facing="front")

    scene.export("results/test08_grid_row.blend")


# ---------------------------------------------------------------------------
# 09  GridGroup — place_grid (desk+chair units in a 2D grid)
# ---------------------------------------------------------------------------
def test_09():
    """GridGroup: 6 desk-chair units arranged in a 3-column grid (classroom)"""
    header(9, "GridGroup place_grid (classroom)")
    scene = SceneProgRoom("test09", seed=SEED)

    with scene.RelativeGroup() as desk_unit:
        desk  = scene.AddAsset("a student desk with a wooden top and metal legs")
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        desk_unit.set_anchor(desk)
        desk_unit.place_on_front_adjacent(chair)

    with scene.GridGroup() as classroom:
        classroom.place_grid(6 * desk_unit, cols=3)

    with scene.RoomGroup() as room:
        room.place_on_center(classroom, facing="front")

    scene.export("results/test09_grid_classroom.blend")


# ---------------------------------------------------------------------------
# 10  RoomGroup — multiple wall placements
# ---------------------------------------------------------------------------
def test_10():
    """RoomGroup: sofa on back wall, cabinet on right wall, lamp and plant in corners"""
    header(10, "RoomGroup multi-wall placement")
    scene = SceneProgRoom("test10", seed=SEED)

    sofa    = scene.AddAsset("a modern 3-seat sofa")
    cabinet = scene.AddAsset("a tall wooden wardrobe with mirrored doors")
    lamp    = scene.AddAsset("a tall floor lamp")
    plant   = scene.AddAsset("a medium indoor potted plant")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_right_wall_left(cabinet, facing="left")
        room.place_on_left_wall_right(lamp, facing="right")
        room.place_on_front_right_corner(plant, facing="left")

    scene.export("results/test10_room_multiwall.blend")


# ---------------------------------------------------------------------------
# 11  Full bedroom (from test2.py) — multi-level hierarchy in RoomGroup
# ---------------------------------------------------------------------------
def test_11():
    """Full bedroom: nightstand_area (lamp on top) nested inside bed_area, all in RoomGroup"""
    header(11, "Full bedroom hierarchy (test2.py scene)")
    scene = SceneProgRoom("test11", seed=SEED)

    with scene.RelativeGroup() as nightstand_area:
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        lamp       = scene.AddAsset("a modern table lamp with a white shade")
        nightstand_area.set_anchor(nightstand)
        nightstand_area.place_on_top(lamp)

    with scene.RelativeGroup() as bed_area:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame and a plush mattress")
        bed_area.set_anchor(bed)
        bed_area.place_on_back_left(nightstand_area)
        bed_area.place_on_back_right(1 * nightstand_area)
        bed_area.place_rug("a soft neutral area rug", size=0.9)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(bed_area, facing="front")
        cabinet = scene.AddAsset("a tall and wide wooden wardrobe with mirrored doors")
        room.place_on_right_wall_left(cabinet, facing="left")

    scene.export("results/test11_full_bedroom.blend")


# ---------------------------------------------------------------------------
# 12  Hierarchical optimization — AroundGroup inside RoomGroup
#     Tests that the inner group freezes as a single unit for outer-level opt
# ---------------------------------------------------------------------------
def test_12():
    """Hierarchical opt: dining group (AroundGroup) placed inside RoomGroup alongside sofa"""
    header(12, "Hierarchical optimization (AroundGroup inside RoomGroup)")
    scene = SceneProgRoom("test12", seed=SEED)

    with scene.AroundGroup() as dining:
        table = scene.AddAsset("a large rectangular dining table")
        chair = scene.AddAsset("an elegant dining chair")
        dining.set_anchor(table)
        dining.place_rectilinear(
            longer_side1=2 * chair,
            longer_side2=2 * chair,
            shorter_side1=1 * chair,
            shorter_side2=1 * chair,
        )

    with scene.RelativeGroup() as seating:
        sofa  = scene.AddAsset("a modern 3-seat sofa")
        table2 = scene.AddAsset("a rectangular wooden coffee table")
        seating.set_anchor(sofa)
        seating.place_on_front(table2)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating, facing="front")
        room.place_on_back_left(dining, facing="front")

    scene.export("results/test12_hierarchical_opt.blend")


# ---------------------------------------------------------------------------
# 13  OverlapConstraint — explicit before/after position logging
# ---------------------------------------------------------------------------
def test_13():
    """OverlapConstraint: three overlapping objects are separated; logs before/after positions"""
    header(13, "OverlapConstraint position logging")
    scene = SceneProgRoom("test13", seed=SEED)
    sofa  = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    chair = scene.AddAsset("a cozy lounge chair")

    # deliberately stack all three objects at the same x, forcing overlaps
    positions = [(2.3, 0, 2.5), (2.5, 0, 2.5), (2.7, 0, 2.5)]
    print_positions("before (no compile yet)", [sofa, table, chair])

    with BasicRoomGroup(scene, WIDTH=6.0, DEPTH=6.0, HEIGHT=3.0) as room:
        room.place([sofa, table, chair], positions=positions, rotations=[0, 0, 0])

    print_positions("after OverlapConstraint + GradSolver", [sofa, table, chair])

    # verify objects moved apart: no pair should have x-positions within 0.3 m of each other
    locs = [o.get_location()[0] for o in [sofa, table, chair]]
    for i in range(len(locs)):
        for j in range(i + 1, len(locs)):
            assert abs(locs[i] - locs[j]) > 0.05, \
                f"Objects {i} and {j} still overlapping after optimization"

    scene.export("results/test13_overlap.blend")


# ---------------------------------------------------------------------------
# 14  OutOfBoundsConstraint — object placed outside room bounds gets pulled in
# ---------------------------------------------------------------------------
def test_14():
    """OutOfBoundsConstraint: sofa at x=4.5 (right edge 5.5) in 5.0-wide room is pulled toward boundary"""
    header(14, "OutOfBoundsConstraint")
    scene = SceneProgRoom("test14", seed=SEED)
    sofa  = scene.AddAsset("a modern 3-seat sofa")
    chair = scene.AddAsset("a cozy lounge chair")

    start_x = 4.5  # sofa half-width ~1 m → right edge at ~5.5, 0.5 m outside WIDTH=5.0
    with BasicRoomGroup(scene, WIDTH=5.0, DEPTH=5.0, HEIGHT=3.0) as room:
        room.place([sofa, chair],
                   positions=[(start_x, 0, 2.5), (2.5, 0, 2.5)],
                   rotations=[0, 0])

    print_positions("after OutOfBoundsConstraint + GradSolver", [sofa, chair])
    aabb = sofa.get_aabb()
    # sofa must have moved left (toward the room) relative to start
    assert sofa.get_location()[0] < start_x, \
        f"Sofa at x={sofa.get_location()[0]:.3f} did not move inward from start x={start_x}"

    scene.export("results/test14_outofbounds.blend")


# ---------------------------------------------------------------------------
# 15  ClearanceConstraint — ensures minimum clearance in front of sofa
# ---------------------------------------------------------------------------
def test_15():
    """ClearanceConstraint: coffee table too close to sofa front face is pushed back to 0.6 m"""
    header(15, "ClearanceConstraint (front clearance)")
    scene = SceneProgRoom("test15", seed=SEED)
    sofa  = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")

    # sofa at z=1.5, table at z=2.0 → gap < 0.6 m → clearance constraint should push table
    hooks = [lambda r: r.ClearanceConstraint(sofa, distance=0.6, dir="front")]

    with ConstraintRoom(scene, WIDTH=5.0, DEPTH=5.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([sofa, table],
                   positions=[(2.5, 0, 1.5), (2.5, 0, 2.0)],
                   rotations=[0, 0])

    print_positions("after ClearanceConstraint", [sofa, table])
    scene.export("results/test15_clearance.blend")


# ---------------------------------------------------------------------------
# 16  AccessConstraint — nightstand must stay within side-access range of bed
# ---------------------------------------------------------------------------
def test_16():
    """AccessConstraint: nightstand drifting too far from bed side is pulled back"""
    header(16, "AccessConstraint (side access distance)")
    scene = SceneProgRoom("test16", seed=SEED)
    bed        = scene.AddAsset("a queen-sized bed with a wooden frame")
    nightstand = scene.AddAsset("a small wooden nightstand with a drawer")

    hooks = [lambda r: r.AccessConstraint(bed, nightstand, min_dist=0.05, max_dist=0.25, dir="sides")]

    # nightstand starts 1.5 m away from bed — too far
    with ConstraintRoom(scene, WIDTH=5.0, DEPTH=5.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([bed, nightstand],
                   positions=[(2.5, 0, 2.5), (4.5, 0, 2.5)],
                   rotations=[0, 0])

    print_positions("after AccessConstraint", [bed, nightstand])
    scene.export("results/test16_access.blend")


# ---------------------------------------------------------------------------
# 17  VisibilityConstraint — obstacle between TV and sofa is cleared aside
# ---------------------------------------------------------------------------
def test_17():
    """VisibilityConstraint: plant between sofa and TV gets pushed out of the sightline"""
    header(17, "VisibilityConstraint (clear sightline)")
    scene = SceneProgRoom("test17", seed=SEED)
    sofa  = scene.AddAsset("a modern 3-seat sofa")
    tv    = scene.AddAsset("a flat-screen television on a low stand")
    plant = scene.AddAsset("a medium indoor potted plant")

    hooks = [lambda r: r.VisibilityConstraint(sofa, tv)]

    # sofa at z=1.0, TV at z=4.5, plant directly between them at z=2.8
    with ConstraintRoom(scene, WIDTH=5.0, DEPTH=6.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([sofa, tv, plant],
                   positions=[(2.5, 0, 1.0), (2.5, 0, 4.5), (2.5, 0, 2.8)],
                   rotations=[0, 180, 0])

    print_positions("after VisibilityConstraint", [sofa, tv, plant])
    scene.export("results/test17_visibility.blend")


# ---------------------------------------------------------------------------
# 18  ObjectProportionsConstraint (VLM) — triggered by AnchorGroup.compile()
#     NOTE: requires render + LLM call; slow
# ---------------------------------------------------------------------------
def test_18():
    """ObjectProportionsConstraint (VLM): AnchorGroup auto-checks proportions after placement"""
    header(18, "ObjectProportionsConstraint (VLM) [slow]")
    scene = SceneProgRoom("test18", seed=SEED)

    with scene.RelativeGroup() as seating:
        sofa  = scene.AddAsset("a modern 3-seat sofa")
        table = scene.AddAsset("a rectangular wooden coffee table")
        seating.set_anchor(sofa)
        seating.place_on_front(table)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating, facing="front")

    feedback = scene.vlm_feedback or ""
    print(f"  VLM feedback:\n    {feedback or '(none)'}")
    scene.export("results/test18_proportions_vlm.blend")


# ---------------------------------------------------------------------------
# 19  RoomProportionsConstraint (VLM) — triggered by RoomGroup.compile()
#     NOTE: requires render + LLM call; slow
# ---------------------------------------------------------------------------
def test_19():
    """RoomProportionsConstraint (VLM): RoomGroup auto-checks whether room feels right-sized"""
    header(19, "RoomProportionsConstraint (VLM) [slow]")
    scene = SceneProgRoom("test19", seed=SEED)

    sofa  = scene.AddAsset("a modern 3-seat sofa")
    plant = scene.AddAsset("a medium indoor potted plant")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_front_left_corner(plant, facing="right")

    feedback = scene.vlm_feedback or ""
    print(f"  VLM feedback:\n    {feedback or '(none)'}")
    scene.export("results/test19_roomsize_vlm.blend")


# ---------------------------------------------------------------------------
# 20  WallOverlapConstraint (VLM) — triggered by RoomGroup.compile()
#     NOTE: requires render + LLM call; slow
# ---------------------------------------------------------------------------
def test_20():
    """WallOverlapConstraint (VLM): RoomGroup checks wall-mounted objects don't collide"""
    header(20, "WallOverlapConstraint (VLM) [slow]")
    scene = SceneProgRoom("test20", seed=SEED)

    sofa    = scene.AddAsset("a modern 3-seat sofa")
    cabinet = scene.AddAsset("a tall wooden wardrobe with mirrored doors")
    cabinet2 = scene.AddAsset("a tall wooden wardrobe with mirrored doors")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_right_wall_left(cabinet, facing="left")
        room.place_on_right_wall_right(cabinet2, facing="left")

    feedback = scene.vlm_feedback or ""
    print(f"  VLM feedback:\n    {feedback or '(none)'}")
    scene.export("results/test20_walloverlap_vlm.blend")


# ---------------------------------------------------------------------------
# 21  RoomGroup — place_walls + place_door + place_window_picture
# ---------------------------------------------------------------------------
def test_21():
    """RoomGroup: textured walls with a door on the right wall and a picture window on the left"""
    header(21, "place_walls + place_door + place_window_picture")
    scene = SceneProgRoom("test21", seed=SEED)

    sofa = scene.AddAsset("a modern 3-seat sofa")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )
        room.place_door("right_wall", position="right")
        room.place_window_picture("left_wall")

    scene.export("results/test21_walls_door_window.blend")


# ---------------------------------------------------------------------------
# 22  RoomGroup — wall-mounted objects (place_on_wall_back_center)
# ---------------------------------------------------------------------------
def test_22():
    """RoomGroup: painting hung on back wall above sofa; mirror on right wall above cabinet"""
    header(22, "Wall-mounted objects (place_on_wall_back_center / _right_center)")
    scene = SceneProgRoom("test22", seed=SEED)

    sofa    = scene.AddAsset("a modern 3-seat sofa")
    cabinet = scene.AddAsset("a tall wooden wardrobe with mirrored doors")
    painting = scene.AddAsset("a large abstract painting in a dark frame")
    mirror   = scene.AddAsset("a round decorative mirror")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_right_wall_left(cabinet, facing="left")
        room.place_on_wall_back_center(painting)
        room.place_on_wall_right_left(mirror)

    scene.export("results/test22_wall_art.blend")


# ---------------------------------------------------------------------------
# 23  RoomGroup — place_on_wall_freeform (gallery wall)
# ---------------------------------------------------------------------------
def test_23():
    """RoomGroup: three paintings spread evenly across back wall using place_on_wall_freeform"""
    header(23, "place_on_wall_freeform (gallery wall)")
    scene = SceneProgRoom("test23", seed=SEED)

    sofa = scene.AddAsset("a modern 3-seat sofa")
    p1   = scene.AddAsset("a small landscape painting")
    p2   = scene.AddAsset("a medium abstract painting")
    p3   = scene.AddAsset("a small portrait painting")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )
        room.place_on_wall_freeform("back_wall", [p1, p2, p3])

    scene.export("results/test23_gallery_wall.blend")


# ---------------------------------------------------------------------------
# 24  add_lighting — ceiling light placement inside a RelativeGroup in RoomGroup
# ---------------------------------------------------------------------------
def test_24():
    """AnchorGroup.add_lighting: ceiling pendant lights distributed over a seating area"""
    header(24, "add_lighting (ceiling pendant lights)")
    scene = SceneProgRoom("test24", seed=SEED)

    with scene.RelativeGroup() as seating:
        sofa   = scene.AddAsset("a modern 3-seat sofa")
        table  = scene.AddAsset("a rectangular wooden coffee table")
        seating.set_anchor(sofa)
        seating.place_on_front(table)
        seating.add_lighting("a simple pendant ceiling light", density=0.5)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating, facing="front")

    scene.export("results/test24_lighting.blend")


# ---------------------------------------------------------------------------
# 25  RelativeGroup — place_on_back_adjacent + place_on_left_further
# ---------------------------------------------------------------------------
def test_25():
    """RelativeGroup: desk with chair placed immediately behind (adjacent); lamp at circulation distance left"""
    header(25, "RelativeGroup place_on_back_adjacent + place_on_left_further")
    scene = SceneProgRoom("test25", seed=SEED)

    with scene.RelativeGroup() as workstation:
        desk  = scene.AddAsset("a student desk with a wooden top and metal legs")
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        lamp  = scene.AddAsset("a tall floor lamp")
        workstation.set_anchor(desk)
        workstation.place_on_back_adjacent(chair)
        workstation.place_on_left_further(lamp)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(workstation, facing="front")

    scene.export("results/test25_adjacent_further.blend")


# ---------------------------------------------------------------------------
# 26  GridGroup.place_rectilinear — surrounding rows (classroom border)
# ---------------------------------------------------------------------------
def test_26():
    """GridGroup.place_rectilinear: chairs forming a rectangular border (top/bottom rows + side columns)"""
    header(26, "GridGroup place_rectilinear")
    scene = SceneProgRoom("test26", seed=SEED)

    with scene.GridGroup(sparsity=0.2) as surround:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        surround.place_rectilinear(
            width1=4 * chair,   # top row
            width2=4 * chair,   # bottom row
            depth1=2 * chair,   # left column
            depth2=2 * chair,   # right column
        )

    with scene.RoomGroup() as room:
        room.place_on_center(surround, facing="front")

    scene.export("results/test26_grid_rectilinear.blend")


# ---------------------------------------------------------------------------
# 27  GridGroup.place_arc — arc with towards=obj (audience facing stage)
# ---------------------------------------------------------------------------
def test_27():
    """GridGroup.place_arc: 6 chairs arranged in a curved arc all facing toward a central lectern"""
    header(27, "GridGroup place_arc with towards=target")
    scene = SceneProgRoom("test27", seed=SEED)

    lectern = scene.AddAsset("a wooden lectern or podium")
    chair   = scene.AddAsset("a standard classroom chair with a plastic seat")

    with scene.GridGroup(sparsity=0.4) as audience:
        audience.place_arc(6 * chair, towards=lectern)

    with scene.RoomGroup() as room:
        room.place_on_front_wall_center(lectern, facing="back")
        room.place_on_back_wall_center(audience, facing="front")

    scene.export("results/test27_grid_arc_towards.blend")


# ---------------------------------------------------------------------------
# 28  AddAsset size overrides — modulate_scale, width=, depth=
# ---------------------------------------------------------------------------
def test_28():
    """AddAsset: modulate_scale=0.7 shrinks a sofa; width=1.2 forces coffee table to 1.2 m wide"""
    header(28, "AddAsset modulate_scale + width/depth overrides")
    scene = SceneProgRoom("test28", seed=SEED)

    sofa  = scene.AddAsset("a modern 3-seat sofa", modulate_scale=0.7)
    table = scene.AddAsset("a rectangular wooden coffee table", width=1.2)
    plant = scene.AddAsset("a medium indoor potted plant", depth=0.4)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_front_wall_center(table, facing="back")
        room.place_on_front_right_corner(plant, facing="left")

    # verify width override landed close to target
    actual_width = table.get_width()
    assert abs(actual_width - 1.2) < 0.3, \
        f"Table width {actual_width:.3f} far from target 1.2 m"

    scene.export("results/test28_asset_size_overrides.blend")


# ---------------------------------------------------------------------------
# 29  AroundGroup sparsity — compare dense vs sparse chair arrangement
# ---------------------------------------------------------------------------
def test_29():
    """AroundGroup.place_circle: sparsity=0.0 (tight) vs sparsity=1.0 (spread) around a round table"""
    header(29, "AroundGroup sparsity parameter")
    scene_dense  = SceneProgRoom("test29_dense",  seed=SEED)
    scene_sparse = SceneProgRoom("test29_sparse", seed=SEED)

    # dense
    with scene_dense.AroundGroup(sparsity=0.0) as seating:
        table = scene_dense.AddAsset("a round wooden coffee table")
        chair = scene_dense.AddAsset("an upholstered accent chair")
        seating.set_anchor(table)
        seating.place_circle(objects=4 * chair)
    with scene_dense.RoomGroup() as room:
        room.place_on_center(seating, facing="front")
    scene_dense.export("results/test29_dense.blend")

    # sparse
    with scene_sparse.AroundGroup(sparsity=1.0) as seating2:
        table2 = scene_sparse.AddAsset("a round wooden coffee table")
        chair2 = scene_sparse.AddAsset("an upholstered accent chair")
        seating2.set_anchor(table2)
        seating2.place_circle(objects=4 * chair2)
    with scene_sparse.RoomGroup() as room2:
        room2.place_on_center(seating2, facing="front")
    scene_sparse.export("results/test29_sparse.blend")


# ---------------------------------------------------------------------------
# 30  SentenceASCIIGenerator — text-based layout of objects
# ---------------------------------------------------------------------------
def test_30():
    """SentenceASCIIGenerator: arrange small plants in the shape of the word 'HI'"""
    header(30, "SentenceASCIIGenerator text layout")
    scene = SceneProgRoom("test30", seed=SEED)

    plant = scene.AddAsset("a small succulent plant")

    with scene.SentenceASCIIGenerator() as ascii_gen:
        ascii_gen.place(plant, "HI")

    with scene.RoomGroup() as room:
        room.place_on_center(ascii_gen, facing="front")

    scene.export("results/test30_ascii_generator.blend")


# ---------------------------------------------------------------------------
# 31  RoomGroup.modulate_scale — scaling the inferred room size
# ---------------------------------------------------------------------------
def test_31():
    """RoomGroup(modulate_scale=1.5): same furniture, room expanded 1.5× so more space around objects"""
    header(31, "RoomGroup modulate_scale")
    scene = SceneProgRoom("test31", seed=SEED)

    sofa  = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")

    with scene.RoomGroup(modulate_scale=1.5) as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_front_wall_center(table, facing="back")

    assert room.WIDTH > 0 and room.DEPTH > 0, "Room should have non-zero dimensions"
    print(f"  Room dims: {room.WIDTH:.2f} × {room.DEPTH:.2f}")

    scene.export("results/test31_modulate_scale.blend")


# ---------------------------------------------------------------------------
# 32  RelativeGroup — peripheral "_further" ring (circulation distance)
# ---------------------------------------------------------------------------
def test_32():
    """RelativeGroup _further: object placed with place_on_left_further sits farther from
    the anchor than one placed with plain place_on_left (and front/right/back_further run)."""
    header(32, "RelativeGroup _further ring placement")
    scene = SceneProgRoom("test32", seed=SEED)

    with scene.RelativeGroup() as grp:
        table = scene.AddAsset("a rectangular wooden coffee table")
        near  = scene.AddAsset("a cozy lounge chair")
        far   = scene.AddAsset("a tall floor lamp")
        right = scene.AddAsset("a medium indoor potted plant")
        front = scene.AddAsset("a small wooden nightstand with a drawer")
        back  = scene.AddAsset("a small wooden nightstand with a drawer")
        grp.set_anchor(table)
        grp.place_on_left(near)
        grp.place_on_left_further(far)
        grp.place_on_right_further(right)
        grp.place_on_front_further(front)
        grp.place_on_back_further(back)

    anchor = np.array(table.get_location())
    d_near = np.linalg.norm(np.array(near.get_location()) - anchor)
    d_far  = np.linalg.norm(np.array(far.get_location())  - anchor)
    print(f"  near (place_on_left)         dist from anchor = {d_near:.3f}")
    print(f"  far  (place_on_left_further) dist from anchor = {d_far:.3f}")
    assert d_far > d_near, \
        f"_further object ({d_far:.3f}) should be farther than plain placement ({d_near:.3f})"

    with scene.RoomGroup() as room:
        room.place_on_center(grp, facing="front")

    scene.export("results/test32_relative_further.blend")


# ---------------------------------------------------------------------------
# 33  RelativeGroup — inner corners (front_left / front_right untested)
# ---------------------------------------------------------------------------
def _quadrant(obj, anchor_loc):
    """Return (sign_x, sign_z) of obj relative to anchor center."""
    loc = np.array(obj.get_location())
    return (int(np.sign(round(loc[0] - anchor_loc[0], 3))),
            int(np.sign(round(loc[2] - anchor_loc[2], 3))))

def test_33():
    """RelativeGroup inner corners: the four corner placements land in four distinct
    quadrants around the anchor (exercises place_on_front_left / place_on_front_right)."""
    header(33, "RelativeGroup inner corner placements")
    scene = SceneProgRoom("test33", seed=SEED)

    with scene.RelativeGroup() as grp:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        c_fl = scene.AddAsset("a small wooden nightstand with a drawer")
        c_fr = scene.AddAsset("a small wooden nightstand with a drawer")
        c_bl = scene.AddAsset("a small wooden nightstand with a drawer")
        c_br = scene.AddAsset("a small wooden nightstand with a drawer")
        grp.set_anchor(bed)
        grp.place_on_front_left(c_fl)
        grp.place_on_front_right(c_fr)
        grp.place_on_back_left(c_bl)
        grp.place_on_back_right(c_br)

    anchor = np.array(bed.get_location())
    quads = {_quadrant(o, anchor) for o in (c_fl, c_fr, c_bl, c_br)}
    print(f"  occupied quadrants: {sorted(quads)}")
    assert len(quads) == 4, f"Expected 4 distinct quadrants, got {len(quads)}: {quads}"

    with scene.RoomGroup() as room:
        room.place_on_center(grp, facing="front")

    scene.export("results/test33_relative_corners.blend")


# ---------------------------------------------------------------------------
# 34  RelativeGroup — corner "_further" placements
# ---------------------------------------------------------------------------
def test_34():
    """RelativeGroup corner _further: the four corner-further placements occupy four
    distinct quadrants, each farther from the anchor than half its own diagonal."""
    header(34, "RelativeGroup corner _further placements")
    scene = SceneProgRoom("test34", seed=SEED)

    with scene.RelativeGroup() as grp:
        table = scene.AddAsset("a rectangular wooden coffee table")
        fl = scene.AddAsset("a medium indoor potted plant")
        fr = scene.AddAsset("a medium indoor potted plant")
        bl = scene.AddAsset("a medium indoor potted plant")
        br = scene.AddAsset("a medium indoor potted plant")
        grp.set_anchor(table)
        grp.place_on_front_left_further(fl)
        grp.place_on_front_right_further(fr)
        grp.place_on_back_left_further(bl)
        grp.place_on_back_right_further(br)

    anchor = np.array(table.get_location())
    quads = {_quadrant(o, anchor) for o in (fl, fr, bl, br)}
    half_diag = np.linalg.norm(table.get_aabb()[1] - table.get_aabb()[0]) / 2
    min_dist = min(np.linalg.norm(np.array(o.get_location()) - anchor) for o in (fl, fr, bl, br))
    print(f"  occupied quadrants: {sorted(quads)}  min_dist={min_dist:.3f}  half_diag={half_diag:.3f}")
    assert len(quads) == 4, f"Expected 4 distinct quadrants, got {len(quads)}"
    assert min_dist > half_diag, "corner_further objects should sit outside the anchor footprint"

    with scene.RoomGroup() as room:
        room.place_on_center(grp, facing="front")

    scene.export("results/test34_relative_corner_further.blend")


# ---------------------------------------------------------------------------
# 35  GridGroup — randomness parameter (jittered vs uniform spacing)
# ---------------------------------------------------------------------------
def test_35():
    """GridGroup.randomness: randomness=0 yields perfectly uniform inter-chair gaps;
    randomness>0 jitters them (gap spread becomes non-zero)."""
    header(35, "GridGroup randomness parameter")
    scene = SceneProgRoom("test35", seed=SEED)

    def gap_std(group):
        xs = sorted(c.get_location()[0] for c in group.children)
        gaps = np.diff(xs)
        return float(np.std(gaps))

    with scene.GridGroup(sparsity=0.5, randomness=0.0) as uniform_row:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        uniform_row.place_row(8 * chair)
    std_uniform = gap_std(uniform_row)

    with scene.GridGroup(sparsity=0.5, randomness=0.9) as jittered_row:
        chair2 = scene.AddAsset("a standard classroom chair with a plastic seat")
        jittered_row.place_row(8 * chair2)
    std_jittered = gap_std(jittered_row)

    print(f"  gap std  randomness=0.0 -> {std_uniform:.5f}")
    print(f"  gap std  randomness=0.9 -> {std_jittered:.5f}")
    assert std_uniform < 1e-4, f"uniform row gaps should be equal, std={std_uniform:.5f}"
    assert std_jittered > 1e-3, f"jittered row gaps should vary, std={std_jittered:.5f}"

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(uniform_row, facing="front")
        room.place_on_front_wall_center(jittered_row, facing="back")

    scene.export("results/test35_grid_randomness.blend")


# ---------------------------------------------------------------------------
# 36  place_on_wall_freeform on a SIDE wall (left) — symmetric distribution
# ---------------------------------------------------------------------------
def test_36():
    """place_on_wall_freeform (left wall): paintings spread evenly along the wall depth and
    are centered about it (guards the side-wall center-coordinate path)."""
    header(36, "place_on_wall_freeform on left wall (symmetry)")
    scene = SceneProgRoom("test36", seed=SEED)

    sofa = scene.AddAsset("a modern 3-seat sofa")
    p1   = scene.AddAsset("a small landscape painting")
    p2   = scene.AddAsset("a medium abstract painting")
    p3   = scene.AddAsset("a small portrait painting")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )
        room.place_on_wall_freeform("left_wall", [p1, p2, p3])

    depth = room.DEPTH
    zs = sorted(p.get_location()[2] for p in (p1, p2, p3))
    centroid = float(np.mean(zs))
    print(f"  room depth={depth:.2f}  painting z-centers={[round(z,3) for z in zs]}  centroid={centroid:.3f}")
    # paintings should be centered about the wall midpoint, not shifted to one end
    assert abs(centroid - depth / 2) < 0.15 * depth, \
        f"paintings centroid {centroid:.3f} not centered on wall depth midpoint {depth/2:.3f}"
    # and evenly spaced
    gaps = np.diff(zs)
    assert np.std(gaps) < 0.1, f"paintings not evenly spaced along wall, gap std={np.std(gaps):.3f}"

    scene.export("results/test36_freeform_left_wall.blend")


# ---------------------------------------------------------------------------
# 37  RoomGroup — grid placement points + corners coverage
# ---------------------------------------------------------------------------
def test_37():
    """RoomGroup grid points: place objects on back/front/left/right and all four corners;
    every object stays within room bounds and occupies a distinct footprint."""
    header(37, "RoomGroup grid points + corners coverage")
    scene = SceneProgRoom("test37", seed=SEED)

    back  = scene.AddAsset("a medium indoor potted plant")
    front = scene.AddAsset("a medium indoor potted plant")
    left  = scene.AddAsset("a medium indoor potted plant")
    right = scene.AddAsset("a medium indoor potted plant")
    bl    = scene.AddAsset("a tall floor lamp")
    br    = scene.AddAsset("a tall floor lamp")
    fl    = scene.AddAsset("a tall floor lamp")
    fr    = scene.AddAsset("a tall floor lamp")
    objs  = [back, front, left, right, bl, br, fl, fr]

    with scene.RoomGroup() as room:
        room.place_on_back(back, facing="front")
        room.place_on_front(front, facing="back")
        room.place_on_left(left, facing="right")
        room.place_on_right(right, facing="left")
        room.place_on_back_left_corner(bl, facing="front")
        room.place_on_back_right_corner(br, facing="front")
        room.place_on_front_left_corner(fl, facing="back")
        room.place_on_front_right_corner(fr, facing="back")

    W, D = room.WIDTH, room.DEPTH
    centers = []
    for o in objs:
        loc = o.get_location()
        aabb = o.get_aabb()
        assert aabb[0, 0] >= -0.5 and aabb[1, 0] <= W + 0.5, \
            f"{o.description} out of X bounds: x=[{aabb[0,0]:.2f},{aabb[1,0]:.2f}] W={W:.2f}"
        assert aabb[0, 2] >= -0.5 and aabb[1, 2] <= D + 0.5, \
            f"{o.description} out of Z bounds: z=[{aabb[0,2]:.2f},{aabb[1,2]:.2f}] D={D:.2f}"
        centers.append((round(loc[0], 2), round(loc[2], 2)))
    assert len(set(centers)) == len(centers), f"objects share footprints: {centers}"

    scene.export("results/test37_room_grid_points.blend")


# ---------------------------------------------------------------------------
# 38  RoomGroup — window variants (floor-to-ceiling + standard)
# ---------------------------------------------------------------------------
def test_38():
    """RoomGroup windows: place_window_floor_to_ceiling and place_window_standard register
    wall objects without error (the two window types untested by test_21)."""
    header(38, "place_window_floor_to_ceiling + place_window_standard")
    scene = SceneProgRoom("test38", seed=SEED)

    sofa = scene.AddAsset("a modern 3-seat sofa")

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )
        room.place_window_floor_to_ceiling("left_wall")
        room.place_window_standard("right_wall", position="center")

    n_wall_objs = len(scene.wall_objects)
    print(f"  registered wall objects: {n_wall_objs}")
    assert n_wall_objs >= 2, f"expected at least 2 window wall objects, got {n_wall_objs}"

    scene.export("results/test38_window_variants.blend")


# ---------------------------------------------------------------------------
# 39  Wall art on an EMPTY back wall — all three slots (no support furniture)
# ---------------------------------------------------------------------------
def test_39():
    """place_on_wall_back_left/center/right with no furniture below: exercises the
    no-support 'else' branch. The three pieces order left<center<right across the wall,
    sit at the same mid-wall height, and hug the back wall (small z)."""
    header(39, "Wall art on empty back wall (left/center/right)")
    scene = SceneProgRoom("test39", seed=SEED)

    # floor furniture in the room center keeps the back-wall slots empty
    table = scene.AddAsset("a rectangular wooden coffee table")
    pL = scene.AddAsset("a small landscape painting")
    pC = scene.AddAsset("a medium abstract painting")
    pR = scene.AddAsset("a small portrait painting")

    with scene.RoomGroup() as room:
        room.place_on_center(table, facing="front")
        room.place_on_wall_back_left(pL)
        room.place_on_wall_back_center(pC)
        room.place_on_wall_back_right(pR)

    W, D = room.WIDTH, room.DEPTH
    xs = [pL.get_location()[0], pC.get_location()[0], pR.get_location()[0]]
    ys = [p.get_location()[1] for p in (pL, pC, pR)]
    zs = [p.get_location()[2] for p in (pL, pC, pR)]
    print(f"  room {W:.2f}x{D:.2f}  xs={[round(x,2) for x in xs]}  ys={[round(y,2) for y in ys]}  zs={[round(z,2) for z in zs]}")

    assert xs[0] < xs[1] < xs[2], f"back-wall art not ordered left<center<right: {xs}"
    assert all(0 <= x <= W for x in xs), f"art outside room width: {xs}"
    assert max(ys) - min(ys) < 0.1, f"art not at a consistent height: {ys}"
    assert all(z < D / 2 for z in zs), f"back-wall art should hug the back wall (small z): {zs}"

    scene.export("results/test39_empty_back_wall.blend")


# ---------------------------------------------------------------------------
# 40  Wall art on front + left walls — covers front (rot 180) & left (rot 90, z-axis)
# ---------------------------------------------------------------------------
def test_40():
    """place_on_wall_front_center (rot 180, hugs far wall) and place_on_wall_left_center
    (rot 90, hugs left wall, distributes along depth): covers the two wall orientations
    and the z-axis no-support branch untested by test_22/test_39."""
    header(40, "Wall art on front + left walls (orientation/axis)")
    scene = SceneProgRoom("test40", seed=SEED)

    table   = scene.AddAsset("a rectangular wooden coffee table")
    front_p = scene.AddAsset("a medium abstract painting")
    left_p  = scene.AddAsset("a small landscape painting")

    with scene.RoomGroup() as room:
        room.place_on_center(table, facing="front")
        room.place_on_wall_front_center(front_p)
        room.place_on_wall_left_center(left_p)

    W, D = room.WIDTH, room.DEPTH

    fz = front_p.get_location()[2]
    frot = float(front_p.get_rotation()) % 360
    lx = left_p.get_location()[0]
    lrot = float(left_p.get_rotation()) % 360
    print(f"  room {W:.2f}x{D:.2f}  front: z={fz:.2f} rot={frot:.0f}   left: x={lx:.2f} rot={lrot:.0f}")

    assert fz > D / 2, f"front-wall art should hug the far wall (large z), got z={fz:.2f} (D={D:.2f})"
    assert abs(frot - 180) < 1, f"front-wall art should face back (rot 180), got {frot:.0f}"
    assert lx < W / 2, f"left-wall art should hug the left wall (small x), got x={lx:.2f} (W={W:.2f})"
    assert abs(lrot - 90) < 1, f"left-wall art should face right (rot 90), got {lrot:.0f}"

    scene.export("results/test40_front_left_wall_art.blend")


# ---------------------------------------------------------------------------
# 41  ClearanceConstraint dir="sides" — side clearance enforced
# ---------------------------------------------------------------------------
def test_41():
    """ClearanceConstraint(dir='sides'): a side table crowding the sofa's side is pushed
    out until the lateral gap reaches the requested clearance."""
    header(41, "ClearanceConstraint (side clearance)")
    scene = SceneProgRoom("test41", seed=SEED)
    sofa  = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a small round side table")

    CLEAR = 0.8
    hooks = [lambda r: r.ClearanceConstraint(sofa, distance=CLEAR, dir="sides")]

    # table sits just to the right of the sofa with almost no gap
    with ConstraintRoom(scene, WIDTH=9.0, DEPTH=5.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([sofa, table],
                   positions=[(4.0, 0, 2.5), (5.1, 0, 2.5)],
                   rotations=[0, 0])

    print_positions("after ClearanceConstraint sides", [sofa, table])
    gap = table.get_aabb()[0, 0] - sofa.get_aabb()[1, 0]
    print(f"  lateral gap sofa->table = {gap:.3f} (target {CLEAR})")
    assert gap > 0.5, f"side clearance not enforced: gap={gap:.3f} (target {CLEAR})"

    scene.export("results/test41_clearance_sides.blend")


# ---------------------------------------------------------------------------
# 42  ClearanceConstraint dir="all" — clearance behind the anchor too
# ---------------------------------------------------------------------------
def test_42():
    """ClearanceConstraint(dir='all'): an object directly behind the sofa is pushed back —
    a clearance that dir='front' alone would never touch."""
    header(42, "ClearanceConstraint (all-around clearance)")
    scene = SceneProgRoom("test42", seed=SEED)
    sofa  = scene.AddAsset("a modern 3-seat sofa")
    plant = scene.AddAsset("a medium indoor potted plant")

    CLEAR = 0.8
    hooks = [lambda r: r.ClearanceConstraint(sofa, distance=CLEAR, dir="all")]

    # plant sits just BEHIND the sofa (smaller z); sofa faces +z (rot 0)
    sofa_z, plant_z = 3.0, 2.3
    with ConstraintRoom(scene, WIDTH=6.0, DEPTH=6.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([sofa, plant],
                   positions=[(3.0, 0, sofa_z), (3.0, 0, plant_z)],
                   rotations=[0, 0])

    print_positions("after ClearanceConstraint all", [sofa, plant])
    gap = sofa.get_aabb()[0, 2] - plant.get_aabb()[1, 2]
    print(f"  rear gap plant->sofa = {gap:.3f} (target {CLEAR})")
    assert plant.get_location()[2] < plant_z, \
        f"plant behind sofa was not pushed further back (z={plant.get_location()[2]:.3f})"
    assert gap > 0.4, f"rear clearance not enforced: gap={gap:.3f} (target {CLEAR})"

    scene.export("results/test42_clearance_all.blend")


# ---------------------------------------------------------------------------
# 43  AccessConstraint dir="front" — keep target within front-access range
# ---------------------------------------------------------------------------
def test_43():
    """AccessConstraint(dir='front'): a chair sitting too far in front of a desk is pulled in
    to within the front max-access distance (exercises the large 'front' branch)."""
    header(43, "AccessConstraint (front access distance)")
    scene = SceneProgRoom("test43", seed=SEED)
    desk  = scene.AddAsset("a student desk with a wooden top and metal legs")
    chair = scene.AddAsset("a standard classroom chair with a plastic seat")

    MIN_D, MAX_D = 0.1, 0.4
    hooks = [lambda r: r.AccessConstraint(desk, chair, min_dist=MIN_D, max_dist=MAX_D, dir="front")]

    # desk faces +z (rot 0); chair starts far in front of it
    desk_z, chair_z = 2.0, 4.2
    with ConstraintRoom(scene, WIDTH=5.0, DEPTH=6.0, HEIGHT=3.0, hooks=hooks) as room:
        room.place([desk, chair],
                   positions=[(2.5, 0, desk_z), (2.5, 0, chair_z)],
                   rotations=[0, 0])

    print_positions("after AccessConstraint front", [desk, chair])
    gap = chair.get_aabb()[0, 2] - desk.get_aabb()[1, 2]
    print(f"  front gap desk->chair = {gap:.3f} (target <= {MAX_D})")
    assert chair.get_location()[2] > desk.get_location()[2], "chair should remain in front of desk"
    assert gap < chair_z - desk_z, f"chair was not pulled closer (gap={gap:.3f})"
    assert gap <= MAX_D + 0.25, f"chair not within front access range: gap={gap:.3f} (max {MAX_D})"

    scene.export("results/test43_access_front.blend")


# ---------------------------------------------------------------------------
# Registry + runner
# ---------------------------------------------------------------------------

TESTS = {
    1:  test_01,
    2:  test_02,
    3:  test_03,
    4:  test_04,
    5:  test_05,
    6:  test_06,
    7:  test_07,
    8:  test_08,
    9:  test_09,
    10: test_10,
    11: test_11,
    12: test_12,
    # --- constraint tests ---
    13: test_13,
    14: test_14,
    15: test_15,
    16: test_16,
    17: test_17,
    # --- VLM constraint tests (slow) ---
    18: test_18,
    19: test_19,
    20: test_20,
    # --- new feature tests ---
    21: test_21,   # RoomGroup place_walls + place_door + place_window_picture
    22: test_22,   # Wall-mounted objects (place_on_wall_back_center / _right_center)
    23: test_23,   # place_on_wall_freeform (gallery wall)
    24: test_24,   # add_lighting (ceiling pendant lights)
    25: test_25,   # RelativeGroup place_on_back_adjacent + place_on_left_further
    26: test_26,   # GridGroup place_rectilinear (surrounding border)
    27: test_27,   # GridGroup place_arc with towards=target
    28: test_28,   # AddAsset modulate_scale + width/depth overrides
    29: test_29,   # AroundGroup sparsity parameter (dense vs sparse)
    30: test_30,   # SentenceASCIIGenerator text layout
    31: test_31,   # RoomGroup modulate_scale
    # --- coverage gap tests ---
    32: test_32,   # RelativeGroup _further ring placement
    33: test_33,   # RelativeGroup inner corner placements (front_left/front_right)
    34: test_34,   # RelativeGroup corner _further placements
    35: test_35,   # GridGroup randomness parameter
    36: test_36,   # place_on_wall_freeform on a side wall (symmetry)
    37: test_37,   # RoomGroup grid points + corners coverage
    38: test_38,   # place_window_floor_to_ceiling + place_window_standard
    39: test_39,   # Wall art on empty back wall (no-support else branch)
    40: test_40,   # Wall art on front + left walls (orientation/axis)
    41: test_41,   # ClearanceConstraint dir="sides"
    42: test_42,   # ClearanceConstraint dir="all" (rear clearance)
    43: test_43,   # AccessConstraint dir="front"
}


def run(n):
    fn = TESTS[n]
    try:
        fn()
        print(f"\n[PASS] test_{n:02d}")
        return True
    except Exception:
        print(f"\n[FAIL] test_{n:02d}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print("Available tests:")
        for n, fn in TESTS.items():
            print(f"  {n:02d}  {fn.__doc__}")
        print("\nUsage: python tests.py <N> [N ...]  |  python tests.py all")
        sys.exit(0)

    if args == ["all"]:
        targets = sorted(TESTS.keys())
    else:
        targets = [int(a) for a in args]

    results = {}
    for n in targets:
        results[n] = run(n)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for n, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  test_{n:02d}: {status}")

    if not all(results.values()):
        sys.exit(1)
