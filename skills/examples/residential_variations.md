---
id: example:residential_variations
kind: example
family: meta-review-round
category: "bedroom / living / dining / bath / kitchen / study"
pattern: "The variation + REVIEW round (2026-07-14)"
---
> **Digest (from the pattern index):** **The variation + REVIEW round (2026-07-14)** — several variants off each of the six residential flagships, then a human review that minted five VLM-invisible rules: **(1) two furniture groups go in DIFFERENT regions** or circulation dies (writer studio desk-crowds-daybed, now in [../workflow/design_principles.md](../workflow/design_principles.md)); **(2) a sparse room you CANNOT shrink** (kitchen camera bound) is fixed by FURNISHING, not resizing; **(3) the console-vignette** (sideboard + art-above + composed plant) is the reusable "fill a bare open-plan wall + rescue a lonely prop" move; **(4) "cozy" is a deliberate human shrink AGAINST a never-flipping enlarge vote** — the vote optimizes uncluttered, the BRIEF decides whether you want clutter or space; **(5) retrieval hands back valid-but-WRONG meshes** (a garden bench for a wardrobe) the clean loop can't see — pin or use the acquire dial. Powder-room jewel-box at 0.6 converged on the autos (evidence for "no toilet clearance rule")


# Residential variations — the 2026-07-14 category batch (bedroom / living / dining / bath / kitchen / study)

Status: **built, VLM-clean, and human-reviewed** (Kunal, 2026-07-14). This is not a new *pattern* —
it is the round where the six user-facing residential categories each got **several variations** off
their flagship recipe, then a human review pass that produced five durable lessons the VLM loop was
blind to. Read the flagship `.md` for the pattern; read THIS for what changes across variants and for
the review-driven rules. The programs are the code (paths in the table at the bottom); the reusable
snippets are inlined below.

The round was human-reviewed on an internal review board (19 scenes, one feedback block each; the
`reviews/` boards are dev-only scratch, not part of the release): 15 approved, 3 sent back for rework,
1 fixed on the spot. The durable findings are distilled below.

## The variations, by category — what changes off the flagship

| Category | Flagship | Variations this round | What the variation exercises |
|---|---|---|---|
| **bedroom** ([bedroom.md](bedroom.md)) | Warm traditional master | `br_guest_cozy` (warm welcome), `br_teen_study` (denim & maple, study corner) | the symmetric-hero skeleton at guest scale, and a bedroom that ALSO carries a desk zone — the first two-zone bedroom (see Lesson 1) |
| **living room** ([living_room_cozy.md](living_room_cozy.md)) | Hearth + facing cluster | `lr_japandi` (low minimalist), `lr_midcentury` (mustard/walnut/teal entertaining) | palette + massing swaps on ONE cluster; japandi = subtractive, MCM = a saturated accent triad. The flagship `living_room_cozy` itself was reworked this round (Lesson 4) |
| **dining room** ([dining_room.md](dining_room.md)) | Formal table hub + service wall | `dr_breakfast_nook` (airy round scandi), `dr_farmhouse` (reclaimed trestle + bench) | the table-hub at cozy scale (round, cane) and rustic (bench-one-side is authentic, not an error) |
| **bathroom** ([bathroom.md](bathroom.md)) | Spa master | `ba_hotel_double` (grey marble & wood, double vanity), `ba_powder_compact` (teal jewel-box) | set-assets at hotel scale, and the powder-room STRESS TEST — a 4-object jewel box at 0.6 that converged on the autos (evidence for "no toilet clearance rule", playbook §5.6) |
| **kitchen** ([kitchen.md](kitchen.md)) | Fitted set + corner align | `kitchen_l_pocket` (L + pocket island), `kt_galley_straight` (straight + front island), plus `kitchen_modular` / `kitchen_u_peninsula` | the three `KitchenIslandGroup` modes (pocket / front / tip). Both single-run variants were reworked for sparseness (Lessons 2–3) |
| **study room** (new — no flagship `.md`) | — | `st_home_office` (executive_office's bones, domestic), `st_library_study` (library's corridor in one room), `st_writer_studio` (desk-by-window + daybed) | study reuses office/library patterns at domestic scale; the writer studio minted the region-separation law (Lesson 1) |

The study trio has no `.md` of its own on purpose: a home office IS
[executive_office.md](executive_office.md) / [office_modern.md](office_modern.md) shrunk, a library
study IS [library.md](library.md) folded into one room, and the only genuinely new study piece — the
writer's studio — is captured in Lesson 1 below.

