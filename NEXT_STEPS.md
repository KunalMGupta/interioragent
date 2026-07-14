# NEXT STEPS (2026-07-14 — delete when drained)

## Blocked on Kunal

1. **Scene feedback** (from the earlier batch): review `reviews/2026-07-14/REVIEW.md` (19 scenes)
   and write under each scene's Feedback block. Next session: `python tools/review_board.py
   reviews/2026-07-14 --pending`, act on every non-empty block, fold durable findings into
   `skills/examples/`.
2. **Constraint playbook discussion**: walk `skills/workflow/constraint_playbook.md` §5
   (7 open questions); promote agreed items into `IDSDL/default_constraints.py` and strip DRAFT.
3. **Asset shop — the one missing key.** `python -m IDSDL.shop` is built and tested, but Sketchfab
   *downloading* needs a free token that we do not have:
   ```
   sketchfab.com -> Settings -> Password & API -> API token
   echo 'SKETCHFAB_API_TOKEN=...' >> .env
   ```
   Everything else in the pipeline is proven end-to-end (search is live and needs no key;
   normalize/triage/verify/ingest were tested on mangled dataset assets against ground truth and
   on raw Sketchfab downloads from `hospital.zip`). Until the token exists, `run` degrades to
   handing you download links + an `inbox/`, which is a supported path, not a failure.
   With the token, one command is worth running first as a shakedown of the download leg:
   `python -m IDSDL.shop run "reception desk" --count 5 --dry-run`.
4. **Meshy** (`--source meshy`): implemented against the documented OpenAPI v2 text-to-3D flow but
   NEVER run against a live key (we have none, and every call spends credits). Needs
   `MESHY_API_KEY` in `.env`, then a 1-asset shakedown; check `IDSDL/shop/meshy.py`'s `API`/`MODEL`
   constants against Meshy's current docs first.
5. PR #1 (feature/scene-skills-orientation-tooling -> main) is still open; **rotate the exposed
   PAT** after it lands.

## Known, deliberate, not bugs

- Auto-ingest yield is high for ordinary furniture (3/4 on the ground-truth set) and LOW for
  exotic equipment (1/6 on the hospital batch) — the library has no size prior for a slit lamp and
  the VLM knows it is guessing, so it asks. That is the intended behaviour, not a regression.
- The VLM is nondeterministic: the same asset can land in `go` on one run and `ask` on the next.
  The gates are what keep this safe, not repeatability.
