"""
Museum (grand hall) — "The Great Gallery": a big, many-exhibit museum built on the 68 newly ingested
custom assets. Companion to the small sculpture gallery in `museum.py`; this one is the BIG room.

What the new ingest unlocks (v1 could not do any of this):
  * a real HERO — a mounted DINOSAUR SKELETON — instead of a field of busts;
  * the ROPE STANCHIONS v1 had to cut for lack of an asset (the mesh is a post WITH its belt already
    spanning, so a row of them chains into an actual cordon);
  * whole themed zones: antiquities (Rosetta Stone, Egyptian priest, Chinese ding), natural history
    (dodo, taxidermy birds), arms & armour (knight + horse, samurai), industry (locomotive, letterpress),
    crafts (loom, potter's wheel, bicycle), a sculpture court (Neptune, marble man, bronze horse).

Zone map (9 floor slots; the hall is BIG and sizes itself from these):
  - CENTRE       = the HERO: the dinosaur skeleton, cordoned by rope stanchions on both flanks.
  - LEFT         = CLASSICAL rank: three marble plinths (Caesar, Nefertiti, a woman's portrait bust).
  - RIGHT        = CURIOSITIES rank: three plinths (dodo, taxidermy birds, a model sailing ship).
  - BACK         = ANTIQUITIES: the Rosetta Stone + the Egyptian priest + a bronze ding on plinths.
  - BACK-LEFT    = INDUSTRY: Stephenson's Rocket + a cast-iron letterpress press.
  - BACK-RIGHT   = CRAFTS: weaving loom, potter's wheel, antique bicycle.
  - FRONT-LEFT   = ARMS & ARMOUR: the mounted knight (his LANCE is what makes the hall tall), samurai,
                   a pilot's uniform.
  - FRONT-RIGHT  = SCULPTURE COURT: Neptune, a standing marble man, a bronze horse, a modern piece.
  - FRONT        = the visitors' bench on the axis + the entrance door.
  - WALLS        = the picture hang (certified canvases) + a ceremonial mask; a low viewing bench under
                   each long-wall run; palms in the back corners.

CEILING: the room auto-grows to `tallest floor object + 2 m`, clamped to `max_height` (default 3.0).
The knight's upright lance is 4.10 m, so `max_height=5.0` turns that clamp into a genuine museum hall
instead of decapitating the exhibit. Height is a CONSEQUENCE of the tallest exhibit — do not shrink a
showpiece to fit a low default ceiling (fixture-true-size rule).

CARRIED OVER FROM museum.py (learned the hard way, do not re-derive):
  * `place_on_top` seats onto the group's ANCHOR — so a plinth is the anchor and the exhibit goes on it.
  * Wall art and TALL floor furniture cannot share a wall: anything near a wall and taller than the art's
    bottom edge gets slid along it, and if no slot can clear it the build WARNS. Hence every tall exhibit
    stands in a FLOOR THIRD (metres clear of the walls in a hall this size) and only the LOW benches go
    wall-flush ("a console below a painting stays").
  * Wall art is sized by the slot cap `min(target, wall_len/5)` and a ~1 m height ceiling in the scale
    computer — in a hall this big that cap is generous (a 10 m wall => ~2 m canvases), which is why the
    slot verbs are used here rather than freeform (freeform hangs at HEIGHT/2 = 2.5 m in a 5 m room —
    too high; the slot band is the right art height).
  * Only CERTIFIED canvases are hung (see museum.py): several dataset paintings are duds that render as
    an empty frame or a black panel.
  * Ingested `scale` is a GUESSED width — always measure with get_whd() and retarget by HEIGHT.

Phase 1: the exhibits + the cordon + the shell (floor layout, room shape).
Phase 2: the plinth-top exhibits + the corner palms.
Phase 3: the picture hang + the mask + the track lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()

scene = SceneProgRoom("MuseumGrand", seed=31)

# ---------------------------------------------------------------- newly ingested exhibits (pinned)
_DINO      = "custom/faba13a524f465b7ede045ca7b86baa3a6b0aaef"  # mounted dinosaur skeleton  (2.69 x 1.60 x 2.85)
_STANCHION = "custom/6c67d07168e6fa6c6259734db71233b9eedc6658"  # rope barrier post + BELT    (1.83 wide incl. belt)
_ROSETTA   = "custom/edb4327a7d4fde2f42693e365331175a88562f6c"  # the Rosetta Stone           (h 1.14)
_PRIEST    = "custom/75fae38e2c9825c70b0866978cd01f629de20920"  # Egyptian statue of a priest (h 0.80)
_DING      = "custom/a0002583456154bd751c49638ad2f87da0a103a4"  # Chinese bronze ding vessel  (h 0.40)
_NEFERTITI = "custom/8ef9db97a4cf049fd34230286e4621bc6225061c"  # bust of Nefertiti           (h 0.50)
_CAESAR    = "custom/754051e7678f6ee20330f3ea1139aa5e3dbf85d4"  # marble bust of Caesar       (h 0.85)
_BUST_W    = "custom/d39ba4cd970d300db3ab2d1077fce7f7f290548f"  # marble portrait bust, woman (h 0.70)
_NEPTUNE   = "custom/5e8ecba1a838a04b1dc80af98afe2dfa85b8bb78"  # marble statue of Neptune    (h 1.80)
_MARBLEMAN = "custom/5353f02fdc2f2e681d3a891841c87976e325f8ad"  # standing marble man         (h 2.00)
_HORSE     = "custom/f2b09d35275927c6a126f84d47e90d2c2f659f4a"  # bronze sculpture of a horse (h 1.60)
_CABBAGE   = "custom/bc1152a33b3faf4479b4b4a6c024de0bcf1f4bd0"  # modern figure w/ cabbage head (h 1.34)
_KNIGHT    = "custom/db834a3c3281660e2fc3168697a4324d44be2be5"  # knight + horse armour, LANCE (h 4.10 -> sets the ceiling)
_SAMURAI   = "custom/d9e196d59e4026b42d503aba272a0c4b1a4d98f4"  # samurai armour on a stand   (h 1.50)
_UNIFORM   = "custom/6733b1985471c1dfd88eddafc89b1eaaae751208"  # pilot's uniform on a stand  (h 0.75)
_DODO      = "custom/ab63a413293446abf1aeac1ae1ec576aa19bc089"  # taxidermy dodo              (h 1.00)
_BIRDS     = "custom/a8b7110549688b39669638aea7c89faa8aefc0bf"  # taxidermy bird display      (h 0.35)
_SHIP      = "custom/4fa035b921ad4d203505487f3d315295e8206ee7"  # model sailing ship          (h 1.00)
_LOCO      = "custom/add534935babce1c23ebee330694fa11ad6b9460"  # Stephenson's Rocket         (h 2.20)
_PRESS     = "custom/6240c055b1a06d88b8af99f387969fb9f4147e18"  # letterpress printing press  (2.06 wide)
_LOOM      = "custom/2e46da4c7fee7935328a2d1673d63e8443f12872"  # weaving loom                (h 1.49)
_WHEEL     = "custom/b18f98d6c5ba560a3669d3e7e6a8e1f14e0c5241"  # potter's wheel              (h 1.00)
_BICYCLE   = "custom/d3946ca9c317ffdace99a98825fa0addf438861d"  # antique wooden bicycle      (h 1.05)
_MASK      = "custom/a8da28bf374f984be15ba212d14ac11b071939d6"  # ceremonial mask, wall-hung  (0.13 deep -> flat enough)
# NOTE: the ship FIGUREHEAD (custom/20bacd78) is 0.43 m DEEP — hanging it would trip the "wall-hung mesh
# reads as furniture floating in mid-air" warning (>0.25 m). It belongs on a plinth, not on a wall; left
# out here rather than shipped floating.

# ---------------------------------------------------------------- carried over from museum.py
_PLINTH  = "future/58d2d3ee-5743-41e7-92dd-92d646e84938"     # plain marble plinth
_BENCH   = "hssd/8466b0bcd50deb8ff1a03e8d90bef577a44b201e"   # oak + saddle-leather bench
# CERTIFIED canvases only (each one verified to actually render its picture — see museum.py)
_FOCAL   = "future/d8f2e7b8-c201-4b29-aec9-7fe402dc1b5c"     # rococo portrait
_CLASSIC = "hssd/5d4c5918e8f7d301d36d21970d18786716dbbb1d"   # classical figure scene
_FLORAL  = "hssd/54c900dd531bc8517ffe514964f6666190d3344a"   # floral oil
_ART_A   = "hssd/950c82d2ac17a015cc5e063b664f78c965247743"   # vibrant abstract
_ART_C   = "hssd/e63f2f68c0d0de795e8a71d0f834b637502bb7db"   # bold abstract
_GEOM    = "future/d689b740-4e99-4d78-9435-1f16388964a8"     # grey geometric abstract

scene.prefetch_assets([
    "a tall potted palm tree in a planter",
    "a slim black linear LED track spotlight ceiling light bar",
])

PLINTH_W, PLINTH_H = 0.5, 1.0


def plinth():
    p = scene.AddAsset("a white marble museum display pedestal", asset_id=_PLINTH)
    p.scale(PLINTH_W)             # uniform: sets the width
    p.scale_only_height(PLINTH_H)  # then squash to display height (a plinth is a box; distortion is free)
    return p


def display(asset_id, desc, height):
    """A plinth with ONE exhibit on top. The PLINTH is the anchor — place_on_top always seats onto the
    group's anchor, so the exhibit must go on top of the plinth, never the other way round."""
    ex = scene.AddAsset(desc, asset_id=asset_id)
    ex.scale(ex.get_width() * height / ex.get_height())   # retarget by HEIGHT (ingest scale is a guess)
    with scene.RelativeGroup() as g:
        g.set_anchor(plinth())
        if PHASE >= 2:
            g.place_on_top(ex)
    return g


