# Classroom — example

Status: **built & rotation-clean** ([classroom_v1.py](classroom_v1.py), seed=7). Bright daylit
classroom, built coarse-to-fine through the workbench. Final compile: rotation
clean at every level, no wall overlap, room proportions converged.

## Prompt this covers
- "a bright, friendly elementary school classroom with rows of student desks and
  chairs facing a teacher's desk and a large chalkboard on the front wall, tall
  windows with curtains, open storage shelves, a cozy reading nook, and warm
  ceiling lighting"

## Plan summary (from the planner)
"Chalkboard-Centered Daylit Classroom": light wood floors, warm-cream walls.
Wood-topped student desks + blue chairs in rows facing the front; wall chalkboard;
teacher's desk facing the students; tall windows + curtains; white open storage
with colorful bins; reading nook with a teal rug + bean-bag poufs. Warm ceiling
panels. Retrieved skills were all strong classroom/kindergarten matches (0.72–0.77).

## Working program (coarse-to-fine)

```python
from IDSDL.scene import SceneProgRoom
scene = SceneProgRoom("ClassroomV1", seed=7)

# desk unit = desk + chair on the BACK of the desk (seat-behind convention);
# gridded into rows WITH AISLES via sparsity
with scene.RelativeGroup() as desk_unit:
    desk = scene.AddAsset("a wooden student desk with metal frame")
    desk_unit.set_anchor(desk)
    desk_unit.place_on_back_adjacent(scene.AddAsset("a small blue plastic school chair"))

with scene.GridGroup(sparsity=0.5) as student_grid:     # 0 = merged benches; 0.5 = aisles
    student_grid.place_grid(6 * desk_unit, cols=3)

with scene.RelativeGroup() as teacher_area:
    teacher_desk = scene.AddAsset("a large teachers desk")
    teacher_area.set_anchor(teacher_desk)
    teacher_area.place_on_back_adjacent(scene.AddAsset("a grey office chair"))
    teacher_area.place_on_top(scene.AddAsset("a small desk task lamp"))
    teacher_area.add_lighting("a warm rectangular ceiling panel light", density=0)

with scene.RelativeGroup() as reading_nook:
    reading_nook.set_anchor(scene.AddAsset("a low kids bookshelf with picture books"))
    poufs = 2 * scene.AddAsset("a colorful round bean bag pouf")
    reading_nook.place_on_front_left(poufs[0]); reading_nook.place_on_front_right(poufs[1])
    reading_nook.place_rug("a teal patterned area rug", size=0.5)   # 0.85 was flagged too big
    reading_nook.add_lighting("a warm rectangular ceiling panel light", density=0)

with scene.RoomGroup() as room:
    room.place_walls(floor_texture="light wood planks", ceiling_texture="white", wall_texture="warm cream")
    room.place_on_front(teacher_area, facing="back")
    room.face(teacher_area, toward="back_wall")          # teacher faces students (90-snapped)
    room.place_on_center(student_grid, facing="front")
    room.face(student_grid, toward="front_wall")         # grid faces the teaching wall
    # teacher-desk asset is front-reversed → corrected once in the front cache
    # (IDSDL/datasets/front_offsets.json), not per scene.
    room.place_on_wall_front_center(scene.AddAsset("a large green chalkboard", width=2.5))  # width forces a board
    room.place_on_right_wall_center(scene.AddAsset("a white open storage shelf with colorful bins and books"))
    room.place_on_back_left_corner(reading_nook)
    room.place_window_floor_to_ceiling("left_wall", curtain="white classroom curtains")
    room.place_door("back_wall", position="right")

scene.export("classroom_v1.blend")
```

## What worked / gotchas
- **GridGroup `sparsity` is the desk-spacing knob.** Default 0 packs desks edge-to-edge
  into long benches; `sparsity=0.5` adds both column and row gaps → individual desks
  with aisles. (Sparsity applies to columns *and* rows.)
- **Asset retrieval can return an undersized item.** "a large green chalkboard" came
  back tabletop-sized; `AddAsset(..., width=2.5)` forces a wall-spanning board. Check
  big wall items in the render and pin `width`/`depth` when retrieval undershoots.
- **Lighting must hang off an AnchorGroup.** `add_lighting` is a Relative/Around method;
  `GridGroup` and `RoomGroup` don't have it. The student grid is a GridGroup, so light
  the room by calling `add_lighting` on the `teacher_area` and `reading_nook`
  RelativeGroups (front + back coverage) — plus the daylight window.
- **Wall-slot hygiene:** chalkboard front, storage right, window left, door back —
  one per wall, WallOverlap stayed clean.
- **Gotcha — reading nook got occluded** in the back-left corner behind the desk grid.
  A zone you want visible should go where the main cluster won't block it (or shrink the
  grid). Left as-is here; flag for v2.
- **Fixed a RoomGroup spacing bug here.** The student grid (`center`) nearly touched the
  teacher desk (`front`). Cause: floor placements used fixed depth fractions (`D/4,D/2,
  3D/4`) while `DEPTH` is the sum of independently-sized rows — a deep item bled into the
  neighbor slot. Now placements land at true cumulative **row/column centers**
  (`init_dims` builds `row_centers`/`col_centers`); adjacent slots can't overlap by
  construction. (The grid pulled back ~0.26 m, opening a real aisle to the teacher.)

## Orientation — the debugging story (the whole point of this scene)
This took three layers to get right; all three matter:
1. **Seat-behind-desk convention.** First pass used `place_on_front_adjacent` → students
   looked *away* from the teacher. Flipping the chair to the **back** of the desk
   (`place_on_back_adjacent`) made each unit's look-direction = chair→desk = correct.
2. **Wall-facing.** `room.face(student_grid, toward="front_wall")` and
   `room.face(teacher_area, toward="back_wall")` — face the *wall*, 90°-snapped, so rows
   stay orthogonal. (`facing=` alone happened to give the same angle here, but wall-facing
   is the deterministic, intent-revealing lever.)
3. **Front-correction cache (the systemic fix).** Even after 1+2 the **teacher desk** still
   rendered backwards — because asset meshes carry no canonical front (see
   ../workflow/constraints.md). It's a *different* asset from the student desks and is
   modeled reversed. Recorded once: `python -m IDSDL.front_cache set <id> 180`; now applied
   automatically on load, no per-scene `rotate()`.

**Trust your eye, not the VLM, for rotation.** The room-level `RotationConstraint` said
`no rotation` on the *mis-oriented* scene (false negative); the per-unit check correctly
flagged `rotate desk by 180` (true positive) but we initially dismissed it. Visual
inspection was the arbiter — it caught the reversed teacher desk both VLM levels disagreed on.

## Other VLM feedback
- **ObjectProportions:** reading-nook rug flagged too big → reduced `place_rug` 0.85 → 0.5;
  cleared. Ceiling panel light flagged slightly big — left (cosmetic).
- **RoomProportions:** hovered around 1.0 (1.1 → 0.99) — noise; held (no resize).

## Manual constraints used
- None. Candidates for v2: `AccessConstraint(desk, chair, dir="front")` to tuck chairs;
  `ClearanceConstraint` along the front for teacher circulation.
