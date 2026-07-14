"""Meshy text-to-3D as a shop source: when the library does not HAVE the thing, generate it.

This is the same pipeline, with the search step replaced by a generator. That is the entire point
of the Source interface: a Meshy model arrives just as un-normalized as a Sketchfab download — no
canonical front, no real-world scale, sometimes several blobs joined into one file — so it needs
exactly the same triage, normalization and verification, and it gets them for free.

    python -m IDSDL.shop run "a brutalist concrete planter" --source meshy --count 2

`search()` does not search; it plans N generations from the prompt. `fetch()` is where the work
(and the money) happens: POST a task, poll it to SUCCEEDED, download the .glb. A generation takes
minutes, so fetch is slow by nature and the pipeline treats it like a big download.

Cost and consent, deliberately:
  * Nothing generates without MESHY_API_KEY (in the environment or <repo>/.env).
  * Every generation spends credits, so `count` is never inferred — you type it.
  * `--refine` doubles the cost for a textured, higher-poly result; preview-only is the default.

STATUS: written against Meshy's documented OpenAPI v2 text-to-3d flow, but NOT yet run against a
live key (we do not have one). The shape is right and the polling is defensive, but treat the
first real run as a shakedown, and check `API`/`MODEL` below against the current docs — Meshy has
rev'd its endpoints before.
"""
import json
import os
import time
import urllib.error
import urllib.request

from IDSDL.shop.sources import Candidate, Unfetchable, slugify

API = "https://api.meshy.ai/openapi/v2/text-to-3d"
BALANCE = "https://api.meshy.ai/openapi/v1/balance"
MODEL = "meshy-5"                 # ai_model; older keys may need "meshy-4"
POLL_EVERY = 10                   # seconds
POLL_TIMEOUT = 900                # a preview is typically 1-3 min; refine can be much longer


def _key(explicit=None):
    if explicit:
        return explicit
    k = os.environ.get("MESHY_API_KEY")
    if k:
        return k
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = os.path.join(root, ".env")
    if os.path.exists(env):
        for line in open(env):
            a, _, b = line.strip().partition("=")
            if a.strip() == "MESHY_API_KEY" and b.strip():
                return b.strip().strip('"').strip("'")
    return None


def _req(url, key, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "IDSDL-shop/1.0"})
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.load(f)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf8", "replace")[:200]
        if e.code in (401, 403):
            raise Unfetchable("bad_key", f"Meshy rejected the API key ({e.code}): {detail}")
        if e.code == 402:
            raise Unfetchable("no_credits", f"Meshy says out of credits: {detail}")
        raise Unfetchable(f"http_{e.code}", detail)


class MeshySource:
    name = "meshy"

    def __init__(self, api_key=None, art_style="realistic", refine=False,
                 target_polycount=30000):
        self.key = _key(api_key)
        self.art_style = art_style
        self.refine = refine
        self.target_polycount = target_polycount

    def balance(self):
        if not self.key:
            return None
        return _req(BALANCE, self.key).get("balance")

    def search(self, query, count=1, **_):
        """No search — a plan for `count` generations of the same prompt. Different tasks give
        different meshes, which is the closest thing generation has to 'candidates', and it is why
        asking for 2-3 and letting triage cull them beats asking for 1 and hoping."""
        return [Candidate(key=f"{slugify(query)}_{i + 1}", name=f"{query} (meshy #{i + 1})",
                          source=self.name, extra={"prompt": query, "index": i})
                for i in range(count)]

    def fetch(self, cand, dest_dir):
        if not self.key:
            raise Unfetchable("needs_token", "no MESHY_API_KEY (see .env)")
        prompt = cand.extra["prompt"]
        os.makedirs(dest_dir, exist_ok=True)

        task = _req(API, self.key, "POST", {
            "mode": "preview",
            "prompt": prompt,
            "art_style": self.art_style,
            "ai_model": MODEL,
            "should_remesh": True,
            "target_polycount": self.target_polycount,
        })
        tid = task.get("result") or task.get("id")
        if not tid:
            raise Unfetchable("no_task", f"Meshy returned no task id: {str(task)[:120]}")
        info = self._poll(tid)

        if self.refine:
            rt = _req(API, self.key, "POST", {"mode": "refine", "preview_task_id": tid})
            rid = rt.get("result") or rt.get("id")
            if rid:
                info = self._poll(rid)
                tid = rid

        url = (info.get("model_urls") or {}).get("glb")
        if not url:
            raise Unfetchable("no_glb", f"task {tid} produced no glb")
        out = os.path.join(dest_dir, f"{cand.key}.glb")
        urllib.request.urlretrieve(url, out)

        cand.path = out
        cand.uid = tid
        cand.url = info.get("thumbnail_url", "") or f"meshy:{tid}"
        cand.license = "Meshy generated"
        cand.author = "Meshy AI"
        cand.extra["task"] = tid
        return out

    def _poll(self, tid):
        t0 = time.time()
        last = ""
        while time.time() - t0 < POLL_TIMEOUT:
            info = _req(f"{API}/{tid}", self.key)
            status = info.get("status", "")
            if status != last:
                print(f"    meshy {tid[:8]}: {status} {info.get('progress', '')}%")
                last = status
            if status == "SUCCEEDED":
                return info
            if status in ("FAILED", "CANCELED", "EXPIRED"):
                raise Unfetchable("generation_failed",
                                  str((info.get("task_error") or {}).get("message", status)))
            time.sleep(POLL_EVERY)
        raise Unfetchable("generation_timeout", f"task {tid} still running after {POLL_TIMEOUT}s")
