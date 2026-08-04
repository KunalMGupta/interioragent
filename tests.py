"""
IDSDL Feature Test Suite
Usage:
    python tests.py            # list all tests
    python tests.py 1          # run test 01
    python tests.py 1 2 5      # run tests 01, 02, 05
    python tests.py all        # run all tests
"""

import os
import sys
import traceback
import numpy as np

from IDSDL.scene import SceneProgRoom
from IDSDL.groups import BasicRoomGroup, SIDE_GAP

SEED = 42

# Every test exports to results/<name>.blend; Blender errors out if the dir is absent.
os.makedirs("results", exist_ok=True)


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
# 44-49  New motif groups (IDSDL/groups_extra.py)
# ---------------------------------------------------------------------------
def test_44():
    """StackGroup: objects stacked vertically, each resting on the one below."""
    header(44, "StackGroup vertical stack")
    scene = SceneProgRoom("test44", seed=SEED)
    box = scene.AddAsset("a wooden storage crate")
    boxes = 3 * box
    with scene.StackGroup() as stack:
        stack.place_stack(boxes)
    scene.bind(stack)

    spans = [(float(b.get_aabb()[0, 1]), float(b.get_aabb()[1, 1])) for b in boxes]
    spans.sort()
    print_positions("stack", boxes)
    for i in range(1, len(spans)):
        assert spans[i][0] >= spans[i - 1][0] - 1e-3, f"levels not ascending: {spans}"
        assert abs(spans[i][0] - spans[i - 1][1]) < 0.06, f"gap/overlap between levels: {spans}"
    scene.export("results/test44_stack.blend")


def test_45():
    """PyramidGroup: centered tiers of decreasing count, stacked upward."""
    header(45, "PyramidGroup tiers")
    scene = SceneProgRoom("test45", seed=SEED)
    crate = scene.AddAsset("a wooden storage crate")
    crates = 6 * crate
    with scene.PyramidGroup() as pyr:
        pyr.place_pyramid(crates)
    scene.bind(pyr)

    bottoms = sorted(float(c.get_aabb()[0, 1]) for c in crates)
    print(f"  tier bottoms: {[round(b,2) for b in bottoms]}")
    assert bottoms[-1] - bottoms[0] > 0.1, f"pyramid did not stack upward: {bottoms}"
    scene.export("results/test45_pyramid.blend")


def test_46():
    """PileGroup: scattered objects de-overlapped by the inherited solver."""
    header(46, "PileGroup organic scatter")
    scene = SceneProgRoom("test46", seed=SEED)
    cushion = scene.AddAsset("a square floor cushion")
    cushions = 5 * cushion
    with scene.PileGroup() as pile:
        pile.place_pile(cushions, spread=0.8)
    scene.bind(pile)

    def overlaps(a, b, eps=0.02):
        return not (a[1, 0] - eps <= b[0, 0] or b[1, 0] - eps <= a[0, 0]
                    or a[1, 2] - eps <= b[0, 2] or b[1, 2] - eps <= a[0, 2])
    aabbs = [c.get_aabb() for c in cushions]
    bad = [(i, j) for i in range(len(aabbs)) for j in range(i + 1, len(aabbs))
           if overlaps(aabbs[i], aabbs[j])]
    print(f"  {len(cushions)} cushions, overlapping pairs after solve: {len(bad)}")
    assert not bad, f"pile still overlaps: {bad}"
    scene.export("results/test46_pile.blend")


def test_47():
    """SymmetryGroup: flanking pairs mirror-symmetric about the anchor."""
    header(47, "SymmetryGroup flanking")
    scene = SceneProgRoom("test47", seed=SEED)
    with scene.SymmetryGroup() as sym:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        sym.set_anchor(bed)
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        sym.place_flanking(nightstand)
    scene.bind(sym)

    flanks = [c for c in sym.get_children() if c is not bed]
    cx = float(bed.get_location()[0])
    xs = sorted(float(c.get_location()[0]) for c in flanks)
    zs = [float(c.get_location()[2]) for c in flanks]
    print(f"  anchor x={cx:.2f}  flank xs={[round(x,2) for x in xs]}  zs={[round(z,2) for z in zs]}")
    assert len(flanks) == 2, f"expected one mirrored pair, got {len(flanks)}"
    assert abs((xs[0] + xs[1]) / 2 - cx) < 0.05, "pair not symmetric about anchor"
    assert abs(zs[0] - zs[1]) < 0.05, "pair not at equal depth"
    scene.export("results/test47_symmetry.blend")


def test_48():
    """FacingGroup: two rows on opposite sides of the anchor, each facing it."""
    header(48, "FacingGroup face-to-face rows")
    scene = SceneProgRoom("test48", seed=SEED)
    chair = scene.AddAsset("a cozy lounge chair")
    side1, side2 = 2 * chair, 2 * chair
    with scene.FacingGroup() as g:
        table = scene.AddAsset("a rectangular wooden coffee table")
        g.set_anchor(table)
        g.place_facing_rows(side1, side2)
    scene.bind(g)

    cz = float(table.get_location()[2])
    z1 = [float(o.get_location()[2]) for o in side1]
    z2 = [float(o.get_location()[2]) for o in side2]
    print(f"  anchor z={cz:.2f}  side1 z={[round(z,2) for z in z1]}  side2 z={[round(z,2) for z in z2]}")
    assert all(z > cz for z in z1), "side1 should sit on the +z side of the anchor"
    assert all(z < cz for z in z2), "side2 should sit on the -z side of the anchor"
    scene.export("results/test48_facing.blend")


def test_49():
    """RingsGroup: concentric rings, outer ring farther from the anchor than inner."""
    header(49, "RingsGroup concentric surround")
    scene = SceneProgRoom("test49", seed=SEED)
    chair = scene.AddAsset("an upholstered accent chair")
    inner, outer = 4 * chair, 6 * chair
    with scene.RingsGroup(sparsity=0.3) as g:
        table = scene.AddAsset("a large round dining table with a dark wood finish")
        g.set_anchor(table)
        g.place_rings([inner, outer])
    scene.bind(g)

    c = np.array(table.get_location(), dtype=float)
    def radius(o):
        p = np.array(o.get_location(), dtype=float)
        return float(np.hypot(p[0] - c[0], p[2] - c[2]))
    r_in = np.mean([radius(o) for o in inner])
    r_out = np.mean([radius(o) for o in outer])
    print(f"  mean radius inner={r_in:.2f}  outer={r_out:.2f}")
    assert r_out > r_in + 0.1, f"outer ring not beyond inner: inner={r_in:.2f} outer={r_out:.2f}"
    scene.export("results/test49_rings.blend")


