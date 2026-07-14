"""Where raw candidate models come from.

A Source does two things: `search(query)` returns Candidates (cheap, metadata only), and
`fetch(candidate, dir)` puts a real .gltf/.glb on disk (expensive, may fail). Everything
downstream — preview, triage, normalize, ingest — is source-agnostic, which is what lets the
Meshy generator (`meshy.py`) slot in beside Sketchfab without touching the pipeline.

Three sources today:
  * `sketchfab` — search is public (no auth); DOWNLOAD NEEDS A FREE API TOKEN. Without one, every
    fetch raises Unfetchable("needs_token") and the pipeline turns those candidates into a HELP
    board of download links — the token is the only thing standing between manual and automatic.
  * `local`     — a directory of .glb/.gltf files. This is both the test source AND the manual
    fallback: whatever the user hand-downloads into `<batch>/inbox/` gets picked up from here.
  * `meshy`     — text-to-3D generation (see meshy.py, registered lazily).
"""
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field

UA = {"User-Agent": "IDSDL-shop/1.0"}


class Unfetchable(Exception):
    """A candidate that cannot be turned into a local file. `.reason` is a stable slug
    (needs_token / no_gltf / http_403 / ...) so the pipeline can route it by machine, not by
    matching prose."""

    def __init__(self, reason, detail=""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass
class Candidate:
    """One model we might ingest, before we have looked at its geometry."""
    key: str                      # filesystem-safe slug; names this candidate's dir everywhere
    name: str
    source: str                   # "sketchfab" | "local" | "meshy"
    uid: str = ""
    url: str = ""
    license: str = ""
    author: str = ""
    faces: int = 0
    animated: bool = False
    thumb: str = ""
    path: str = ""                # set by fetch(): the local .glb/.gltf to import
    extra: dict = field(default_factory=dict)

    def provenance(self):
        """What we owe the author — carried into the asset's library metadata so a licence can
        always be traced back from a rendered scene (some Sketchfab licences require attribution;
        an asset whose origin we cannot name is an asset we cannot legally ship)."""
        return {k: v for k, v in
                {"source": self.source, "uid": self.uid, "url": self.url,
                 "license": self.license, "author": self.author, "name": self.name}.items() if v}


def slugify(name, fallback=""):
    s = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")
    return (s or fallback or "asset")[:60]


# --------------------------------------------------------------------------------------------
# Sketchfab
# --------------------------------------------------------------------------------------------
_API = "https://api.sketchfab.com/v3"
_LICENSE_SLUGS = {"cc0", "by", "by-sa", "by-nd", "by-nc", "by-nc-sa", "by-nc-nd"}
_BUCKETS = {
    "permissive":    ["cc0", "by"],                    # most reuse-friendly
    "commercial-ok": ["cc0", "by", "by-sa", "by-nd"],  # excludes NonCommercial
}
_SORT = {"relevance": None, "likes": "-likeCount", "views": "-viewCount", "recent": "-publishedAt"}


def _get(url, token=None, retries=4):
    headers = dict(UA)
    if token:
        headers["Authorization"] = f"Token {token}"
    last = None
    for a in range(retries):
        try:
            return json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=headers), timeout=45))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (408, 429, 500, 502, 503):   # transient — back off
                time.sleep(1.5 * (a + 1))
                continue
            raise
        except Exception as e:                        # noqa: BLE001 — network flake
            last = e
            time.sleep(1.5 * (a + 1))
    raise last


