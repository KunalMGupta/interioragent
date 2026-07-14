"""
Big commercial gym — "Full Fitness Floor". A larger, four-zone build used to stress-test how
much of a realistic gym the asset library actually covers and whether it all places cleanly.
Same aesthetic as scenes/work/gym.py (black rubber + turf, exposed ceiling, warm-white walls,
one full mirrored wall, glass on the opposite wall).

Zones (each loads a different wall; the four walls do the heavy lifting, centre stays functional):
  - right (long) wall  = GLASS: a CARDIO bank (3 treadmills + elliptical + upright bike) on the view.
  - left  (long) wall  = full MIRRORED wall + FREE-WEIGHT zone: power rack, dumbbell rack, plate
                         tree, two flat benches in front.
  - back  (short) wall = MACHINE circuit: lat pulldown, chest/pec machine, ab-crunch machine,
                         cable functional trainer, in a row facing the floor.
  - front (short) wall = ENTRY + AMENITIES: door, lockers, water cooler, wood console (art + clock),
                         a potted plant.
  - centre             = FUNCTIONAL turf patch: plyo box, kettlebells, medicine ball, sandbag.

Every asset id below was picked by previewing candidates (see scenes/work/gym.md audit). Gaps in
the dataset (rowing ergometer, leg press, Smith machine, battle rope) are covered by close
stand-ins (elliptical/incline-bench-press/power-rack/sandbag) or simply omitted.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("GymLarge", seed=11)

# --- pinned assets (previewed) ---
_TREADMILL  = "hssd/fdd91608c418ead483b7a0bbd78a82a6306f36d0"
_ELLIPTICAL = "future/1f79b924-dc7c-427e-aaf8-eef7974ad805"
_BIKE       = "hssd/b3ef9e90aaafb14f946e6c716f36eba419fa76a7"
_POWERRACK  = "hssd/b46437ac19972f7c42291bbdc7a45a549297fce6"   # squat rack w/ barbell
_DBRACK     = "hssd/f7109eaad4235fd4db456ca184f9f458a3611421"   # dumbbell rack
_PLATETREE  = "hssd/fb93338620659f63363044463164f29680667a7a"   # loaded vertical plate tree
_BENCH      = "hssd/0391f7b149076276d028060971ae3d197619f196"   # flat bench
_LAT        = "future/96bb6aab-d17f-4cf2-821a-fc29cd0545d2"     # lat pulldown, weight stack
_PEC        = "hssd/5406441590ae50f71a4d5a65d7a427761713e647"   # chest/pec multi-gym
_AB         = "hssd/b16e1cc9c69bef43c81087e0c7d4ae7cee2acec4"   # ab-crunch machine
_CABLE      = "hssd/ac2b117a76e842cf7e2af1dd16d0a88d01e78c41"   # cable tower / functional trainer
_PLYO       = "hssd/2f2b6ebda280d38ed6c9bfcec919f6308ab17f27"   # plyo box
_KETTLE     = "hssd/c3bb69cc0d810d1d784e523f38de24fef5f1c244"   # kettlebell
_MEDBALL    = "hssd/33adf260d1a6f88f0d5b7bd017a6182f815d715c"   # rubber medicine ball
_SANDBAG    = "hssd/b98b86e3d373233c18f0f9c2b00119d220db8059"   # training sandbag
_LOCKERS    = "future/902f9b5b-72ce-4fb7-a870-4f8ec97a3a2d"     # black 3-door lockers
_COOLER     = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"   # water cooler
_CONSOLE    = "future/11e48b3a-7f5a-4964-a56b-20b5313c1de8"     # wood console
_ART        = "future/9c5ac3d9-107f-49da-ae76-be9eb2c6de32"     # navy + gold feature art

# --- CARDIO bank (right glass wall) ---
cardio_items = 3 * scene.AddAsset("a treadmill exercise machine", asset_id=_TREADMILL)
cardio_items.append(scene.AddAsset("an elliptical cross-trainer cardio machine", asset_id=_ELLIPTICAL))
cardio_items.append(scene.AddAsset("an upright stationary exercise bike", asset_id=_BIKE))
with scene.GridGroup(sparsity=0.5) as cardio:
    cardio.place_row(cardio_items)

# --- FREE-WEIGHT benches (in front of the mirror wall) ---
benches = 2 * scene.AddAsset("a flat weight training bench", asset_id=_BENCH)
with scene.RelativeGroup() as strength:
    strength.set_anchor(benches[0])
    strength.place_on_right(benches[1])

# --- MACHINE circuit (back wall) ---
with scene.GridGroup(sparsity=0.5) as machines:
    machines.place_row([
        scene.AddAsset("a lat pulldown weight machine", asset_id=_LAT),
        scene.AddAsset("a seated chest press pec deck machine", asset_id=_PEC),
        scene.AddAsset("an abdominal crunch weight machine", asset_id=_AB),
        scene.AddAsset("a functional trainer cable machine", asset_id=_CABLE),
    ])

# --- FUNCTIONAL turf zone (centre) ---
kettles = 2 * scene.AddAsset("a cast iron kettlebell weight", asset_id=_KETTLE)
with scene.RelativeGroup() as functional:
    functional.set_anchor(scene.AddAsset("a black plyometric jump box", asset_id=_PLYO))
    functional.place_on_left(kettles[0])
    functional.place_on_front_left(kettles[1])
    functional.place_on_right(scene.AddAsset("a rubber medicine ball", asset_id=_MEDBALL))
    functional.place_on_front_right(scene.AddAsset("a heavy training sandbag", asset_id=_SANDBAG))
    functional.place_rug("bright green artificial turf with white line markings", size=1.6)

with scene.RoomGroup(modulate_scale=0.8, randomness=0.12) as room:
    room.place_walls(floor_texture="black rubber gym flooring",
                     ceiling_texture="exposed grey industrial ceiling",
                     wall_texture="warm white plaster")
    # right (long) wall = glass: cardio bank faces the view
    room.place_on_right_wall_center(cardio, facing="right")
    room.place_window_floor_to_ceiling("right_wall")
    # left (long) wall = mirrored: free-weight zone
    room.place_mirror_full_wall("left_wall")
    room.place_on_left_wall_left(scene.AddAsset("a squat rack with a barbell", asset_id=_POWERRACK))
    room.place_on_left_wall_right(scene.AddAsset("a weight rack with dumbbells", asset_id=_DBRACK))
    room.place_on_back_left(scene.AddAsset("a loaded weight plate tree", asset_id=_PLATETREE))
    room.place_on_left(strength, facing="left")
    # back (short) wall = machine circuit facing the floor
    room.place_on_back_wall_center(machines, facing="front")
    # centre = functional turf
    room.place_on_center(functional)
    # front (short) wall = entry + amenities
    room.place_door("front_wall", position="right")
    room.place_on_front_wall_left(scene.AddAsset("a row of gym lockers", asset_id=_LOCKERS))
    room.place_on_front_wall_center(scene.AddAsset("a low wooden media console sideboard", asset_id=_CONSOLE))
    room.place_on_front_left(scene.AddAsset("a freestanding water cooler dispenser", asset_id=_COOLER))
    room.place_on_front_right(scene.AddAsset("a tall potted plant"))
    # decor
    room.place_on_wall_front_center(scene.AddAsset("a large abstract geometric wall art in navy and gold", asset_id=_ART))
    room.place_on_wall_front_left(scene.AddAsset("a large modern wall clock"))
    # lighting: linear industrial ceiling runs (low density -- a big ceiling swarms otherwise)
    room.add_lighting("a row of bright industrial linear ceiling lights", density=0.012)

scene.export("gym_large.blend")
