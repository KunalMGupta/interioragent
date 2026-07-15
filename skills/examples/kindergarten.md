# Kindergarten — worked example

Status: **built & VLM-clean** (`skills/examples/kindergarten_v1.py`, seed=11). Final compile returns
`no rescale` / `no wall overlap`, zero `[Lint]` lines, and the single rotation vote is the
documented `place_desk_chair` false positive (declined by eye). Supersedes the thin
pre-workflow `scenes/kindergarten.py` (which shipped `place_window_picture` → a black void,
unpinned chairs, and a non-flush ceiling light).

Read alongside [toy_shop.md](toy_shop.md) (pre-stocked fixtures carry the identity),
[children_room.md](children_room.md) (kid scale + nook) and [game_room.md](game_room.md)
(hero-in-the-middle).

## Prompt(s) this covers
- "a kindergarten" / preschool / nursery-school activity room / early-years classroom.

## The layout idea: a HERO ON THE FLOOR, zones ringed around it
The circle-time rug is the hero — but unlike every other hero in the catalogue it is not a
piece of furniture, it's **floor**. That turns out to be the whole trick:

- **CENTRE** — the oval alphabet rug, placed as an ordinary **FLOOR object**
  (`room.place_on_center(rug)`). The `OverlapConstraint` then reserves its footprint, so
  *the clear carpet a class sits on comes for free* — no clearance constraint needed. The
  empty middle of a kindergarten is not empty, it IS the circle-time zone.
- **FRONT wall** = TEACHING WALL: whiteboard hung centre + ABC poster; the teacher desk
  front-left `face()`d at the class; the door front-right.
- **BACK wall** = the STOCKED STORAGE RUN (3 items — a deliberate hero run): toy shelf,
  cubby of labelled bins, toddler locker.
- **LEFT** = READING NOOK under the window: two bean bags + a teddy on their own rug, book
  stand against the wall so the books are in reach.
- **RIGHT / BACK-RIGHT / BACK-LEFT** = ACTIVITY FIELD: three low round tables, each ringed
  by four kid chairs.

## Everything is CHILD height — and that is also a CAMERA rule
Tables 0.95 m, chairs 0.62 m, all storage ≤ 1.15 m. Kid scale is the brief, but it also buys
the bakery camera rule for free: the interior wall cameras sit at ~1.4–1.5 m, so nothing at a
wall centre can blind a view or provoke hallucinated rotation flags. **This scene was
rotation-clean from the first phase-1 build to the last** — the same clean-by-construction
outcome as classroom v1, for a different reason.

## Assets (all pinned; previews eyeballed at gate 3)
| Role | id | note |
|---|---|---|
| Alphabet rug (HERO) | `hssd/ba8bdada…` | oval, blue centre, letter border — letters legible in every render |
| Kid table (×3) | `hssd/4b9ff34f…` | round, **BARE** flat top (0.95 m) |
| Kid chair (×12) | `future/938f5c3e…` | cartoon **lion-faced** chair, yellow seat (0.62 m) |
| Cubby | `future/187f9f51…` | light wood, **PRE-STOCKED with colourful labelled bins** |
| Toy shelf | `future/1fc1d19b…` | cartoon shelf **PRE-STOCKED with toys** (toy_shop pin) |
| Toddler locker | `hssd/e81617da…` | 4 sections + colourful bins |
| Book stand | `hssd/f3a8d459…` | **FILLED** with children's books |
| Bean bags | `hssd/0598a08d…` (blue star), `hssd/0839789d…` (yellow) | the pink ones wash out to WHITE in render |
| Teaching wall | whiteboard `hssd/1b37271d…` + ABC poster `hssd/caf281fc…` |
| Art | train `hssd/128c8d8d…`, whale `hssd/8e37f5ae…` | **verified visible content** (see below) |
| Table props | ABC blocks `future/6b72a461…` + puzzle box `hssd/d5f0014a…` |
| Teacher | desk `hssd/99e2a3e3…` + globe `hssd/55c813d9…` (classroom_v1 pins) |

**AVOID:**
- `hssd/12ef49da…` "colourful children's planets wall art" — a **wheeled EASEL** (0.26 m deep),
  not a print (children_room already blacklists it; it still ranks top-10 on kid-art queries).
