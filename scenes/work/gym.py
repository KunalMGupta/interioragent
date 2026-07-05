"""
Gym — "Boutique Fitness Floor". Premium zoned gym off the planner target:
black rubber floor + green turf, exposed grey ceiling, warm-white walls, one mirrored wall,
floor-to-ceiling glass on the opposite wall.

Zoning (planner target, tmp/gym/plan/plan.png):
  - right (long) wall = floor-to-ceiling WINDOWS -> the CARDIO bank (treadmills + a bike) sits
    along the glass facing the view (sightlines, daylight).
  - left  (long) wall = MIRRORED -> the STRENGTH zone: a dumbbell rack against the wall with two
    flat benches in front; three large mirrors tiled across the wall (place_on_wall_freeform) read
    as one mirrored wall (a true full-wall mirror is a deferred architectural feature).
  - centre floor = the FUNCTIONAL zone on a green turf patch: a plyo box, kettlebells, a sandbag.
  - back (short) wall = the "brand"/wellness end: a low wood storage console under a navy+gold
    geometric feature-art, a clock beside it.  (A real per-wall navy branding wall would need a
    per-wall accent texture -- not in the DSL yet; flagged as future work.)
  - front (short) wall = entry door.

Phase 1: cardio bank + strength (rack + benches) + functional plyo box  (floor anchors).
Phase 2: kettlebells / sandbag / turf rug + linear ceiling lighting     (details).
Phase 3: mirrored wall + window + door + console + feature art + clock  (walls & decor).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Gym", seed=8)

# --- pinned assets (audited previews; see scenes/work/gym.md) ---
_TREADMILL = "hssd/fdd91608c418ead483b7a0bbd78a82a6306f36d0"   # black treadmill, LED console
_BIKE      = "hssd/b3ef9e90aaafb14f946e6c716f36eba419fa76a7"   # upright stationary bike
_BENCH     = "hssd/0391f7b149076276d028060971ae3d197619f196"   # flat weight bench
_RACK      = "hssd/f7109eaad4235fd4db456ca184f9f458a3611421"   # dumbbell rack, two rows
_PLYO      = "hssd/2f2b6ebda280d38ed6c9bfcec919f6308ab17f27"   # black plyo box
_KETTLE    = "hssd/c3bb69cc0d810d1d784e523f38de24fef5f1c244"   # black kettlebell
_SANDBAG   = "hssd/b98b86e3d373233c18f0f9c2b00119d220db8059"   # Rogue training sandbag (functional)
_CONSOLE   = "future/11e48b3a-7f5a-4964-a56b-20b5313c1de8"     # low wood media console / sideboard
_ART       = "future/9c5ac3d9-107f-49da-ae76-be9eb2c6de32"     # navy + gold geometric feature art

# --- CARDIO bank: three identical treadmills + a bike, as one row along the window wall ---
cardio_machines = 3 * scene.AddAsset("a treadmill exercise machine", asset_id=_TREADMILL)
cardio_machines.append(scene.AddAsset("an upright stationary exercise bike", asset_id=_BIKE))
with scene.GridGroup(sparsity=0.5) as cardio:
    cardio.place_row(cardio_machines)

# --- STRENGTH zone: two parallel flat benches (placed in front of the wall dumbbell rack) ---
benches = 2 * scene.AddAsset("a flat weight training bench", asset_id=_BENCH)
with scene.RelativeGroup() as strength:
    strength.set_anchor(benches[0])
    strength.place_on_right(benches[1])

# --- FUNCTIONAL zone: plyo box + kettlebells + sandbag on a green turf patch ---
kettles = 2 * scene.AddAsset("a cast iron kettlebell weight", asset_id=_KETTLE)
with scene.RelativeGroup() as functional:
    functional.set_anchor(scene.AddAsset("a black plyometric jump box", asset_id=_PLYO))
    functional.place_on_left(kettles[0])
    functional.place_on_front_left(kettles[1])
    functional.place_on_right(scene.AddAsset("a heavy training sandbag", asset_id=_SANDBAG))
    functional.place_rug("bright green artificial turf with white line markings", size=1.4)

with scene.RoomGroup(modulate_scale=0.85, randomness=0.12) as room:
    room.place_walls(floor_texture="black rubber gym flooring",
                     ceiling_texture="exposed grey industrial ceiling",
                     wall_texture="warm white plaster")
    # right (long) wall = glass: cardio bank faces the windows
    room.place_on_right_wall_center(cardio, facing="right")
    room.place_window_floor_to_ceiling("right_wall")
    # left (long) wall = mirrored: dumbbell rack on the wall, benches in front, mirrors tiled above
    room.place_on_left_wall_center(scene.AddAsset("a weight rack with dumbbells", asset_id=_RACK))
    room.place_on_left(strength, facing="right")
    # a real floor-to-ceiling mirrored wall behind the strength zone (one reflective surface)
    room.place_mirror_full_wall("left_wall")
    # centre = functional turf zone
    room.place_on_center(functional)
    # back (short) wall = brand/wellness end: console + feature art above + clock
    room.place_on_back_wall_left(scene.AddAsset("a low wooden media console sideboard", asset_id=_CONSOLE))
    room.place_on_wall_back_left(scene.AddAsset("a large abstract geometric wall art in navy and gold", asset_id=_ART))
    room.place_on_wall_back_right(scene.AddAsset("a large modern wall clock"))
    # front (short) wall = entry
    room.place_door("front_wall", position="right")
    # lighting: linear industrial ceiling runs
    room.add_lighting("a row of bright industrial linear ceiling lights", density=0.03)

scene.export("gym.blend")
