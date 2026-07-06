# Children's room — worked example

Status: **built & VLM-clean** (`scenes/work/children_room.py`, seed=7). Final compile returns
`no rescale` / `no rotation` / `no wall overlap`; RoomProportions converged to ~0.9. Planner-driven,
built coarse-to-fine through the workbench.

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

## Skeleton (the working structure)
```python
scene = SceneProgRoom("ChildrenRoom", seed=7)
scene.prefetch_assets([...all queries...])          # warm the retrieval cache (5x faster cold build)

# Phase 1 majors — PIN a clean SINGLE bed (the shortlist is full of BUNK beds) + a kids desk
bed  = scene.AddAsset("a kids single bed with colorful bedding", asset_id="future/f65434b4-…")
desk = scene.AddAsset("a kids wooden study desk with drawers",  asset_id="hssd/49fcf2005b…")
# nightstand, chair, cubby, bookshelf via plain AddAsset

# Phase 2 details — pin small lamps (generic "desk lamp" came back an OVERSIZED designer lamp)
mushroom_lamp = AddAsset("a mushroom shaped table lamp", asset_id="hssd/fd1e99da…")
desk_lamp     = AddAsset("a small childrens desk lamp",  asset_id="hssd/5d1cede6…")
baskets       = 3 * AddAsset("a woven seagrass storage basket")   # ONE unit, duplicated
beanbag       = AddAsset("a large yellow kids bean bag chair", asset_id="hssd/0d129d28…",
                         modulate_scale=5.0)          # its scale metadata loads it ~6x too small

# Phase 3 art — FLAT kid canvases, pre-scaled small (place_on_wall_* mounts by art height)
ocean_art, blossom_art = AddAsset(…8e37f5ae…), AddAsset(…5ece73ce…)
for a in (ocean_art, blossom_art): a.scale_only_width(0.5); a.scale_only_height(0.5); a.scale_only_depth(0.03)

with scene.RelativeGroup() as desk_group:
    desk_group.place_desk_chair(desk, chair); desk_group.place_on_top([desk_lamp, pencils])
with scene.RelativeGroup() as ns_group:
    ns_group.set_anchor(nightstand); ns_group.place_on_top(mushroom_lamp)
with scene.RelativeGroup() as cubby_group:
    cubby_group.set_anchor(cubby); cubby_group.place_inside(baskets)
    cubby_group.place_on_top([teddy, bunny, shelf_plant])
with scene.RelativeGroup() as bed_group:
    bed_group.set_anchor(bed); bed_group.place_on_back_right(ns_group)
    bed_group.place_rug("a soft scalloped cream kids play rug with pastel dots", size=0.9)
    bed_group.add_lighting("a warm flush kids ceiling light", density=0)

with scene.RoomGroup(modulate_scale=0.80, randomness=0.15) as room:
    room.place_walls(floor_texture="light maple wood planks", ceiling_texture="soft white",
                     wall_texture="pale sky blue")
    room.place_on_back_wall_center(bed_group)
    room.place_on_right_wall_left(cubby_group); room.place_on_right_wall_right(bookshelf)
    room.place_on_left_wall_center(desk_group);  room.place_on_right(beanbag)
    room.place_on_wall_left_center(ocean_art);   room.place_on_wall_right_center(blossom_art)
    room.place_window_standard("front_wall", position="center", curtain="bright cheerful patterned curtains")
    room.place_door("front_wall", position="right")
```

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
