"""Bedroom — "Warm Traditional Master Suite" (planner-driven).

Planner target: the bed is the central focal anchor on the main wall with a substantial headboard
and SYMMETRY — identical nightstands + table lamps, a bench at the foot, a classic wood dresser
with a framed mirror nearby, and a cozy armchair reading nook. A large patterned rug grounds the
sleep zone; floor-length curtains; layered warm lighting; framed art. Palette: creams, taupes, soft
golds, rich warm wood, muted-burgundy accents. Refined, cozy, timeless.

Layout — SYMMETRIC HERO + a self-contained NOOK (the core residential pattern):
- BACK wall  : the bed HERO. Nightstands aligned to the HEADBOARD (place_on_back_left/right, not
               the bed's sides); storage bench tucked at the foot (place_on_front_adjacent);
               the reading nook pushed off the right flank (place_on_right_further).
- LEFT wall  : the dresser, styled, with a mirror mounted above it.
- RIGHT wall : the window (curtained) — the only wall with no furniture, so it stays the light source.
- FRONT wall : the door, left. A corner plant fills the remaining dead corner.
- CENTRE     : deliberately OPEN. A bedroom reads intimate, not busy; the rug does the grounding.

Identity comes from the bed being a SET asset — the mesh ships fully DRESSED (bedding, pillows), so
nothing is place_on_top'd onto it. modulate_scale=0.8 keeps the suite cozy: a master bedroom that
solves to a cavernous shell reads like a hotel lobby.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/bedroom_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 dresses the surfaces; phase 3 adds walls decor/window/lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BedroomMaster", seed=41)

# ---- pinned assets (gate-3 audit: every mesh eyeballed on a contact sheet) --------------------
BED       = "hssd/298cd407f13b1d4b9121440bba198d34b43b46b0"  # SET asset — ships with its bedding
NIGHTSTAND= "hssd/830e2ed47548d8372294609fe7eeca11fb384b29"
BENCH     = "hssd/448a7a6a5a63f9ec692bcc96e29cf9da999dd05e"
DRESSER   = "hssd/d913eb66da3fa49ca0690dbf057279c4a05ccbfa"
LAMP      = "hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed"  # the generic "table lamp" query kept
                                                             # returning MODERN WHITE lamps; this is
                                                             # the classic urn base + pleated shade
FLOOR_LAMP= "hssd/9c9f247345d354b16c65805e73d6a239ddbc28dd"
ART       = "hssd/4192b93682edc3c5585701c1ba90a34e9fd2f75b"  # the retrieved landscape was a bad mesh

scene.prefetch_assets([
    "a traditional dark wood panel bed with bedding",
    "a classic dark wood nightstand",
    "a carved wood upholstered storage bench",
    "a traditional dark wood dresser chest of drawers",
    "a traditional upholstered reading armchair",
    "a small round traditional wood side table",
    "a large traditional patterned area rug",
])

# ---- the nightstand unit: build ONE, then DUPLICATE it ----------------------------------------
# Building the two nightstands separately runs place_on_top's sizing tournament TWICE, so the two
# lamps come out DIFFERENT SIZES. One unit -> one tournament -> an identical pair.
with scene.RelativeGroup() as ns:
    ns.set_anchor(scene.AddAsset("a classic dark wood nightstand", asset_id=NIGHTSTAND))
    if PHASE >= 2:
        ns.place_on_top(scene.AddAsset("a classic urn table lamp with a pleated shade",
                                       asset_id=LAMP))
ns_l, ns_r = 2 * ns

# ---- the dresser, styled --------------------------------------------------------------------
with scene.RelativeGroup() as dresser_grp:
    dresser_grp.set_anchor(scene.AddAsset("a traditional dark wood dresser chest of drawers",
                                          asset_id=DRESSER))
    if PHASE >= 2:
        dresser_grp.place_on_top([
            scene.AddAsset("a classic urn table lamp with a pleated shade", asset_id=LAMP),
            scene.AddAsset("a decorative ceramic vase with flowers"),
        ])

# ---- the reading nook: a seat NEVER travels alone --------------------------------------------
# The chair carries its own side table and its own floor lamp INSIDE its group, so the lamp is not
# stranded in a corner and the three rotate together when the nook is faced at the bench.
with scene.RelativeGroup() as chair_group:
    chair_group.set_anchor(scene.AddAsset("a traditional upholstered reading armchair"))
    chair_group.place_on_left(scene.AddAsset("a small round traditional wood side table"))
    if PHASE >= 2:
        chair_group.place_on_back(scene.AddAsset("a classic brass floor lamp with a beige shade",
                                                 asset_id=FLOOR_LAMP))

# ---- HERO: the bed arrangement ---------------------------------------------------------------
bed   = scene.AddAsset("a traditional dark wood panel bed with bedding", asset_id=BED)
bench = scene.AddAsset("a carved wood upholstered storage bench", asset_id=BENCH)
with scene.RelativeGroup() as bed_group:
    bed_group.set_anchor(bed)
    bed_group.place_on_back_left(ns_l)             # aligned to the HEADBOARD, not the bed's sides
    bed_group.place_on_back_right(ns_r)
    bed_group.place_on_front_adjacent(bench)       # tucked close at the foot
    bed_group.place_on_right_further(chair_group)  # the nook sits off the right flank
    bed_group.face(chair_group, toward=bench)      # face() works on a nested GROUP, not just a leaf
    if PHASE >= 2:
        bed_group.place_rug("a large traditional patterned area rug", size=1.0)
    if PHASE >= 3:
        bed_group.add_lighting("a brass semi-flush ceiling light", density=0)

with scene.RoomGroup(modulate_scale=0.8, randomness=0.1) as room:
    # warm oak + soft greige: cozy traditional warmth that does not blow out under daylight
    room.place_walls(floor_texture="warm medium oak wood planks",
                     ceiling_texture="soft white", wall_texture="warm greige taupe")
    room.place_on_back_wall_center(bed_group)
    room.place_on_left_wall_center(dresser_grp)
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="left")

    if PHASE >= 2:
        room.place_on_front_left_corner(scene.AddAsset("a tall potted plant in a traditional planter"))

    if PHASE >= 3:
        # PRE-SCALE the art BEFORE place_on_wall_*: the mount height is derived from the art's
        # UN-scaled height, so a large painting is mounted too high and punches through the ceiling.
        art = scene.AddAsset("a framed traditional landscape painting", asset_id=ART)
        art.scale_only_width(1.1); art.scale_only_height(0.75); art.scale_only_depth(0.04)
        room.place_on_wall_back_center(art)
        room.place_on_wall_left_center(scene.AddAsset("a framed wall mirror"))
        room.place_window_standard("right_wall", position="center",
                                   curtain="floor length linen curtains")

scene.export("bedroom_v1.blend")
