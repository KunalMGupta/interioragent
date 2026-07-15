"""Acquisition effort: what the retriever is allowed to do when the dataset cannot serve a query.

The default has always been "make do": take the closest thing in the dataset, however wrong. That
is usually right — the dataset is big, and a scene full of hand-fetched assets is a scene nobody
can reproduce. But it fails silently and badly at the edges. Measured on the real index:

    "a modern grey three seat sofa"   0.81  -> a modern grey three-seat sofa      (served)
    "a pinball machine"               0.64  -> a pinball machine                  (served)
    "a chemistry fume hood"           0.45  -> a kitchen chimney hood             (WRONG)
    "a church confessional booth"     0.47  -> a "modern privacy booth"           (WRONG)
    "a hospital defibrillator"        0.43  -> a wheelchair                       (WRONG)

Below ~0.55 the top hit stops being the thing you asked for and starts being something that merely
embeds near it — and nothing downstream ever says so. The scene just quietly contains a wheelchair.

So the effort level is a dial, and the dial only ever engages on a MEASURED gap:

    low   (default)  never acquire. The dataset is the world; take its best hit.
    mid              a real gap may be filled by SEARCHING (Sketchfab). Free, but slow.
    high             ...and if the web has nothing usable either, GENERATE it (Meshy). Spends
                     credits, so it is never the default.

Every level tries the dataset FIRST and only escalates on a query the dataset demonstrably cannot
serve. Acquisition is a fallback, not a strategy: an asset already in the library is faster, free,
reproducible, and known-good.

Set it per scene — `SceneProgRoom("X", seed=1, acquire="mid")` — or globally with `IDSDL_ACQUIRE`.
Tunables: `IDSDL_ACQUIRE_GAP` (default 0.55), `IDSDL_ACQUIRE_BUDGET` (default 6 acquisitions per
process — a runaway loop here costs real money and hours of Blender).
"""
import os
import re
import threading

import numpy as np

LEVELS = {"low": 0, "mid": 1, "high": 2}
GAP_SIM = float(os.environ.get("IDSDL_ACQUIRE_GAP", 0.55))
BUDGET = int(os.environ.get("IDSDL_ACQUIRE_BUDGET", 6))
SKETCHFAB_COUNT = 5          # candidates to try per gap; triage culls them
MESHY_COUNT = 1              # generations per gap — each one costs credits

# Acquisition mutates the shared library and drives Blender + the GPU. Prefetch resolves queries
# in a thread pool, so without this two workers would race to fill the same gap, and several would
# thrash Blender at once.
_LOCK = threading.RLock()
_state = {"spent": 0, "tried": {}, "log": []}


def level(explicit=None):
    v = (explicit or os.environ.get("IDSDL_ACQUIRE") or "low").strip().lower()
    return v if v in LEVELS else "low"


def enabled(mode):
    return LEVELS[level(mode)] > 0


def report():
    """What this process acquired, for the build log. Silence here means the dataset carried the
    whole scene, which is the outcome we actually want."""
    return list(_state["log"])


_TERMS_SYS = """
You turn an interior-design asset description into search terms for a 3D model website
(Sketchfab). Its search is keyword-based and literal: it chokes on natural-language phrasing.
"a chemistry fume hood" returns NOTHING; "fume hood" returns results.

Give 3 queries, each 1-4 words, no articles, and no adjectives that are not essential to the
object's identity (drop "modern", "warm", "black", "sleek"; keep "grand" in "grand piano"):
- term1: the most specific one that still stands a chance of existing.
- term2: a plainer synonym or the common name for the same object.
- term3: the bare object category — the BROADEST search that would still return the right KIND of
  object. For "a chemistry fume hood" that is "fume hood", not "laboratory".

JSON: {"term1": "...", "term2": "...", "term3": "..."}. Only that JSON.
""".strip()


