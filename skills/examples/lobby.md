# Lobby (corporate reception) — worked example

Status: built as `scenes/lobby.py`. [`lobby_v1.py`](lobby_v1.py) is that program **phase-gated**
and **verified 2026-07-13**: phase-1 layout pass, then a full rebuild converged clean
(`no rescale / no rotation / no wall overlap`). Two findings from that rebuild:
- **The focal art behind reception hangs CLEAR of the monitor** (the suspected
  art-crosses-the-monitor collision from waiting_room does not occur here — eyeballed in the
  render).
- **A front-wall TV + a lounge FACING it triggers the wall-occlusion WARNING by construction**
  ("AroundGroup occludes wall-hung TV … no along-wall slot can clear it"): seating that watches
  a screen necessarily stands in its wall patch. The render shows the TV fully visible above the
  seat backs — treat this warning as benign FOR A TV + ITS AUDIENCE specifically (it is real for
  art vs tall furniture), and don't let it block a flow gate.

Scene: `scenes/lobby.py` (seed=13), planner-driven **"Polished Corporate Lobby: Reception Anchor +
Open Lounge."** The **single-room, zoned** pattern (same bones as `executive_office.md`): a
**reception anchor** in the back third + an **open waiting lounge** pushed to the front-right so the
desk has a clear walk-up, wrapped in glazing, a wall TV, amenities + decor. Built coarse-to-fine and
iterated on user feedback; final VLM clean (`no rescale` / `no rotation` / `no wall overlap`).

## Prompt this covers
- "a (corporate / hotel / office) lobby / reception / waiting area": a reception desk + a lounge of
  sofas & armchairs around a coffee table, tall plants, big art, floor-to-ceiling windows, a wall TV.

## Layout pattern — reception anchor (back) + waiting lounge (front-RIGHT, not centre)
- **Reception** is a **`WorkstationGroup`** (see the monitor-facing lesson below), dropped in the back
  third with `room.place_on_back(reception, facing="back")` — **`place_on_back`, NOT `place_on_back_wall`**,
  so there's staff space *behind* the desk (a wall-flush desk leaves the receptionist inside the wall).
- **Lounge** is an `AroundGroup.place_rectilinear` — two 3-seat sofas on the long sides + two accent
  armchairs on the short sides around a coffee-table anchor. Auto-faces every seat inward (no per-seat
  `face()`), reads as the classic symmetric waiting cluster. **Push it to `place_on_front_right`, not
  `place_on_center`** — a centred lounge walls the reception desk off behind the seating (you'd have to
  weave through it to reach the desk); front-right leaves an open diagonal walk-up from the entrance to
  the desk. `place_on_top` a vase + books on the coffee table; `place_rug` under it.
- **Amenities / decor:** a wall-mounted TV on the front wall (something to watch), an entrance water
  cooler, a lamp-lit **console vignette** (side table + lamp + books) so an accent table reads with a
  clear *purpose*, tall plants for greenery, a colourful focal artwork behind reception, secondary art
  on the right wall, floor-to-ceiling glazing on a long wall, the entrance door front-**left** (moved
  off-centre to clear the front-centre TV), flush disc ceiling lights.

## The reusable lesson: a desk with a monitor on it → use `WorkstationGroup`
"Monitor seated on a desk, facing the wrong way" recurred for three renders while the reception was a
hand-rolled `RelativeGroup` + `place_on_top(computer)` + a per-scene `face()` — the VLM kept voting
`rotate desktop computer by 180`, and `face(computer, toward="<wall>")` was fragile (the AIO mesh's
geometric front is opposite its screen, and face-to-*wall* snapped inconsistently as the group shifted).

**Fix once and for all: build the desk unit as a `WorkstationGroup`.** It seats the computer with the
DSL's own `place_on_top` and then **`face(computer, toward=chair)`** — pointing the screen at the actual
operator object, deterministically, every build. No wall-guessing, no per-scene `face()`.

```python
with scene.WorkstationGroup() as reception:
    desk = scene.AddAsset("a modern reception desk with a marble front", asset_id=_DESK, width=2.2)
    desk.set_rotation(180)                     # see "reception is an INVERTED desk" below
    reception.set_anchor(desk)
    reception.place_chair(scene.AddAsset("a black leather office task chair on casters"), gap=True)
    reception.place_computer(scene.AddAsset("a desktop computer"))     # screen auto-faces the chair
    reception.place_accessories([scene.AddAsset("a small potted plant")])
...
room.place_on_back(reception, facing="back")   # operator (+Z) to the back wall -> receptionist faces the room
```

**A reception desk is an INVERTED workstation.** `WorkstationGroup` assumes a normal desk: the working
front (+Z) faces the operator, so the nice front and the operator are on the *same* side. A reception
desk is the opposite — the **display front (marble transaction counter) faces the customers**, while the
**staff + monitor sit behind**. Two moves reconcile it:
1. `desk.set_rotation(180)` on the anchor — flips the marble to the customer side and turns the open
   staff side into the group's operator (+Z) side. (An anchor's own rotation is a *local* offset that
   rides along when the group is later rotated for `facing=`, so it survives placement.)
