# Wine cellar — worked example ("Chandelier-Centered Vaulted Wine Cellar")

Built end-to-end through the 9-gate flow from the planner target
(`tmp/plan_A_wine_cellar__stone_brick_vault/plan.png`). Program: `scenes/work/wine_cellar_v1.py`
(seed=21), copied here as `wine_cellar_v1.py`. Layout is the **library corridor** skeleton, so read
that one first — this file exists for the thing the library never had to solve: **a deliberately DIM
room**. It is the reference for any moody brief (cellar, bar, cinema, speakeasy, nightclub).

## Prompt(s) this covers
- "a wine cellar" / wine tasting room / bottle vault / any cellar-y storage-plus-tasting brief.

## Plan summary
Perimeter wine racks wrapping a stone/brick vault as a gallery of bottles; a heavy oak tasting table
on the centre axis under warm dim light, set with a decanter and stemware; oak barrels and weathered
crates as rustic accents. Palette: warm brick, deep walnut, bottle-glass, brass.

## THE layout: the library corridor, one-for-one
Perimeter storage + a central table = the library's symmetric-corridor pattern. Copying it collapsed
the whole layout thread to zero iterations (`no rotation` / `no wall overlap` from the FIRST build):
- **LEFT + RIGHT (long) walls = twin `GridGroup.place_row(4 * rack)` runs**, `facing` OMITTED (the
  heuristic turns the bottle faces into the room). Loading the two long walls is what makes the shell
  come out as a deep corridor.
- **CENTRE = the hero**: an `AroundGroup` (table anchor + `place_rectilinear(3, 3)` chairs +
  `face(chair, toward=table)` on each + `place_on_top` glassware + `place_rug(size=0.75)`).
- **BACK (short) wall** = two more stocked racks + a barrel cluster + a crate stack.
- **FRONT (short) wall** = door + a rustic wine credenza + a framed wine print.

## Assets — the identity prop is the BOTTLES, and the picker will not give them to you
| Role | id | note |
|---|---|---|
| Rack (hero) | `future/daaa8299-afb9-4008-a00e-da7b736debc3` | 1.00 × 2.06 × 0.33 m, **four tiers of bottles** + an X-bin. Thin/tall = an ideal wall-run module; ten of them wrap the room. |
| Tasting table | `hssd/dad9e55721b563e24e25d575b256536985f1569c` | rustic trestle — **ships 0.51 m tall** (see below) |
| Chair | `future/9c2e6c40-74b3-40b9-84bf-5de7cbfec0ff` | dark leather + wood |
| Barrel | `future/19f58522-7c3d-493b-8657-417204dfdfa3` | oak + brass bands (native 0.65 m → `modulate_scale=1.35`) |
| Barrel display | `future/e591b956-a912-4570-a843-e38c928de172` | a barrel **with bottles on top** — free product mass |
| Glassware | `hssd/a9d615bcd75af8e73df80fe7df1c64c938fa21ae` | **decanter + 4 stemmed glasses** — the plan's centerpiece, in one mesh |
| Wine service | `future/45884782-5d93-4c19-8d2d-1dd6fbd2096a` | bottle in a holder + 2 glasses |
| Wine crate | `hssd/de123db78af8441c9abd5b45acb63fca224d493f` | crate **holding bottles** |
| Credenza | `hssd/eedc60093cc3519ed6b7891469ad7097bd9867c0` | rustic wine cabinet w/ lattice |