## Lesson 1 — two furniture groups go in DIFFERENT regions of the room

`st_writer_studio` carries a desk `WorkstationGroup` AND a daybed — the first two-zone room where the
zones competed. Built at `place_on_back` (desk, back-CENTRE) + `place_on_left_wall_center` (daybed),
both reached into the shared back-left corner; the desk chair crowded the bed and the bed had
circulation on only two sides. **Every constraint passed** — `no rotation`, `no wall overlap` — the
pieces were legal, just cramped. Kunal caught it by eye and named the cause exactly: the two groups
were in the same region. The fix is purely spatial:

```python
room.place_on_back_right(station, facing="back")       # desk -> back-RIGHT third
room.place_on_left_wall_center(daybed, facing="right")  # bed  -> LEFT wall, a region away
room.place_on_back_wall_left(shelf)                     # shelf off the right wall so it, too, clears
```

Promoted to a default in [../workflow/design_principles.md](../workflow/design_principles.md): prefer
the corner/third verbs to spread groups diagonally; reserve wall-CENTRE for a single group or a
wall-flush run. This is the same family as the bedroom's self-contained nook — but stated for the case
where BOTH zones are load-bearing and neither may collapse into the other.

## Lesson 2 — a sparse room you CANNOT shrink is furnished with NON-FLOOR elements only

Both single-run kitchens (`kitchen_l_pocket`, `kt_galley_straight`) read too sparse. The instinct from
kindergarten/grocery is "fill the floor, then shrink" — but a kitchen built on a fitted set has a
**hard camera bound** (`run_width ≤ W/2 − 0.3`; below it the wall-run camera renders solid black — see
[kitchen.md](kitchen.md)), so it cannot shrink. The trap is that it **cannot freely take new floor
furniture either.** This round proved it empirically: the first rework added a serving **console** to
the front wall to fill the floor, and the back-wall-centre camera rendered **solid black** (verified —
back view mean-luma 0.2). A console is FLOOR MASS; the auto-shell sums column widths, so a new floor
slot shifts the shell and pushes the fixed-size run past the camera bound — the exact trap the whole
scene is built around. The console was reverted from both kitchens.