2. place the group `facing="back"` — operator/chair to the back wall, receptionist facing the room —
   the same "power layout" as `executive_office.md`'s `facing="back"`. Result: marble → customers,
   screen → staff (customers see the monitor's back), chair tucked behind. VLM went fully `no rotation`.

## Asset-first kickoff — stress-test retrieval, THEN ingest the hero
The reference for **running a retrieval stress test before building** (the asset-first kickoff done
properly). Retrieve every planned asset, read the top similarity + the visual pick:

| Asset | sim | verdict |
|---|---|---|
| sofa / plant / side table / vase / reception chair / lamp | 0.72–0.83 | ✅ strong |
| coffee table / armchair / art / rug / flush light / wall TV / books | 0.57–0.71 | ✅ usable (rugs always ~0.6) |
| water cooler | 0.62 | ✅ (auto-scale metadata is bad → set `width=0.35`) |
| **reception desk** | 0.69 | ⚠️ ONE wooden option, no marble → **ingest gap** |
| **branded signage / logo** | 0.44–0.52 | ⚠️ gap (no clean corporate logo) |

**Hero = the reception desk**, and the dataset had one (wooden). The user supplied three `.glb`s →
ingested via `python -m IDSDL.ingest reception_tables.zip --manifest m.json` (manifest overrides
`description` → drives the retrieval embedding, `placement=floor`, `scale` = real-world width m). Hero
pinned = **`custom/cffdedd8…`** (wood frame + dark marble panels — nails the "polished stone + warm
wood" palette); two alternates ingested (curved + L-shaped). **Verify ingest previews before trusting
scale** — the auto-render preview, not the vertex bbox, tells you the mesh is right. The **logo gap was
left unfilled** (no per-wall texture exists) — the "focal wall" is a large colourful abstract instead.

## Other gotchas
- **`add_lighting` fixture COUNT is `N = 1 + (max_lights-1)*density`, `max_lights ≈
  ceiling_area / fixture_footprint`.** A *small* flush disc at `density=0.2` in a big lobby exploded to
  **~250 dots**. Fix is two-fold: **enlarge the fixture** (`modulate_scale=2.2` shrinks `max_lights`)
  **and drop density** (`0.03`) → a clean ~9-fixture grid. Energy is a fixed 500 W split across N, so
  fewer fixtures ≠ dimmer. Steer the *mesh* by wording: `"square LED panel"` → a spotlight-on-arm;
  `"flat round LED flush mount"` → the clean disc. [[lighting-footprint]]
- **Floor-to-ceiling window: `curtain=None`.** No exterior environment → the pane is a black night
  void, and every curtain/blind query rendered as **billowing ghost drapes**. Bare glazing reads as a
  clean glass curtain wall (mullions + dark glass). (Prefer `place_window_standard` if you must hide the void.)
- **Pin the sofa to dodge sectionals** (`"a straight modern beige three-seat sofa"` + the 0.82 id), and
  pin a **flat** rug (avoids the upright-slab `place_rug` warning).
- **`AroundGroup.place_rectilinear` is the waiting cluster** — 2 sofas + 2 armchairs auto-faced inward
  in one call; `place_on_top` (vase + books) + `place_rug` decorate/ground it.

## VLM feedback we hit and how we resolved it
- v1 `rescale room 0.9` → `modulate_scale` 1.15→1.0; v2 `rescale coffee table 0.8` → `width` 1.2→0.95.
- v3 `rotate computer/chair 180` → first patched with room-level `face(..., toward=wall)` (worked v4);
  but it **regressed in v5** when the group shifted → the real fix was rebuilding reception as a
  `WorkstationGroup` (above), after which v6 was fully `no rotation`. *Recurring facing votes on a
  desk monitor = reach for `WorkstationGroup`, don't keep patching `face()`.*
- v4 `rotate the front sofa to face the coffee table` → **declined as noise** (the rectilinear sofas
  already face the table in every render; same noise `executive_office.md` declined).
- v5 `rescale room 0.8` (lounge in a corner left the centre empty) → `modulate_scale` 1.0→**0.9**
  (kept some openness for the walk-up).
- Lighting + the window void are **VLM-blind** — judged by eye.

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed. The front-right lounge keeps a clear diagonal
  walk-up from the entrance to the reception desk (the plan's "clear sightlines, no bottlenecks").

## Program

[`lobby_v1.py`](lobby_v1.py) — phase 1 the reception workstation, lounge cluster, console, walls and door; phase 2 the desktop computer + accessories, coffee-table styling, rugs, console lamp and plants; phase 3 the focal and secondary art, wall TV, bare floor-to-ceiling glazing and flush ceiling lights.

`workbench run skills/examples/lobby_v1.py --phase 1` builds the layout alone in ~1–2 min.
