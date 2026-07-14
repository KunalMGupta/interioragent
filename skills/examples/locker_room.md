# Locker room — worked example

A premium fitness/team **locker room**, built from the planner target "Pro Locker Spine & Wet-Dry
Flow". The reference for a **wide corridor room whose long rows go flush-on-wall or down-the-centre**
(the layout trap that wrecks these rooms). Read alongside `../workflow/coarse_to_fine.md`.

## Status
Built as `scenes/locker_room.py`. `locker_room_v1.py` is that same program, phase-gated
(2026-07-13), lint-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record); a FULL rebuild the same day reproduced the original (clean signals, the documented occupancy 0.8 vote declined per the lesson below).

## Prompt(s) this covers
- "a team sports locker room" / gym changing rooms / spa locker rooms.

## Plan summary
Cool-clinical + warm wood: **grey porcelain floor tile, white wall tile, dark metal lockers, oak
benches, rolled white towels**. The room reads as a **wide corridor**: a continuous **locker spine**
on one long wall, **oak benches down the centre aisle**, a **dressing wall** (towel cubbies + entry
door) opposite, a **grooming zone** (sinks + mirror) on one short wall, and a **wet zone** (glass
shower stalls) on the other. Ceiling = a grid of recessed downlights.

## Assets (all pinned; audited previews)
| Role | id | note |
|---|---|---|
| Locker bank (hero) | `future/e96b46b7-a9f5-4e2e-b1d7-0dfc670d5461` | grey vented FULL-HEIGHT metal bank — reads as a real locker; better than the black 3-door `902f9b5b` (which has furniture-like tapered legs). Dataset locker pool is thin (~8 units); for anything more premium, ingest a glb. |
| Bench | `hssd/1ccdd93676483606fdf96f81d6111a7c0e3b1d9f` | slatted oak top, black legs |
| Towel cubbies | `hssd/c075ced257f48c753d22d3bd3400186d6de319da` | 6-compartment oak cube |
| Grooming vanity | `future/8275e724-5f49-4e38-a65f-6d007cd47985` | sink cabinet, **no mirror** — hang one separately |
| Rolled towels | `hssd/6ece1a15f0f508aab2371808d58eefa8420cf725` | the "premium" cue; put them on cubbies + counter |
| Wall mirror | `hssd/fe6a04f91f6d8c9d44b6c1ec30350ae3b12c6ef0` | large rectangular, hung above the sinks |
| Glass shower | `hssd/b74cfc2ae648ddcf1375088e23d9643b7c5ed736` | corner glass panel + fixture (reads faintly — accent only) |

Lockers/cubbies route to `CabinetandShelfRetriever`, vanity to `BathroomVanityUnitRetriever`, all
by pinned id so routing is moot. No ingestion needed — the dataset covers a locker room well.

## THE layout lesson (why this example exists)
A long **row** (lockers, benches, cubbies) has exactly two correct placements:
- **flush on a wall** — `place_on_<wall>_wall_center(row, facing="<wall>")`; the auto-sizer aligns
  the row's long axis *along* that wall.
- **down the centre** — `place_on_center(row)`; `GridGroup.place_row` lays items along the room's
  width, already parallel to the long walls.

Dropping a long row with **`place_on_<side>`** (`place_on_right(bench_row)`) puts it as a **diagonal
line floating across the open floor** and **balloons the auto-sized room** (14×10 m vs the intended
11×5). First build did exactly this; the fix was to reorient the corridor so the long walls are
back/front (lockers on back, cubbies+door on front) and run the benches down the centre — where
`place_row`'s natural axis is already right, so no `face()` fiddling.

## Program
[`locker_room_v1.py`](locker_room_v1.py) — phase 1 the floor anchors (locker spine, centre bench
row, cubby row, grooming stations, walls + door), phase 2 the surface dressing (rolled towels on the
cubbies, water cooler, laundry hamper), phase 3 the walls & mood (shower stalls, wall clock,
downlights). `workbench run skills/examples/locker_room_v1.py --phase 1` builds the layout alone in
~1–2 min.

## Overlaps & over-height: keep modulate_scale=1.0, don't fight the auto-sizer
Three failures all traced to the SAME misuse — treating the VLM's occupancy-driven "rescale room by
0.8" as a real instruction and fighting the auto-sizer:
- **`modulate_scale<1.0` is unsafe when the room is furniture-packed.** RoomGroup sizes WIDTH/DEPTH to
  FIT the furniture at scale 1.0; `<1.0` shrinks the shell below that footprint, so fixed-size rows
  overflow their grid slots and the overlap solver *can't undo it* (no free floor). At 0.8 the centre
  bench row punched into the grooming vanity on the short wall. Fix: hold `modulate_scale=1.0` and add
  furniture to fill a room — never shrink the shell into it. (VLM room-rescale is occupancy-only; ignore
  it when walls are loaded.)
