# Living room — example

Status: **built & VLM-clean** (warm modern living room, `livingroom_v1.py`, seed=42).
Built coarse-to-fine through the workbench; final compile returns `no rescale` /
`no rescale` / `no wall overlap`. The older `test.py` seed remains a second
reference for nested-group patterns (see bottom).

## Prompt this covers
- "a warm, modern living room with a central sofa-and-armchairs seating area
  around a coffee table, a wool rug, a large window with sheer curtains, a
  bookshelf, indoor plants, and soft ambient lighting"

## Plan summary (from the planner)
"Warm Modern Living Oasis": light oak floors, warm-beige walls. Low-profile
cream sofa + two wood-framed leather accent chairs around a low coffee table on
a plush ivory wool rug. Tall wooden open bookshelf as the architectural anchor.
Large window with sheer curtains for daylight. Potted plants in corners. Layered
lighting (ring pendant + floor lamp). Retrieved skills were all 0.75–0.76
living-room/lounge matches — the library covers this type well.

## Working program (coarse-to-fine, VLM-clean)

```python
from IDSDL.scene import SceneProgRoom
scene = SceneProgRoom("LivingRoomV1", seed=42)

# Phase 1: U-style seating cluster (coffee table center, sofa back, chairs flanking)
with scene.RelativeGroup() as seating:
    coffee = scene.AddAsset("a low wooden coffee table")
    seating.set_anchor(coffee)
    sofa = scene.AddAsset("a cream low-profile 3-seat sofa")
    seating.place_on_back_further(sofa)
    chairs = 2 * scene.AddAsset("a wood-framed leather accent chair")
    seating.place_on_front_left_further(chairs[0])
    seating.place_on_front_right_further(chairs[1])
    seating.face(chairs[0], toward=coffee)   # turn chairs IN to face the table
    seating.face(chairs[1], toward=coffee)   # (placement bakes ±90° = sideways)

    # Phase 2: floor lamp beside sofa + coffee-table centerpiece
    seating.place_on_back_right_further(scene.AddAsset("a warm-toned arc floor lamp"))
    seating.place_on_top(scene.AddAsset("a decorative tray with stacked books and a small vase"))
    seating.place_rug("a plush ivory wool rug", size=0.9)

    # Phase 3: ring pendant over the cluster — ALSO the room's main light source
    seating.add_lighting("a circular ring pendant light", density=0)

# modulate_scale=0.9 = final-phase room rescale (see VLM section)
with scene.RoomGroup(modulate_scale=0.9) as room:
    room.place_walls(floor_texture="light oak planks", ceiling_texture="warm white", wall_texture="warm beige")
    room.place_on_center(seating, facing="front")
    room.place_on_back_wall_center(scene.AddAsset("a tall wooden open bookshelf with books and decor"))

    # Phase 2: corner greenery
    room.place_on_back_left_corner(scene.AddAsset("a large potted fiddle-leaf fig plant"))
    room.place_on_front_right_corner(scene.AddAsset("a medium potted plant"))

    # Phase 3: window + sheers, wall art, door
    room.place_window_floor_to_ceiling("left_wall", curtain="white sheer curtains")
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract art print"))
    room.place_door("front_wall", position="right")

scene.export("livingroom_v1.blend")
```

## What worked / gotchas
- **U-cluster via one RelativeGroup:** anchor = coffee table; sofa on
  `place_on_back_further`, chairs on `place_on_front_left/right_further`. Reads as
  a conversation U. `_further` (vs `_adjacent`) leaves walking gaps.
- **Orient the flanking chairs explicitly.** `place_on_front_left/right_further`
  bake a ±90° rotation, so the chairs face *sideways*, not the table. Add
  `seating.face(chair, toward=coffee)` per chair — applied after layout, it turns
  them in toward the cluster. `RotationConstraint` (VLM) confirms with `no rotation`.
- **Lighting is also illumination.** Until Phase 3 the scene had **0 lights** and
  every render was dim/flat. `seating.add_lighting(..., density=0)` adds the ring
  pendant *and* an area light over the cluster — that's what lit the room. Add
  lighting before judging final look; don't mistake "no lights yet" for a bad scene.
- **Wall-slot hygiene avoids overlap:** keep one element per wall — bookshelf back,
  window left, art right, door front. WallOverlap stayed clean throughout.
- `place_window_floor_to_ceiling` removes that wall (5 walls after) and adds the
  window+curtain as wall-objects; great for the daylight look.
- Distinguish `place_on_back_wall_center` (bookshelf *against* wall) from
  `place_on_wall_right_center` (art *hung on* wall) — different method families.
- `place_on_top` on the seating group puts the centerpiece on the anchor (coffee
  table); `place_on_top`/`place_rug`/`add_lighting` are deferred to end-of-compile.

## VLM feedback we hit and how we resolved it
- **Object proportions:** `no rescale` at every phase — asset scales were fine.
- **Wall overlap:** clean at every phase (one item per wall).
- **Room proportions (the interesting one):** suggestion drifted as occupancy
  rose — Phase 1 `1.2` (enlarge) → Phase 2 `0.92` → Phase 3 `0.9` (shrink). We
  **held the room size through phases 1–2** (render looked fine; occupancy still
  climbing) and only acted in the **final phase**: applied `0.9` via
  `RoomGroup(modulate_scale=0.9)`, after which RoomProportions returned
  `no rescale`. Rule lives in ../workflow/vlm_feedback.md ("render wins early
  phases; act on room size in the final phase").

## Manual constraints used
- None were needed here (overlap solver handled spacing). Natural future adds:
  `room.add_visibility(sofa, tv)` if a TV is introduced;
  `room.add_clearance(sofa, dir="front")` to guarantee legroom to the coffee table.

## Secondary reference — `test.py` (nested-group patterns)
Shows `AroundGroup.place_arc` for chairs around a table and a nested
(side table + lamp) RelativeGroup placed as a single unit on a couch — useful when
you need sub-assemblies.
