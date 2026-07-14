# NEXT STEPS (2026-07-14 — delete when drained)

## Blocked on Kunal

1. **Scene feedback**: review `reviews/2026-07-14/REVIEW.md` (19 scenes) and write under each
   scene's Feedback block. Next session: `python tools/review_board.py reviews/2026-07-14
   --pending`, act on every non-empty block, fold durable findings into `skills/examples/`.
2. **Constraint playbook discussion**: walk `skills/workflow/constraint_playbook.md` §5
   (7 open questions); promote agreed items into `IDSDL/default_constraints.py` and strip DRAFT.
3. **Two new library assets need to reach everyone else.** The shop ingested a Royal typewriter
   (sketchfab, CC-BY) and a cork pinboard (meshy) — both filling gaps the lessons had recorded as
   unfillable. Their metadata is committed, but `IDSDL/datasets/custom/models/*.glb` is
   git-ignored, so **fold the two new .glb into datasets.zip** or a fresh clone will have dangling
   entries. (Same for anything the shop ingests from here on.)
4. PR #1 (feature/scene-skills-orientation-tooling -> main) is still open; **rotate the exposed
   PAT** after it lands — and the Sketchfab + Meshy keys, which are also in the chat log.

## Done, keys live

`SKETCHFAB_API_TOKEN` and `MESHY_API_KEY` are in `.env` (git-ignored) and both legs are proven
end-to-end against the real APIs. Meshy balance after the shakedown: 1675 credits
(~5/preview, ~10/refine).

## Known, deliberate, not bugs

- Auto-ingest yield is high for ordinary furniture (3/4 on ground truth) and LOW for exotic
  equipment (1/6 on the hospital batch) — the library has no size prior for a slit lamp and the
  VLM knows it is guessing, so it asks. Intended, not a regression.
- The VLM is nondeterministic: the same asset can land in `go` on one run and `ask` on the next.
  The gates are what keep this safe, not repeatability.
- Meshy `--no-refine` produces an UNTEXTURED grey blob. It is the opt-out, never the default, and
  the untextured gate will park it on the board rather than ingest it. See
  `skills/acquire-assets/SKILL.md`.
