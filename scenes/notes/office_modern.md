# office_modern — notes

- **Status:** BUILT & VLM-clean — `scenes/office_modern.py` (seed=21), exported to
  `office_modern.blend`. Full recipe in `skills/examples/office_modern.md`. Distinct from
  `executive_office.py` (which adds a lounge zone); this is the small single-zone private office.
- **Plan:** planner headline "Daylight-Driven Green-Enclosed Office Nook" — a green wall wrapping a
  warm-wood desk under a window, slim storage flanking, rug-zoned workspace, tall plant, layered light.
- **Pattern:** ONE hero work zone (`WorkstationGroup`, `facing="back"` so the operator looks out at
  the window wall) + a storage backbone SPLIT TO THE CORNERS of the back wall (bookcase left, filing
  cabinet right, **back-centre empty so the interior camera can see the room** — the bakery
  blinded-view rule applied preventively) + two light walls (one print each) + door + standard window.
  Five occupied floor slots ⇒ a cozy shell by construction.
- **Heroes (pinned, measured):** desk `future/4d763507…` (1.80×0.72×0.90 warm wood — the
  executive_office desk `hssd/68049539…` renders WHITE-topped and kills the palette), task chair
  `hssd/2502dd40…` (→0.6 m), bookcase `hssd/2e29b3aa…` (2.17 m, shelves FILLED with books), filing
  cabinet `hssd/8090916a…` (→0.5 m), fiddle-leaf fig `future/f3a1cc15…` (0.95 m native → height-fit
  to 1.6 m), all-in-one computer `hssd/d41c6620…` (bundles keyboard+mouse), art `hssd/b9c49bfc…` +
  `hssd/18a5ab4d…` (both flat AND with visible artwork).
- **Fixes (reusable):**
  1. **Wall texture — three wordings, two different failure modes.** "deep green painted wall" →
     matched a PALE green → rendered beige (a wording bug). "a dark olive green color with subtle
     irregular brush strokes" → matched the library's darkest green at **0.82** and STILL rendered
     grey-taupe (a renderer limit: dark tones wash out at room scale — the bakery brick lesson).
     "solid deep green smooth uniform wall" → a true green that holds. **Verify the match offline
     against `wall_textures_embeddings.npz` (5 s) instead of re-wording via 8-minute builds.**
  2. **Empty-frame art caught at the audit gate** — the rank-1 abstract print previews as a blank
     white rectangle (the living_room_cozy v2 class); swapped at the contact sheet, not post-build.
  3. **"low filing cabinet" is a retrieval gap** — returned a tall apothecary cabinet + blank-preview
     meshes; `browse` over 18 file cabinets found a real 3-drawer unit immediately.
- **Scale:** `modulate_scale=0.8` applied ONCE in the final phase on a unidirectional decaying vote
  train (0.67→0.7→0.8); the post-apply bounce (0.92/0.8/0.85 across identical builds) declined as noise.
- **Clean by construction:** `no rotation` + `no wall overlap` + no lints on every build —
  `WorkstationGroup` pose, `facing` omitted on all wall placements, door and art in disjoint slots.
