---
id: example:nursery
kind: example
family: hero-anchor-room
category: "nursery / baby room"
pattern: "Four walls, four jobs, an empty middle"
read_for:
  - "READ FOR ANY PALE OR PASTEL ROOM: an all-white room is an EXPOSURE trap — a big window + the default sky 3"
---
> **Digest (from the pattern index):** **Four walls, four jobs, an empty middle** — low sleep hero (crib + art above) / changing station (dresser + mirror) / caregiver nook on a rug under the window / low storage by the door; kid scale keeps everything under the 1.4 m cameras ⇒ rotation-clean by construction. **READ FOR ANY PALE OR PASTEL ROOM: an all-white room is an EXPOSURE trap** — a big window + the default sky 3.0 bouncing off white walls/floor/furniture blows the room to pure white and the loop says nothing; drop `IDSDL_SKY` (~1.2) and note it works from the SHELL but is IGNORED by MCP `run_scene` (A/B verified — corrects the dining_room note). Also: a pastel wall texture fails twice ("blush pink wall" → pink TILES; "pale pink plaster" → a peach that renders SALMON — pick one notch PALER); **bad PROPORTIONS can't be scaled away** (a "small side table" that is a 1.20×0.55 coffee table — swap the mesh, unlike a bad-*scale* asset); an unpinned "plush bunny" that is a **flat cardboard slab with a BLANK desc** (a blank desc column = a junk pick); and a **DSL gap** — baby mobiles EXIST but are unplaceable (too deep to wall-hang, and `add_lighting` is the only ceiling verb, which would make it emit)


# Nursery — worked example

Scene: `scenes/work/nursery.py` (seed=12), planner-driven **"Sunlit Pastel Nursery"**, built through
the guided 9-gate flow. The **residential kid-scale** pattern: a low **sleep hero** (crib) on the main
wall, a **changing station** (dresser + mirror) on the opposite wall, a **caregiver nook** (glider +
pouf + lamp table) on a rug under the window, and a **low storage run** by the door. Converged clean
(`no rotation` / `no wall overlap`, zero lints) with the room vote decaying `0.75 → 0.9 → 0.95 → 0.9`
to neutral.

## Prompt this covers
- "a nursery / baby's room": crib, changing table, rocking chair or glider, toy storage, soft rug,
  pastel walls, sunlit. Also the general shape of any **small pastel kid-scale room**.

## Layout pattern — four walls, four jobs, and a deliberately empty middle
- **BACK wall = SLEEP.** The crib (`place_on_back_wall_center`) as a `RelativeGroup` carrying the
  room's single flush ceiling fixture. A soft floral print hangs **above it**
  (`place_on_wall_back_center`) — wall-hung art and wall-adjacent floor furniture occupy independent
  slots, so this stacks cleanly (the living_room_cozy hearth+gallery pattern).
- **LEFT wall = the WINDOW + the caregiver nook.** `place_window_picture` (glaze freely — the black
  void is fixed) with sheer curtains, and the nook placed *wall-adjacent*, not in a floor slot.
- **RIGHT wall = CHANGE.** The dresser as its own group (linens + basket ON TOP), round mirror above.
- **FRONT wall = STORE + the door.** Low cubby in one third, door in the other, art on the centre.
- **The middle stays EMPTY on purpose** — it is the play/circulation floor the category exists for,
  and an occupancy metric always reads it as "too big" (garage's vehicle lane, corridor's centre lane).

Every fixture is kid-scale (crib 1.04 m, dresser 0.95 m, cubby 0.91 m, rocker 0.99 m), so **nothing
reaches the ~1.4–1.5 m interior wall cameras** — kindergarten's rule applied *preventively*: no blinded
view, and therefore no hallucinated rotation storm (bakery). `no rotation` from the first build to the
last.

## Lessons this scene encodes

### 1. An ALL-WHITE room is an exposure trap — the pastel envelope washes out to pure white
The first full build came back **blown to white**: a big picture window + the default
`INTERIOR_SKY_STRENGTH` of 3.0, bouncing around a room whose walls, floor, crib, rocker, rug and pouf
are *all* white/cream. Every surface is a reflector, so the room integrates to white and the blush
walls vanish. No signal fires — the VLM loop was clean (`no rotation` / `no wall overlap`), because
exposure is not geometry. → `os.environ.setdefault("IDSDL_SKY", "1.2")` **before importing IDSDL**
restored a daylit room whose pastels hold. This is wine_cellar's dark-room lesson **inverted**: a pale
room needs the sky DROPPED just as a cellar does, for the opposite reason (nothing absorbs). Rule of
thumb: **the paler the room, the lower the sky.** Brightness is *only* ever a sky/`light_budget`
setting — `add_lighting` spends a fixed 500 W split across N fixtures, so `density` can never dim or
brighten anything.

### 2. TOOLING — `IDSDL_SKY` works from the shell and is IGNORED by MCP `run_scene` (A/B verified)
Confirms wine_cellar's gotcha with a clean experiment, and **corrects** the dining_room note that says
the in-program line "is a no-op inside the program under workbench too" — it is not:

| harness | in-program `IDSDL_SKY=1.2` | result |
|---|---|---|
| `python workbench.py run …` (shell) | yes | correctly exposed, pastels hold |
| MCP `run_scene` | yes, *same file* | **blown white** |