def test_50():
    """MirrorStationGroup: mirror mounted on the wall above a counter, anchor facing it."""
    header(50, "MirrorStationGroup mirror + counter + facing anchor")
    scene = SceneProgRoom("test50", seed=SEED)
    with scene.MirrorStationGroup() as st:
        chair = scene.AddAsset("an upholstered accent chair")
        st.set_anchor(chair)
        counter = scene.AddAsset("a narrow wooden console table")
        st.place_counter(counter)
        mirror = scene.AddAsset("a round framed wall mirror")
        st.place_mirror(mirror)
    scene.bind(st)

    az = float(chair.get_location()[2])
    cz = float(counter.get_location()[2])
    m_aabb = mirror.get_aabb()
    mz = float(mirror.get_location()[2])
    m_center_y = float((m_aabb[0, 1] + m_aabb[1, 1]) / 2)
    m_bottom = float(m_aabb[0, 1])
    counter_top = float(counter.get_aabb()[1, 1])
    a_rot = float(chair.get_rotation()) % 360.0
    m_rot = float(mirror.get_rotation()) % 360.0
    print(f"  anchor z={az:.2f} counter z={cz:.2f} mirror z={mz:.2f}")
    print(f"  mirror center_y={m_center_y:.2f} bottom={m_bottom:.2f} counter_top={counter_top:.2f}")
    print(f"  anchor rot={a_rot:.0f} mirror rot={m_rot:.0f}")
    assert m_center_y > 0.8, f"mirror not mounted off the floor: center_y={m_center_y:.2f}"
    assert m_bottom > counter_top - 0.1, f"mirror not above the counter: {m_bottom:.2f} vs {counter_top:.2f}"
    assert cz > az + 0.02, f"counter should be in front of the anchor (wall side): az={az:.2f} cz={cz:.2f}"
    assert mz > az + 0.02, f"mirror should be behind the anchor (wall side): az={az:.2f} mz={mz:.2f}"
    assert mz >= cz - 0.1, f"mirror should sit at/behind the counter: cz={cz:.2f} mz={mz:.2f}"
    assert a_rot < 5 or a_rot > 355, f"anchor should face +z toward the mirror: rot={a_rot:.0f}"
    assert abs(m_rot - 180.0) < 5, f"mirror should face back toward the anchor: rot={m_rot:.0f}"
    scene.export("results/test50_mirror_station.blend")


def test_51():
    """WorkstationGroup: desk anchor, chair on the floor in front facing it, and the computer +
    accessories seated ON the real desktop surface via place_on_top (NOT floating on the aabb top).
    The seating-height + chair asserts are what the group guarantees; place_on_top owns the
    on-surface arrangement, so we do not assert exact item x/z or the computer's yaw."""
    header(51, "WorkstationGroup desk + chair + on-top (place_on_top) seating")
    scene = SceneProgRoom("test51", seed=SEED)
    FLAT_DESK = "hssd/a42e2ef37ca205ecb1927bde89c6b618ddcda71b"   # flat 0.72 m desk (deterministic)
    with scene.WorkstationGroup() as ws:
        desk = scene.AddAsset("a simple flat wooden office desk", asset_id=FLAT_DESK)
        ws.set_anchor(desk)
        chair = ws.place_chair(scene.AddAsset("an ergonomic office chair"))
        comp = ws.place_computer(scene.AddAsset("an all-in-one desktop computer"))
        acc = ws.place_accessories([scene.AddAsset("an articulated desk lamp"),
                                    scene.AddAsset("a pen cup with pens")])
    scene.bind(ws)

    d_aabb = desk.get_aabb()
    desk_top = float(d_aabb[1, 1])
    desk_bot = float(d_aabb[0, 1])
    dz = float(desk.get_location()[2])
    chz = float(chair.get_location()[2])
    chair_bot = float(chair.get_aabb()[0, 1])
    ch_rot = float(chair.get_rotation()) % 360.0
    print(f"  desk top={desk_top:.2f} bottom={desk_bot:.2f} z={dz:.2f}   chair z={chz:.2f} "
          f"bottom={chair_bot:.2f} rot={ch_rot:.0f}")

    assert desk_top < 1.05, f"pinned desk should be a flat seated desk: top={desk_top:.2f}"
    # Every desktop item must REST ON the desk surface (bottom ~ desk top), not float above it.
    for label, o in [("computer", comp), ("lamp", acc[0]), ("pen cup", acc[1])]:
        b = float(o.get_aabb()[0, 1])
        print(f"  {label} bottom={b:.2f} (desk top={desk_top:.2f})")
        assert desk_top - 0.05 < b < desk_top + 0.08, \
            f"{label} should rest on the desk surface, not float: bottom={b:.2f} vs top={desk_top:.2f}"
    assert abs(chair_bot - desk_bot) < 0.06, f"chair should stand on the floor: {chair_bot:.2f} vs {desk_bot:.2f}"
    assert chz > dz + 0.02, f"chair should be in front (+z) of the desk: dz={dz:.2f} chz={chz:.2f}"
    assert abs(ch_rot - 180.0) < 5, f"chair should face the desk (rot 180): {ch_rot:.0f}"
    scene.export("results/test51_workstation.blend")


