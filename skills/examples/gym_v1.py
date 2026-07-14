"""Gym — "Big-Box Fitness Floor" (Planet-Fitness scale), zoned properly.

Planner target: a large commercial health club that reads as a *club*, not a room with machines
in it — black rubber floor + green functional turf, exposed grey industrial ceiling, warm-white
plaster walls, one FULL mirrored wall, floor-to-ceiling glass on the opposite wall, and a staffed
reception at the entrance. Palette: black / grey / warm white, navy + gold branding.

LESSON this scene encodes: a big gym is a set of FUNCTIONAL ZONES. Decide where each zone goes
FIRST, then fill it — don't scatter machines. And people want a view while they train, so the
cardio run lines the glass wall facing out.

Layout — LARGE PERIMETER MULTI-ZONE (glass = RIGHT wall, mirror = LEFT wall). Each wall gets a
zone, and the zone dictates what the wall is:
- RIGHT wall : GLASS + the CARDIO run. A 2-row grid of 8 treadmills (nearest the glass) and 8
               ellipticals behind them, all facing OUT. Cardio is the longest-dwell, most boring
               activity in the building, so it gets the only view. The wall is glazed BECAUSE the
               cardio is there, not the other way round.
- LEFT wall  : MIRROR + the WEIGHT-TRAINING zone (machine bank + free weights). Lifters check
               form, so the free weights get the full-wall mirror. Machines and free weights are
               kept TOGETHER on and beside this wall — splitting them scatters the floor.
- BACK wall  : the SPIN studio — bikes in a 3x2 grid facing into the room. A grid, not a row:
               spin is the one zone that is naturally a block of identical units.
- CENTRE     : the FUNCTIONAL turf. The middle of a gym floor must stay OPEN (mat work, ropes,
               boxes), so the centre gets the cheapest, lowest, most rearrangeable zone.
- FRONT wall : ENTRY. Reception desk (left, backed to the wall, facing INTO the room), massage
               lounge beside it, amenities in the corner, lockers + brand art + the door.

Identity comes from the ZONING and the two opposing long walls — a real reflective mirror wall
facing bare floor-to-ceiling glass. Strip the equipment out and the shell still reads "gym".
Room height is allowed to grow to 4 m (RoomGroup(max_height=4.0)) so the tall racks/machines
don't get clipped and the wall decor above the lockers has headroom.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/gym_v1.py --phase 1` builds only
the floor layout — every zone, every clearance aisle, the mirror-vs-glass shell (~1-2 min, and
the layout is the whole point of this scene); phase 2 dresses the functional turf and the
reception plant; phase 3 adds the mirror wall, the glazing, the wall decor and the lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("GymMega", seed=21)


def _fit_height(obj, target_h):
    """Uniformly scale obj so its height == target_h (m). Small props can get a bad
    description-driven scale even when pinned, so pin the real size explicitly."""
    w, h, d = (float(v) for v in obj.get_whd())
    if h > 1e-6:
        f = target_h / h
        obj.scale_only_width(w * f)
        obj.scale_only_height(h * f)
        obj.scale_only_depth(d * f)
    return obj


# ---- pinned assets (gate-3 audit: every mesh eyeballed on a contact sheet; the audit table
#      lives in scenes/work/gym.md — verdicts were made from the preview PNG, not similarity) ----
# --- cardio ---
TREADMILL  = "hssd/fdd91608c418ead483b7a0bbd78a82a6306f36d0"  # black treadmill, LED console (audited GOOD)
ELLIPTICAL = "future/1f79b924-dc7c-427e-aaf8-eef7974ad805"    # elliptical cross-trainer — the pool's
                                                              # only credible one; also the stand-in
                                                              # for the MISSING rowing ergometer
BIKE       = "hssd/b3ef9e90aaafb14f946e6c716f36eba419fa76a7"  # upright stationary bike
# --- machines (the selectorized bank) ---
LAT        = "future/96bb6aab-d17f-4cf2-821a-fc29cd0545d2"    # lat pulldown WITH a weight stack —
                                                              # the generic query returns bare frames
PEC        = "hssd/5406441590ae50f71a4d5a65d7a427761713e647"  # chest/pec multi-gym
AB         = "hssd/b16e1cc9c69bef43c81087e0c7d4ae7cee2acec4"  # ab-crunch machine
CABLE      = "hssd/ac2b117a76e842cf7e2af1dd16d0a88d01e78c41"  # cable tower / functional trainer
SEATED_ROW = "hssd/f87c00e6e729f39bc0a6cf8a7762489dd147f4a9"  # seated row (no audit note recorded)
INCLINE    = "hssd/1fa8df7c61ca18ca75b7a8a795048340f91d56db"  # incline bench press — also the
                                                              # stand-in for the MISSING Smith machine
# --- free weights ---
POWERRACK  = "hssd/b46437ac19972f7c42291bbdc7a45a549297fce6"  # squat rack w/ barbell — also the
                                                              # stand-in for the MISSING leg press
DBRACK     = "hssd/f7109eaad4235fd4db456ca184f9f458a3611421"  # dumbbell rack, two rows (audited GOOD)
PLATETREE  = "hssd/fb93338620659f63363044463164f29680667a7a"  # loaded vertical plate tree
BENCH      = "hssd/0391f7b149076276d028060971ae3d197619f196"  # flat weight bench (audited GOOD, sim 0.752)
# --- functional ---
PLYO       = "hssd/2f2b6ebda280d38ed6c9bfcec919f6308ab17f27"  # black plyo box
KETTLE     = "hssd/c3bb69cc0d810d1d784e523f38de24fef5f1c244"  # black cast-iron kettlebell
MEDBALL    = "hssd/33adf260d1a6f88f0d5b7bd017a6182f815d715c"  # rubber medicine ball
SANDBAG    = "hssd/b98b86e3d373233c18f0f9c2b00119d220db8059"  # training sandbag — the stand-in for
                                                              # the MISSING battle rope
# --- reception / amenities / decor ---
DESK       = "hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860"  # curved reception front desk. NOTE:
                                                              # grocery_store_v1 measured this mesh at
                                                              # 0.60 m and rejected it as a CHECKOUT
                                                              # counter; as a low reception desk it is
                                                              # the right shape, and it is what
                                                              # bookstore/library pin too.
MASSAGE    = "hssd/e129e1f4da860f37471cf8395a8e92253a532ed2"  # black leather massage recliner
COOLER     = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"  # water cooler — description-driven scale
                                                              # once rendered it ~2.4 m tall, so its
                                                              # height is pinned with _fit_height below
TRASH      = "hssd/141dd97fde5601e6c4fb47e9e08b4b489686a500"  # cylindrical trash can (same trap)
LOCKERS    = "future/902f9b5b-72ce-4fb7-a870-4f8ec97a3a2d"    # black 3-door locker bank
ART        = "future/9c5ac3d9-107f-49da-ae76-be9eb2c6de32"    # navy + gold geometric feature art — the
                                                              # branded/neon gym signage queries are WEAK,
                                                              # so the brand wall is carried by abstract art

# ============================ CARDIO run (glass wall) ============================
# 8 treadmills nearest the glass + 8 ellipticals in the row behind -> a 2-row grid, cols=8.
# The SECOND grid row lands against the wall, so ellipticals go first and treadmills second
# (treadmills end up on the glass, where the view matters most while running).
cardio_units = (
    8 * scene.AddAsset("an elliptical cross-trainer cardio machine", asset_id=ELLIPTICAL)
    + 8 * scene.AddAsset("a treadmill exercise machine", asset_id=TREADMILL)
)
with scene.GridGroup(sparsity=0.4, randomness=0.08) as cardio:
    cardio.place_grid(cardio_units, cols=8)

# SPIN studio: bikes in a 3x2 grid against the back wall
bikes_units = 6 * scene.AddAsset("an upright stationary exercise bike", asset_id=BIKE)
with scene.GridGroup(sparsity=0.45, randomness=0.08) as bikes:
    bikes.place_grid(bikes_units, cols=3)

# ============================ WEIGHT-TRAINING zone ============================
# machine bank: 2 rows x 3 selectorized machines
machine_units = [
    scene.AddAsset("a lat pulldown weight machine", asset_id=LAT),
    scene.AddAsset("a seated chest press pec deck machine", asset_id=PEC),
    scene.AddAsset("an abdominal crunch weight machine", asset_id=AB),
    scene.AddAsset("a functional trainer cable machine", asset_id=CABLE),
    scene.AddAsset("a seated row weight machine", asset_id=SEATED_ROW),
    scene.AddAsset("an incline bench press machine", asset_id=INCLINE),
]
with scene.GridGroup(sparsity=0.5, randomness=0.08) as machines:
    machines.place_grid(machine_units, cols=3)

# free-weight benches (in front of the mirror wall)
benches = 2 * scene.AddAsset("a flat weight training bench", asset_id=BENCH)
with scene.RelativeGroup() as benches_grp:
    benches_grp.set_anchor(benches[0])
    benches_grp.place_on_right(benches[1])

# ============================ FUNCTIONAL turf (centre) ============================
# The plyo box is the only PHASE-1 anchor here: the turf zone is deliberately the cheapest zone
# on the floor, and its kettlebells / medicine balls / sandbag / turf are floor DRESSING (phase 2).
with scene.RelativeGroup() as functional:
    functional.set_anchor(scene.AddAsset("a black plyometric jump box", asset_id=PLYO))
    if PHASE >= 2:
        kettles = 2 * scene.AddAsset("a cast iron kettlebell weight", asset_id=KETTLE)
        medballs = 2 * scene.AddAsset("a rubber medicine ball", asset_id=MEDBALL)
        functional.place_on_left(kettles[0])
        functional.place_on_back_left(kettles[1])
        functional.place_on_right(medballs[0])
        functional.place_on_back_right(medballs[1])
        functional.place_on_front(scene.AddAsset("a heavy training sandbag", asset_id=SANDBAG))
        functional.place_rug("bright green artificial turf with white line markings", size=1.8)

# ============================ RECEPTION (desk backed to wall, facing in) ============================
reception_desk = scene.AddAsset("a modern curved reception front desk", asset_id=DESK)
with scene.RelativeGroup() as reception:
    reception.set_anchor(reception_desk)
    reception.place_on_back(scene.AddAsset("an ergonomic office chair"))   # staff behind, toward wall
    if PHASE >= 2:
        reception.place_on_right(_fit_height(scene.AddAsset("a tall potted plant"), 1.4))

# MASSAGE lounge: a pair of recliners by the reception (its own zone, not the reception group)
massage_pair = 2 * scene.AddAsset("a black leather massage recliner chair", asset_id=MASSAGE)
with scene.GridGroup(sparsity=0.5, randomness=0.08) as massage:
    massage.place_row(massage_pair)

# AMENITIES: water cooler + trash tucked in a corner. Both are pinned to their REAL height:
# AddAsset derives scale from the DESCRIPTION TEXT, and an unlucky phrasing once rendered the
# cooler ~2.4 m tall even though the id was pinned.
with scene.RelativeGroup() as amenities:
    amenities.set_anchor(_fit_height(scene.AddAsset("a freestanding water cooler dispenser", asset_id=COOLER), 1.1))
    amenities.place_on_right(_fit_height(scene.AddAsset("a tall cylindrical trash can", asset_id=TRASH), 0.6))

# ============================ ROOM ============================
# max_height=4.0: HEIGHT is normally CLAMPED to 3.0 m, and a 2.2 m power rack (plus a clock hung
# above a locker bank) then clips the ceiling. With max_height the ceiling grows with the tallest
# FLOOR object, clamped to [3.0, 4.0]; _warn_over_height still flags anything that pokes through.
with scene.RoomGroup(modulate_scale=0.9, randomness=0.1, max_height=4.0) as room:
    room.place_walls(floor_texture="black rubber gym flooring",
                     ceiling_texture="exposed grey industrial ceiling",
                     wall_texture="warm white plaster")

    # RIGHT (glass) wall = cardio run, facing the view
    room.place_on_right(cardio, facing="right")

    # BACK wall (right side) = spin studio, facing into the room
    room.place_on_back_right(bikes, facing="front")

    # LEFT (mirror) wall + back-left = weight-training zone (kept together)
    room.place_on_back_left(machines, facing="front")
    room.place_on_left_wall_left(scene.AddAsset("a squat rack with a barbell", asset_id=POWERRACK))
    room.place_on_left_wall_center(scene.AddAsset("a weight rack with dumbbells", asset_id=DBRACK))
    room.place_on_left_wall_right(scene.AddAsset("a loaded weight plate tree", asset_id=PLATETREE))
    room.place_on_left(benches_grp, facing="left")

    # CENTRE = functional turf
    room.place_on_center(functional)

    # FRONT = reception (left) + massage lounge (centre); amenities in the front-right corner
    room.place_on_front_left(reception, facing="back")
    room.place_on_front(massage, facing="back")
    room.place_on_front_right_corner(amenities, facing="back")

    # FRONT wall = entry + storage. The door stays in PHASE 1: its automatic clearance shapes the
    # floor solve, so deferring it would change the layout you validated.
    room.place_door("front_wall", position="right")
    lockers = scene.AddAsset("a row of gym lockers", asset_id=LOCKERS)
    room.place_on_front_wall_left(lockers)

    # ---- clearances (circulation aisles + usable space around equipment) ----
    # NOTE: clearance targets individual placed objects (the raytracer works on leaf objects,
    # not group wrappers). Applying a row's clearance to each of its machines gives the same
    # row-level aisles: front_back on every treadmill/elliptical -> a clear strip at the glass,
    # between the two rows, and behind the run.
    for _c in cardio_units:
        room.add_clearance(_c, distance=0.5, dir="front_back")
    # spin studio: space on all sides of each bike -> a clear border around the grid
    for _b in bikes_units:
        room.add_clearance(_b, distance=0.4, dir="all")
    # each strength machine: room to enter/exit and stand at the stack -> front + both sides
    for _m in machine_units:
        room.add_clearance(_m, distance=0.55, dir="front_sides")
    # reception: a clear approach in front and to the sides of the desk (the DESK leaf, not the
    # reception group -- a group wrapper throws KeyError)
    room.add_clearance(reception_desk, distance=0.8, dir="front_sides")
    # lockers ("wardrobe"): changing space in front
    room.add_clearance(lockers, distance=0.8, dir="front")

    if PHASE >= 3:
        # The two long walls, opposed. A TRUE full-wall mirror (IDSDL/mirror.py: a thin metallic /
        # ~0 roughness PBR panel -> a real Cycles reflection), NOT a retrieved mirror prop and NOT
        # tiled with place_on_wall_freeform (that path sizes flat objects by their DEPTH and
        # collapses a 5 cm mirror to nothing on a side wall). It claims all three slots of the
        # wall, so nothing else is mounted on the left wall.
        room.place_mirror_full_wall("left_wall")
        # ...and bare floor-to-ceiling glass opposite (no curtain= -> real glass; curtains would
        # hide the view the whole cardio run is pointed at).
        room.place_window_floor_to_ceiling("right_wall")

        # brand wall above the lockers; the clock goes on the BACK wall (above the spin studio)
        # because the front wall's 'right' slot is the door's.
        room.place_on_wall_front_center(scene.AddAsset("a large abstract geometric wall art in navy and gold",
                                                       asset_id=ART))
        room.place_on_wall_back_center(scene.AddAsset("a large modern wall clock"))

        # lighting: linear industrial ceiling runs (LOW density -- N = 1 + (max-1)*density, and a
        # huge ceiling swarms with fixtures otherwise)
        room.add_lighting("a row of bright industrial linear ceiling lights", density=0.008)

scene.export("gym_v1.blend")
