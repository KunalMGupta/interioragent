"""Hospital patient room — "Bed-Centered Healing Inpatient Room" (planner target,
tmp/plan_a_hospital_patient_room___a_sing/plan.png).

A single-bed inpatient room balancing clinical function with calm: warm wood-look
floor, soft sage walls, a hospital bed hero on the headwall, medical equipment at
the bedside, a daylight visitor nook, and biophilic softeners (plants, botanical
art, soft textiles).

Zoning (procedural signature: bed-as-hero + purpose-loaded walls):
- BACK wall = the HEADWALL: hospital bed (with attached IV arm) centered, a white
  bedside cabinet on its left, the vitals monitor on its right, the ingested
  headwall unit (gas outlets — FLAT strip) hung on the wall above.
- RIGHT wall = DAYLIGHT + VISITOR zone: standard window with sheer curtains, a
  visitor nook (two upholstered chairs arced around a small round table on a rug).
- LEFT wall = STAFF/SERVICE zone: compact sink vanity (hygiene counter) center,
  the white 3-drawer med supply cart near the bed end, a tall wood wardrobe.
- FRONT wall = door (right), framed botanical print center (in the patient's
  sightline), wheelchair parked in the front-left corner.
- Lighting: one flush LED pass at density 0.01 (small-room lesson).

Known gaps (asset audit): no standalone overbed table (surgical cantilever mesh
reads wrong — bedside cabinet + med cart carry the function); no privacy-curtain
mesh (window curtains carry the softness).

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the
floor layout (~1 min) before surface dressing (2) and walls/lighting/mood (3).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("HospitalRoom", seed=42)

BED      = "future/280e7e5e-4128-4696-abb8-72744becce48"     # metal hospital bed, blue mattress, IV arm
HEADWALL = "custom/920037c5376d7f897f7b4b142bea7792e938400d" # headwall strip w/ gas outlets (flat)
MONITOR  = "custom/475c4c6d50144e1659d7bbc18121378a897d505e" # vitals monitor on rolling stand
WHEELCH  = "custom/07c9f10971507810789d358c15c1861a4e19a67f" # hospital wheelchair
MEDCART  = "hssd/cc15f4f67e55963a009abe0f4fe10148cb632f2f"   # white 3-drawer metal supply trolley
# hssd/3cc3f058... FLOATS 0.14 m (off-center mesh origin) — swapped per the lint
VANITY   = "future/a521cb7a-d9df-4bc8-a2e2-8dc1e61c4d23"     # white vanity cabinet w/ rectangular sink

scene.prefetch_assets([
    "a metal hospital bed with side rails and an IV pole",
    "a hospital headwall unit with medical gas outlets",
    "a patient vital signs monitor on a rolling stand",
    "a hospital wheelchair",
    "a white metal medical supply cart with drawers",
    "a compact white cabinet with a built-in sink",
    "a white bedside cabinet with drawers",
    "a tall light wood wardrobe cabinet",
    "a light grey upholstered armchair with wooden legs",
    "a small round light wood side table",
    "a leafy potted plant in a white planter",
    "a small potted succulent plant",
    "a framed botanical print in a light wood frame",
    "a plain light grey area rug",
    "a flat round LED flush mount ceiling light",
])

# --- BACK wall: the patient-care core (bed hero + bedside kit as ONE group) ------
# mesh ships at ~half scale (native length 1.0 m; real bed ~2.1 m incl. the IV
# arm's height) — UNIFORM 2.1x, never width= alone (bad-scale-asset lesson)
bed = scene.AddAsset("a metal hospital bed with side rails and an IV pole", asset_id=BED,
                     modulate_scale=2.1)
with scene.RelativeGroup() as care_core:
    care_core.set_anchor(bed)
    # bedside cabinet and vitals monitor aligned to the headboard, like nightstands
    with scene.RelativeGroup() as bedside:
        bedside.set_anchor(scene.AddAsset("a white bedside cabinet with drawers"))
        if PHASE >= 2:
            bedside.place_on_top(scene.AddAsset("a small potted succulent plant"))
    care_core.place_on_back_left(bedside)
    care_core.place_on_back_right(scene.AddAsset("a patient vital signs monitor on a rolling stand",
                                                 asset_id=MONITOR))

# --- RIGHT wall: the visitor nook (chairs arced around a small table, on a rug) ---
with scene.AroundGroup(sparsity=0.2, jitter=0.3) as visitor_nook:
    nook_table = scene.AddAsset("a small round light wood side table")
    visitor_nook.set_anchor(nook_table)
    nook_chairs = 2 * scene.AddAsset("a light grey upholstered armchair with wooden legs")
    visitor_nook.place_arc(nook_chairs)
    # arc/side placements orient sideways by default (living_room lesson) — aim
    # each chair at the shared table; VLM flagged both after the full build.
    for c in nook_chairs:
        visitor_nook.face(c, toward=nook_table)
    if PHASE >= 2:
        visitor_nook.place_rug("a plain light grey area rug", size=1.0)

# --- the room ----------------------------------------------------------------------
# 0.75: after redistributing the left-wall overload the vote returned to 0.8
# (user agreed the room read too big). The wall runs are short now — small
# items, generous slot gaps — so a deeper shrink is safe (laundromat lesson:
# a genuinely sparse room may go well below 1.0).
with scene.RoomGroup(modulate_scale=0.75, randomness=0.1) as room:
    room.place_walls(floor_texture="light warm oak wood plank floor",
                     ceiling_texture="white",
                     wall_texture="pale sage green")
    # facing omitted on wall placements: the default heuristic already faces the room
    room.place_on_back_wall_center(care_core)
    room.place_on_right_wall_right(visitor_nook)
    # WALL-LOAD BALANCE: wardrobe+vanity+cart+wheelchair all on the left wall
    # inflated the room depth (RoomGroup grows the shell to fit the longest wall
    # run) — wardrobe redistributed to the front wall, wheelchair takes its slot.
    # Vanity mesh front is REVERSED (fixed once via front_cache 180, not facing=).
    room.place_on_left_wall_center(scene.AddAsset("a compact white cabinet with a built-in sink",
                                                  asset_id=VANITY))
    room.place_on_left_wall_left(scene.AddAsset("a hospital wheelchair", asset_id=WHEELCH))
    room.place_on_left_wall_right(scene.AddAsset("a white metal medical supply cart with drawers",
                                                 asset_id=MEDCART))
    room.place_on_front_wall_left(scene.AddAsset("a tall light wood wardrobe cabinet"))
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")
    if PHASE >= 3:
        room.place_on_wall_back_center(
            scene.AddAsset("a hospital headwall unit with medical gas outlets",
                           asset_id=HEADWALL))
        room.place_on_wall_front_center(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        room.place_window_standard("right_wall", position="center",
                                   curtain="light sheer curtains")
        room.place_on_back_right_corner(
            scene.AddAsset("a leafy potted plant in a white planter"))
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

scene.export("hospital_room_v1.blend")
