# Home laundry room — worked example ("Integrated Laundry Command Center")

Status: **built & VLM-clean** (`skills/examples/laundry_room_v1.py`, seed=17; converged copy
beside this file as `laundry_room_v1.py`). Final full build: `no rotation` / `no wall
overlap` / zero lints at `modulate_scale=0.85`, `light_budget=180`. Built through the
guided 9-gate flow (flow_0713_025459_0aa9): two phase-1 builds, three phase-2, three full.

## Prompt(s) this covers
- "a home laundry room / utility room / mudroom laundry" — a DOMESTIC laundry, which is a
  different room from [laundromat.md](laundromat.md) (that one is a commercial coin-op with
  a machine bank and waiting seating; this one is one service wall in a small house).

## Plan summary
Planner → **"Integrated Laundry Command Center."** Two front-loaders aligned under a
continuous folding counter; an integrated sink at the counter end for pre-wash; open wire
shelving above holding baskets and detergent; a drying rack and ironing board tucked onto a
secondary edge; bright durable palette (white cabinetry, light tile, warm wood top); ample
daylight.

## THE layout: one service wall, and a shell you fix with SLOTS, not `modulate_scale`
A laundry is a **one-heavy-wall service room** (the laundromat skeleton at domestic scale)
with an empty working aisle down the middle. But the interesting work here was the SHELL,
and it is the most transferable thing in this file — see the footprint rule below.

