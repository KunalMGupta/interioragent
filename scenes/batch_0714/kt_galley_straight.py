"""Galley kitchen — "Straight-Set Galley with a Front Island" (KitchenIslandGroup mode "front").

The production exercise of KitchenIslandGroup's third mode: a STRAIGHT fitted set (the
raster classifies it "straight") takes the island parallel to the run — the classic galley —
with `min_aisle` guarding the working corridor between run and island. The U ("tip") and L
("pocket") modes have worked examples (kitchen_set_v3.py / kitchen_l_v1.py); this is the
straight one.

The set: `future/4253258a` — 8/11 components on the hand-tagged annotations
(kitchen_components.json), the most complete STRAIGHT run, and it INCLUDES the fridge (a
5/68 scarce tag). So NO separate appliances are added anywhere: the set is complete, and
kitchen.md rule 2 bans placing anything on/in/around it regardless.

Scaled BY HEIGHT to 2.2 m — never by width (the ceiling is clamped to 3.0 m and width-
fitting punches through it), and deliberately BELOW the 2.4 m of v3 because of the camera
bound: this run ends in a full-height fridge column, and a wall-flush run whose inner end is
TALL must satisfy `run_width <= W/2 - 0.3` (kitchen_l_v1: at nominal margins the front view
rendered SOLID BLACK — the camera needs lateral clearance it cannot see over). Height 2.2 m
keeps run_width short enough that the auto-sized shell clears the bound without inflating
the room. Verify all four views by eye anyway — no VLM signal sees a blinded camera.

Layout:
- BACK-RIGHT corner : the whole kitchen zone (set + island + stools) as ONE corner-aligned
                      block. `facing="front"` is MANDATORY (omitting it does NOT mean "no
                      rotation" — the heuristic fills in "left"/-90 and spins the run), and
                      `is_static` pins it (corner ops are never re-pinned flush; the
                      exploration floor walked v2's set 0.44 m off the wall).
- FRONT             : dining table + 2 chairs — the open-plan zone, and the occupant that
                      keeps the front row from collapsing against the island's aisle.
- LEFT wall         : the window (phase 3) — OPPOSITE the set's corner, so daylight rakes
                      across the cabinetry instead of backlighting it.
- FRONT wall, right : the door.

Phase 2 is deliberately EMPTY (the set rule): nothing on the set, nothing on the island
counter. The vibe layer is FLOOR + WALL only — operating_room's inverted vibe.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 EMPTY by design / 3 walls+mood

scene = SceneProgRoom("KtGalleyStraight", seed=44)

KITCHEN_SET = "future/4253258a-c066-4ccd-a126-f67b1cead6a5"  # straight run, 8/11 comps INCL fridge
COUNTER = "hssd/f8b8235c6e241b3ef1922a7560736535d9c9219c"    # navy paneled island, BARE marble top
                                                             # (the best-matching alternative has
                                                             # bowls MODELLED INTO the mesh — the
                                                             # no-smallwares rule by proxy)
STOOL = "hssd/ce64089b08a3ba3e5a2c4c8e70c627c71c64cccc"      # rustic wood barstool, woven seat
TABLE = "future/9ff76d8d-af20-493d-a17c-a4aaaa94114a"        # light oak dining table, BARE top
CHAIR = "hssd/24fd37914321b915b9503d25add09332900a8d61"      # light wood classic dining chair

scene.prefetch_assets([
    "a complete modern fitted kitchen unit with integrated appliances",
    "a navy blue kitchen island counter with a marble top",
    "a rustic wooden bar stool with a woven seat",
    "a warm brass dome pendant light",
    "a flat round LED flush mount ceiling light",
    "a light oak rectangular dining table",
    "a light wood classic dining chair",
    "a tall leafy potted plant in a woven basket",
    "a framed botanical print in a light wood frame",
    # rework 2026-07-14 (Kunal: too sparse / uninteresting): CAMERA-SAFE fill only — a full 4-seat
    # nook on a rug, a pendant, and a wall-art pair (a console blinds the camera; see kitchen_l).
    "a flat woven jute area rug in warm cream tones",
])

# --- the SET: scaled BY HEIGHT (2.2 m — see the camera-bound rationale in the docstring) --------
kitchen = scene.AddAsset("a complete modern fitted kitchen unit with integrated appliances",
                         asset_id=KITCHEN_SET)
kitchen.scale(kitchen.get_width() * 2.2 / kitchen.get_height())

# --- the ISLAND UNIT: bare-top counter + its own pendant, one rigid piece -----------------------
# The pendant rides INSIDE the island unit (never anchored to the set): lights are is_light
# children skipped by every AABB, so it lands over the counter wherever the raster puts it,
# while the aisle math sees only the counter. density=0.0 -> exactly one pendant.
counter = scene.AddAsset("a navy blue kitchen island counter with a marble top", asset_id=COUNTER)
with scene.AroundGroup(sparsity=0.0, jitter=0.0) as island_unit:
    island_unit.set_anchor(counter)
    if PHASE >= 3:
        island_unit.add_lighting("a warm brass dome pendant light", density=0.0)

# --- the KITCHEN ZONE: set + galley island + stools, ONE corner-aligned block -------------------
with scene.KitchenIslandGroup() as kz:
    kz.set_anchor(kitchen)
    # straight set -> raster classifies "straight" -> mode auto = "front": the island lies
    # PARALLEL to the run with a min_aisle working corridor — the galley. Island + stools are
    # floor mass -> phase 1 ALWAYS (the floor-mass gating rule).
    kz.place_island(island_unit)
    kz.place_stools(2 * scene.AddAsset("a rustic wooden bar stool with a woven seat",
                                       asset_id=STOOL))
# PIN THE BLOCK: corner ops are never re-pinned flush after the solve (not in
# WALL_FURNITURE_OPS) and the exploration floor drifts unpinned heroes off their wall.
kz.is_static = True

# --- the DINING zone: table + 4 chairs at the front-left (the open-plan second zone) ------------
# Rework 2026-07-14: a FULL four-seat nook (was two) grounded on a jute rug (phase 2) with a brass
# pendant over it (phase 3, density=0 -> exactly one) — the two-chair table read thin in the open
# plan. These are CAMERA-SAFE fills (a rug claims no slot, a pendant is an AABB-skipped light). A
# first attempt ALSO put a serving console on the front wall; kitchen_l proved that blinds the
# back camera (a console is FLOOR MASS in a set-piece kitchen — kitchen.md's bound), so it's out.
with scene.AroundGroup(sparsity=0.05, jitter=0.15) as dining:
    dining.set_anchor(scene.AddAsset("a light oak rectangular dining table", asset_id=TABLE,
                                     width=1.4))
    chairs = 4 * scene.AddAsset("a light wood classic dining chair", asset_id=CHAIR)
    # one chair per long side... now two per long side, uniform straight facing — never per-chair
    dining.place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])
    if PHASE >= 2:
        dining.place_rug("a flat woven jute area rug in warm cream tones", size=0.9)
    if PHASE >= 3:
        dining.add_lighting("a warm brass dome pendant light", density=0.0)

plant = scene.AddAsset("a tall leafy potted plant in a woven basket")

with scene.RoomGroup(modulate_scale=1.0, randomness=0.0) as room:
    room.place_walls(floor_texture="dark brown hardwood floor",   # verified warm-oak match ("warm
                     ceiling_texture="white plaster",             # oak" strings embed to a salmon
                     wall_texture="soft white painted plaster wall")  # plank — kitchen.md)

    # THE ALIGNMENT: one corner op moves the whole block flush to both walls. facing MANDATORY.
    room.place_on_back_right_corner(kz, facing="front")

    room.place_on_front_left(dining, facing="back")
    room.place_on_back_left_corner(plant, facing="front")   # fills the bare wall beside the run
    room.place_door("front_wall", position="right")

    # PHASE 2: nothing on the SET or the island (kitchen.md rule 2) — but the nook RUG is dressed
    # here; that rule guards the fitted set, not the whole room.

    if PHASE >= 3:
        # window OPPOSITE the set's corner: back-right corner -> LEFT wall
        room.place_window_standard("left_wall", position="center",
                                   curtain="white linen roman shade")
        # wall art breaks up the bare white walls WITHOUT adding floor mass (camera-safe interest):
        # a botanical PAIR on the front wall (centre + left) instead of one lone print
        room.place_on_wall_front_center(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        room.place_on_wall_front_left(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        # flush room lighting: density 0.015 with the fixture ENLARGED so count stays low —
        # a tiny flush disc at this density tiles a starfield (kitchen_l_v1, seed-dependent)
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.015,
                          modulate_scale=2.0)

scene.export("kt_galley_straight.blend")
