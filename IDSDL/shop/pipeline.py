"""The pipeline: query in, library assets out.

    search -> fetch -> preview (Blender) -> triage (VLM) -> normalize (Blender) -> VERIFY (VLM)
           -> ingest (IDSDL.ingest)

Two things here are worth knowing before you change anything.

**The verify pass is not optional.** After normalizing, we re-render the file we actually wrote
and ask a second VLM whether the front really did land on panel 2. This is what makes automatic
ingestion trustworthy: a front call is a guess until the render says otherwise, and a silently
back-to-front asset poisons every scene it is retrieved into (an asset the placement code turns
to "face the room" would show the room its back). If the check fails we rotate by the residual
and try ONCE more; if it still fails, no more guessing — the asset goes to the user.

**Nothing is ever thrown away quietly.** Every candidate ends in one of five states, all of them
recorded in `<batch>/<key>/meta.json` and visible on the board:
    ingested  — normalized, verified, registered in the library
    ask       — a judgment we would not make alone (manual mode asks; auto mode leaves it here)
    skip      — mechanically unusable (multi-unit, not an interior object, broken geometry)
    dropped   — the user said no
    failed    — Blender or the network fell over
"""
import argparse
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from IDSDL.shop import blender as BL
from IDSDL.shop import board, triage
from IDSDL.shop.sources import LocalSource, Unfetchable, get_source


def _meta(batch, key):
    return json.loads((Path(batch) / key / "meta.json").read_text())


def _write(batch, m):
    d = Path(batch) / m["key"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps(m, indent=1))
    return m


# --------------------------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------------------------
def _fetch_all(batch, source, cands):
    """Download (or locate) each candidate. A missing Sketchfab token is not an error here — it
    is the single most likely state of a fresh checkout, so it degrades into a request for help:
    the board hands the user the download links and an inbox to drop the files into."""
    metas = []
    for c in cands:
        m = {"key": c.key, "candidate": c.__dict__.copy(), "status": "new", "reason": "",
             "provenance": c.provenance()}
        if c.animated:
            m.update(status="skip", reason="animated")     # rigged models import posed/broken
            metas.append(_write(batch, m))
            continue
        try:
            src = source.fetch(c, os.path.join(batch, c.key, "src"))
            m["src"] = src
            m["status"] = "fetched"
        except Unfetchable as e:
            # Route by what the failure MEANS, not by "it failed". `skip` tells the user this file
            # is mechanically unusable and not worth their minute; being out of Meshy credits or
            # getting a 503 says nothing at all about the asset, and burying those under "skip"
            # would quietly discard a whole batch as if the models were bad.
            if e.reason in ("needs_token", "http_401", "http_403"):
                m.update(status="ask", reason="needs_download",
                         needs_download=bool(c.url))       # a link only helps if there IS one
            elif e.reason in ("no_gltf", "missing_file"):
                m.update(status="skip", reason=e.reason)   # genuinely nothing we can use
            else:                                          # transient / account / generation —
                m.update(status="failed", reason=f"{e.reason}: {e.detail}"[:120])   # retryable
        except Exception as e:                              # noqa: BLE001 — the open internet
            m.update(status="failed", reason=f"fetch_error: {e}")
        metas.append(_write(batch, m))
    return metas


def _preview(batch, metas, res=420):
    todo = [m for m in metas if m["status"] == "fetched"]
    cfgs = [{"mode": "preview", "src": m["src"], "out_dir": str(Path(batch) / m["key"]),
             "tag": "raw", "res": res} for m in todo]
    for m, r in zip(todo, BL.run_jobs(cfgs)):
        if not r.get("ok"):
            m.update(status="failed", reason=r.get("error", "preview_failed"))
        else:
            m["dims"] = r["dims"]
            m["n_images"] = r.get("n_images", 0)
            m["n_polys"] = r.get("n_polys", 0)
            m["views"] = r["views"]
            m["status"] = "previewed"
            d = Path(batch) / m["key"]
            triage.compose_strip(r["views"], str(d / "strip.png"), title=m["candidate"]["name"])
            shutil.copy(r["views"]["hero"], d / "hero.png")
        _write(batch, m)
    return metas