- **BACK (hero) = THE RUN**: `GridGroup.place_row([washer, dryer, folding_counter, tub])`
  flush on the wall. The DSL has no fitted joinery, so the counter **continues** the machine
  line rather than sitting over it — same box silhouette, same ~0.9 m height, so it reads as
  one continuous worktop. Framed botanical print above it (a LOW support, laundromat's rule).
- **LEFT** = the open shelving tower, stocked. **RIGHT** = the concertina airer. Both in the
  **wall-CENTRE slot** so they share ONE grid row (see below).
- **FRONT** = the ironing board (centre), the door (right), a curtained window (left).
- **CENTRE** = the working aisle — holding only the basket of laundry you carry in.
- Appliance/cabinet clearance is FREE (`CategoryClearanceConstraint`), which is what keeps
  the aisle open. No manual constraints anywhere in this scene.

## THE footprint rule (the big one — read this for any small room)
`RoomGroup` sums **5 column-widths and 5 row-depths** (`compute_grid_dims`), and
`compute_dims_of_point` **swaps w/d by facing**:

| Wall the item stands on | costs, in room WIDTH | costs, in room DEPTH |
|---|---|---|
| back / front | its **width** (to one column) | its **depth** (to one row) |
| left / right | its **depth** (to one column) | its **width** (to one row) |

So **a side-wall item pays its WIDTH in room DEPTH**, and every *distinct slot* claims its own
row. v1 put sink (left-centre), shelf (left-left), airer (right-centre) and ironing board
(right-right) in **four different rows** and auto-sized a **4.5 × 3.9 m hall** around 12 m² of
furniture — `rescale room by 0.6`. Three re-slottings, no `modulate_scale`:

1. **The sink went INTO the back run** — which the PLAN had already told me to do ("an
   integrated sink at the counter end"). A wide piece is cheap on the back wall (pays its
   0.59 m depth) and expensive on a side wall (pays its 0.50 m width in a whole new row).
2. **Shelf and airer both moved to the wall-CENTRE slot**, facing each other across the aisle,
   so they **share one row** instead of claiming two.
3. **The ironing board moved to the front wall**, where its 0.40 m DEPTH pays for a shallow
   row instead of its 1.20 m WIDTH paying for a deep one.

Vote went 0.6 → 0.72 → 0.80 on structure alone. **Generalises kitchen's "find the footprint
culprit before you rescale" into a rule you can apply at DESIGN time: put wide things on the
back/front walls, keep side-wall items thin, and give the side walls ONE shared slot row.**

## Pinned assets (previews eyeballed at gate 3)
| Role | id | note |
|---|---|---|
| Washer | `future/39482d28-ac90-4f33-a07b-923edf6bd054` | white, black porthole, control panel |
| Dryer | `future/3a419f6e-b0d4-46e8-b5fe-d031008fee39` | white, silver drum — the matching sibling |
| Folding counter | `hssd/fa5562e2e06d5c189107ed10f1c3e05552cb1bb2` | white base cabinet, warm wood top — a solid BOX (see below) |
| Utility tub | `hssd/f06b92490816c0ae1d22b0e979718e475b8903a0` | grey tub on legs + faucet + drainboard; the real thing |
| Open shelving | `hssd/cf3140a9b17b1de888dc3670dd00799488566d19` | white 5-tier; `scale_only_height(1.35)` |
| Concertina airer | `hssd/a55da36088048698a1bebfd9aa7aaa5c17422961` | chrome folding clothes airer — unmistakable |
| Ironing board | `hssd/cc916aa81e794cea2f80fd42864aa66b285334c4` | white board, metal legs |
| Basket of laundry | `future/684d3071-f52e-48d9-a572-4288304678c5` | grey woven, **clothes spilling out** — the product |
| Wicker basket | `future/9f1cfe06-b99a-4b9e-93e2-21571589b0f0` | cloth draped over the rim |
| Rolled towels | `hssd/6ece1a15f0f508aab2371808d58eefa8420cf725` | the laundromat pin |
| "Detergent" | `hssd/9a83f86ed492c9283fed9baa9a97e1cfdc5140f3` + `hssd/e55406dff300de474e7a08711a7e75afd3495004` | bottle trio + pump jug — SUBSTITUTES, see below |

## Asset gotchas (all three caught at the audit gate, none by the loop)
- **No laundry DETERGENT mesh exists.** "plastic detergent bottles" tops out at **0.49** and the
  entire shortlist is bathroom toiletries (lotion pumps, soap dispensers, bath salts) — the
  casino poker-chip / kindergarten crayon-cup trap. Substituted by **silhouette** (tv_studio):
  at room scale a cluster of plastic bottles IS a detergent lineup. The one honest ingest
  candidate for a v2.
- **Every "clothes dryer" mesh is a FEATURELESS WHITE BOX** (`hssd/c2c17462`, `hssd/6cd2dc26` —
  no door, no drum), which at room scale reads as a blank cabinet, not an appliance. **A machine
  reads by its PORTHOLE**, so the pair is two front-loaders — which is what a real washer/dryer
  pair looks like anyway. (laundromat.md pinned the featureless box; prefer this.)
- **The top "wire shelving" hit is a SUPERMARKET basket rack** (`custom/71bda402`, 0.69 — an
  ingested retail mesh). Right words, wrong register for a house. Similarity ranked it first;
  the preview disqualified it.
- **Counter form factor matters for a RUN**: pinned a solid white base cabinet with a wood top
  rather than laundromat's leggy counter *table*, so it shares the machines' box silhouette and
  the back wall reads as one worktop instead of three unrelated objects.

## `place_inside` cannot carry a category read — the product goes on the LOW surface
The shelf was stocked (`place_inside`) with bottles and baskets and still rendered as a **bare
white bookcase with specks on it**. Cause: the smart-placement tournament **height-fits each item
to a fraction of the ANCHOR's height**, so a bottle against a 1.35 m shelf lands at ~0.14 m —
invisible from across the aisle. Massing 7 items did not fix it (each one is just another speck),
and `modulate_scale` is a **no-op** on on-top/inside items (tv_studio).

**The fix: put the same product on the 0.9 m folding COUNTER via `place_on_top`**, where the same
height-fit rule sizes it to a readable ~0.3 m — and where the money-shot camera actually looks.
**Corollary to jewelry_shop's product rule: "product at viewing height" is not just about the
camera, it is about the ANCHOR — the shorter the anchor, the bigger the prop it seats.** Stock the
shelf anyway (it is correct up close), but never let it carry the read.

## Lighting: the BRIGHT-room mirror of the wine_cellar lesson
The first full build **blew out to pure white** — the tile floor vanished entirely — the moment
phase 3 added a window and `add_lighting`. `add_lighting` spends a fixed **500 W** budget, which in
an ~11 m² room whose every surface is white, on top of the interior sky, is a flood.
→ **`scene.light_budget = 180.0`.** Not the fixture (already a flush disc), not the density
(0.01 — that is COUNT, not brightness). And unlike `IDSDL_SKY`, `light_budget` is a **scene
attribute**, so it works through the warm MCP `run_scene` (the cellar's sky override does not).
**A small all-white room needs the budget dropped just as much as a cellar does.**

## VLM feedback log
- **Room size, settled with ARITHMETIC** (kitchen_set's rule). Vote train `0.6` → `0.72` → `0.80`
  (Ph2) → held per render-wins-early. The back-wall run is a **rigid `GridGroup` row that cannot
  compress**, so the shrink has a closed-form floor:
  `WIDTH >= run (3.0) + shelf depth (0.26) + airer depth (0.64) + margin ~= 4.1 m`, i.e.
  `modulate_scale >= 4.1 / 5.03 = 0.82`. **The voted 0.80 is BELOW that floor** — obeying it would
  overflow the run into the side-wall pieces (the locker_room packed-row bug). Applied **0.85**;
  the vote decayed `0.90` → `0.95` → bounced back to `0.90` across identical builds = noise →
  declined. **When a wall carries a rigid row, compute the floor instead of negotiating.**
- **`rotate door by 90` (×2) appeared ONLY on the blown-out build** and vanished, unprompted, the
  moment the exposure was fixed — the layout never changed. The door renders perfectly face-on in
  every view. **A garbage render corrupts the VLM constraints judged from it — and OVEREXPOSURE is
  a garbage render, not just occlusion** (bakery's blinded-camera lesson, new variant). If rotation
  flags appear alongside a render you can barely read, fix the render first and re-look.
- `no rotation` / `no wall overlap` on every other build: all four wall placements omitted `facing`
  (the heuristic turns each piece into the room), the art hangs over the LOW run, and the door /
  window / floor items sit in disjoint slots — clean by construction (laundromat, classroom).

## Camera notes (the wall-centre rule, and why it was survivable here)
Everything in the run is ~0.9 m and the ironing board is 0.79 m, so no interior camera is ever
blinded. The two pieces that DO stand at wall centres — where the opposite view's camera sits —
are the shelf and the airer, so the shelf is **height-fit to 1.35 m** (`scale_only_height`; the
native 1.68 m crowds the ~1.9 m lens) and nothing is stacked on top of it. Note `scale_only_height`
is the right tool here precisely because the frame is rectilinear: a uniform fit would also have
shaved the width to 0.80 m and shrunk every tile the product sits in.

## Manual constraints used
None. Auto overlap/bounds + door clearance + the appliance/cabinet category clearance sufficed.

## Possible refinements (not blocking)
- **Ingest real detergent bottles** (a jug, a powder box, a fabric-softener bottle). It is the one
  asset gap in the scene and would sharpen the read more than any layout change.
- The airer is empty; a garment draped over it would be the strongest "in use" cue available. No
  such combined mesh exists (`hssd/538d8ca4` is a clothes LINE with laundry — worth a look for a
  utility/balcony variant).
