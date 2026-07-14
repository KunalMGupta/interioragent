# Next steps — handoff before the docker restart (2026-07-13)

Written because the NVIDIA driver became inaccessible and the container must be restarted.
Delete this file once the queue below is drained.

## BEFORE restarting (only matters if the container filesystem is recreated, not just restarted)
1. **`git push`** — the branch is ~50 commits ahead of origin. Unpushed commits die with the container.
2. **Kitchen + museum WIP is UNCOMMITTED** — `skills/examples/kitchen.md` (modified),
   `skills/examples/kitchen*_v?.py`, `scenes/work/kitchen*_v?.py`, `scenes/work/museum.py`,
   `scenes/work/museum_grand.py`. Commit them as WIP or copy them out.
3. **`/work/.env` is gitignored** (holds `OPENAI_API_KEY`) — back it up or re-create it after.

## AFTER the restart
- Rebuild the image from the **updated Dockerfile** (commit `47368c9` pins `mcp==1.28.1 pillow`).
  If reusing an old image instead: `/opt/conda/envs/interioragent/bin/pip install "mcp==1.28.1"`.
- `git config --global --add safe.directory /work`
- Re-create `/work/.env`, then restart Claude Code so the `idsdl` MCP server spawns.

## The work queue
1. **Verification round** (GPU required): phase-1 builds of the 20 remaining retrofits.
   The full checklist — scene list, run command, per-scene judgement calls, the partial-build
   room-size-vote rule — is in `skills/examples/_VERIFY_NOTES.md`. `bedroom` and `bar` already
   passed phase 1.
2. **Reconcile the two lesson/program contradictions** (computer_room's phantom 1.1 enlarge;
   retail_store's stale 0.9/0.08 + the rotate vote its program now applies) — details in
   `_VERIFY_NOTES.md`; the lessons were deliberately left untouched.
3. **Cross-scene flags**: gym's 0.60 m reception desk (`get_whd()` it), lobby's focal art behind
   the reception counter, delete the duplicate `scenes/work/salon_pretty.py`.
4. **Finish the WIP scenes**: kitchen, museum (promote to `skills/examples/` when done).
   `resto_kitchen` is the last uncovered dataset category (Restaurant-Kitchen, 54 entries).
5. **Release blockers** (pre-release audit, 2026-07-13): 36 hardcoded `/work` + `/opt/conda`
   paths across `IDSDL/service/{core,flow,mcp_server}.py`, `retriever_core/catalog.py`,
   `IDSDL/renderer/utils.py`, `.mcp.json` (repo only works when cloned to `/work`); README's
   install line is missing `mcp`/`pillow`/`sceneprogexec`; no `LICENSE`; no `requirements.txt`;
   `test.py` at root is a scratch scene, not a test.
6. **Cosmetics**: `classroom.md` vs `classroom_v1.md` duplication; `kindergarten_v1.md` naming
   (the convention is no `_v1` on the `.md`); root utility scripts could move under `tools/`.
