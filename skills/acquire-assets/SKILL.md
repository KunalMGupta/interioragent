---
name: acquire-assets
description: >
  Use when the library does not HAVE an asset a scene needs — when retrieve() keeps returning
  the wrong category, a stress test flags a gap, or the user asks to find / download / source /
  generate 3D models (Sketchfab, Meshy, "get me a proper reception desk"). Runs the automatic
  search-and-ingestion pipeline in IDSDL/shop: search -> download -> normalize in Blender ->
  VLM triage -> verify -> ingest, skipping what it cannot judge and asking the user about the
  rest. Also read this before changing anything in IDSDL/shop/ — the normalization fixes and the
  triage gates in there are all load-bearing, and each one is here because it failed first.
---

# Skill: acquire assets the library doesn't have

The library used to be a closed set: 29k dataset assets, plus whatever `.glb`s a human had
already downloaded, hand-oriented and hand-scaled. `IDSDL/shop` makes it open — a query goes in,
a normalized, verified, retrievable asset comes out — and the human is only consulted about the
things a machine genuinely should not decide alone.

```bash
python -m IDSDL.shop search "reception desk"            # look, ingest nothing
python -m IDSDL.shop run "reception desk" --count 6     # the whole pipeline
python -m IDSDL.shop run "..." --manual                 # ...and ask me about the hard ones
python -m IDSDL.shop apply shops/<batch>                # act on my answers in HELP.md
python -m IDSDL.shop remove custom/<sha>                # un-ingest a mistake
```
From an agent, the same thing is `shop_search` / `shop_run` / `shop_apply` over MCP; `shop_run`
re-warms the retrievers, so an asset ingested mid-session is retrievable in that same session.

## The contract you are meeting

`IDSDL.ingest` assumes — and never checks — that a `.glb` is **one mesh, real-world metres,
Y up, front facing +Z**. Internet models satisfy none of that. The shop's whole job is to make
them satisfy it, which reduces to three judgments a human used to make by eye:

