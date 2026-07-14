"""
Grocery store — SUPERSEDED.

The worked, built, VLM-clean grocery store is `scenes/work/grocery_store_v1.py` (seed=23); the
recipe is `skills/examples/grocery_store.md`. This file was a never-built first draft, and nearly
every move in it was wrong in a way worth remembering:

  - It hung the aisles on `GridGroup.place_grid(..., cols=3)`. A grid CANNOT open a shopper aisle:
    its inter-row gap is `sparsity * row_depth`, and a gondola is only ~0.38 m deep (warehouse's
    forklift-aisle lesson). Aisles come from the ROOM's slots, not from a grid.
  - It placed the gondola run and the fridge case at wall CENTRES. The interior wall-cameras stand
    at each wall's centre at ~1.4 m, so a 1.93 m gondola there literally contains the camera: both
    side views render PURE BLACK, while the VLM still reports a clean `no rotation / no wall
    overlap`. The worked scene keeps every wall centre short (a 0.93 m counter), empty, or an
    OPENING (the door), and puts the gondolas in the side slots — where, flanking the counter, they
    also became the money shot from the entrance.
  - It used a `PileGroup` of "a crate of fresh produce" on a produce bin. Produce props do exist,
    but every produce FIXTURE in the dataset is EMPTY, and the picker's top "crate of fruit"
    (hssd/2c751d20…) renders as a near-empty WHITE BLOB. Produce has to be MASSED as product on a
    low market table (jewelry_shop's rule).
  - It anchored the lighting to a shopping cart. There IS no supermarket shopping cart in the
    dataset (the best hit is a pink personal granny-trolley), and `add_lighting` on a floor prop is
    not how a shop's ceiling is lit.
  - `place_grid`/`place_row` of anything wide dropped into ONE room slot inflates the WHOLE shell:
    the room is the SUM of 5 column maxima (`groups.py:compute_grid_dims`), so a 4 m row in the
    centre column adds 4 m of width outright.
"""