def search_terms(query):
    """Scene-speak -> search-speak.

    Asset queries in this codebase are written for an EMBEDDING index ("a black articulated desk
    task lamp") and read like prose. Sketchfab's search is literal keyword matching, so it returns
    zero hits for exactly the phrasing our scenes use — which looked, from inside the pipeline,
    like "the web does not have a fume hood" when in fact the web has three.

    Note the asymmetry, which is easy to get backwards: SEARCH wants terse keywords, GENERATION
    wants the full descriptive prose (Meshy renders what you describe). So this only rewrites the
    search leg; Meshy always gets the original query.
    """
    fallback = [re.sub(r"^(a|an|the)\s+", "", query.strip(), flags=re.I)]
    try:
        from sceneprogllm import LLM
        # sceneprogllm's json mode only supports scalar fields (str/int/float/bool) — a "list"
        # type raises, and the raise lands in the except below, which is how this silently
        # degraded to the article-stripping fallback and made the web look empty.
        llm = LLM(system_desc=_TERMS_SYS, response_format="json",
                  response_params={"term1": "str", "term2": "str", "term3": "str"})
        r = llm(query)
        r = r if isinstance(r, dict) else getattr(r, "__dict__", {}) or {}
        terms = [str(r.get(k, "")).strip() for k in ("term1", "term2", "term3")]
        out = []
        for t in [t for t in terms if t] + fallback:      # never lose the deterministic fallback
            if t.lower() not in {o.lower() for o in out}:
                out.append(t)
        return out[:3]
    except Exception as e:                                   # noqa: BLE001 — a rewrite is a bonus
        print(f"[acquire] search-term rewrite unavailable ({e}); using {fallback[0]!r}")
        return fallback


def _best_sim(retriever, query):
    e = np.asarray(retriever.encoder.embed_query(query))
    sims = np.dot(retriever.all_embeddings, e)
    if not len(sims):
        return 0.0, None
    i = int(np.argmax(sims))
    return float(sims[i]), retriever.all_models[i]


def _pick_best(retriever, query, ids):
    """Of the assets we just ingested, which one actually answers the query? The shop can bring
    back several, and 'it was in the batch' is not the same as 'it is the right one'."""
    e = np.asarray(retriever.encoder.embed_query(query))
    best, best_sim = None, -1.0
    for a in ids:
        d = (retriever.metadata.get(a) or {}).get("description")
        if not d:
            continue
        s = float(np.dot(np.asarray(retriever.encoder.embed_query(d)), e))
        if s > best_sim:
            best, best_sim = a, s
    return best, best_sim


def maybe_acquire(retriever, query, mode=None):
    """The whole point of the dial, in one function.

    Returns an asset id to PIN for this query, or None to let normal retrieval proceed. Returning
    a pin (rather than just reloading the index and hoping) matters: some retrievers are
    restricted to a curated pool, so an asset we just ingested would be invisible to them — but we
    acquired it FOR this query, so we hand it over directly.

    Never raises. A failed acquisition falls back to the dataset's best hit, which is exactly the
    behaviour we had before — the scene still builds.
    """
    mode = level(mode)
    if not enabled(mode):
        return None

    sim, top = _best_sim(retriever, query)
    if sim >= GAP_SIM:
        return None                       # the dataset can serve this. Do not spend a cent.

    with _LOCK:
        if query in _state["tried"]:      # a gap we already tried (and maybe failed) to fill
            return _state["tried"][query]
        if _state["spent"] >= BUDGET:
            print(f"[acquire] BUDGET SPENT ({BUDGET}) — falling back to the dataset for {query!r}")
            return None
        # Re-check under the lock: a sibling prefetch thread may have just filled this very gap.
        sim, top = _best_sim(retriever, query)
        if sim >= GAP_SIM:
            return None
        _state["spent"] += 1
        print(f"[acquire] GAP: {query!r} — the dataset's best is only {sim:.2f} "
              f"({(retriever.metadata.get(top) or {}).get('description', '?')[:48]}). "
              f"Acquiring (mode={mode}).")
        got = _acquire(retriever, query, mode)
        _state["tried"][query] = got
        return got


