# NEXT STEPS (2026-07-14, end of session — delete when drained)

All four of Kunal's 2026-07-14 tasks are done and pushed (kitchen islands, category batch +
review board, auto room height, constraint playbook draft). What remains is BLOCKED ON KUNAL:

1. **Scene feedback**: Kunal reviews `reviews/2026-07-14/REVIEW.md` (19 scenes) and writes
   under each scene's Feedback block. Next session: `python tools/review_board.py
   reviews/2026-07-14 --pending`, act on every non-empty block, fold durable findings into
   `skills/examples/`.
2. **Constraint playbook discussion**: walk `skills/workflow/constraint_playbook.md` §5
   (7 open questions) with Kunal; promote agreed items into `IDSDL/default_constraints.py`
   and strip the DRAFT banner.
3. PR #1 (feature/scene-skills-orientation-tooling -> main) is still open; the exposed PAT
   should be rotated after it lands.
