# Warehouse / industrial storage — worked example

Status: **built & VLM-clean** (`scenes/work/warehouse.py`, seed=31). Final compile: `no rescale`,
`no rotation`, `no wall overlap`. Built coarse-to-fine through the workbench.

> **v2 (2026-07-06):** rebuilt around Kunal's **ingested custom warehouse gear** — a real forklift,
> pallet jack, traffic cones, roller-shutter dock door, exit sign, gas cylinder, wooden crates, and a
> factory-boiler backdrop. This is what lifts the scene from "credible" to "unmistakable"; the racking
> layout below is unchanged. Two v2-specific lessons: the **working loading dock** and the **-Z-front
> vehicle facing gotcha** (both at the bottom). Custom ids in memory [[ingested-warehouse-office-assets]].

## Prompt this covers
- "an industrial warehouse: tall steel pallet racking loaded with boxes, wide forklift aisles, a
  loading/staging area with stacked pallets, concrete floor, high ceiling + industrial lighting."

## Plan summary (from the planner)
"Industrial Warehouse Merchandising Rhythm": tall racks in a modular grid, DOUBLE-LOADED aisles, a
loading/staging zone with stacked pallets, concrete + neutral-grey + steel palette, square/linear
industrial lighting, safety floor markings. (A Costco-ish merchandising warehouse — legible rows.)

## The layout idea: racking IS the structure; the room's THIRDS make the aisle
A warehouse is repeating loaded rack rows with wide forklift aisles between them. Two constraints shape
the recipe:
- **`GridGroup.place_grid` can't make a forklift aisle.** Its inter-row gap is `sparsity·row_depth`,
  and racks are shallow (~0.6 m), so the widest aisle it can open is ~0.6 m. Too tight.
- **So build each rack ROW as a butted line and let the ROOM's thirds supply the aisle.** A "rack wall"
  = `GridGroup.place_row(n*rack)` (a deterministic frozen group → exact alignment, no overlap solve).
  Place one wall on the BACK third and one on the CENTER third; the room auto-sizes so the gap between
  those two thirds is a generous aisle.
