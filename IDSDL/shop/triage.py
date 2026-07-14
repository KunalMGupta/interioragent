"""The three judgments, made by a VLM instead of a human.

Normalizing an internet model is mechanical except for three calls that used to need eyes on a
render: **which way is the front**, **how big is it really**, and **is this one object at all**.
This module makes those calls from a labelled 4-view strip, and — critically — it never has to
reason about coordinate axes to do it. The strip's panels are NUMBERED and captioned, the VLM
answers with a panel number, and the axis arithmetic happens here in Python:

    panel 1 = the +Y side      panel 3 = the +X side
    panel 2 = the -Y side      panel 4 = the -X side          (-Y is the library's front)

Every sign error the human pipeline ever made was in that translation step, so we took it away
from the model. Rotation to bring the chosen side round to -Y:

    front on -Y -> 0 deg     +Y -> 180     +X -> -90     -X -> +90

Confidence is not decoration. Below `CONF`, the asset is not guessed at: auto mode skips it and
manual mode asks the user (pipeline.py routes it, board.py asks).
"""
import os

from PIL import Image, ImageDraw, ImageFont

# panel -> (caption, rotation in degrees about Z that brings this side round to -Y)
PANELS = {1: ("+Y side", 180.0),
          2: ("-Y side", 0.0),
          3: ("+X side", -90.0),
          4: ("-X side", 90.0)}

CONF = 0.7                 # below this we do not guess — we skip (auto) or ask (manual)
MIN_SIZE_M, MAX_SIZE_M = 0.05, 4.0     # an interior asset outside this band is a misread, not a
                                       # discovery: 5 cm to 4 m spans a coaster to a tall wardrobe

_JUDGE_SYS = """
You are triaging a 3D model for an interior-design asset library, looking at a strip of four
straight-on renders of the SAME object (panels 1-4, captioned with which side of the object each
one shows) plus a 3/4 "hero" view. Answer with JSON:

- object: a short name for what this actually is (not what it was searched for).
- n_units: COUNT the separate, physically disconnected objects in this file. Look at the hero
  view and count things standing apart from each other on the ground: three draped tables in a
  row is 3, a pair of chairs is 2, one cabinet is 1. Parts that are attached to or resting on one
  main object (cushions on a sofa, instruments on a tray, a lamp bolted to a machine, a 4-bay
  shelf sharing one frame) do NOT add to the count — they are part of that one object.
- single_unit: true only if n_units is 1. FALSE for a set, a pack, a row of the same thing, or a
  whole staged scene — those files have to be split by hand, and we do not split them.
- interior_object: true if it is a plausible object to place inside a room. False for vehicles,
  buildings, characters/creatures, weapons, environments, abstract art, texture planes.
- front_panel: which PANEL NUMBER (1-4) shows the object's FRONT. The front is the side a person
  faces it from: the product/branded/display side of a fixture; the seat-opening of a chair; the
  screen of a TV; the doors of a cabinet; the face of a figure. For objects operated from behind
  (desks, counters, reception desks, pianos, carts) the front is the side the CUSTOMER/audience
  sees, not the operator's side. If two opposite sides are genuinely identical, pick either and
  say so in `concerns` with lower confidence.
  For anything with storage — shelves, bookcases, cabinets, wardrobes, sideboards, fridges — the
  front is the side with the OPENINGS, shelves, doors or drawers, and NEVER the flat closed back,
  no matter which side is better lit or more detailed.
- front_confidence: 0..1. Be honest: below 0.7 means "a human should look at this".
- size_anchor: "height" for almost everything; "width" only for wide flat things (a poster, a
  wall board, a rug) whose width is the meaningful dimension.
- size_m: the object's real-world size along that anchor, in METRES (a dining chair ~0.9 m tall,
  a standing mannequin ~1.85, a shelving gondola ~2.0, a mug ~0.1, an area rug ~2.5 wide).
- size_confidence: 0..1.
- concerns: anything a human should know (ambiguous front, looks broken/untextured, only half a
  model, etc). Empty string if none.
Answer with only that JSON.
""".strip()

