# Jewelry shop — worked example (fine-jewelry boutique)

> **v3 UPDATE (2026-07-10) — rebuilt on real fixtures; prefer this.** Once the `ShopFixtureRetriever`
> + ingested retail meshes landed, the scene was rebuilt on **purpose-built jewelry furniture** (pinned
> by `custom/<id>`): a walnut **jewelry display counter** `custom/1028be7dddc5b7e1a0c4339582223f5d787400c3`
> (glass top with rings/earrings + branding — massed ×6 = a legible showroom), a **cash-wrap with an
> integrated POS** `custom/eedaa74ba03140b24a6629be7ce4be699bd96307`, black-velvet **necklace busts**
> (`custom/3add6d78…` single-gold-chain, `custom/df9fc6e6…` triple), a **ring-display cube**
> `custom/dec1d5a87920cce3073622b19b6d2ad7737befdc`, a velvet **cushion** `custom/53ec24cb…`.
> **The meta-lesson: the RIGHT fix for "the identity prop is a mesh gap" is to check for a dedicated
> retriever / ingest FIRST** — the improvised-decor approach documented below (geode/cloche/hand-stand)
> is only the fallback when no real asset exists. Gotchas from the rebuild: LOW jewelry counters DON'T
> congest like tall wardrobe-vitrines (line every wall); the cash-wrap's native H=1.70m **includes its
> POS screen** so don't uniform-scale it to "counter height" (shrinks the body) and don't stack a tall
> bust on it (towers → VLM "rescale counter 0.5"); pin `custom/<id>` (the warm MCP `retrieve` can't see
> a newly-added retriever class until a server restart, but `run_scene`/`workbench.py` can). The rest of
> this file (the improvised-prop version) stays as the fallback recipe + the reasoning that led here.

## Status

Status: **built & iterated as `scenes/jewelry_shop.py` (seed=42)** — the v3 rebuild on the real
`ShopFixtureRetriever` fixtures. [`jewelry_shop_v1.py`](jewelry_shop_v1.py) is that program
**phase-gated** (2026-07-13): `lint_program`-clean, with the layout / pinned ids / seed / comments
preserved. **It has NOT been re-run or re-rendered since the retrofit, so the phase splits are
UNVERIFIED.**

## (earlier) fine-jewelry boutique, "visible-jewelry display tables + calm vitrine backdrop"

A luxury jewelry boutique. **The hard-won lesson (v2): a shop is read by its PRODUCT, not its
fixtures.** The dataset has no velvet necklace bust, so v1 leaned on a gallery of glass display
vitrines to carry the identity — but the cabinets render *empty* (no jewelry inside the mesh),
so the room read as a **furniture showroom, not a jewelry shop**, and 6 tall cabinets made it
**congested**. The fix that worked: **mass real jewelry-display PROPS at viewing height** — a
gold hand-shaped jewelry stand, a geode/gem specimen, an agate on a gold stand, a glass cloche,
stacked velvet jewelry boxes, a display bust — on a **central hero display table + the cash-wrap
+ the window pedestals**, and **cut the vitrines 6→4** (backdrop only) while up-scaling the room
0.8→0.9 to de-congest. Supporting cast: a **consultation cash-wrap** (counter + POS + stools), an
ornate gold **focal mirror**, a small emerald-velvet **lounge nook**, greenery. Reach for this
for "a jewelry / jewellery store, a watch shop, a luxury boutique, a gallery-style showroom." A
close cousin of `retail_store.md` (shop = central piece + perimeter loop + branded service wall);
read both, plus `../workflow/asset_selection.md` (this scene opened with a retrieval **stress
test**) and `../workflow/vlm_feedback.md`.

## Prompt(s) this covers
- "a jewelry store", "a jewellery / watch shop", "a fine-jewelry boutique", "a luxury showroom / gallery shop".

## Plan summary
Planner → **"Luxe Jewelry Boutique: Gallery Spine Conditioning"**: a continuous showroom
spine of glass-topped display banks; a back-wall focal rhythm of niches/busts + mirrors;
consultation seating at the counter + a discreet lounge nook; warm wood + marble + glass +
brass, velvet accents, biophilic greenery. Palette: greige walls, polished-stone floor, dark
warm-wood-and-glass cabinetry with brass accents, one **jewel-tone** (sapphire + emerald) velvet accent.

