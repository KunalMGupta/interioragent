# Pantry — worked example ("Vertical-Integrated Pantry System")

Built via the guided 9-gate flow from the planner target
(`tmp/plan_A_walk_in_food_pantry___storage_/plan.png`). Program: `scenes/pantry.py` (seed=20);
converged copy beside this file (`pantry_v1.py`). Layout is the **library/corridor galley** verbatim
— twin shelf runs on the long walls, a clear centre aisle, a service end — so the layout took **one**
phase-1 build. The real subject of this example is the thing that took **six**: a room whose entire
category read lives *inside a tall fixture*, which is precisely what the placement solver cannot do.

## Prompt(s) this covers
- "a pantry" / walk-in larder / dry store / food storage room.

## Plan summary
Planner → **"Vertical-Integrated Pantry System."** A narrow walk-in: tall white-and-oak open shelving
floor-to-ceiling down both long walls, densely stocked with glass jars, canisters, boxes and baskets;
a wood-topped work counter and a freestanding stainless fridge on the service side; a two-step stool
for the high shelves; a pendant over the aisle. Palette: light neutrals + warm oak + glass.

## THE layout (free — copy corridor/library)
- **LEFT (long)**: `GridGroup.place_row(4 * stocked_shelf_unit)` at `left_wall_center`.
- **RIGHT (long)**: `place_row(3 * unit)` at `right_wall_center` + the **fridge** at `right_wall_right`.
- **BACK (short)**: the **work counter run** (2 units, dressed on top) + a `place_window_standard`
  above it + the bulk boxes on the floor beside it. This end is the money shot.
- **FRONT (short)**: the single **door** + the step stool + a crate/sack corner.
- **CENTRE**: EMPTY — the walk-in aisle IS the category (corridor rule; expect the shrink vote forever).

## THE lesson: you cannot densely stock a tall rack — adding goods makes it EMPTIER

The prompt leads with "floor-to-ceiling shelving **stocked** with jars, cans, boxes and sacks", and
jewelry_shop says *mass the PRODUCT*. Both point at `place_inside` on the racks. Both are traps.

`place_inside` resizes every item to a **tile** it derives from the anchor + the goods list; the scene
has no say (`modulate_scale` is a no-op on inside/on-top items — tv_studio). Measured by calling
`tools/planar_regions.solve_placement` directly on the 2.4 m rack (do this — it is a minute, and it
ends the guessing that a full build cannot):

| goods passed to `place_inside` | solved item width | render |
|---|---|---|
| 3 | 0.15 m | reads |
| 8 | 0.06 m | specks |
| 18 | ~0.04 m | dust |
| **36** | invisible | **emptier than 6** |

Cause: `judge_tile_size` shrinks the tile until *all n items would fit on **ONE** shelf board*, then
every item is resized to it. **A rack's total product mass is roughly FIXED** — the goods list only
chooses how finely it gets ground up. Hence:

1. **A FEW substantial goods per rack (~6), never a long list.** Adding goods to fix an empty-looking
   shelf is the one move that guarantees it stays empty. I did it three times.
2. **One oversized mesh poisons the whole rack.** The tile floors at the LARGEST item's footprint, so a
   1.07 m box stack forced ~1 m tiles → *one lonely prop per board*. Bulk (box stacks, cartons, crates)
   belongs on the **floor**, at its own size. Conversely, keep **one basket (0.45 m)** in each list: it
   holds the tile floor generous so the jars beside it come out chunky instead of tiny. The lever on
   apparent density is the **footprint spread of the list**, not its length.
3. **Product reads on a LOW anchor.** `place_on_top` on the **0.9 m counter** — same solver — height-fits
   the same jar sets to a believable **~0.2 m at viewing height**, and they rendered perfectly first try.

> **This lesson already existed** in [laundry_room.md](laundry_room.md) ("`place_inside` cannot carry a
> category read … put the product on the LOW surface") and **retrieval did not surface it** — the
> procedural signature matched corridor/library/locker_room on *layout*, and the real difficulty was in
> the *surface layer*. When a prompt's identity lives in what sits ON/IN the furniture, go read the
> laundry_room + jewelry_shop product rules **before** gate 4, whatever the retriever picked.

**So: the racks carry STRUCTURE; the counter and the floor carry IDENTITY.** Generalised statement of
jewelry_shop: "show the product at viewing height" is not really about eye level — it is about choosing
an **anchor whose solver will render the product at a size you can see**.

## Assets (audited previews, gate 3)
| Role | id | note |
|---|---|---|
| Shelf rack (hero ×7) | `hssd/93ca3ca5…` | tall oak+white open shelving; scale-by-height to 2.4 m |
| Work counter | `hssd/fa5562e2…` | white base cabinet, warm wood worktop — **the identity surface** |
| Fridge | `future/a266bc1f…` | stainless side-by-side; future/ scale is unreliable → retarget to 1.8 m |
| Step stool | `hssd/8a199393…` | wooden two-step; loads ~1 m wide → `scale(0.5)` or it reads as a bench |
| Jars / tins (counter) | `hssd/309e63ae…`, `hssd/11b88fa1…`, `hssd/e20a7e44…` | glass jars, dark canisters, café/sucre tins |
| Spice rack (shelf) | `hssd/dd3b98de…` | twelve glass jars in ONE mesh — the densest food mesh available |
| Basket (shelf) | `future/8a0f0758…` | 0.45 m footprint — **include one per rack to hold the tile floor up** |
| Bulk boxes (floor) | `hssd/66f9623b…` | 1.07 m — floor ONLY; on a rack it poisons the tile |
| Crate + sack (floor) | `custom/eb9d3e7b…`, `future/c1ebb64b…` | the "sacks of dry goods" cue; crate `scale(0.6)` |

**Asset gap — there is no pre-stocked domestic pantry shelf.** The only pre-filled food fixtures are
branded retail: `custom/d79cf88b` (supermarket gondola), `custom/e6b832f2` (Borges nut stand),
`custom/5996d434` (pizza rack). I **test-rendered the gondola as a wall run** rather than trusting its
preview: it comes out a **wall of dark chaotic panels** (the mesh is largely black-textured), nothing
like stocked shelving. Rejected. A 3-minute probe scene beats a 10-minute full build for this call.

## VLM feedback log
- `rescale room by 0.6–0.8` on **every** build → applied one decisive `modulate_scale=0.85`, then
  **declined the residual** (corridor: a passage room's clear lane reads as empty floor forever).
- `no rotation` / `no wall overlap` clean throughout — all wall furniture omitted `facing`.
- **The VLM loop was clean while the racks were EMPTY.** It checks per-object geometry, not "does this
  look like a pantry" (jewelry_shop). The empty shelves were caught by *looking*, then by crop-zooming
  the render — do that whenever a fixture is supposed to be full.
- `add_lighting` size↔count coupling (library, hit again): the globe renders ~1.5 m at scale 1.0 and
  filled the ceiling; `modulate_scale=0.3` shrank it to a dot **and multiplied it into 8**. Settled
  `modulate_scale=0.5, density=0.006` → 2 calm pendants.

## Tooling gotcha
**MCP `run_scene` can return ANOTHER scene's report/renders** when other builds share the box — mine
came back as a *Laboratory*, and two builds were nearly diagnosed off someone else's renders. On a busy
machine run `workbench.py run` directly and trust the run_dir **it** prints; a report whose asset list
doesn't match your program is not your build.