class SketchfabSource:
    name = "sketchfab"

    def __init__(self, token=None):
        # Token is optional at construction: search works without it, fetch does not.
        self.token = token or os.environ.get("SKETCHFAB_API_TOKEN") or _token_from_dotenv()

    # -- search (public, no auth) -------------------------------------------------------------
    def search(self, query, count=20, license="permissive", min_faces=200, max_faces=750_000,
               sort="relevance", static_only=True):
        base = {"type": "models", "q": query, "downloadable": "true", "count": 24}
        if min_faces:
            base["min_face_count"] = str(min_faces)
        if max_faces:
            base["max_face_count"] = str(max_faces)
        if static_only:
            base["animated"] = "false"
        if _SORT.get(sort):
            base["sort_by"] = _SORT[sort]

        if license in ("any", None):
            slugs = [None]
        elif license in _BUCKETS:
            slugs = _BUCKETS[license]
        elif license in _LICENSE_SLUGS:
            slugs = [license]
        else:
            raise ValueError(f"unknown license filter {license!r}")

        found = {}
        for slug in slugs:
            params = dict(base)
            if slug:
                params["license"] = slug
            cursor = None
            while len(found) < count:
                p = dict(params)
                if cursor:
                    p["cursor"] = cursor
                data = _get(f"{_API}/search?" + urllib.parse.urlencode(p))
                for r in data.get("results", []):
                    found.setdefault(r["uid"], r)
                nxt = data.get("next")
                if not nxt:
                    break
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(nxt).query)
                cursor = qs.get("cursor", [None])[0]
                if not cursor:
                    break
            if len(found) >= count:
                break

        out = []
        for r in list(found.values())[:count]:
            uid = r.get("uid", "")
            imgs = (r.get("thumbnails") or {}).get("images") or []
            out.append(Candidate(
                key=f"{slugify(r.get('name'), uid)}_{uid[:6]}",
                name=r.get("name") or uid,
                source=self.name,
                uid=uid,
                url=f"https://sketchfab.com/3d-models/{uid}",
                license=(r.get("license") or {}).get("label", ""),
                author=(r.get("user") or {}).get("displayName", ""),
                faces=r.get("faceCount") or 0,
                animated=(r.get("animationCount") or 0) > 0,
                thumb=imgs[0].get("url") if imgs else "",
            ))
        return out

    # -- fetch (needs the token) --------------------------------------------------------------
    def fetch(self, cand, dest_dir):
        """Download + unpack one model. Returns the path of the glTF/GLB entry file to import.

        We deliberately do NOT convert the extracted glTF to a packed .glb here: the normalizer
        imports it into Blender anyway and exports a clean single-mesh .glb at the end, so a
        separate conversion pass would be a second lossy round-trip for nothing."""
        if not self.token:
            raise Unfetchable("needs_token", "no SKETCHFAB_API_TOKEN (see .env)")
        try:
            links = _get(f"{_API}/models/{cand.uid}/download", token=self.token)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise Unfetchable("http_%d" % e.code, "token rejected or model not downloadable")
            raise Unfetchable("http_%d" % e.code, str(e))
        url = (links.get("gltf") or {}).get("url")
        if not url:
            # The author published only .blend/.fbx/etc. Nothing to do automatically.
            raise Unfetchable("no_gltf", "no glTF archive offered for this model")

        os.makedirs(dest_dir, exist_ok=True)
        zpath = os.path.join(dest_dir, "model.zip")
        urllib.request.urlretrieve(url, zpath)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(dest_dir)
        os.remove(zpath)
        entry = _find_entry(dest_dir)
        if not entry:
            raise Unfetchable("no_gltf", "archive contained no .gltf/.glb")
        cand.path = entry
        return entry


def _token_from_dotenv():
    """Read SKETCHFAB_API_TOKEN from <repo>/.env — the same place OPENAI_API_KEY lives, so the
    user has exactly one file to paste secrets into (and it is gitignored)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return None
    for line in open(path):
        k, _, v = line.strip().partition("=")
        if k.strip() == "SKETCHFAB_API_TOKEN" and v.strip():
            return v.strip().strip('"').strip("'")
    return None


def _find_entry(root):
    """Prefer .gltf (the archive's authored scene) over any stray .glb, and ignore macOS junk."""
    for ext in (".gltf", ".glb"):
        for dp, _, fs in os.walk(root):
            for f in sorted(fs):
                if f.lower().endswith(ext) and not f.startswith("._") and "__MACOSX" not in dp:
                    return os.path.join(dp, f)
    return None


# --------------------------------------------------------------------------------------------
# Local directory — the manual-download inbox, and the test source
# --------------------------------------------------------------------------------------------
class LocalSource:
    name = "local"

    def __init__(self, directory):
        self.dir = directory

    def search(self, query=None, count=1000, **_):
        out = []
        if not os.path.isdir(self.dir):
            return out
        for f in sorted(os.listdir(self.dir)):
            if f.lower().endswith((".glb", ".gltf")) and not f.startswith("._"):
                out.append(Candidate(key=slugify(os.path.splitext(f)[0]),
                                     name=os.path.splitext(f)[0],
                                     source=self.name,
                                     path=os.path.join(self.dir, f),
                                     url=os.path.join(self.dir, f)))
        return out[:count]

    def fetch(self, cand, dest_dir):
        if not cand.path or not os.path.exists(cand.path):
            raise Unfetchable("missing_file", cand.path)
        return cand.path


def get_source(name, **kw):
    if name == "sketchfab":
        return SketchfabSource(token=kw.get("token"))
    if name == "local":
        return LocalSource(kw["directory"])
    if name == "meshy":
        from IDSDL.shop.meshy import MeshySource
        return MeshySource(api_key=kw.get("token"))
    raise ValueError(f"unknown source {name!r}")
