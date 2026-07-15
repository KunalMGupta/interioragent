---
id: example:children_room
kind: example
family: hero-anchor-room
category: "kids bedroom"
pattern: "Three small zones;"
---
> **Digest (from the pattern index):** Three small zones; `place_inside` tile-fit


# Children's room — worked example

Status: **built & VLM-clean** (`scenes/work/children_room.py`, seed=7). Final compile returns
`no rescale` / `no rotation` / `no wall overlap`; RoomProportions converged to ~0.9. Planner-driven,
built coarse-to-fine through the workbench. Built as `scenes/work/children_room.py`;
[`children_room_v1.py`](children_room_v1.py) is that program phase-gated (2026-07-13),
`lint_program`-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record).

## Prompt / plan
"A bright, playful children's bedroom for a young kid: single bed with colorful bedding, a soft play
rug, open toy storage + cubby shelves, a small study desk + chair, a low bookshelf with picture books,
wall art, a window with bright curtains, warm friendly lighting."

Planner ("Playful Single-Bed Kids Room") = **zone into SLEEP / STUDY / PLAY**: single bed on a main
wall, a low desk + child chair study nook, open cubbies + a picture-book shelf, a soft play rug, art
at kid height, layered warm light (flush ceiling + bedside + desk). Palette: gentle blues, pinks,
neutrals, light wood. Retrieved skills were Nursery/Children-Room at ~0.75 — the library covers kids
rooms well.

## The layout idea: three zones, one per side
- **Back wall** — the hero **bed group** (bed + a nightstand-with-lamp at the head, a grounding play
  rug, and the room's ceiling light via `add_lighting`).
- **Right wall** — the **storage/reading run**: a cubby unit + a low bookshelf (a long run on a long
  wall), with a bean-bag reading seat out in front (`place_on_right`).
- **Left wall** — the **study nook**: `place_desk_chair(desk, chair)` + a task lamp on the desk.
- **Front wall** — window (bright curtains) + door.

Each functional cluster is its own `RelativeGroup`, placed as a unit so it travels/rotates together.

## Program
[`children_room_v1.py`](children_room_v1.py) — phase 1 the floor anchors (bed hero + bedside unit,
the cubby/bookshelf run, the desk+chair study nook, the walls and the door); phase 2 the surface and
floor dressing (baskets inside the cubbies, toys and lamps on top, the play rug, the bean bag);
phase 3 the kid-height wall art, the curtained window and the lighting.
`workbench run skills/examples/children_room_v1.py --phase 1` builds the layout alone in ~1–2 min.

## What worked / gotchas (kids-room specific)
- **Beds are "set assets" AND the shortlist skews to BUNK beds.** For a *single*-bed brief, pin a
  clean single (here `future/f65434b4…`); the mesh is pre-dressed, so don't add separate bedding.
- **"Small desk/bedside lamp" retrieval is unreliable** — the generic desk-lamp query returned an
  oversized designer lamp that dwarfed the desk, and "mushroom night light" returned a metal lantern.
  Pin small, obviously-a-lamp meshes (a retro pink desk lamp; a white mushroom lamp).
- **A retrieved asset can carry BAD real-world scale metadata.** The yellow bean bag loaded at 0.15 m
  (native mesh 0.92 m — the retriever `scale` is ~6x off) and rendered as a tiny blob. Fix with
  **`modulate_scale`** (uniform), NOT `width=` — `width=` scales only X and squashes it flat.
- **Wall art must be a FLAT print, not a standing/wheeled display.** The first "planets" pick was a
  wheeled EASEL (0.26 m deep) that read as a frame on a stand. Check depth; pick a thin canvas
  (`d ≈ 0.005–0.03 m`). Pre-scale art small (0.5×0.5) — `place_on_wall_*` derives mount height from
  the art's height, so a big print hangs too high for a kid's room.
- **Cubby toys go `place_inside`, decor goes `place_on_top`** — baskets tucked into the compartments,
  soft toys + a plant styled on the top surface.
- **Zone the room by loading long runs on one long wall** (cubby + bookshelf on the right) so the
  `RoomGroup` sizes a room with clear sleep / study / play areas.

## VLM feedback we hit and how we resolved it
- **RoomProportions drifted** 0.83 → 0.85 → 0.92 → 0.9 as furniture filled in. Held the size through
  Phase 1–2 (render wins early), then applied `modulate_scale=0.80` in the final phase **and** added a
  bean bag to fill the open play floor (better than over-shrinking). Converged to ~0.9 → accepted.
- **RotationConstraint** kept emitting "rotate desk by 180 / rotate chair to face the desk / rotate
  nightstand" on a layout that reads correct in every render. Declined — the VLM rotation check is a
  noisy smoke alarm; `place_desk_chair` already makes the desk pose correct by construction (see
  ../workflow/vlm_feedback.md).
- **ObjectProportions / WallOverlap** stayed clean (one wall element per wall span; art pre-scaled).

## DSL fix this scene motivated
`place_inside` baskets **overflowed** their cubby compartments: the smart-placement footprint cap
sized items against the *largest* region, not the small cell they land in. Fixed in
`tools/planar_regions.py:build_candidate` — each item is now **uniformly clamped to its assigned
tile** (`TILE_FOOTPRINT_FRAC = 0.9`) before placement, a no-op for normal tabletops. See
../workflow/constraints.md ("place_inside / place_on_top tile clamp").
