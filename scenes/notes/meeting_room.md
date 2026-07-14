# Meeting Room

- **Status:** BUILT & essentially VLM-clean — `scenes/work/meeting_room.py` (seed=17). Full worked
  recipe in `skills/examples/meeting_room.md`. (Supersedes the thin pre-workflow `scenes/meeting_room.py`.)
- **Plan:** planner headline "Integrated Executive Boardroom" — a central table hub, a dark presentation
  wall as the visual anchor, a glass perimeter with blinds, a coffee/water station, neutral palette
  (white seating + charcoal + warm wood).
- **Pattern:** the dining/conference cluster refocused on a PRESENTATION wall. CENTER = a long
  conference table + a rectilinear ring of chairs (4 per long side + 1 each end = 10), `AroundGroup`,
  jittered, on a grounding rug, with ONE linear pendant. FRONT wall = the presentation anchor (a large
  wall display hung above a slim AV credenza + a whiteboard beside it). BACK wall = the service zone
  (a coffee sideboard with coffee machine + carafe on top, a water cooler + greenery in the corners).
  LEFT wall = floor-to-ceiling glass + blinds (daylight). RIGHT wall = framed art + the door.
- **Stress test FIRST:** 39/40 resolved, **none < 0.30** → low-risk, **no ingest**. 1 ERR ("coffee
  service cart" → composed from the coffee machine + sideboard). Weak/route-arounds: speakerphone
  returned a whole table (used the desk phone as the conference phone); flip-chart → whiteboard (skip);
  water pitcher → wine (used the floral centerpiece); oval/round tables → coffee-table/cafe-SET (skip,
  used the rectangular). Measured heroes via `get_whd()`: table 2.0×0.87 (stretched to width=3.2),
  chair 0.6 wide, wall TV 1.2 wide (modulate_scale 1.6 → ~1.9 m display), whiteboard 1.8 wide.
- **Heroes (pinned):** table `hssd/aee7c3b…`, white-leather conference chair `hssd/430315716…`, wall TV
  `hssd/576f0a57…`, whiteboard `hssd/1b37271d…`, sideboard (AV credenza + coffee station) `hssd/70d4947…`,
  coffee machine `hssd/85ba1568…`, water cooler `hssd/b77968f3…`, tall plant `future/feeb8797…`,
  abstract `hssd/5e9d4d4d…`, desk phone `hssd/b81bee4e…`, laptop `hssd/57d2b6c1…`.
- **Fixes over 3 passes (reusable):**
  1. **Lighting starfield + blowout** — a room-wide `add_lighting("flush panel", density=0.3)` multiplied
     into a chaotic ceiling strip AND over-lit the room (compounded by the floor-to-ceiling glass
     flooding daylight). Fix = ONLY the table's linear pendant at **density=0** (density>0 multiplies the
     wiry pendant mesh); the glass supplies ambient. Reinforces [[lighting-footprint]] / [[ceiling-light-fixture]].
  2. **Reversed-front sideboard** — this sideboard mesh's finished doors are on its REVERSED face, so the
     default wall-facing showed its open legs (VLM: "rotate credenza/coffee 180"). Fix = flip per wall:
     `facing="front"` on the front wall, `facing="back"` on the back wall (the deliberate override of the
     "don't pass the wall's own name" default).
  3. **Oversized on-top props** — coffee machine + carafe came out ~2× big on the credenza →
     `modulate_scale=0.5`.
- **Rotation noise:** the VLM flags "rotate coffee machine/carafe to face center" (tiny props on the
  sideboard) — declined as the usual weak-smoke-alarm RotationConstraint.
- **Scale/jitter:** RoomGroup modulate_scale 1.05 (VLM asked +1.1 from 0.95; converged clean),
  randomness 0.2, max_height 3.2; AroundGroup jitter 0.35.
