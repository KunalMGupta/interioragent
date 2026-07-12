"""Phase-gated builds — the coarse-to-fine workflow made mechanical.

A scene program can OPT IN to phased construction by gating its statements:

    from IDSDL.phases import current_phase
    PHASE = current_phase()                      # defaults to 3 = build everything

    # phase 1 — anchors: floor furniture, composed stations, the RoomGroup shell
    # phase 2 — surfaces: place_on_top / place_inside dressing (VLM tournaments)
    # phase 3 — walls & mood: wall art, windows/doors*, lighting, rugs, textures
    if PHASE >= 2:
        counter_group.place_on_top([...])
    if PHASE >= 3:
        room.add_lighting(...)

Then `workbench run <program> --phase 1` builds ONLY the floor layout — roughly a
minute instead of many — so layout errors (room size, overlaps, clearances,
orientation) are caught and fixed before any expensive surface dressing or
lighting is attempted. `workbench run <program>` (no flag) and every existing
non-gated program behave exactly as before: current_phase() is 3 unless the
IDSDL_PHASE env var says otherwise, and a program with no gates ignores it.

*Doors influence the floor solve (auto door clearance), so placing doors in
phase 1 is also reasonable — the recommended split is a convention, not a rule.
The one hard rule: LATER phases must only ADD; never move phase-1 geometry.
"""
import os

DEFAULT_PHASE = 3
PHASE_NAMES = {1: "anchors", 2: "surfaces", 3: "walls+mood"}


def current_phase(default: int = DEFAULT_PHASE) -> int:
    """The build phase requested via IDSDL_PHASE (workbench --phase sets it).
    Clamped to [1, 3]."""
    try:
        p = int(os.environ.get("IDSDL_PHASE", default))
    except (TypeError, ValueError):
        p = default
    return max(1, min(DEFAULT_PHASE, p))
