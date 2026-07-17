"""VLM proposal+critic search over the relative scales of an anchor-group ensemble.

The tile tournament (planar_regions.py) works because its search space is discrete:
the PDF is an explicit per-tile value vector updated by decay/boost credit assignment.
Scale is different — continuous and semantically coupled (the fix for "nightstand
towers over the bed" is to SHRINK the nightstand, not grow the bed, and a render
alone doesn't say which). So here the PDF lives INSIDE the proposer VLM: every
pairwise match verdict — both candidates' scale vectors plus the judge's directional
feedback — is appended to a running transcript that conditions the next round's
proposals. sceneprogllm's LLM is stateless, so this context memory is threaded
manually, which also makes the whole search auditable (match_log.json).

Loop per round:
  1. The PROPOSER (sees member dims in meters, the champion render, and the full
     match history) emits k-1 challenger scale vectors with rationales. The reigning
     champion always competes as candidate 0 (elitism -> monotone improvement).
  2. Candidates are built by a caller-provided layout function — contacts are
     recomputed from the scaled AABBs so nightstands stay flush and lamps stay on
     top at any scale — and rendered head-on (cheap: 384px / 8 samples).
  3. Single-elimination pairwise tournament; matches within a bracket round run in
     parallel. EVERY match yields (factors_a, factors_b, winner, feedback), so one
     solver round generates k-1 labeled comparisons for the proposer's memory, not
     just a winner.

Parameterization per member: a uniform factor `s` plus an optional height-only
override `h` (applied mesh scale = [s, s*h, s]). The anchor moves within tight
bounds; satellites within wide ones. Symmetric duplicates (two nightstands, two
lamps) should share ONE member entry — the layout function instantiates copies.
"""
import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor

# (s_lo, s_hi, h_lo, h_hi)
BOUNDS = {
    "anchor": (0.85, 1.15, 0.90, 1.10),
    "satellite": (0.50, 1.60, 0.75, 1.33),
}

# Members whose MIDDLE dimension is below this get an extra close-up render per
# candidate and a [SMALL] tag (sized numerically, not from pixels): at
# ensemble-frame scale such objects are a handful of pixels, and the benchmark
# showed they get ignored (plant never fixed) or randomly drifted (teapot
# wrongly shrunk 45%). Middle dim, not max: a chef's knife is 0.6m LONG but 2cm
# tall — max-dim calls it big, yet it is invisible in the full view.
SMALL_MEMBER_MAX = 0.45


def _is_small(member):
    return (member.get("role", "satellite") != "anchor"
            and sorted(member["whd"])[1] < SMALL_MEMBER_MAX)

_PROPOSER_SYSTEM = """
You are the scale proposer in an iterative search over the RELATIVE SIZES of a
furniture ensemble for a 3D interior scene. Retrieval sometimes delivers assets at
implausible relative scales (a nightstand as tall as the bed, an oversized lamp).
Your job: propose per-member scale corrections that make the ensemble physically
believable in the real world.

Each member has a uniform factor `s` and a height-only factor `h`; the mesh is
scaled [s, s*h, s], so h!=1 stretches/squashes ONLY the height. All factors are
relative to the member's ORIGINAL (round-0) size, NOT to the current champion —
the dims listed for each member are its original real-world dimensions, so you can
compute the resulting size directly (e.g. s=0.6 on a 0.9 m-tall piece -> 0.54 m).

Reason from real-world furniture knowledge FIRST, pixels second: a nightstand top
should sit near the mattress top, a table lamp is ~0.4-0.7 m, a stool seat ~0.65-0.8 m
under a 0.9-1.1 m counter. Prefer fixing the member that is WRONG over compensating
with the others; prefer satellites over the anchor (the room layout is solved around
the anchor's footprint — only nudge it within its tight bounds if it is clearly off).

Members tagged [SMALL] are nearly invisible in the full render and a close-up fills
the frame at ANY size — pixels carry no scale signal for them. Size [SMALL] members
PURELY NUMERICALLY: compare their listed dims (exact measurements) to the typical
real-world size of that object and set the factor that lands them there in ONE step
— retrieval errors run 2-3x, so be bold, not incremental. If the listed dims already
match the typical size, LEAVE the member at the champion's factors.

You will see the full history of pairwise match verdicts (each candidate's factors
and the judge's feedback). Treat it as your accumulated evidence: early rounds
EXPLORE (diverse hypotheses about which member is off and by how much), later rounds
EXPLOIT (refine around what the judge kept rewarding, and stop repeating settings
the judge already rejected).

Respond with ONLY a JSON object:
{"proposals": [{"rationale": "<one line>",
                "scales": {"<member>": {"s": <float>, "h": <float>}, ...}}, ...]}
Give exactly the requested number of proposals. Members you omit inherit the
champion's current factors. Stay inside each member's stated bounds.
"""

