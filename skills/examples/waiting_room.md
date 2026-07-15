---
id: example:waiting_room
kind: example
family: zoned-multi-zone
category: "clinic / office waiting room"
pattern: "Two facing seat banks + a reception anchor"
---
> **Digest (from the pattern index):** **Two facing seat banks + a reception anchor** — the lobby's reception bones (a `WorkstationGroup` with an INVERTED desk, `place_on_back` so staff have floor to stand on) with the lounge swapped for a symmetric double seat run pinned flush to both long walls, a magazine table between them, palms flanking reception. Teaches: **"rows of linked chairs" has no mesh — PACK them** (the only multi-seat banks are moulded cafeteria rows, and every "waiting bench" query returns a DOMESTIC sofa with throw pillows — categorically wrong, prison_cell); `GridGroup(sparsity=0.05)` runs **no overlap solve**, so single chairs stay abutted and read as one linked bank (greenhouse v2's packing trick, applied to seating), and the two runs on the two long walls buy the room shape for free. Its sharpest lesson: **a back-centre print behind a reception desk is ALWAYS crossed by the monitor** — art centres at ~1.5 m, a counter + monitor tops out at ~1.6 m, the wall-object clearance pass only slides FLOOR objects (never an on-top item), and there is no `bottom=` lift on the wall-HUNG path ⇒ **the fix is ASPECT, not size**: a 1.92-aspect PANORAMIC lets the monitor interrupt only a central strip (widening the portrait print instead would have made it 2.16 m TALL — wall scaling is uniform). Also: **the empty-frame trap is not just picture frames** — 6 of the 8 top wall-CLOCK hits are featureless white DISCS (a dinner plate on the wall); the plan's GLASS table rendered as a solid BLACK MONOLITH (loop-clean — form factor is an eye catch, caught in the cheap phase-1 loop); and a room whose walls carry rigid GridGroup rows must **fill the floor and stop SHORT of the shrink vote**


# Waiting room (clinic) — worked example

Status: **built & converged** (`skills/examples/waiting_room_v1.py`, seed=11; 2× phase-1, 1× phase-2, 3× full).
Final compile: `no rotation`, `no wall overlap`, no `[Lint]`/WARNING lines; room size converged at
`modulate_scale=0.95` (vote decayed 0.8 → 0.9 → 0.95 ≈ neutral). Built through the guided 9-gate
flow (flow_0713_025644_6bc4). Supersedes the thin pre-workflow `scenes/waiting_room.py`.

## Prompt this covers
- "a (clinic / doctor's / dental / office) waiting room / waiting area": rows of linked waiting
  chairs, a reception desk, a low table with magazines, plants, wall art, soft overhead lighting.

## Plan summary (from the planner)
"Layered Focal Axis for a Modern Clinic Waiting": a dark-wood reception desk anchoring the service
end, low-profile **olive-green** lounge seating around a slim table, biophilic palms, calm framed
art, a neutral beige/grey envelope over polished stone, daylight through large windows plus soft
overhead light.

## The layout idea: two facing seat banks + a reception anchor in the back third
The lobby's reception-anchor bones with the lounge swapped for a **symmetric double seat run** —
which is what makes it a *waiting room* rather than a *lounge*:
- **LEFT + RIGHT walls = the seating field.** ONE bank (4 chairs) built once, `2 * bank` duplicated,
  each pinned flush with `place_on_left/right_wall_center`. No `facing=` — the wall heuristic already
  turns each bank into the room, so the two rows face **each other** across the table.
- **CENTER = the magazine table** — a `RelativeGroup` whose ANCHOR is the table, so `place_on_top`
  seats the magazines on the *table* (not on a chair — the living_room_cozy v3 trap).
- **BACK third = reception** — a `WorkstationGroup` with an INVERTED desk (`set_rotation(180)`),
  dropped with `place_on_back(facing="back")` — **not** `place_on_back_wall`, so the receptionist has
  floor to stand on. Palms flank it; the focal print hangs behind it.
- **FRONT wall = entry** — door right, **wall clock** centre, water cooler in the corner.

