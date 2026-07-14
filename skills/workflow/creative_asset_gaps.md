# Creative-space asset gaps — the ingest shopping list

What the dataset actually has for **creativity scenes** (art studio, museum/gallery, ceramics,
sculpture, printmaking, photography, textile atelier, design/maker studio), what it is missing, and
therefore what to go source as `.glb`. Produced by a 60-query stress test, 2026-07-13.

## The one-sentence finding

**The dataset is home-furniture biased, so every PROFESSIONAL CREATIVE TOOL comes back as its
DOMESTIC or TOY analogue** — and at a similarity score that looks perfectly healthy:

| You ask for | You get | sim |
|---|---|---|
| a wooden artist easel holding a canvas | a **kids' easel with a crayon drawing** of a sunny house | 0.65 |
| a pottery kiln | a **casserole dish** | 0.47 |
| a potter's wheel | a **ceramic pot** | 0.42 |
| an antique printing press | a **cast-iron doorbell** | 0.52 |
| a set of oil paint tubes | **coloured pencils** | 0.56 |
| a photography softbox on a stand | a **microphone stand** | 0.45 |
| a weaving loom | a **woven basket** | 0.47 |
| stone carving chisels and mallet | a **kitchen knife block** | 0.48 |
| a museum rope stanchion | a **plain metal rod** | 0.41 |
| a wire drying rack for prints | a **kids' paint drying rack** | 0.54 |

This is the art_studio lesson generalised: the tool is the identity of a creative room, the tool is
the gap, and **the loop cannot see the substitution** — geometry is legal, only the semantics are
absurd. A scene shipped on these picks reads as a *kindergarten* or a *kitchen*.

By contrast the dataset is **rich in the OUTPUT of creativity** (sculptures, busts, framed
paintings, art books) and in **gallery furniture** (plinths, display cabinets, track lighting).
So: **museums are buildable today; workshops are not.**

## Method (and its one caveat)

Embedding **recall** — top-5 dataset descriptions per query
(`IDSDL/service/core.py:browse`, one dot product against `all_embeddings`). *Not* the full router.
The full route + visual-VLM pick runs **~3.5 min/query** (4 h for this list); recall runs in under a
minute, and recall is what a gap audit actually asks: **if the top-5 for "potter's wheel" contains
no potter's wheel, no amount of visual picking will conjure one.**

> **Caveat: a caption is not a mesh.** Everything below marked *HAVE* is recall-verified, not
> eyeball-verified — `browse`/`show(n, big=True)` each preview before you pin it. The plinths, the
> easel pool and the paint props below WERE eyeballed.

---

> ## ✅ STATUS 2026-07-13: TIER 1 IS INGESTED (`art_done.zip`, 68 meshes, Kunal)
> Every Tier-1 item below has now been sourced and ingested as `custom/*`. Highlights, all
> preview-verified: **three real 2.00 m floor easels** — painted canvas `custom/fa1ed245`, blank
> canvas `custom/3ae58737`, bare `custom/f65f7c3d` — plus a paint-box/palette prop set
> `custom/65b64100`, an art supply cart `custom/4d5c0810`, a drafting desk `custom/1d3219db`,
> **a potter's wheel, a Vandercook letterpress, a Greco-Roman loom, a Durst enlarger, a softbox +
> backdrop + 19 photo rigs, a queue-barrier stanchion**, and a museum trove (Rosetta Stone,
> Nefertiti, three Louvre statues, samurai + knight armour, two dinosaur skeletons, a dodo).
> `scenes/art_studio.py` is REBUILT on the real easels — see `../examples/art_studio.md` §0.
>
> **Two ingested meshes were REJECTED at the contact sheet** (filenames lie; the preview is the
> evidence): `canvas_stretcher` renders as a grey tapered MONOLITH, not a canvas; and
> `easel_stool_and_canvases` is flat-shaded STYLISED red/blue art that clashes with a photoreal
> room. Yield 11/13 on the art meshes — better than operating_room's 6/20, because the source glbs
> were already correctly scaled.
>
> **Still missing after this ingest:** paint-stocked SHELVING (the studio shelf is still a
> book-filled bookcase), a museum wall-label placard, and a bare stretched canvas.
> **Still to do:** a `CreativeStudioRetriever` pool — until it exists, "an artist easel" routes to
> `PresentationFixtureRetriever` (boards/projectors) and these meshes are invisible to plain
> `AddAsset`. **Pin them by id.**

