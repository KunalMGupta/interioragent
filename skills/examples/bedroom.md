# Bedroom (traditional master suite) — worked example

Scene: `scenes/work/bedroom.py` (seed=41), planner-driven "Warm Traditional Master Suite". The
core **residential** pattern: one symmetric **hero (the bed)** on the main wall, a small
reading-nook sub-group off to the side, storage on a side wall. Built coarse-to-fine and iterated
on VLM feedback.

## Layout pattern — symmetric hero + a self-contained nook
- **Bed hero** on `place_on_back_wall_center`, built as a `RelativeGroup`: nightstands aligned to
  the headboard via `place_on_back_left` / `place_on_back_right`; a storage bench tucked at the
  foot with `place_on_front_adjacent` (close); the reading nook pushed out off the right side with
  `place_on_right_further`; a grounding `place_rug` and one `add_lighting(..., density=0)` fixture.
- **Reading nook** is its OWN `RelativeGroup` (chair anchor + `place_on_left` side table +
  `place_on_back` floor lamp) so the chair, its table and its lamp travel and rotate as one unit —
  then `bed_group.place_on_right_further(chair_group)` drops the whole nook beside the bed and
  `bed_group.face(chair_group, toward=bench)` angles it inward. `face()` works on a nested **group**,
  not just a leaf.
- **Dresser** on the left wall (`place_on_left_wall_center`) as its own styled group (lamp + vase on
  top), with a mirror mounted above it (`place_on_wall_left_center`).

## Lessons this scene encodes

### 1. Beds are "set assets" — the mesh comes fully dressed
Pin a good traditional bed and **do not** add separate bedding/pillows — the asset already carries
them, and `place_on_top` bedding fights the mesh. Same family as vanities/toilets/kitchen sets
(see the set-assets note). Beds also carry real-world scale, so no height override is needed.

### 2. Build ONE symmetric unit, then duplicate with `2 * unit`
The matching nightstand+lamp pair is built once as a `RelativeGroup` (`ns.place_on_top(lamp)`) then
duplicated: `ns_l, ns_r = 2 * ns`. Building the two individually runs `place_on_top`'s VLM sizing
tournament **twice**, so the two lamps come out **different sizes**. One unit → one tournament →
identical pair. (This is the general "build a repeated unit once and copy it" principle.)

### 3. Wall art: pre-scale it BEFORE `place_on_wall_*` or it punches through the ceiling
`place_on_wall_*` derives the mount height from the art's **un-scaled** height, so a large painting
is mounted too high and clips the ceiling. Fix: `scale_only_width/height/depth` the art down to a
moderate size *before* placing it (`art.scale_only_height(0.75)` etc.). Generalizable — see the
`wall-art-mount-height` memory.

### 4. A seat always gets a table + its own light, kept in the seat's group
The reading chair carries a small side table and a floor lamp *in its group* — the lamp is not left
stranded in a corner. Standard design-principles composition.

### 5. Pin lamps/art for style
The generic "table lamp" query kept returning modern white lamps; pinning a classic urn-base lamp
id (`_LAMP`) gets the traditional look. Likewise pin a clean landscape id (the retrieved art was a
bad mesh).

Palette/room: warm oak floor, greige walls, `modulate_scale=0.8` to keep the suite cozy (a bedroom
should read intimate, not cavernous); standard window with floor-length linen curtains.
