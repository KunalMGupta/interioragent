"""
Dental office — "Cheerful Pediatric Operatory".

Built coarse-to-fine (see skills/workflow/coarse_to_fine.md + skills/examples/dental_office.md).
Palette: soft-white walls, warm-wood cabinetry, light blue-grey vinyl tile; the orange
pediatric chair is the single pop of colour. A green botanical accent + a kids' poster
give the room its child-friendly, calm-clinical read.

The hero is an INGESTED complete pediatric dental UNIT (custom/64a7f627...): one mesh that
supplies the reclining chair + overhead exam light arm + articulated patient monitor +
delivery/instrument tray + cuspidor — the whole operatory in a single asset. The dataset
has no true dental chair (only a blue phlebotomy exam chair), so this asset was the crux;
see the example file. Everything else is dataset retrieval.

  Phase 1 — major floor assets: the dental unit (+ dentist saddle stool) as the central
    operatory group; a wood clinical sink/prep counter on one wall, a tall supply cabinet on the other.
  Phase 2 — details: a mobile assistant instrument cart at the foot of the chair; a corner plant;
    a back-left-corner admin workstation (reusable WorkstationGroup).
  Phase 3 — decor/openings: clinical LED ceiling panels; a botanical accent print on the
    patient-facing back wall; a colourful kids' poster; a floor-to-ceiling GLASS front wall
    (the plan's glass-partition suite) + a side entry door.
"""
from IDSDL.scene import SceneProgRoom

# Ingested complete pediatric dental unit (chair + light + delivery + monitor + cuspidor).
DENTAL_UNIT = "custom/64a7f627dc9e7a246ebfef4bc10fb15c27be636f"
FLAT_DESK = "hssd/a42e2ef37ca205ecb1927bde89c6b618ddcda71b"   # simple flat 0.72 m office desk
SINK_CABINET = "hssd/048d80c36ddc6ac63785ca08ccf231431195717c"  # wood cabinet + stainless sink, NO mirror

scene = SceneProgRoom("DentalOffice", seed=35)

# --- admin/charting workstation for the back-left corner (reusable WorkstationGroup + the
#     DesktopWorkstationRetriever supplies the on-top computer/lamp/accessories) ---
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a simple flat wooden office desk", asset_id=FLAT_DESK))
    station.place_chair(scene.AddAsset("an ergonomic office chair"))
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
    room.place_on_center(operatory, facing="front")
    # clinical wood handwash/prep counter (cabinet + stainless sink, NO mirror -> reads clinical,
    # not bathroom) on the right wall; tall supply storage on the left
    room.place_on_right_wall_center(scene.AddAsset("a wood base cabinet with a stainless sink",
                                                   asset_id=SINK_CABINET))
    room.place_on_left_wall_center(scene.AddAsset("a tall white medical supply cabinet"))
    room.place_on_back_right_corner(scene.AddAsset("a tall potted plant in a modern planter"))
    room.place_on_back_left_corner(station, facing="front")   # admin desk in the corner

    # ceiling light, accent-wall decor, openings
    room.add_lighting("a flat rectangular LED ceiling panel light", density=0.35)
    room.place_on_wall_back_center(scene.AddAsset("a large framed botanical green leaf print"))
    room.place_on_wall_left_left(scene.AddAsset("a colorful framed cartoon tooth brushing poster for kids"))
    # glass-partition entry: the whole front wall is a floor-to-ceiling glass panel (the plan's
    # glass-suite look + daylight); the actual door moves to a side wall.
    # clean mullioned glass (no curtain — parted drapes read residential and expose a black gap;
    # the bare glass partition reads as a modern clinical glass wall)
    room.place_window_floor_to_ceiling("front_wall")
    room.place_door("left_wall", position="right")

scene.export("dental_office.blend")
