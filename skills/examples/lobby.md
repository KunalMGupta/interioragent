# Lobby (corporate reception) — worked example

Scene: `scenes/lobby.py` (seed=13), planner-driven **"Polished Corporate Lobby: Reception Anchor +
Open Lounge."** The **single-room, zoned** pattern (same bones as `executive_office.md`): one
**reception anchor** in the back third + an **open waiting lounge** dead-centre, wrapped in glazing +
decor. Built coarse-to-fine; final VLM clean (`no rescale` / `no rotation` / `no wall overlap` at
every level).

## Prompt this covers
- "a (corporate / hotel / office) lobby / reception / waiting area": a reception desk + a lounge of
  sofas & armchairs around a coffee table, tall plants, big art, floor-to-ceiling windows.

## Layout pattern — reception anchor (back) + waiting lounge (centre)
- **Reception** is a `RelativeGroup` (anchor = the desk): staff chair `place_on_back` (behind the
  desk), computer + small plant `place_on_top`. Dropped in the back third with
  `room.place_on_back(reception, facing="front")` — **`place_on_back`, NOT `place_on_back_wall`**, so
  there's staff space *behind* the desk (a wall-flush desk leaves the receptionist inside the wall).
- **Lounge** is an `AroundGroup.place_rectilinear` — two 3-seat sofas on the long sides + two accent
  armchairs on the short sides, around a coffee-table anchor. This auto-faces every seat inward (no
  per-seat `face()` needed) and reads as the classic symmetric lobby waiting cluster. `place_on_top`
  a vase on the coffee table; `place_rug` under the whole thing.
- **Perimeter:** tall plants in both back corners, a side table in a front corner, a colourful focal
  artwork on the back wall behind reception, secondary art on the right wall, floor-to-ceiling
  windows on a long wall, the entrance door front-centre, flush ceiling lights.

