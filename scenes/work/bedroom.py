"""
Bedroom — "Warm Traditional Master Suite" (planner-driven).

Design brief (planner): the bed is the central focal anchor on the main wall with a substantial
headboard and SYMMETRY — identical nightstands + table lamps, a bench at the foot, a classic wood
dresser with a framed mirror nearby, and a cozy armchair reading nook. A large patterned rug grounds
the sleep zone; floor-length curtains; layered warm lighting; framed art. Palette: creams, taupes,
soft golds and rich warm wood, with muted-burgundy accents. Refined, cozy, timeless.

Coarse-to-fine (skills/workflow/coarse_to_fine.md):
  Phase 1 — bed HERO group (symmetric nightstands at the headboard, foot bench, reading chair off the
    right side facing the bench, grounding rug, ceiling light); dresser on the left wall.
  Phase 2 — surface/floor: matching table lamps on the nightstands, a styled dresser top, a floor
    lamp by the chair, a corner plant.
  Phase 3 — walls/openings: art over the bed, a mirror over the dresser, a curtained window, a door.

Beds are "set assets" — the mesh comes fully DRESSED, so we pin a good traditional bed and DON'T add
separate bedding. (place_on_top runs the full VLM-tournament smart placement — it is core DSL
behaviour and must NOT be disabled for speed.)
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("BedroomMaster", seed=41)

scene.prefetch_assets([
    "a traditional dark wood panel bed with bedding",
    "a classic dark wood nightstand",
    "a carved wood upholstered storage bench",
    "a traditional dark wood dresser chest of drawers",
    "a traditional upholstered reading armchair",
    "a large traditional patterned area rug",
    "a brass semi-flush ceiling light",
    "a traditional brass table lamp with a cream pleated shade",
    "a traditional brass floor lamp with a cream shade",
    "a decorative ceramic vase with flowers",
    "a tall potted plant in a traditional planter",
    "a large framed traditional landscape painting",
    "a framed wall mirror",
])

# --- Phase 1 majors (beds carry real-world scale, no override needed) ---
bed = scene.AddAsset("a traditional dark wood panel bed with bedding",
                     asset_id="hssd/298cd407f13b1d4b9121440bba198d34b43b46b0")
nightstand = scene.AddAsset("a classic dark wood nightstand",
                            asset_id="hssd/830e2ed47548d8372294609fe7eeca11fb384b29")
bench   = scene.AddAsset("a carved wood upholstered storage bench",
                         asset_id="hssd/448a7a6a5a63f9ec692bcc96e29cf9da999dd05e")
dresser = scene.AddAsset("a traditional dark wood dresser chest of drawers",
                         asset_id="hssd/d913eb66da3fa49ca0690dbf057279c4a05ccbfa")
armchair = scene.AddAsset("a traditional upholstered reading armchair")

# --- Phase 2 surface pieces. Pin a classic urn-base lamp with a pleated shade (the generic query
# kept returning modern white lamps; this matches the traditional reference). ---
_LAMP = "hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed"
lamp = scene.AddAsset("a classic urn table lamp with a pleated shade", asset_id=_LAMP)
dresser_lamp = scene.AddAsset("a classic urn table lamp with a pleated shade", asset_id=_LAMP)
floor_lamp = scene.AddAsset("a classic brass floor lamp with a beige shade",
                            asset_id="hssd/9c9f247345d354b16c65805e73d6a239ddbc28dd")
plant = scene.AddAsset("a tall potted plant in a traditional planter")
side_table = scene.AddAsset("a small round traditional wood side table")
# Art over the bed: pin a clean landscape (the prior pick was a bad mesh) and pre-scale it to a
# moderate size — place_on_wall_* derives the mount height from the (un-scaled) art height, so a
# large painting lands too high and punches through the ceiling.
art = scene.AddAsset("a framed traditional landscape painting",
                     asset_id="hssd/4192b93682edc3c5585701c1ba90a34e9fd2f75b")
art.scale_only_width(1.1); art.scale_only_height(0.75); art.scale_only_depth(0.04)

# Build ONE nightstand+lamp unit, then DUPLICATE it (2 * ns) so the pair is identical. Building the
# two individually runs place_on_top's sizing tournament twice -> the lamps come out different sizes.
with scene.RelativeGroup() as ns:
    ns.set_anchor(nightstand)
    ns.place_on_top(lamp)
ns_l, ns_r = 2 * ns

# dresser styled with a lamp + a vase
with scene.RelativeGroup() as dresser_grp:
    dresser_grp.set_anchor(dresser)
    dresser_grp.place_on_top([dresser_lamp, scene.AddAsset("a decorative ceramic vase with flowers")])

# reading chair as its OWN group — a seat always gets a small table in its vicinity, and the floor
# lamp belongs to the chair (not stranded in a corner). They travel together when placed/rotated.
with scene.RelativeGroup() as chair_group:
    chair_group.set_anchor(armchair)
    chair_group.place_on_left(side_table)           # small accent table beside the chair
    chair_group.place_on_back(floor_lamp)           # reading floor lamp behind the chair

# --- HERO: the bed arrangement ---
with scene.RelativeGroup() as bed_group:
    bed_group.set_anchor(bed)
    bed_group.place_on_back_left(ns_l)              # nightstands aligned to the headboard
    bed_group.place_on_back_right(ns_r)
    bed_group.place_on_front_adjacent(bench)        # bench tucked close at the foot
    bed_group.place_on_right_further(chair_group)   # reading nook off the right side of the bed
    bed_group.face(chair_group, toward=bench)       # angle the nook toward the foot bench
    bed_group.place_rug("a large traditional patterned area rug", size=1.0)
    bed_group.add_lighting("a brass semi-flush ceiling light", density=0)

with scene.RoomGroup(modulate_scale=0.8, randomness=0.1) as room:
    # warm wood floor + soft greige walls: cozy traditional warmth without blowing out under daylight
    room.place_walls(floor_texture="warm medium oak wood planks",
                     ceiling_texture="soft white", wall_texture="warm greige taupe")
    # Phase 1 — hero bed (with its reading nook); dresser on the left wall
    room.place_on_back_wall_center(bed_group)
    room.place_on_left_wall_center(dresser_grp)
    # Phase 2 — a plant in a corner (the floor lamp now lives with the reading chair)
    room.place_on_front_left_corner(plant)
    # Phase 3 — art over the bed, a mirror over the dresser, a curtained window + a door
    room.place_on_wall_back_center(art)
    room.place_on_wall_left_center(scene.AddAsset("a framed wall mirror"))
    room.place_window_standard("right_wall", position="center", curtain="floor length linen curtains")
    room.place_door("front_wall", position="left")

scene.export("bedroom.blend")