- **Don't drop a free-standing prop into a CORNER already claimed by a full-width wall row.** The 6-bank
  locker spine fills the whole back wall, so a `place_on_back_right_corner` hamper lands *inside* the
  spine's footprint and overlaps it (a corner item vs a full-wall row has nowhere to go on either axis).
  Fix: put it in a free wall slot — here the wet-zone `right_wall_center`, between the two showers.
- **Wall art can punch through the ceiling with no constraint catching it.** `place_on_wall_back_center`
  stacks art above its support (the tall lockers) and scales it to `~(WIDTH/3)*0.6` (grows with room
  width); nothing clamps the top to HEIGHT (only *floor* objects grow the ceiling). A clock over the
  locker spine ended ~4.2 m in a 3 m room. Added `RoomGroup._warn_over_height()` (warns at compile,
  lists offenders + overage, records to `scene.vlm_feedback`). Scene fix: hang such art over a LOW
  support (the cubby wall via `place_on_wall_front_center`) so it clears the ceiling.

## A mirror over a SINK RUN: use MirrorStationGroup, not `place_on_wall_*`
A plain wall mirror (`place_on_wall_left_center`) is **capped to a wall-third** (`min(target_width,
(DEPTH/3)*0.6)`), so over a two-vanity grooming run it only covers ONE sink — you can't widen it from
the scene. `MirrorStationGroup` instead sizes its mirror to the **station/anchor width** (uncapped,
`* width_ratio`) and stands it proud of the wall. Build one station per vanity (anchor = vanity,
`place_mirror(mirror)`), row them, and place the row on the wall — a mirror lands over EACH vanity,
covering the whole run:
```python
def grooming_station():
    with scene.MirrorStationGroup() as st:
        st.set_anchor(scene.AddAsset("a bathroom vanity with a sink", asset_id=_VANITY))
        st.place_mirror(scene.AddAsset("a large rectangular wall mirror", asset_id=_MIRROR))
    return st
grooming = [grooming_station() for _ in range(2)]
with scene.GridGroup(sparsity=0.06) as grooming_row: grooming_row.place_row(grooming)
...
room.place_on_left_wall_center(grooming_row, facing="left")   # see facing note below
```
**Facing exception for MirrorStationGroup:** its mirror sits on the station's +Z (wall) side, so —
opposite to plain furniture — it takes `facing=<the wall it sits on>` (`facing="left"` on the left
wall) so the mirror lands against the wall and the vanities face the room. (A single *seamless* mirror
across both sinks would need lifting the wall-third cap in core — out of scope; two adjacent station
mirrors read fine and match real grooming walls.)

## Facing: don't pass `facing=<the wall's own name>` — the default already faces the room
`place_on_<wall>_wall_*` defaults (via `fill_facing_heuristic`) to facing the OPPOSITE direction —
into the room — so the asset's access side (locker doors, sink, cubby openings) is reachable. Passing
`facing="back"` on the back wall / `facing="left"` on the left wall turns the asset to face the wall
it stands against and denies access. The first build did this on all three wall groups; the grooming
vanity (which has an obvious front) ended up facing the wall and the VLM flagged "rotate vanity to
face center." Fix: **omit `facing`** on `place_on_<wall>_wall_*` and let the heuristic orient it
inward (recompiled → `no rotation`, sinks face the room). Only pass `facing` for a deliberate
non-default pose; if an asset's *unnormalized* mesh front makes it render backwards under the default,
fix that asset once with the front cache, not a per-scene facing override.

## What worked / gotchas
- **Compose ONE cubby+towels unit, `N * unit`, then `GridGroup.place_row`** — the rolled towels
  survived the row + flush-on-wall placement here (unlike the salon's `place_on_front_adjacent`
  chair which vanished). `place_on_top` parents children onto the anchor, so it travels through the
  row + wall placement intact. Same trick put towels on the two-sink grooming unit.
- **`place_on_right_adjacent` does not exist** on RelativeGroup — only `*_front/back_adjacent`. Use
  plain `place_on_right`.
- **The sink vanity has no mirror** — hang a wall mirror above it with `place_on_wall_left_center`.
- **Rolled white towels are the "premium" cue** — a bare locker room reads institutional; towels on
  the cubbies + counter make it read spa/pro.

## VLM feedback we hit and how we resolved it
- **v1 "rescale room by 0.8" + a diagonal floating bench line** → not a size problem: the floating
  `place_on_right(bench_row)` had ballooned the shell. Restructured (see the layout lesson); room
  dropped 14×10 → 11×5 and the benches lined up down the centre.
- **"rescale towels by 0.6"** → applied `modulate_scale=0.7` on the towel assets (they read a touch
  chunky on the cubbies).
- **"rescale room by 0.9"** held through Ph1–2 (render wins early; occupancy rises with detail),
  applied via `RoomGroup(modulate_scale=0.9)` in the final phase.

## Manual constraints used
- None required; auto overlap/bounds + wall-flush placements sufficed.
