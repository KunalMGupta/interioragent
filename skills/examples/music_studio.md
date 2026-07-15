---
id: example:music_studio
kind: example
family: zoned-multi-zone
category: "recording studio"
pattern: "Two zones on the centerline"
---
> **Digest (from the pattern index):** **Two zones on the centerline** — a control-zone hero unit (mixer + flanking `face()`-angled monitors + sweet-spot chair, one rug) faces a live zone (drums + mic stands) down the room axis; guitar `GridGroup` line on a side wall; acoustic panels massed via `place_on_wall_freeform`; teaches gap-category hero pinning (mixer-on-stand over the picker's DJ table), the desirable SET (guitar+amp), stock-the-rack, and "red accent via textiles when the wall texture won't cooperate"


# Music recording studio — worked example (control zone + live zone, guided 9-gate flow)

Status: **built & VLM-clean** (`scenes/work/music_studio.py`, seed=42, converged in 2 full renders +
2 phase builds). Final compile: `no rescale` oscillating to a declined `1.1`, `no rotation`,
`no wall overlap`, no `[Lint]`/WARNING lines. Program copy beside this file: `music_studio_v1.py`.

## Prompt this covers
- "a music / recording studio: mixing console, studio monitors, instruments (guitars, keyboard,
  drum kit), acoustic panels, mic stands, warm moody lighting", "a control room", "a band room /
  rehearsal space" (drop the console for the last).

## Plan summary (from the planner)
"Moody Pro Studio: Central Console Anchor with Acoustic Architecture" — a dominant central mixing
console as the hub, wall racks as a gear spine, a grid of black acoustic panels on a red back wall,
warm wood + dark palette with red accent, a big grounding rug, drum kit at the back, guitars lining
a side wall, warm low-glare lighting.

## The layout idea: TWO ZONES on the room's centerline
A studio is a **control zone** (console hero) facing a **live zone** (instrument cluster) down the
center axis — the meeting_room "operator faces the focal wall" idea with the executive_office
zoned-single-room split:
- **FRONT/CENTER = control**: the mixer-on-stand hero flanked by two nearfield monitors on stands,
  the engineer's chair at the sweet spot behind it (chair faces mixer/front wall), all on ONE
  oriental rug (`RelativeGroup`, placed `room.place_on_front(console, facing="back")`).
- **BACK = live**: drum kit sub-hero on its own dark rug + two mic stands (`RelativeGroup`,
  `facing="front"` so the kit plays toward the console).
- **LEFT** = keyboard station (`facing="right"`); **RIGHT wall** = the guitar line (a `GridGroup`
  row: guitar-on-stand, guitar+amp SET, guitar-on-stand).
- **FRONT wall** = stocked gear rack (left) + entry door (right).
- **Walls (phase 3)** = the acoustic architecture: 3 black geometric panels massed via
  `place_on_wall_freeform("back_wall", [...])`, an upholstered grid panel at EACH side wall's
  first-reflection point; a small standard window with dark curtains; one framed concert print.

## Asset audit (gate 3) — what the dataset has and hasn't
- **No mixing-console DESK exists.** The best mesh is a **professional mixer on a black stand**
  (`hssd/6990fec2…`, inspect candidate #1) — the picker chose a white DJ table (#2) that clashes
  with a dark studio; overrode by pin. Same move as garage's pinned car: for a gap-category hero,
  pin the id.
- **Real wins**: full classic drum kit (`hssd/eca42afb…`), mic-on-stand (`hssd/7b2ed578…`),
  monitor speaker on a stand at ear height (`hssd/5f1030c8…`), digital keyboard on stand
  (`hssd/f51e066d…`), electric guitar on a floor stand (`future/b4c95c67…`).
- **The guitar+amp SET is desirable here** (`future/0f058977…`) — the amp only exists bundled, so
  the set covers the amplifier need (inverse of the cafe-SET trap).
- **No acoustic foam / no 19" rack**: upholstered grid panel (`future/540e8add…`) + black geometric
  panel (`future/2ab78653…`) read as treatment (both thin, wall-hang safe); a tall black shelf
  cabinet (`future/9f6fd95f…`) stands in for the rack — STOCK it (stereo system `future/4c6888e5…`
  via `place_inside`) or it reads as bare furniture.

## What worked / gotchas
- **The console unit is one RelativeGroup**: monitors `place_on_left/right`, chair
  `place_on_front`, then `face(chair, toward=mixer)` + `face(mon_l/r, toward=chair)` — the
  monitors angle in at the listener (the "equilateral triangle" read) with zero VLM rotation
  churn. Correct-by-construction beats chasing RotationConstraint.
- **`room.place_on_front(console, facing="back")`** points the mixer's control face into the room,
  which puts the chair between console and room center facing the front wall — the classic
  engineer pose fell out of one facing value.
- **Warm moody lighting = three restrained layers**: flush fixture at **density 0.01** (0.02
  tripped the starfield lint at 12 fixtures on 38 m²), dark curtains over a small standard window,
  and a warm brass floor lamp in the back corner as the decorative warm accent.
- **The red accent survives via textiles, not paint**: the wall texture
  ("dark charcoal grey with one deep red accent wall") resolved to plain dark grey — the red
  arrived through the Persian rugs instead, which reads better anyway. Don't fight a texture
  embedding for an accent a prop can carry.

## VLM feedback we hit and how we resolved it
- **Room size: hold early, one decisive change, accept the oscillation.** `0.85` (Ph1) → `0.8`
  (Ph2) — held per render-wins-early; applied `modulate_scale=0.85` in the final phase → the next
  full render voted `1.1` (slight enlarge). A flip across neutral after acting = converged;
  declined (casino's 1.05 lesson).
- **Lighting starfield lint at density 0.02.** 12 fixtures on a 38 m² room (budget ~11) — the
  0.01–0.02 "small room" band is not flat: 38 m² already needs the bottom of it. `0.01` → clean.
- **Everything else was clean by construction** — `no rotation` / `no wall overlap` every single
  build (facing defaults omitted on wall furniture, panels in distinct wall slots, freeform for
  the massed back-wall grid).

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed; the two-zone axis has natural circulation.
