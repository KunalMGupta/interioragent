"""Operating room / surgical suite — "Sterile Core with Service Walls" (planner target,
tmp/plan_A_hospital_operating_room___surg/plan.png).

v2 — rebuilt on the INGESTED surgical kit (user-supplied hospital.zip). v1 had to fake the
whole clinical layer (a med cart standing in for the anesthesia machine, folded bath towels
standing in for sterile trays); v2 uses real meshes for all of it. What changed:
  anesthesia machine   : white med cart  -> REAL anesthesia machine (custom/e6e17191)
  mayo stands          : white med carts -> REAL blue-draped instrument tables (custom/7db820c5)
  sterile "product"    : folded towels   -> REAL tray of surgical instruments (custom/c9cbd96a)
  + new: a gas sterilizer/autoclave (custom/aec28f56) and an ultrasound cart (custom/d295f3ed)
The PATIENT table stays the dataset mesh (future/51434359): the zip's three "surgical_table"
glbs turned out to be draped INSTRUMENT tables, not patient tables — the previews, not the
filenames, are the evidence.

STILL MISSING (the one gap the zip didn't close): a surgical DOME light. add_lighting also
yields exactly one fixture at density=0 (best_grid squares any higher count), so the prompt's
TWIN domes need two real ceiling meshes. A large flush round luminaire stands in.

Zoning (procedural signature: centre hero + 360 deg sterile ring + service walls, near-square):
- CENTRE     = the STERILE CORE: the operating table (hero) with the REAL anesthesia machine at
  the HEAD (back), the vitals monitor beside it, and two draped mayo stands flanking, each
  carrying a tray of surgical instruments at working height.
- BACK wall  = EQUIPMENT/HEAD wall: two tall supply cabinets (left+right slots), the flat
  gas-outlet headwall strip hung between them.
- LEFT wall  = SCRUB/PREP: the long stainless counter with an integrated sink + sterile linen.
- RIGHT wall = STERILE PROCESSING: the gas sterilizer/autoclave + the ultrasound cart.
- FRONT wall = the door (right) + the draped back table (left).
- NO windows: a real OR has none. (The black-void renderer limit is moot here anyway.)
- Lighting: the table dome + one flush LED panel pass at density 0.01 (small-room band).

SCALE — every ingested mesh had to be height-fitted. Ingest's VLM guesses a real-world WIDTH
and that guess resizes the asset: the anesthesia machine loaded 0.86 m tall (real: ~1.5 m), the
sterilizer 1.55 m (real: ~1.7 m). Same class as the dataset's bad `scale` metadata (corridor's
2x cabinets, children_room's 6x bean bag) — measure with get_whd(), then fit. Never trust the
caption or the auto-scale of an ingested mesh.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor layout.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("OperatingRoom", seed=34)

# --- dataset pins ---------------------------------------------------------------------
OR_TABLE = "future/51434359-427d-4f35-b2f2-f2ad9b875b2e"     # patient table: dark top, steel pedestal
MONITOR  = "custom/475c4c6d50144e1659d7bbc18121378a897d505e" # vitals monitor on a rolling stand
HEADWALL = "custom/920037c5376d7f897f7b4b142bea7792e938400d" # gas-outlet strip (FLAT -> wall-hangable)
CABINET  = "hssd/3a2fd60fc421b402f4bfd365fd2a7accfa6ce4b1"   # tall grey metal cabinet (native H=3.0!)
SINKCTR  = "hssd/79bf13063599b7fff88cc250d8fe76a2e46e9683"   # stainless counter w/ integrated sink
LINEN    = "hssd/248568c07dbfce7d21987a3af20f72d38d4398b3"   # stack of folded white cloth

# --- ingested surgical kit (hospital.zip) ---------------------------------------------
# Three things the raw zip needed before it was usable (see skills/examples/operating_room.md):
#  1. MERGE — the glbs were multi-mesh (the sterilizer had 143). The loader keeps only
#     imported_objs[0], so they would render DISASSEMBLED. Joined in Blender (join preserves
#     material slots; a trimesh concat strips them -> flat white).
#  2. UNIT-NORMALIZE — they shipped at wild scales (the ENT unit was 420 m wide).
#  3. RECENTER — the first ingest floated/sank every one of them ([Lint] FLOATS 0.81 m). Fixed
#     at the source in Blender (origin_set BOUNDS -> zero the location), NOT with a translate
#     hack in the scene. Recentering changes the file, hence the sha1 ids, hence these pins.
# Their auto-captions are unreliable (the VLM called the mayo stand a "drill press" and the
# instrument tray a "trough planter") — pinned by id, so the caption never matters. Trust the
# preview render, not the caption.
ANESTH   = "custom/e6e171912392d15999e34590299eaab0f78c9de9" # REAL anesthesia machine on a cart
MAYO     = "custom/7db820c55be6991b9b5541b094c4e5fef152f0aa" # blue-draped instrument (mayo) stand
BACKTBL  = "custom/c7966f1817cabdecbb6961d40d0ae3586d666bb6" # larger draped instrument BACK table
TRAY     = "custom/c9cbd96abf664f10c79d47f05f0da85c9e438329" # tray of surgical instruments
STERILZR = "custom/aec28f56f031931bc434b6f1689224d7000cb5ee" # gas sterilizer / autoclave
ULTRASND = "custom/d295f3ed29959a4b8336630adbb8362dff267487" # ultrasound cart

scene.prefetch_assets([
    "a surgical operating table with a dark padded top",
    "a patient vital signs monitor on a rolling stand",
    "a hospital headwall unit with medical gas outlets",
    "a tall grey metal medical supply cabinet",
    "a commercial stainless steel counter with an integrated sink",
    "a stack of neatly folded white cloth towels",
    "an anesthesia machine on a wheeled cart",
    "a blue draped surgical instrument mayo stand",
    "a draped surgical back table with instruments",
    "a tray of surgical instruments",
    "a gas sterilizer autoclave",
    "a medical ultrasound cart",
    "a flat round white LED ceiling light",
    "a flat rectangular LED ceiling panel light",
    "a wall-mounted flat screen display monitor",
])


def _fit_height(obj, target_h):
    """Uniform scale so the mesh stands target_h metres tall (aspect preserved).
    `scale(w)` sets WIDTH uniformly, so drive it from the width/height ratio."""
    return obj.scale(obj.get_width() * target_h / obj.get_height())


# --- the mayo stand: ONE unit, then duplicated ---------------------------------------
# The draped stand is its OWN RelativeGroup so place_on_top seats the instrument tray on the
# STAND. place_on_top ALWAYS targets the group's anchor — this call inside sterile_core
# (anchor = the operating table) would lay the instruments on the PATIENT surface
# (living_room_cozy v3: the lamp that landed on the armchair's seat).
# `2 * unit` runs the on-top tournament ONCE, so the pair comes out identical.
with scene.RelativeGroup() as mayo_unit:
    _mayo = scene.AddAsset("a blue draped surgical instrument mayo stand", asset_id=MAYO)
    # 0.92: at 1.05 the draped stands visually OUT-MASSED the patient table (they are really
    # instrument tables, not little mayo trays) — the hero has to stay the hero. Eye catch: the
    # VLM loop was clean, since nothing here is geometrically wrong.
    _fit_height(_mayo, 0.92)                     # loads 0.95 m
    mayo_unit.set_anchor(_mayo)
    if PHASE >= 2:
        # the sterile "product" at working height — a REAL instrument tray now, not linen
        mayo_unit.place_on_top(scene.AddAsset("a tray of surgical instruments", asset_id=TRAY))
mayo_l, mayo_r = 2 * mayo_unit

# --- CENTRE: the sterile core -------------------------------------------------------
# The hero ships short (native H=0.53 m) -> UNIFORM 1.5x (never width= alone, which squashes:
# children_room bean-bag / hospital_room bed lesson). Top lands at ~0.80 m.
or_table = scene.AddAsset("a surgical operating table with a dark padded top",
                          asset_id=OR_TABLE, modulate_scale=1.5)
with scene.RelativeGroup() as sterile_core:
    sterile_core.set_anchor(or_table)
    # HEAD of the table: the REAL anesthesia machine (loads 0.93 m -> a real one is ~1.5 m)
    anesth = scene.AddAsset("an anesthesia machine on a wheeled cart", asset_id=ANESTH)
    _fit_height(anesth, 1.50)   # loads 0.86 m
    sterile_core.place_on_back(anesth)
    sterile_core.place_on_back_right(scene.AddAsset("a patient vital signs monitor on a rolling stand",
                                                    asset_id=MONITOR))
    # the two draped mayo stands flanking the table, within the surgeon's reach
    sterile_core.place_on_left(mayo_l)
    sterile_core.place_on_right(mayo_r)
    if PHASE >= 3:
        # ONE large round luminaire over the table = the surgical dome (no dome mesh exists).
        # A FLUSH fixture, never a pendant: add_lighting caps a fixture's height at 1.5 m but
        # pins its origin at the CEILING, so a stemmed lamp hangs into the room and its emissive
        # mesh blows the exposure (executive_office). modulate_scale=2.6: at 1.6 it read as an
        # ordinary downlight — no VLM signal fires on "too small to be a dome", an eye catch.
        sterile_core.add_lighting("a flat round white LED ceiling light", density=0,
                                  modulate_scale=2.6)

# --- the room -----------------------------------------------------------------------
# modulate_scale=0.9: v1 converged at 0.85, but v2 adds real floor equipment (sterilizer,
# ultrasound cart, back table), so the shell needs a little more room to keep the sterile ring.
with scene.RoomGroup(modulate_scale=0.9, randomness=0.08) as room:
    room.place_walls(floor_texture="pale green vinyl flooring",
                     ceiling_texture="white",
                     wall_texture="white ceramic wall tiles")

    room.place_on_center(sterile_core, facing="front")
    # The sterile ring is what actually SIZES the room (game_room's cue-stroke rule): a scrub
    # team must be able to walk a full loop around the table.
    room.add_clearance(or_table, distance=1.2, dir="all")

    # BACK = equipment/head wall: two tall supply cabinets in the LEFT/RIGHT slots. Never a wall
    # CENTRE: interior cameras sit at ~1.4-1.5 m at each wall's centre, so a taller fixture there
    # blinds that view AND corrupts the VLM votes judged from it (bakery's rotation storm).
    cab_l = scene.AddAsset("a tall grey metal medical supply cabinet", asset_id=CABINET)
    cab_r = scene.AddAsset("a tall grey metal medical supply cabinet", asset_id=CABINET)
    _fit_height(cab_l, 2.0)          # native 3.0 m -> a believable supply cabinet
    _fit_height(cab_r, 2.0)
    room.place_on_back_wall_left(cab_l)
    room.place_on_back_wall_right(cab_r)

    # LEFT = scrub/prep: the long stainless counter, with sterile linen stacked on it. Again its
    # own anchor-unit so place_on_top lands on the COUNTER. Wall placements accept a composed
    # group (bakery's window-bar lesson). facing omitted everywhere: the default faces the room.
    sink_counter = scene.AddAsset("a commercial stainless steel counter with an integrated sink",
                                  asset_id=SINKCTR)
    _fit_height(sink_counter, 0.92)
    with scene.RelativeGroup() as prep_station:
        prep_station.set_anchor(sink_counter)
        if PHASE >= 2:
            prep_station.place_on_top(scene.AddAsset("a stack of neatly folded white cloth towels",
                                                     asset_id=LINEN))
    room.place_on_left_wall_center(prep_station)

    # RIGHT = sterile processing: the autoclave and the ultrasound cart. Both are TALL, so they
    # take the left/right slots and leave the wall centre clear for the camera.
    sterilizer = scene.AddAsset("a gas sterilizer autoclave", asset_id=STERILZR)
    _fit_height(sterilizer, 1.70)    # loads 1.55 m
    room.place_on_right_wall_right(sterilizer)
    ultrasound = scene.AddAsset("a medical ultrasound cart", asset_id=ULTRASND)
    _fit_height(ultrasound, 1.40)    # loads 1.70 m — too tall for a wheeled cart
    room.place_on_right_wall_left(ultrasound)

    # FRONT = entry: the door, plus the draped back table (where the scrub nurse works).
    back_table = scene.AddAsset("a draped surgical back table with instruments", asset_id=BACKTBL)
    _fit_height(back_table, 1.00)
    room.place_on_front_wall_left(back_table)
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # the flat gas-outlet strip between the two cabinets, above the head of the table
        room.place_on_wall_back_center(
            scene.AddAsset("a hospital headwall unit with medical gas outlets", asset_id=HEADWALL))
        # a clinical display in the surgeon's sightline
        room.place_on_wall_right_center(
            scene.AddAsset("a wall-mounted flat screen display monitor"))
        # even, glare-free ambient. density is a fixture COUNT that grows with floor area:
        # 0.01 is the small-room band (music_studio's starfield lint).
        room.add_lighting("a flat rectangular LED ceiling panel light", density=0.01)

scene.export("operating_room_v1.blend")