def _triage(batch, metas, query, workers=4):
    todo = [m for m in metas if m["status"] == "previewed"]
    if not todo:
        return metas
    vlm = triage.judge_vlm()
    v2 = triage.second_vlm()

    def one(m):
        d = Path(batch) / m["key"]
        strip, hero = str(d / "strip.png"), str(d / "hero.png")
        try:
            j = triage.judge(vlm, strip, hero, query)
        except Exception as e:                              # noqa: BLE001
            return m, {}, {}, ("ask", f"vlm_error: {e}", {})
        s = {}
        if j.get("single_unit") and j.get("interior_object"):
            try:                                            # only worth a second call if it is
                s = triage.second(v2, strip, hero)          # actually a candidate
            except Exception:                               # noqa: BLE001
                s = {}
        return m, j, s, triage.decide(j, m.get("dims"), second_op=s)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for m, j, s, (verdict, reason, plan) in ex.map(one, todo):
            m["judgment"] = j
            m["second_opinion"] = s
            m["plan"] = plan
            m["status"] = {"go": "go", "ask": "ask", "skip": "skip"}[verdict]
            m["reason"] = reason
            _write(batch, m)
    return metas


def _normalize_and_verify(batch, metas, res=420):
    """Normalize every `go`, then check our own work on the re-rendered result. One retry with the
    residual rotation, then we stop guessing and ask."""
    todo = [m for m in metas if m["status"] == "go"]
    if not todo:
        return metas
    vv = triage.verify_vlm()

    for attempt in (1, 2):
        if not todo:
            break
        cfgs = []
        for m in todo:
            d = Path(batch) / m["key"]
            p = m["plan"]
            cfgs.append({"mode": "finalize", "src": m["src"], "out_dir": str(d), "tag": "fin",
                         "res": res, "rot_deg": p["rot_deg"], "scale_axis": p["scale_axis"],
                         "scale_size": p["scale_size"],
                         "out_glb": str(d / f"{m['key']}.glb")})
        results = BL.run_jobs(cfgs)

        retry = []
        for m, r in zip(todo, results):
            d = Path(batch) / m["key"]
            if not r.get("ok"):
                m.update(status="failed", reason=r.get("error", "finalize_failed"))
                _write(batch, m)
                continue
            m["final"] = {"glb": r["out_glb"], "dims": r["dims"],
                          "mesh_count": r.get("final_mesh_count"),
                          "n_images": r.get("n_images_final", 0)}
            triage.compose_strip(r["views"], str(d / "final_strip.png"),
                                 title=f"{m['key']} (normalized)")
            shutil.copy(r["views"]["hero"], d / "final_hero.png")
            try:
                v = triage.verify(vv, str(d / "final_strip.png"), str(d / "final_hero.png"))
            except Exception as e:                          # noqa: BLE001
                v = {"ok": False, "note": f"verify_error: {e}", "front_panel": 0}
            m["verify"] = v

            if not m["final"]["n_images"]:
                # An asset with ZERO textures is not library-grade, and it fails in a way that
                # hides itself: it renders as a uniform grey solid, so the caption VLM indexes it
                # by its silhouette ("large gray metal wall panel" — that was a generated cork
                # pinboard), and the front call collapses because the features that mark a front
                # (notes, labels, screens, branding) are texture, not geometry. Never ingested
                # silently; a human can still wave it through from the board.
                m.update(status="ask",
                         reason="untextured (0 textures — renders as a flat grey solid)")
            elif v.get("ok"):
                m["status"] = "normalized"
            elif attempt == 1 and int(v.get("front_panel") or 0) in triage.PANELS:
                # The render disagrees with the triage call. Believe the render: rotate by the
                # residual (the front is on panel k now; PANELS[k] says how to bring k round
                # to -Y) and rebuild from the ORIGINAL source, not from the wrong output.
                k = int(v["front_panel"])
                m["plan"] = dict(m["plan"],
                                 rot_deg=[0.0, 0.0,
                                          m["plan"]["rot_deg"][2] + triage.PANELS[k][1]])
                m["reason"] = f"front_retry (verify saw the front on panel {k})"
                retry.append(m)
            else:
                m.update(status="ask", reason="front_verify_failed")
            _write(batch, m)
        todo = retry
    for m in todo:                       # exhausted the retry and still not on panel 2
        m.update(status="ask", reason="front_verify_failed")
        _write(batch, m)
    return metas