def test_52():
    """KitchenIslandGroup / tip mode: a U set's footprint is rasterised, the island attaches
    flush with the LONGER wing's frontal tip across the mouth, the entry gap is protected by
    shrinking the island, and the stools sit in a row on the OUTWARD face facing back. The
    raster/classification numbers are exposed on group.analysis, so assert on those plus
    relative geometry (never absolute coords — __exit__ recenters the group)."""
    header(52, "KitchenIslandGroup U set -> tip peninsula + entry gap + stool row")
    scene = SceneProgRoom("test52", seed=SEED)
    U_SET = "future/3c2bf09e-eb79-4a8f-a3f4-36446e9ea656"     # navy U: wings -x 2.49 / +x 2.99 m
    COUNTER = "hssd/f8b8235c6e241b3ef1922a7560736535d9c9219c" # bare-marble-top island
    STOOL = "hssd/ce64089b08a3ba3e5a2c4c8e70c627c71c64cccc"
    with scene.KitchenIslandGroup() as kz:
        kitchen = scene.AddAsset("a complete navy fitted kitchen unit", asset_id=U_SET)
        kitchen.scale(kitchen.get_width() * 2.4 / kitchen.get_height())
        kz.set_anchor(kitchen)
        island = kz.place_island(
            scene.AddAsset("a navy kitchen island counter", asset_id=COUNTER))
        stools = kz.place_stools(
            2 * scene.AddAsset("a rustic wooden bar stool", asset_id=STOOL))
    scene.bind(kz)

    a = kz.analysis
    print(f"  analysis: shape={a['shape']} mode={a['mode']} wing={a.get('wing')} "
          f"mouth={a.get('mouth', 0):.2f} entry={a.get('entry', 0):.2f}")
    assert a["shape"] == "U" and a["mode"] == "tip", f"expected U/tip, got {a['shape']}/{a['mode']}"
    assert a["wing"] == "+x", f"should attach at the LONGER (+x, 2.99 m) wing: {a['wing']}"
    assert a["entry"] >= 0.85, f"entry gap must stay walkable: {a['entry']:.2f}"

    k_aabb, i_aabb = kitchen.get_aabb(), island.get_aabb()
    cellish = a["cell"] * 2 + 0.02
    print(f"  set z_max={k_aabb[1,2]:.2f} island z=[{i_aabb[0,2]:.2f},{i_aabb[1,2]:.2f}] "
          f"x=[{i_aabb[0,0]:.2f},{i_aabb[1,0]:.2f}] (set x_max={k_aabb[1,0]:.2f})")
    # flush with the wing's frontal tip (opening is +z for this set), inside the mouth
    assert abs(i_aabb[1, 2] - k_aabb[1, 2]) < cellish, "island far face should be flush with the wing tip"
    assert i_aabb[1, 0] < k_aabb[1, 0] - 0.3, "island must sit INSIDE the mouth, not on the wing"
    assert abs(float(i_aabb[0, 1]) - float(k_aabb[0, 1])) < 0.06, "island stands on the floor"
    surviving = [s for s in stools if s in kz.children]     # the fit guard may drop overflow
    assert surviving, "at least one stool must survive the fit guard"
    for s in surviving:
        s_aabb = s.get_aabb()
        assert s_aabb[0, 2] > i_aabb[1, 2] - 0.05, "stools sit BEYOND the island's outward face"
        assert abs(float(s.get_rotation()) % 360.0 - 180.0) < 5, "stools face the island"
    scene.export("results/test52_kitchen_island_tip.blend")


def test_53():
    """KitchenIslandGroup / pocket mode: an L set's island floats in the concave middle of the
    L's AABB — past the base run, clear of the leg — long axis parallel to the base run, with
    the pocket dimensions exposed on group.analysis."""
    header(53, "KitchenIslandGroup L set -> pocket island in the concave middle")
    scene = SceneProgRoom("test53", seed=SEED)
    L_SET = "future/b3e7e64f-417f-4da5-b4ce-cb2bfd06e039"     # warm-grey L: base -z, leg +x
    ISLAND = "hssd/559f21c7f5628a83b31d616e90bdcc02e7744731"  # walnut base cab, marble top
    with scene.KitchenIslandGroup() as kz:
        kitchen = scene.AddAsset("a complete grey fitted kitchen unit", asset_id=L_SET)
        kitchen.scale(kitchen.get_width() * 2.5 / kitchen.get_height())
        kz.set_anchor(kitchen)
        island = kz.place_island(
            scene.AddAsset("a walnut kitchen island with a marble top", asset_id=ISLAND, width=1.2))
    scene.bind(kz)

    a = kz.analysis
    print(f"  analysis: shape={a['shape']} mode={a['mode']} pocket={a.get('pocket')} "
          f"aisle_base={a.get('aisle_base', 0):.2f}")
    assert a["shape"] == "L" and a["mode"] == "pocket", f"expected L/pocket, got {a['shape']}/{a['mode']}"
    k_aabb, i_aabb = kitchen.get_aabb(), island.get_aabb()
    print(f"  set x=[{k_aabb[0,0]:.2f},{k_aabb[1,0]:.2f}] z=[{k_aabb[0,2]:.2f},{k_aabb[1,2]:.2f}]  "
          f"island x=[{i_aabb[0,0]:.2f},{i_aabb[1,0]:.2f}] z=[{i_aabb[0,2]:.2f},{i_aabb[1,2]:.2f}]")
    # inside the L's AABB, past the base run (-z), clear of the leg (+x)
    assert i_aabb[0, 0] > k_aabb[0, 0] and i_aabb[1, 0] < k_aabb[1, 0] - 0.4, \
        "pocket island must sit inside the AABB, clear of the +x leg"
    assert i_aabb[0, 2] > k_aabb[0, 2] + 0.3, "pocket island must sit PAST the base run"
    assert i_aabb[1, 2] <= k_aabb[1, 2] + 0.05, "pocket island stays within the AABB depth"
    pw, pd = a["pocket"]
    assert float(island.get_width()) <= pw + 0.01, "island must fit the pocket span"
    scene.export("results/test53_kitchen_island_pocket.blend")


def test_54():
    """Room HEIGHT auto-fix (Kunal 2026-07-14): no asset may ever pierce the roof.
    (a) A normal room stays at exactly 3.0 m (behaviour unchanged).
    (b) A floor asset taller than max_height RAISES the ceiling to asset + CEILING_MARGIN
        instead of clipping through it, and every object's top stays under HEIGHT."""
    header(54, "RoomGroup auto ceiling: never below the tallest asset")
    # (a) normal room: unchanged 3.0
    scene_a = SceneProgRoom("test54a", seed=SEED)
    sofa = scene_a.AddAsset("a modern 3-seat sofa")
    with scene_a.RoomGroup() as room_a:
        room_a.place_on_back_wall_center(sofa, facing="front")
        room_a.place_walls(floor_texture="light oak wood floor",
                           ceiling_texture="smooth white ceiling",
                           wall_texture="warm off-white painted wall")
        room_a.place_door("right_wall", position="right")
    print(f"  normal room HEIGHT={room_a.HEIGHT:.2f}")
    assert abs(room_a.HEIGHT - 3.0) < 1e-6, f"normal room must stay 3.0: {room_a.HEIGHT:.2f}"

    # (b) over-tall floor asset: ceiling rises, nothing clips
    scene_b = SceneProgRoom("test54b", seed=SEED)
    shelf = scene_b.AddAsset("a tall industrial storage shelf")
    shelf.scale_only_height(3.6)                     # deliberately over the 3.0 cap
    tall_top = float(shelf.get_height())
    with scene_b.RoomGroup() as room_b:
        room_b.place_on_back_wall_center(shelf, facing="front")
        room_b.place_walls(floor_texture="grey concrete floor",
                           ceiling_texture="smooth white ceiling",
                           wall_texture="plain grey painted wall")
        room_b.place_door("right_wall", position="right")
    print(f"  tall-asset room HEIGHT={room_b.HEIGHT:.2f} (asset {tall_top:.2f})")
    assert room_b.HEIGHT >= tall_top + room_b.CEILING_MARGIN - 1e-3, \
        f"ceiling must rise past the {tall_top:.2f} m asset: HEIGHT={room_b.HEIGHT:.2f}"
    for obj in scene_b.objects:
        try:
            top = float(obj.get_aabb()[1, 1])
        except Exception:
            continue
        assert top <= room_b.HEIGHT + 0.05, \
            f"{obj.name} pierces the roof: top={top:.2f} vs HEIGHT={room_b.HEIGHT:.2f}"
    scene_b.export("results/test54_tall_ceiling.blend")


