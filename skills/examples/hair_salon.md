---
id: example:hair_salon
kind: example
family: service-spine-counter
category: "hair salon"
pattern: "Motif-group build — `MirrorStationGroup` styling row;"
---
> **Digest (from the pattern index):** **Motif-group build** — `MirrorStationGroup` styling row; canonical coarse-to-fine


# Hair salon — worked example (the canonical coarse-to-fine build)

Status: built as `scenes/hair_salon.py`. [`hair_salon_v1.py`](hair_salon_v1.py) is that program **phase-gated** (2026-07-13): `lint_program`-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record).

The first scene built end-to-end with the **asset-first kickoff** + a **new placement group**, and
the reference example for the **three-phase build** in `../workflow/coarse_to_fine.md`. Read this
alongside that file, `../workflow/asset_selection.md` (kickoff), and `../add-placement-group/SKILL.md`.

## Prompt(s) this covers
- "a pretty hair salon" / styling-row salons, barbershops, blow-dry bars.

## Plan summary
Palette **blush + brass + concrete**. The room wants to be **wide and shallow** (real salons are).
The hero is a **styling row**: a line of identical stations along one long wall, each = a chair
facing a wall mirror with a console under it. The opposite long wall carries the **reception** and a
blush-velvet **waiting nook**; the two short walls stay light (backwash row, retail shelf, openings).

## Assets — kickoff did the heavy lifting (do this first)
- **Mapped ~60 salon items, catalogued the dataset, built a curated pool** → `HairSalonRetriever`
  (pool `assets/hair_salon.json`) with a **general-furniture fallback merge** so e.g. a "blush
  accent chair" still reaches the general pool when the salon pool lacks it.
- **5 high-impact assets were missing → user sourced free glbs → ingested** (`custom/…`): barber
  **styling chair**, **backwash unit**, ornate **arched mirror**, **neon sign**, retail shelf.
  These five unblocked the scene; everything else came from the pool.
- **Pin the styling chair** (`asset_id="custom/59a3f803…"`): the visual picker kept choosing a low
  tub chair; pinning the real barber chair fixed it durably.
- **Mesh-centering gotcha:** the ingested chair/backwash were authored off-center and sat sunk into
  the floor (−0.186 m); fixed by recentering the glbs (ingest now auto-centers — see
  asset_selection.md → ingest contract). Off-center mesh ⇒ floor sink/float is the #1 ingest trap.

## The placement group: `MirrorStationGroup` (why it exists)
Wall-mounting was RoomGroup-only and `RelativeGroup` is floor-only, so "mirror on the wall + chair
facing it + console under it" was **unrepresentable** → it earned a group (the only DSL extension
this scene needed). It builds one station in a local frame whose **+Z is the viewing axis** (anchor
faces +Z; mirror/counter/shelf sit on the +Z wall side, facing back at the anchor), then you drop N
of them in a `GridGroup` row and place the row flush on a wall. Optional slots: `place_counter`,
`place_shelf(shelf, items=[...])`, `place_beside(cart, side=...)` (the **mobile trolley/dresser**
slot). It **auto-fits under the ceiling** (caps the counter to desk height, shrinks the mirror so its
top stays under `max_top`) and **stands the mirror `MIRROR_WALL_OFFSET` proud of the wall** so its
reflective face reads instead of going coplanar. Generalises to **gym treadmill + mirror**, vanities,
dressing rooms.

> A *row of mirrors alone* needs **no** group — `place_on_wall_freeform("back_wall", mirrors)` already
> spaces + scales N wall mirrors. The group is for the chair+console+mirror *relationship*.

---

## Phase 1 — major assets: layout + proportions (long strips on the long edges)
Place only the big pieces, and **load the two long walls** to force the wide, shallow room:
the **styling row** (5 stations) on the **back** long wall, the **reception + waiting nook** on the
**front** long wall, and keep the **short** walls light (backwash, retail). The `RoomGroup` sizes
each wall from what's on it, so this distribution *is* what makes the room wide.

