"""
Greenhouse — "Glasshouse Atelier Rhythm" (planner target: tmp/plan_A_greenhouse___glass_conservator/plan.png).

A working glass conservatory. The identity is NOT a hero mesh — it is the RHYTHM of repeated
potting benches massed with potted plants and seed trays, under a mullioned glass envelope, on
gravel. (florist_shop lesson: when the dataset is thin on the literal hero — no potting bench, no
seed tray, no bag of soil — MASS the prop it IS rich in. Here that is potted plants.)

Zone map (the nave runs front<->back; the LONG walls are LEFT + RIGHT, both GLAZED):
  - LEFT + RIGHT (long, glazed) = twin BENCH RUNS lining the glass (library's twin-shelf corridor,
    but the runs are potting benches and the "wall" behind them is a wall of glass).
  - CENTRE                      = the HERO: a spine of potting benches down the long axis (the plan's
    "central spine of long potting benches").
  - BACK (short, solid)         = the potting/"shed" end: the potting station bench (watering can +
    tool box), the hung GARDEN TOOL BOARD, tall tropicals in both corners.
  - FRONT (short, solid)        = the entrance door.

THE GLASS DECISION (this is the scene's whole design risk — read before editing):
  The bundle's lore says any opening renders as a BLACK NIGHT VOID, and that a full-height glazed
  wall is the worst case (retail_store). I checked instead of inheriting it:
    * the texture library has ZERO glass textures (1391 descriptions, 0 hits) — so the glass CANNOT
      come from wall_texture. Glazing is the only route to a conservatory.
    * `place_window_floor_to_ceiling` REMOVES the wall (groups.py:1977) and tiles the
      window_tofloor mesh across it every ~1.5 m — i.e. it builds a real MULLION FRAME, which is
      structurally exactly a greenhouse glazed wall.
    * every render path calls set_white_world_background(0.7 grey, strength=1.0)
      (renderer/utils.py:504) — the world is LIGHT GREY, not black.
  So the void lore may be stale. Both long walls are glazed and the glazing is deliberately built in
  PHASE 1 (not phase 3) so the cheap ~1-min layout build answers the question before any expensive
  surface dressing. If the glass does come back black: fall back to glazing the BACK wall only and
  stage the tall palms in front of it (retail_store's "foreground object turns the void into a
  backdrop"), and let gravel + massed plants carry the read.

Scale traps caught in the audit (get_whd, offline — hospital-bed / garage-car lesson):
  - the bench mesh is natively 1.20 x 0.70 x 0.43 m -> too low/short for a potting bench.
    scale(1.6) takes it to a real ~0.93 m bench height.
  - the "tall tropical palm" is natively only 0.70 m TALL (its retriever scale metadata lies). Left
    alone it reads as a tabletop plant, not a vertical anchor -> scale-by-height to ~1.7 m.

Phase 1: the three bench runs (bare), the corner palms, the room shell, the door, the GLAZING.
Phase 2: the massing — potted plants + seed trays on every bench; floor props (grow bags, pots).
Phase 3: the hung garden-tool board, ceiling lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Greenhouse", seed=52)

# --- pinned assets (every preview eyeballed; audit notes in scenes/notes/greenhouse.md) ---
_BENCH    = "hssd/291a6b41232b94554e4a613e65fc08bd34274724"  # rustic wooden console + LOWER SHELF = the potting-bench form
_PLANT_LU = "hssd/c7a9fcbab796f68f91b16ab2bc5edd05f477d26f"  # lush green indoor plant (the workhorse bench plant)
_PLANT_TC = "future/76b98744-c079-456e-9376-046b1399c40c"    # succulent in a TERRACOTTA pot (carries the terracotta tone)
_PLANT_FL = "hssd/431965c6c19be61f2eca3ad05b85000be9abfd5c"  # terracotta pot of colorful flowering plants
_PLANT_PA = "hssd/b785b0fada85f3b40bf8bb126dce2b03c82d86cf"  # terracotta pot of pansies
_SEEDTRAY = "hssd/37ee3df8ebe30258d6d109ce4cdd99076d979478"  # low trough of green sprouts = the seed tray stand-in
_TRAY_BLK = "future/5903100c-0111-42a9-bcdf-f0fb9d4e28ca"    # lush plant in a black rectangular planter (2nd tray form)
_SUCCUL   = "hssd/ccc8eeed121cb0930adf6b38231b4c9ad2c72391"  # small succulent, brown pot
_GRASS    = "hssd/ea0200d78c2699f025cc8ec86930842e214bd6d2"  # tall green grass in a dark pot
_PALM_BIG = "future/130b1ed4-b579-481b-a8ee-aaeee5c6e6ef"    # lush multi-frond palm (the vertical anchor) - SCALE IT UP
_PALM_BSK = "future/9d83605d-ea7c-423c-83c0-98a48ab56058"    # palm in a woven basket
_CAN      = "hssd/8e8089c948738f725830da4294a3c8a1ca40ab4b"  # REAL stainless watering can (0.72) - the signature prop
_TOOLS    = "hssd/0071f864b2cc52a7ecd4603f5f92bcdcdc93a2d1"  # wooden garden tool board: rake/fork/spade/broom (0.06 m deep = FLAT -> hangable)
_TOOLBOX  = "hssd/f2d794dbfd6d4a15ecb42b527d337a3e02d45947"  # wooden box holding a garden tool set
_GROWBAG  = "hssd/2cc7a3e14760c46af43565634f9d4492ec303b9f"  # green fabric grow bag with plants growing out of it

scene.prefetch_assets([
    "a long rustic wooden potting bench with a lower shelf",
    "a lush green potted plant", "a succulent in a terracotta pot",
    "a terracotta pot of flowering plants", "a terracotta pot of pansies",
    "a tray of green seedling sprouts", "a lush plant in a rectangular planter",
    "a small succulent in a brown pot", "tall green grass in a pot",
    "a tall tropical potted palm plant", "a stainless steel watering can",
    "a wooden garden tool board with a rake and spade", "a wooden box of garden tools",
    "a green fabric grow bag with plants",
])


def _fit_height(obj, h):
    """Scale UNIFORMLY to a target HEIGHT (dsl_reference: scale(width*H/height)). Used on the palms,
    whose meshes are natively ~0.70 m — `width=` alone would squash them (children_room bean-bag)."""
    obj.scale(obj.get_width() * h / obj.get_height())
    return obj


def potting_bench():
    """A bare potting bench at real bench scale. The reusable unit of the whole scene."""
    bench = scene.AddAsset("a long rustic wooden potting bench with a lower shelf", asset_id=_BENCH)
    bench.scale(1.6)            # native 1.20 W x 0.70 H -> 1.60 W x ~0.93 H = a real potting bench
    return bench


def bench_unit(plants):
    """A potting bench MASSED with plants/trays — the florist `bloom_table` pattern.
    place_on_top distributes the list along the bench top, and ALWAYS targets the group's
    anchor (living_room_cozy v3 lesson) — here the anchor IS the bench, which is what we want."""
    with scene.RelativeGroup() as b:
        b.set_anchor(potting_bench())
        if PHASE >= 2:
            b.place_on_top(plants)
    return b


# ---------------- PLANT BEDS: the thing that makes this a NURSERY and not a flower shop -------------
# Kunal's note on v1: massing single specimens on repeated tables is literally the florist_shop recipe,
# so it CAME OUT looking like the florist shop. A nursery does not read by tidy specimens — it reads by
# THICKETS: dense pockets where plants are packed shoulder-to-shoulder into a single mass of foliage.
#
# A GridGroup is exactly the tool: it is deterministic (no overlap solve), so a near-zero `sparsity`
# packs items until they almost touch — which is what we want here and is normally a bug. `randomness`
# jitters the gaps so the block reads as a grown-in bed rather than a CAD array. Rotating the pinned
# plant palette per cell makes each bed a mixed thicket instead of a monoculture.
_BED_MIX = [_PLANT_LU, _PLANT_TC, _SUCCUL, _GRASS, _PLANT_PA, _SEEDTRAY, _PLANT_FL, _TRAY_BLK]
_bed_i = [0]


def plant_bed(n=12, cols=4, sparsity=0.0):
    """A densely-packed pocket of mixed plants — the nursery's signature. Placed as ONE floor object,
    so it costs a single room slot (the shell does not balloon) but fills it with a mass of green.

    sparsity=0.0 packs the plants until their bounding boxes touch, so the FOLIAGE interlaces and the
    block reads as one thicket rather than N pots in rows. This is only safe because GridGroup is
    deterministic (no overlap solve) — in any solving group this would be fought back apart.
    Normalize the bed by WIDTH (`scale(w)`, uniform), never by height. The mix contains flat troughs
    (the seed tray is 0.30 W x 0.10 H): height-fitting one of those multiplies it ~5.5x and it lands as
    a 1.65 m pale-green SLAB that eats the bed — tried it, saw it. Fitting a common width keeps every
    footprint packable while natural height variation is preserved, which is what makes the canopy read
    as a grown-in bed instead of a shelf of identical product."""
    plants = []
    for _ in range(n):
        aid = _BED_MIX[_bed_i[0] % len(_BED_MIX)]
        _bed_i[0] += 1
        p = scene.AddAsset("a potted green plant", asset_id=aid)
        p.scale(0.42)                     # NB: scale() returns None — never chain it
        plants.append(p)
    with scene.GridGroup(sparsity=sparsity, randomness=0.35) as bed:
        bed.place_grid(plants, cols=cols)
    return bed


# ---------------- the two bench mixes (built ONCE, then duplicated: design_principles) ----------------
# Two distinct mixes so the runs read as a working nursery rather than a CAD array, but only TWO
# place_on_top tournaments run — `N * unit` deep-copies the composed unit for free.
mix_a = bench_unit([
    scene.AddAsset("a lush green potted plant", asset_id=_PLANT_LU),
    scene.AddAsset("a tray of green seedling sprouts", asset_id=_SEEDTRAY),
    scene.AddAsset("a succulent in a terracotta pot", asset_id=_PLANT_TC),
    scene.AddAsset("a terracotta pot of flowering plants", asset_id=_PLANT_FL),
])
mix_b = bench_unit([
    scene.AddAsset("a terracotta pot of pansies", asset_id=_PLANT_PA),
    scene.AddAsset("a lush plant in a rectangular planter", asset_id=_TRAY_BLK),
    scene.AddAsset("tall green grass in a pot", asset_id=_GRASS),
    scene.AddAsset("a small succulent in a brown pot", asset_id=_SUCCUL),
])

a1, a2, a3 = 3 * mix_a
b1, b2, b3 = 3 * mix_b

# LEFT + RIGHT long walls: twin bench runs lining the glass. A butted GridGroup.place_row is
# deterministic (no overlap solve) -> exact alignment, the warehouse/library "wall run" pattern.
with scene.GridGroup(sparsity=0.06, randomness=0.0) as run_left:
    run_left.place_row([a1, b1, a2])
with scene.GridGroup(sparsity=0.06, randomness=0.0) as run_right:
    run_right.place_row([b2, a3, b3])

# CENTRE: the hero spine — a column of benches down the long axis (cols=1, library's centre column).
c1, c2 = 2 * mix_a
with scene.GridGroup(sparsity=0.45, randomness=0.12) as spine:
    spine.place_grid([c1, c2], cols=1)

# ---------------- BACK end: the potting STATION (the working heart of the shed wall) ----------------
# The bench stays LOW (~0.93 m, well under the ~1.4 m interior camera height) so it neither blinds the
# back-wall camera nor triggers the phantom rotation storm (bakery v1 lesson).
with scene.RelativeGroup() as potting_station:
    potting_station.set_anchor(potting_bench())
    if PHASE >= 2:
        potting_station.place_on_top([
            scene.AddAsset("a stainless steel watering can", asset_id=_CAN),
            scene.AddAsset("a wooden box of garden tools", asset_id=_TOOLBOX),
            scene.AddAsset("a terracotta pot of flowering plants", asset_id=_PLANT_FL),
        ])

# ---------------- tall tropicals: the vertical anchors (SCALED UP — the mesh is natively 0.70 m) -----
palm_l = _fit_height(scene.AddAsset("a tall tropical potted palm plant", asset_id=_PALM_BIG), 1.75)
palm_r = _fit_height(scene.AddAsset("a tall tropical potted palm plant", asset_id=_PALM_BSK), 1.65)

# modulate_scale 0.9: the shrink vote never flipped (0.88 -> 0.82 -> 0.7) so it is signal, but 0.7 is
# not safe to apply — the shell auto-sizes to FIT the three fixed-size bench rows, and going far below
# 1.0 pushes them out of their slots (locker_room). One mild, decisive 0.9 + a dressed floor instead.
with scene.RoomGroup(modulate_scale=0.9, randomness=0.12) as room:
    # gravel: "coarse grey gravel and pebble ground" was verified by embedding against
    # wall_textures_embeddings.npz -> it matches the library's ONE true gravel texture (0.591).
    # (The old draft's "gravel and stone path floor" matches a DRY STONE WALL — checked, not guessed.)
    room.place_walls(floor_texture="coarse grey gravel and pebble ground",
                     ceiling_texture="smooth white ceiling",
                     wall_texture="white painted wooden plank wall")

    # the nave: twin bench runs on the two long walls + the centre spine between them.
    # facing OMITTED on the wall runs -> the heuristic faces each bench into the room (library).
    room.place_on_left_wall_center(run_left)
    room.place_on_right_wall_center(run_right)
    room.place_on_center(spine)

    # the back "shed" end: the potting station, flanked by the two tall tropicals.
    room.place_on_back_wall_center(potting_station)
    room.place_on_back_left_corner(palm_l)
    room.place_on_back_right_corner(palm_r)

    room.place_door("front_wall", position="center")

    # THE GLASS ENVELOPE — deliberately in PHASE 1 (not 3) so the cheap layout build answers the
    # black-void question before any expensive dressing. See the header note.
    room.place_window_floor_to_ceiling("left_wall", curtain=None)
    room.place_window_floor_to_ceiling("right_wall", curtain=None)

    # FLOOR LIFE = the PLANT BEDS (phase 1: they are floor anchors, they size the room).
    # v1 dressed these slots with single specimens — one grow bag, one pot — which both left the
    # entrance reading as bare gravel AND made the room a florist_shop clone. Dense thickets in the
    # same four slots fix both at once: same slot count (the shell does not grow), far more green.
    # They also do the job the room-size vote was really asking for (0.88 -> 0.82 -> 0.7 was "too
    # empty", not "too big" — children_room: fill the floor before shrinking).
    room.place_on_front_left(plant_bed(12, cols=4))
    room.place_on_front_right(plant_bed(9, cols=3))
    room.place_on_left(plant_bed(8, cols=2))
    room.place_on_right(plant_bed(12, cols=4))
    # a third palm anchors the entrance; the grow bag keeps a bit of working-nursery mess in the aisle
    room.place_on_front(_fit_height(
        scene.AddAsset("a tall tropical potted palm plant", asset_id=_PALM_BIG), 1.6))

    if PHASE >= 2:
        room.place_on_back_left(scene.AddAsset("a green fabric grow bag with plants", asset_id=_GROWBAG))

    if PHASE >= 3:
        # the garden-tool board on the shed wall. It is genuinely FLAT (0.06 m deep) so it is a
        # legitimate place_on_wall_* hang — but it is a small mesh (0.50 m), so pre-scale it via
        # width= to read as a real tool board (wall-art-mount-height lesson).
        room.place_on_wall_back_center(scene.AddAsset(
            "a wooden garden tool board with a rake and spade", asset_id=_TOOLS, width=1.1))
        # Slim linear tubes over the benches (the plan's "slender linear task lighting"). SINGULAR
        # query + LOW density: count ~= density * area / footprint, and this is a ~50 m2 floor, so
        # 0.015 is the calibrated band (bookstore: 0.04 -> a 35-fixture starfield on 56 m2).
        room.add_lighting("a slim linear LED tube ceiling light", density=0.015, modulate_scale=1.4)

scene.export("greenhouse.blend")
