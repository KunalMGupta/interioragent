---
id: example:closet
kind: example
family: rows-runs-corridors
category: "walk-in closet / dressing room"
pattern: "Narrow corridor with DEEP cabinetry both sides — the camera rule applied at DESIGN time"
read_for:
  - "READ FOR ANY NARROW ROOM WITH LOADED LONG WALLS (closet, pantry, galley, utility, archive)"
---
> **Digest (from the pattern index):** **Narrow corridor with DEEP cabinetry both sides — the camera rule applied at DESIGN time** — library's twin runs + a dressing island/ottoman hero, but the real lesson is arithmetic: the interior camera sits only `0.04 × room_dimension` in from the wall OPPOSITE the one it shoots, so a deep wardrobe at a wall's CENTRE *contains* that camera and returns a black view the VLM loop calls clean. Put tall bays in the wall END slots and keep both long-wall centres under ~1.3 m (folded-goods shelf, shoe rack) ⇒ four clear views on the first build. **READ FOR ANY NARROW ROOM WITH LOADED LONG WALLS** (closet, pantry, galley, utility, archive). Forced out a core lint (**`[Lint] … is EMBEDDED IN …`**) after a wall shelf shipped **0.45 m inside a wardrobe** with the whole loop reporting `no wall overlap`: wall furniture sits at `row_centers[]` whose pitch is set by each row's FLOOR occupants, so two adjacent wall items can be placed closer than their own widths allow — and a `bottom=`-mounted piece MUST be `ignore_overlap`, which `GradSolver.overlap_pairs` filters out, so nothing ever checks it again. **Three long items on one wall is an ARITHMETIC ((wᵢ+wⱼ)/2 ≤ the row pitch), not a slot count.** Also: **room DEPTH = 3 wall slots × the WIDEST wall item**, so an 8 m closet is fixed by trimming the wall items, never by obeying the shrink vote (which would overflow the fixed runs — locker_room); a "floating shoe shelf" IS a wall unit (mount it with `bottom=`+`ignore_overlap`+`is_static`, don't swap it), and stacking 3 shelves in ONE slot gives a shoe column; uniform scaling couples W to H, so a mesh whose aspect fights your slot grid is the WRONG MESH (a 2.5×1.93 closet system fitted to the slot came out 1.39 m — a stunted run); only 2 of 12 shoe racks in the dataset actually hold shoes


# Walk-in closet — worked example ("Boutique Walk-In Wardrobe")

A luxury **walk-in closet / dressing room**, built from the planner target "Boutique Walk-In
Wardrobe: Perimeter Storage with Central Dressing Oasis". Structurally it is
[library.md](library.md)'s **symmetric corridor** (twin runs on the long walls + a hero down the
centre) with [jewelry_shop.md](jewelry_shop.md)'s **product rule** doing the category work.

The one genuinely new thing here: the **interior-camera clearance rule applied at DESIGN time**
rather than diagnosed after a black render — and the arithmetic for it. Read this before building
any NARROW room whose long walls carry deep cabinetry (closet, pantry, dressing room, utility,
galley kitchen, archive).

## Prompt(s) this covers
- "a walk-in closet" / "a dressing room" / "a wardrobe room" / a boutique fitting room.

## Plan summary
Planner → perimeter floor-to-ceiling cabinetry maximising hanging space; a **central dressing
island** (marble top) with a **tufted circular ottoman** as the try-on perch; open shoe cubbies at
display height; a **full-height mirror** as the focal point; layered boutique light; soft
whites/greys + brass; a plant and a runner for warmth.

