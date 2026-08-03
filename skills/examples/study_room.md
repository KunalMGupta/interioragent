---
id: example:study_room
kind: example
family: hero-anchor-room
category: "residential computer study / home office"
pattern: "Hero workstation + a LOADED IDENTITY WALL — wall mass is paid in floor area, and the camera budget decides the wall's profile"
read_for:
  - "READ FOR ANY ROOM WHOSE IDENTITY IS A LOADED WALL (bookshelf wall, gallery wall, display run) — coverage is bought with the shell's floor area"
  - "READ FOR ANY WorkstationGroup ANCHORED ON A NON-RECTANGULAR (L/U) DESK — the chair seats off the BOUNDING BOX"
---
> **Digest (from the pattern index):** **Hero workstation + a loaded identity wall** —
> `office_modern`'s skeleton re-cut for three explicit prompt clauses (L-desk, monitor ARM,
> bookshelf WALL). The two lessons that cost builds: (1) **wall mass is paid in floor area** — a
> wall's slots are THIRDS of that wall, so doubling the shelving run forced the shell from 22.5 m²
> to 44.8 m²; buy coverage with deliberate width-only stretches on height-pinned pieces instead.
> (2) The **stepped shelf run is camera arithmetic**: eye = 1.65 m stands at every wall centre, so
> the 2.175 m units go to the wall ENDS and a measured 1.25 m unit takes the CENTRE. Also: an
> L-desk's bbox is square and mostly air, so `place_chair` strands the chair ~1 m out —
> `station.face(chair)` fixes the aim but not the distance; and a centre slot beat the type's
> corner-desk signature by 15 m² of shell.

# Residential computer study — worked example ("Ladder-Frame Study Wall")

## Status

Status: **built & VLM-clean** ([`study_room_v1.py`](study_room_v1.py), seed=11, Arm B guided
flow, 7 builds). Final compile: no rescale / no rotation / no wall overlap, zero lint or
WARNING lines, 5.12 × 4.00 = 20.5 m². Per-view pure-black fractions measured with PIL on the
final build's raw `vlm_views` PNGs: ≤ 0.18% on every view — the camera trap was designed
around, not diagnosed after.

## Prompt(s) this covers
- "a residential computer study room with an L-desk, a monitor arm, and a bookshelf wall"

## Plan summary (from the planner)
"Ladder-Frame Study Wall": a warm-wood study whose signature was a ladder-frame shelving wall
with an INTEGRATED desk surface, a teal back panel and brass sconces. Two of those three were
not expressible (no integrated desk-shelf system exists in the pool; `place_walls` applies ONE
texture to all four walls, so a single accent wall cannot be painted) — the teal accent
migrated onto a green velvet armchair + greenery, per `office_modern`'s carry-the-accent-on-a-
prop lesson. Declared as a deviation, not discovered as a failure.

## The layout idea: HERO WORKSTATION + A LOADED IDENTITY WALL
Inherits `office_modern`'s skeleton (one hero work zone + a storage backbone + two light
walls); what is new is that the backbone IS the room's identity, and its profile is dictated by
the camera budget. Wall jobs:

- **BACK** — the bookshelf wall: a stepped tall–low–tall three-unit run, one unit per wall slot.
- **CENTRE** — the `WorkstationGroup`: L-desk + task chair + monitor arm + lamp + pen cup on a
  rug, `facing="back"` so the operator sits with their back to the books, looking at the window.
- **LEFT** — a low credenza with decor (its own `RelativeGroup`, so `place_on_top` targets it).
- **RIGHT** — the reading perch: green velvet armchair + side table as ONE group.
- **FRONT** — a standard punched window centre + the door right; the fig in the back-right corner.

## Pinned assets (audited previews, dims verified offline with `get_whd()`)
See the id block in the program. The ones that carry lessons:
- **L-desk** `hssd/5f27a543` (1.800 × 0.719 × 1.800, flat top). Build 1's live-edge L had
  correct geometry but its "wooden" top RENDERED as pale grey concrete at camera distance —
  caught by eyeballing the phase-1 render, not by the VLM, which said `no rescale` on it.
