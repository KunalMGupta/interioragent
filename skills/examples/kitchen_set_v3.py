"""
Kitchen v3 — "Navy Anchor Kitchen, open-plan" with an ATTACHED peninsula (KitchenIslandGroup).

v2 proved the corner-aligned fitted set; its one remaining compositional lie was the breakfast
counter FLOATING at place_on_center — a real U kitchen doesn't park its island in the middle of
the room, it attaches it. (Kunal, 2026-07-14, with the layout-ideas reference sheet: for a
U-shaped kitchen the island attaches at the FRONTAL TIP of whichever wing is LONGER, closing the
mouth into a covered cook zone with ONE walk-in entry gap at the other wing.)

That placement is not expressible with the existing verbs (every place_* is AABB-relative, and
the mouth of a U is INSIDE the set's AABB), so this scene is the debut of
`scene.KitchenIslandGroup()` (IDSDL/groups_extra.py): it rasterises the set's REAL footprint from
the mesh (surface-sampled, base-height band), classifies U/L/straight, measures both wings, and
- attaches the island flush with the longer wing's frontal tip, across the mouth   (mode "tip")
- guards the entry gap (min_entry=0.9 m) by shrinking the island if it would seal the mouth
- seats the stools in a straight row on the island's OUTWARD face, dropping any that don't fit.
The analysis (ASCII raster + wing lengths + chosen attachment) prints at compile — read it.

For `future/3c2bf09e` the raster reads: base run at -z, wings -x 2.49 m / +x 2.99 m -> attach at
the +x (RIGHT) wing, entry gap at -x. In the back-right corner that is exactly right: the right
wing lies along the right wall, the peninsula grows from its tip across the mouth, and the entry
gap opens toward the ROOM (the left/open side). The mouth is only 1.56 m, so the island shrinks
to ~0.7 m and seats ONE stool — that is the honest geometry of this narrow U, not a bug.

The pendant rides INSIDE the island unit: the island passed to place_island is a small
AroundGroup (counter + add_lighting), because lights are is_light children (skipped by AABBs)
that move rigidly with their group — so the pendant lands over the counter wherever the analysis
puts it. add_lighting still NEVER anchors to the set itself.

Everything else is v2 unchanged (one complete set, nothing on/in it, phase 2 EMPTY, corner
alignment + is_static, window opposite the corner, dining in the front row for the camera depth
bound).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces (EMPTY by design) / 3 walls+mood

scene = SceneProgRoom("KitchenSetV3", seed=3)

KITCHEN_SET = "future/3c2bf09e-eb79-4a8f-a3f4-36446e9ea656"   # navy U, all appliances integrated
COUNTER = "hssd/f8b8235c6e241b3ef1922a7560736535d9c9219c"     # navy paneled island, BARE marble top
STOOL = "hssd/ce64089b08a3ba3e5a2c4c8e70c627c71c64cccc"       # rustic wood barstool, woven seat
TABLE = "future/9ff76d8d-af20-493d-a17c-a4aaaa94114a"         # light oak dining table, BARE top
CHAIR = "hssd/24fd37914321b915b9503d25add09332900a8d61"       # light wood classic dining chair

scene.prefetch_assets([
    "a complete navy blue fitted kitchen unit with integrated appliances",
    "a navy blue kitchen island counter with a marble top",
    "a rustic wooden bar stool with a woven seat",
    "a warm brass dome pendant light",
    "a flat round LED flush mount ceiling light",
    "a tall leafy potted plant in a woven basket",
    "a framed botanical print in a light wood frame",
    "a light oak rectangular dining table",
    "a light wood classic dining chair",
])

# --- the SET: scaled BY HEIGHT (the ceiling is clamped to 3.0 m; width-fitting punches through it)
kitchen = scene.AddAsset("a complete navy blue fitted kitchen unit with integrated appliances",
                         asset_id=KITCHEN_SET)
kitchen.scale(kitchen.get_width() * 2.4 / kitchen.get_height())

# --- the ISLAND UNIT: counter + its pendant, one rigid piece for place_island -------------------
# The pendant is added HERE (not on the set — never on the set) so it travels with the counter to
# wherever the footprint analysis attaches it. Lights don't count toward the unit's AABB, so the
# entry-gap math below sees only the counter.
counter = scene.AddAsset("a navy blue kitchen island counter with a marble top", asset_id=COUNTER)
with scene.AroundGroup(sparsity=0.0, jitter=0.0) as island_unit:
    island_unit.set_anchor(counter)
    if PHASE >= 3:
        island_unit.add_lighting("a warm brass dome pendant light", density=0.0)  # exactly one

# --- the KITCHEN ZONE: set + attached peninsula + stool, ONE rigid corner-aligned block ---------
with scene.KitchenIslandGroup() as kz:
    kz.set_anchor(kitchen)
    # mode/wing auto: the raster classifies U and attaches at the LONGER (+x) wing tip. The
    # island is floor mass -> phase 1 ALWAYS (the floor-mass gating rule): gating it would
    # shrink the phase-1 shell and fake overlaps.
    kz.place_island(island_unit)
    kz.place_stools(2 * scene.AddAsset("a rustic wooden bar stool with a woven seat",
                                       asset_id=STOOL))
# PIN THE WHOLE BLOCK. Corner ops are never re-pinned flush after the solve (not in
# WALL_FURNITURE_OPS), and the exploration floor walked v2's set 0.44 m off the back wall until
# is_static zeroed its gradient. The group still exerts force on its neighbours.
kz.is_static = True

# --- the DINING zone: the front-row functional group of the open-plan layout --------------------
# Still load-bearing geometrically: the U's right wing runs the full 3 m depth of the right wall,
# and the left-wall camera clears it only when room depth > ~2x the wing. A front-row occupant is
# the clean lever for that depth (not modulate_scale, which would inflate the width too).
with scene.AroundGroup(sparsity=0.05, jitter=0.15) as dining:
    table = scene.AddAsset("a light oak rectangular dining table", asset_id=TABLE, width=1.4)
    dining.set_anchor(table)
    chairs = 4 * scene.AddAsset("a light wood classic dining chair", asset_id=CHAIR)
    dining.place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])

plant = scene.AddAsset("a tall leafy potted plant in a woven basket")

# modulate_scale=0.92 with 0.90 the HARD camera floor, inherited from v2 (W > 5.70 m for the front
# camera, D > 5.98 m for the left one). The attached peninsula + stool deepen the block by ~0.5 m,
# which only pushes the auto-size FURTHER past the depth bound — verify all four views by eye
# anyway (no VLM signal sees a blinded camera).
with scene.RoomGroup(modulate_scale=0.92, randomness=0.0) as room:
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="white plaster",
                     wall_texture="soft white painted plaster wall")

    # THE ALIGNMENT (v2's rules, now applied to the composed block): flush to both walls, facing
    # MANDATORY (omitting it does not mean "no rotation" — the heuristic fills in "left" and spins
    # the U sideways). The group's combined AABB corner-aligns exactly like the bare set: back run
    # on the back wall, right wing flush along the right wall, peninsula + entry gap toward the room.
    room.place_on_back_right_corner(kz, facing="front")

    room.place_on_front(dining, facing="back")
    room.place_on_back_left_corner(plant, facing="front")   # fills the bare back wall beside the U
    room.place_door("front_wall", position="center")

    if PHASE >= 3:
        # WINDOW OPPOSITE THE UNIT'S CORNER: unit back-right -> window LEFT, daylight rakes across
        # the navy cabinetry instead of backlighting it.
        room.place_window_standard("left_wall", position="center",
                                   curtain="white linen roman shade")
        room.place_on_wall_front_left(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01,
                          modulate_scale=0.4)

scene.export("kitchen_set_v3.blend")