def floor_exhibit(asset_id, desc, height=None):
    o = scene.AddAsset(desc, asset_id=asset_id)
    if height is not None:
        o.scale(o.get_width() * height / o.get_height())
    return o


# ============================ CENTRE: the hero — dinosaur under a rope cordon ============================
# The stanchion mesh is a post WITH its belt already spanning ~1.8 m, so a rectilinear rank of them on each
# flank of the skeleton chains into a continuous cordon rather than reading as loose poles.
_dino = floor_exhibit(_DINO, "a mounted dinosaur skeleton fossil")
# 3.0 m, not the 3.4 of the first pass: at 3.4 the tail swept clear across the hall and cut through the
# industry and crafts zones behind it. A hero commands the room by standing alone in it, not by being big
# enough to overlap its neighbours.
_dino.scale(3.0)
# sparsity 0.8 (was 0.5): the cordon must stand OFF the skeleton — at 0.5 the posts ended up inside its
# footprint, under the ribs, which reads as scaffolding rather than a barrier.
with scene.AroundGroup(sparsity=0.8, jitter=0.0) as dino_hall:
    dino_hall.set_anchor(_dino)
    dino_hall.place_rectilinear(
        longer_side1=3 * scene.AddAsset("a museum rope barrier stanchion post", asset_id=_STANCHION),
        longer_side2=3 * scene.AddAsset("a museum rope barrier stanchion post", asset_id=_STANCHION))