_JUDGE_SYSTEM = """
You are judging two candidate versions of the same furniture ensemble. They differ
ONLY in the relative sizes of the members. The attached images are listed in a
labeled manifest in the query: a full view of each candidate, plus close-up views
of any small members. A close-up fills the frame at ANY true size, so for members
tagged [SMALL] judge from their NUMERIC dims (exact measurements) against the
object's typical real-world size — use the close-up only to see what the object is. The numeric real-world dimensions of every member in
both candidates are given — use them together with the renders; relative-size errors
can be hard to see from pixels alone.

Pick the candidate whose relative sizes are more believable for a real room:
correct functional relationships (a nightstand top near the mattress top, a lamp
proportionate to its table, seats matched to their counter/table) and natural
overall proportions. Penalise any member that would look toy-like or monstrous next
to the others in real life.

First DESCRIBE what you see in each image (look_a, look_b): the size of each member
relative to the others in that image. Only then pick the winner — your verdict must
be consistent with your own descriptions.

Also write one short line of DIRECTIONAL feedback naming each member that is still
off in the winner and which way (e.g. "nightstands still ~20% too tall; lamps now
believable"). If the winner already looks right, say so.

Respond with look_a, look_b, winner = 1 (candidate A) or 2 (candidate B), and the
feedback line.
"""


def _parse_json(text):
    text = str(text).strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"proposer returned no JSON object: {text[:200]!r}")
    return json.loads(text[start:end + 1])


def _bounds(member):
    return member.get("bounds") or BOUNDS[member.get("role", "satellite")]


def _clamp_factors(members, factors):
    out = {}
    for m in members:
        f = factors.get(m["name"], {})
        s_lo, s_hi, h_lo, h_hi = _bounds(m)
        s = min(max(float(f.get("s", 1.0)), s_lo), s_hi)
        h = min(max(float(f.get("h", 1.0)), h_lo), h_hi)
        out[m["name"]] = {"s": round(s, 3), "h": round(h, 3)}
    return out


def _dims(member, f):
    w, h, d = member["whd"]
    return (w * f["s"], h * f["s"] * f["h"], d * f["s"])


def _fmt_factors(members, factors):
    return ", ".join(f"{m['name']} s={factors[m['name']]['s']:.2f}"
                     + (f" h={factors[m['name']]['h']:.2f}"
                        if abs(factors[m['name']]['h'] - 1.0) > 1e-3 else "")
                     for m in members)


def _fmt_dims(members, factors):
    lines = []
    for m in members:
        w, h, d = _dims(m, factors[m["name"]])
        lines.append(f"  {m['name']}: {w:.2f}w x {h:.2f}h x {d:.2f}d m")
    return "\n".join(lines)


def _member_table(members):
    lines = []
    for m in members:
        w, h, d = m["whd"]
        s_lo, s_hi, h_lo, h_hi = _bounds(m)
        lines.append(
            f"- {m['name']} ({m.get('role', 'satellite')})"
            + (" [SMALL]" if _is_small(m) else "")
            + f": \"{m['desc']}\" — original "
            f"{w:.2f}w x {h:.2f}h x {d:.2f}d m; bounds s in [{s_lo}, {s_hi}], "
            f"h in [{h_lo}, {h_hi}]"
            + (f"; {m['note']}" if m.get("note") else ""))
    return "\n".join(lines)