The only variable was the harness. (`sceneprogexec` spawns Blender with `subprocess.run(cmd, cwd=…)`
and **no `env=`**, so the child inherits `os.environ` and re-imports the renderer fresh — which is why
the shell path works even though `INTERIOR_SKY_STRENGTH` is a class attribute bound at import. The MCP
server's warm render path does not deliver it.) → **Build any mood/exposure-dependent scene from the
SHELL**, and distrust a surprising `run_scene` exposure.

### 3. A pastel wall is TWO texture traps deep — settle it offline
`wall_texture` is embedding-matched against **caption text**, and pastels fail twice:
- `"soft blush pink painted wall"` → **pink bathroom TILES**. A tiled nursery — the prison_cell
  wrong-kind-of-object failure, at texture level.
- `"plain pale pink painted plaster wall, smooth and uniform"` → a genuine **peach paint** swatch…
  which rendered as strong **SALMON** at room scale. Note the direction: the render came out *more*
  saturated than the swatch, the **opposite** of bakery/office_modern's "room-scale tiling washes dark
  tones OUT".
- `"very pale barely-there pink white wall, almost white"` → a desaturated dusty blush that **holds**.

→ **For a pastel, pick a swatch one notch PALER than the colour you want**, and open the matched
`texture.png` offline (5 s) before paying for a build. Both failures are invisible to every constraint.

### 4. Only `place_on_top` a prop you have VERIFIED — a "plush bunny" that was a cardboard box
The unpinned `"a plush stuffed bunny toy"` resolved to a **0.60 × 0.68 × 0.12 m flat slab with a BLANK
description**, and rendered as a **cardboard box standing on the cubby**. The whole VLM loop ran clean
through it (`no rescale` / `no rotation` / `no wall overlap`, zero lints) — the geometry is fine, and
*"that is not a bunny"* is semantics. Kindergarten's crayon-cup rule at full strength, with a new tell:
**a blank `desc` in the printed asset list is self-identifying evidence of a junk pick — read that
column every build.** Caught by eye in the render; fixed by pinning a real pastel plush.

### 5. Wrong PROPORTIONS cannot be scaled away — swap the mesh
The unpinned `"a small round light wood side table"` came back **1.20 × 0.55 m — a COFFEE table** that
dwarfed the glider beside it. It cannot be rescued by scaling: uniform-scaling it to a 0.5 m width
gives a 0.23 m *height* (a footstool), and height-fitting it to 0.5 m gives back a 1.09 m width. A
mesh's **aspect ratio is an identity**, not a parameter. → Swapped for a genuine pedestal table
(0.60 × 0.77) and height-fit it to 0.60 m. (Contrast the bad-*scale* cases — hospital bed, garage car,
bean bag — where a uniform `modulate_scale` IS the fix. Bad scale is fixable; bad proportions are not.)

### 6. The picker's rank-1 "nursery animal print" is a row of framed INSECT SPECIMENS
And its runner-up previews as a **blank white rectangle** (the office_modern empty-frame trap). Both
would have shipped silently. **Eyeball the contact sheet — that IS the gate.** Pinned two prints with
real, soft artwork.

### 7. A dataset asset can exist and still be UNPLACEABLE — the crib mobile (DSL gap)
The single most iconic nursery prop after the crib. Baby mobiles genuinely exist — a whole
`CeilingObjectRetriever` pool, six candidates at 0.57–0.68 — and **not one can be placed**:
- `place_on_wall_*` needs a **flat** mesh (< ~0.25 m deep); every mobile is **0.36–2.80 m deep** (a
  dangly 3-D object by nature — scaling it down to fit makes it invisible), and their scale metadata is
  wild (one loads 2.80 m across).
- `add_lighting` is the **only** ceiling-hang verb, and it would make the mobile **EMIT** — plus it caps
  a fixture's height at 1.5 m while pinning the origin at the ceiling, so it would dangle into the room
  (executive_office's chandelier ban).

→ Dropped it, and the room still reads (the crib is decisive). **Logged as a genuine DSL gap: there is
no verb for a non-luminous ceiling-suspended object.** A `place_on_ceiling(obj, drop=…)` would unlock
mobiles, hanging plants, pendants-as-decor and ceiling fans. Verify a prop is *placeable*, not merely
*present*, at the audit gate.

### 8. Room size — fill the floor, then stop
The shell auto-sized to **6.44 × 4.85 m = 31 m²** — a hall, for a category whose real size is ~12–16 m².
Acted in **phase 1** rather than holding to the final phase, deliberately: the hold-early rule exists
because occupancy *climbs* as furniture lands, but phases 2–3 here add only surface dressing and wall
art — **zero floor furniture** — so the vote could not move. One decisive `modulate_scale=0.8`, then the
vote decayed `0.9 → 0.95 → 0.9` and bounced at neutral = converged (declined the residual). The last
mild vote was answered the documented way — **filled the floor** with a wicker toy basket rather than
shrinking onto a play space that is the category (children_room/kindergarten).

## Asset coverage
Excellent — no ingest needed. Cribs, nursery gliders, changing dressers, kid cubbies, knit poufs, shag
rugs, plush toys, woven baskets and pastel prints all exist at good similarity. **Pinned for palette,
form or because the picker was wrong:** crib, dresser, glider, cubby, pouf, rug, both prints, mirror,
both plushes, linens, baskets, side table. The only unpinned picks are the lamp, plant and flush
fixture (proven queries from living_room_cozy).

Verify a real dimension with `get_whd()` **offline, before the first build**, for every pinned hero —
it caught the nightstand-sized "wide dresser" (0.80 m → height-fit to 0.95 m), the coffee-table "side
table", and the unplaceable mobiles, all for free.

Palette: pale blush walls, pale oak floor, white/cream furniture, light wood, warm lamp.