def _ingest(batch, metas, category=None, workers=3):
    """Hand the normalized files to the existing ingest path, pinning what we know exactly.

    We measured the object's real width in Blender, so we override the caption VLM's `scale`
    guess with it — the only number in the library that is a measurement rather than an opinion.
    Provenance rides along so a licence can be traced back from any scene."""
    from IDSDL import ingest as I

    # A dry run stops here on purpose. Without this guard, a later `apply` (to settle one asset
    # you were asked about) would re-read the batch and quietly ingest the ENTIRE dry run —
    # exactly the thing you used --dry-run to avoid.
    todo = [m for m in metas if m["status"] == "normalized" and not m.get("dry_run")]
    if not todo:
        return metas
    paths, manifest = [], {}
    for m in todo:
        p = m["final"]["glb"]
        paths.append(p)
        manifest[os.path.basename(p)] = {
            "scale": float(m["final"]["dims"]["w_x"]),
            "provenance": m["provenance"],
        }
    I.ingest_paths(paths, category=category, manifest=manifest, workers=workers)

    # CHECK, do not assume. ingest_paths swallows per-asset failures (a preview render or a
    # caption call can fail, which is a normal outcome for internet models) and reports them only
    # in its return value. Claiming "ingested" for an asset that never registered would put an
    # asset_id on the board that resolves to nothing, and — because "ingested" short-circuits
    # apply() — it would never be retried. So we ask the library what it actually has.
    registered = I._load_meta()
    for m in todo:
        mid = "custom/" + I._sha1(m["final"]["glb"])
        if mid in registered:
            m["asset_id"] = mid
            m["status"] = "ingested"
            m["reason"] = ""
        else:
            m["status"] = "failed"
            m["reason"] = "ingest_failed (preview render or caption failed — see the log above)"
        _write(batch, m)
    return metas


# --------------------------------------------------------------------------------------------
# entry points
# --------------------------------------------------------------------------------------------
def run(query, batch, source="sketchfab", count=10, mode="auto", category=None,
        license="permissive", res=420, workers=3, from_dir=None, dry_run=False, refine=True):
    t0 = time.time()
    batch = str(batch)
    os.makedirs(batch, exist_ok=True)
    src = LocalSource(from_dir) if from_dir else get_source(source, refine=refine)
    cands = src.search(query, count=count, license=license) if not from_dir else src.search(query)
    print(f"[shop] {len(cands)} candidate(s) from {src.name}")
    if not cands:
        return []

    metas = _fetch_all(batch, src, cands)
    metas = _preview(batch, metas, res=res)
    metas = _triage(batch, metas, query)
    metas = _normalize_and_verify(batch, metas, res=res)
    if dry_run:
        # Everything up to and including the verified .glb, but nothing written to the library.
        # Use it to look at what a query WOULD bring in before it is in there for good. The flag
        # is PERSISTED, not just honoured here: `apply` re-reads the whole batch off disk, and
        # without a mark on each asset it would cheerfully ingest the entire dry run the first
        # time you came back to settle one question.
        for m in metas:
            m["dry_run"] = True
            _write(batch, m)
        print("[shop] dry run — normalized but NOT ingested")
    else:
        metas = _ingest(batch, metas, category=category)

    (Path(batch) / "batch.json").write_text(json.dumps(
        {"query": query, "source": src.name, "mode": mode, "category": category,
         "count": count, "license": license, "seconds": round(time.time() - t0)}, indent=1))
    board.generate(Path(batch))
    _report(metas, batch, mode)
    return metas