def _history_text(members, match_log):
    if not match_log:
        return "(none yet — this is round 1: explore diverse hypotheses)"
    lines = []
    for rec in match_log:
        lines.append(
            f"R{rec['round']}: A[{_fmt_factors(members, rec['factors_a'])}] vs "
            f"B[{_fmt_factors(members, rec['factors_b'])}] -> winner "
            f"{'A' if rec['winner_side'] == 0 else 'B'}. Judge: {rec['feedback']}")
    return "\n".join(lines)


def propose(members, scene_desc, champion, match_log, n, champ_views,
            model_name="gpt-5", log=print):
    from sceneprogllm import LLM
    llm = LLM(system_desc=_PROPOSER_SYSTEM, response_format="text",
              model_name=model_name)
    images, img_note = [], ""
    if champ_views:
        images = [champ_views["main"]] + list(champ_views["details"].values())
        img_note = "(Attached: the champion render" + (
            ", then close-ups of " + ", ".join(champ_views["details"])
            if champ_views["details"] else "") + ".)\n"
    query = (
        f"Scene: {scene_desc}\n\nMembers:\n{_member_table(members)}\n\n"
        f"Current champion factors: {_fmt_factors(members, champion)}\n"
        f"Champion resulting dims:\n{_fmt_dims(members, champion)}\n"
        + img_note +
        f"\nMatch history so far:\n{_history_text(members, match_log)}\n\n"
        f"Propose exactly {n} challenger scale settings."
    )
    raw = _parse_json(llm(query, image_paths=images or None))
    props = []
    for p in (raw.get("proposals") or [])[:n]:
        merged = {name: dict(f) for name, f in champion.items()}
        for name, f in (p.get("scales") or {}).items():
            if name in merged and isinstance(f, dict):
                merged[name].update({k: f[k] for k in ("s", "h") if k in f})
        props.append({"factors": _clamp_factors(members, merged),
                      "rationale": str(p.get("rationale", "")).strip()})
        log(f"  proposal: {_fmt_factors(members, props[-1]['factors'])}"
            f"  ({props[-1]['rationale'][:70]})")
    return props


def judge_pair(members, scene_desc, cand_a, cand_b, views_a, views_b,
               model_name="gpt-5-mini"):
    from sceneprogllm import LLM
    llm = LLM(system_desc=_JUDGE_SYSTEM, response_format="json",
              response_params={"look_a": "str", "look_b": "str",
                               "winner": "int", "feedback": "str"},
              model_name=model_name)
    images, manifest = _views_images(views_a, views_b)
    query = (
        f"Scene: {scene_desc}\nMembers: "
        + "; ".join(f"{m['name']} = \"{m['desc']}\"" for m in members)
        + f"\n\nAttached images:\n{manifest}\n"
        + f"\nCandidate A dims:\n{_fmt_dims(members, cand_a)}\n"
        f"\nCandidate B dims:\n{_fmt_dims(members, cand_b)}\n"
        f"\nWhich has the more believable relative sizes, 1 (A) or 2 (B)?"
    )
    res = llm(query, image_paths=images)
    winner = 0 if int(res.get("winner", 1)) == 1 else 1
    return winner, str(res.get("feedback", "")).strip(), {
        "look_a": str(res.get("look_a", "")).strip(),
        "look_b": str(res.get("look_b", "")).strip()}


