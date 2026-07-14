"""
Mega health club — "Big-Box Fitness Floor" (Planet-Fitness scale), zoned properly.

LESSON this scene encodes: a big gym is a set of FUNCTIONAL ZONES. Decide where each zone goes
first, then fill it -- don't scatter machines. And people want a view while they train, so the
cardio run lines the glass wall facing out.

Zone map (glass = RIGHT wall, mirror = LEFT wall):
  - RIGHT wall (glass) = CARDIO run: a row of 8 treadmills against the glass facing the view, with
    a row of 8 ellipticals directly behind them (also facing out).
  - BACK wall           = SPIN studio: bikes in a 3x2 grid.
  - LEFT wall + back-left = WEIGHT-TRAINING zone (kept together): a 2-row machine bank + the free
    weights (power rack, dumbbell rack, plate tree, benches) along the mirrored wall.
  - CENTRE              = FUNCTIONAL turf: plyo box, kettlebells, medicine balls, sandbag.
  - FRONT-LEFT          = RECEPTION: curved desk backed against the wall, facing INTO the room.
  - FRONT-centre        = MASSAGE lounge: a row of massage recliners by the reception (own zone).
  - FRONT-right corner  = AMENITIES: water cooler + trash bin tucked in the corner.
  - FRONT wall          = entry door, lockers, brand art, clock.

Room height is allowed to grow to 4 m (RoomGroup(max_height=4.0)) so the tall racks/machines don't
get clipped and wall decor has headroom.
"""
from IDSDL.scene import SceneProgRoom

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


# --- cardio ---
_TREADMILL  = "hssd/fdd91608c418ead483b7a0bbd78a82a6306f36d0"
_ELLIPTICAL = "future/1f79b924-dc7c-427e-aaf8-eef7974ad805"
_BIKE       = "hssd/b3ef9e90aaafb14f946e6c716f36eba419fa76a7"
# --- machines ---
_LAT     = "future/96bb6aab-d17f-4cf2-821a-fc29cd0545d2"
_PEC     = "hssd/5406441590ae50f71a4d5a65d7a427761713e647"
_AB      = "hssd/b16e1cc9c69bef43c81087e0c7d4ae7cee2acec4"
_CABLE   = "hssd/ac2b117a76e842cf7e2af1dd16d0a88d01e78c41"
_LATMACH = "hssd/f87c00e6e729f39bc0a6cf8a7762489dd147f4a9"
_INCLINE = "hssd/1fa8df7c61ca18ca75b7a8a795048340f91d56db"
# --- free weights ---
_POWERRACK = "hssd/b46437ac19972f7c42291bbdc7a45a549297fce6"
_DBRACK    = "hssd/f7109eaad4235fd4db456ca184f9f458a3611421"
_PLATETREE = "hssd/fb93338620659f63363044463164f29680667a7a"
_BENCH     = "hssd/0391f7b149076276d028060971ae3d197619f196"
# --- functional ---
_PLYO    = "hssd/2f2b6ebda280d38ed6c9bfcec919f6308ab17f27"
_KETTLE  = "hssd/c3bb69cc0d810d1d784e523f38de24fef5f1c244"
_MEDBALL = "hssd/33adf260d1a6f88f0d5b7bd017a6182f815d715c"
_SANDBAG = "hssd/b98b86e3d373233c18f0f9c2b00119d220db8059"
# --- reception / amenities / decor ---
_DESK    = "hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860"
_MASSAGE = "hssd/e129e1f4da860f37471cf8395a8e92253a532ed2"
_COOLER  = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"
_TRASH   = "hssd/141dd97fde5601e6c4fb47e9e08b4b489686a500"
_LOCKERS = "future/902f9b5b-72ce-4fb7-a870-4f8ec97a3a2d"
_ART     = "future/9c5ac3d9-107f-49da-ae76-be9eb2c6de32"

# ============================ CARDIO run (glass wall) ============================
# 8 treadmills nearest the glass + 8 ellipticals in the row behind -> a 2-row grid, cols=8.
# The SECOND grid row lands against the wall, so ellipticals go first and treadmills second
# (treadmills end up on the glass, where the view matters most while running).
cardio_units = (
    8 * scene.AddAsset("an elliptical cross-trainer cardio machine", asset_id=_ELLIPTICAL)
    + 8 * scene.AddAsset("a treadmill exercise machine", asset_id=_TREADMILL)
)
with scene.GridGroup(sparsity=0.4, randomness=0.08) as cardio:
    cardio.place_grid(cardio_units, cols=8)

# SPIN studio: bikes in a 3x2 grid against the back wall
bikes_units = 6 * scene.AddAsset("an upright stationary exercise bike", asset_id=_BIKE)
with scene.GridGroup(sparsity=0.45, randomness=0.08) as bikes:
    bikes.place_grid(bikes_units, cols=3)

