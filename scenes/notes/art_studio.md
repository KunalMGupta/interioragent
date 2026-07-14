# Art Studio

- **Status (v2, 2026-07-13):** REBUILT ON INGESTED EASELS & VLM-clean — `scenes/art_studio.py`
  (seed=13) → `art_studio.blend`. `no rotation` / `no wall overlap` / no lints; room vote converged
  to 0.82 against `modulate_scale=0.85`. Full recipe: `skills/examples/art_studio.md`.
- **THE v2 HEADLINE — one correct mesh deleted ~40 lines of workaround.** `art_done.zip` brought
  three real **2.00 m floor easels** (painted canvas `custom/fa1ed245`, blank `custom/3ae58737`,
  bare `custom/f65f7c3d`). Every v1 workaround evaporated: the silhouette hunt past the picker's
  KIDS' crayon easel; the 1.00 m → 1.65 m height-fit; the `place_on_top` that shattered on the
  skeletal A-frame (postage-stamp canvases on the crossbar); the floor-standing-canvas fallback;
  and the canvas-as-anchor inversion that stopped the placement verb showing the canvas's blank
  BACK to the room. All of it is now `AddAsset(asset_id=EASEL_ART)` + one `place_on_*`.
  **Rule: when the loop is clean and the room still doesn't convince, it's ASSETS, not placement —
  a growing pile of workarounds IS the signal that the asset is wrong** (operating_room, escalated).
- **v2 pins (ingested, all preview-verified):** easel+painting `custom/fa1ed2452840e6cc…`,
  easel+blank canvas `custom/3ae587371564779c…`, paint box + palette + brushes
  `custom/65b641003dcd65f9…`, art supply cart `custom/4d5c0810966a3a08…`. Pinning by id is
  MANDATORY for ingested meshes (a mis-captioned asset is invisible to NL retrieval), and until a
  `CreativeStudioRetriever` pool exists, "an artist easel" still routes to
  `PresentationFixtureRetriever` (boards/projectors).
- **REJECTED at the contact sheet** (filenames lie; the preview is the evidence):
  `canvas_stretcher` → a grey tapered MONOLITH, not a canvas; `easel_stool_and_canvases` →
  flat-shaded STYLISED red/blue art that would clash with a photoreal room. 11/13 art meshes usable.
- **Ingest gotcha that cost a full pass** (now in workflow/vlm_feedback.md): the prescribed Blender
  fix pass **silently no-ops without `parent_clear`** — the glTF importer parents meshes to EMPTIES,
  so `obj.location = (0,0,0)` only zeroes the LOCAL location and every asset came out exactly as
  off-centre as it went in (the easels at 1.35× their own bbox). And **trimesh's geometry count is
  material PRIMITIVES, not objects**, so it reports MULTIMESH on files that are already one object.
- **CAMERA:** the easels are 2.00 m, so they are kept OUT of the left wall's CENTRE slot
  (`back_left` + `front_left`). A fixture taller than the ~1.4 m interior camera at a wall centre
  blinds that view and hallucinates rotation flags (bakery).
- **Still missing after the ingest:** paint-stocked SHELVING (the shelf is still a book-filled
  bookcase) and a bare stretched canvas.

---

## v1 notes (kept — the workarounds are what you do while the ingest does not exist)