def judge_match(members, scene_desc, cand_a, cand_b, views_a, views_b,
                judge_model="gpt-5-mini", tiebreak_model="gpt-5"):
    """Order-debiased verdict: judge A-vs-B AND B-vs-A; agreement decides,
    disagreement escalates to the (stronger, slower) tiebreak model.

    Pairwise VLM judges have a measurable slot bias — with the reigning champion
    always seated in slot A, a biased judge freezes the tournament (observed:
    9/9 champion wins on gpt-5-nano vs 4/4 correct on order-swapped gpt-5-mini).
    """
    w1, fb1, looks1 = judge_pair(members, scene_desc, cand_a, cand_b,
                                 views_a, views_b, model_name=judge_model)
    w2r, fb2, _ = judge_pair(members, scene_desc, cand_b, cand_a,
                             views_b, views_a, model_name=judge_model)
    w2 = 1 - w2r  # map the swapped verdict back to original sides
    if w1 == w2:
        return w1, fb1, {"agreed": True, **looks1}
    w3, fb3, looks3 = judge_pair(members, scene_desc, cand_a, cand_b,
                                 views_a, views_b, model_name=tiebreak_model)
    return w3, fb3, {"agreed": False, "tiebreak": True, **looks3}


def _tournament(members, scene_desc, cand_idxs, factors, views, rnd,
                workers=4, judge_model="gpt-5-mini", tiebreak_model="gpt-5",
                log=print):
    """Single elimination over cand_idxs; returns (champion_idx, match_records)."""
    idxs, records = list(cand_idxs), []
    while len(idxs) > 1:
        pairs = [(idxs[i], idxs[i + 1]) for i in range(0, len(idxs) - 1, 2)]
        bye = idxs[-1:] if len(idxs) % 2 else []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(
                lambda ab: judge_match(members, scene_desc, factors[ab[0]],
                                       factors[ab[1]], views[ab[0]], views[ab[1]],
                                       judge_model=judge_model,
                                       tiebreak_model=tiebreak_model),
                pairs))
        nxt = []
        for (a, b), (w, feedback, meta) in zip(pairs, results):
            winner = a if w == 0 else b
            records.append({
                "round": rnd, "a": a, "b": b,
                "factors_a": factors[a], "factors_b": factors[b],
                "winner": winner, "winner_side": w, "feedback": feedback,
                **meta})
            tag = "" if meta.get("agreed", True) else " [tiebreak]"
            log(f"  match c{a} vs c{b} -> c{winner}{tag}  ({feedback[:80]})")
            nxt.append(winner)
        idxs = nxt + bye
    return idxs[0], records


def _cluster_bounds(scene, member_name):
    """Union bounds of a member's geometry in a candidate scene.

    Harness contract: build_scene_fn names every geometry with its member-name
    prefix and bakes transforms into the geometry (both harnesses' merge() do)."""
    import numpy as np
    lo = hi = None
    for gname, geom in scene.geometry.items():
        if not gname.startswith(member_name):
            continue
        b = geom.bounds
        if b is None:
            continue
        lo = b[0] if lo is None else np.minimum(lo, b[0])
        hi = b[1] if hi is None else np.maximum(hi, b[1])
    if lo is None:
        return None
    ext = hi - lo
    return np.array([lo - 0.3 * ext, hi + 0.3 * ext])


def _views_images(views_a, views_b):
    """Flatten two candidates' view dicts into (image_paths, labeled manifest)."""
    imgs, lines = [], []
    for tag, v in (("A", views_a), ("B", views_b)):
        imgs.append(v["main"])
        lines.append(f"Image {len(imgs)}: candidate {tag} — full view")
        for m, p in v["details"].items():
            imgs.append(p)
            lines.append(f"Image {len(imgs)}: candidate {tag} — close-up of {m}")
    return imgs, "\n".join(lines)


