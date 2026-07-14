# Meeting / conference room — worked example

Status: **built & essentially VLM-clean** (`scenes/work/meeting_room.py`, seed=17, 3 render passes).
Final compile: `no rescale`, `no room-rescale`, `no wall overlap`, no overlap warning; only the noisy
`RotationConstraint` on two tiny on-top props remained (declined). Built asset-first (retrieval stress
test) then coarse-to-fine.
Built as `scenes/work/meeting_room.py`; [`meeting_room_v1.py`](meeting_room_v1.py) is that program
**phase-gated** (2026-07-13) — same layout, same pinned ids, same seed. It is **`lint_program`-clean**, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record) — fully clean: `no rescale / no rotation / no wall overlap`.

## Prompt this covers
- "a professional corporate meeting / conference / board room: a long central table ringed with office
  chairs, a presentation wall (wall display + whiteboard), a credenza/AV cabinet, a coffee & water
  station, tabletop items, greenery, framed art, glass + blinds, neutral modern palette."

## Plan summary (from the planner)
"Integrated Executive Boardroom": a long central table is the activity hub; the presentation wall (large
monitor + whiteboard over a slim AV credenza) is the visual anchor; a coffee/water station + speakerphone
within reach; glass perimeter with blinds for daylight; recessed/linear ceiling light. Palette: white
seating, charcoal surfaces, warm wood, brushed metal.

## The layout idea: the dining/conference cluster, refocused on a PRESENTATION wall
A boardroom is the dining pattern (a central table ringed by chairs) with one wall promoted to a
*presentation anchor*, and the room's four walls each given a job:
- **CENTER = the table hub** — a long table + a rectilinear ring of chairs (`AroundGroup.place_rectilinear`,
  4 per long side + 1 each end), jittered, on a grounding rug, lit by ONE linear pendant.
- **FRONT wall = presentation anchor** — a slim AV credenza on the floor, a large display hung ABOVE it,
  a whiteboard beside it.
- **BACK wall = service zone** — a coffee sideboard (coffee machine + carafe on top), a water cooler and
  greenery in the corners.
- **LEFT wall = daylight glass** (`place_window_floor_to_ceiling` + blinds); **RIGHT wall = art + door.**

## Step 0 — the retrieval STRESS TEST
39/40 wishlist items resolved, **none < 0.30** → low-risk, **no ingest**. The audit's value was in the
route-arounds it surfaced (read the `desc`, not just the score): "conference speakerphone" returned a
whole TABLE → use the desk phone as the conference phone; "flip chart" → a whiteboard (skip); "water
pitcher with glasses" → a wine bottle (use the floral centerpiece); "oval/round conference table" →
a coffee table / a cafe-SET (skip; use the rectangular). One hard ERR ("coffee service cart") → compose
the station from the coffee machine on a sideboard. Then **measure the heroes** (`AddAsset(asset_id=…)`
+ `get_whd()`, no network): table 2.0×0.87 → stretch to `width=3.2`; chair 0.6 wide; wall TV only
1.2 m → `modulate_scale=1.6` for a ~1.9 m display; whiteboard 1.8 m.

## Program

[`meeting_room_v1.py`](meeting_room_v1.py) — phase 1 the floor anchors (the table hub with its
rectilinear chair ring, the AV credenza, the coffee station, the water cooler, the walls and the
door), phase 2 the surface dressing (the tabletop styling, the coffee machine + carafe, the rug, the
corner plant), phase 3 the wall decor (display, whiteboard, framed print), the floor-to-ceiling glass
and the table's linear pendant.

`workbench run skills/examples/meeting_room_v1.py --phase 1` builds the layout alone in ~1–2 min.

## What worked / gotchas
- **Stretch the table into a boardroom table with `width=`** (not uniform scale): the meeting-table mesh
  is 2.0 m; `width=3.2` lengthens only the top, keeps a realistic ~0.7 m height (same lesson as the bar
  counter). Then a rectilinear ring (4+4+1+1) seats 10.
- **`place_rectilinear` gives a straight, uniform chair facing** — leave the facing default; the ring
  reads correctly without per-chair `face()`.
- **Pre-scale the wall display BEFORE `place_on_wall_*`** — the TV mesh is only 1.2 m; `modulate_scale=1.6`
  (uniform, keeps aspect) makes a ~1.9 m presentation display. (Wall-art-mount-height lesson.)

## VLM feedback we hit and how we resolved it (the 3 passes)
- **Lighting starfield + blowout (pass 1→2).** A room-wide `add_lighting("flush panel", density=0.3)`
  multiplied into a chaotic ceiling strip of fixtures AND over-lit the room — worsened by the
  floor-to-ceiling glass flooding daylight. **Fix: drop the room panels; light ONLY the table with a
  linear pendant at `density=0`.** `density>0` copies the (wiry) pendant mesh N times across the group
  footprint → a mess; `density=0` = one clean fixture. The glass supplies the ambient. (Extends
  [[lighting-footprint]] / [[ceiling-light-fixture]]: a boardroom rarely needs `add_lighting` panels at
  all — one table pendant + daylight reads best and avoids the starfield.)
- **Reversed-front sideboard (pass 1→2).** The pinned sideboard's finished doors sit on its REVERSED
  face, so the default wall-facing pointed its open legs at the room (VLM: "rotate credenza/coffee 180").
  **Fix: flip each per wall** — `facing="front"` on the front wall, `facing="back"` on the back wall.
  This is the deliberate exception to "don't pass the wall's own name as `facing`" (constraints.md): the
  default is right for a normal mesh, wrong for a reversed one — override only that asset. (A durable
  alternative is the front-cache, but this sideboard is used elsewhere, so a per-scene flip is safer.)
- **Oversized on-top props (pass 2→3).** Coffee machine + carafe landed ~2× too big on the credenza
  (`place_on_top` sized them to the wide sideboard) → `modulate_scale=0.5` on each.
- **Persistent "rotate coffee machine/carafe to face center"** — declined as noise (RotationConstraint
  on tiny on-top props; their facing is invisible). Render is the arbiter.

## Asset gaps (LOW risk — the office/AV pool covers this well)
No ingest. Genuine gaps, all with substitutes: no true conference SPEAKERPHONE (use the desk phone); no
flip chart (use the whiteboard); "water pitcher with glasses" mis-retrieves (use the floral centerpiece).
Everything structural (table, conference chair, wall TV, whiteboard, credenza, coffee machine, water
cooler, plant, art) is a clean dataset hit.

## Manual constraints used
- None. The door auto-clearance keeps the entrance clear; the chair ring is geometric.
