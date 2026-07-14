# Operating Room

- **Pattern:** Relative operating table + carts (surgical light); supply/scrub on walls; monitor
- **Jitter/randomness:** RoomGroup randomness=0.1
- **Review first:** operating table + surgical light retrieval
- **Asset-gap risk:** HIGH — surgical equipment
# Operating Room

- **Pattern:** Hero-in-the-middle sterile core (game_room skeleton, dental_office discipline).
  Central operating table + anesthesia cart/vitals monitor at the head + two draped mayo carts;
  a 1.2 m `add_clearance(dir="all")` sterile ring SIZES the room. Service walls: twin tall supply
  cabinets + gas-outlet headwall (back), stainless scrub counter (left), instrument trolley +
  wall display (right), door (front). No windows (real ORs have none).
- **Asset gap:** NO surgical dome light, NO anesthesia machine, NO instrument-tray mesh in the
  dataset (all three confirmed by browse — "dome light" returns residential lamps, "instrument
  tray" returns kitchen cutlery). Substituted: a large FLUSH round luminaire (never a pendant),
  a med cart at the head, folded white linen as sterile drapes. All logged as ingest candidates.
  BUT a real OR table DOES exist: `future/51434359` (captioned only "medical examination table").
- **Scale traps (both caught offline with `get_whd()`):** hero ships SHORT (H=0.53 →
  `modulate_scale=1.5`); supply cabinet ships 3.00 m tall (→ height-fit to 2.0 m, and keep it
  OUT of the wall-centre slots or it blinds the interior camera — bakery lesson).
- **Jitter/randomness:** RoomGroup randomness=0.08, modulate_scale=0.85 (final-phase, on the
  0.8 vote; decayed to 0.97 = converged).
- **Status:** built end-to-end 2026-07-12; `no rotation / no wall overlap` / no lints on every
  build. See `skills/examples/operating_room.md`.

## v2 — rebuilt on the ingested surgical kit (hospital.zip, 2026-07-13)
- The user diagnosed v1 as asset-starved (correct) and supplied `hospital.zip`. Ingested a REAL
  anesthesia machine, blue-draped instrument/mayo tables, trays of surgical instruments, a gas
  sterilizer/autoclave and an ultrasound cart. v1's fakes (med cart = anesthesia machine, folded
  BATH TOWELS = sterile trays) are gone.
- **The zip needed 3 fixes before ingest, all silent:** multi-mesh (→ Blender `join`, preserves
  materials; the loader keeps only mesh[0] → would render disassembled), wild units (ENT unit
  420 m), off-center origins (→ `origin_set BOUNDS`; the first ingest floated/sank everything).
  Recentering changes the sha1 → the ids change → re-pin.
- **Ingest's auto-caption and auto-scale are both wrong often** (mayo stand → "drill press";
  anesthesia machine loaded 0.86 m, real ~1.5 m). Pin by id, `get_whd()`, height-fit.
- 6 of 20 ingested assets were usable; the three "surgical_table" glbs were INSTRUMENT tables, so
  the dataset's `future/51434359` remains the patient-table hero.
- STILL missing: a surgical DOME light (not in the zip). One flush luminaire stands in; the
  prompt's TWIN domes need two real ceiling meshes (`add_lighting` gives exactly one at
  density=0, and best_grid squares any higher count).
