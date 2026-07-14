# Next steps (rewritten 2026-07-13, post-verification-round)

The original post-restart queue is drained — the 20-scene phase-1 verification round is
complete (record: `skills/examples/_VERIFY_NOTES.md`), the release blockers are fixed
(portable paths, `.mcp.json` launcher, `requirements.txt`, LICENSE CC BY-NC 4.0), kitchen and
museum are promoted and gate-verified, and the lesson/program contradictions are reconciled.
Delete this file once the short tail below is drained.

1. **resto_kitchen** (the last uncovered dataset category): `scenes/work/resto_kitchen.py`
   passed phase 1 (after the cold-pair camera fix); the full build + VLM iteration was in
   flight at session end. When converged: write `skills/examples/resto_kitchen.md`, copy the
   program to `resto_kitchen_v1.py`, add the README index row.
2. **game_room window check** (opportunistic, one full build): confirm the floor-to-ceiling
   window renders correctly post-void-fix (greenhouse fixed the renderer 2026-07-12).
3. **Possibly-stale window workarounds** (opportunistic, same builds): bathroom's black
   back-wall window note; lobby's `curtain=None` rationale.