# ============================ LEFT: the classical rank ============================
with scene.GridGroup(sparsity=0.55, randomness=0.05) as classical_rank:
    classical_rank.place_row([
        display(_CAESAR, "a classical marble bust of Caesar", 0.85),
        display(_NEFERTITI, "a bust of Nefertiti", 0.55),
        display(_BUST_W, "a marble portrait bust of a woman", 0.70),
    ])

# ============================ RIGHT: curiosities (natural history + maritime) ============================
with scene.GridGroup(sparsity=0.55, randomness=0.05) as curiosities:
    curiosities.place_row([
        display(_DODO, "a taxidermy model of a dodo bird", 0.95),
        display(_BIRDS, "a taxidermy display of birds", 0.45),
        display(_SHIP, "a detailed model of a historic sailing ship", 0.85),
    ])

# ============================ BACK: antiquities ============================
with scene.GridGroup(sparsity=0.5, randomness=0.05) as antiquities:
    antiquities.place_row([
        floor_exhibit(_ROSETTA, "the rosetta stone, an ancient inscribed stone tablet"),
        display(_PRIEST, "an ancient egyptian stone statue of a priest", 0.85),
        display(_DING, "an ancient chinese bronze ding censer vessel", 0.45),
    ])

# ============================ BACK-LEFT: industry ============================
with scene.GridGroup(sparsity=0.45, randomness=0.05) as industry:
    industry.place_row([
        floor_exhibit(_LOCO, "a model of stephenson's rocket steam locomotive"),
        floor_exhibit(_PRESS, "a cast iron letterpress printing press"),
    ])

# ============================ BACK-RIGHT: crafts ============================
with scene.GridGroup(sparsity=0.45, randomness=0.05) as crafts:
    crafts.place_row([
        floor_exhibit(_LOOM, "a wooden weaving loom"),
        floor_exhibit(_WHEEL, "a potter's wheel"),
        floor_exhibit(_BICYCLE, "an antique wooden bicycle"),
    ])

# ============================ FRONT-LEFT: arms & armour ============================
# The knight keeps his native 4.10 m (the lance). That is what pushes the shell to a 5 m museum ceiling —
# the exhibit sets the room, not the other way round.
with scene.GridGroup(sparsity=0.5, randomness=0.05) as armoury:
    armoury.place_row([
        floor_exhibit(_KNIGHT, "a suit of medieval armour for a knight and horse"),
        floor_exhibit(_SAMURAI, "a japanese samurai armour suit on a display stand"),
        floor_exhibit(_UNIFORM, "a vintage military pilot's uniform jacket on a stand"),
    ])

