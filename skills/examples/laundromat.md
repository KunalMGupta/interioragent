# Small laundromat — worked example

Status: **built & VLM-clean** ("Efficient Compact Laundromat Block",
`scenes/work/laundromat_v1.py`, seed=42). Final compile: `no rescale / no rotation /
no wall overlap` at `modulate_scale=0.75`. Built through the guided 9-gate flow
(flow_0712_142841_c8f4), three phase-gated builds + one convergence rebuild.

## Prompt(s) this covers
- "a (small) laundromat / coin-op laundry", "a laundry room with washers and dryers,
  folding counter, waiting seating". Scale the machine row for bigger shops.

## Plan summary (from the planner)
"Efficient Compact Laundromat Block": a continuous folding/sorting surface with a warm
wood top over/beside a linear run of side-by-side front-loading machines; a slim rolling
cart between machines; waiting seating along a wall; bright calm palette (white machines,
pale grey walls, warm wood, wicker/greenery textures); a framed ocean artwork focal;
bright even task lighting; durable reflective floor.

## The layout idea: single service wall + light opposite wall
A laundromat is a **one-heavy-wall** room (procedural cousin of locker_room's spine and
bar's line): the machine run carries the back wall, the folding counter takes a side wall,
and the waiting nook sits opposite the counter so the centre aisle stays clear. Slot
economy for the "small" brief (coffee_shop lesson): 4 floor slots only.

- BACK: `GridGroup.place_row(washers + [cart] + dryers)` flush on the wall — the plan's
  "slim rolling cart parks between the machines" is expressed literally as a row member.
  Framed ocean art hangs ABOVE the low machine run (low support → clears the ceiling,
  unlike locker_room's over-spine clock).
- LEFT: folding counter (white base + warm wood top, `width=1.8`) with rolled towels +
  wicker basket `place_on_top`; triple canvas laundry sorter in the left wall's front slot.
- RIGHT: waiting nook = bench (anchor) + plant + grey rug, one RelativeGroup.
- FRONT: door (right) + standard window (left; small pane — void lesson) + wall clock
  (center).
- Lighting: `room.add_lighting(flush LED, density=0.01)` — small-room density.

## Pinned assets (audited previews — dataset covers laundry WELL, contrary to the
"washing machines are a likely gap" catalog warning)
| Role | id | note |
|---|---|---|
| Washer ×2 | `future/460819c5-917f-4c72-9b3d-84de0ca36aa0` | front-loader, chrome door ring; renders SILVER-grey, not white |
| Dryer ×2 | `hssd/6cd2dc2611c27f758c972b4874efad8c8cbd5d29` | white, light drum door — good washer/dryer contrast |
| Folding counter | `hssd/67b505c2cfc433bc4ffe39250cafda3951d91939` | white counter table + warm wood top (the plan's surface, one mesh) |
| Bench | `hssd/a5faa788a66067bdb536364b705735ba7c5547af` | the known floor-resting bench (coffee_shop swap target) |
| Rolling cart | `hssd/491b7091a828edecf83eaa865059e3a680d0d728` | white 3-tier; `modulate_scale=0.6` to slot between machines |
| Laundry sorter | `hssd/aeae32d8bdeefca3ed46e3f0e6b69106e226fe22` | triple canvas — the strongest laundromat identity prop |
| Wicker basket | `future/c96d2ee0-8593-42b8-bcc3-bd9e4476b49d` | fabric liner, warm texture accent |
| Towels | `hssd/6ece1a15f0f508aab2371808d58eefa8420cf725` | rolled white stack (locker_room's premium cue), `modulate_scale=0.7` |

## What worked / gotchas
- **Mixed-type GridGroup row.** `place_row(washers + [cart] + dryers)` happily rows
  heterogeneous items — the cart-between-machines plan motif needed no special group.
- **Appliance clearance is free.** The washers/dryers match `CategoryClearanceConstraint`'s
  appliance rule, so the loading aisle in front of the run kept itself clear — no manual
  clearance.
- **Skipped the plan's white upper cabinetry** deliberately: wall-hung deep meshes render
  as floating furniture (`place_on_wall_*` is FLAT-only), and a laundromat reads fine
  without uppers. The ocean art carries the wall instead.
- **Skipped counter detergent bottles** (casino place_on_top lesson — don't assume a small
  prop exists); towels + basket dress the counter sufficiently.
- **A sparse room may be shrunk below 1.0** — the locker_room "never shrink" rule is about
  furniture-PACKED rooms. Here the empty centre aisle was genuine oversize.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.7` (Ph1) → `0.8` (Ph2) → `0.75` (full, at 0.85) → **held through
  phases 1–2** (render-wins-early), applied `modulate_scale=0.85` in the final phase,
  vote persisted at 0.75, took one more decisive shrink to **0.75** → `no rescale`.
  Two-step final-phase convergence; the room is sparse so sub-1.0 was safe.
- `no rotation` / `no wall overlap` every phase — the omit-`facing` defaults on all three
  wall placements were correct from the first build.

## Manual constraints used
- None. Auto overlap/bounds + door clearance + the appliance category clearance sufficed.

## v2 — the same aesthetic at real coin-op scale (user iteration)
`scenes/work/laundromat_v2.py` ("needs a lot more machines"): 9 machines on TWO
walls — a 5-washer bank (+ cart) on the back wall, a 4-dryer bank on the right
wall, waiting nook moved to the front wall (clock above the bench — floor vs
wall-hung occupy independently). Converged lint-clean at `modulate_scale=0.9`,
`density=0.01`. Two v2-specific notes:
- **Lighting density does NOT transfer across versions of the same scene.** v1's
  clean `0.01` was bumped to `0.02` for the bigger floor — that tiled 14 fixtures
  onto 39 m² (starfield lint). The count already scales with area; keep the small
  number and let the budget spread.
- **Declined the persistent `rescale room by 0.8` at 0.9** — three walls loaded
  (locker_room packed-room rule) and the open centre is the customer aisle, which
  reads correctly. A centre wood-top folding island is the right move if the
  floor must fill (also the authentic fixture), not a deeper shrink.

## Possible refinements (not blocking)
- The washers render silver-grey; for a strict all-white plan palette, rebrowse and pin a
  whiter front-loader (e.g. `hssd/16c33cffd5b62d0d5df5ed6dd607f690ce2ee7c7`).
- No coin-op cue exists in the dataset (no coin machine / vending / detergent dispenser
  mesh) — logged as an ingest candidate for a truly commercial laundromat read.
