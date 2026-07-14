"""Asset shop — search the web for 3D assets, normalize them, and ingest them into the library.

The library's assets must satisfy a strict contract (single mesh, real-world metres, front facing
+Z in glTF, Y up) that internet models never satisfy on their own. `IDSDL.ingest` assumes that
contract is already met; this package is what MEETS it, automatically:

    search (Sketchfab)  ->  download  ->  normalize (Blender)  ->  triage (VLM)  ->  IDSDL.ingest

The only per-asset judgments in the whole chain are the three the human used to make by eye —
which way is the FRONT, how BIG is it really, and is this even ONE object — and a VLM makes them
from a labelled 4-view preview, with a second VLM pass verifying the result on the re-rendered
final. Anything it cannot decide confidently is never guessed: in `auto` mode it is SKIPPED, in
`manual` mode it is parked on a HELP board for the user to answer (see `board.py`).

Entry points:
    python -m IDSDL.shop search "<query>"          # look, don't touch
    python -m IDSDL.shop run "<query>" --auto      # search -> ... -> ingest, skipping hard ones
    python -m IDSDL.shop run "<query>" --manual    # ... and ask the user about the hard ones
    python -m IDSDL.shop apply shops/<batch>       # ingest the ones the user answered
"""
from IDSDL.shop.sources import Candidate, LocalSource, SketchfabSource, Unfetchable, get_source

__all__ = ["Candidate", "LocalSource", "SketchfabSource", "Unfetchable", "get_source"]
