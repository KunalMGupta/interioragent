"""Cozy guest bedroom — "Warm Welcome Guest Room".

Brief: a double bed with a bench at its foot, a dresser, ONE reading vignette (armchair + floor
lamp + side table), art above the headboard, a standard curtained window. Soft warm palette.

Layout — the bedroom_v1 SYMMETRIC HERO + NOOK skeleton, guest-sized:
- BACK wall  : the bed HERO — matching nightstands aligned to the HEADBOARD (place_on_back_left/
               right, never the bed's sides), the bench tucked at the foot, the reading vignette
               hanging off the right flank so it reads as part of the sleep zone, not an island.
- LEFT wall  : the dresser (styled in phase 2) — a guest room's landing zone for a suitcase's
               contents.
- RIGHT wall : the window — the only wall with NO furniture, so it stays the light source.
- FRONT wall : the door (left) + a corner plant filling the dead corner.
- CENTRE     : deliberately OPEN; the rug does the grounding.

Phase-gated: phase 1 = every floor-standing object + the door; phase 2 = lamps, dresser top, rug;
phase 3 = the art above the headboard, the curtained window, the ceiling light.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BedroomGuestCozy", seed=32)

# ---- pinned assets ------------------------------------------------------------------------------
BED        = "future/df473f4d-a693-4ccd-af03-5c1cdeab00de"  # SET asset: cloth headboard + layered
                                                            # warm bedding already dressed on the
                                                            # mesh — nothing gets place_on_top'd.
                                                            # Audited 2026-07-14: the warmest of
                                                            # the top picks (its siblings are
                                                            # crisp-white hotel beds).
# The four below are bedroom_v1's AUDITED pins, reused on purpose — same roles, same traps:
DRESSER    = "hssd/d913eb66da3fa49ca0690dbf057279c4a05ccbfa"  # traditional warm dark-wood dresser
BENCH      = "hssd/448a7a6a5a63f9ec692bcc96e29cf9da999dd05e"  # carved upholstered storage bench
LAMP       = "hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed"  # the generic "table lamp" query keeps
                                                              # returning MODERN WHITE lamps; this
                                                              # is the classic urn + pleated shade
FLOOR_LAMP = "hssd/9c9f247345d354b16c65805e73d6a239ddbc28dd"
ART        = "hssd/4192b93682edc3c5585701c1ba90a34e9fd2f75b"  # the retrieved landscape painting is
                                                              # a bad mesh (empty-frame trap)

scene.prefetch_assets([
    "a modern double bed with an upholstered headboard and layered bedding",
    "a classic dark wood nightstand",
    "a carved wood upholstered storage bench",
    "a traditional dark wood dresser chest of drawers",
    "a traditional upholstered reading armchair",
    "a small round traditional wood side table",
    "a classic urn table lamp with a pleated shade",
    "a classic brass floor lamp with a beige shade",
    "a large traditional patterned area rug",
    "a decorative ceramic vase with flowers",
    "a tall potted plant in a traditional planter",
    "a framed traditional landscape painting",
    "a warm brass semi flush mount ceiling light",
])

# ---- the nightstand unit: build ONE, then DUPLICATE ---------------------------------------------
# Two separately-built nightstands run place_on_top's sizing tournament TWICE and the two lamps
# come out different sizes — on a pair whose whole job is symmetry. One unit -> one tournament.
with scene.RelativeGroup() as ns:
    ns.set_anchor(scene.AddAsset("a classic dark wood nightstand"))
    if PHASE >= 2:
        ns.place_on_top(scene.AddAsset("a classic urn table lamp with a pleated shade",
                                       asset_id=LAMP))
ns_l, ns_r = 2 * ns

# ---- the dresser, styled -------------------------------------------------------------------------
with scene.RelativeGroup() as dresser_grp:
    dresser_grp.set_anchor(scene.AddAsset("a traditional dark wood dresser chest of drawers",
                                          asset_id=DRESSER))
    if PHASE >= 2:
        dresser_grp.place_on_top([
            scene.AddAsset("a classic urn table lamp with a pleated shade", asset_id=LAMP),
            scene.AddAsset("a decorative ceramic vase with flowers"),
        ])

# ---- the reading vignette: a seat NEVER travels alone --------------------------------------------
# The armchair carries its side table and floor lamp INSIDE its own group so the three rotate as
# one piece when the nook is faced at the bed (bedroom_v1 lesson 4). The floor lamp is part of the
# vignette's identity, so it stays with the chair rather than stranded on a far wall.
with scene.RelativeGroup() as vignette:
    vignette.set_anchor(scene.AddAsset("a traditional upholstered reading armchair"))
    vignette.place_on_left(scene.AddAsset("a small round traditional wood side table"))
    vignette.place_on_back(scene.AddAsset("a classic brass floor lamp with a beige shade",
                                          asset_id=FLOOR_LAMP))

# ---- HERO: the bed arrangement --------------------------------------------------------------------
bed   = scene.AddAsset("a modern double bed with an upholstered headboard and layered bedding",
                       asset_id=BED)
bench = scene.AddAsset("a carved wood upholstered storage bench", asset_id=BENCH)
with scene.RelativeGroup() as bed_group:
    bed_group.set_anchor(bed)
    bed_group.place_on_back_left(ns_l)             # aligned to the HEADBOARD, not the bed's sides
    bed_group.place_on_back_right(ns_r)
    bed_group.place_on_front_adjacent(bench)       # the brief's bench, tucked close at the foot
    bed_group.place_on_right_further(vignette)     # the nook off the right flank
    bed_group.face(vignette, toward=bench)         # face() works on a nested GROUP
    if PHASE >= 2:
        bed_group.place_rug("a large traditional patterned area rug", size=1.0)

# modulate_scale=0.8 — a guest room must feel snug, not like a hotel lobby (bedroom_v1's dial).
with scene.RoomGroup(modulate_scale=0.8, randomness=0.1) as room:
    # soft warm palette that does NOT blow out under window daylight: warm oak + greige — the
    # proven bedroom_v1 pairing (a paler cream wall is the nursery exposure trap).
    room.place_walls(floor_texture="warm medium oak wood planks",
                     ceiling_texture="soft white",
                     wall_texture="warm greige taupe")

    # --- PHASE 1: ALL the floor mass ---
    room.place_on_back_wall_center(bed_group)
    room.place_on_left_wall_center(dresser_grp)     # dresser is ~1 m tall — safe at a wall centre
    room.place_on_front_left_corner(scene.AddAsset("a tall potted plant in a traditional planter"))
    # door in PHASE 1: its automatic clearance shapes the floor solve
    room.place_door("front_wall", position="left")

    if PHASE >= 3:
        # the brief's art ABOVE THE HEADBOARD — pre-scaled BEFORE place_on_wall_* (the mount
        # height derives from the UN-scaled height; a big canvas clips the ceiling).
        art = scene.AddAsset("a framed traditional landscape painting", asset_id=ART)
        art.scale_only_width(1.1); art.scale_only_height(0.75); art.scale_only_depth(0.04)
        room.place_on_wall_back_center(art)
        # standard window + curtain on the furniture-free right wall
        room.place_window_standard("right_wall", position="center",
                                   curtain="floor length linen curtains")
        # ONE warm flush fixture; 0.012 for a small bedroom (0.02+ starfields)
        room.add_lighting("a warm brass semi flush mount ceiling light", density=0.012)

scene.export("br_guest_cozy.blend")
