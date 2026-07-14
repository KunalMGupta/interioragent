# executive_office — notes

**Pattern:** a single private/executive office split into two zones around a **storage
backbone**: (1) a wide bookcase on the back wall (anchor + proportion-setter), (2) a
warm-wood desk `WorkstationGroup` in front of it (executive faces the room/window), and a
small **lounge nook** (2-seat sofa + round table + orange accent chair) set apart on the
left. Warm traditional-modern palette: warm oak + soft-white walls + grey upholstery +
brass-ish fixture + one orange accent + greenery. Distinct from `office.py` (open-plan grid).

**Heroes (pinned):** desk `hssd/6804953904df…` (warm-wood top, slim metal legs, FLAT),
bookcase `future/f1f6fd18…` (wide grid + lower cabinet), orange winged accent chair
`hssd/91999bead15…`, grey 2-seat sofa `hssd/7092826dbd…`, round side table `hssd/d4bff730…`.
Built on the reusable `WorkstationGroup` + `DesktopWorkstationRetriever` (laptop + task lamp
+ succulent on-top).

**Gotchas (full detail in skills/examples/executive_office.md + workflow/vlm_feedback.md):**
- **`add_lighting` needs a FLAT/FLUSH fixture, never a hanging chandelier.** A sputnik/globe
  chandelier hangs ~1.5 m into the room (height cap + ceiling-pinned origin) as giant emissive
  globes and blows the scene out to white. Use `"a flat round LED flush mount ceiling light"`,
  density ~0.2 (density = fixture count, fixed total watts); the desk lamp is the warm layer.
- **Executive facing:** `place_on_center(station, facing="back")` — WorkstationGroup operator is
  local +Z facing the desk, so `facing="back"` seats the boss on the bookcase side facing the room.
- **Window = black night void** (no exterior env); use `place_window_standard` (small pane), not the
  wide `place_window_picture`, and fix room lighting first so the void reads as "evening."

**Status:** built & VLM-clean 2026-07-05 (`scenes/executive_office.py`, seed 42). Rescale
converged at `modulate_scale=0.85`; remaining VLM notes (side-table 0.8, sofa-rotate) judged noise.