def _batch_query(batch: Path):
    f = batch / "batch.json"
    return json.loads(f.read_text()).get("query", "") if f.exists() else ""


def _resume(batch, metas, res=420):
    """Carry any half-finished asset the rest of the way.

    `fetched` / `previewed` / `go` are MID-STAGE states: an asset only sits in one because the run
    died there (Ctrl-C, OOM, a VLM call that raised). They are invisible to the board and to the
    answers loop, so without this they would sit on disk forever — downloaded, paid for, and
    never ingested — and the only recovery would be re-running the whole batch from scratch.
    `apply` is where a batch gets picked back up, so it resumes them first."""
    q = _batch_query(Path(batch))
    stages = [("fetched", lambda ms: _preview(batch, ms, res=res)),
              ("previewed", lambda ms: _triage(batch, ms, q)),
              ("go", lambda ms: _normalize_and_verify(batch, ms, res=res))]
    for status, run_stage in stages:
        stranded = [m for m in metas if m["status"] == status]
        if stranded:
            print(f"[shop] resuming {len(stranded)} asset(s) stranded at '{status}'")
            run_stage(stranded)
    return metas


def apply(batch, category=None, res=420):
    """Act on the user's answers in HELP.md, pick up anything they hand-downloaded, and resume
    anything a previous run left half-finished.

    Files dropped in `<batch>/inbox/` are ingested too. Name one after an asset's key (the
    board says so) and it inherits that candidate's licence and attribution; otherwise it comes
    in as a plain local file with no provenance beyond its filename."""
    batch = Path(batch)
    metas = [board.load(d) for d in board.asset_dirs(batch)]
    by_key = {m["key"]: m for m in metas}

    inbox = batch / "inbox"
    if inbox.is_dir():
        fresh = []
        for c in LocalSource(str(inbox)).search():
            m = by_key.get(c.key)
            if m and m.get("needs_download"):
                m["src"] = c.path                      # a hand-download of a known candidate:
                m["status"] = "fetched"                # keep its licence and attribution
                m.pop("needs_download", None)
                fresh.append(_write(str(batch), m))
            elif not m:
                m = {"key": c.key, "candidate": c.__dict__.copy(), "src": c.path,
                     "status": "fetched", "reason": "", "provenance": c.provenance()}
                by_key[c.key] = m
                metas.append(m)
                fresh.append(_write(str(batch), m))
        if fresh:
            print(f"[shop] inbox: {len(fresh)} hand-downloaded file(s)")
            _preview(str(batch), fresh, res=res)
            _triage(str(batch), fresh, _batch_query(batch))
            _normalize_and_verify(str(batch), fresh, res=res)

    _resume(str(batch), [m for m in metas if m["status"] in ("fetched", "previewed", "go")],
            res=res)

    answers = board.read_answers(batch)
    accepted = []
    for key, a in answers.items():
        m = by_key.get(key)
        if not m:
            print(f"  ! answer for unknown asset {key}")
            continue
        if m["status"] == "ingested":
            continue
        action, plan = board.parse_answer(a, m)
        if action == "drop":
            m.update(status="dropped", reason="user dropped")
            _write(str(batch), m)
        elif action == "incomplete":
            print(f"  ! {key}: answer needs both a front panel and a size — skipping")
        elif not m.get("src"):
            print(f"  ! {key}: accepted but no file yet — download it into {inbox}/")
        else:
            # Answering an asset is an explicit "yes, this one" — it lifts the dry-run hold on
            # that asset and no others.
            m.update(status="go", plan=plan, reason="user answered", dry_run=False)
            accepted.append(_write(str(batch), m))

    if accepted:
        _normalize_and_verify(str(batch), accepted, res=res)
        # A user-set front overrules the verifier: they looked at the render, it only guessed.
        for m in accepted:
            if m["status"] == "ask" and m["reason"] == "front_verify_failed":
                m["status"] = "normalized"
                m["reason"] = "user override (verify disagreed)"
                _write(str(batch), m)

    all_metas = [board.load(d) for d in board.asset_dirs(batch)]
    _ingest(str(batch), all_metas, category=category)
    board.generate(batch)
    _report([board.load(d) for d in board.asset_dirs(batch)], str(batch), "apply")