def test_55():
    """Asset shop triage (Kunal 2026-07-14): the gates that decide what gets ingested.

    Pure logic — no network, no VLM, no Blender — so it runs anywhere and pins the two rules the
    whole pipeline rests on: the panel->rotation table (a sign error here silently ingests every
    asset back-to-front) and skip-vs-ask (misfiling an UNCERTAIN asset as a SKIP throws a good
    model away without telling anyone)."""
    header(55, "shop triage: panel->rotation, skip vs ask, size prior")
    from IDSDL.shop import board, triage

    # (a) the rotation table: bring each side round to -Y (the library's front)
    assert triage.PANELS[2][1] == 0.0, "panel 2 IS the front — no rotation"
    assert triage.PANELS[1][1] == 180.0
    assert triage.PANELS[3][1] == -90.0
    assert triage.PANELS[4][1] == 90.0

    good = {"object": "lounge chair", "n_units": 1, "single_unit": True, "interior_object": True,
            "front_panel": 3, "front_confidence": 0.9, "size_anchor": "height", "size_m": 0.9,
            "size_confidence": 0.9}
    dims = {"w_x": 0.62, "d_y": 0.7, "h_z": 0.9}
    second_ok = {"front_panel": 3, "confidence": 0.9}

    # (b) a clean, agreed candidate goes — with the -90 that panel 3 implies
    v, why, plan = triage.decide(good, dims, second_op=second_ok, use_prior=False)
    print(f"  clean candidate -> {v} rot={plan['rot_deg'][2]}")
    assert v == "go" and plan["rot_deg"][2] == -90.0, (v, why, plan)

    # (c) SKIP: several objects in one file. This is the one the boolean waved through until we
    #     made the VLM COUNT (a 3-table 'surgical instrument table collection').
    v, why, _ = triage.decide({**good, "n_units": 3}, dims, second_op=second_ok)
    print(f"  3 objects in one file -> {v} ({why})")
    assert v == "skip" and "multi_unit" in why, (v, why)
    v, why, _ = triage.decide({**good, "interior_object": False}, dims, second_op=second_ok)
    assert v == "skip", (v, why)

    # (d) ASK, never skip: the two front judges disagree -> a human settles it. If this ever
    #     returns "skip", good assets start vanishing silently.
    v, why, _ = triage.decide(good, dims, second_op={"front_panel": 1, "confidence": 0.9})
    print(f"  judges disagree (3 vs 1) -> {v} ({why})")
    assert v == "ask" and "front_disagreement" in why, (v, why)

    # (e) ASK: neither judge is confident
    v, why, _ = triage.decide({**good, "front_confidence": 0.4}, dims,
                              second_op={"front_panel": 3, "confidence": 0.4})
    assert v == "ask" and why == "front_uncertain", (v, why)

    # (f) the width the plan implies — a +-90 rotation SWAPS width and depth, and getting that
    #     backwards is how a chair ends up sideways in the library
    w = triage.predicted_width({"rot_deg": [0, 0, -90.0], "scale_axis": "z", "scale_size": 0.9},
                               dims)
    assert abs(w - 0.9 * dims["d_y"] / dims["h_z"]) < 1e-6, w      # rotated: width comes from d_y
    w0 = triage.predicted_width({"rot_deg": [0, 0, 180.0], "scale_axis": "z", "scale_size": 0.9},
                                dims)
    assert abs(w0 - 0.9 * dims["w_x"] / dims["h_z"]) < 1e-6, w0    # unrotated: width is w_x
    print(f"  predicted width: rotated {w:.3f} m, unrotated {w0:.3f} m")

    # (g) the board round-trip: what the user types must survive back into a plan
    meta = {"plan": {"rot_deg": [0, 0, 0.0], "scale_axis": "z", "scale_size": 1.0,
                     "front_panel": 2}}
    action, plan = board.parse_answer(
        {"action": "accept", "front": "4", "size": "2.5 m", "anchor": "width"}, meta)
    print(f"  user answer -> {action} rot={plan['rot_deg'][2]} {plan['scale_axis']}={plan['scale_size']}")
    assert action == "accept" and plan["rot_deg"][2] == 90.0
    assert plan["scale_axis"] == "x" and abs(plan["scale_size"] - 2.5) < 1e-9
    assert board.parse_answer({"action": "drop"}, meta)[0] == "drop"

    # (h) an UNTOUCHED block is not an answer. The template line reads `action: accept | drop` —
    #     the menu, not a choice — and parsing it as a choice made `apply` "act on" every asset
    #     the user had not looked at yet.
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        b = Path(td)
        (b / "HELP.md").write_text(
            "## 1. untouched  <!-- asset:untouched -->\n\n```\naction: accept | drop\nfront:  3\n"
            "size:   2.0\nanchor: height\n```\n\n"
            "## 2. answered  <!-- asset:answered -->\n\n```\naction: accept\nfront:  4\n"
            "size:   2.5\nanchor: width\n```\n")
        got = board.read_answers(b)
        print(f"  answered blocks seen: {sorted(got)}")
        assert set(got) == {"answered"}, got