1. **which way is the FRONT** (the library's front is glTF `+Z`, which is Blender `-Y`),
2. **how BIG is it really**,
3. **is this even ONE object** (or a scene, a set, a pack).

Everything else is mechanical.

## The one idea that makes it work: never let the model do axis arithmetic

The preview is a strip of four straight-on renders, **numbered and captioned**:

```
PANEL 1 (+Y side)   PANEL 2 (-Y side)   PANEL 3 (+X side)   PANEL 4 (-X side)
```

The VLM answers *"which PANEL shows the front?"* — a question about a picture. Python then does
the axis arithmetic, which is the part that always went wrong when a human did it by eye:

| front is on | rotate about Z |
|---|---|
| panel 2 (-Y) | 0 |
| panel 1 (+Y) | 180 |
| panel 3 (+X) | -90 |
| panel 4 (-X) | +90 |

Then — this is not optional — the pipeline **re-renders the file it actually wrote** and asks a
second VLM whether the front really did land on panel 2. A wrong front is invisible downstream
(the placement code dutifully turns the asset's *back* to face the room), so it must be caught
here or never. If the check fails, rotate by the residual and retry ONCE, then stop guessing and
ask the user.

Know what that verify pass does and does not buy you: it catches **rotation-math** errors, not
**judgment** errors. If the model thinks a shelf's back is its front, it will think so just as
firmly on the re-render. Which is why the front is judged twice, differently.

## Agreement, not confidence

Every gate in `triage.py` is a *disagreement* detector, because a single confident answer is
exactly what put a wall shelf into the library back-to-front during development.

- **Front: two lenses.** One VLM is asked which side is the front; a second is asked, in
  completely different words, *"if you walked up to use this, which side would you stand at?"*
  They must agree. On the ground-truth set, this is what caught the shelf (judge said the flat
  back, the second opinion said the shelved side — the second one was right).
- **Size: vision vs. the library.** The VLM is the worst estimator we have of real-world size —
  it is guessing metres from an object on a grey background with no reference. But the library
  holds ~29k curated real widths and we own the embedder that indexes them, so we look the object
  up among its nearest neighbours and take their median width. Measured against ground truth:

  | | lounge chair (0.5 m) | 3-seat sofa (2.5 m) | coffee table (1.2 m) |
  |---|---|---|---|
  | VLM vision | 0.62 (+25%) | 3.11 (+24%) | 2.41 (**+100%**) |
  | library neighbours | 0.60 (+20%) | 2.35 (-6%) | 1.35 (+13%) |

  So **the prior sets the size and vision is the cross-check.** When the two disagree beyond
  `[0.55, 1.8]x`, that usually means the object was *misidentified*, not mis-measured — our shelf
  came back as a "wooden panel", and the library's wooden panels are 0.6 m, not 2.7 m — and a
  misidentified object is precisely what a human should look at. (Tunable:
  `triage.PRIOR_MIN_SIM`, `PRIOR_LO/HI`.)

## Skip vs ask — the distinction the whole design rests on

`auto` mode "skips the hard ones" and `manual` mode "asks for help", so the two buckets must
mean genuinely different things:

- **skip** = mechanically unusable, never worth a human's minute: several separable units in one
  file (the human used to split these by hand — we do not guess), not an interior object,
  degenerate geometry, animated/rigged, no glTF offered.
- **ask** = a judgment we decline to make alone: the two front judges disagreed, the size fights
  the library, confidence is low, the self-verify failed twice.

Filing an *uncertain* asset as a *skip* silently throws away a good model — that is the failure
this split exists to prevent. Nothing is ever dropped quietly either: skips are listed on the
board too, so you can overrule them.

## HELP.md — how the pipeline asks

Same idiom as the scene review board (`tools/review_board.py`): one section per asset, the
labelled strip, the hero view, why it needs you, and a block you edit in place. Regenerating
never destroys an answer.

```
#### Your call — edit the block below
action: accept
front:  4   # it's a wall bookshelf — the openings are on panel 4, not the flat back
size:   2.5
anchor: width
```
`python -m IDSDL.shop apply shops/<batch>` reads those, normalizes with YOUR numbers (a
user-set front overrules the verifier — you looked at the render, it only guessed), ingests, and
regenerates the board.

**No Sketchfab token is the normal state, not an error.** Search is public; downloading needs a
free token (`SKETCHFAB_API_TOKEN` in `.env`). Without one, every candidate becomes a
`needs_download` entry on the board with its link, and anything the user drops into
`<batch>/inbox/` is picked up by `apply` — name the file `<key>.glb` and it inherits that
candidate's licence and attribution. The token is the only thing between the manual flow and the
automatic one.

## Licences are not optional

Every ingested asset carries `provenance` (source, uid, url, licence, author) into its library
metadata, and the run prints an attribution block. Default search filter is `permissive`
(CC0 + CC-BY); `commercial-ok` excludes NonCommercial. An asset whose origin we cannot name is
an asset we cannot ship.

## The Blender fixes in `bl_job.py` are load-bearing

Six of them, each one bought with real debugging time. Read the docstring before you "simplify"
any of them. Five came from the hand-rolled normalizer that preceded this
(`glb-shop-normalizer`); the sixth is ours:

1. **Unit-scale overwritten by resize** — join, then unparent by *assigning* `matrix_world`
   (the operator no-ops in `--background`), delete the empties, `transform_apply`. Otherwise a
   later `obj.scale = f` *replaces* the importer's cm->m scale instead of composing → 72x blowups.
2. **Quaternion rotation mode** — the importer leaves objects in `QUATERNION`, where assigning
   `rotation_euler` is silently ignored. Force `rotation_mode = 'XYZ'` first.
3. **The EEVEE enum name moves between Blender versions** — pick whichever the running build
   offers (`BLENDER_EEVEE_NEXT` on 4.5, `BLENDER_EEVEE` on 5.x).
4. **Camera clip planes cull large-unit models** — a model authored in millimetres is thousands
   of units tall and falls past the default far clip; it renders as a blank grey frame and the
   VLM calls it empty.
5. **UV-safe join** — Blender's Join merges UV layers *by name* off the ACTIVE object; if the
   active mesh has no UVs, textured UVs scramble and the textures vanish. Give every mesh a
   `UVMap` active-render layer and anchor the join to a mesh that has UVs.
6. **Lighting must not pick a favourite side** *(new)* — a single fixed sun lights +X and leaves
   -X black, and the VLM then reliably calls the *bright* side the front. A wall shelf whose flat
   back was lit and whose shelved front was in shadow got its front called 180 degrees wrong,
   with 0.78 confidence. **The render was lying, not the model.** So the key light now rides the
   camera: each panel gets an identical headlight, plus a strong even ambient. If you ever find
   yourself blaming the VLM for a front call, look at the render first.

## Generating what nobody has: `--source meshy`

`IDSDL/shop/meshy.py` is the same pipeline with the search step replaced by a generator — a
generated model arrives just as un-normalized as a download (no canonical front, no real scale),
so it needs exactly the same triage and gets it for free. Needs `MESHY_API_KEY`; every generation
spends the user's credits, so `count` is never inferred and `--refine` (higher cost) is opt-in.
**Untested against a live key** — treat the first real run as a shakedown and check the endpoint
constants against Meshy's current docs.

## How we know it works

Ground truth was manufactured: four known dataset assets (a lounge chair, a 3-seat sofa, a coffee
table, a wall bookshelf) were **deliberately mangled** — each rotated by a known angle about Z and
its units blown up 100x, exactly like a real download — and the pipeline was told none of it.

- **Fronts:** 3 of 4 recovered automatically and exactly. The 4th (the wall shelf) was the
  interesting one: it was *never ingested wrong*, because on one run the two front judges
  disagreed and on another the size cross-check fired. It went to the board, one line settled it,
  and `apply` rotated it +90 to land the openings back on panel 2.
- **Sizes:** +13%, +20%, -6% of true (the VLM alone was +100%, +25%, +24%).
- **In a real room** (`proof_scene.py` -> `proof_render.png`): all four sit correctly oriented and
  correctly proportioned, and the build's own VLM pass returned "no rotation / no wall overlap".

![proof](proof_render.png)

On raw internet input (six un-normalized Sketchfab downloads from `hospital.zip`) the multi-unit
gate correctly **skipped** a file containing three separate draped instrument tables, and most of
the rest went to the board — the library has no size prior for a slit lamp and the VLM knows it is
guessing. **Expect a high auto-yield on ordinary furniture and a low one on exotic equipment.**
That is the pipeline being honest, not broken.

## Checklist for a batch

- [ ] `search` first — if the internet has nothing good, no pipeline will save you.
- [ ] Run `--dry-run` when you want to see what a query *would* bring in.
- [ ] Read the `ask` list. It is short by design; each entry is one line to answer.
- [ ] Look at `final_strip.png` for anything you accepted by hand — the front should be panel 2.
- [ ] Check the attribution block if these assets will ship.
- [ ] Wrong asset in the library? `python -m IDSDL.shop remove custom/<sha>` — it is reversible.
