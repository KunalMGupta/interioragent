# Worked example: a game room / rec lounge (`scenes/work/game_room.py`)

Status: built as `scenes/work/game_room.py`. [`game_room_v1.py`](game_room_v1.py) is that program
**phase-gated and verified 2026-07-13**: phase-1 pass, and a FULL rebuild the same day came back
**fully clean** (`no rescale / no rotation / no wall overlap`). Three findings from that rebuild
(this example's "no VLM history" hole is now closed):
- **The floor-to-ceiling window renders as bright glazing post-void-fix** (greenhouse fixed the
  renderer 2026-07-12) — the old black-void caveat for this scene is retired.
- **The historic rotation-storm mystery has a root cause: the FRONT camera is blinded by the
  entry door.** The design centres the door on the front wall ("walk in at the hero"), and the
  interior camera at that wall's centre sits inside the door mesh — its whole view renders as
  dark wood planks, and a garbage view corrupts every constraint judged from it
  (laundry_room's law). This rebuild stayed clean anyway; if a vote storm ever recurs here,
  move the door off-centre (lobby's fix for its TV) before touching any furniture.
- **The dartboard cabinet warns as 0.44 m-deep wall furniture** (its doors stand open — the
  museum mask class) but renders correctly on the wall. Shipped as a judgment call: it is the
  category's identity piece; the warning is understood, not ignored.

A moody home game room built entirely by **composition** — no new DSL, no asset ingestion. The
`GameEquipmentRetriever` pool is deep enough to cover every game piece off the shelf.

## Zone map (hero-in-the-middle, zones ringed around it)
A rec room is the same "plan the zones first, then fill them" problem as the gym, but with a single
social **hero at the centre** instead of perimeter rows:

- **CENTRE** = billiards: 8-ft pool table on a bordered area rug, one billiards pendant overhead.
- **BACK wall** = bar social hub: counter + back-bar bottle cabinet + a stool row; gallery photos
  and a colourful painting above.
- **BACK-RIGHT corner** = arcade cabinets.
- **LEFT wall** = media/lounge: wall TV over a low console; leather sofa flanked by two velvet
  armchairs angled into a coffee-table cluster.
- **RIGHT wall** = window; foosball in front of it (players get the view — the gym "cardio faces
  the view" rule generalises).
- **FRONT-LEFT** = poker table + four chairs. **FRONT wall** = door (centre), trophy cabinet,
  wall dartboard.

## Lessons this scene encodes

### 1. The hero's clearance sizes the room
The pool table gets `add_clearance(pool_table, 1.3, dir="all")` — enough to draw a cue on every
side. That single all-round clearance is what actually drives the room's footprint; the other zones
settle into the space it reserves. Put the hero + its clearance down first and let the ring fill in.

### 2. `add_lighting` footprint is set by the group, so keep the group compact
Pendant lighting over a group scatters if the group's bounding box is big. First pass placed the 3
bar stools with `place_on_front_left / _front / _front_right` (spread in BOTH x and z) and used
`density=0.25` → ~15 globes strung in a line across the whole back of the room. Fix: a compact
**straight** stool row via `AroundGroup.place_rectilinear(longer_side1=stools)` + `density≈0.18` →
a tight cluster of ~5 globes directly over the counter. (Same pattern as the cocktail lounge.)
Rule of thumb: for a pendant *cluster* over one piece, keep that piece's group tight and density low
(~0.15–0.2); `density=0` gives exactly one fixture (used for the billiards pendant).

### 3. `face(child, toward=target)` angles flanking seats into a cluster
Chairs placed with `place_on_left/right/front/back` inherit the anchor's rotation and face outward.
To seat them *at* something — armchairs toward the coffee table, poker chairs toward the poker
table — call `group.face(chair, toward=table)` inside the group. Loop it for a whole set:
`for ch in poker_chairs: poker.face(ch, toward=poker_table)`.

### 4. Back-bar behind the counter as one rigid station
`RelativeGroup.set_anchor(bar_line); place_on_back(back_bar_cabinet)` bakes a fixed service aisle
between the bottle cabinet (against the wall) and the counter — more reliable than a clearance
constraint fighting the stool overlap.

### 5. VLM orientation notes are noisy — verify, then override
The VLM flip-flopped between "rotate the armchairs" and "rotate the poker chairs" across renders and
repeated "rotate bottom chair" four identical times, even though `face()` had already angled them
correctly (confirmed in the render). Treat repeated/contradictory rotation notes as noise once the
image shows the seats are right.

## Asset coverage (all off-the-shelf)
`GameEquipmentRetriever` covers: pool table (green felt, incl. a purpose-built billiards pendant
light in the same pool), foosball, upright arcade cabinet, air hockey, wall dartboard cabinet,
poker table. Furniture from the usual retrievers: bar counter (+ back-bar bottle cabinet), wooden
bar stools, leather sofa, green-velvet armchairs, slim wall TV, low media console, dark-wood glass
display cabinet (trophies). **Only gap:** a dedicated wall cue rack (no visual match) — skipped.

Palette: hunter-green walls, dark stone-tile floor, walnut/charcoal/brass.

## Program

[`game_room_v1.py`](game_room_v1.py) — phase 1 every floor anchor (the pool hero and its clearance, bar line, arcade, foosball, poker), walls and door; phase 2 the billiards rug; phase 3 the billiards fixture, bar pendants and ambient fill, the photo grid, painting, wall TV, dartboard and the floor-to-ceiling window.

`workbench run skills/examples/game_room_v1.py --phase 1` builds the layout alone in ~1–2 min.
