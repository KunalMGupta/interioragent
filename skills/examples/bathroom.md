# Bathroom — worked example ("Marble & Brass Spa Bath")

Status: **phase-gated retrofit, NOT re-rendered.** The scene was built and iterated as
`scenes/work/bath_spa.py` (seed=21). [`bathroom_v1.py`](bathroom_v1.py) is that program retrofitted
with phase gating (2026-07-13): `lint_program`-clean, layout / pinned ids / seed / comments
preserved verbatim. **It has NOT been re-run or re-rendered since the retrofit, so the phase-1 /
phase-2 / phase-3 splits are UNVERIFIED** — no build, no render pass, no VLM vote has been taken
against the gated program. Treat the phase boundaries as a proposal until someone runs
`--phase 1`.

Open items carried over from the original build (see [Possible refinements](#possible-refinements-not-blocking)):
the back-wall window rendered **black** in `room_views`, and the room read a touch tight. The scene
was never promoted out of `scenes/work/`.

## Prompt(s) this covers
- "a pretty / spa-style master bathroom."
- Any master-bath / ensuite / powder-room brief where the fixtures (tub, vanity, shower, WC) are the
  content. **Read this before ANY bathroom, and before any room whose furniture is bundled
  plumbing/appliance sets.**

## Plan summary (from the planner)
"Marble & Brass Spa Bath." White marble **grounded with warm wood + brass**: a freestanding oval tub
as the hero, under a window, with a **statement brass chandelier** over the soak zone; a walk-in
glass shower as the open counterpoint; a **warm-wood double vanity** with a marble top and brass
mirrors as the grooming zone; ferns / eucalyptus, candles and plush towels for the spa ritual.

**Always run the planner first (`idsdl__plan`).** Skipping it on this prompt gives you a generic
three-piece bath — tub, sink, toilet against three walls — with no hero, no ritual layer, and no
palette. Every good decision in this scene descends from the plan naming the tub as the hero and
the wood/brass as the warming agent.

**Asset kickoff finding — a rich library, so the work was FIXTURE QUALITY, not ingests.** The
category browse returned tubs, glass showers, double vanities, brass mirrors, toilets, linen towers,
towel ladders, plants, candles and botanical art — **all abundant**. No ingests, no new pool needed
(confirmed via `gallery`). That *finding* is itself the payoff of the asset-first gate: it said
"move straight to placements," and everything below is what actually bit instead.

## The layout idea: TWO HEROES FACING ACROSS THE LONG AXIS

The two big fixtures take the two **long** walls and look at each other across an open barefoot
lane; the two **short** walls take the boxy, plumbing-bound, vertical stuff. It is the same "every
wall gets exactly one job" discipline as [`bedroom.md`](bedroom.md) and
[`hospital_room.md`](hospital_room.md), but with **two** heroes instead of one — which is why the
job assignment is decided by *fixture shape*, not by importance.

| Wall | Job | Why it is that |
|---|---|---|
| back (long) | the **tub hero**, window over it, chandelier above | a soaking tub only reads as a *spa* if it is **freestanding** — crammed into a corner it turns back into a builder's alcove bath, and the whole plan dies |
| front (long) | the **double vanity**, facing the tub | the second-widest run in the plan, so it takes the second long wall; the two heroes face off down the short axis instead of fighting for one wall |
| left (short) | the **wet zone** — walk-in shower + wall-hung toilet | both are short, boxy and plumbing-bound: they share a short wall and leave the long walls to the heroes |
| right (short) | the **door** + the tall linen tower | the entry wall does the storage — a linen tower is a vertical strip, the only thing that fits beside a door |
| centre | deliberately **open** | the barefoot lane. A bathroom you cannot walk through is not a spa |

**The rule to steal:** assign walls by **fixture footprint shape**, not by how important the fixture
is. Long runs → long walls. Vertical strips and boxes → short walls. Openings → whatever is left.
Get that backwards and the tub ends up in a corner with the shower hogging a 4 m wall.

## Pinned assets (audited previews)

Every fixture pin here exists because **the caption and the scale both lie** — see Lesson 1.

| Role | id | Why pinned |
|---|---|---|
| tub | `hssd/4106160b…` | proportions are right (≈0.20:0.10:0.06, a real tub) but the metadata scale says **0.2 m long**. Pinned so the uniform width-fit is applied to a *known* mesh |
| vanity | `hssd/44a88da9…` | warm-wood **double**, marble top — a SET asset whose mesh spans cabinet → sinks → **its own wall mirror**. Pinned so the vanity tagger's `double` → 1.5 m / floor-mount metadata is the one applied |
| bath caddy | `hssd/c758aecb…` | the single prop that names the tub as a *soak* rather than a bath |
| bath mat | `hssd/a63f792f…` | a **verified-FLAT** mat — see Lesson 4 |
| towel ladder | `hssd/f63203ce…` | a ladder that actually **carries a towel**; the bare-ladder picks read as a stepladder someone left in the bathroom |

The shower, toilet, linen tower, palm, fern, candles and botanical print are **unpinned** —
retrieval is reliable for them; it is the *sets* that need a pin.

## Asset gaps
**None.** This is the rare category where the dataset is genuinely rich (see the kickoff finding
above), and it is worth knowing: not every scene needs an ingest. Contrast
[`operating_room.md`](operating_room.md) and [`clothing_store.md`](clothing_store.md), where the
category does not exist in the pool and the whole scene is an ingest problem. The bathroom's
difficulty is **quality**, not **coverage** — which is a *different* failure mode, and the one this
example teaches.

## Lesson 1 — the scale metadata is BROKEN for bathroom fixtures; fix it UNIFORMLY, by width

The pinned tub resolves to **0.2 m long**. Not a rounding error — a bath the size of a soap dish.

Fix it by enforcing the real size, but **scale UNIFORMLY**: capture the mesh's own w/h/d, compute a
single factor from the target width, apply it to all three axes.

```python
def _fit_width(o, target_w):
    w0, h0, d0 = o.get_width(), o.get_height(), o.get_depth()
    f = target_w / max(w0, 1e-6)
    o.scale_only_width(w0 * f); o.scale_only_height(h0 * f); o.scale_only_depth(d0 * f)
    return o
```

Three sub-rules, each one earned:
- **NEVER scale the axes independently** on a fixture. A tub, a sink or a vanity that has been
  stretched on one axis reads instantly as wrong — the basin goes oval, the drawer fronts go
  rectangular. Per-axis scaling (`_dims`) is reserved for meshes whose *proportions* are genuinely
  wrong, which in this scene is exactly two: a shower enclosure modelled too short, and a linen
  tower modelled too tall.
- **`obj.scale(w)` is buggy on a pre-scaled asset** — use a factor computed from the *captured* whd,
  as above.
- **Do the sizing BEFORE you build any group.** `place_on_top`, `place_on_left` and `place_rug` all
  position against the anchor's footprint. Size the tub after you have hung the caddy off it and the
  caddy is sized against a soap dish.

The general form of this lesson is now everywhere: an asset's **scale is a guess**
([`operating_room.md`](operating_room.md): "an ingested asset's caption AND scale are both VLM
guesses"; [`hospital_room.md`](hospital_room.md): "uncurated hero → pin id + UNIFORM rescale"). But
note the boundary [`nursery.md`](nursery.md) draws: bad **scale** is fixable by rescaling; bad
**proportions** are not — swap the mesh.

## Lesson 2 — "SET ASSETS": a vanity and a toilet are bundled COMPLETE UNITS, not parts

The defining lesson of this scene. A bathroom fixture is retrieved and placed as **one thing**, and
it already contains the things you were about to add to it.

**The vanity bundles its own wall mirror.** The mesh spans cabinet → sink → mirror, ~1.6 m tall.
Consequences:
- **Do NOT hang a separate mirror above it.** The plan asked for *two brass-framed mirrors*; adding
  them made them **interpenetrate the vanity's own mirror**. The program hangs **zero** mirrors, and
  the planner's request is satisfied by the mesh.
- **Do NOT `place_on_top` a vanity.** The top is complex (sinks, faucets, a raised backsplash) and
  stacked decor sits unreliably on it. If you want counter decor, **retrieve a vanity variant that
  already bundles it** — do not build it up from parts.
- Vanities are **type-tagged** (`tools/build_vanity_tagger.py` → `IDSDL/datasets/assets/vanity_types.json`):
  floating / single / double / extra_wide → a real width and a floor-vs-wall mount, applied
  **transparently inside `AddAsset`** (`SceneProgRoom._apply_vanity_metadata`). The program just
  `AddAsset`s a vanity and places it — no import, no helper — and `place_on_*_wall_*` auto-reads
  `obj.mount_bottom`. A `floating` vanity would auto-narrow AND wall-mount with **no extra code**.

**The toilet bundles cistern + flush buttons + TP holder + brush** into one bbox, so the *seat* — the
part your eye measures — reads small. Toilets are uniform in the real world, so unlike vanities they
need **no per-asset tagging**: one consistent uniform scale (≈1.5× the metadata width, i.e.
`_fit_width(…, 0.90)`) fixes the whole category. Curated pool `bathroom_toilet_set.json` +
`BathroomToiletSetRetriever` (registered; "toilet" was **removed** from the generic bathroom
retriever so the query routes there).

This is the same family as [`kitchen.md`](kitchen.md) — the extreme version, where the entire room
is ONE fitted unit and phase 2 is deliberately empty — and as [`bedroom.md`](bedroom.md)'s beds,
which ship fully dressed with their bedding. The generalisation:

> **When a mesh is a SET, your job is to place it and STOP.** Every `place_on_top`, every companion
> object, every "and a mirror above it" is a bug in waiting. The set already has one.

## Lesson 3 — `bottom=` is how a wall-hung fixture gets off the floor

Floating vanities, wall-hung toilets and wall basins must sit at a **mounted height**, not
floor-aligned. `bottom=` was added to all **12** `place_on_*_wall_*` methods for exactly this, and
`AddAsset` sets `obj.mount_bottom` on a tagged floating vanity so the placement reads it
automatically.

Two traps the later examples turned up and that you inherit here:
- a `bottom=`-mounted piece **always trips the floaters lint** ([`clothing_store.md`](clothing_store.md)) —
  a false positive, and [`prison_cell.md`](prison_cell.md) documents the same thing on a wall-hung
  basin;
- a `bottom=`-mounted piece must be `ignore_overlap`, which `GradSolver.overlap_pairs` then filters
  out — so **nothing ever checks it again**, and it can end up embedded inside its neighbour
  ([`closet.md`](closet.md)). Check the AABB by hand.

## Lesson 4 — a rug must be modelled FLAT, and many "bath mats" are not

Many `bath mat` picks are authored **UPRIGHT** — thin in *depth* rather than thin in *height*, as if
they were hung on a rail. `place_rug` scales width and depth; the upright **height survives**, and
the mat comes out as a giant slab standing in the middle of the room. The export is **yaw-only**, so
it cannot be tilted flat afterwards. There is no recovery.

`place_rug(desc, size, asset_id=)` now takes a pin, and **warns when the chosen rug is not flat** —
so the fix is: pin a verified-flat mat and heed the warning. The pinned mat above is that.

This is the head of a family of "the mesh's *form factor* is wrong and no amount of scaling saves
it" traps: [`art_studio.md`](art_studio.md) generalises it (`place_on_top` shatters on a *skeletal*
anchor), and [`nursery.md`](nursery.md) states the rule flatly — **bad proportions cannot be scaled
away; swap the mesh.**

## Lesson 5 — `WallOverlapConstraint` checks ACTUAL GEOMETRY, because slot-counting missed a real overlap

The wall-overlap check used to count occupants per wall/slot bucket. That is blind to two objects
that are in *different* buckets but physically intersecting — and it silently passed a **wall mirror
/ art print interpenetrating the toilet**.

It now runs `check_geometric_overlap` (`IDSDL/constraints.py`, 5 mm margin) against the real AABBs.
The lesson generalises past bathrooms:

> **A clean constraint string is not proof of a clean room** — it is proof that the checks you have
> did not fire. Every example that has been re-read carefully has found something the loop was
> structurally unable to see ([`fast_food.md`](fast_food.md): a POS screen turned broadside;
> [`laboratory.md`](laboratory.md): a microscope sunk *through* its bench; [`pantry.md`](pantry.md):
> shelves that were simply empty). Crop-zoom the render.

Applied here: the left wall is **full** (shower + toilet), so the program hangs **no art on it at
all** — one botanical print, on the right wall. Do not hang wall decor on a wall whose furniture
already occupies the mounting band.

## Lesson 6 — an all-white marble room BLOWS OUT to white; a saturated mid-tone wall is the fix

Every surface in the brief is high-albedo: marble floor, marble walls, white tub, white sinks, white
towels. Put a window in it and the surfaces **inter-reflect the daylight into a white-out** — the
render comes back as a bright empty box with no readable geometry, and the VLM loop, which is
judging a blown render, will happily tell you nothing is wrong.

The fix is **not** to dim the window. It is to give the room a **saturated mid-tone wall**:

```python
room.place_walls(floor_texture="honed grey marble tiles",
                 ceiling_texture="white", wall_texture="soft sage green")
```

Soft sage was also the brief's own accent, so the fix cost nothing — and the honed **grey** marble
floor (not white) keeps the tonal range. This is exactly [`hair_salon.md`](hair_salon.md)'s
blush-walls trick, and `modulate_scale=0.72` pulls the shell in so it is not a *bright empty* box on
top of being a bright one.

Since this scene was built, the pale-room problem has been chased down further, and you should read
the follow-ups before repeating the fix blind:
- [`nursery.md`](nursery.md) — **an all-white room is an EXPOSURE trap**, and the honest dial is the
  sky (`IDSDL_SKY` ≈ 1.2), which works from the **shell** but is ignored by MCP `run_scene`;
- [`laundry_room.md`](laundry_room.md) — the small bright all-white room again, fixed with
  **`scene.light_budget = 180`**, which is a *scene attribute* and therefore survives the warm MCP
  server (unlike `IDSDL_SKY`). It also records that **an overexposed render corrupts the constraints
  judged from it** — spurious `rotate door by 90` flags that vanished when the exposure was fixed.

The sage wall is a *palette* fix and it works; the exposure dials above are the *lighting* fix and
they did not exist when this scene was built. A rebuild should use both.

## Program

[`bathroom_v1.py`](bathroom_v1.py) — the `scenes/work/bath_spa.py` program, retrofitted with phase
gates. `workbench run skills/examples/bathroom_v1.py --phase 1` should build the layout alone in
~1–2 min.

| Phase | Builds |
|---|---|
| 1 | the five fixtures, sized to true dimensions (`_fit_width` / `_dims`), the two heroes on the long walls, the wet zone + linen tower on the short walls, `place_walls`, `place_door` |
| 2 | the spa ritual — bath caddy `place_on_top` the tub, fern and candle cluster beside it, the flat bath mat, the corner palm, the towel ladder |
| 3 | the botanical print, the window over the tub, the brass chandelier over the soak zone |

Two structural notes:
- **`place_walls` and `place_door` are UNGATED.** The door's automatic clearance shapes the floor
  solve, so deferring it to phase 3 would change the very layout that phase 1 exists to validate.
- **Every `place_on_top` / `place_on_left` gate sits INSIDE its `with` block.** A group compiles on
  `__exit__`, so an op registered *after* the block never runs — the prop is silently GONE, the
  count still increments, and the loop stays clean. [`prison_cell.md`](prison_cell.md) minted that
  lesson by losing a stack of books to it.

**Honest caveat:** the gated program is lint-clean and the splits follow the convention, but it has
**not been re-run**. Nothing here is claimed to have been rendered since the retrofit.

## What worked / gotchas
- **The `_fit_width` / `_dims` split.** Uniform-by-width for anything whose proportions are fine
  (tub, toilet); per-axis only for the two meshes whose proportions are genuinely wrong (shower
  enclosure too short, linen tower too tall). Naming the two helpers separately is what keeps the
  distinction honest at the call site.
- **Doing the sizing before any group is built.** Everything downstream positions against a
  footprint; a wrong footprint poisons the whole surface layer.
- **The vanity needing zero code.** `AddAsset` on a tagged vanity does the width + mount for you.
  That is the payoff of the tagger, and the model to copy for any other bundled-set category.
- **Leaving the left wall art-free.** The wall was already full. Wall decor is not an entitlement.
- **`modulate_scale=0.72`.** The scene still "reads a touch tight" per the original notes — see
  refinements. It is not obvious this number is right; it is obvious that 1.0 was wrong.

## VLM feedback we hit and how we resolved it

**Not recorded.** This scene predates the convention of logging the feedback loop, and its VLM
history — the votes, the passes, the ones declined — was **never written down**. The lessons above
survive only because they were captured in the program's comments and in the original `.md`.

That is a real gap, and it is the one thing this example cannot teach. **If you rebuild this scene,
log the votes** — including the arithmetic for any you decline. The one piece of render-derived
evidence that *was* recorded is in the refinements below (the black window, the tight room), and it
is anecdotal, not a vote train.

## Manual constraints used

None beyond the defaults. The door clearance comes free from `CategoryClearanceConstraint`. What
this scene *changed* was a default: `WallOverlapConstraint` now runs `check_geometric_overlap`
(5 mm margin) instead of counting slot buckets — see Lesson 5. That is a core fix this scene forced
out, not a manual constraint the program declares.

## Possible refinements (not blocking)

- **Run the gated program.** Phases 1/2/3 are unverified. Nothing in this file claims otherwise, and
  the claim closes only when someone runs `--phase 1`.
- **The back-wall window rendered BLACK** in `room_views` (the original note blamed sun direction —
  side-wall windows lit fine). Since then, [`greenhouse.md`](greenhouse.md) established that the
  "black window void" was a **renderer bug (a transparent film), and it is FIXED** — roughly six
  prior scenes had accepted it as a law of nature. So this open item is *probably* already gone.
  **Unverified here** — this scene has not been re-rendered.
- **The room reads a touch tight** at `modulate_scale=0.72`. Read that against
  [`bedroom.md`](bedroom.md)'s rule that a room-size vote on a half-dressed room is voting on a room
  that does not exist yet — and against [`kindergarten_v1.md`](kindergarten_v1.md)'s "fill the floor,
  THEN shrink."
- **The brass chandelier and the brass hardware never really landed** as a palette. The wood + the
  sage carry the warmth; the brass is a claim the render has not been shown to support.
- **Never promoted** out of `scenes/work/bath_spa.py` to `scenes/bathroom.py`.