def render_corner(blend, png, bounds, res=512, samples=8, dist_factor=1.2,
                  scene_bounds=None):
    """Tight 3/4 render from the top-left corner of a bounding cube.

    ``bounds`` is the view target (the whole ensemble, or a small member's padded
    cluster for close-ups); ``scene_bounds`` is the FULL scene's bounds (defaults
    to ``bounds``). Both are trimesh y-up; the glTF import maps them to Blender's
    z-up as (x, -z, y). The render worker interprets location/target as OFFSETS
    from the blend's scene center, so we convert absolutes by subtracting the
    full-scene center.
    """
    import numpy as np
    from IDSDL.renderer.renderer import SceneRenderer

    def blender_center(bb):
        lo, hi = bb
        return np.array([(lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2,
                         (lo[1] + hi[1]) / 2])

    b = np.asarray(bounds)
    C = blender_center(b)
    F = blender_center(np.asarray(scene_bounds if scene_bounds is not None
                                  else bounds))
    m = float(max(b[1] - b[0])) * dist_factor
    loc = C + np.array([-m, -m, m]) - F
    tgt = C - F
    SceneRenderer(resolution_x=res, resolution_y=res, samples=samples,
                  cuda=True).render(blend, png, location=tuple(loc),
                                    target=tuple(tgt))
    return png


def build_contact_sheet(round_records, out_path, cell=280):
    """One row per solver round: every candidate render, champion outlined."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.load_default()
    pad, lh = 3, 30
    cols = max(len(r["cands"]) for r in round_records)
    W, rowH = cols * cell, cell + lh + 24
    M = Image.new("RGB", (W, len(round_records) * rowH), (15, 15, 15))
    d = ImageDraw.Draw(M)
    for r, rec in enumerate(round_records):
        y0 = r * rowH
        d.rectangle([0, y0, W, y0 + 22], fill=(40, 40, 55))
        d.text((8, y0 + 5), rec["title"], fill=(200, 210, 255), font=font)
        for c, cand in enumerate(rec["cands"]):
            x = c * cell
            y = y0 + 24
            im = Image.open(cand["png"]).convert("RGB").resize(
                (cell - 2 * pad, cell - 2 * pad - lh))
            M.paste(im, (x + pad, y + lh + pad))
            win = cand.get("winner")
            d.rectangle([x, y, x + cell, y + lh], fill=(20, 60, 20) if win else (28, 28, 28))
            d.text((x + 4, y + 4), cand["label"][:46] + ("  WIN" if win else ""),
                   fill=(120, 240, 120) if win else (210, 210, 210), font=font)
            if win:
                d.rectangle([x + pad, y + lh + pad, x + cell - pad, y + cell - pad - lh + lh],
                            outline=(90, 220, 90), width=3)
    M.save(out_path)
    return out_path


def solve_relative_scales(members, build_scene_fn, scene_desc, out_dir,
                          rounds=3, k=4, res=512, samples=8, render_workers=3,
                          convert_workers=8, proposer_model="gpt-5",
                          judge_model="gpt-5-mini", tiebreak_model="gpt-5",
                          log=print):
    """Run the proposal/critic scale search.

    members: [{name, desc, role: 'anchor'|'satellite', whd: (w,h,d), note?, bounds?}]
             whd are the CURRENT (possibly mis-scaled) real-world dims at factors 1.0.
    build_scene_fn(factors) -> trimesh.Scene, factors = {name: {'s','h'}}; the caller
             recomputes contacts (flush sides, on-top stacking) from the scaled AABBs.
    Returns (best_factors, match_log). Artifacts land in out_dir: candidate renders,
    match_log.json, contact sheet, initial/final renders.
    """
    from tools.planar_regions import _GLB2BLEND, glb_to_blend

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "_glb2blend.py"), "w") as f:
        f.write(_GLB2BLEND)

    small_members = [m["name"] for m in members if _is_small(m)]
    if small_members:
        log(f"[scale-solver] close-up views for small members: {small_members}")

    def render_candidates(tag, factor_list):
        jobs = []      # (blend_job, png, bounds, dist_factor) flat render list
        cands = []     # per-candidate view dicts (paths filled in before render)
        for c, fac in enumerate(factor_list):
            sc = build_scene_fn(fac)
            glb = os.path.join(out_dir, f"{tag}c{c}.glb")
            sc.export(glb)
            main = os.path.join(out_dir, f"{tag}c{c}.png")
            views = {"main": main, "details": {}}
            jobs.append((glb, main, sc.bounds, 1.2, sc.bounds))
            for mname in small_members:
                cb = _cluster_bounds(sc, mname)
                if cb is None:
                    continue
                dpng = os.path.join(out_dir, f"{tag}c{c}_{mname}.png")
                views["details"][mname] = dpng
                jobs.append((glb, dpng, cb, 1.6, sc.bounds))
            cands.append(views)
        unique_glbs = list({j[0] for j in jobs})
        with ThreadPoolExecutor(max_workers=convert_workers) as ex:
            list(ex.map(lambda g: glb_to_blend(g, out_dir), unique_glbs))
        with ThreadPoolExecutor(max_workers=render_workers) as ex:
            list(ex.map(
                lambda j: render_corner(os.path.splitext(j[0])[0] + ".blend",
                                        j[1], j[2], res, samples,
                                        dist_factor=j[3], scene_bounds=j[4]),
                jobs))
        return cands

    champion = _clamp_factors(members, {m["name"]: {"s": 1.0, "h": 1.0} for m in members})
    log(f"[scale-solver] {len(members)} members, {rounds} rounds x {k} candidates")
    champ_views = render_candidates("r0_champ_", [champion])[0]
    shutil.copy2(champ_views["main"], os.path.join(out_dir, "initial.png"))

    match_log, sheet_rows = [], []
    for rnd in range(1, rounds + 1):
        log(f"[scale-solver] round {rnd}: proposing {k - 1} challengers")
        props = propose(members, scene_desc, champion, match_log, k - 1,
                        champ_views, model_name=proposer_model, log=log)
        if not props:
            log("  proposer returned nothing usable; stopping early")
            break
        factors = [champion] + [p["factors"] for p in props]
        views = [champ_views] + render_candidates(
            f"r{rnd}_", [p["factors"] for p in props])
        champ_idx, records = _tournament(members, scene_desc, list(range(len(factors))),
                                         factors, views, rnd, workers=max(2, k // 2),
                                         judge_model=judge_model,
                                         tiebreak_model=tiebreak_model, log=log)
        match_log.extend(records)
        sheet_rows.append({
            "title": f"ROUND {rnd}   champion = c{champ_idx}",
            "cands": [{"png": views[i]["main"],
                       "label": ("champ | " if i == 0 else f"c{i} | ")
                                + _fmt_factors(members, factors[i]),
                       "winner": i == champ_idx}
                      for i in range(len(factors))]})
        champion, champ_views = factors[champ_idx], views[champ_idx]
        log(f"[scale-solver] round {rnd} champion: {_fmt_factors(members, champion)}")

        # Convergence stop: the champion survived unbeaten AND most matches were
        # so close the two judge orders disagreed (tiebreak). More rounds from
        # here only add noise-driven drift on already-correct members.
        tb = sum(1 for r in records if r.get("tiebreak"))
        if champ_idx == 0 and tb >= len(records) / 2 and rnd < rounds:
            log(f"[scale-solver] converged after round {rnd}: champion unbeaten, "
                f"{tb}/{len(records)} matches needed tiebreaks — stopping early")
            break

    shutil.copy2(champ_views["main"], os.path.join(out_dir, "final.png"))
    with open(os.path.join(out_dir, "match_log.json"), "w") as f:
        json.dump({"scene": scene_desc, "champion": champion,
                   "members": [{k2: v for k2, v in m.items() if k2 != "mesh"}
                               for m in members],
                   "matches": match_log}, f, indent=2)
    if sheet_rows:
        build_contact_sheet(sheet_rows, os.path.join(out_dir, "evolution.png"))
    log(f"[scale-solver] DONE: {_fmt_factors(members, champion)}")
    log(f"[scale-solver] artifacts in {out_dir} (initial.png, final.png, "
        f"evolution.png, match_log.json)")
    return champion, match_log
