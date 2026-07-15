---
id: example:gym
kind: example
family: zoned-multi-zone
category: "gym (3 sizes)"
pattern: "Large perimeter multi-zone — zone first, cardio faces the view, mirror wall"
---
> **Digest (from the pattern index):** **Large perimeter multi-zone** — zone first, cardio faces the view, mirror wall


# Gym — worked example (zone-first, view-facing cardio, mirrored wall)

Status: built as `scenes/work/gym_mega.py`. [`gym_v1.py`](gym_v1.py) is that program **phase-gated** (2026-07-13): `lint_program`-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record) — fully clean; the 0.60 m reception desk eyeballed and reads as the deliberate low check-in counter.

Three gyms of increasing scale live in `scenes/work/`: `gym.py` (boutique studio), `gym_large.py`
(one of each zone), `gym_mega.py` (a Planet-Fitness-scale club). The mega scene is the reference.

## The core lesson: for a big scene, plan ZONES first, then fill them
A large gym is a set of **functional zones** (cardio, free weights, machines, functional/turf,
spin, reception, amenities). Decide *where each zone goes* before placing a single asset — assign
zones to the room's regions (the 3×3 floor grid + the four walls), then drop each zone's equipment
into its region. Scattering machines one-by-one gives an incoherent floor. Interior zones that are
whole rows/grids of machines use `GridGroup.place_grid(units, cols=N)` placed on a floor position
(`place_on_back_left`, `place_on_right`, …), not just perimeter `place_on_*_wall_*` calls.

## Cardio faces the view
People want something to look at while they train, so the **cardio run lines the glass wall facing
out**. Treadmills go nearest the glass (best view while running); ellipticals in the row behind.
Practical detail: in a 2-row `place_grid`, the **second** grid row lands against the wall, so list
the back-row asset first (`8*elliptical + 8*treadmill` puts treadmills on the glass).

## Full-wall floor-to-ceiling mirror (a real reflection)
`room.place_mirror_full_wall("left_wall")` covers a whole wall with one reflective surface — a true
Cycles mirror (`IDSDL/mirror.py` builds a thin panel with a metallic / ~0 roughness PBR material;
it does NOT cut the wall). This is different from a retrieved "gym wall mirror" prop. Do NOT tile
mirror props with `place_on_wall_freeform` on a left/right wall: that path sizes flat objects to
their **depth**, collapsing a ~5 cm-thick mirror to nothing.

## Dynamic room height for tall equipment
Room HEIGHT is normally clamped to 3.0 m. Tall racks/machines (and wall decor above them, like a
clock over a locker bank) then clip the ceiling. Pass `RoomGroup(max_height=4.0)` — HEIGHT grows
with the tallest floor object, clamped to `[3.0, max_height]`. Default 3.0 leaves every other scene
identical. A compile-time `_warn_over_height` check now flags any object whose top still pokes
through the ceiling (surfaced in `scene.vlm_feedback`).

## Clearances are per-OBJECT (leaf), not per-group
`room.add_clearance(obj, distance, dir)` keeps space around `obj`. **Pass a placed leaf object, not
a group wrapper** — the raytracer keys on `get_children()` (flattened leaves), so passing a
`GridGroup`/`RelativeGroup` throws `KeyError`. To clear a whole row/grid, loop its units:
`for m in row_units: room.add_clearance(m, 0.5, dir=...)` — front_back on every treadmill/elliptical
gives the glass-side aisle, the between-rows aisle, and the behind aisle. `dir` options:
`front` (facing dir) · `sides` (the two perpendicular sides) · `all` (front+back+sides) ·
`front_back` (aisles ahead/behind a row) · `front_sides` (front+left+right, e.g. a machine or a
reception desk). Reception clearance goes on the **desk** leaf, not the reception group.

## Reception desk: along the wall, facing INTO the room
Back the desk against a wall but face it into the room (`place_on_front_left(reception,
facing="back")` with the staff chair `place_on_back` of the desk, tucked toward the wall). A desk
facing the wall reads as broken. The VLM may suggest "rotate the desk 180" — that would face it at
the wall; override it, this orientation is correct.

## Bare floor-to-ceiling glass
`place_window_floor_to_ceiling(wall)` with no `curtain=` is now bare glass (the curtain bug that
also affected the picture window is fixed in `IDSDL/window.py`). Cardio against bare glass reads far
better than curtains hiding the view.

## Prop scaling: pin the real height for small props
`AddAsset` derives scale from the **description text**, so a pinned small prop (bin, water cooler,
foam roller, potted plant) can still come out wrong-sized under an unlucky phrasing (a cooler
rendered ~2.4 m once). Pin the real size with a `_fit_height(obj, target_h)` helper (uniform scale
to a target height) — see `scenes/work/gym_mega.py`.

## Asset coverage (the `gym_equipment` pool is deep)
GOOD: treadmill, upright bike, elliptical, dumbbell rack/tree, flat/incline bench, power/squat rack
(+ barbell), plate tree, barbell+plates, lat pulldown, pec/chest & ab-crunch machines, cable tower,
plyo box, kettlebell, medicine ball, stability ball, sandbag, punching bag, lockers, water cooler,
massage chair, reception desk, trash can. GAPS (use stand-ins): rowing ergometer, leg press, Smith
machine, battle rope (→ sandbag), branded/neon signage (weak).

## Status
`scenes/work/gym{,_large,_mega}.py` — built & VLM-clean. Not yet promoted to `scenes/gym.py`.

## Program

[`gym_v1.py`](gym_v1.py) — phase 1 all zones (cardio row, machine bank, spin grid, functional corner, reception, massage lounge, amenities), walls and door; phase 2 the turf props + turf rug and the reception plant; phase 3 the full-wall mirror, floor-to-ceiling glazing, brand art, clock and linear lights.

`workbench run skills/examples/gym_v1.py --phase 1` builds the layout alone in ~1–2 min.