**The rule: furnish a camera-bound room with elements that claim NO floor slot** — a rug (`place_rug`
seats under the anchor), a pendant (`add_lighting` is an AABB-skipped light), and **wall art** (hung,
zero footprint). Those are what shipped: a full four-seat nook on a jute rug, a brass pendant over it,
and a botanical wall-art PAIR on the bare walls. None of it touches the set (kitchen.md's "phase 2 is
empty" rule guards the SET + island, not the whole room). If a camera-bound room still reads sparse
after that, the emptiness is the open-plan circulation the run's size forces — declare it, don't chase
it with a floor piece.

## Lesson 3 — the console-vignette: fill a bare open-plan wall (in a room WITHOUT a camera bound)

For a living/dining/bedroom (no fitted-set camera bound), a serving console on a free wall — top
styled, wall art hung above it, any stray plant COMPOSED beside it instead of floating alone — is the
cheapest way to make a bare wall read finished and to rescue a lonely prop:

```python
with scene.RelativeGroup() as vignette:
    vignette.set_anchor(console)                            # a LOW console (< 1.0 m, camera-safe)
    vignette.place_on_left(plant)                           # the lonely plant, now composed
    vignette.place_on_top([vase, book_stack])
room.place_on_front_wall_center(vignette, facing="back")
room.place_on_wall_front_center(art)                       # hangs directly above it
```

**But do NOT use it in a set-piece kitchen** (Lesson 2) — there the same move is a new floor slot that
blinds the camera. `kitchen_l_pocket` had its lonely plant fixed the cheaper, camera-safe way instead:
the plant simply moved to the front-left CORNER (corners are camera-safe by construction), and the
bare wall got a wall-art pair rather than a console.

## Lesson 4 — "cozy" is a deliberate override of the never-flipping enlarge vote

`living_room_cozy` shipped at `modulate_scale=1.1` because RoomProportions voted enlarge every phase
(1.2/1.25/1.1/1.1, never flipped) — and a vote that never flips is usually real signal. But Kunal
reviewed the result as **"cavernous, not cozy"**: the seating was marooned around an empty floor. The
resolution is that the enlarge vote optimizes for UNCLUTTERED, and *cozy is the opposite brief*. So we
overrode it — pulled the shell to `0.85` (~23% tighter than shipped) and enlarged the seating rug
`0.75 → 0.9` so the sectional and the leather nook sit on ONE rug as a single conversation zone.

The rule: **an intimate/cozy/snug brief licenses a human shrink AGAINST a persistent enlarge vote.**
It will vote enlarge again on rebuild — refuse it; the brief wins. This is the complement of the
bedroom's Lesson 5 (a phase-1 enlarge vote is voting on a half-dressed room) and kindergarten's "fill
then shrink" — three faces of the same truth: **the room-size vote is advice about clutter, and the
BRIEF decides whether clutter or space is what you want.**

## Lesson 5 — retrieval will hand back a valid-but-WRONG mesh, and the clean loop can't see it

Both bedrooms (`bedroom`, `br_guest_cozy`) shipped with a white slatted **garden-style bench**
standing in for a wardrobe/settee — a perfectly good mesh, cool white against a warm-wood palette,
and categorically wrong. The VLM loop never complained (it verifies geometry, not that the object IS
what the brief asked for — the casino/kindergarten "clean loop can't see semantics" rule). This is
exactly the silent substitution the **acquisition dial** exists for
([../acquire-assets/SKILL.md](../acquire-assets/SKILL.md)): at `acquire="mid"/"high"` the retriever
measures the similarity gap and goes and finds/generates the real thing when the dataset's best hit
stops being the object named. When a residential brief asks for a specific piece the dataset is thin
on (wardrobe, armoire, specific accent chair), either pin an audited id or build it with the dial —
don't trust the top hit to be the right *category*.

## The reworks (what the review changed, 2026-07-14)

| Scene | Complaint | Change (final) | Rebuild verdict |
|---|---|---|---|
| `kitchen_l_pocket` | too sparse; plant floated behind the dining | dining rug + pendant + botanical wall-art pair; plant → front-left corner (a console was tried FIRST and blinded the camera — reverted, L2) | CONVERGED, 4 views clean (back luma 0.2→219); rescale 0.9 held (camera bound) |
| `kt_galley_straight` | too sparse / uninteresting | dining 2→4 seats + rug + pendant + wall-art pair; nook shifted front-left (console reverted, L2) | CONVERGED, 4 views clean; rescale 0.8 held (camera bound) |
| `living_room_cozy` | cavernous, not cozy | `modulate_scale` 1.1→0.85; seating rug 0.75→0.9 | CONVERGED (no wall overlap); enlarge vote 1.35 REFUSED (cozy override, L4) |
| `st_writer_studio` | desk crowded the daybed; no circulation | desk → back-right region, shelf → back wall, window → back-right (L1) | CONVERGED: no rotation, no wall overlap; 4 views clean (luma 158–184) |

## Programs (the code)

| Scene | Program |
|---|---|
| bedroom variants | [`scenes/batch_0714/br_guest_cozy.py`](../../scenes/batch_0714/br_guest_cozy.py), [`br_teen_study.py`](../../scenes/batch_0714/br_teen_study.py) |
| living room variants | [`scenes/batch_0714/lr_japandi.py`](../../scenes/batch_0714/lr_japandi.py), [`lr_midcentury.py`](../../scenes/batch_0714/lr_midcentury.py); reworked flagship [`scenes/work/living_room_cozy.py`](../../scenes/work/living_room_cozy.py) |
| dining variants | [`scenes/batch_0714/dr_breakfast_nook.py`](../../scenes/batch_0714/dr_breakfast_nook.py), [`dr_farmhouse.py`](../../scenes/batch_0714/dr_farmhouse.py) |
| bathroom variants | [`scenes/batch_0714/ba_hotel_double.py`](../../scenes/batch_0714/ba_hotel_double.py), [`ba_powder_compact.py`](../../scenes/batch_0714/ba_powder_compact.py) |
| kitchen variants | reworked [`skills/examples/kitchen_l_v1.py`](kitchen_l_v1.py), [`scenes/batch_0714/kt_galley_straight.py`](../../scenes/batch_0714/kt_galley_straight.py) |
| study trio | [`scenes/batch_0714/st_home_office.py`](../../scenes/batch_0714/st_home_office.py), [`st_library_study.py`](../../scenes/batch_0714/st_library_study.py), [`st_writer_studio.py`](../../scenes/batch_0714/st_writer_studio.py) |