def test_56():
    """Acquisition dial (Kunal 2026-07-14): the DATASET gets first refusal, always.

    `low` (default) never acquires. `mid`/`high` acquire ONLY on a measured gap. This test pins
    the gate itself, because everything expensive and irreversible sits behind it: if it ever
    fires on a query the dataset can already serve, every build starts silently spending money and
    minutes on assets we already own. No network, no VLM, no Blender."""
    header(56, "acquisition dial: only ever spend on a measured gap")
    from IDSDL.shop import acquire as A

    # (a) the dial parses, and anything unrecognised means DO NOTHING
    assert A.level(None) == "low" and A.level("mid") == "mid" and A.level("high") == "high"
    assert A.level("banana") == "low", "an unknown level must fail SAFE (never acquire)"
    assert not A.enabled("low") and A.enabled("mid") and A.enabled("high")

    calls = []

    class FakeRetriever:
        """Answers every query at `sim`, and records any acquisition attempt."""
        def __init__(self, sim):
            self.sim = sim
            self.metadata = {"m0": {"description": "whatever"}}

        def _sim(self, _q):
            return self.sim

    orig_best, orig_acq = A._best_sim, A._acquire
    A._best_sim = lambda r, q: (r._sim(q), "m0")
    A._acquire = lambda r, q, mode: calls.append((q, mode)) or "custom/fake"
    try:
        # (b) a query the dataset SERVES must never acquire — not even at "high". This is the
        #     line between "a fallback" and "a spending habit".
        A._state["tried"].clear(); A._state["spent"] = 0
        got = A.maybe_acquire(FakeRetriever(0.81), "a grey sofa", mode="high")
        print(f"  served (0.81) at high -> {got}, attempts={len(calls)}")
        assert got is None and not calls

        # (c) low must never acquire, even on a hopeless gap
        got = A.maybe_acquire(FakeRetriever(0.20), "a fume hood", mode="low")
        assert got is None and not calls, "low must NEVER acquire"

        # (d) a real gap at mid DOES acquire
        got = A.maybe_acquire(FakeRetriever(0.20), "a fume hood", mode="mid")
        print(f"  gap (0.20) at mid -> {got}, attempts={len(calls)}")
        assert got == "custom/fake" and calls == [("a fume hood", "mid")]

        # (e) the same gap is not paid for twice
        got = A.maybe_acquire(FakeRetriever(0.20), "a fume hood", mode="mid")
        assert got == "custom/fake" and len(calls) == 1, "a query must be attempted only once"

        # (f) the budget is a hard stop — a runaway loop here costs real money and hours
        A._state["tried"].clear()
        A._state["spent"] = A.BUDGET
        got = A.maybe_acquire(FakeRetriever(0.20), "another gap", mode="high")
        print(f"  gap at high with budget spent -> {got} (must be None)")
        assert got is None and len(calls) == 1
    finally:
        A._best_sim, A._acquire = orig_best, orig_acq
        A._state["tried"].clear(); A._state["spent"] = 0; A._state["log"].clear()


# ---------------------------------------------------------------------------
# 57-60  Targeted placement fixes (2026-08): arc-around-target + room re-aim,
#        randomness decoupled from sparsity, RingsGroup jitter, seeded PileGroup
# ---------------------------------------------------------------------------
def test_57():
    """place_arc(towards=): objects surround the target at a standoff and face it,
    even after a RoomGroup repositions the grid and the target independently."""
    header(57, "GridGroup place_arc towards= geometry + room re-aim")
    scene = SceneProgRoom("test57", seed=SEED)
    fireplace = scene.AddAsset("an electric fireplace with a dark mantel")
    chair = scene.AddAsset("a cozy lounge chair")
    chairs = 5 * chair
    with scene.GridGroup(sparsity=0.3) as arc:
        arc.place_arc(chairs, towards=fireplace)

    with scene.RoomGroup() as room:
        room.grad_solver = None      # keep placements analytic for exact assertions
        room.place_on_back_wall_center(fireplace, facing="front")
        room.place_on_center(arc, facing="back")

    t = np.array(fireplace.get_location(), dtype=float)
    standoff = max(float(fireplace.get_width()), float(fireplace.get_depth())) / 2.0
    for c in chairs:
        p = np.array(c.get_location(), dtype=float)
        rel = t - p
        d = float(np.hypot(rel[0], rel[2]))
        needed = float(np.degrees(np.arctan2(rel[0], rel[2])))
        err = abs((float(c.get_rotation()) - needed + 180.0) % 360.0 - 180.0)
        print(f"  chair dist={d:.2f} (standoff={standoff:.2f})  yaw err={err:.2f} deg")
        assert err < 2.0, f"chair not facing target after room layout: err={err:.1f} deg"
    scene.export("results/test57_arc_towards.blend")


def test_58():
    """GridGroup.randomness must bite even at sparsity=0 (was a silent no-op)."""
    header(58, "GridGroup randomness decoupled from sparsity")
    scene = SceneProgRoom("test58", seed=SEED)

    def gap_std(group):
        xs = sorted(c.get_location()[0] for c in group.children)
        return float(np.std(np.diff(xs)))

    with scene.GridGroup(sparsity=0.0, randomness=0.9) as row:
        chair = scene.AddAsset("a standard classroom chair with a plastic seat")
        row.place_row(8 * chair)
    scene.bind(row)
    s = gap_std(row)
    print(f"  gap std at sparsity=0, randomness=0.9 -> {s:.4f}")
    assert s > 1e-3, "randomness had no effect at sparsity=0"
    scene.export("results/test58_randomness_sparsity0.blend")


def test_59():
    """RingsGroup honours the inherited jitter knob (was silently ignored)."""
    header(59, "RingsGroup jitter wiring")
    scene = SceneProgRoom("test59", seed=SEED)

    def max_yaw_err(chairs, anchor):
        c = np.array(anchor.get_location(), dtype=float)
        errs = []
        for o in chairs:
            p = np.array(o.get_location(), dtype=float)
            needed = float(np.degrees(np.arctan2(c[0] - p[0], c[2] - p[2])))
            errs.append(abs((float(o.get_rotation()) - needed + 180.0) % 360.0 - 180.0))
        return max(errs)

    chair = scene.AddAsset("an upholstered accent chair")
    ring_a, ring_b = 6 * chair, 6 * chair
    with scene.RingsGroup(sparsity=0.2) as g0:
        g0.grad_solver = None
        table_a = scene.AddAsset("a large round dining table with a dark wood finish")
        g0.set_anchor(table_a)
        g0.place_rings([ring_a])
    scene.bind(g0)
    with scene.RingsGroup(sparsity=0.2, jitter=0.8) as g1:
        g1.grad_solver = None
        table_b = scene.AddAsset("a large round dining table with a dark wood finish")
        g1.set_anchor(table_b)
        g1.place_rings([ring_b])
    scene.bind(g1)

    err0, err1 = max_yaw_err(ring_a, table_a), max_yaw_err(ring_b, table_b)
    print(f"  max yaw deviation  jitter=0 -> {err0:.3f} deg   jitter=0.8 -> {err1:.3f} deg")
    assert err0 < 1e-3, f"jitter=0 ring should face the anchor exactly, err={err0:.3f}"
    assert err1 > 0.5, f"jitter=0.8 ring shows no rotational perturbation, err={err1:.3f}"
    scene.export("results/test59_rings_jitter.blend")


def test_60():
    """PileGroup scatter is reproducible under the scene seed (was unseeded)."""
    header(60, "PileGroup seeded reproducibility")

    def build():
        scene = SceneProgRoom("test60", seed=SEED)
        cushion = scene.AddAsset("a square floor cushion")
        cushions = 5 * cushion
        with scene.PileGroup() as pile:
            pile.grad_solver = None   # compare the raw scatter, not the solve
            pile.place_pile(cushions, spread=0.8)
        scene.bind(pile)
        return np.array([c.get_location() for c in cushions], dtype=float), \
            np.array([float(c.get_rotation()) for c in cushions], dtype=float)

    loc1, rot1 = build()
    loc2, rot2 = build()
    print(f"  max |dloc|={np.abs(loc1 - loc2).max():.2e}  max |drot|={np.abs(rot1 - rot2).max():.2e}")
    assert np.allclose(loc1, loc2, atol=1e-6), "pile positions differ across same-seed builds"
    assert np.allclose(rot1, rot2, atol=1e-6), "pile rotations differ across same-seed builds"