## The reusable lesson: no beam-linked bank exists — PACK a GridGroup instead
"Rows of linked waiting chairs" is the literal ask, and the dataset cannot serve it directly:
- `"a row of linked waiting room chairs on a metal beam"` → the two genuine multi-seat meshes
  (`hssd/14c4e5a4`, `hssd/61d4e356`) are rows of loose **moulded cafeteria chairs** — an event
  hall, not a clinic.
- `"upholstered three-seat waiting bench / public seating bank"` → **domestic sofas with throw
  pillows**, top to bottom. Geometrically fine, categorically wrong (the prison_cell floral-curtains
  rule: the loop cannot see "that object has no business in this room").

**Fix: build the bank out of single chairs and pack them.** `GridGroup(sparsity=0.05)` runs **no
overlap solve**, so the chairs stay abutted instead of being pushed apart — they read as one linked
bank. Same mechanic as greenhouse v2's plant beds, applied to seating:
```python
with scene.GridGroup(sparsity=0.05, randomness=0.12) as bank:
    bank.place_row(4 * scene.AddAsset("an olive green upholstered lounge armchair", asset_id=CHAIR))
bank_left, bank_right = 2 * bank          # build ONCE, duplicate (design_principles)
...
room.place_on_left_wall_center(bank_left)   # no facing= — the heuristic turns it into the room
room.place_on_right_wall_center(bank_right)
```
This also buys the room shape for free: the two long runs land on the two long walls, and the shell
comes out as a proper deep waiting room.

## The other reusable lesson: a back-centre print is ALWAYS crossed by the desk monitor — go PANORAMIC
Wall art mounts centred at **~1.5 m**; a reception counter (1.10 m) with a monitor on it tops out at
**~1.6 m**. So *any* `place_on_wall_back_center` print behind a reception desk is crossed by the
monitor — and **no signal fires**: the automatic wall-object clearance pass only slides **FLOOR**
objects out of a wall item's span, never an `place_on_top` item, and there is no `bottom=` lift on
the wall-HUNG path to raise the art.

v1 hung a **portrait** print (0.40 × 0.54, aspect 0.74) and the monitor's white back **bisected it**.
The fix is not to enlarge it — wall scaling is **uniform**, so widening that print to 1.4 m would
have made it **2.16 m tall**. The fix is a different **aspect**: a 1.92-aspect **panoramic**
(`hssd/950c82d2`, 1.00 × 0.52) at `width=1.4` lets the monitor interrupt only a small central strip,
so the artwork reads on both sides and above — *a desk in front of a picture*, as in a real clinic.
**Aspect ratio is a layout property, not a taste one; check it with `get_whd()` before you hang.**

## Step 0 — asset audit (gate 3): four traps caught before the first build
Every hero eyeballed via `browse`/`show` and **dimension-checked offline with `get_whd()`**. This gate
paid for itself four times:

