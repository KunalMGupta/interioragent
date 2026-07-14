"""Dental office — "Cheerful Pediatric Operatory" (planner: "Glass-Partitioned Modern Dental
Exam Suite").

Planner target: a single operatory with the dental chair as the focal hub, wood-toned perimeter
cabinetry with wipe-clean counters, a green accent to calm anxiety, bright even ceiling light, a
glass entry + daylight. Palette: soft-white walls, warm wood, light blue-grey vinyl tile; the
orange pediatric chair is the single pop of colour. Built coarse-to-fine
(skills/workflow/coarse_to_fine.md + skills/examples/dental_office.md).

Layout — HERO IN THE MIDDLE, purpose-loaded perimeter (a single operatory is compact/near-square,
so you do NOT load long walls to stretch it — you balance all four and let modulate_scale set the
size):
- CENTRE     : the dental UNIT, facing="front". The operatory is the room; it stands free in the
               middle so the dentist can work all the way around it (saddle stool on its back-left,
               assistant cart at the foot on its front-right — both inside the group, so the whole
               operatory rotates as one).
- RIGHT wall : the handwash/prep counter — a wood base cabinet with an integrated stainless sink.
               NOT a bathroom vanity: the vanity retriever's sets bundle a wall mirror and the
               corner then reads bathroom, not clinic.
- LEFT wall  : tall supply storage (the only other bulk mass) + the kids' poster above it. Balances
               the sink counter opposite so neither wall run inflates the shell.
- BACK wall  : the calm wall in the patient's reclined sightline — the botanical green leaf print
               (the plan's "green accent wall": place_walls takes ONE wall_texture for all four
               walls, so the accent is HUNG, not painted). Plant + admin workstation take the two
               back corners, the dead space the operatory does not want.
- FRONT wall : the glass-partition suite — a floor-to-ceiling glass panel (place_door only mounts a
               fixed OPAQUE door, so the "glass entry" is a glass WALL) with the real door displaced
               to the left wall. No curtain: parted drapes render as opaque panels with a black gap.

Identity comes from ONE INGESTED SET ASSET: the dental unit mesh is chair + overhead exam-light arm
+ articulated patient monitor + delivery/instrument tray + cuspidor in a single mesh — one ingest
closed four asset gaps at once. Everything else is ordinary dataset retrieval.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/dental_office_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the desktop + drops the plant; phase 3 adds the
wall decor, the glass wall and the ceiling light.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("DentalOffice", seed=35)

# ---- pinned assets (gate-3 audit) ------------------------------------------------------------
# Ingested complete pediatric dental unit (chair + light + delivery + monitor + cuspidor). The
# dataset has NO true dental treatment chair — "a dental examination chair" retrieves a blue
# phlebotomy exam chair, then salon/barber chairs — so this asset was the crux. It also ranks #1
# for the query below, but pinning is durable.
DENTAL_UNIT = "custom/64a7f627dc9e7a246ebfef4bc10fb15c27be636f"
# Simple flat 0.72 m office desk: the default desk retrieval returned a 1.2x1.48x0.88 m hutch/
# back-unit that slipped past the flat-top rule, and place_on_top's AABB fallback would seat the
# computer on the HUTCH top. A flat desk is the safe anchor for a WorkstationGroup.
FLAT_DESK = "hssd/a42e2ef37ca205ecb1927bde89c6b618ddcda71b"
# Wood base cabinet + stainless sink, NO mirror. "a wood bathroom vanity with a sink" routes to the
# BathroomVanityUnitRetriever, whose sets bundle a wall mirror -> the counter read bathroom.
SINK_CABINET = "hssd/048d80c36ddc6ac63785ca08ccf231431195717c"

scene.prefetch_assets([
    "a pediatric dental treatment chair unit",
    "a dentist saddle stool on casters",
    "a white mobile medical instrument cart on casters",
    "a wood base cabinet with a stainless sink",
    "a tall white medical supply cabinet",
    "a simple flat wooden office desk",
    "an ergonomic office chair",
])

# --- admin/charting workstation for the back-left corner (reusable WorkstationGroup; the paired
#     DesktopWorkstationRetriever supplies the on-top computer/lamp/accessories) ---
# The desk + operator chair are phase-1 floor mass; the DESKTOP is the phase-2 surface layer, and
# its gate sits INSIDE the `with` block — a place_on_top gated outside the block never runs at all.
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a simple flat wooden office desk", asset_id=FLAT_DESK))
    station.place_chair(scene.AddAsset("an ergonomic office chair"))
    if PHASE >= 2:
        # the computer is a SET (monitor + keyboard + mouse in one mesh) — standalone keyboards
        # and mice barely exist in the dataset
        station.place_computer(scene.AddAsset("an all-in-one desktop computer"))
        station.place_accessories([   # <= 3 on-top items total (computer + these two)
            scene.AddAsset("an articulated desk lamp"),
            scene.AddAsset("a small potted succulent for a desk"),
        ])

# --- central operatory: the dental unit + the dentist's saddle stool + assistant cart ---
with scene.RelativeGroup() as operatory:
    unit = scene.AddAsset("a pediatric dental treatment chair unit", asset_id=DENTAL_UNIT)
    operatory.set_anchor(unit)
    operatory.place_on_back_left(scene.AddAsset("a dentist saddle stool on casters"))
    operatory.place_on_front_right(scene.AddAsset("a white mobile medical instrument cart on casters"))

# modulate_scale=0.85 acts on the Phase-1/2 "rescale room by 0.85" VLM feedback (final phase).
with scene.RoomGroup(modulate_scale=0.85, randomness=0.12) as room:
    room.place_walls(floor_texture="light grey vinyl flooring",
                     ceiling_texture="white", wall_texture="soft white")
    # a reclining dental unit has no canonical room-facing; facing="front" read correctly from
    # every corner, and the repeated "rotate by 180 to face the operator" vote was noise
    room.place_on_center(operatory, facing="front")
    # clinical wood handwash/prep counter (cabinet + stainless sink, NO mirror -> reads clinical,
    # not bathroom) on the right wall; tall supply storage on the left
    room.place_on_right_wall_center(scene.AddAsset("a wood base cabinet with a stainless sink",
                                                   asset_id=SINK_CABINET))
    room.place_on_left_wall_center(scene.AddAsset("a tall white medical supply cabinet"))
    room.place_on_back_left_corner(station, facing="front")   # admin desk in the corner
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("left_wall", position="right")

    if PHASE >= 2:
        room.place_on_back_right_corner(scene.AddAsset("a tall potted plant in a modern planter"))

    if PHASE >= 3:
        # accent-wall decor, ceiling light, openings
        room.place_on_wall_back_center(
            scene.AddAsset("a large framed botanical green leaf print"))
        room.place_on_wall_left_left(
            scene.AddAsset("a colorful framed cartoon tooth brushing poster for kids"))
        # glass-partition entry: the whole front wall is a floor-to-ceiling glass panel (the plan's
        # glass-suite look + daylight); the actual door moves to a side wall.
        # clean mullioned glass (no curtain — parted drapes read residential and expose a black gap;
        # the bare glass partition reads as a modern clinical glass wall)
        room.place_window_floor_to_ceiling("front_wall")
        room.add_lighting("a flat rectangular LED ceiling panel light", density=0.35)

scene.export("dental_office_v1.blend")
