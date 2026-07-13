# Modern private office — worked example (single hero work zone + storage backbone)

Status: **built & VLM-clean** (`scenes/office_modern.py`, seed=21, 4 render passes: 2× phase-1,
phase-2, 3× full). Final compile: `no rotation`, `no wall overlap`, no `[Lint]`/`WARNING` lines;
the only open thread was the room-size vote, converged with ONE decisive `modulate_scale=0.8`.

## Prompt(s) this covers
- "a modern office", "a private office / home office / study" **without a lounge zone** — the
  small-room sibling of `executive_office.md` (which adds a sofa/accent-chair lounge and is the
  one to copy when the brief is bigger or more corporate).

## Plan summary
Planner → **"Daylight-Driven Green-Enclosed Office Nook"**: a saturated green wall wrapping a
warm-wood desk under a window, monitor kept clear of clutter, slim storage flanking, a textured
rug zoning the workspace, a tall plant tying the room to nature, layered light (daylight + task
lamp). Warm wood + green + black + greenery.

## The layout idea: ONE hero zone, a storage backbone, and two deliberately light walls
The private-office signature is a single zoned room — don't over-furnish it:
- **CENTER = the hero work zone.** A `WorkstationGroup` (desk anchor + task chair + all-in-one
  computer + task lamp + pen cup) on its own rug, placed `facing="back"` so the operator sits on
  the storage side and looks OUT at the window wall (the +Z-operator rule, reconfirmed).
- **BACK wall = the storage backbone**, but pushed to the CORNERS: bookcase LEFT, filing cabinet
  RIGHT, **back-center left empty**. See the camera gotcha below — this is not a style choice.
- **FRONT wall = daylight** (a STANDARD punched window + the tall plant beside it).
- **LEFT / RIGHT = the light walls** — one framed print each, plus the door. Two items per wall,
  never more (the overloaded-wall rule inflates the shell).

Five occupied floor slots ⇒ the shell auto-sizes to a cozy private office by construction.

## Pinned assets (audited by eye, then measured with `get_whd()` before the first build)
- **Desk** `future/4d763507-ca63-437a-827e-e66fcececbe8` — warm-wood flat top, black metal legs,
  1.80×0.72×0.90 (a real desk height).
- **Task chair** `hssd/2502dd408e62b2aa751080d4555d9b126f5a8d22` — black mesh-back on castors,
  0.50 m native → `scale(0.6)` (~1.0 m tall).
- **Bookcase** `hssd/2e29b3aa38387e1a9682778d64f27e8a9ec40296` — 0.80×2.17, shelves **filled with
  books** (the identity prop — see below).
- **Filing cabinet** `hssd/8090916af54ef2700b78f6a3ed489b4ab21f54a3` — black 3-drawer, 0.40 m
  native → `scale(0.5)`.
- **Plant** `future/f3a1cc15-c18b-49e7-be30-8f7698a26129` — fiddle-leaf fig, white ceramic pot;
  only 0.95 m native → uniform height-fit to ~1.6 m for the plan's "tall plant".
- **Computer** `hssd/d41c6620aab11d8fde10b5e24b37b38e3c928c5b` — an iMac-style all-in-one that
  **bundles screen + keyboard + mouse** (the dataset has essentially no standalone keyboard).
- **Art** `hssd/b9c49bfce9696145e4328cd3e23b5b3e9eeb5b78` + `hssd/18a5ab4d9f66855d5fcf59051ec83820a4a49f14`
  — both genuinely FLAT (d = 0.05 / 0.02 m) and both with **visible artwork**.

## What worked / gotchas

- **Keep the BACK-WALL CENTER empty when the backbone is tall.** The interior cameras sit at each
  wall's center at ~1.4–1.5 m, so a 2.17 m bookcase at `back_wall_center` would sit *in* the back
  camera — the bakery failure (a garbage view that also hallucinates rotation flags on a correct
  layout). Splitting the backbone to `back_wall_left` (bookcase) + `back_wall_right` (filing
  cabinet) kept all four views clean and gave `no rotation` from the first build to the last.
  **Design the wall so the camera can see the room**, not just so the furniture fits.
