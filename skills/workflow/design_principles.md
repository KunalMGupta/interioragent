# Design principles (composition defaults)

Reusable interior-composition rules to apply **by default** when laying out any scene — the
"make the room feel finished and usable" defaults, distilled from build feedback. They go
beyond what any single constraint enforces; apply them unless the brief says otherwise.

## A seating arrangement always gets a small table within reach
Any seat — reading chair, accent chair, armchair nook, sofa — needs a surface within reach
(side/accent table, coffee table) for a drink, book, or remote. A lone chair reads unfinished
and unusable.

Build the table as part of the seat's group so they travel (and rotate) together as one nook:
```python
with scene.RelativeGroup() as chair_group:
    chair_group.set_anchor(armchair)
    chair_group.place_on_left(side_table)      # a table always belongs by a seat
    chair_group.place_on_back(floor_lamp)      # (task light — see next)
bed_group.place_on_right_further(chair_group)  # place the whole nook as a unit
```

## A seat's task light belongs WITH the seat
A reading floor lamp / a chair's task light goes **into the chair's group** (`place_on_back` /
`place_on_left` of the chair), not stranded separately in a room corner. It then stays beside the
seat when the group is placed or rotated. The reading nook is one coherent unit, not scattered parts.

## Build a symmetric / repeated unit ONCE, then duplicate with `N * unit`
For matching pieces — a pair of nightstands-with-lamps, a row of identical chairs, two flanking
plants — build ONE fully-composed unit and **duplicate** it. NEVER construct the copies individually.
```python
# RIGHT — one unit, then a matching pair (identical, and the heavy work runs once)
with scene.RelativeGroup() as ns:
    ns.set_anchor(nightstand)
    ns.place_on_top(lamp)
ns_l, ns_r = 2 * ns

# WRONG — two units built separately: the two lamps come out DIFFERENT sizes
with scene.RelativeGroup() as ns_l:
    ns_l.set_anchor(nightstand_l); ns_l.place_on_top(lamp_l)
with scene.RelativeGroup() as ns_r:
    ns_r.set_anchor(nightstand_r); ns_r.place_on_top(lamp_r)
```
**Why it matters:** `place_on_top` runs a VLM sizing/placement **tournament each call**, so building
the units separately sizes their on-top items *differently* (a mismatched pair) and does the heavy
work twice. `N * group` deep-copies the anchor + its already-placed children (`SceneProgObject.copy`),
giving identical units for free. This applies to any repeated *composed* unit, not just nightstands.

## Related
- Grouping mechanics, `place_on_*`, `face`, and the `place_on_top` behavior these rely on:
  [../dsl_reference.md](../dsl_reference.md).
- Per-category "baked-in defaults" (e.g. a rug under seating) live in the [../examples/](../examples/).