## Retrieval stress test FIRST (this scene's kickoff)
Embedding-only availability sweep (see `retail_store.md` for the loop). **34 jewelry queries,
ZERO hard gaps** — every top-1 ≥ 0.399. Strong (>0.6): glass display cabinets/vitrines,
reception/showcase counters, POS terminal, ornate gold mirror (**0.855**), oval/floor mirrors,
crystal chandelier, velvet armchair, plant, neon sign, marble pedestal, safe. **Soft spots a
substitute covers (no ingest):** "cash register" (0.40 → the **POS touchscreen** is 0.72),
"jewelry cleaning desk" (0.48), and the whole family of jewelry **busts/stands** (0.42–0.59 →
returns *decorative sculptures on stands*, **not** real jewelry busts). That last one is the key
finding — see below.

## The identity-prop gap → show the PRODUCT, not the fixtures (the central lesson)
The stress test's similarity NUMBERS looked fine for "necklace/ring/bracelet stand" (~0.5), but
the returned **meshes** were decorative agate/shell sculptures on stands — recall ≠ quality (the
florist "asset-mesh trap"). **v1 mistake:** I pivoted the identity to the strong *fixture* — a
glass display vitrine repeated ×6 — assuming "cases = jewelry store." It didn't work: the vitrine
meshes are **empty glass** (no jewelry modelled inside), so the room read as a wardrobe/furniture
showroom, and 6 tall cabinets congested it. **v2 fix that worked:** a shop reads by its
**merchandise at viewing height**, so scan for the best *jewelry* props and **MASS them on low
display surfaces** — a `gold hand-shaped jewelry stand` (0.76, the star), a `white geode` gem
specimen (0.80), an `agate on a gold stand`, a `glass cloche`, `velvet jewelry boxes`, a `display
bust` — on a central hero table + the cash-wrap + the window pedestals. Keep the vitrines only as a
thinned backdrop (4). **General rule: to make a retail scene read as its category, put the CATEGORY'S
PRODUCT on the display surfaces at eye level — an empty display fixture names the fixture, not the
shop.** (Do a dedicated *prop* scan for this — the initial furniture-level stress test won't surface
"a diamond ring / a gold necklace / a gem on a stand.")

## Pool-routing reword (the other retrieval lesson)
"a … display **counter**" routes to `CountersRetriever` → **bar counters** (~0.40, wrong). A
jewelry showcase is a glass **display CABINET**, owned by `CabinetandShelfRetriever`: query
**"a glass display showcase cabinet with glass doors and shelves"** → 0.74 dark-wood glass
vitrines. Same reword-to-the-retriever's-class trick as the restaurant back-bar and the
"cash register"→"point of sale terminal" fix.

## Pinned assets
**Visible-jewelry props (the identity — massed on tables/counter/pedestals at viewing height):**
- **Gold hand-shaped jewelry stand** `hssd/20cb1bd807a71bfa93e1283f53e26380570ffbf3` — the star jewelry prop (0.76).
- **Geode / gem specimen** `hssd/3ae595cd7a3ec8a6abbe11b5e09563c03f300efb` (0.80).
- **Agate on a gold stand** `hssd/e8540f75ac3b5ae5897fedf516a04071ecdad299`.
- **Glass display cloche** `hssd/77989676b84972eca4446877471cb10bcf587b63` — a "precious piece under glass."
- **Display bust** `hssd/9eed1f0f783dc4214060c2e8ae4e3aaf50198006`.
- **Jewelry boxes** `future/09f5f6ca-c09f-4364-b189-9dd82f4712fc` — stacked velvet boxes; halve them (`scale(w*0.5)`).