def remove(asset_ids):
    """Un-ingest. The library had no way to take an asset back out, which makes an automatic
    ingestion pipeline scary to run: a mistake was permanent. It is not any more."""
    import numpy as np

    from IDSDL import ingest as I
    from IDSDL.datasets import retrievers as R

    meta = I._load_meta()
    models, embs = I._load_npz()
    ids = [a if a.startswith("custom/") else f"custom/{a}" for a in asset_ids]
    keep = [(m, e) for m, e in zip(models, embs) if m not in ids]
    gone = []
    for a in ids:
        if a in meta:
            meta.pop(a)
            gone.append(a)
            sha = a.split("/", 1)[1]
            for p in (os.path.join(I.MODELS_DIR, sha + ".glb"),
                      os.path.join(I.IMAGES_DIR, sha + ".png")):
                if os.path.exists(p):
                    os.remove(p)
        else:
            print(f"  ! not in the library: {a}")
    I._save(meta, [m for m, _ in keep], [e for _, e in keep] or np.zeros((0, I.EMB_DIM)))

    pools = os.path.join(os.path.dirname(R.__file__), "assets")
    for f in os.listdir(pools):
        if not f.endswith(".json") or f in ("futurehssd.json",):
            continue
        p = os.path.join(pools, f)
        try:
            pool = json.load(open(p))
        except Exception:                                  # noqa: BLE001
            continue
        if isinstance(pool, list) and any(a in pool for a in ids):
            json.dump([x for x in pool if x not in ids], open(p, "w"), indent=1)
            print(f"  - pruned {f}")
    R._NPZ_CACHE.clear()
    R._JSON_CACHE.clear()
    print(f"[shop] removed {len(gone)} asset(s); {len(keep)} custom asset(s) left")
    return gone