- **The empty-frame trap, caught at AUDIT time.** The rank-1 pick for "a large framed abstract wall
  art print in warm tones" (`hssd/fd940fdb…`) previews as a **blank white rectangle**. That is the
  living_room_cozy v2 asset class — an empty frame and a reversed front look identical from behind,
  and `RotationConstraint` never flags either. Dropped it at the contact sheet for two prints with
  real artwork. **Eyeballing the previews is what makes this a 30-second fix instead of a
  post-build mystery.**
- **A "low filing cabinet" query is a retrieval gap.** It returned a tall apothecary-style cabinet
  plus several blank-preview meshes. `browse` over 18 file cabinets surfaced a real black 3-drawer
  unit immediately. When a *type* keeps coming back wrong, browse by hand and pin — don't reword.
- **Books on the shelves ARE the office.** The bookcase was pinned specifically because its shelves
  are modelled full (jewelry_shop's product rule applied to a workroom): an empty bookcase reads as
  a furniture showroom. Same for the desk — screen + keyboard + mouse + pencils in a pen cup + a
  task lamp is what makes it read *worked-at* rather than staged.

## VLM feedback we hit and how we resolved it
- **Room size — one decisive application, then decline the bounce.** Vote train `0.67` → `0.7`
  (Ph1) → `0.8` (Ph2), unidirectional and decaying = converging (living_room_cozy). Held through
  phases 1–2 per render-wins-early, then applied ONE `modulate_scale=0.8` in the final phase —
  picked **at** the latest vote, not below it (bakery). The vote then bounced `0.92` / `0.8` /
  `0.85` across identical builds → **declined as noise** (a vote that oscillates after you act is
  the stop signal).
- **`no rotation` / `no wall overlap` from the first build to the last** — clean by construction:
  `WorkstationGroup` (pose correct by construction) + `facing` omitted on every wall placement +
  door and art in disjoint wall slots. Copying the worked-example defaults collapsed the whole
  feedback loop to the single room-size thread (same effect as laundromat/classroom).

## The texture lesson this scene sharpens (a MATCHING bug and a RENDERING limit look identical)
Three wordings for the plan's green wall, and they separate the two failure modes cleanly:

| Wording | Matched caption | Rendered |
|---|---|---|
| `"deep green painted wall"` | a **pale** green stucco (0.53) | **beige** — a WORDING bug |
| `"a dark olive green color with subtle irregular brush stroke patterns"` | the library's **darkest** green (0.82) | **grey-taupe** — a RENDERER limit |
| `"solid deep green smooth uniform wall"` ✅ | "solid deep green, smooth and uniform" (0.70) | a true green that **holds** |

Two takeaways. **(1) Verify the match OFFLINE instead of burning 8-minute builds on re-wordings** —
embed the query against `IDSDL/assets/wall_textures_embeddings.npz` and read the winning caption
(~5 seconds). **(2) A correct match is NOT a guarantee of the colour you asked for**: the room-scale
tiling + fixed light budget wash *dark* tones out (the bakery brick lesson, now confirmed on a
second colour family). So when the match is already right and the render is still wrong, stop
re-wording — pick a value that **survives the wash**, or carry the accent on a prop instead.
Corollary: texture strings are matched against the library's **caption text**, so word them like a
caption ("solid deep green, smooth and uniform"), not like a paint chip ("deep forest green").

## Asset gaps (LOW risk — the office pool covers this well)
No ingest. Genuine gaps, all substituted: no cowhide rug (the plan's cowhide → a beige woven rug
with an abstract brown pattern; note `place_rug` takes a *description*, not an id, so it can't be
pinned); no standalone keyboard/mouse (the all-in-one bundles them); the "warm abstract print"
top pick is an empty frame (swapped for prints with real artwork).

## Manual constraints used
- None. Auto overlap/bounds + the automatic door clearance + the automatic wall-object clearance
  (which keeps the two prints visible) were sufficient for a single-zone room.
