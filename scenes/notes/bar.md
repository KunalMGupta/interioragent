# Bar

- **Status:** BUILT & essentially VLM-clean — `scenes/work/bar_lounge.py` (seed=26). Full worked
  recipe in `skills/examples/bar.md`.
- **Pattern:** WIDE+SHALLOW room; bar LINE (back-bar cabinet + counter + stool row) on the long back
  wall; two velvet lounge nooks (`place_circle(2)` 2-tops, built once + `2*nook`) fill the front; short
  walls light (mirror / framed print); door front-center between the nooks.
- **Hero assets (pinned):** counter `future/dd75f4ed`, tufted stool `future/84e8c226`, back-bar
  `future/f92b65d2`. Lengthen counter with `width=3.6` (NOT uniform scale). Back-bar already displays
  glassware → no bottle `place_on_top` needed.
- **Lighting gotcha:** query a SINGULAR pendant + low density (0.2). A plural/"row of" query returns a
  pre-clustered mesh → `add_lighting` copies it into a ~30-globe cloud. See vlm_feedback.md.
- **Jitter/randomness:** Around jitter 0.25 (stools) / 0.4 (nooks); RoomGroup randomness 0.15,
  modulate_scale 0.85 (final-phase shrink).
- **Asset-gap risk:** LOW (resolved) — dataset covers bar counters/stools/back-bar/velvet chairs well.