def _report(metas, batch, mode):
    order = ["ingested", "ask", "skip", "dropped", "failed"]
    by = {s: [m for m in metas if m["status"] == s] for s in order}
    print(f"\n[shop] {batch}  ({mode})")
    for s in order:
        if by[s]:
            print(f"  {s:9s} {len(by[s]):2d}")
            for m in by[s]:
                extra = m.get("asset_id", "") or m.get("reason", "")
                obj = (m.get("judgment") or {}).get("object", "")
                print(f"      {m['key'][:34]:34s} {obj[:26]:26s} {extra}")

    # Attribution FIRST — it must print on every path that ingested something. (It used to sit
    # at the bottom, under three early returns, where it never printed at all.) Several Sketchfab
    # licences require credit; an asset we ingest without naming its author is one we cannot ship.
    lic = [m for m in by["ingested"] if (m.get("provenance") or {}).get("license")]
    if lic:
        print("\n  attribution (ingested):")
        for m in lic:
            p = m["provenance"]
            print(f"      {p.get('name', '?')} — {p.get('license')} — {p.get('author', '?')} — "
                  f"{p.get('url', '')}")

    # The two modes really do end differently, and this is where. AUTO promises not to bother
    # anyone: the hard ones are left un-ingested (recoverable — they are all still on the board)
    # and the run is a success. MANUAL promises to ask: it ends by naming what it needs and
    # exiting non-zero, so a caller — a script, or an agent deciding whether to put a question in
    # front of the user — can tell "done" from "waiting on a human" without parsing prose.
    need = by["ask"] + by["failed"]
    if not need:
        return 0
    if mode == "manual":
        print(f"\n  WAITING ON YOU — {len(need)} asset(s) need a call:")
        for m in need:
            print(f"      {m['key'][:34]:34s} {m.get('reason', '')}")
        print(f"  answer them in {batch}/HELP.md, then: python -m IDSDL.shop apply {batch}")
        return 2
    print(f"\n  skipped {len(need)} asset(s) the pipeline would not guess at — nothing is lost, "
          f"they are on {batch}/HELP.md\n  (settle them any time: python -m IDSDL.shop apply {batch})")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="IDSDL.shop", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search only — print candidates, ingest nothing")
    s.add_argument("query")
    s.add_argument("--count", type=int, default=15)
    s.add_argument("--license", default="permissive")
    s.add_argument("--json", default=None)

    r = sub.add_parser("run", help="search -> normalize -> ingest")
    r.add_argument("query", nargs="?", default="")
    r.add_argument("--batch", default=None, help="output dir (default shops/<date>-<slug>)")
    r.add_argument("--count", type=int, default=8)
    r.add_argument("--source", default="sketchfab", choices=["sketchfab", "meshy"])
    r.add_argument("--from-dir", default=None, help="ingest a local dir of glb/gltf instead")
    r.add_argument("--manual", action="store_true",
                   help="ask the user about anything uncertain (default: auto, which skips it)")
    r.add_argument("--category", default=None, help="also add ingested ids to this category pool")
    r.add_argument("--license", default="permissive")
    r.add_argument("--res", type=int, default=420)
    r.add_argument("--dry-run", action="store_true",
                   help="normalize + verify but do NOT write to the library")
    r.add_argument("--no-refine", action="store_true",
                   help="meshy only: skip the texturing pass (CHEAPER, but the result is an "
                        "untextured grey blob — not library-grade; see IDSDL/shop/meshy.py)")

    rm = sub.add_parser("remove", help="un-ingest asset ids from the library")
    rm.add_argument("asset_ids", nargs="+")

    a = sub.add_parser("apply", help="act on the answers written into <batch>/HELP.md")
    a.add_argument("batch")
    a.add_argument("--category", default=None)

    b = sub.add_parser("board", help="(re)generate <batch>/HELP.md")
    b.add_argument("batch")
    b.add_argument("--pending", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "search":
        from IDSDL.shop.sources import SketchfabSource
        hits = SketchfabSource().search(args.query, count=args.count, license=args.license)
        for i, c in enumerate(hits, 1):
            print(f"{i:2}. {c.name}\n    {c.license} · by {c.author} · {c.faces:,} faces\n"
                  f"    {c.url}")
        if args.json:
            json.dump([c.__dict__ for c in hits], open(args.json, "w"), indent=1)
        if not SketchfabSource().token:
            print("\nNo SKETCHFAB_API_TOKEN — `run` will hand you these as manual downloads.")
        return 0

    if args.cmd == "board":
        p = Path(args.batch)
        (board.pending if args.pending else board.generate)(p)
        return 0

    if args.cmd == "apply":
        apply(args.batch, category=args.category)
        return 0

    if args.cmd == "remove":
        remove(args.asset_ids)
        return 0

    from IDSDL.shop.sources import slugify
    batch = args.batch or os.path.join(
        "shops", f"{time.strftime('%Y-%m-%d')}-{slugify(args.query or Path(args.from_dir or 'local').name)}")
    mode = "manual" if args.manual else "auto"
    metas = run(args.query, batch, source=args.source, count=args.count,
                mode=mode, category=args.category, license=args.license, res=args.res,
                from_dir=args.from_dir, dry_run=args.dry_run, refine=not args.no_refine)
    # manual mode exits 2 while a human still owes us an answer, so a caller can tell "finished"
    # from "waiting on you" without reading the prose.
    pending = [m for m in metas if m["status"] in ("ask", "failed")]
    return 2 if (mode == "manual" and pending) else 0


if __name__ == "__main__":
    sys.exit(main())
