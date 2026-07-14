# Executive office — worked example (single room, "storage-backbone + work/lounge zones")

Status: **built as `scenes/executive_office.py`** (seed=42), planner-driven, iterated on VLM
feedback. [`executive_office_v1.py`](executive_office_v1.py) is that program **phase-gated**
(2026-07-13): a retrofit only — same layout, same pinned ids, same seed. It is **lint-clean**, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record).

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

## Program
[`executive_office_v1.py`](executive_office_v1.py) — phase 1 the floor anchors (the backbone
bookcase, the desk workstation with its executive chair, the lounge nook, the orange accent chair,
the walls and the door), phase 2 the surface dressing (the laptop, task lamp and succulent on the
desktop, plus the corner plant), phase 3 the wall art, the window and the ceiling lighting.

`workbench run skills/examples/executive_office_v1.py --phase 1` builds the layout alone in ~1–2 min.

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