- `hssd/c5fcff66…` — the visual picker's #1 for *"a small colourful child's chair"* is a
  **wheeled swivel OFFICE chair**. Caption and similarity both look fine; only the preview
  gives it away.
- `hssd/2af5d109…`, `hssd/f8261de4…` — kid table+chair **SET** meshes (double-seat an
  AroundGroup that supplies its own chairs).

## Lessons this build forced out

### 1. A "cup of crayons" does not exist — and the VLM loop will never tell you
`place_on_top("a cup full of colored crayons")` resolved at **0.43** to a *white ceramic
geometric DESIGNER pencil holder with two black pens* (the shortlist is beige pencils, wooden
pencils, post-its — there is no crayon cup in the dataset). It put a **vase-like object on
every kid table** and the full VLM loop stayed clean through it: the geometry is fine, and
*"a designer pen pot doesn't belong in a kindergarten"* is semantics, not geometry. Caught by
eye in the render; swapped for a boxed puzzle the library provably has. Same failure class as
casino's poker chips → **only `place_on_top` a prop you have verified exists.**

### 2. A nook is a corner, not an island — pin it to the wall
`place_on_left(reading_nook)` (a floor SLOT) left the bean bags stranded mid-floor: door
clearance + `randomness` push slot groups around. `place_on_left_wall_center(reading_nook)`
pins the whole composed group flush under the window. Wall placements accept composed groups —
use them whenever "tucked against a wall" is the intent (bakery's window-bar drift, same fix).

### 3. Fill the floor, THEN shrink — a sparse room is not always a too-big room
`RoomProportions` ran `0.92 → 0.90 → 0.80` — same-direction and *growing*, i.e. genuinely
sparse (contrast living_room_cozy's decaying vote). But kid-scale furniture is small **by
definition**, so chasing the vote to 0.8 would have bought the occupancy number by crushing
the open floor a kindergarten exists for (the garage "circulation lane reads as empty" rule).
Applied `modulate_scale=0.85` **and** added a third activity table (the plan's "construction
center") into the empty `back_left` slot → next build `no rescale`. Children_room's
"add a bean bag rather than over-shrink", generalised: **when the vote grows, ask whether the
room is too big or the floor is too empty — and fix the one that is actually true.**

### 4. Kid wall art: most posters are EMPTY FRAMES; check for visible content
Nearly every "ABC poster / kids canvas" candidate renders as a **blank white rectangle** in
the contact sheet (the empty-frame class from living_room_cozy v2 — a reversed front and an
empty frame look identical). Pin only meshes whose preview shows **actual illustration**: the
"Oliver" train canvas and the whale canvas both carry real artwork; the ABC poster is genuine
but pale (its letters do read, just washed out). Browse the *previews*, not the captions.

### 5. The accent rides on PROPS, never on the wall string
Wall texture is plain `"smooth white painted plaster wall"`. The entire primary-colour
palette is carried by the rug, the lion chairs, the bin fabrics, the bean bags and the
canvases. Classroom v1's `"white ... with one teal accent wall"` recoloured **all four walls
green**; music_studio's red accent arrived on the rugs instead. Kindergarten is the strongest
case for this rule — the props are so colourful the walls *should* stay white.

## VLM feedback we hit and how we resolved it
- `rescale room by 0.92 → 0.90 → 0.80` (growing, same direction) → held per render-wins-early;
  final phase applied **0.85 + a third table** → **`no rescale`**. Converged.
- Post-apply vote flipped to **`1.1`** (enlarge) on the intermediate build → **declined**: a
  flip *across neutral* right after one decisive application is the converge signal (classroom
  v1, music_studio, casino).
- `rotate black office task chair to face the teacher desk` → **declined**. Verified by eye:
  the chair sits behind the desk with the desk's working front toward it — correct *by
  construction* via `place_desk_chair` (the same false positive as children_room /
  computer_room / classroom).
- `no wall overlap` and **zero lints every single build**: wall fixtures all kid-height and in
  disjoint slots, door and window on different walls, `add_lighting` flush at `density=0.015`
  (the bookstore ~50–56 m² datapoint — right first time, no starfield).

## Known residual (honest)
The walls render pale grey-green rather than "bright cheerful" under the fixed light budget.
The texture string is the proven classroom_v1 pin, so this is the renderer's wash, not a
wording bug — **check the match before re-wording** (bakery), then converge. The teacher's
black mesh office chair also reads a little corporate beside twelve lion chairs.
