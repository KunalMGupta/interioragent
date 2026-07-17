# VLM-guided placement & relative sizing for 3D scene synthesis

*Context notes from InteriorAgent (interior-scene generation: retrieval-based asset
pipeline + IDSDL scene DSL + Blender). Written for other agents building
VLM-in-the-loop spatial pipelines (set dressing, prop scaling, shot judging — the
mechanics transfer directly).*

## The problem

Scene synthesis from retrieved 3D assets fails in two recurring ways that no amount
of prompt engineering on a single VLM call fixes:

1. **Placement** — where exactly small objects sit on/inside a support (a lamp on a
   nightstand, dishes inside a cabinet). Captions and AABB heuristics put things on
   the wrong shelf, sunk into bodies, or hanging off edges.
2. **Relative scale** — retrieved assets come with unreliable metadata sizes, so a
   nightstand rivals the bed, a lamp is a monster, a bar cart is toy-sized. One VLM
   "guess the right size" call is not reliable enough to fix this.

Both are solved with the same core move: **generate candidates, render them, and let
a VLM pick winners in a pairwise tournament — while a proposal distribution updates
from the outcomes.** Where the two problems differ is where that distribution lives.

## 1. Placement: explicit PDF over discrete tiles (`tools/planar_regions.py`)

The search space is discrete, so the PDF is an explicit value vector:

- Detect planar support regions of the base mesh; grid them into tiles. Each tile
  holds a value (initially 1.0) — this is the PDF.
- Per generation: sample K candidate arrangements ∝ tile values, render each,
  run a single-elimination pairwise VLM tournament (judge criteria: visibility,
  on-the-right-surface).
- Credit assignment: losers' tiles decay (×0.6), winners' tiles boost (×1/0.6);
  tiles shared by both sides cancel, so only *distinguishing* tiles move.
- After N generations, place greedily on the highest-value tiles.

Wired into the DSL as the primary path for `place_on_top` / `place_inside`
(`IDSDL/vlm_placement.py`), with a deterministic AABB fallback on any failure.

## 2. Relative scale: the PDF lives inside the proposer VLM (`tools/scale_solver.py`)

Scale is continuous and semantically coupled — the fix for "nightstand towers over
the bed" is to shrink the nightstand, not grow the bed, and a render alone doesn't
tell you which. There is no natural tile vector. Instead:

- **Parameterization**: per member, a uniform factor `s` plus a height-only factor
  `h` (mesh scale `[s, s·h, s]`), always relative to the *original* size so numbers
  stay comparable across rounds. The ensemble anchor moves within tight bounds
  (±15%); satellites within wide ones. Symmetric duplicates share one entry.
- **Proposer** (strong VLM): sees the member table (descriptions + exact dims in
  meters + bounds), the champion render, and the FULL transcript of every pairwise
  verdict so far (both sides' factor vectors + the judge's directional feedback).
  It emits K−1 challenger scale vectors with rationales. The transcript *is* the
  posterior — early rounds explore diverse hypotheses, later rounds refine around
  what the judge rewarded.
- **Candidates**: built by a layout function that recomputes contacts from the
  scaled AABBs (things stay flush/stacked at any scale), rendered as textured 3/4
  views from the top corner of the bounding cube, tightly framed.
- **Critic**: single-elimination pairwise tournament; the reigning champion always
  competes (elitism → monotone improvement). EVERY match — not just the final —
  emits (factors_A, factors_B, winner, feedback) into the transcript, so one round
  of K candidates yields K−1 labeled comparisons of training signal.
- **Stopping**: if the champion survives unbeaten and most matches were too close
  to call (see order-swap below), stop — further rounds only add noise drift.

Everything is auditable: the transcript is saved as `match_log.json`.

## Hard-won lessons (the expensive ones)

1. **The judge model gates everything.** Our LLM wrapper defaulted to a nano-tier
   model; on relative-size judgments it was a coin flip with a slot bias. With the
   champion always seated in slot A, single elimination turned that bias into a
   ratchet — the *mis-scaled start won 9/9 matches* across two runs. Same inputs on
   a mid-tier model: 4/4 correct. Pin the judge model explicitly; never trust a
   library default for judge/critic roles.
2. **Debias pairwise verdicts structurally.** Judge each match twice with image
   order swapped; agreement decides, disagreement escalates to a stronger tiebreak
   model. Bonus: the tiebreak *rate* is a free convergence signal — when most
   matches need the tiebreak, the candidates are indistinguishable and you're done.
3. **Renders must carry the signal.** Head-on orthographic-ish views collapse
   depth; a 3× camera standoff leaves the subject at 100px; untextured gray merges
   objects into one silhouette. Fix: 3/4 corner view, ~1.2× standoff, textures on.
   Judged accuracy is a property of the *renders* as much as the judge.
4. **Pixels carry no scale signal for small objects.** A sub-45cm object is a few
   pixels in an ensemble view, and a close-up fills the frame at ANY true size.
   Tag such members `[SMALL]` and have both proposer and judge size them
   **numerically** — exact dims are in the prompt, and the model knows a cocktail
   shaker is ~25cm. This took our worst small-object cases from "ignored or
   randomly drifted" to 0.8–11% error. (Detect smallness on the *middle* dimension:
   a chef's knife is 0.6m long but 2cm tall.)
5. **Plausibility is the only recoverable objective.** Injected-corruption
   benchmarks taught us: corruptions that keep an object *inside* its real-world
   plausible band (a 10cm desk succulent, a 20cm vase) are undetectable by any
   plausibility-based method — and harmless. Meanwhile the solver repeatedly
   "missed" synthetic ground truth by *correctly fixing* wild mis-scales we never
   injected (raising a genuinely too-low counter, crushing a 2m chalkboard).
   Score such systems against believability, not labels.
6. **Give the judge numbers AND pixels.** Both candidates' exact dims go in the
   judge prompt alongside the renders; relative-size errors can be invisible in
   pixels but obvious in meters, and vice versa. Also force the judge to describe
   each image before voting — verdict/description consistency exposes incoherent
   judgments in the log.
7. **Benchmark design**: inject known corruptions (both directions, 0.5×–3×) into
   some members, leave others clean, include fully-clean control scenes, and keep
   the wild retrieval noise — then measure recovery error AND false-positive drift
   on clean members. Our drift fell from ±14% to ~0–5% after the order-swap +
   numeric-sizing + early-stop fixes.

## Results snapshot (23-scene benchmark, 2 waves)

- Out-of-band corruptions on normal-sized members: typically 4–16% from ground
  truth, direction correct almost always.
- Out-of-band small objects (post-fix): shaker 2.4×→0.8% err, soap 2.5×→5%,
  wastebasket 0.55×→10%, water bottle 3×→11%.
- Anchors: untouched when correct; moved to their bound only when genuinely wrong.
- Large apparent errors are dominated by wrong-label rows (solver fixing real
  mis-scales) and in-band-unrecoverable rows — both acceptable behaviors.

## Code pointers

- `tools/planar_regions.py` — tile tournament (placement); `solve_placement` API.
- `IDSDL/vlm_placement.py` — DSL integration + AABB fallback.
- `tools/scale_solver.py` — proposal/critic scale solver; `solve_relative_scales`.
- `tools/scale_tournament_test.py` — minimal single-scene harness (bedroom).
- `tools/scale_bench.py` — 23-scene corruption benchmark; `--stage layout|solve|report`.