- **Status:** BUILT & VLM-clean — `scenes/art_studio.py` (seed=13), exported to `art_studio.blend`.
  Full worked recipe in `skills/examples/art_studio.md`. Supersedes the 29-line auto-generated draft
  (a `place_circle` of 4 easels around a supply table) that was never built — the planner's brief is a
  different and better room: ONE hero painting zone worked in daylight, not a ring of easels. (The old
  note's one-line guess, "Asset-gap risk: MED — easels", turned out to be exactly right — see below.)
- **Plan:** planner headline "North-Light Painter's Loft" — an upright easel holding a canvas, an
  expansive paint-splattered worktable with brushes/palettes at arm's reach, a wall of north glazing,
  canvases leaning on calm white walls, warm-wood shelving + a rolling cart of paints.
- **Pattern:** work zone ON the glass + storage backbone opposite (executive_office/office_modern
  skeleton, re-cut for daylight). LEFT (long) = floor-to-ceiling glazing with the two easels standing
  in it, turned to face the room. CENTRE = the hub (work table + stool + paint still life + jute rug +
  the ceiling lighting hung off this group). RIGHT (long) = the backbone: shelf in the wall's **LEFT**
  slot (it is 1.60 m — above the ~1.4 m interior camera, so the CENTRE stays clear: the bakery
  blinded-view rule applied preventively) + supply cart, one finished painting hung between them.
  BACK (short) = a packed `GridGroup` row of four leaning canvases. FRONT (short) = the door.
  Shell auto-sizes to 5.60 × 4.97 m (27.8 m²).
- **Heroes (pinned, measured with `get_whd()` before the first build):** easel `hssd/5e19cedd…` (bare
  wood A-frame — 0.50 × **1.00** native, height-fit to 1.65 m), work table `hssd/b752a35d…` (0.63 →
  0.76 m), stool `hssd/5cbddc42…`, shelf `hssd/2db50fb1…` (shelves modelled FULL), cart
  `future/10d2a1e8…` (shelves already LOADED), **the identity prop** `future/4a9dc3a5…` (brushes in a
  glass jar + palette + paint tubes), architect lamp `hssd/a980ba02…`, four canvases with REAL artwork
  (`hssd/c96b3310…`, `hssd/4820e7f8…`, `hssd/88228361…`, `hssd/7acc5775…`).
- **THE BIG ONE — the hero is a gap, and the picker's rank-1 is its TOY version.** No floor-standing
  artist easel with a canvas exists. `"a wooden artist easel with a canvas on it"` returns
  `future/fc0b2119` — **a KIDS' easel holding a crayon drawing of a sunny house** — at a perfectly
  respectable similarity, with a fine caption and fine geometry. It would have made this room read as a
  **kindergarten**, and nothing in the VLM loop can see that. Only `show(n, big=True)` gives it away
  (at contact-sheet size the crayon drawing reads as "a colourful canvas"). The rest of the pool is
  whiteboard easels, chalkboard easels and tripod PLANT STANDS. → Hunted by SILHOUETTE (tv_studio's
  rule) and pinned the one true A-frame. Its caption "table easel" turned out to be **literal**: 1.00 m
  native, i.e. a toy beside a 0.76 m table → height-fit to 1.65 m.
- **`place_on_top` shatters on a SKELETAL anchor.** `place_on_top(canvas)` with the easel as anchor
  rendered a **postage-stamp canvas parked on the lower crossbar** — on both easels — because an A-frame
  has no substantial horizontal region, so the tiler tiles a crossbar sliver and clamps the canvas to
  that cell. The flat-rug/3-cm-bean-bag class, generalised: **an anchor with no real TOP cannot be
  stacked on.** Loop-clean through it (`no rotation`, no lints); caught by EYE at phase 2. There is no
  vertical lift to fall back on (`bottom=` is wall-adjacent only), so the fix is geometric: stand the
  canvas on the floor hard against the easel and let the A-frame rise behind it.
- **Anchor a unit on the piece whose FACING carries the read.** Anchoring the easel and hanging the
  canvas off its front (`place_on_front_adjacent`) turned the canvas's **blank back** to the room — the
  `*_front*` verbs bake a face-the-anchor rotation (the seating semantic). → Anchor the **CANVAS**,
  `place_on_back_adjacent(easel)`. The canvas then inherits the room's `facing=`, and the symmetric
  A-frame's own facing stops mattering.
- **Leaning canvases are not a mesh — a canvas IS a flat upright slab.** Four of them standing as FLOOR
  objects in a packed `GridGroup(sparsity=0.04, randomness=0.3)` row, placed flush with
  `place_on_back_wall_center`, is the whole effect. Mixed heights (1.15/0.85/1.05/0.95) so it reads as a
  working stack; all under the ~1.4 m camera, so the back view is never blinded.
- **"Fill the floor instead of shrinking" is NOT universal.** The shrink vote (0.75/0.7/0.81/0.5/0.7/
  0.65/0.75) never flipped = signal, so I tried the children_room/kindergarten fill — and **every fill
  grew the shell**: a second composed canvas row took it 5.60 → **6.86 m** wide (in a front-WALL slot
  AND in a corner floor slot alike), and the cart in the `right` FLOOR slot forced the middle row to fit
  easel + table + cart → 6.70 m wide with the depth collapsed to 4.39 m, **jamming the back camera**.
  (All measured off the exported floor glb, not guessed.) The greenhouse plant-bed is free because it is
  ONE object in ONE slot; **a composed ROW claims a row/column the shell must grow to fit.** → Dropped
  the fill, kept the good shell, applied ONE decisive `modulate_scale=0.85` — deliberately **short of**
  the vote, because a painter must step BACK to judge a canvas and that floor is the category (garage's
  vehicle lane / corridor's centre lane). Vote decayed to `0.8` → declined.
- **Declined as noise:** `rotate round stool by 180 to face the table` (×2, one build) — a **round
  backless** stool has no front, and it was already `face()`d at the table. Did not recur.
- **Clean by construction otherwise:** `no rotation` / `no wall overlap` / zero lints on every other
  build — `facing` omitted on all wall placements, the tall shelf kept out of the wall CENTRE, door and
  hung art in disjoint slots, the canvas row deterministic.
- **Vibe layer DECLINED (operating_room's inversion).** Greenery / a warm accent seat / a warm envelope
  would break this room: a working loft earns its read by being austere, white-walled and cluttered with
  WORK. The warmth comes from the wood and the paintings — which is where the palette belongs.
- **Asset-gap risk: MED.** Two ingest candidates, in priority order: (1) **a real floor easel holding a
  canvas** — would fix both the toy-easel trap and the floor-standing-canvas compromise in one mesh;
  (2) **paint-stocked shelving** (the current shelf is a book-filled bookcase, which reads as stocked
  storage but leans faintly "study").
