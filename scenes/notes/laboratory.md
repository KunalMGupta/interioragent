# Laboratory

- **Pattern:** Repeated-unit grid + clinical perimeter. Four bench units (bench + stool +
  microscope + reagent bottles) in a 2x2 `GridGroup` centre; autoclave + stocked glass reagent
  cabinet (back), stainless sink counter + gas-cylinder bank under the window (left), yellow
  flammables cabinet + lab fridge (right), door + trolley + whiteboard (front). Inverted vibe
  layer (operating_room): no rug, no plants — the only colour is functional.
- **The category read comes from the PRODUCT, not the grid.** classroom / computer_room /
  laboratory are the same layout; the microscopes + reagent bottles at working height are what
  make it a lab.
- **Asset gap:** HIGH, and *sharper than it looks*. 12 of the identity props return `0.000`
  (EMPTY candidate list): fume hood, microscope, centrifuge, bunsen burner, beakers, flasks,
  test-tube racks, petri dishes, eyewash, safety sign. But the microscope + autoclave + gas cart
  ALREADY EXIST in `custom/` (operating-room ingest leftovers) — invisible to NL retrieval, so
  **pin by id**. Glassware = the "decorative glass decanters" mesh (silhouette, not caption).
  **Ingest candidates, in order: FUME HOOD (the only true blocker), eyewash, centrifuge, benchtop
  glassware.**
- **Mesh traps (both fixed at the source, `tmp/fix_lab_glbs.py`):** the ingested microscope's
  origin was **+118% of its height off-centre** → it sank 0.23 m through the bench and read as
  floor-standing (the VLM loop stayed clean); the gas cart's was −26% → floated 0.62 m. **An
  ingest batch's UNUSED meshes never got its repair pass — check glb bounds before pinning one.**
- **Jitter/randomness:** GridGroup sparsity=0.12 (0.3 inflated the shell and cost a `0.5` shrink
  vote), randomness=0.15; RoomGroup randomness=0.15, modulate_scale=0.92 (final-phase; residual
  0.9 declined).
- **Status:** built end-to-end 2026-07-13; `no rotation / no wall overlap` / no lints on the final
  build. Program `scenes/work/laboratory_v1.py`; recipe `skills/examples/laboratory.md`.
  (Supersedes the thin first-draft `scenes/laboratory.py`.)