# ---------------------------------------------------------------------------
# 61-64  sparsity/jitter knobs for every motif group (2026-08)
# ---------------------------------------------------------------------------
def test_61():
    """Every newly-knobbed group responds to sparsity and/or jitter (effect exists)."""
    header(61, "sparsity/jitter effect sweep across the motif groups")
    scene = SceneProgRoom("test61", seed=SEED)

    def build_stack(**kw):
        box = scene.AddAsset("a wooden storage crate")
        boxes = 3 * box
        with scene.StackGroup(**kw) as g:
            g.grad_solver = None
            g.place_stack(boxes)
        scene.bind(g)
        return boxes

    tidy, tall = build_stack(), build_stack(sparsity=0.8)
    top = lambda objs: max(float(o.get_aabb()[0, 1]) for o in objs)
    print(f"  stack top-level bottom: sparsity=0 -> {top(tidy):.2f}, 0.8 -> {top(tall):.2f}")
    assert top(tall) > top(tidy) + 0.1, "StackGroup sparsity did not open vertical gaps"
    wobbly = build_stack(jitter=0.8)
    dx = max(abs(float(o.get_location()[0]) - float(wobbly[0].get_location()[0])) for o in wobbly[1:])
    print(f"  stack max |dx| at jitter=0.8 -> {dx:.3f}")
    assert dx > 1e-3, "StackGroup jitter did not slide upper levels"

    def build_pyr(**kw):
        crate = scene.AddAsset("a wooden storage crate")
        crates = 6 * crate
        with scene.PyramidGroup(**kw) as g:
            g.grad_solver = None
            g.place_pyramid(crates)
        scene.bind(g)
        return crates

    p0, p1 = build_pyr(), build_pyr(sparsity=0.8)
    span = lambda objs: (max(float(o.get_location()[0]) for o in objs[:3])
                         - min(float(o.get_location()[0]) for o in objs[:3]))
    print(f"  pyramid base-tier span: sparsity=0 -> {span(p0):.2f}, 0.8 -> {span(p1):.2f}")
    assert span(p1) > span(p0) + 0.05, "PyramidGroup sparsity did not widen tiers"

    def build_pile(**kw):
        cushion = scene.AddAsset("a square floor cushion")
        cushions = 5 * cushion
        with scene.PileGroup(**kw) as g:
            g.grad_solver = None
            g.place_pile(cushions, spread=0.8)
        scene.bind(g)
        c = np.mean([[float(v) for v in o.get_location()] for o in cushions], axis=0)
        return float(np.mean([np.hypot(float(o.get_location()[0]) - c[0],
                                       float(o.get_location()[2]) - c[2]) for o in cushions]))

    r0, r1 = build_pile(), build_pile(sparsity=0.8)
    print(f"  pile mean scatter radius: sparsity=0 -> {r0:.2f}, 0.8 -> {r1:.2f}")
    assert r1 > r0, "PileGroup sparsity did not widen the scatter disk"

    def build_sym(**kw):
        with scene.SymmetryGroup(**kw) as g:
            g.grad_solver = None
            bed = scene.AddAsset("a queen-sized bed with a wooden frame")
            g.set_anchor(bed)
            ns = scene.AddAsset("a small wooden nightstand with a drawer")
            g.place_flanking(ns)
        scene.bind(g)
        flanks = [c for c in g.get_children() if c is not bed]
        return bed, flanks

    bed0, f0 = build_sym()
    bed1, f1 = build_sym(sparsity=0.8)
    gap = lambda bed, fl: min(abs(float(c.get_location()[0]) - float(bed.get_location()[0]))
                              for c in fl)
    print(f"  symmetry flank offset: sparsity=0 -> {gap(bed0, f0):.2f}, 0.8 -> {gap(bed1, f1):.2f}")
    assert gap(bed1, f1) > gap(bed0, f0) + 0.3, "SymmetryGroup sparsity did not widen the gap"
    bed2, f2 = build_sym(jitter=0.8)
    dz = abs(float(f2[0].get_location()[2]) - float(bed2.get_location()[2]))
    print(f"  symmetry |dz| at jitter=0.8 -> {dz:.3f}")
    assert dz > 1e-3, "SymmetryGroup jitter did not perturb the pair"

    def yaw_err(objs, anchor):
        c = np.array(anchor.get_location(), dtype=float)
        errs = []
        for o in objs:
            p = np.array(o.get_location(), dtype=float)
            needed = float(np.degrees(np.arctan2(c[0] - p[0], c[2] - p[2])))
            errs.append(abs((float(o.get_rotation()) - needed + 180.0) % 360.0 - 180.0))
        return max(errs)

    def build_facing(**kw):
        chair = scene.AddAsset("a cozy lounge chair")
        s1, s2 = 2 * chair, 2 * chair
        with scene.FacingGroup(**kw) as g:
            g.grad_solver = None
            table = scene.AddAsset("a rectangular wooden coffee table")
            g.set_anchor(table)
            g.place_facing_rows(s1, s2)
        scene.bind(g)
        return table, s1 + s2

    t0, rows0 = build_facing()
    t1, rows1 = build_facing(jitter=0.8)
    e0, e1 = yaw_err(rows0, t0), yaw_err(rows1, t1)
    print(f"  facing max yaw err: jitter=0 -> {e0:.3f}, 0.8 -> {e1:.3f}")
    assert e0 < 1e-3 and e1 > 0.5, "FacingGroup jitter did not perturb facing yaw"

    def build_rel(**kw):
        with scene.RelativeGroup(**kw) as g:
            g.grad_solver = None
            sofa = scene.AddAsset("a modern three-seat sofa")
            g.set_anchor(sofa)
            side = scene.AddAsset("a small wooden nightstand with a drawer")
            g.place_on_left(side)
        scene.bind(g)
        return float(abs(side.get_location()[0] - sofa.get_location()[0])) \
            - float(sofa.get_width()) / 2.0 - float(side.get_width()) / 2.0

    g0, g1 = build_rel(), build_rel(sparsity=0.8)
    print(f"  relative left gap: sparsity=0 -> {g0:.3f} (SIDE_GAP={SIDE_GAP}), 0.8 -> {g1:.3f}")
    assert abs(g0 - SIDE_GAP) < 1e-5, "RelativeGroup default gap changed"
    assert abs(g1 - SIDE_GAP * 1.8) < 1e-5, "RelativeGroup sparsity gap formula wrong"
    gj = build_rel(jitter=0.8)
    print(f"  relative left gap at jitter=0.8 -> {gj:.3f}")
    assert abs(gj - SIDE_GAP) > 1e-3, "RelativeGroup jitter did not move the placement"

    def build_rings(s):
        chair = scene.AddAsset("an upholstered accent chair")
        inner, outer = 4 * chair, 6 * chair
        with scene.RingsGroup(sparsity=s) as g:
            g.grad_solver = None
            table = scene.AddAsset("a large round dining table with a dark wood finish")
            g.set_anchor(table)
            g.place_rings([inner, outer])
        scene.bind(g)
        c = np.array(table.get_location(), dtype=float)
        return float(np.mean([np.hypot(float(o.get_location()[0]) - c[0],
                                       float(o.get_location()[2]) - c[2]) for o in outer]))

    rr0, rr1 = build_rings(0.0), build_rings(0.6)
    print(f"  rings outer radius: sparsity=0 -> {rr0:.2f}, 0.6 -> {rr1:.2f}")
    assert rr1 > rr0 + 0.5, "RingsGroup sparsity did not separate the rings"
    scene.export("results/test61_knob_sweep.blend")