```python
from IDSDL.scene import SceneProgRoom
scene = SceneProgRoom("HairSalonPretty", seed=77)

# back (long) wall: 5 styling stations — the hero row, each its own MirrorStationGroup
def styling_station():
    with scene.MirrorStationGroup() as st:
        st.set_anchor(scene.AddAsset("a salon styling chair",
                                     asset_id="custom/59a3f803acb6e00ec8e3637e862c879cf03c06be"))
        st.place_counter(scene.AddAsset("a narrow styling station console"))
        st.place_mirror(scene.AddAsset("an arched gold-framed salon wall mirror"))
        st.place_beside(scene.AddAsset("a rolling salon tool trolley cart"), side="right")  # Ph2 slot
    return st
stations = [styling_station() for _ in range(5)]
with scene.GridGroup(sparsity=0.4) as spine:
    spine.place_row(stations)

backwash = 2 * scene.AddAsset("a salon backwash shampoo unit")          # short-wall "cabinets"

with scene.RoomGroup(modulate_scale=0.92, randomness=0.12) as room:
    room.place_walls(floor_texture="polished concrete floor",
                     ceiling_texture="white", wall_texture="soft blush pink")
    # FLUSH against the long back wall — place_on_back_wall_center, NOT place_on_back (which leaves a
    # wall-row gap and makes the mirrors look like they float). facing="back" both rotates the spine
    # AND tells the auto-sizer how deep the back row is — so NO redundant room.face() is needed.
    room.place_on_back_wall_center(spine, facing="back")
    # short walls stay light → room comes out wide & shallow
    room.place_on_right_wall_center(backwash[0]); room.place_on_right_wall_right(backwash[1])
    room.place_on_left_wall_left(scene.AddAsset("a salon retail product display shelf"))
```

**Phase-1 checks:** room is visibly wide/shallow; the 5 stations sit flush (no floating mirrors,
no mid-room overlap — verify numerically if a corner perspective *looks* like overlap); proportions
clean. This is where the floating-mirror, mid-room-overlap, and redundant-render bugs were all caught
and killed (see gotchas).

## Phase 2 — surface & floor details (what sits on / beside the anchors)
Build the reception and waiting clusters with their on-surface and beside-anchor detail, and place
them on the **front** long wall. Each is a `RelativeGroup` with `place_on_top` / `place_on_back` /
`place_rug` / `add_lighting`. (The per-station trolley from Phase 1's `place_beside` is also this
layer.)

```python
with scene.RelativeGroup() as reception:                       # prominent: scale the desk up to >=2.2m
    desk = scene.AddAsset("a large curved salon reception desk")
    w0, h0, d0 = (float(v) for v in desk.get_whd()); f = max(2.2 / max(w0, 0.1), 1.0)
    desk.scale_only_width(w0*f); desk.scale_only_height(h0*f); desk.scale_only_depth(d0*f)
    reception.set_anchor(desk)
    reception.place_on_back(scene.AddAsset("an ergonomic reception office chair"))   # receptionist
    reception.place_on_right(scene.AddAsset("a tall potted plant"))                  # greenery
    reception.place_on_top(scene.AddAsset("a small decorative flower vase"))         # on-desk decor
    reception.add_lighting("a brass pendant light", density=0)

with scene.RelativeGroup() as waiting:                         # blush pair + brass table + rug
    side = scene.AddAsset("a round brass side table"); waiting.set_anchor(side)
    tubs = 2 * scene.AddAsset("a blush old-rose velvet accent chair",
                              asset_id="hssd/3b522b2a379a3a5248dbaa0159cc5ddfbf43a2e0")
    waiting.place_on_left_further(tubs[0]); waiting.place_on_right_further(tubs[1])
    waiting.face(tubs[0], toward=side); waiting.face(tubs[1], toward=side)
    waiting.place_on_top(scene.AddAsset("a gold magazine rack"))
    waiting.place_rug("a soft blush wool area rug", size=0.8)
    waiting.add_lighting("a brass pendant light", density=0)

# inside the RoomGroup, on the front long wall:
    room.place_on_front_left(reception, facing="back")
    room.place_on_front(waiting)
```