## Assets: the category is carried by PRODUCT, and most of the pool is EMPTY
The dataset is full of closet frames and shoe racks with **nothing in them**. An empty fixture
names the fixture, not the room (jewelry_shop's empty vitrines). So every storage mesh here was
pinned *because the clothes and shoes are modelled into it*:

| Role | id | note |
|---|---|---|
| Wardrobe bay (hero, x3) | `future/03608677…` | 2.00x2.12x0.58 — open bay: hanging shirts on TWO rails + folded stacks + drawers + boxes. The whole scene rests on this mesh. |
| Folded-goods shelf | `hssd/76ae9b47…` | 1.50x1.07x0.63 — folded clothes on top, hanging rod under (retail_store's `WALL_MERCH`). A WALL unit — see the mounting note. |
| Dressing island | `hssd/e0c58f0e…` | 1.50x0.71x0.49 — light-oak 6-drawer dresser, black top. Width-fit to 1.7 m ⇒ a real 0.80 m island. |
| Tufted ottoman | `hssd/a58885b1…` | 0.80x0.39 — beige round tufted, dark wood legs. The plan's perch, exactly. |
| Full-length mirror | `hssd/2603ceec…` | 0.70x**1.74**x0.04 — genuinely full-length AND 4 cm thin, so it leans flush and cannot blind a camera. |
| Shoe shelf (x3, column) | `hssd/e9597e32…` | 0.80x0.19x0.25 — white shelf WITH pairs of shoes (retail_store's `SHOE_SHELF`). |
| Shoe rack | `hssd/26d31e9c…` | 1.20x0.28x0.37 — black shelf WITH shoes. |
| Valet rail | `future/a419b5a4…` | 1.20x2.17x0.85 — double-sided rail WITH garments (retail_store's `SPINE_RAIL`). Height-fit to 1.7 m. |
| Island props | `future/725133ce…` (perfume tray), `future/aa8e5dc9…` (handbag), `future/c17aa2e4…` (folded sweaters) | the accessory layer, at viewing height |

**Only 2 of 12 shoe racks in the dataset carry shoes** (both pinned above); the other ten are bare
frames. Same story for closet systems — so *mass what exists* rather than shipping empties.

**Rejected at the audit gate (30 seconds each, all would have been post-build mysteries):**
- `hssd/7bbdbc91` — captioned "white kitchen island with a **marble countertop**", i.e. the plan's
  island by name. Its preview is a **rustic farmhouse work table** with cross-braced legs: a
  wrong-kind object (prison_cell's floral curtains in a jail cell). *The caption matched the plan;
  the mesh didn't.*
- `future/4115684f` — a "classic freestanding **full-length** mirror" that `get_whd()` says is
  **1.05 m tall**. Not full-length. Pinned `2603ceec` (1.74 m) instead.
- `future/1ed074bd` — the best-looking dresser (light oak + marble edge), but 1.50x**0.54** m: at
  a 2.78 W/H aspect, height-fitting it to a real island forces a **2.4 m wide** island that chokes
  the aisles. Aspect ratio is a layout property — check it before falling in love with a preview.

## THE LAYOUT: keep both long-wall CENTRES low (the camera rule, derived not discovered)
`IDSDL/renderer/utils.py::render_interior_walls` puts each camera on the room centreline at
`eye = 0.55 x ceiling_height`, `inset = 0.92` — i.e. **`0.04 x room_dimension` in from the wall
OPPOSITE the one it is looking at**. In a 4.6 m wide closet that is **~0.18 m**. A 0.58 m deep
wardrobe standing at a wall's CENTRE therefore *contains* the camera that looks at the other wall,
and you get a black view — which the VLM loop happily reports as `no rescale / no rotation / no
wall overlap` (kitchen_set's blinded-camera trap; bakery's hallucinated rotation storm).

A walk-in closet is the worst case for this: it is narrow *and* both long walls are deep cabinetry.
The fix is structural, not a rescale — **tall pieces go in the wall's END slots, and each wall's
CENTRE slot gets something under ~1.3 m**:

```
LEFT  wall:  [ wardrobe 1.91m ] [        (empty)           ] [ folded-goods shelf ]
RIGHT wall:  [ wardrobe 1.91m ] [ shoe rack, top at 0.48m  ] [ shoe column        ]
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                 the camera for the OPPOSITE wall lives here
```
Both side views came back clear on the **first** build. The low centre pieces are not a compromise:
a shoe rack is exactly what belongs mid-run in a real closet, and an empty wall centre is the
safest thing you can put in front of a camera.

## The bug this example exists to warn you about: WALL ITEMS CAN BE PLACED INSIDE EACH OTHER
v1 ran **wardrobe / shelf / wardrobe** across all three left-wall slots. It shipped, and the
folded-goods shelf was **0.45 m inside** the far wardrobe bay. The full VLM loop said
`no rescale / no rotation / no wall overlap` on every build, and no lint fired. A **user** caught
it. Two independent DSL properties combine to make this invisible:

1. **Wall furniture is placed at `row_centers[1..3]`, and the row centres are sized by each row's
   FLOOR occupants — not by the wall items.** This room's back row is shallow (a 4 cm mirror, a
   plant), so its centre sat only **1.20 m** from the middle row's centre — while a 1.8 m bay
   beside a 1.5 m shelf needs `(1.8 + 1.5)/2 = 1.65 m` between centres. The DSL packs them anyway.
2. **The shelf had to be `ignore_overlap`** (it is mounted with `bottom=`; without the flag the 2D
   solver reads the lifted shelf and the cabinet beside it as interpenetrating and shoves them
   apart along the wall). But `GradSolver.overlap_pairs` — which backs the residual-overlap
   warning — **filters ignore_overlap items out by construction**. So once flagged, nothing ever
   looks at that object again: the bay was free to sit inside it and no pass could push back.

⇒ **Three long items on one wall is an ARITHMETIC, not a slot count.** Check
`(wᵢ + wⱼ)/2 ≤ the row-centre pitch` before assuming three slots hold three things. When they
don't fit, the fix is to drop one (here: leave the centre empty, which the camera wanted anyway),
not to shrink a hero into a stub.

This forced a **core fix**: `IDSDL/lints.py::lint_embedded_wall_objects` now runs a full **3D**
AABB test over exactly the pairs the solver refuses to look at (every `ignore_overlap` item vs
every other room child, parent/child pairs excluded so a `place_on_top` prop resting on its anchor
stays silent), and emits `[Lint] '…' is EMBEDDED IN '…' — they interpenetrate WxHxD`. 3D, not the
2D footprint the solver uses, because a shelf ABOVE a console is legal and must stay quiet.

## Skeleton program
```python
scene = SceneProgRoom("WalkInCloset", seed=21)

def wardrobe_bay():                       # width-fit 1.8 m => 1.91 m tall; SETS THE ROOM LENGTH
    w = scene.AddAsset("an open wardrobe bay with hanging clothes", asset_id=WARDROBE)
    w.scale(1.8)                          # scale() returns None — never chain it
    return w

island = scene.AddAsset("a light oak six drawer dresser with a black top", asset_id=ISLAND)
island.scale(1.7)                         # uniform width-fit => 0.80 m island height

with scene.RelativeGroup() as island_group:
    island_group.set_anchor(island)
    island_group.place_on_front(ottoman)          # the try-on perch
    if PHASE >= 2:
        island_group.place_on_top([tray, handbag, folded])   # targets the ANCHOR = the island
    if PHASE >= 3:
        island_group.place_rug("a flat neutral wool runner rug", size=0.7)

with scene.RoomGroup(modulate_scale=0.9, randomness=0.1) as room:
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="smooth white plaster ceiling",
                     wall_texture="smooth cream painted plaster wall")
    room.place_on_center(island_group, facing="front")
    room.place_on_left_wall_right(wardrobe_bay())               # ONE bay: three long items do NOT fit
    merch.ignore_overlap = True; merch.is_static = True         # a WALL unit: mount it
    room.place_on_left_wall_left(merch, bottom=0.45)            # top 1.52 m — under the camera
    room.place_on_right_wall_left(wardrobe_bay())
    shoe_rack.ignore_overlap = True; shoe_rack.is_static = True
    room.place_on_right_wall_center(shoe_rack, bottom=0.20)
    for i, shelf in enumerate(3 * scene.AddAsset("a white shelf displaying pairs of shoes", asset_id=SHOE_SHELF)):
        shelf.ignore_overlap = True; shelf.is_static = True     # a lifted wall column
        room.place_on_right_wall_right(shelf, bottom=0.45 + 0.45 * i)
    room.place_on_back_wall_center(mirror)         # focal, 4 cm thin
    room.place_on_back_right_corner(olive_tree)
    room.place_door("front_wall", position="right")
    room.place_on_front_left(rail)                 # valet rail fills the entry third
    if PHASE >= 3:
        room.place_window_standard("back_wall", position="left", curtain="sheer white linen curtains")
        room.add_lighting("a flat round brass LED flush mount ceiling light", density=0.01)
        room.place_on_wall_front_left(scene.AddAsset("a framed black and white fashion photograph print", width=0.7))
scene.export("closet.blend")
```

## What worked / gotchas
- **A "floating shoe shelf" IS a wall unit — mount it, don't swap it.** The folded-goods shelf and
  the shoe rack both tripped `[Lint] FLOATS 0.45 m / 0.20 m`. The lint's advice ("off-center mesh
  origin — swap the mesh") is aimed at FLOOR furniture; these meshes are *authored as wall units*
  (one is literally captioned "floating shoe shelf", and retail_store mounts the other at
  `bottom=0.4`). Fix = mount them via the wall-adjacent + `bottom=` path with `ignore_overlap`
  **and** `is_static` (the range-hood recipe). `lints.py` skips `ignore_overlap` children, so the
  lint goes quiet *because the placement is now honest*, not because it was silenced. Both are
  0.37–0.63 m deep, far past the 0.25 m limit where `place_on_wall_*` would float them as art.
- **Stack a shoe COLUMN in ONE wall slot.** Three shelves at `bottom = 0.45 / 0.90 / 1.35` in the
  same end slot give the plan's lit shoe niches. `ignore_overlap` is mandatory or the 2D-footprint
  solver reads the stack as one interpenetrating pile and shoves the shelves apart along the wall;
  `is_static` stops the GradSolver's exploration floor walking them off (living_room_cozy's drift).
- **Room DEPTH = 3 wall slots x the WIDEST wall item — that is the lever, not `modulate_scale`.**
  The shell auto-sized to 4.48 x **8.15 m** (an 8-metre closet) because one wall unit was 2.5 m
  wide. Trimming the wall items (2.5 → 1.8 m) walked it to 6.6 m *honestly*; obeying the VLM's 0.8
  shrink instead would have dropped the slot to 2.17 m and overflowed the fixed wall runs into each
  other — the locker_room packed-room trap. **When a room is too long, measure the wall queue
  before you touch the shell** (kitchen's "the vote tells you THAT, never WHICH").
- **Uniform scaling couples width to height — so "tall" and "narrow" can be mutually exclusive.**
  The closet system (2.50x1.93) fitted to the 1.8 m slot came out **1.39 m tall**: a stunted run
  under a blank wall band, opposite two 1.91 m bays. No signal fires for that (the geometry is
  perfect). Swapped it for a third matching wardrobe bay → twin floor-to-ceiling runs, as the plan
  asked. **A mesh whose aspect fights your slot grid is the wrong mesh, however good its preview.**
- **The island is a DRESSER, and a dresser has one good face.** Its plain back faces the door. The
  hero view (from the entry, looking in) shows the oak drawer fronts, so this is the right way
  round — but know that you are choosing which view gets the back.
- **`place_on_top` targets the group's ANCHOR** — here the anchor *is* the island, which is what we
  wanted (contrast living_room_cozy v3, where a nook's anchor was the armchair and the lamp landed
  on the cushion). Tray + handbag + folded sweaters at viewing height are what make it a *dressing*
  island rather than a sideboard.
- **The plan's chandelier is a trap.** `add_lighting` caps fixture HEIGHT at 1.5 m but pins the
  origin at the ceiling, so a chandelier hangs into the room and its emissive globes blow the
  exposure (executive_office). Used a flush brass fixture at `density=0.01` (small-room band) and
  let the oak/brass/walnut palette carry the "boutique" warmth.

## VLM feedback we hit and how we resolved it
- **`[Lint] FLOATS 0.45 m` / `0.20 m`** (phase 1) → **accepted as real, fixed by MOUNTING** the two
  wall-unit meshes with `bottom=` + `ignore_overlap` + `is_static` (not by swapping). Clean after.
- **A wall shelf embedded 0.45 m inside a wardrobe, reported by NOTHING** (user catch) → the
  row-centre-pitch bug above. Fixed in the scene (dropped the third long item off that wall) AND in
  core (the new `EMBEDDED IN` lint). Worth noting how a wrong diagnosis was caught: my first fix was
  `is_static` on the bays, assuming the solver had *drifted* them into the shelf. The rebuild came
  back with a **bit-identical penetration (0.52 x 1.00 x 0.47 m)** — which proves the solver never
  moved them at all, and sent me to read `place_on_left_wall_*` instead of guessing again. **When a
  fix changes the numbers by exactly zero, the mechanism you blamed is not the mechanism.**
- **`rescale room by 0.8`, four builds running** → **partially declined, and re-diagnosed.** The
  vote was right that the room was wrong, but wrong about the fix: the room was too LONG (a wall-slot
  problem), not too big. Trimmed the wall items, added a valet rail to fill the dead entry third
  (kindergarten/greenhouse: *a persistent shrink vote on a wall-packed room means ADD FURNITURE*),
  and applied ONE safe `modulate_scale=0.9`. 36.5 m² → 30.8 m².
- **The residual vote then bounced `0.8 → 0.9 → 0.8 → 0.78` across IDENTICAL builds** → **declined
  permanently.** An oscillation across repeated builds of the same program is measurement noise
  (office_modern), and a walk-in's dressing aisle is working floor that an occupancy metric always
  reads as emptiness (garage/corridor/operating_room).
- **`no rotation` / `no wall overlap` from the first build to the last** — clean by construction:
  `facing` omitted on every wall placement (the heuristic already turns furniture into the room),
  the door and window on different walls entirely, and wall art hung over the low/empty end.

## Manual constraints used
- None. Auto overlap/bounds + door clearance + `_repin_wall_furniture` sufficed. (`bottom=`,
  `ignore_overlap` and `is_static` on the lifted wall pieces are placement args, not constraints.)