# ============================ FRONT-RIGHT: the sculpture court ============================
with scene.GridGroup(sparsity=0.5, randomness=0.05) as sculpture_court:
    sculpture_court.place_row([
        floor_exhibit(_NEPTUNE, "a classical marble statue of neptune"),
        floor_exhibit(_MARBLEMAN, "a tall classical marble statue of a standing man"),
        floor_exhibit(_HORSE, "a bronze sculpture of a horse"),
        floor_exhibit(_CABBAGE, "a modern sculpture of a figure with a cabbage head"),
    ])


# ============================ benches ============================
def gallery_bench():
    b = scene.AddAsset("a long backless bench with a saddle brown leather seat", asset_id=_BENCH)
    b.scale(1.6)   # UNIFORM — width= would pin one axis and flatten the bench into a plank
    with scene.RelativeGroup() as g:
        g.set_anchor(b)
    return g


axis_bench = gallery_bench()
side_benches = 2 * gallery_bench()   # low (0.5 m) -> they sit UNDER the picture hang without occluding it


def art(asset_id, desc, hung_width):
    """Wall art must be scaled UNIFORMLY — width= pins one axis and letterboxes the canvas, after which
    the scale computer preserves the broken aspect and hangs a sliver."""
    a = scene.AddAsset(desc, asset_id=asset_id)
    a.scale(hung_width)
    return a


# ============================ THE HALL ============================
# max_height=5.0: the shell grows to (tallest floor object + 2 m) clamped to this, so the knight's lance
# (4.10 m) yields a lofty 5 m hall instead of being clipped by the default 3 m ceiling.
with scene.RoomGroup(modulate_scale=0.9, randomness=0.08, max_height=5.0) as room:
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white plaster ceiling",
                     wall_texture="warm ivory plaster wall")

    room.place_on_center(dino_hall)                       # the hero
    room.place_on_left(classical_rank, facing="right")    # ranks turn to face the central aisle
    room.place_on_right(curiosities, facing="left")
    room.place_on_back(antiquities, facing="front")
    room.place_on_back_left(industry, facing="front")
    room.place_on_back_right(crafts, facing="front")
    room.place_on_front_left(armoury, facing="back")
    room.place_on_front_right(sculpture_court, facing="back")
    room.place_on_front(axis_bench)                       # the visitors' bench on the axis

    # LOW benches go wall-flush (they stay below the pictures); the tall exhibits never do
    room.place_on_left_wall_center(side_benches[0])
    room.place_on_right_wall_center(side_benches[1])
    room.place_door("front_wall", position="right")

    if PHASE >= 2:
        room.place_on_back_left_corner(scene.AddAsset("a tall potted palm tree in a planter"))
        room.place_on_back_right_corner(scene.AddAsset("a tall potted palm tree in a planter"))

    if PHASE >= 3:
        # THE PICTURE HANG — slot verbs (not freeform): in a hall this big the slot cap (wall_len/5) is
        # generous, and the slot band hangs the art at a proper viewing height, whereas freeform would
        # centre it at HEIGHT/2 = 2.5 m in a 5 m room. Certified canvases only.
        room.place_on_wall_left_left(art(_CLASSIC, "a large framed classical oil painting of figures", 1.8))
        room.place_on_wall_left_center(art(_FLORAL, "a framed floral still life oil painting", 1.4))
        room.place_on_wall_left_right(art(_GEOM, "a large framed grey geometric abstract painting", 1.5))
        room.place_on_wall_right_left(art(_ART_A, "a large framed vibrant abstract colour field painting", 1.8))
        room.place_on_wall_right_center(art(_ART_C, "a large framed bold abstract painting", 1.5))
        # the rococo portrait caps the sightline down the hall.
        # The ceremonial MASK was here and is now DROPPED: its manifest depth is 0.13 m, but the wall
        # scaler re-derives depth from the hung size and it came out 0.31 m — over the 0.25 m limit —
        # so the build warned it "will read as furniture FLOATING in mid-air". A mask that thick is a
        # plinth exhibit, not wall art; hanging it anyway would have shipped a floating object.
        room.place_on_wall_back_center(art(_FOCAL, "a large framed classical portrait painting", 1.6))
        # TRACK LIGHTING — density is a fixture COUNT and the count grows with FLOOR AREA, so the ladder
        # runs BACKWARDS from intuition: the small gallery wanted 0.08, but at 0.12 this big hall tiled
        # its ceiling with a STARFIELD of dozens of fixtures. 0.02 gives a calm run of bars over a floor
        # this size. (Same trap as retail_store/bookstore: when the ceiling reads as a grid, cut density.)
        room.add_lighting("a slim black linear LED track spotlight ceiling light bar", density=0.02)

scene.export("museum_grand.blend")
