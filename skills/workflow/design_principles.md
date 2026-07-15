---
id: workflow:design_principles
kind: principles
role: "Composition laws with owner attributions; always-on core doc; sections parsed as lesson:principle/* cards"
---

# Design principles (composition defaults)

Reusable interior-composition rules to apply **by default** when laying out any scene — the
"make the room feel finished and usable" defaults, distilled from build feedback. They go
beyond what any single constraint enforces; apply them unless the brief says otherwise.

## A seating arrangement always gets a small table within reach {#principle-a-seating-arrangement-always-gets-a-small-ta}
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

## A seat's task light belongs WITH the seat {#principle-a-seat-s-task-light-belongs-with-the-seat}
A reading floor lamp / a chair's task light goes **into the chair's group** (`place_on_back` /
`place_on_left` of the chair), not stranded separately in a room corner. It then stays beside the
seat when the group is placed or rotated. The reading nook is one coherent unit, not scattered parts.

## Build a symmetric / repeated unit ONCE, then duplicate with `N * unit` {#principle-build-a-symmetric-repeated-unit-once-then-du}
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

## A desk/counter SCREEN faces the wall the desk stands against (Kunal, 2026-07-13) {#principle-a-desk-counter-screen-faces-the-wall-the-des}
A reception desk, service counter, POS station or check-in desk is worked from the **wall side** —
the operator stands between the desk and the wall it backs onto. So its **monitor faces that wall**,
and the customer sees the screen's BACK. A screen turned broadside to the room (or out at the
customer) reads instantly wrong to anyone who has stood at a counter.

`place_on_top`'s VLM tournament optimizes *position on the surface*, not semantic orientation — it
will happily leave a monitor side-on. Fix it explicitly, on the **RoomGroup** (wall targets are
RoomGroup-only and 90°-snapped), which applies at the end of compile and so overrides the rotation
the placement baked in:
```python
pos = scene.AddAsset("a touchscreen point of sale terminal", asset_id=POS)
with scene.RelativeGroup() as counter_group:
    counter_group.set_anchor(counter)
    counter_group.place_on_top([pos, ...])
...
with scene.RoomGroup() as room:
    room.place_on_back(counter_station, facing="front")   # counter stands against the BACK wall
    room.face(pos, toward="back_wall")                    # so its screen faces the BACK wall
```
Generalizes to anything with a working face on a wall-backed surface: a monitor, a till display, a
staff terminal. Worked example: [../examples/fast_food.md](../examples/fast_food.md).

## A table's HEIGHT must be fit explicitly — `width=` is a SINGLE-AXIS pin (Kunal, 2026-07-13) {#principle-a-table-s-height-must-be-fit-explicitly-widt}
`AddAsset(..., width=0.8)` stretches the **width only**. It does not touch the height, so a mesh that
ships at bar height stays at bar height and **towers over its own seats** — the fast_food cafe table
shipped **0.96 m** tall while its molded chairs are **0.68–0.71 m in TOTAL** (seat ≈ 0.43 m), i.e. the
tabletop sat above the chair backs. The VLM loop is blind to it (`no rescale` every build); a human sees
it immediately.

**Seat height tracks the surface it serves, and the surface must be fit to human dining height** —
dining table ≈ 0.75 m, seat ≈ 0.45 m, bar counter ≈ 1.05 m with a 0.75 m stool. Measure both offline
(`obj.get_whd()` on a pinned id needs no network) and fit the table uniformly:
```python
def _fit_height(obj, h):          # uniform: preserves the mesh's own proportions
    W, H, D = (float(v) for v in obj.get_whd())
    f = h / H
    obj.scale_only_width(W * f); obj.scale_only_height(H * f); obj.scale_only_depth(D * f)
    return obj

table = _fit_height(scene.AddAsset("a cafe table", asset_id=TABLE), 0.75)   # NOT width=0.8
```
The mirror of restaurant's bar-stool rule (a 1.25 m stool at a 0.67 m counter), hit from the table side.

## Wall-backed seating goes on the WALL verbs, never a floor slot (Kunal, 2026-07-13) {#principle-wall-backed-seating-goes-on-the-wall-verbs-n}
A booth, banquette, bench or sofa whose whole point is that it **backs a wall** must be placed with
`place_on_<wall>_wall_<left|center|right>` — the wall-adjacent family, which pins it flush and re-snaps
it after the solve. A floor slot (`place_on_left`, `place_on_front_left`) leaves a **visible gap behind
the seat**: the slot is a third of the ROOM, not of the wall, and `randomness` + the gradient solve
drift the group off it. **A booth backed by air is not a booth.** Omit `facing` — the wall heuristic
already turns wall furniture into the room.
```python
room.place_on_left_wall_left(booth_1)      # RIGHT — flush against the wall
room.place_on_left_wall_right(booth_2)
room.place_on_left(booth_1, facing="right")   # WRONG — floats a bench's back off the wall
```
Same family as bakery's window-bar ("a front SLOT drifts") and kindergarten's "a nook is a corner, not
an island" — stated here as the general seating rule.

## Two furniture groups belong in DIFFERENT regions of the room (Kunal, 2026-07-14) {#principle-two-furniture-groups-belong-in-different-reg}
When a room holds more than one furniture group — a desk workstation AND a daybed, a seating
cluster AND a dining nook — place each in a **distinct region** of the `RoomGroup`, not two
that share a corner. Two groups aimed at the same region crowd each other and there is **no
circulation** around either; the VLM loop is blind to it (`no rotation` / `no wall overlap`
both pass — the pieces are legal, just cramped), and a human sees the choked room instantly.

The trap in `st_writer_studio`: the desk sat at `place_on_back` (back-CENTRE) and the daybed at
`place_on_left_wall_center` — both reached into the shared back-left corner, so the desk chair
crowded the bed and the bed had floor on only two sides. The fix was purely spatial — send the
groups to opposite regions:
```python
room.place_on_back_right(station, facing="back")     # desk -> back-RIGHT third
room.place_on_left_wall_center(daybed, facing="right")  # bed  -> LEFT wall, a region away
room.place_on_back_wall_left(shelf)                  # shelf off the right wall so it, too, clears
```
Prefer the **corner / third** verbs (`place_on_back_right`, `place_on_front_left`, `…_corner`)
to spread groups diagonally; reserve wall-CENTRE for a single group or a wall-flush run. A room
that leaves open floor *between* its zones reads calm; two zones fighting for one region reads
broken even when every constraint is satisfied. Worked example:
[../examples/residential_variations.md](../examples/residential_variations.md).

## Related {#principle-related}
- Grouping mechanics, `place_on_*`, `face`, and the `place_on_top` behavior these rely on:
  [../dsl_reference.md](../dsl_reference.md).
- Per-category "baked-in defaults" (e.g. a rug under seating) live in the [../examples/](../examples/).