# TIER 1 — source these (each one unblocks a scene; no acceptable substitute)

1. **A floor-standing artist easel — one BARE, one HOLDING A CANVAS.** *The single highest-value
   mesh on this list.* Today the only true artist easel is a **1.00 m tabletop** A-frame
   (`hssd/5e19cedd`) with nothing on it, and the picker prefers a kids' crayon easel over it. It also
   cannot be dressed: `place_on_top` **shatters on a skeletal A-frame** (it seats a postage-stamp
   canvas on the crossbar), and there is no vertical lift on an anchor-group placement — so
   art_studio v1 had to stand the canvas on the FLOOR against the easel. A single mesh with the
   canvas modelled in fixes both problems at once.
2. **Bare stretched canvases** — blank, and a leaning stack. Every "canvas" in the dataset is a
   *finished framed picture*; there is no blank canvas, no stretcher-bar back, nothing "in progress".
   Needed for the easel, for drying, and for the leaning stacks that make a studio read.
3. **A painter's supply kit** (bundle): a palette with wet paint, loose paint tubes, a jar of
   brushes, paint cans/jars. Exactly ONE genuine prop exists (`future/4a9dc3a5` — brushes in a glass
   jar + palette + tubes) and it is carrying the entire category on its own; everything else routes
   to coloured pencils or kitchen utensil holders.
4. **A potter's wheel** — the hero of a ceramics studio. Nothing close exists.
5. **A pottery kiln** — the other ceramics hero. Currently returns a casserole dish.
6. **A museum rope stanchion + velvet rope** — the single most legible "this is a museum" prop, and
   a total gap (returns a metal rod). Cheap to model, huge legibility payoff.
7. **A printing press** (cast-iron / letterpress) — the hero of a printmaking studio. Returns a
   doorbell.
8. **Photography lighting: a softbox on a stand + a seamless backdrop roll.** tv_studio found a
   silhouette substitute (a "floor lamp with a tripod base" reads as a light stand) but it is a
   workaround; a real softbox + backdrop unblocks a photo studio properly.
9. **A weaving loom** — the hero of a textile/weaving studio. Returns a basket.
10. **A drafting table with a TILTED top** — the tilt IS the identity; the dataset has only flat
    adjustable desks (0.60), which read as an ordinary office.

## TIER 2 — nice to have (a substitute exists, but it compromises)
- **Taboret / art-supply cart with paint drawers** — metal trolleys substitute acceptably.
- **A paint-splattered drop cloth / tarp** — no floor-cloth mesh at all (returns abstract wall art).
- **Sculptor's modelling stand with an armature** — a bust-on-pedestal is a passable stand-in.
- **Stone-carving chisels & mallet; pottery hand tools** — both return kitchen cutlery (the
  operating_room "surgical instruments → kitchen cutlery" trap, again).
- **A block of uncarved marble** — a marble pedestal substitutes.
- **Museum wall-label placards** — returns a chalkboard; a small plaque substitutes.
- **A dinosaur skeleton / fossil** — returns a dinosaur *poster* and a *toy* dinosaur. Only needed
  for a natural-history museum.
- **Spray paint cans** — returns a fragrance spray bottle.
- **A darkroom enlarger** — returns a photocopier.
- **A 3D printer** — returns a bench.
- **Thread spool rack; bolts of fabric** — folded-fabric stacks substitute weakly.
- **Rolls of paper in a tube rack** — `custom/d2a76f62` (a rack of fabric rolls) substitutes.
- **A light box / tracing table** — a glass-top desk substitutes.

---

# DO NOT SOURCE — these are already good (pin them)

**Museum / gallery is the best-covered creative category — it is buildable TODAY:**
- **Bare display plinths** (eyeballed — genuinely empty blocks, and unlike an easel a plinth has a
  REAL flat top, so `place_on_top` works): `future/58d2d3ee` (marble), `future/ed0621cc` (marble),
  `hssd/9d9b3a0d` (white column), `custom/5f92a4aa` (white cube).
