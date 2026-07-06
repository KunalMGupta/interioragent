"""
Locker room — "Pro Locker Spine & Wet-Dry Flow" (planner target, tmp/lockerroom/plan/plan.png).

A premium fitness/team locker room. Cool-clinical palette with warm-wood accents: grey large-format
floor tile, white wall tile, dark metal lockers, oak benches, rolled white towels.

Zoning (a WIDE room; the long back/front walls do the heavy lifting, benches run down the middle):
  - back (long) wall  = the LOCKER SPINE: a continuous row of metal locker banks (the hero).
  - front (long) wall = the DRESSING/ENTRY wall: a row of towel-cubby units + the entry door.
  - centre aisle      = a row of oak benches running PARALLEL to the lockers (sit-to-change).
  - left (short) wall  = the GROOMING zone: two sink vanities + a mirror hung above them.
  - right (short) wall = the WET zone: a pair of glass shower stalls.

NOTE (layout lessons):
  1. A long bench ROW must NOT be dropped with `place_on_<side>` — that leaves it floating/diagonal
     in open floor and blows the room size up. Run it down the CENTRE with `place_on_center`, where
     GridGroup.place_row's left-right axis is already parallel to the long walls.
  2. Keep `modulate_scale=1.0`. The room auto-sizes to FIT the furniture; a value <1.0 (an
     occupancy-driven "tighten") shrinks the shell below the furniture footprint, so fixed-size rows
     overflow their slots and the solver can't undo it — the bench row punched into the grooming
     vanity and a corner item into the locker spine at 0.8. Fill a room with furniture, don't shrink
     the shell into it.
  3. Don't drop a free-standing prop into a CORNER already claimed by a full-width wall row (the
     locker spine fills the whole back wall, so a back-corner hamper overlaps it). Put it in a free
     wall slot instead (here: the wet-zone right_wall_center).
  4. Wall art stacks above its support and scales with room width, and nothing clamps it to the
     ceiling — a clock over the tall locker spine punched through the roof. RoomGroup now warns at
     compile (_warn_over_height); place such art over a LOW support (here the cubby wall) so it fits.

Phase 1: locker spine + centre bench row + cubby row + grooming vanities (floor anchors, room shape).
Phase 2: rolled towels on the cubbies + grooming + laundry bin + water cooler + downlights (details).
Phase 3: grooming mirror + glass shower stalls + door + wall clock (walls & decor).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("LockerRoom", seed=15)

# --- pinned assets (audited previews; see scenes/work/locker_room.md) ---
_LOCKERS = "future/e96b46b7-a9f5-4e2e-b1d7-0dfc670d5461"          # grey vented full-height metal locker bank
_BENCH   = "hssd/1ccdd93676483606fdf96f81d6111a7c0e3b1d9f"        # slatted oak bench, black legs
_CUBBY   = "hssd/c075ced257f48c753d22d3bd3400186d6de319da"        # 6-compartment wood cube (towel cubbies)
_VANITY  = "future/8275e724-5f49-4e38-a65f-6d007cd47985"          # sink vanity (mirror added Ph3)
_TOWELS  = "hssd/6ece1a15f0f508aab2371808d58eefa8420cf725"        # stack of rolled white towels
_COOLER  = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"        # freestanding water cooler
_MIRROR  = "hssd/fe6a04f91f6d8c9d44b6c1ec30350ae3b12c6ef0"        # large rectangular wall mirror
_SHOWER  = "hssd/b74cfc2ae648ddcf1375088e23d9643b7c5ed736"        # glass corner shower + fixture

# --- LOCKER SPINE: a continuous row of locker banks along the back long wall ---
lockers = 6 * scene.AddAsset("a bank of tall metal lockers", asset_id=_LOCKERS)
with scene.GridGroup(sparsity=0.02) as locker_spine:
    locker_spine.place_row(lockers)

# --- DRESSING wall: a row of towel-cubby units (towels stacked on top) on the front long wall ---
# Build ONE cubby-with-towels unit and duplicate it (identical, heavy on-top work runs once).
with scene.RelativeGroup() as cubby_unit:
    cubby_unit.set_anchor(scene.AddAsset("an open wooden cubby storage unit", asset_id=_CUBBY))
    cubby_unit.place_on_top(scene.AddAsset("a stack of rolled white towels", asset_id=_TOWELS, modulate_scale=0.7))
cubbies = 3 * cubby_unit
with scene.GridGroup(sparsity=0.15) as cubby_row:
    cubby_row.place_row(cubbies)

# --- CENTRE aisle: a row of oak benches running parallel to the lockers ---
# Keep the row shorter than the room so its ends stay clear of the short (grooming/wet) walls.
benches = 3 * scene.AddAsset("a wooden slat locker room bench", asset_id=_BENCH)
with scene.GridGroup(sparsity=0.5) as bench_row:
    bench_row.place_row(benches)

# --- GROOMING zone: a row of sink stations on the left short wall. Each station = a vanity with a
# mirror mounted on the wall behind it, SIZED TO THE VANITY (MirrorStationGroup; the plain
# place_on_wall_* mirror is capped to a wall-third and only covers one sink). Two stations => a
# mirror over BOTH vanities.
def grooming_station():
    with scene.MirrorStationGroup() as st:
        st.set_anchor(scene.AddAsset("a bathroom vanity with a sink", asset_id=_VANITY))
        st.place_mirror(scene.AddAsset("a large rectangular wall mirror", asset_id=_MIRROR))
    return st
grooming_stations = [grooming_station() for _ in range(2)]
with scene.GridGroup(sparsity=0.06) as grooming:
    grooming.place_row(grooming_stations)

# modulate_scale stays at 1.0: the room auto-sizes to FIT the furniture footprint. Shrinking it
# below 1.0 (as an occupancy-driven "tighten") packs fixed-size rows past their slots and forces
# overlaps the solver can't undo (a long bench row into the grooming wall; a corner item into the
# locker spine). Add furniture to fill a room, don't shrink the shell into it.
with scene.RoomGroup(modulate_scale=1.0, randomness=0.1) as room:
    room.place_walls(floor_texture="large format grey porcelain floor tiles",
                     ceiling_texture="white",
                     wall_texture="white ceramic wall tiles")
    # NOTE on facing: DON'T pass facing=<the wall's own name>. Every place_on_<wall>_* defaults
    # (via fill_facing_heuristic) to facing the OPPOSITE way — into the room — which is what a
    # locker/sink/cubby wants (its access side toward the room). Passing facing="back" on the back
    # wall etc. turns the asset to face the wall it stands against and denies access. Omit facing
    # and let the heuristic orient it inward; only override for a genuine non-default pose.
    # back (long) wall = the locker spine, flush, facing into the room (heuristic -> "front")
    room.place_on_back_wall_center(locker_spine)
    # centre aisle = benches, parallel to the lockers (place_row's axis already runs along width)
    room.place_on_center(bench_row)
    # front (long) wall = dressing cubbies (centre) + the entry door (right); cubbies face in ("back")
    room.place_on_front_wall_center(cubby_row)
    room.place_door("front_wall", position="right")
    # left (short) wall = the grooming row. A MirrorStationGroup builds its mirror on its +Z
    # (wall) side, so — unlike plain furniture — it takes facing=<the wall it sits on> so that
    # mirror side lands against the wall and the vanities face the room (same as the salon row).
    room.place_on_left_wall_center(grooming, facing="left")
    # right (short) wall = WET zone: a pair of glass shower stalls
    room.place_on_right_wall_left(scene.AddAsset("a glass walk-in shower stall", asset_id=_SHOWER))
    room.place_on_right_wall_right(scene.AddAsset("a glass walk-in shower stall", asset_id=_SHOWER))
    # amenities: a water cooler by the entry; a laundry hamper in the wet zone (a FREE wall slot,
    # not a corner already claimed by the full-width locker spine, which would overlap it).
    room.place_on_front_wall_left(scene.AddAsset("a freestanding water cooler dispenser", asset_id=_COOLER))
    room.place_on_right_wall_center(scene.AddAsset("a tall wicker laundry hamper basket"))
    # a wall clock over the dressing wall (low cubby support -> it clears the ceiling; over the
    # tall locker spine it stacked high enough to punch through the roof — see _warn_over_height).
    room.place_on_wall_front_center(scene.AddAsset("a large round wall clock"))
    # ceiling = a grid of recessed downlights (even, glare-free)
    room.add_lighting("a recessed ceiling downlight", density=0.06)

scene.export("locker_room.blend")
