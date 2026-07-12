# retail_store — notes

**Pattern:** a modern apparel **boutique** built on a **central merchandising spine** — two
double-sided garment rails (`place_on_left`/`place_on_right`, `facing="left"` to run them
front-back) flanking a low wood+metal display table (`place_on_center`) topped with folded
sweaters — plus a **branded service wall** at the back (curved reception-desk cash-wrap +
POS + bags, under a "Welcome"/neon sign), **perimeter merchandising** on the side walls
(wall shelf + shoe display + framed rack + fitting mirror), and a **front-window mannequin
display** (3 mannequins across the front row). Palette: greige walls + concrete floor +
matte-black metal fixtures + warm wood tops; clothing colour is the accent.

**Kickoff = a retrieval STRESS TEST** (`scratchpad/retail_stress.py`, embedding-only
`svc.browse` over ~34 category queries): **zero hard gaps**, every query ≥0.39 top-1. Soft
spots covered by substitutes (checkout→reception desk, cash register→POS terminal, store
sign→neon/Welcome sign, basket→wicker). No ingest.

**Heroes (pinned):** rail `future/a419b5a4…` (true double-sided; the VLM #1 is a coat valet),
framed rack `future/a3e8bf5a…`, wall shelf `hssd/76ae9b47…`, shoe shelf `hssd/e9597e32…`,
counter `hssd/7379d8877f…`, mannequin `hssd/852f2364…`, display table `hssd/e7b5486297…`,
folded sweaters `future/c17aa2e4…`, showcase `hssd/be0ea104…`.

**Gotchas (full detail in skills/examples/retail_store.md + workflow/vlm_feedback.md):**
- **Lighting density scales with floor area:** `density=0.3` tiled ~40 flush discs on this
  big floor; use **~0.05–0.1** for a large room. (Still FLUSH, never a chandelier/track rig.)
- **Storefront = worst-case black void:** `place_window_floor_to_ceiling` on the front wall =
  a wall-sized void → use `place_window_standard` + mannequins staged in front as the display.
- **`run_scene` mtime-fallback:** on a build error it reports the newest *other* run's renders
  (I got a garage back) — check the asset list, re-run via `workbench.py run` for the truth.

**Status:** built & VLM-clean 2026-07-06 (`scenes/retail_store.py`, seed 42), converged at
`modulate_scale=0.9` after 3 renders (window + lighting-density fixes, then a 0.9 tighten).
Distinct from `office.py` (open-plan) and other category templates.