## Asset-first kickoff — stress-test retrieval, THEN ingest the hero
This scene is the reference for **running a retrieval stress test before building** (the user asked
for it explicitly, and it's the asset-first kickoff done properly). Retrieve every planned asset and
read the top similarity + the visual pick:

| Asset | sim | verdict |
|---|---|---|
| sofa / plant / side table / vase / reception chair | 0.74–0.83 | ✅ strong |
| coffee table / armchair / wall art / rug / flush light | 0.57–0.71 | ✅ usable (rugs always score ~0.6) |
| **reception desk** | 0.69 | ⚠️ ONE wooden option, no marble → **ingest gap** |
| **branded signage / logo** | 0.44–0.52 | ⚠️ gap (no clean corporate logo; only "Welcome"/retro signs) |

The lobby's **hero is the reception desk**, and the dataset had exactly one (wooden, curved). The
user supplied three `.glb`s → ingested via `python -m IDSDL.ingest reception_tables.zip --manifest m.json`
with a manifest overriding `description` (drives the retrieval embedding) + `placement=floor` +
`scale` (real-world width, m). Hero pinned = **`custom/cffdedd8…`** (wood frame + dark marble front
panels — nails the plan's "polished stone + warm wood" palette). Two alternates also ingested
(a curved welcome desk, an L-shaped slatted desk). **Verify ingest previews before trusting scale:**
the auto-render preview (not the vertex bbox) is what tells you the mesh looks right; low-poly vertex
scatter is too ambiguous. The **logo gap was left unfilled** — no per-wall texture exists, so the
"focal wall" is done with a large colourful abstract art instead.

## Working program (final)
```python
_DESK   = "custom/cffdedd8d354e346e510f227b4a6bc5b65dc3dcb"  # INGESTED wood+marble reception desk (hero)
_SOFA   = "hssd/05206ad5b8ad9956a076ab73038089b964ddb2fd"    # straight beige 3-seat (0.82; pin to dodge sectionals)
scene = SceneProgRoom("Lobby", seed=13)

with scene.RelativeGroup() as reception:                     # reception anchor
    desk = scene.AddAsset("a modern reception desk with a marble front", asset_id=_DESK, width=2.2)
    reception.set_anchor(desk)
    chair = scene.AddAsset("a black leather office task chair on casters")
    reception.place_on_back(chair)                           # staff side (space behind the desk)
    computer = scene.AddAsset("a desktop computer")
    reception.place_on_top([computer, scene.AddAsset("a small potted plant")])

with scene.AroundGroup(sparsity=0.4, jitter=0.3) as lounge:  # symmetric waiting cluster
    coffee = scene.AddAsset("a low minimalist wood coffee table", asset_id=_COFFEE, width=0.95)  # VLM: coffee ×0.8
    lounge.set_anchor(coffee)
    lounge.place_rectilinear(longer_side1=[SOFA], longer_side2=[SOFA],
                             shorter_side1=[ARMCHAIR], shorter_side2=[ARMCHAIR])  # auto-faces seats inward
    lounge.place_on_top(scene.AddAsset("an elegant white ceramic vase with branches", asset_id=_VASE))
    lounge.place_rug("a flat beige wool area rug", size=0.95, asset_id=_RUG)

with scene.RoomGroup(modulate_scale=1.0, randomness=0.12) as room:   # 1.0 = acted on VLM "rescale room 0.9"
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white ceiling", wall_texture="warm greige painted wall")
    room.place_on_back(reception, facing="front")            # back third; desk front faces the room
    room.face(chair, toward="front_wall")                    # receptionist faces the entrance
    room.face(computer, toward="back_wall")                  # screen faces the staff, not the customers
    room.place_on_center(lounge, facing="front")
    room.place_on_back_left_corner(TALL_PLANT); room.place_on_back_right_corner(TALL_PLANT)
    room.place_on_front_left_corner(SIDE_TABLE)
    room.place_on_wall_back_center(scene.AddAsset("...colourful abstract art...", asset_id=_FOCAL, width=1.8))
    room.place_on_wall_right_center(scene.AddAsset("...abstract art...", asset_id=_ART, width=1.2))
    room.place_window_floor_to_ceiling("left_wall", curtain=None)   # bare glazing (see lesson)
    room.place_door("front_wall", position="center")
    room.add_lighting("a flat round LED flush mount ceiling light", density=0.03, modulate_scale=2.2)
scene.export("lobby.blend")
```

## What worked / gotchas
- **`add_lighting` fixture COUNT is `N = 1 + (max_lights-1)*density`, and `max_lights ≈
  ceiling_area / fixture_footprint`.** A *small* fixture (a flat flush disc) at `density=0.2` in a
  big lobby exploded to **~250 tiny dots** carpeting the ceiling. The fix is TWO-fold: **enlarge each
  fixture** (`modulate_scale=2.2`, which shrinks `max_lights`) **and drop density low** (`0.03`) → a
  clean ~9-fixture grid. Energy is a fixed 500 W split across N, so fewer fixtures ≠ dimmer. Also
  **pick the fixture by mesh, not by words:** `"a large square LED flush ceiling light panel"`
  retrieved a *spotlight-on-an-arm*; `"a flat round LED flush mount ceiling light"` is the clean disc.
  (`add_lighting` takes only a `desc`, no `asset_id`, so you steer it by wording + `modulate_scale`.)
  Generalises the exec-office "flush, not a chandelier" rule with the *count* math. [[lighting-footprint]]
- **Floor-to-ceiling window: use `curtain=None`.** With no exterior environment the pane is a black
  night void, and every curtain/blind query (`"sheer white curtains"`, `"light grey window blinds"`)
  rendered as **billowing ghost drapes** over it. Bare glazing reads as a clean modern glass curtain
  wall (mullions + dark glass) — far better than the ghost cloth. (If you need to hide the void, prefer
  `place_window_standard` — a smaller pane — over a dressed floor-to-ceiling one.)
- **Reception desk needs staff space: `place_on_back`, not `place_on_back_wall`.** Flush-to-wall the
  chair `place_on_back` puts the receptionist *inside* the wall. Drop the whole reception group in the
  back third instead, and hang the focal art on the wall behind it.
- **Reception facing is orthogonal, fixed at ROOM level.** The desk front (marble) faces the room via
  `place_on_back(reception, facing="front")`, but the on-top **computer's screen** came out facing the
  *customers* and the chair the wrong way (VLM: `rotate ... by 180` on both). `face(obj, toward="<wall>")`
  only works inside a `RoomGroup`, so orient the leaves there: `room.face(chair, toward="front_wall")`
  (staff faces the entrance) + `room.face(computer, toward="back_wall")` (screen faces staff). A
  face-to-wall snaps to 90° — clean for a desk setup. Note `face_towards` points an object's **front**
  at the target: a computer's front is its screen, a chair's front is its seat.
- **Pin the sofa to dodge sectionals.** `"a modern lounge sofa"` kept returning L-shaped sectionals;
  `"a straight modern beige three-seat sofa"` + pinning the 0.82 hit gets a clean straight 3-seater
  for the symmetric `place_rectilinear` cluster. Pin a **flat** rug too (the retrieved beige rug was
  flat — no upright-slab `place_rug` warning).
- **`AroundGroup.place_rectilinear` is the lobby waiting cluster.** Two sofas + two armchairs around a
  coffee table, auto-faced inward — one call, no per-seat `face()`. `place_on_top`/`place_rug` on the
  group decorate the anchor + ground the cluster.

## VLM feedback we hit and how we resolved it
- v1 `rescale room by 0.9` → `modulate_scale` 1.15 → **1.0** (the room read a touch empty; converged).
- v2 `rescale coffee table by 0.8` → `width=1.2` → **0.95** (matched the eye — the pinned coffee table
  rendered dining-table-sized until scaled).
- v3 `rotate office task chair by 180` + `rotate desktop computer by 180` → the reception staff setup
  faced out; fixed with the room-level `face(..., toward=wall)` pair above (a *consistent* two-object
  180 vote is signal, not the lone-chair noise the computer_room warned about). **v4 confirmed clean**
  (`no rotation` at reception).
- v4 `rotate the front beige three-seat sofa to face the coffee table` → **declined as noise.** The
  `place_rectilinear` sofas already face the coffee-table centre in every render; a lone sofa-face-table
  vote against what the renders show is the same noise `executive_office.md` declined. Don't re-render for it.
- Lighting + the window void are **VLM-blind** (it never commented) — judged by eye from the renders.

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed. The lounge sits centre with open circulation to
  the reception and entrance (the plan's "clear sightlines, no bottlenecks").
