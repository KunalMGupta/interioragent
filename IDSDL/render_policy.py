"""Global render policy.

The DSL renders a lot by default: every anchor group's VLM constraints
(ObjectProportions + Rotation) each do a full Blender 4-view render per
compile, and every RoomGroup compile renders the interior strip for each
room-level VLM constraint plus an 8-view `render_interior()` set.

For fast iteration we keep ONE critique channel: the room-level VLM strip
(`RoomGroup.render_interior_combined()`, cached once per compile). Everything
else is skipped under minimal mode — the code paths are untouched, just gated.

Default is MINIMAL. Set IDSDL_MINIMAL_RENDERS=0 to restore full rendering
(anchor-group VLM critique + the per-compile interior view set).
"""
import os


def minimal_renders() -> bool:
    return os.environ.get("IDSDL_MINIMAL_RENDERS", "1") != "0"
