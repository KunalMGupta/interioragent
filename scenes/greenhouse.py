"""
Greenhouse — SUPERSEDED.

The worked, built, VLM-clean greenhouse is `scenes/work/greenhouse.py` (seed=52); the recipe is
`skills/examples/greenhouse.md`. This file was a never-built first draft and had two real bugs worth
remembering:
  - floor_texture="gravel and stone path floor" embeds to a DRY STONE WALL, not gravel. The wording
    that actually matches the library's one gravel texture is "coarse grey gravel and pebble ground".
  - it glazed the left AND right walls at a time when interior views rendered with a transparent film,
    so both would have come out as black voids. That bug is now fixed (see the example), and the
    worked scene glazes both long walls deliberately.
"""
from scenes.work.greenhouse import *  # noqa: F401,F403