- **Double-loaded aisle = opposing facings.** Back wall `facing="front"` + center wall `facing="back"`
  → both loaded faces point INTO the same aisle (the collage's money shot). Leave the FRONT third open
  as a loading/staging DOCK + the entrance.

## Working skeleton (coarse-to-fine)

```python
scene = SceneProgRoom("Warehouse", seed=31)
RACK = "hssd/44935cd7942c9a256e13286fd3c07e148fb3e5aa"   # loaded industrial rack: dark frame, plank decking
PALLET, BOXES_CARD = "hssd/a5d4b9f0…", "hssd/71e625e1…"
WORKBENCH = "hssd/81ad56ba…"

def rack_wall(n):                                  # a butted horizontal row of loaded racks
    racks = n * scene.AddAsset("a heavy-duty industrial warehouse pallet racking bay loaded with boxes", asset_id=RACK)
    with scene.GridGroup(sparsity=0.05, randomness=0.0) as w:
        w.place_row(racks)
    return w
wall_back, wall_mid = rack_wall(5), rack_wall(5)

# FRONT dock: a wide row of brown cardboard box-stacks, sized UP to palletized-load scale (~1.2 m).
# (See "place_on_top" note — do NOT put boxes on a flat pallet.)
dock_items = [_fit_w(scene.AddAsset("a stack of brown cardboard shipping boxes", asset_id=BOXES_CARD), 1.2) for _ in range(5)]
with scene.GridGroup(sparsity=0.5, randomness=0.15) as dock:
    dock.place_row(dock_items)
# a corner staging pile + a packing station (workbench + box on top — bench has real height so on_top is fine)
staging_l = staging_cluster()
with scene.RelativeGroup() as packing:
    packing.set_anchor(scene.AddAsset("a heavy-duty industrial steel workbench", asset_id=WORKBENCH))
    packing.place_on_top(scene.AddAsset("a stack of brown cardboard shipping boxes", asset_id=BOXES_CARD))

with scene.RoomGroup(modulate_scale=0.85, randomness=0.05, max_height=5.0) as room:
    room.place_walls(floor_texture="polished grey concrete warehouse floor with painted safety lines",
                     ceiling_texture="light grey exposed industrial ceiling with steel beams",
                     wall_texture="light grey industrial corrugated metal wall")
    room.place_on_back(wall_back, facing="front")     # loaded face -> aisle
    room.place_on_center(wall_mid, facing="back")     # loaded face -> SAME aisle = double-loaded
    room.place_on_front(dock, facing="back")          # front third = busy dock
    room.place_on_front_left_corner(staging_l, facing="back")
    room.place_on_front_right(packing, facing="back")
    room.place_door("right_wall", position="center")  # NB: position is a wall label (left/center/right), NOT "front"
    room.place_on_back_wall_center(scene.AddAsset("a large plain black round wall clock"))
    room.add_lighting("a row of bright industrial linear ceiling lights", density=0.02, modulate_scale=2.4)
scene.export("warehouse.blend")
```

## What worked / gotchas
- **`place_grid` won't give forklift aisles** (gap capped at `sparsity·depth`); use `place_row` lines in
  separate room thirds. **Double-loaded aisle = back `facing="front"` + center `facing="back"`.**
- **`add_lighting(..., modulate_scale=)` is the fixture-SIZE lever.** Over a big/high ceiling, small
  fixtures render as a scattered *starfield* of dots (density alone can't fix it — that only adds more
  dots). Scale the fixture up (~2.4×) at low density (~0.02) → a few visible linear high-bays.
  Corollary from the bar: a SINGULAR fixture query (not "a row of…") avoids pre-clustered meshes.
  (Note: the ceiling still renders dark — high-bays light DOWNWARD, so the ceiling stays in shadow.
  That's physically correct, not a bug.)
- **`place_on_top` onto a flat PALLET is broken.** `_fit_on_top` sizes the placed object to the anchor's
  HEIGHT; a pallet's height is ~its board thickness, so the boxes shrink to nothing and vanish. Two
  robust fixes: (a) use the floor box-stack asset directly (it already reads as stacked cardboard), or
  (b) put things on a THICK anchor — the workbench packing station works perfectly.
- **Size small props UP.** The box-stack asset is desk-parcel scale by default; `_fit_w(box, 1.2)` makes
  it read as a palletized load, not a shoebox. Same width-only pin used for pallets (~1.2 m) and totes.
- **RoomProportions oscillates** (1.0→wants 0.7; 0.78→wants 1.2). Settle mid (0.85) and let the render
  be the arbiter — same lesson as bar/living_room. Filling the empty FRONT third with a busy dock did
  more for the "not-empty" read than any rescale.

## Asset gaps (home-furniture dataset, HIGH risk for this theme)
This dataset is home/retail furniture; true warehouse gear is thin. Accepted compromises rather than
ingesting:
- **Rack load renders cyan/teal.** `hssd/44935cd7…` is the best pallet-rack silhouette (dark boltless
  frame + plank decking + palletized goods), but its goods are baked blue and it's a complete mesh — you
  CAN'T recolor it. Balanced by pushing lots of brown cardboard to the foreground (the dock row).
- **No forklift exists** — every "forklift/truck" hit is a wooden TOY. Left as a follow-up ingest.
- **No real industrial signage** — "a hazard safety sign" retrieved a pirate skull-and-crossbones FLAG;
  "traffic cone" returned orange cushions. Skip signage rather than ship an off-theme prop.
- **Follow-up if a stricter look is wanted:** ingest GLBs (Y-up, +Z front, metres) for a forklift + a
  tall black pallet rack via `ingest_glbs`, same as the dental unit / server rack in prior sessions.

## v2: the working loading DOCK (ingested gear)
Once real gear exists, the open FRONT third stops being "a floor with boxes" and becomes a working dock:
```python
# forklift (hero) + traffic cones, as one group in the front-left
with scene.RelativeGroup() as fork_grp:
    fork_grp.set_anchor(scene.AddAsset("an industrial warehouse forklift", asset_id=FORKLIFT))
    fork_grp.place_on_left(scene.AddAsset("an orange traffic safety cone", asset_id=CONE))
    fork_grp.place_on_right(scene.AddAsset("an orange traffic safety cone", asset_id=CONE))
# staged dock row: crates + boxes + a PARKED pallet jack (row → rotation 0 = correct heading)
with scene.GridGroup(sparsity=0.5, randomness=0.12) as dock:
    dock.place_row([crate, pallet_jack, box, crate])
...
room.place_on_front_left(fork_grp, facing="front")   # see -Z gotcha
room.place_on_front(dock, facing="back")
room.place_on_front_right(packing, facing="back")     # workbench + gas cylinder
room.place_on_front_wall_center(scene.AddAsset("a grey metal roller shutter dock door", asset_id=SHUTTER))
room.place_on_front_wall_right(scene.AddAsset("a green emergency exit sign", asset_id=EXIT), bottom=2.2)
room.place_on_back_right_corner(scene.AddAsset("a rusty factory boiler with tanks", asset_id=TANKS), facing="front")
```
- **Roller shutter as the dock door** (placement `wall`, `place_on_front_wall_center`) reads far more
  like a warehouse than a house door; keep a personnel door on a side wall too.
- **Exit sign** mounts high — `place_on_front_wall_right(..., bottom=2.2)`.
- **A tall industrial backdrop in a back corner** (factory boiler + tanks) gives depth; use 4-wide (not
  5-wide) rack walls so the back corners stay free of the rack ends for it.

## -Z-front facing gotcha (ingested vehicle GLBs)
Downloaded vehicle GLBs (forklift, pallet jack) were modelled with their **front on −Z**, opposite the
+Z ingest convention — so a `facing=` slot points them 180° wrong (VLM flags "rotate forklift by 180").
Two fixes: (a) place the vehicle facing the **opposite** of intent (the forklift is placed `facing="front"`
to actually face into the room); (b) drop it in a **`GridGroup` row**, whose `_place_row` sets rotation 0
= the vehicle's real forward, so it parks correctly (the pallet jack). General rule: after ingesting,
eyeball each vehicle's heading in the first render and flip per-asset; the ingest tool does NOT re-orient.

## Manual constraints used
- None. The GridGroup rows are deterministic; the door auto-clearance keeps the entrance clear; the
  forklift aisle is geometric (room thirds), not a `ClearanceConstraint`.