_SECOND_SYS = """
You see four straight-on renders of one object (panels 1-4) and a hero view. Answer ONE question:
if a person walked up to this object to USE it, which panel shows the side they would be standing
at and looking at?

Think about how the object is used, not about how it is lit or how detailed it looks:
- you sit INTO a chair or sofa from its seat opening;
- you reach INTO shelves, cabinets, wardrobes and fridges through their openings/doors — the
  closed flat back is never the front, even if it is the better-lit or more textured side;
- you look AT the screen of a TV or monitor;
- you stand at the CUSTOMER side of a counter, desk or reception unit, not the operator's side;
- you face the working surface of an appliance or machine (its controls, dials or door).

JSON: {"front_panel": 1-4, "confidence": 0..1, "why": "one short sentence"}. Answer with only JSON.
""".strip()

_VERIFY_SYS = """
You are checking a normalization result. You see a strip of four straight-on renders of one
object (panels 1-4) plus a hero view. Panel 2 is supposed to show the object's FRONT — the side a
person faces it from. Answer with JSON:
- front_panel: which panel number (1-4) actually shows the front now.
- ok: true if that is panel 2.
- note: one short sentence.
Answer with only that JSON.
""".strip()

_FONT_PATHS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def _font(size):
    for p in _FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def compose_strip(views, out_path, title=""):
    """Four side views -> one captioned 1x4 strip. The captions are the whole point: they let the
    VLM answer 'which panel' instead of 'which axis', and they make the same image reviewable by a
    human on the HELP board without a legend."""
    panels = [views[f"p{i}"] for i in (1, 2, 3, 4)]
    ims = [Image.open(p).convert("RGB") for p in panels]
    w, h = ims[0].size
    band = max(26, h // 14)
    head = band + 4 if title else 0
    strip = Image.new("RGB", (w * 4, h + band + head), (255, 255, 255))
    d = ImageDraw.Draw(strip)
    if title:
        d.text((8, 4), title[:110], fill=(20, 20, 20), font=_font(max(14, band - 12)))
    for i, im in enumerate(ims):
        strip.paste(im, (i * w, head))
        n = i + 1
        cap, _ = PANELS[n]
        d.rectangle([i * w, head + h, (i + 1) * w - 1, head + h + band], fill=(24, 24, 28))
        d.text((i * w + 8, head + h + 4), f"PANEL {n}   ({cap})",
               fill=(255, 255, 255), font=_font(max(13, band - 12)))
        d.rectangle([i * w, head, (i + 1) * w - 1, head + h - 1], outline=(24, 24, 28), width=2)
    strip.save(out_path)
    return out_path


def judge_vlm():
    from sceneprogllm import LLM
    return LLM(system_desc=_JUDGE_SYS, response_format="json",
               response_params={"object": "str", "n_units": "int", "single_unit": "bool",
                                "interior_object": "bool", "front_panel": "int",
                                "front_confidence": "float", "size_anchor": "str",
                                "size_m": "float", "size_confidence": "float",
                                "concerns": "str"})


def second_vlm():
    """A second opinion on the front, asked a DIFFERENT way — 'which side would you walk up to
    and use?' instead of 'which side is the front?'. Two independent lenses on the one judgment
    that silently poisons a scene when it is wrong (a back-to-front asset shows the room its
    back, and nothing downstream can tell). Where they disagree, we do not pick a winner: we ask."""
    from sceneprogllm import LLM
    return LLM(system_desc=_SECOND_SYS, response_format="json",
               response_params={"front_panel": "int", "confidence": "float", "why": "str"})


def verify_vlm():
    from sceneprogllm import LLM
    return LLM(system_desc=_VERIFY_SYS, response_format="json",
               response_params={"front_panel": "int", "ok": "bool", "note": "str"})


def _as_dict(r):
    return r if isinstance(r, dict) else getattr(r, "__dict__", {}) or {}


def judge(vlm, strip_png, hero_png, query=""):
    ask = f'This model was found by searching for: "{query}". Triage it.' if query else "Triage it."
    return _as_dict(vlm(ask, image_paths=[strip_png, hero_png]))


def second(vlm, strip_png, hero_png):
    return _as_dict(vlm("Which panel would you walk up to?", image_paths=[strip_png, hero_png]))


def verify(vlm, strip_png, hero_png):
    return _as_dict(vlm("Is the front on panel 2?", image_paths=[strip_png, hero_png]))


# --------------------------------------------------------------------------------------------
# The size prior: ask the library how big this kind of thing is
# --------------------------------------------------------------------------------------------
PRIOR_MIN_SIM = 0.45       # below this the neighbours are not really the same kind of object
PRIOR_LO, PRIOR_HI = 0.55, 1.8    # how far from the neighbours' median width we tolerate

_PRIOR_CACHE = {}


def library_width_prior(description, k=8):
    """How wide is a "<description>", according to the 100k assets we already have?

    Real-world size is the judgment a VLM is worst at — it is guessing metres from an object on a
    grey background with no reference. But the library is FULL of curated real-world widths, and
    we have the text embedder that indexes them. So we look the object up among its neighbours
    and get an empirical width: an independent second estimate, from data rather than vision.
    Two estimates that agree are worth far more than one confident one.

    Returns (median_width_m, mean_similarity) or (None, 0.0) if the neighbours are not close
    enough to mean anything."""
    import numpy as np

    if description in _PRIOR_CACHE:
        return _PRIOR_CACHE[description]
    try:
        from IDSDL.datasets import retrievers as R
        r = R.FUTURE_HSSD_ASSET_RETRIEVERS[0]
        v = np.asarray(r.encoder.embed_query(description), dtype=np.float64)
        E = np.asarray(r.all_embeddings, dtype=np.float64)
        sims = (E @ v) / (np.linalg.norm(E, axis=1) * np.linalg.norm(v) + 1e-9)
        top = np.argsort(-sims)[:k]
        widths = []
        for i in top:
            s = (r.metadata.get(r.all_models[i]) or {}).get("scale")
            if s:
                widths.append(float(s))
        if not widths:
            out = (None, 0.0)
        else:
            out = (float(np.median(widths)), float(np.mean(sims[top])))
    except Exception:                                       # noqa: BLE001 — a prior is a bonus
        out = (None, 0.0)
    _PRIOR_CACHE[description] = out
    return out


def predicted_width(plan, dims):
    """What the object's real WIDTH will be once this plan is applied — the number the library
    stores, and so the number the prior can be compared against. A +-90 deg rotation swaps width
    and depth, which is exactly the kind of thing that is easy to get wrong by eye."""
    if not dims:
        return None
    rot = plan["rot_deg"][2] % 360
    width_axis = dims["w_x"] if rot in (0.0, 180.0) else dims["d_y"]
    if plan["scale_axis"] == "x":
        return float(plan["scale_size"])            # the anchor IS the width
    h = dims["h_z"]
    if h <= 1e-9:
        return None
    return float(plan["scale_size"]) * width_axis / h


def decide(j, dims=None, second_op=None, use_prior=True, relax_size=False):
    """Turn the judgments into a decision. Returns (verdict, reason, plan).

    verdict is one of: "go" (normalize it), "skip" (mechanically unusable — never worth a
    human's time), "ask" (a judgment call we are not confident enough to make alone).

    The split between skip and ask IS the feature: auto mode drops both, manual mode drops the
    skips and puts every `ask` in front of the user. So `skip` must mean genuinely hopeless, and
    anything merely uncertain must be an `ask` — misfiling an uncertain asset as a skip silently
    throws away a good model.

    Note what carries the weight here: not a single confidence number, but AGREEMENT between two
    independent estimates — two differently-framed VLMs on the front, vision vs the library's own
    curated widths on the size. A lone confident answer is the thing that got a wall shelf ingested
    back-to-front; agreement is much harder to fake.
    """
    if dims:
        d = sorted(dims.values())
        if d[-1] <= 1e-6 or d[0] / d[-1] < 1e-4:
            return "skip", "degenerate_geometry", {}
    if not j:
        return "ask", "vlm_no_answer", {}
    # Two ways to fail this, on purpose. Asked only for the BOOLEAN, the model waved through a
    # file containing three separate draped instrument tables — "a surgical instrument table
    # collection" sounded like one thing. Asked to COUNT the objects standing apart on the
    # ground, it gets it right: counting is a much easier visual task than an abstract judgment,
    # and it is far harder to talk yourself into "3 is basically 1".
    n = int(j.get("n_units") or 1)
    if n > 1 or not j.get("single_unit", False):
        return "skip", f"multi_unit ({n} objects in one file)", {}
    if not j.get("interior_object", False):
        return "skip", "not_an_interior_object", {}

    panel = int(j.get("front_panel") or 0)
    if panel not in PANELS:
        return "ask", "front_unreadable", {}
    size = float(j.get("size_m") or 0.0)
    anchor = "width" if str(j.get("size_anchor", "")).lower().startswith("w") else "height"
    plan = {"rot_deg": [0.0, 0.0, PANELS[panel][1]],
            "scale_axis": "x" if anchor == "width" else "z",
            "scale_size": size,
            "front_panel": panel}

    # --- the front: two lenses must agree -----------------------------------------------------
    p2 = int((second_op or {}).get("front_panel") or 0)
    if second_op and p2 in PANELS and p2 != panel:
        plan["second_panel"] = p2
        return "ask", f"front_disagreement (panels {panel} vs {p2})", plan
    if float(j.get("front_confidence") or 0) < CONF and \
            float((second_op or {}).get("confidence") or 0) < CONF:
        return "ask", "front_uncertain", plan

    # --- the size: vision proposes, the library disposes ---------------------------------------
    # Measured on a ground-truth set (a chair, a sofa, a coffee table of known real width): the
    # VLM came in +25%, +24% and +100% oversized, while the library's nearest-neighbour median was
    # within ~20% every time — including on the table the VLM doubled. A model guessing metres off
    # a grey background has no reference object; the library has thousands of curated widths for
    # the same kind of thing. So when the neighbours are close enough to mean anything, the PRIOR
    # sets the size and vision becomes the cross-check: if the two disagree wildly, that usually
    # means the object was misidentified (our wall shelf came back as a "wooden panel"), and a
    # misidentified object is exactly what a human should look at.
    if not (MIN_SIZE_M <= size <= MAX_SIZE_M):
        return "ask", "size_out_of_band", plan
    w_pred = predicted_width(plan, dims)
    prior, sim = library_width_prior(j.get("object", "")) if use_prior else (None, 0.0)
    if prior and w_pred and sim >= PRIOR_MIN_SIM:
        ratio = w_pred / prior
        plan["width_vision"] = round(w_pred, 3)
        plan["width_prior"] = round(prior, 3)
        plan["prior_sim"] = round(sim, 3)
        if not (PRIOR_LO <= ratio <= PRIOR_HI):
            return "ask", (f"size_disagreement (vision says {w_pred:.2f} m wide, "
                           f"the library's {j.get('object', 'similar')}s are {prior:.2f} m)"), plan
        plan["scale_axis"] = "x"                 # anchor the WIDTH...
        plan["scale_size"] = round(prior, 3)     # ...at what the library says this thing measures
        plan["size_source"] = "library_prior"
        return "go", "", plan
    # No usable prior. Normally we ask — but `relax_size` says this asset is being fetched to fill
    # a MEASURED GAP in the library, and there is a circularity to face: the prior comes from the
    # library's nearest neighbours, so an asset worth acquiring is by definition one the library
    # has no neighbours for. Demanding a prior there is demanding the impossible, and it would
    # block precisely the acquisitions that matter most.
    #
    # We relax the SIZE gate and not the FRONT gate, because their failures cost different things:
    # a wrong size is visible in the render and any program can override it (`width=`,
    # `modulate_scale=`); a wrong front is silent, and the placement code will turn the asset's
    # back to the room and report no error. So we take vision's size (bounded to the sane band
    # above) and keep both front judges strict.
    if float(j.get("size_confidence") or 0) < CONF and not relax_size:
        return "ask", "size_uncertain", plan
    plan["size_source"] = "vlm" + ("(no prior, gap-fill)" if relax_size else "")
    return "go", "", plan