- **Monitor arm** `hssd/878fded4` — a REAL articulated arm + panel on a desk clamp, not a
  plain-monitor stand-in. Height-fit UNIFORMLY 1.141 → 0.62 m after an ASPECT check (the
  panel's width lies along D: 0.988 × 0.543 = 0.54 m — a 24" screen). A single-axis `width=`
  pin would have squashed the arm's reach instead.
- **Bookcases** — all three pinned BECAUSE their shelves ship full of books (see lesson below).

## Asset gaps
No integrated desk-shelving system; no expressible accent wall. Both resolved by substitution
(see plan summary) rather than acquisition — every id is from the warm pool.

## Wall mass is paid in floor area
The run coverage took three builds, and the tension generalises to any loaded wall:

- build 1: one 0.80 m unit per end slot → 49% wall coverage; right-sized room but it read as "a
  room that owns three bookcases", not a BOOKSHELF WALL.
- build 2: `place_row` of two per end → the wall genuinely read as a library, and the shell blew
  out to 44.8 m² with the desk in — a residential study the size of a squash court (the
  `coffee_shop` cavernous-shell failure).
- **Why:** a wall's slots are THIRDS of that wall, so the shell must grow until every slot fits
  its occupant. A 1.60 m row in a third forces the wall past 4.8 m before margins.
- build 4 (final): single tall units at the ends, coverage bought instead by width-only
  stretches (ends 0.80 → 1.10 m, centre 1.00 → 1.40 m): 78% coverage, shell stays study-sized.

## The stepped run is camera arithmetic, not styling
`renderer/utils.py:741`: each interior camera stands at the OPPOSITE wall's CENTRE at
`eye = floor_z + 0.55*H`; `groups.py` clamps H to 3.0 m, so **the eye is 1.65 m**. Anything
taller parked at a wall centre CONTAINS a camera and renders that view pure black — while the
VLM feedback string still reads clean, because it checks per-object geometry and never asserts
a render exists. So: 2.175 m units at the wall ENDS only; the measured 1.25 m unit takes the
CENTRE (0.40 m of clearance); all four wall centres carry a sub-1.65 m occupant. Same rule as
`closet`, applied to a single loaded wall.

## The deliberate single-axis stretch (the exception that proves uniform-fit)
Both `width=` pins in this program are deliberate: these pieces' HEIGHTS are pinned by the
camera budget, so a uniform fit is the trap — it would drag the centre unit to 1.75 m (through
the eye line) and the tall ends to 2.99 m (into the 3.0 m ceiling). Stretching a bookcase's
shelves 1.375× along width alone is a mild, believable change. Everywhere else the program
uniform-fits (`_fit_height`).

## The L-desk bbox trap
`WorkstationGroup.place_chair` seats the chair off the anchor's BOUNDING-BOX front face. An
L-desk's bbox is SQUARE (1.80 × 1.80) and mostly empty air, so the chair landed stranded ~1 m
out in open floor, square-on to the room. `station.face(chair)` — re-applied at END of compile
from final positions — fixed the aim (`no rotation`), but not the distance. Honest residual:
the chair sits ~1 m off the desk rather than in the L's inner elbow.

## Centre slot vs the type's corner signature
A corner desk is this room type's procedural signature, and build 3 delivered it — at 37.4 m²
vs 22.5 m² for the identical program with the station at centre: a corner slot forces the shell
to grow a front row AND a side column deep enough for the station. 15 m² of dead floor is a far
worse failure than a desk that doesn't touch two walls, and the room-size vote got
monotonically angrier as the room grew. **Room size is a consequence of slot occupancy — fix it
at the slot, never in `modulate_scale`.**

## Books ship IN the mesh — never stock a bookcase
There is deliberately no `place_inside` stocking pass: the pantry lesson measured that
`place_inside` grinds a tall fixture's fixed product mass into ever-smaller specks
(n=3 → 0.15 m; n=18 → invisible). All three units were pinned because their shelves ship full.

## Program
[`study_room_v1.py`](study_room_v1.py) — phase 1 the whole floor layout (workstation, shelf
run, credenza, perch, fig, door, ~1 min); phase 2 the desktop dressing, credenza/side-table
decor and rug; phase 3 the window, wall art, ceiling fixture.
`workbench run study_room_v1.py --phase 1` validates the layout alone.

## What worked / gotchas
- `facing` OMITTED on all wall placements — the wall heuristic already turns furniture into the
  room; naming the wall's own direction turns it to face the wall.
- Two groups reaching into one region (desk centre + perch left) read broken in build 2 even
  with every constraint passing (the `st_writer_studio` trap) — the perch moved to the RIGHT
  wall, diagonally opposite.
- Door placed in PHASE 1: its auto clearance shapes the floor solve.
- `modulate_scale=0.85` applied ONCE in the final phase, on a vote stable at 0.78–0.84 across
  five builds (converged signal, not oscillation) — and picked slightly ABOVE the vote because
  the slot arithmetic still clears at 0.85, while at 0.80 the left wall's slot (1.21 m) starts
  overflowing its 1.20 m credenza. A shrink that buys occupancy by creating overlaps is not a
  win (the `locker_room` failure).

## VLM feedback we hit and how we resolved it
- `rotate office chair to face the L-shaped desk` (build 2) → `station.face(chair)` → aim fixed
  from final positions; accepted.
- Room-size votes 0.84/0.78/0.80/0.71/0.80 → held at 1.0 through phases 1–2 (a vote on a
  partial build is a vote on a room that does not exist yet — `bedroom` lesson), applied once
  at 0.85 in the final phase; the 0.71 outlier declined as the vote reacting to the corner-slot
  build's oversized shell.

## Manual constraints used
None beyond the defaults — camera safety was handled by geometry (measured heights), and the
lifted/wall pieces are ordinary placements.

## Possible refinements (not blocking)
- The shelf run covers ~70% of its wall with plaster gaps between units, and the pale tall
  units clash slightly with the dark walnut centre — a wall OF bookcases, not a built-in
  library wall. A matched three-unit family would close it.
- The task chair's ~1 m stand-off (bbox trap above) — a `WorkstationGroup` variant that seats
  the chair off the desk's occupied footprint rather than its bbox would fix the class.