def _rollback(retriever, ids):
    """Take assets back out of the library. The whole reason `IDSDL.shop remove` exists: an
    automatic ingestion pipeline you cannot undo is one nobody should be willing to run."""
    try:
        from IDSDL.shop.pipeline import remove
        remove(ids)
        retriever.reload_library()
    except Exception as e:                                   # noqa: BLE001
        print(f"[acquire] WARNING: could not roll back {ids}: {e}")


def _acquire(retriever, query, mode):
    from IDSDL.shop.pipeline import run as shop_run
    from IDSDL.shop.sources import slugify

    batch_root = os.path.join(os.environ.get("IDSDL_ROOT", os.getcwd()), "shops", "auto")

    # SEARCH first, and try the narrow term before the broad one — a hit on "fume hood" beats a
    # generated approximation of one every time. Only when the web has genuinely nothing do we
    # escalate to spending credits, and only at `high`.
    plan = [("sketchfab", t, SKETCHFAB_COUNT) for t in search_terms(query)]
    if LEVELS[mode] >= 2:
        plan.append(("meshy", query, MESHY_COUNT))   # generation gets the FULL prose, not keywords

    for source, term, count in plan:
        try:
            batch = os.path.join(batch_root, f"{source}-{slugify(term)}")
            # relax_size: this asset exists to fill a gap, so the library HAS no neighbours to
            # price it against — see triage.decide(). The front gates stay strict.
            metas = shop_run(term, batch, source=source, count=count, mode="auto",
                             relax_size=True)
        except Exception as e:                                  # noqa: BLE001
            print(f"[acquire] {source} failed for {term!r}: {e}")
            continue

        ids = [m["asset_id"] for m in (metas or []) if m.get("status") == "ingested"]
        if not ids:
            print(f"[acquire] {source}({term!r}) brought back nothing usable")
            continue

        retriever.reload_library()          # the new assets must be visible to resolve the pin

        # AN ACQUISITION MUST CLOSE THE GAP IT WAS MADE FOR, OR IT IS ROLLED BACK.
        #
        # Getting *an* asset back is not the same as getting the RIGHT one, and the difference is
        # invisible unless you measure it. Asked to generate "a chemistry fume hood", Meshy
        # returned a white box that the captioner — reading the actual render — filed as a
        # "recessed fireplace insert". Left alone, that does double damage: the scene silently
        # gets a fireplace, and the LIBRARY permanently gains an asset indexed under the wrong
        # words, which will now surface for the wrong queries forever.
        #
        # So we re-measure the same gap that triggered all this. If the library's best answer to
        # the query is still below the gap line, the acquisition did not work — no matter how
        # confidently it completed — and we take it back out. The .glb stays in the batch dir with
        # its HELP.md entry, so nothing is lost and a human can rescue it; the library stays clean.
        new_sim, _ = _best_sim(retriever, query)
        best, match = _pick_best(retriever, query, ids)
        if not best or new_sim < GAP_SIM:
            print(f"[acquire] {source}({term!r}) did NOT close the gap "
                  f"(best answer is still {new_sim:.2f}; the closest thing it brought back "
                  f"matches at {match:.2f}) — rolling it back out of the library")
            _rollback(retriever, ids)
            continue

        print(f"[acquire] {query!r} <- {best} ({source} via {term!r}, "
              f"gap {new_sim:.2f} — closed)")
        _state["log"].append({"query": query, "asset_id": best, "source": source, "term": term,
                              "similarity": round(new_sim, 3)})
        return best

    print(f"[acquire] could not fill {query!r} — falling back to the dataset's best hit"
          + ("" if LEVELS[mode] >= 2 else "  (try acquire='high' to generate it)"))
    _state["log"].append({"query": query, "asset_id": None, "source": None, "similarity": None})
    return None
