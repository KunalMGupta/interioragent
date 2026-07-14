# Pantry

- **Pattern:** Galley/corridor (corridor + library): stocked shelf runs on BOTH long walls, counter
  capping the back wall under a window, fridge beside it, clear center aisle. Front wall = the
  single door + step stool + crate/sack corner.
- **Jitter/randomness:** RoomGroup randomness=0.05; modulate_scale=0.85
- **Review first:** the SHELF STOCKING — this is the whole scene, and `place_inside` fights you
  (see below). Then the room width (the shrink vote never goes quiet on a passage room).
- **Asset-gap risk:** HIGH — there is **no pre-stocked domestic pantry shelf** in the dataset. The
  only pre-filled food fixtures are branded retail (`custom/d79cf88b` supermarket gondola,
  `custom/e6b832f2` Borges nut stand, `custom/5996d434` pizza rack). I test-rendered the gondola as
  a run: it reads as a **wall of dark chaotic panels**, not stocked shelving. Rejected — the racks
  are open oak shelving stocked by hand instead.

## The lesson this scene exists for: you cannot densely stock a tall rack with `place_inside`

Six builds went into this and the intuition ("more goods = fuller shelf") is **backwards**.
`place_inside` resizes every item to a tile it computes from the anchor + the goods list — the
scene has no say (`modulate_scale` is a no-op on on-top/inside items). Measured on the hero rack
(`hssd/93ca3ca5`, 2.4 m) by calling `tools/planar_regions.solve_placement` directly:

| goods passed | solved item width | render |
|---|---|---|
| 3 | 0.15 m | reads |
| 8 | 0.06 m | specks |
| 18 | ~0.04 m | dust |
| 36 | invisible | **emptier than 6** |

`judge_tile_size` shrinks the tile until *all n items would fit on ONE shelf board*, then every item
is resized to it. So the rack's total product mass is roughly **fixed**; the goods list only chooses
how finely it is ground up. Two rules fall out:

1. **A few substantial goods per rack (~6), never a long list.** Adding goods to fix an empty-looking
   shelf makes it emptier. This is the opposite of the jewelry_shop "mass the product" instinct —
   mass it, but not *inside a tall fixture*.
2. **One oversized mesh poisons the whole rack.** `judge_tile_size` floors the tile at the LARGEST
   item's footprint, so the 1.07 m box stack forced ~1 m tiles → a single lonely prop per board.
   Box stacks / cartons / the jar tray go on the FLOOR or the counter, at their own size. Conversely,
   keeping ONE basket (0.45 m) in each list *holds the floor generous* so the jars beside it come out
   chunky instead of tiny — that is the lever, not the count.

**Where the product actually reads: `place_on_top` on the 0.9 m counter.** Same solver, short anchor →
the height-fit gives believable ~0.2 m jars/tins at viewing height, and they render beautifully. So
the pantry's category cue (jars, canisters, tins) is massed on the counter, with bulk (boxes, crates,
burlap sack) on the floor — and the racks carry the *structure*, not the identity.

## Other gotchas hit

- **`place_on_<wall>_wall_back` does not exist** — wall slots are thirds: `left` / `center` / `right`.
- **`add_lighting` fixture size ↔ count coupling** (library lesson, hit again): the globe pendant
  renders ~1.5 m at scale 1.0 and filled the ceiling; `modulate_scale=0.3` shrank it to a dot AND
  multiplied it into **8** fixtures. `modulate_scale=0.5, density=0.006` → 2-3 calm pendants.
- **future/ scale metadata is unreliable** (corridor lesson): the fridge is retargeted by height
  (`scale(w * 1.8 / h)`); the crate and step stool load furniture-sized and are scaled to 0.6 / 0.5.
- **`rescale room by 0.72` persists on every build** — declined per the corridor rule: a walk-in
  pantry's clear aisle IS the category, and the occupancy vote reads it as empty floor forever.
- **The MCP `run_scene` tool can return ANOTHER scene's report** when other builds run concurrently
  on the box (it picked up a Laboratory run mid-session). When the machine is busy, run
  `workbench.py run` directly and trust the run_dir it prints.