- **Classical sculpture — RICH:** marble bust `hssd/74463d60` (0.74), classical figure w/ trident
  `hssd/a858cdf5` (0.69), bronze bust on pedestal `future/1847b0ef` (0.73), female torso
  `hssd/7f9c9547`.
- **Track lighting with adjustable spotlights — EXCELLENT (0.77):** `hssd/82e45a03`,
  `hssd/3ab03fd3`. Gallery lighting is a solved problem. *(But remember `add_lighting` wants a
  FLAT/FLUSH fixture and spends a fixed 500 W across N — use these as geometry, keep density low.)*
- **A suit of armour on a stand (0.78!):** `future/0ec9e67a`.
- **Gilt-framed oil paintings — RICH:** `hssd/54c900dd`, `hssd/6a669a56`, `future/7b0ad909`.
- **Glass display cabinets** (passable vitrines): `hssd/05be6be9`, `hssd/80dea841`.
- **Gallery bench:** `hssd/804b9e64` (backless). **Kiosk:** `hssd/8cf3b150` (touchscreen).
- **Amphora-ish antique vases:** `hssd/64e73ca8`, `hssd/1d6275b1`.

**Elsewhere, already solid:** dress form / tailor's dummy (`future/34f62b6f`, `hssd/713d48d7`),
sewing machines (3 of them), cork & bulletin boards *with pins and notes on them*
(`hssd/b728cc95`, `hssd/ee5d696b`), workbench with a vise (`hssd/b08ab647`), stacks of art books
(`hssd/c9af68a5`, 0.75), stepladders, rolling trolleys, buckets, stools, the paint still life
(`future/4a9dc3a5`).

---

# Scene readiness, at a glance

| Scene | Status |
|---|---|
| **Museum / art gallery** | **BUILD NOW** — plinths + statues + track light + gilt frames all real. Only rope stanchions missing. |
| **Art studio** | **BUILT** (`scenes/art_studio.py`) with 2 compromises — easel + canvas ingest would close them. |
| **Design / maker studio** | Mostly buildable — needs the tilted drafting table. |
| **Sculpture workshop** | Half — output (busts/plinths/workbench) real, TOOLS missing. |
| **Textile atelier** | Half — dress forms + sewing machines real; loom/spools missing. |
| **Ceramics studio** | **BLOCKED** — no wheel, no kiln. |
| **Printmaking studio** | **BLOCKED** — no press. |
| **Photography studio** | **BLOCKED-ish** — silhouette substitutes only (see tv_studio). |

---

# The ingest contract (read before you download anything)

From operating_room v2 — a raw Sketchfab-style zip breaks the contract **three ways, all silently**:
- **Y up, front facing +Z, width along X, real-world METRES.** Ingest does not re-orient or re-unit.
- **ONE mesh per glb.** Both loaders keep `imported_objs[0]`, so a multi-mesh glb renders
  **disassembled** with the rest stranded at the origin. Fix at the source with Blender `join()` —
  never a trimesh concat (it strips materials → flat white).
- **Centred origin.** Off-centre origins produce `[Lint] FLOATS/SUNK` on every build. Fix with
  `origin_set(ORIGIN_GEOMETRY, BOUNDS)`. *Recentring rewrites the file → the sha1 id changes → re-pin.*
- After ingest, the VLM's **caption AND scale are both guesses** — a mis-captioned asset is invisible
  to NL retrieval (so **pin by id**), and its `scale` silently resizes the mesh (so `get_whd()` +
  height-fit every pin).
- **Expect ~30% yield.** Build a contact sheet of the ingested previews and eyeball it BEFORE writing
  placements.

Then: `python -m IDSDL.ingest <zip> --category <pool>`. A new **`CreativeStudioRetriever`** pool
(easels, canvases, paint props, wheels, kilns, presses, looms, stanchions) would be worth adding at
the same time — otherwise "an artist easel" keeps routing to `PresentationFixtureRetriever` (whose
pool is boards/projectors) and the ingested meshes stay invisible to plain `AddAsset`.