**Phase-2 checks:** details sit where intended (vase on desk, plant beside it, rug under the nook),
nothing floats/clips, small-item proportions clean.

## Phase 3 — walls, decor & openings (close the gap to the prompt)
Wall art that *signals the room type*, signage, the door and the window+curtain — the cheapest-impact
layer, last. Added inside the `RoomGroup`:

```python
    room.place_on_wall_front_left(scene.AddAsset("a large framed fashion portrait of an elegant woman"))
    room.place_on_wall_front_center(scene.AddAsset("a neon salon sign"))
    room.place_door("left_wall", position="right")
    room.place_window_standard("right_wall", position="center", curtain="sheer white curtains")
scene.export("hair_salon.blend")
```

**Phase-3 checks:** `WallOverlapConstraint` (art not colliding with door/window), and the final
interior renders read unmistakably as a *beauty* salon (the woman portrait + neon do that work).

---

## What worked / gotchas (the whole journey)
- **Long strips on long walls = wide room.** Loading both long walls (stations / reception+waiting)
  and keeping short walls light is what produced the salon's wide-shallow footprint. The room shape
  is a *consequence of asset distribution*, not a separate dial.
- **Flush, not gapped.** `place_on_back_wall_center(spine, facing="back")` seats the row ON the wall;
  `place_on_back` leaves a wall-row-deep gap → mirrors look like they float. This was the #1 layout fix.
- **`facing=` already does the job; `room.face()` is redundant for this.** `facing=` sets the rotation
  *and* informs the auto-sizer; the post-layout `room.face(spine, toward="back_wall")` just re-snapped
  the same orientation and was removed. Don't stack both.
- **Deterministic groups should set `self.vlm_solver = None`.** Each `MirrorStationGroup` is hand-laid
  and identical, so the per-instance VLM render was pure waste — it re-rendered the same station 5× and
  starved the renders you actually wanted to see. Disabling it cut renders ~35→15.
- **Mirror standoff.** A wall-coplanar mirror blends in and shows no reflection; the group now stands
  it `MIRROR_WALL_OFFSET` proud of the wall toward the anchor so the glass reads (casts a soft shadow).
- **Per-station = one `MirrorStationGroup`, rowed by `GridGroup`.** An earlier attempt (chair anchor +
  `place_on_front_adjacent(counter)` in a `RelativeGroup`) made chairs **vanish** — the dedicated group
  lays each station out deterministically and survives the row + flush placement.
- **Pin retrieved hero assets the picker drifts on** (the styling chair).

## VLM / layout feedback we hit and how we resolved it
- **"mirror top breaches the ceiling"** (tall console pushed the mirror to ~3 m) → group auto-fits:
  console capped to desk height + mirror shrunk so its top ≤ `max_top` (≈2.7 m under a 3 m ceiling).
- **"chair sunk into floor (−0.186 m)"** → off-center ingested mesh; recenter the glb (ingest now
  auto-centers).
- **"stations look like they're in the middle of the room / overlapping"** → a *corner-perspective
  illusion* in a wide-shallow room; a numeric dump (mirror z≈0, no AABB overlap) proved the geometry
  was correct. When a render *looks* wrong but the call is right, verify numerically before "fixing."
- **"room reads a touch empty"** → nudged `modulate_scale` 0.78 → 0.92 (smaller room for the same
  furniture). Minor.

## Manual constraints used
- None required; the auto overlap/bounds + the group's deterministic layout sufficed.

## Program

[`hair_salon_v1.py`](hair_salon_v1.py) — phase 1 the five-station mirror spine (the mirror itself is ungated — MirrorStationGroup requires place_mirror before compile), backwash pair, retail shelf, reception and waiting pair, walls and door; phase 2 the trolleys, desk vase, magazine rack, blush rug and plant; phase 3 the fashion portrait, neon sign, window and brass pendants.

`workbench run skills/examples/hair_salon_v1.py --phase 1` builds the layout alone in ~1–2 min.