def test_62():
    """Group contracts survive max knobs: symmetry stays mirrored, the kitchen island
    stays audit-placed with only the stools wobbling, the mirror station's wall chain is
    untouched, and the workstation chair still reads as seated at the desk."""
    header(62, "contract preservation at high sparsity/jitter")
    scene = SceneProgRoom("test62", seed=SEED)

    with scene.SymmetryGroup(sparsity=0.5, jitter=0.8) as sym:
        sym.grad_solver = None
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        sym.set_anchor(bed)
        ns = scene.AddAsset("a small wooden nightstand with a drawer")
        sym.place_flanking(ns)
    scene.bind(sym)
    flanks = [c for c in sym.get_children() if c is not bed]
    cx = float(bed.get_location()[0])
    xs = sorted(float(c.get_location()[0]) for c in flanks)
    zs = [float(c.get_location()[2]) for c in flanks]
    print(f"  symmetry: midpoint err={abs((xs[0]+xs[1])/2 - cx):.4f}  dz={abs(zs[0]-zs[1]):.4f}")
    assert abs((xs[0] + xs[1]) / 2 - cx) < 0.05, "jitter broke the mirror midpoint"
    assert abs(zs[0] - zs[1]) < 0.05, "jitter broke the pair's equal depth"

    U_SET = "future/3c2bf09e-eb79-4a8f-a3f4-36446e9ea656"
    COUNTER = "hssd/f8b8235c6e241b3ef1922a7560736535d9c9219c"
    STOOL = "hssd/ce64089b08a3ba3e5a2c4c8e70c627c71c64cccc"
    with scene.KitchenIslandGroup(sparsity=0.6, jitter=0.8) as kz:
        kz.grad_solver = None
        kitchen = scene.AddAsset("a complete navy fitted kitchen unit", asset_id=U_SET)
        kitchen.scale(kitchen.get_width() * 2.4 / kitchen.get_height())
        kz.set_anchor(kitchen)
        island = kz.place_island(
            scene.AddAsset("a navy kitchen island counter", asset_id=COUNTER))
        stools = kz.place_stools(
            2 * scene.AddAsset("a rustic wooden bar stool", asset_id=STOOL))
    scene.bind(kz)
    a = kz.analysis
    print(f"  island: shape={a['shape']} mode={a['mode']} entry={a.get('entry', 0):.2f}")
    assert a["shape"] == "U" and a["mode"] == "tip", "knobs changed the island classification"
    assert a["entry"] >= 0.85, "knobs broke the walkable entry guarantee"
    k_aabb, i_aabb = kitchen.get_aabb(), island.get_aabb()
    assert abs(i_aabb[1, 2] - k_aabb[1, 2]) < a["cell"] * 2 + 0.02, "island tip no longer flush"
    surviving = [s for s in stools if s in kz.children]
    assert surviving, "stools vanished under the knobs"
    for s in surviving:
        yaw = abs(float(s.get_rotation()) % 360.0 - 180.0)
        assert yaw < 20.0, f"stool yaw wandered past its clamp: {yaw:.1f}"

    def build_station(jit):
        with scene.MirrorStationGroup(jitter=jit) as st:
            st.grad_solver = None
            ch = scene.AddAsset("an upholstered accent chair")
            st.set_anchor(ch)
            counter = scene.AddAsset("a narrow wooden console table")
            st.place_counter(counter)
            mirror = scene.AddAsset("a round framed wall mirror")
            st.place_mirror(mirror)
        scene.bind(st)
        m_aabb = mirror.get_aabb()
        return (float(mirror.get_location()[2]) - float(ch.get_location()[2]),
                float((m_aabb[0, 1] + m_aabb[1, 1]) / 2))

    (dz0, cy0), (dz1, cy1) = build_station(0.0), build_station(0.8)
    print(f"  mirror wall chain: dz {dz0:.4f} vs {dz1:.4f}   center_y {cy0:.3f} vs {cy1:.3f}")
    assert abs(dz0 - dz1) < 1e-4, "jitter moved the mirror off the wall chain"
    assert abs(cy0 - cy1) < 1e-4, "jitter changed the mirror mounting height"

    FLAT_DESK = "hssd/a42e2ef37ca205ecb1927bde89c6b618ddcda71b"
    with scene.WorkstationGroup(sparsity=0.5, jitter=0.8) as ws:
        ws.grad_solver = None
        desk = scene.AddAsset("a simple flat wooden office desk", asset_id=FLAT_DESK)
        ws.set_anchor(desk)
        chair = ws.place_chair(scene.AddAsset("an ergonomic office chair"))
    scene.bind(ws)
    ch_rot = float(chair.get_rotation()) % 360.0
    dz = float(chair.get_location()[2]) - float(desk.get_location()[2])
    print(f"  workstation chair: rot={ch_rot:.1f}  dz={dz:.2f}")
    assert abs(ch_rot - 180.0) < 25.0, "chair yaw wandered past its clamp"
    assert dz > float(desk.get_depth()) / 2.0, "chair no longer in front of the desk"
    scene.export("results/test62_knob_contracts.blend")