# ============================ WEIGHT-TRAINING zone ============================
# machine bank: 2 rows x 3 selectorized machines
machine_units = [
    scene.AddAsset("a lat pulldown weight machine", asset_id=_LAT),
    scene.AddAsset("a seated chest press pec deck machine", asset_id=_PEC),
    scene.AddAsset("an abdominal crunch weight machine", asset_id=_AB),
    scene.AddAsset("a functional trainer cable machine", asset_id=_CABLE),
    scene.AddAsset("a seated row weight machine", asset_id=_LATMACH),
    scene.AddAsset("an incline bench press machine", asset_id=_INCLINE),
]
with scene.GridGroup(sparsity=0.5, randomness=0.08) as machines:
    machines.place_grid(machine_units, cols=3)

# free-weight benches (in front of the mirror wall)
benches = 2 * scene.AddAsset("a flat weight training bench", asset_id=_BENCH)
with scene.RelativeGroup() as benches_grp:
    benches_grp.set_anchor(benches[0])
    benches_grp.place_on_right(benches[1])

# ============================ FUNCTIONAL turf (centre) ============================
kettles = 2 * scene.AddAsset("a cast iron kettlebell weight", asset_id=_KETTLE)
medballs = 2 * scene.AddAsset("a rubber medicine ball", asset_id=_MEDBALL)
with scene.RelativeGroup() as functional:
    functional.set_anchor(scene.AddAsset("a black plyometric jump box", asset_id=_PLYO))
    functional.place_on_left(kettles[0])
    functional.place_on_back_left(kettles[1])
    functional.place_on_right(medballs[0])
    functional.place_on_back_right(medballs[1])
    functional.place_on_front(scene.AddAsset("a heavy training sandbag", asset_id=_SANDBAG))
    functional.place_rug("bright green artificial turf with white line markings", size=1.8)

# ============================ RECEPTION (desk backed to wall, facing in) ============================
reception_desk = scene.AddAsset("a modern curved reception front desk", asset_id=_DESK)
with scene.RelativeGroup() as reception:
    reception.set_anchor(reception_desk)
    reception.place_on_back(scene.AddAsset("an ergonomic office chair"))   # staff behind, toward wall
    reception.place_on_right(_fit_height(scene.AddAsset("a tall potted plant"), 1.4))

# MASSAGE lounge: a pair of recliners by the reception (its own zone, not the reception group)
massage_pair = 2 * scene.AddAsset("a black leather massage recliner chair", asset_id=_MASSAGE)
with scene.GridGroup(sparsity=0.5, randomness=0.08) as massage:
    massage.place_row(massage_pair)

# AMENITIES: water cooler + trash tucked in a corner
with scene.RelativeGroup() as amenities:
    amenities.set_anchor(_fit_height(scene.AddAsset("a freestanding water cooler dispenser", asset_id=_COOLER), 1.1))
    amenities.place_on_right(_fit_height(scene.AddAsset("a tall cylindrical trash can", asset_id=_TRASH), 0.6))

# ============================ ROOM ============================
with scene.RoomGroup(modulate_scale=0.9, randomness=0.1, max_height=4.0) as room:
    room.place_walls(floor_texture="black rubber gym flooring",
                     ceiling_texture="exposed grey industrial ceiling",
                     wall_texture="warm white plaster")

    # RIGHT (glass) wall = cardio run, facing the view
    room.place_on_right(cardio, facing="right")
    room.place_window_floor_to_ceiling("right_wall")

    # BACK wall (right side) = spin studio, facing into the room
    room.place_on_back_right(bikes, facing="front")

    # LEFT (mirror) wall + back-left = weight-training zone (kept together)
    room.place_mirror_full_wall("left_wall")
    room.place_on_back_left(machines, facing="front")
    room.place_on_left_wall_left(scene.AddAsset("a squat rack with a barbell", asset_id=_POWERRACK))
    room.place_on_left_wall_center(scene.AddAsset("a weight rack with dumbbells", asset_id=_DBRACK))
    room.place_on_left_wall_right(scene.AddAsset("a loaded weight plate tree", asset_id=_PLATETREE))
    room.place_on_left(benches_grp, facing="left")

    # CENTRE = functional turf
    room.place_on_center(functional)

    # FRONT = reception (left) + massage lounge (centre); amenities in the front-right corner
    room.place_on_front_left(reception, facing="back")
    room.place_on_front(massage, facing="back")
    room.place_on_front_right_corner(amenities, facing="back")

    # FRONT wall = entry + storage + brand
    room.place_door("front_wall", position="right")
    lockers = scene.AddAsset("a row of gym lockers", asset_id=_LOCKERS)
    room.place_on_front_wall_left(lockers)
    room.place_on_wall_front_center(scene.AddAsset("a large abstract geometric wall art in navy and gold", asset_id=_ART))
    # clock on the back wall (above the spin studio) -- front-wall 'right' is the door's slot
    room.place_on_wall_back_center(scene.AddAsset("a large modern wall clock"))

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
    # reception: a clear approach in front and to the sides of the desk
    room.add_clearance(reception_desk, distance=0.8, dir="front_sides")
    # lockers ("wardrobe"): changing space in front
    room.add_clearance(lockers, distance=0.8, dir="front")

    # lighting: linear industrial ceiling runs (low density -- a huge ceiling swarms otherwise)
    room.add_lighting("a row of bright industrial linear ceiling lights", density=0.008)

scene.export("gym_mega.blend")