| Trap | What the audit found | Fix |
|---|---|---|
| **Caption lies about COLOUR** | The top two `"olive green armchair"` hits render **yellow** (`future/62c3067f`) and **tan** (`future/2777ee3b`) | Pinned `hssd/f08e9f00` — the one genuinely olive mesh. The palette lives on the chair, so pin it (jewelry_shop) |
| **Scale metadata lies** | DESK natively **0.66 m tall** (a coffee-table-height "counter"); PALM natively **0.55 m** (a tabletop plant) | Uniform height-fit both: `o.scale(o.get_width()*H/o.get_height())` → 1.10 m / 1.75 m |
| **Flat-mesh detonation** | The best magazine mesh (`future/057a6e38`) has **H = 0.00** — `place_on_top` height-fits to a fraction of the anchor height, which would blow a zero-height mesh up in every axis (greenhouse's seed-tray slab) | Pinned `hssd/37ab8971` instead (**H = 0.047**, real 3-D height) |
| **Empty-frame trap ×2** | Half the top framed-print hits preview as **blank white rectangles**; and **6 of the 8 top wall-clock hits are featureless white DISCS** — no face, no hands | Pinned only art with visible artwork, and the one clock (`hssd/e1725f63`) that has a real face |

The clock one is worth its own line: **the empty-frame trap is not specific to picture frames.** Any
"flat round/rectangular thing on a wall" category (clocks, mirrors, signage, boards) is full of meshes
whose *front is blank*. A blank white disc on a wall reads as a dinner plate. **Eyeball the contact
sheet — that IS the gate.**

## What worked / gotchas
- **The category read comes from the CLOCK and the magazines, not the furniture.** A reception desk +
  chairs + plants is a *lobby*. What makes it a **waiting room** is that you *wait*: magazines on the
  low table and a clock on the wall. Both are identity props, and both were added deliberately (the
  jewelry_shop product rule: put the thing the room is *for* at viewing height).
- **The plan's GLASS table rendered as a solid BLACK MONOLITH** (dark glass + a dark lower shelf) — a
  heavy slab in a calm beige clinic, and **nothing flagged it** (geometry is perfect; "that reads as a
  black box" is semantics). Caught in the cheap **phase-1** loop and swapped for an open-frame walnut
  top, which echoes the reception counter and gives the magazines an opaque surface to read against.
  **Dropped the plan's material, kept the plan's warmth** — the form factor of a mesh is a layout
  property (living_room_cozy's corner-fireplace lesson) and phase 1 is where it surfaces.
- **`place_accessories` on a reception counter is height-fit, not `modulate_scale`d.** The "small
  potted plant" came in as a ~0.55 m agave (the tournament sizes on-top items; `modulate_scale` is a
  **no-op** there — tv_studio). It reads fine as a counter plant from the room, so it was kept — but
  its top sits ~1.7 m, i.e. **above the interior camera line**, and a taller one would have blinded
  the back-wall view (bakery). Watch on-top items near a wall-centre fixture.
- **Room size: fill the floor, and stop SHORT of the vote on a row-packed room.** `RoomProportions`
  sat at 0.8–0.9 in every phase. Held per render-wins-early, then **filled** the bare floor with the
  palms + a water cooler (children_room/kindergarten) rather than crushing the shell — because the
  two seat banks are **rigid GridGroup rows** and a shell shrunk below the footprint they dictate
  makes fixed-size rows overflow their slots (locker_room). Applied ONE decisive **0.95**, well short
  of the vote; the vote decayed to 0.95 ≈ neutral → converged. The open centre is also the **walk-up
  lane to the desk** — legitimate circulation that an occupancy metric always reads as "empty"
  (garage/corridor).
- **Clean by construction:** `no rotation` / `no wall overlap` from the **first** phase-1 build to the
  last. The whole loop collapsed to the single room-size thread because every orientation was
  structural: `WorkstationGroup` + `set_rotation(180)` for the inverted reception, and **no `facing=`
  on any wall placement** (the heuristic already turns wall items into the room).
- **Windows: glaze freely.** `place_window_picture(curtain=None)` on the seating wall gives real
  daylight since the 2026-07-12 renderer fix — the old "black night void" workarounds are obsolete
  (greenhouse). The trade-off: the strength-3.0 interior sky **pales the greige walls toward white**.
  That is on-brief here ("daylight drives brightness"); a dimmer envelope would need `IDSDL_SKY` from
  a **shell** build, since MCP `run_scene` binds the sky at import (wine_cellar tooling gotcha).

## VLM feedback log (chronological)
- Ph1 `rescale room by 0.8` → **held** (render-wins-early). `no rotation` / `no wall overlap` from the
  first build.
- Ph1 (rebuild, after the black-slab table swap) `rescale room by 0.9` → held. *The table swap was an
  EYE catch, not a VLM signal.*
- Ph2 `rescale room by 0.8` → held (occupancy still rising). Dressing verified by eye: magazines on
  the table, monitor's screen to the staff and its back to the room.
- Ph3 full `rescale room by 0.9` → **filled the floor instead** (palms flanking reception + entrance
  water cooler), and applied ONE decisive `modulate_scale=0.95` (short of the vote — rigid rows).
- Ph3 re-run `rescale room by 0.95` ≈ neutral → **converged, declined** (executive_office's
  decay-toward-neutral rule).
- The focal-art/monitor collision and the black-slab table produced **no VLM signal at all** — both
  were caught by looking.

## Manual constraints used
- None. Door auto-clearance + the wall-object clearance pass (which correctly left the 0.84 m chair
  banks alone, being well below the art's bottom edge) + `CategoryClearanceConstraint` on the
  reception desk were enough.
