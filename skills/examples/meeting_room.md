# Meeting / conference room — worked example

Status: **built & essentially VLM-clean** (`scenes/work/meeting_room.py`, seed=17, 3 render passes).
Final compile: `no rescale`, `no room-rescale`, `no wall overlap`, no overlap warning; only the noisy
`RotationConstraint` on two tiny on-top props remained (declined). Built asset-first (retrieval stress
test) then coarse-to-fine.

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

## Working skeleton (coarse-to-fine)
```python
scene = SceneProgRoom("MeetingRoom", seed=17)
TABLE="hssd/aee7c3b…"; CHAIR="hssd/430315716…"; WALL_TV="hssd/576f0a57…"; WHITEBOARD="hssd/1b37271d…"
SIDEBOARD="hssd/70d4947…"; COFFEE="hssd/85ba1568…"; WATER="hssd/b77968f3…"; TALL_PLANT="future/feeb8797…"
scene.prefetch_assets([ ...all descriptions... ])

# CENTER: table + a rectilinear ring of chairs (4 per long side, 1 each end) + styling + ONE pendant + rug
with scene.AroundGroup(sparsity=0.15, jitter=0.35) as boardroom:
    boardroom.set_anchor(scene.AddAsset("a long rectangular boardroom conference table", asset_id=TABLE, width=3.2))
    long1 = 4 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    long2 = 4 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    ends  = 2 * scene.AddAsset("a white leather conference chair with armrests", asset_id=CHAIR)
    boardroom.place_rectilinear(longer_side1=long1, longer_side2=long2, shorter_side1=[ends[0]], shorter_side2=[ends[1]])
    boardroom.place_on_top([scene.AddAsset("a low floral centerpiece in a vase"),
                            scene.AddAsset("a black conference desk phone", asset_id=PHONE),
                            scene.AddAsset("an open silver laptop computer", asset_id=LAPTOP),
                            scene.AddAsset("a stack of notepads with pens")])
    boardroom.add_lighting("a long linear LED ceiling pendant light", density=0)   # ONE — density>0 STARFIELDS the wiry mesh
    boardroom.place_rug("a large grey commercial area rug", size=0.9)

# BACK service station: sideboard + coffee machine + carafe on top (scale the props down)
with scene.RelativeGroup() as coffee_station:
    coffee_station.set_anchor(scene.AddAsset("a low dark wood office sideboard credenza", asset_id=SIDEBOARD, width=1.6))
    coffee_station.place_on_top([scene.AddAsset("a stainless steel office coffee machine", asset_id=COFFEE, modulate_scale=0.5),
                                 scene.AddAsset("a glass water carafe with drinking glasses", modulate_scale=0.5)])

tv = scene.AddAsset("a large wall-mounted flat screen display", asset_id=WALL_TV, modulate_scale=1.6)   # pre-scale BEFORE wall
av_credenza = scene.AddAsset("a low dark wood office AV credenza cabinet", asset_id=SIDEBOARD, width=1.8)

with scene.RoomGroup(modulate_scale=1.05, randomness=0.2, max_height=3.2) as room:
    room.place_walls(floor_texture="grey commercial carpet tile", ceiling_texture="white acoustic panel ceiling",
                     wall_texture="soft warm grey with one charcoal accent wall")
    room.place_on_center(boardroom, facing="front")
    room.place_on_front_wall_center(av_credenza, facing="front")   # reversed-front sideboard -> flip (see gotcha)
    room.place_on_wall_front_center(tv)
    room.place_on_wall_front_right(scene.AddAsset("a white dry-erase whiteboard", asset_id=WHITEBOARD))
    room.place_on_back_wall_center(coffee_station, facing="back")   # reversed-front sideboard -> flip
    room.place_on_back_left_corner(scene.AddAsset("a white office water cooler dispenser", asset_id=WATER), facing="front")
    room.place_on_back_right_corner(scene.AddAsset("a tall potted indoor office plant", asset_id=TALL_PLANT, width=0.8), facing="front")
    room.place_window_floor_to_ceiling("left_wall", curtain="light grey roller blinds")
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract print", asset_id=ABSTRACT))
    room.place_door("right_wall", position="right")
    # no room-wide ceiling fixtures: the table's pendant + the glass daylight are enough (panels starfielded + blew out)
```

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