- **The visual picker's top "wine rack" hit (`hssd/cfc3a88b…`) is an EMPTY WHITE lattice.** Shipping
  it would have named the fixture, not the cellar (jewelry_shop's empty-vitrine trap). Browse past the
  pick until you find a rack with the **bottles modelled in**, then pin it.
- **"a glass wine decanter" does not exist** as a standalone (the hits are perfume/oil bottles). The
  decanter arrives inside a **tableware SET** mesh — query the set, not the object.
- **AVOID `future/ca401fa0…`** (the bottle cabinet). Its shelves are stocked, but its mesh has a
  **bright white base drawer** that reads as a blown-out rectangle in a dim room. Eye catch — the VLM
  loop was clean on it. Swapped for two more hero racks, which also gave the plan's continuous
  perimeter backdrop.

## THE lesson: "warm dim" is a BUDGET problem, not a fixture problem
The prompt's mood was the one thing that was genuinely unbuildable, and no amount of fixture-picking
fixed it. Two dials, and you need BOTH:

1. **The interior renderer floods the room with a strength-3.0 sky** (`INTERIOR_SKY_STRENGTH`,
   `IDSDL/renderer/utils.py`). The interior views hide the ceiling and light the room from that sky —
   which is right for a daylit room and makes a cellar a bright white gallery **no fixture choice can
   beat**. Set `os.environ["IDSDL_SKY"] = "0.6"` **before importing IDSDL** (the renderer binds the
   value at import). This is the greenhouse note read in reverse: brightness is a SKY setting.
2. **`add_lighting`'s wattage was hardcoded at 500 W.** `density` is fixture COUNT and can never
   change brightness, so a room with the sky dialled down still rendered flat and bright. Added
   **`scene.light_budget`** (`IDSDL/scene.py`, default 500 → every existing scene unchanged;
   `IDSDL/object.py::add_lighting` splits it across N). **90 W over ~32 m² of stone** is the cellar.

> Order matters when you tune these: I dropped the sky and RAISED the wattage in the same build, they
> cancelled exactly, and I nearly concluded the sky override was broken. One dial at a time.

**TOOLING GOTCHA — the MCP `run_scene` builds ignore the program's `IDSDL_SKY`.** The same program
renders bright through `run_scene` and dim through `python workbench.py run <prog>` (verified with an
otherwise byte-identical program, budget 90 W both times: MCP bright, shell dim — the warm MCP server
has already imported the renderer, so the class attribute is bound before the program's `os.environ`
line runs). **Build any moody scene from the SHELL**, or you will chase a mood that your renders can
never show. Sibling of the known `run_scene` mtime-fallback gotcha.

## Other gotchas
- **Scale-check the hero mesh offline before the first build.** `get_whd()` showed the trestle table
  at **0.51 m tall** — coffee-table scale. Fixed uniformly by HEIGHT:
  `t.scale(t.get_width() * 0.76 / t.get_height())` → a real 2.24 × 0.76 m tasting table. (`width=`
  alone would have squashed it — children_room's bean-bag rule.) Same class as the half-scale
  hospital bed; for any uncurated hero, verify a real-world dimension.
- **The on-top tournament oversizes small props, and the useful band is narrow.** The decanter/bottle
  went `modulate_scale=0.55` → a 0.6 m magnum lying across the table; `0.3` → invisible specks;
  **0.4** reads. Bracket it from both sides rather than creeping down (library's banker's lamps).
- **Brick renders paler than the texture.** Verified the embedding: `"old red brick wall"` already
  matches a genuine deep-red brick (`c71761a5`, 0.68) — the pale render is the room-scale tiling +
  light budget, i.e. the renderer, not the wording (bakery's rule: check the match before re-wording).
  Dropping the sky fixed most of it anyway — a washed-out texture is often a LIGHTING symptom.
- **No vaulted ceiling exists.** The DSL shell is a flat box; the vault lives in the textures. Don't
  burn iterations on it.
- **No statement chandelier, ever.** `add_lighting` pins the fixture at the ceiling but caps its
  height at 1.5 m, so a hanging fixture drops into the room — the "caged industrial lamp" query came
  back a giant Tiffany lamp swinging over the table. Compact FLUSH disc, `density=0.01` (a small
  fixture multiplies the count).

## VLM feedback log
- `rescale room by 0.8` every phase (unidirectional) → held per render-wins-early, applied ONE
  decisive `modulate_scale=0.9` in the final phase (0.8 was unsafe: the rack runs are fixed-size rows
  and a wall-loaded shell overflows them — locker_room). The vote decayed to `0.92` → `0.94` on a
  render with clear aisles → **declined as converged noise** (bookstore).
- `no rotation` / `no wall overlap` / no lints from the first build to the last — the payoff for
  copying the library's defaults (omit `facing` on wall runs, explicit `face()` inside the seating
  cluster, door and wall art in disjoint slots).
- **What the clean VLM loop did NOT catch** (all eye catches): the blown-out white drawer on the
  bottle cabinet, the coffee-table-height tasting table, the giant Tiffany lamp, and the entire
  brightness problem. Converged ≠ correct — the loop checks proportions/rotation/slots, never mood.
