# Closet

- **Pattern:** Walk-in closet as library's **symmetric corridor** — a wardrobe bay on each LONG
  wall + a dressing ISLAND (oak dresser, width-fit to 1.7 m ⇒ 0.80 m tall) with a tufted OTTOMAN
  as the centre hero, on a runner. Full-length mirror focal on the back short wall; valet rail in
  the entry; three-tier shoe column + shoe rack on the right wall; folded-goods shelf on the left.
- **A wall shelf shipped 0.45 m INSIDE a wardrobe (user catch, 2026-07-13) → new core lint.** Wall
  furniture sits at `row_centers[]` whose pitch is set by each row's FLOOR occupants, so the back
  row's centre was 1.20 m from the middle row's while a 1.8 m bay + 1.5 m shelf need 1.65 m; and the
  shelf must be `ignore_overlap` to be `bottom=`-mounted, which `GradSolver.overlap_pairs` filters
  out — so nothing ever checked it. Added `IDSDL/lints.py::lint_embedded_wall_objects` (3D AABB over
  exactly the pairs the solver skips). Scene fix: dropped the third long item off the left wall (its
  centre is now empty — which the camera wanted anyway). **Three long items on one wall is an
  arithmetic, not a slot count.**
- **Camera rule, applied at DESIGN time:** tall bays go in the wall END slots; both long-wall
  CENTRES carry LOW pieces (folded-goods shelf 1.07 m, shoe rack topping at 0.48 m). The interior
  camera sits `0.04 × room_dimension` off the wall opposite the one it shoots (~0.18 m here), so
  deep cabinetry at a wall centre would swallow it and return a black view the VLM calls clean.
  Four clear views on the first phase-1 build.
- **Identity = PRODUCT:** every storage mesh pinned because the clothes/shoes are modelled IN it —
  the dataset's closet frames are mostly EMPTY, and only 2 of 12 shoe racks actually hold shoes.
- **Room size:** the `0.8` shrink vote (4 builds) was re-diagnosed, not obeyed — the room was too
  LONG (depth = 3 wall slots × the widest wall item = a 2.5 m unit ⇒ 8.15 m). Trimmed the wall
  items to 1.8 m, added a valet rail to the dead entry, then ONE safe `modulate_scale=0.9`.
  36.5 m² → **30.8 m² (4.61 × 6.67)**. Residual vote bounced 0.8/0.9/0.8/0.78 across identical
  builds = noise → declined.
- **Jitter/randomness:** RoomGroup randomness=0.1; seed 21.
- **Asset-gap risk:** MED — open wardrobes exist and are excellent (`future/03608677`), but the
  pale/greige cabinetry the plan wanted exists only as EMPTY frames ⇒ palette moved to dark walnut.
- **Gotchas:** a "floating shoe shelf" IS a wall unit (mount with `bottom=` + `ignore_overlap` +
  `is_static`; don't swap it); uniform scaling couples W↔H, so the 2.5 × 1.93 m closet system
  fitted to the slot came out 1.39 m tall (stunted) → replaced with a matching bay; the
  `add_lighting` chandelier the plan asked for is a banned fixture (flush brass at density 0.01).
- **Status:** built & VLM-clean 2026-07-13 (`scenes/closet.py`, seed 21), converged after 3 full
  builds. Worked recipe: `skills/examples/closet.md` + `closet_v1.py`. Replaces the thin
  52-category batch version of this scene.
