"""Locker room — "Pro Locker Spine & Wet-Dry Flow" (planner target, tmp/lockerroom/plan/plan.png).

Planner target: a premium fitness/team locker room. Cool-clinical palette with warm-wood accents —
grey large-format floor tile, white wall tile, dark metal lockers, oak benches, rolled white towels.

Layout — LONG ROWS, FLUSH-ON-WALL or DOWN-THE-CENTRE (a WIDE corridor room; the two long walls do
the heavy lifting and the benches run down the middle). A long row has exactly TWO correct homes:
flush on a wall, or down the centre. `place_on_<side>` leaves it floating diagonally across open
floor and balloons the auto-sized shell (14x10 m vs the intended 11x5) — that was the first build:
- BACK wall  (long) : the LOCKER SPINE — a continuous row of metal locker banks. The hero.
- FRONT wall (long) : the DRESSING/ENTRY wall — a row of towel-cubby units + the entry door, so the
                      two long walls carry the load and the room comes out wide and shallow.
- CENTRE            : the aisle — a row of oak benches running PARALLEL to the lockers. GridGroup's
                      place_row lays items along the room's WIDTH, so on place_on_center its axis is
                      already right: sit-to-change, no face() fiddling.
- LEFT wall  (short): the GROOMING zone — two sink vanities, each with its own mirror above it.
- RIGHT wall (short): the WET zone — a pair of glass shower stalls, plus the laundry hamper in the
                      free centre slot (NOT a back corner: the full-width locker spine owns those).

Identity comes from the SPINE plus the rolled white towels. Six locker banks in an unbroken line is
the one image that says "locker room"; the towels on the cubbies are what make it read spa/pro
rather than institutional. modulate_scale stays at 1.0 — see the note above the RoomGroup.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/locker_room_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the surfaces (towels, amenities); phase 3 adds
the wall decor and the lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("LockerRoom", seed=15)

# ---- pinned assets (audited previews; see skills/examples/locker_room.md) ------------------------
LOCKERS = "future/e96b46b7-a9f5-4e2e-b1d7-0dfc670d5461"    # grey vented FULL-HEIGHT metal locker bank.
                                                           # Reads as a real locker; the black 3-door
                                                           # 902f9b5b has furniture-like tapered legs.
BENCH   = "hssd/1ccdd93676483606fdf96f81d6111a7c0e3b1d9f"  # slatted oak top, black legs
CUBBY   = "hssd/c075ced257f48c753d22d3bd3400186d6de319da"  # 6-compartment oak cube (towel cubbies)
VANITY  = "future/8275e724-5f49-4e38-a65f-6d007cd47985"    # sink cabinet — ships with NO mirror, so
                                                           # the station hangs one itself
TOWELS  = "hssd/6ece1a15f0f508aab2371808d58eefa8420cf725"  # stack of rolled white towels — the
                                                           # "premium" cue
COOLER  = "hssd/b77968f3bfaa85fec68e60f7d559967e7e2b9b23"  # freestanding water cooler
MIRROR  = "hssd/fe6a04f91f6d8c9d44b6c1ec30350ae3b12c6ef0"  # large rectangular wall mirror
SHOWER  = "hssd/b74cfc2ae648ddcf1375088e23d9643b7c5ed736"  # glass corner panel + fixture (reads
                                                           # faintly — an accent, not a hero)

# ---- LOCKER SPINE: a continuous row of locker banks along the back long wall -----------------
lockers = 6 * scene.AddAsset("a bank of tall metal lockers", asset_id=LOCKERS)
with scene.GridGroup(sparsity=0.02) as locker_spine:
    locker_spine.place_row(lockers)

# ---- DRESSING wall: a row of towel-cubby units (towels stacked on top) on the front long wall -
# Build ONE cubby-with-towels unit and duplicate it (identical, and the heavy on-top work runs once).
# place_on_top parents the towels onto the anchor, so they survive the row AND the flush-on-wall
# placement intact — which is why the gate sits INSIDE the `with`, not around it.
with scene.RelativeGroup() as cubby_unit:
    cubby_unit.set_anchor(scene.AddAsset("an open wooden cubby storage unit", asset_id=CUBBY))
    if PHASE >= 2:
        cubby_unit.place_on_top(scene.AddAsset("a stack of rolled white towels", asset_id=TOWELS,
                                               modulate_scale=0.7))
cubbies = 3 * cubby_unit
with scene.GridGroup(sparsity=0.15) as cubby_row:
    cubby_row.place_row(cubbies)

# ---- CENTRE aisle: a row of oak benches running parallel to the lockers ----------------------
# Keep the row shorter than the room so its ends stay clear of the short (grooming/wet) walls.
benches = 3 * scene.AddAsset("a wooden slat locker room bench", asset_id=BENCH)
with scene.GridGroup(sparsity=0.5) as bench_row:
    bench_row.place_row(benches)

# ---- GROOMING zone: a row of sink stations on the left short wall ----------------------------
# Each station = a vanity with a mirror mounted on the wall behind it, SIZED TO THE VANITY
# (MirrorStationGroup; a plain place_on_wall_* mirror is capped to a wall-third and would cover only
# ONE sink). Two stations => a mirror over BOTH vanities.
# The mirror is UNGATED: it is not wall decor, it is the station — place_mirror() is REQUIRED before
# compile, and its auto-fit under the ceiling is exactly what phase 1 exists to check.
def grooming_station():
    with scene.MirrorStationGroup() as st:
        st.set_anchor(scene.AddAsset("a bathroom vanity with a sink", asset_id=VANITY))
        st.place_mirror(scene.AddAsset("a large rectangular wall mirror", asset_id=MIRROR))
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
    # front (long) wall = dressing cubbies (centre) + the entry door (right)
    room.place_on_front_wall_center(cubby_row)
    # the door stays in PHASE 1: its automatic clearance shapes the floor solve
    room.place_door("front_wall", position="right")
    # left (short) wall = the grooming row. A MirrorStationGroup builds its mirror on its +Z
    # (wall) side, so — unlike plain furniture — it takes facing=<the wall it sits on> so that
    # mirror side lands against the wall and the vanities face the room (same as the salon row).
    room.place_on_left_wall_center(grooming, facing="left")

    if PHASE >= 2:
        # amenities: a water cooler by the entry; a laundry hamper in the wet zone — a FREE wall
        # slot, NOT a corner already claimed by the full-width locker spine, which would overlap it
        # (a corner item vs a full-wall row has nowhere to go on either axis).
        room.place_on_front_wall_left(scene.AddAsset("a freestanding water cooler dispenser",
                                                    asset_id=COOLER))
        room.place_on_right_wall_center(scene.AddAsset("a tall wicker laundry hamper basket"))

    if PHASE >= 3:
        # right (short) wall = WET zone: a pair of glass shower stalls
        room.place_on_right_wall_left(scene.AddAsset("a glass walk-in shower stall", asset_id=SHOWER))
        room.place_on_right_wall_right(scene.AddAsset("a glass walk-in shower stall", asset_id=SHOWER))
        # a wall clock over the dressing wall (a LOW cubby support -> it clears the ceiling; over the
        # tall locker spine it stacked high enough to punch through the roof — see _warn_over_height,
        # which now warns at compile: wall art scales with room WIDTH and nothing clamps it to HEIGHT).
        room.place_on_wall_front_center(scene.AddAsset("a large round wall clock"))
        # ceiling = a grid of recessed downlights (even, glare-free)
        room.add_lighting("a recessed ceiling downlight", density=0.06)

scene.export("locker_room_v1.blend")