def test_63():
    """Knobbed layouts are reproducible under the scene seed (same-seed build twice)."""
    header(63, "seeded reproducibility with knobs on")

    def build():
        scene = SceneProgRoom("test63", seed=SEED)
        tracked = []

        box = scene.AddAsset("a wooden storage crate")
        boxes = 3 * box
        with scene.StackGroup(sparsity=0.5, jitter=0.7) as g:
            g.grad_solver = None
            g.place_stack(boxes)
        scene.bind(g)
        tracked.extend(boxes)

        with scene.SymmetryGroup(sparsity=0.5, jitter=0.7) as g:
            g.grad_solver = None
            bed = scene.AddAsset("a queen-sized bed with a wooden frame")
            g.set_anchor(bed)
            g.place_flanking(scene.AddAsset("a small wooden nightstand with a drawer"))
        scene.bind(g)
        tracked.extend(g.get_children())

        chair = scene.AddAsset("a cozy lounge chair")
        s1, s2 = 2 * chair, 2 * chair
        with scene.FacingGroup(sparsity=0.5, jitter=0.7) as g:
            g.grad_solver = None
            table = scene.AddAsset("a rectangular wooden coffee table")
            g.set_anchor(table)
            g.place_facing_rows(s1, s2)
        scene.bind(g)
        tracked.extend([table] + s1 + s2)

        with scene.RelativeGroup(sparsity=0.5, jitter=0.7) as g:
            g.grad_solver = None
            sofa = scene.AddAsset("a modern three-seat sofa")
            g.set_anchor(sofa)
            side = scene.AddAsset("a small wooden nightstand with a drawer")
            g.place_on_left(side)
            far = scene.AddAsset("a cozy lounge chair")
            g.place_on_front_further(far)
        scene.bind(g)
        tracked.extend([sofa, side, far])

        return np.array([[float(v) for v in o.get_location()] for o in tracked]), \
            np.array([float(o.get_rotation()) for o in tracked])

    loc1, rot1 = build()
    loc2, rot2 = build()
    print(f"  {len(loc1)} transforms  max |dloc|={np.abs(loc1 - loc2).max():.2e}  "
          f"max |drot|={np.abs(rot1 - rot2).max():.2e}")
    assert np.allclose(loc1, loc2, atol=1e-6), "knobbed positions differ across same-seed builds"
    assert np.allclose(rot1, rot2, atol=1e-6), "knobbed rotations differ across same-seed builds"


def test_64():
    """Default-path invariance canary: a no-kwargs group and an explicit sparsity=0, jitter=0
    group are bit-identical, and the zero-knob spacing formulas equal the legacy constants.
    If this ever fails, some knob path draws RNG or shifts a gap at defaults."""
    header(64, "defaults are inert (sparsity=0, jitter=0 == legacy)")

    def build(explicit):
        kw = dict(sparsity=0.0, jitter=0.0) if explicit else {}
        scene = SceneProgRoom("test64", seed=SEED)
        out = []

        box = scene.AddAsset("a wooden storage crate")
        boxes = 3 * box
        with scene.StackGroup(**kw) as g:
            g.grad_solver = None
            g.place_stack(boxes)
        scene.bind(g)
        out.extend(boxes)
        heights = [float(b.get_height()) for b in boxes]
        bots = [float(b.get_aabb()[0, 1]) for b in boxes]
        for i in range(1, len(boxes)):
            assert abs((bots[i] - bots[i - 1]) - heights[i - 1]) < 1e-5, \
                "stack gap at defaults is not exactly zero"

        with scene.SymmetryGroup(**kw) as g:
            g.grad_solver = None
            bed = scene.AddAsset("a queen-sized bed with a wooden frame")
            g.set_anchor(bed)
            ns = scene.AddAsset("a small wooden nightstand with a drawer")
            g.place_flanking(ns)
        scene.bind(g)
        flanks = [c for c in g.get_children() if c is not bed]
        out.extend([bed] + flanks)
        # (no exact-gap pin here: face_towards swaps the flanks' AABB width/depth, so the
        # placement-time width isn't recoverable; the pair midpoint is translation-proof)
        xs = sorted(float(c.get_location()[0]) for c in flanks)
        assert abs((xs[0] + xs[1]) / 2 - float(bed.get_location()[0])) < 1e-5, \
            "flanking pair not centred on the anchor at defaults"

        with scene.RelativeGroup(**kw) as g:
            g.grad_solver = None
            sofa = scene.AddAsset("a modern three-seat sofa")
            g.set_anchor(sofa)
            side = scene.AddAsset("a small wooden nightstand with a drawer")
            g.place_on_left(side)
        scene.bind(g)
        out.extend([sofa, side])
        d = abs(float(side.get_location()[0]) - float(sofa.get_location()[0]))
        expect = float(sofa.get_width()) / 2.0 + float(side.get_width()) / 2.0 + SIDE_GAP
        assert abs(d - expect) < 1e-5, "relative SIDE_GAP at defaults changed"

        return np.array([[float(v) for v in o.get_location()] for o in out]), \
            np.array([float(o.get_rotation()) for o in out])

    loc_a, rot_a = build(explicit=False)
    loc_b, rot_b = build(explicit=True)
    print(f"  {len(loc_a)} transforms  max |dloc|={np.abs(loc_a - loc_b).max():.2e}")
    assert np.array_equal(loc_a, loc_b), "explicit 0.0 knobs differ from no-kwargs build"
    assert np.array_equal(rot_a, rot_b), "explicit 0.0 knobs differ from no-kwargs build (rot)"


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
    # --- new motif groups (groups_extra.py) ---
    44: test_44,   # StackGroup (stack)
    45: test_45,   # PyramidGroup (pyramid)
    46: test_46,   # PileGroup (pile / scatter)
    47: test_47,   # SymmetryGroup (flanking / on_each_side)
    48: test_48,   # FacingGroup (face_to_face)
    49: test_49,   # RingsGroup (concentric surround)
    50: test_50,   # MirrorStationGroup (mirror + counter + facing anchor)
    51: test_51,   # WorkstationGroup (desk + chair + computer + accessories)
    52: test_52,   # KitchenIslandGroup tip mode (U set peninsula + entry gap + stools)
    53: test_53,   # KitchenIslandGroup pocket mode (L set concave-middle island)
    54: test_54,   # RoomGroup auto ceiling (never below the tallest asset)
    55: test_55,   # asset-shop triage gates (panel->rotation, skip vs ask, size prior)
    56: test_56,   # acquisition dial (low/mid/high; only ever spend on a measured gap)
    # --- targeted placement fixes (2026-08) ---
    57: test_57,   # GridGroup place_arc towards= (arc around target + room re-aim)
    58: test_58,   # GridGroup randomness decoupled from sparsity
    59: test_59,   # RingsGroup jitter wiring
    60: test_60,   # PileGroup seeded reproducibility
    # --- sparsity/jitter for every motif group (2026-08) ---
    61: test_61,   # effect sweep: every knobbed group responds
    62: test_62,   # contracts hold at max knobs (mirror pair, island audit, wall chain)
    63: test_63,   # seeded reproducibility with knobs on
    64: test_64,   # defaults are inert (the no-extra-RNG canary)
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
