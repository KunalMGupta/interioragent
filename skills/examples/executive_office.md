# Executive office — worked example (single room, "storage-backbone + work/lounge zones")

A single private/executive office. Its defining moves: a **wide bookcase as the storage
backbone** on the back wall (the visual anchor), a **warm-wood desk WorkstationGroup** in
front of it with the executive facing the room, and a small **lounge nook** (2-seat sofa +
round table + orange accent chair) set apart yet visible. Distinct from `office.md`, which
is the **open-plan** workspace (a grid of desks); reach for this one for "a private office /
executive office / study / home office". Read alongside `../workflow/design_principles.md`.

## Prompt(s) this covers
- "a (private / executive) office", "a study", "a home office / den".

## Plan summary
Planner → **"Integrated Library-Backbone Executive Office"**: centre the room on a bookcase
wall (storage backbone + anchor), a daylight desk facing a window, an upholstered executive
chair, a **sculptural orange accent chair** for visitors, a lounge zone set apart, and
**layered light** (daylight + desk task lamp + a globe/sputnik chandelier focal point).
Materials: warm wood, leather/soft upholstery, brass, greenery.

The retrieved library skews **traditional/dark** (classic executive desks, wood bookcases)
rather than the collage's light Scandinavian oak. Rather than fight retrieval for light oak,
lean into a **warm traditional-modern** read (warm wood + light walls + grey upholstery +
the orange chair as the single accent) — it plays to the dataset's strengths. No ingest gap.

## Pinned assets (asset-first kickoff)
All rank-1..3 good; pinned for durability:
- **Desk** `hssd/6804953904df94d4abdb0776ad6d55c2a5b8aeaa` — warm-wood top + slim metal legs,
  FLAT (WorkstationGroup-safe; renders slightly two-tone white-top/wood-apron but reads modern).
- **Bookcase backbone** `future/f1f6fd18-6494-40d5-9fba-988c0734aaf3` — wide warm-wood grid
  shelving with a lower cabinet strip (the plan's "open shelves + lower cabinetry"). Goes on the
  back wall; a long unit like this **sets room proportions** (place it first).
- **Sofa** `hssd/7092826dbd4e79eb1468f5f1be75b558b87c2c82` (grey 2-seat), **side table**
  `hssd/d4bff7307857a9634e9785ce7febc342217cce7c` (round mid-century wood), **orange accent chair**
  `hssd/91999bead15b71802e7a306d174b69a924619756` (winged).

## Skeleton program
```python
DESK = "hssd/6804953904df94d4abdb0776ad6d55c2a5b8aeaa"
BOOKCASE = "future/f1f6fd18-6494-40d5-9fba-988c0734aaf3"
scene = SceneProgRoom("ExecutiveOffice", seed=42)

# desk workstation: warm-wood desk + leather exec chair + laptop + task lamp + succulent (<=3 on-top)
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a modern warm wood writing desk with slim metal legs", asset_id=DESK))
    station.place_chair(scene.AddAsset("a brown leather executive office chair"))
    station.place_computer(scene.AddAsset("an open laptop computer"))
    station.place_accessories([scene.AddAsset("an articulated black desk task lamp"),
                               scene.AddAsset("a small potted succulent for a desk")])

with scene.RelativeGroup() as lounge:            # seating always gets a table (design_principles)
    lounge.set_anchor(scene.AddAsset("a modern grey two-seat sofa", asset_id=SOFA))
    lounge.place_on_front_right(scene.AddAsset("a small round wooden side table", asset_id=SIDE_TABLE))

with scene.RoomGroup(modulate_scale=0.85, randomness=0.1) as room:   # 0.85 = acted-on rescale feedback
    room.place_walls(floor_texture="warm oak wood flooring", ceiling_texture="white", wall_texture="soft warm white")
    room.place_on_back_wall_center(scene.AddAsset("a wide modern wood open bookcase with a lower cabinet", asset_id=BOOKCASE))
    room.place_on_center(station, facing="back")            # facing="back" -> executive faces the ROOM/window
    room.place_on_left_wall_center(lounge, facing="right")
    room.place_on_front_left(scene.AddAsset("a sculptural orange winged accent lounge chair", asset_id=ACCENT_CHAIR), facing="back")
    room.place_on_back_right_corner(scene.AddAsset("a tall potted plant in a modern planter"))
    room.add_lighting("a flat round LED flush mount ceiling light", density=0.2)   # FLUSH fixture, NOT a chandelier
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract wall art print in warm tones"))
    room.place_window_standard("front_wall", position="center", curtain="sheer white curtains")
    room.place_door("right_wall", position="right")
scene.export("executive_office.blend")
```

## What worked / gotchas
- **The bookcase backbone is the anchor + the proportion-setter.** Place the long storage unit on
  the back wall first (like the salon's long strips) — it grounds the composition and fixes the room
  width before you fill in desk + lounge.
- **Executive facing (WorkstationGroup).** The operator side is the desk's local **+Z** and the chair
  faces the desk, so `place_on_center(station, facing="back")` seats the boss on the bookcase side
  facing the room/window — the classic power layout. (Same +Z-operator rule as the computer_room grid;
  confirm by eye, the `RotationConstraint` can't tell.)
- **LIGHTING — do NOT `add_lighting` a chandelier.** The plan wanted a "globe/sputnik chandelier focal
  point"; feeding that to `add_lighting` rendered **giant emissive globes at head height + a blown-out
  white room**. `add_lighting` caps fixture *height* at 1.5 m but hangs it from the ceiling, so a tall
  chandelier drops into the room, and its glowing globe meshes over-light the scene. → Use a **compact
  flat/flush fixture** (`"a flat round LED flush mount ceiling light"`, density ~0.2); let the **desk
  task lamp** be the warm/decorative light. Pick the ceiling fixture by geometry (short, small emissive
  area), not by catalog looks. `density` = fixture COUNT (fixed total watts), so keep it low. Full
  detail in `../workflow/vlm_feedback.md`.
- **Window = black void (renderer limit).** No exterior environment, so any opening is a black night
  pane and curtains render as parted drapes around it. Use `place_window_standard` (small pane, modest
  void), not the wide `place_window_picture`; and fix the room lighting first — the void only looks bad
  when the walls are blown white.
- **Warm-traditional beats fighting for light oak.** The dataset's executive desks / bookcases are
  warm-dark; embracing that (warm wood + grey + one orange accent) is more coherent than forcing the
  planner's Scandinavian palette through reluctant retrieval.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.8` (twice) → walked to `0.9` as I applied `modulate_scale` 1.0→0.9→0.85. A vote
  that **decays toward neutral as you act = converging**; stopped at 0.85 on a good render.
- `rotate sofa to face the round table` (repeated) → **declined** (noise): a wall-backed lounge sofa
  shouldn't pivot to face its own end table.
- `rescale side table by 0.8` (once, late) → left as-is; it reads as an appropriately sized coffee
  table by the sofa, and a single late minor-prop vote isn't worth another 3–8 min render.

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed for a single-room, three-zone layout.