**Fixtures / furniture:**
- **Display table (hero surface)** `hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f` — flat top for the massed props (reused from retail).
- **Cash-wrap counter** `hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860` — curved wood-front reception desk (reused from retail).
- **Display vitrine (backdrop, ×4)** `hssd/80bfb59e9d68cc3b03a1b04e626640e5d4e4396d` — dark wood + glass; a thinned gallery, NOT the star.
- **Consultation stool** `hssd/670c0caf8cb7df8466c675d7c91f7877840f9513` — sapphire barstool, gold frame.
- **Emerald armchair** `hssd/1672e0bc1abcdde2fd45c13b85d7bcf74f2f8236` — tufted velvet (**pinned to lock the jewel-tone palette**, see gotcha).
- Unpinned but high-recall: ornate gold mirror (0.86), floor mirror, marble pedestal, POS terminal, plant, neon sign.

## Program

[`jewelry_shop_v1.py`](jewelry_shop_v1.py) — the v3 program (real fixtures), phase-gated: phase 1 the
floor anchors (cash-wrap, the six low jewelry counters around the perimeter, stools, the featured
table, the lounge, the floor mirror, the pedestals, the walls and the door), phase 2 the surface
dressing that IS the identity (the busts / ring cubes / cushions massed at viewing height, the rug,
the plant), phase 3 the wall decor (focal mirror, neon sign), the storefront window and the lighting.

`workbench run skills/examples/jewelry_shop_v1.py --phase 1` builds the layout alone in ~1–2 min.

## What worked / gotchas
- **Show the PRODUCT at viewing height, not the fixture** (the v2 rescue). Massed jewelry props on
  low tables/counter/pedestals; an empty display cabinet reads as furniture, not a jewelry shop.
- **De-congest by cutting the TALL pieces, not the small ones.** The room felt cramped because of 6
  wardrobe-height vitrines blocking sightlines — dropping to 4 + up-scaling 0.8→0.9 fixed it while
  the low jewelry tables kept the floor lively. Tall cabinets are the congestion cost; low displays are cheap.
- **Reused the retail "central piece + perimeter loop + branded service wall" recipe** — swap garment
  rails → jewelry tables, mannequins → marble-pedestal jewelry displays, add stools at the cash-wrap.
- **Reword "counter" → "display cabinet"** to hit the showcase retriever, not bar counters.
- **PIN anything whose COLOUR carries the palette.** The accent armchair was left unpinned and the
  retrieval **flipped it pink → emerald between two runs at the same seed=42** (the VLM pick isn't
  deterministic). Since the jewel-tone palette leaned on it, pinned the emerald tufted chair
  (`…1672e0bc…`, 0.86). Reinforces the restaurant "pin-for-palette, not just type" rule.
- **Halve the jewelry boxes** — they render oversized at native scale; `b.scale(b.get_width()*0.5)`
  (uniform). (`.scale(target_width)` sets a uniform scale to hit a target width.)
- **Resisted the crystal chandelier.** It's the obvious "jewelry sparkle" fixture and scores 0.68,
  but `add_lighting` drops a tall fixture ~1.5 m into the room and its globes blow the scene out —
  used a flush LED. (Jewelry really wants track spots, which the fixture set doesn't have; flush + a
  warm palette is the safe read.)

## VLM feedback we hit and how we resolved it
- render 1: `rescale room by 0.8` (empty floor) + `rescale jewelry boxes 0.5` (oversized) + a
  `density=0.1` ceiling disc-band → `modulate_scale=0.8`, `jbox()` halving, `density` 0.1 → 0.05.
- render 2: VLM-clean. **But the USER caught what the VLM missed: "too congested" + "no visible
  jewelry / doesn't read as a jewelry shop."** The VLM's per-object geometry checks don't judge
  *category legibility* or *crowding-by-tall-fixtures* — a human read is the backstop. → the v2
  rework above (jewelry props at viewing height + 6→4 vitrines + 0.9).
- render 3 (v2): visible jewelry + open floor confirmed. Residual VLM notes were low-value —
  `rotate gold hand stand to face the viewer` (×N; the props are already visible from the main
  camera, and the pedestal pieces face the storefront *on purpose* as a window display) and the
  perennial `rotate chair/stool to face the [central] table` — **declined as noise/ambiguous**,
  same call as the retail cash-wrap and the dental-unit rotation.

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed.

## Meta-lesson
The VLM feedback loop converging is **necessary but not sufficient** — it verifies geometry, not
"does this look like the thing the user asked for." For a *retail* scene especially, gut-check
**category legibility** (is the product visible?) and **crowding** yourself before declaring done.
