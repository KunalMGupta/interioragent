"""
Kitchen v2 — "Navy Anchor Kitchen, open-plan" — the SET-PIECE recipe, CORNER-ALIGNED.

v1 shipped the fitted set at `place_on_back_wall_center`. It converged VLM-clean and it was WRONG:
a U-set centred on a wall projects BOTH of its wings into open air, so the kitchen reads as a
freestanding block dumped in the room rather than as cabinetry INSTALLED against the building.
(Kunal, 2026-07-13.) A fitted kitchen is joinery — every run of it that can touch a wall, must.

THE ALIGNMENT RULES (they follow from the SHAPE tag in kitchen_components.json):
  * L-shaped  -> the leg must lie ALONG a wall. Place the unit in the CORNER the leg points into:
                 leg on the right => back_RIGHT corner.
  * U-shaped  -> two runs can touch walls, never three. Place it in a CORNER (back run on one wall,
                 one wing along the adjoining wall). The remaining wing is then an exposed
                 PENINSULA, and a functional group must be placed BEYOND it — that is what turns
                 the exposed wing from "a mistake" into the open-plan divider it reads as.
  * straight  -> a wall centre can work, but a corner still reads better (joinery starts at a wall).
  * WINDOW    -> hang it on a wall OPPOSITE the unit's corner. Unit in the back-right corner =>
                 window on the LEFT wall: the daylight then rakes ACROSS the cabinetry instead of
                 backlighting it from behind.

Verified against the mesh, not the caption: rasterising `future/3c2bf09e`'s XZ footprint shows a
solid back run at z-min and two wings running to z-max (open side = +z = the room front, under the
default rotation). So pushing it into the back-right corner lands the back run on the back wall AND
the right wing flush along the right wall; the LEFT wing becomes the peninsula. The breakfast
counter goes BEYOND that left wing, which is the functional group the U's open side demands.

Free bonus: a corner op lands in the OUTERMOST grid column (compute_grid_dims), so the set no
longer straddles the room's centreline — which is where the interior cameras sit. v1 needed
modulate_scale=1.10 purely to stop the cameras rendering the inside of the cabinets (a solid-black
view the VLM loop reported as "no rescale / no rotation / no wall overlap"). Corner-aligning the
set fixes the composition and the cameras at once.

Everything else is v1's set-piece recipe, unchanged:
  1. ONE complete fitted kitchen UNIT (future/3c2bf09e, 10/11 components) — never assembled parts.
  2. NOTHING placed on / in / around the set. No place_on_top, place_inside, place_rug, and no
     add_lighting anchored to it.
  3. The separate breakfast counter is legal only because this set has no `island` component; and
     nothing goes on that counter either (its mesh was chosen BARE for exactly that reason).
  4. Gaps filled from the component annotations: this set integrates the fridge, dishwasher,
     microwave and oven, so ZERO extra appliances are added.
So phase 2 is deliberately EMPTY and the whole decor layer is FLOOR + WALL only.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces (EMPTY by design) / 3 walls+mood

scene = SceneProgRoom("KitchenSetV2", seed=3)

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
    "a patterned woven runner rug",
    "a tall leafy potted plant in a woven basket",
    "a framed botanical print in a light wood frame",
    "a light oak rectangular dining table",
    "a light wood classic dining chair",
])

# --- the SET: scaled BY HEIGHT (the ceiling is clamped to 3.0 m; width-fitting punches through it)
kitchen = scene.AddAsset("a complete navy blue fitted kitchen unit with integrated appliances",
                         asset_id=KITCHEN_SET)
kitchen.scale(kitchen.get_width() * 2.4 / kitchen.get_height())
# PIN IT. A corner op is NOT in WALL_FURNITURE_OPS, so unlike a place_on_<wall>_wall_* piece it is
# never re-pinned flush after the solve — and the GradSolver's exploration floor duly walked the set
# 0.44 m off the back wall on the first v2 build (the living_room_cozy drift, on a hero this time).
# is_static zeroes its gradient every step, so it stays exactly where the corner op put it: flush to
# both walls. It still EXERTS force on its neighbours (only its own grad is zeroed), so the bar and
# the plant are still pushed clear of it.
kitchen.is_static = True

# --- the BREAKFAST COUNTER: the functional group that sits BEYOND the U's exposed left wing ------
counter = scene.AddAsset("a navy blue kitchen island counter with a marble top", asset_id=COUNTER)
with scene.AroundGroup(sparsity=0.12, jitter=0.15) as bar:
    bar.set_anchor(counter)
    stools = 3 * scene.AddAsset("a rustic wooden bar stool with a woven seat", asset_id=STOOL)
    # one straight row on the far (room) side; place_rectilinear already gives them a uniform
    # facing square to the counter — do NOT face() each at the anchor (bar.md; it fans the ends).
    bar.place_rectilinear(longer_side1=stools)
    if PHASE >= 3:
        bar.add_lighting("a warm brass dome pendant light", density=0.12)   # on the BAR, not the set
        bar.place_rug("a patterned woven runner rug", size=0.9)

# --- the DINING zone: the second functional group of the open-plan layout --------------------
# The U's exposed left wing needs something to BE a divider between. Bar + dining make the wing read
# as a peninsula separating "cook" from "eat" — which is the whole point of corner-aligning a U.
# It also earns its keep geometrically: it is the front-row occupant that pushes the room's depth
# past twice the right wing's length, which is what finally frees the last interior camera (below).
with scene.AroundGroup(sparsity=0.05, jitter=0.15) as dining:
    table = scene.AddAsset("a light oak rectangular dining table", asset_id=TABLE, width=1.4)
    dining.set_anchor(table)
    chairs = 4 * scene.AddAsset("a light wood classic dining chair", asset_id=CHAIR)
    dining.place_rectilinear(longer_side1=chairs[:2], longer_side2=chairs[2:])

plant = scene.AddAsset("a tall leafy potted plant in a woven basket")

# modulate_scale=0.92 — and 0.90 is a HARD FLOOR, not a preference. The set is `is_static` and flush
# in the back-right corner, so shrinking the shell slides the walls TOWARD a fixed hero, and the
# interior cameras (centreline, ~1.65 m, just inside each wall) go back inside the cabinets:
#     front camera clears the set   <=>  W > 2 x set width  = 5.70 m
#     left  camera clears the wing  <=>  D > 2 x wing depth = 5.98 m
# At the VLM's requested 0.85 the room is 5.44 x 6.22 and the FRONT view goes solid black again.
# 0.92 -> 5.89 x 6.73: a real shrink with margin on both bounds. The occupancy vote cannot see
# cameras, so this bound has to be computed, not negotiated.
with scene.RoomGroup(modulate_scale=0.92, randomness=0.0) as room:
    # randomness=0: the corner ops are excluded from floor jitter anyway (FLOOR_SLOTS), but the
    # whole point of this version is precise wall alignment — don't let anything nudge it.
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="white plaster",
                     wall_texture="soft white painted plaster wall")

    # THE ALIGNMENT. A corner op is flush to BOTH walls by construction — it sets the location from
    # wall_deltas on both axes. But you MUST pass `facing` explicitly: omitting it does NOT mean
    # "no rotation". facing_to_rotation() raises on None, so the @placemethod heuristic fills it in,
    # and for a corner it chose "left" (-90 deg) — which spun the U to open sideways and put its back
    # run against the RIGHT wall (v2 build 1). facing="front" (rotation 0) is what keeps the back run
    # on the back wall with the open side toward the room; pushed into the right corner, the RIGHT
    # WING then runs flush ALONG the right wall. Two runs on two walls — the most a U can align.
    room.place_on_back_right_corner(kitchen, facing="front")

    # BEYOND the exposed left wing — the open-plan move. The peninsula now divides "kitchen" from
    # "seating" instead of floating in the middle of nowhere.
    room.place_on_center(bar, facing="front")

    # The dining zone in the FRONT row is load-bearing, not just decor. The U's right wing runs the
    # full depth of the right wall (y = 0 .. -2.99 m), and the left-wall view's camera sits near the
    # RIGHT wall at MID-depth — i.e. INSIDE that wing — unless the room is deeper than twice the
    # wing (D > ~5.98 m). A front-row occupant pushes the depth past that threshold and frees the
    # camera. Room size is a consequence of slot occupancy: use that lever, not modulate_scale
    # (which would inflate the width too, and the width is already right).
    room.place_on_front(dining, facing="back")
    room.place_on_back_left_corner(plant, facing="front")   # fills the bare back wall beside the U
    room.place_door("front_wall", position="center")

    if PHASE >= 3:
        # WINDOW OPPOSITE THE UNIT'S CORNER (rule 4): unit is back-RIGHT, so the window goes on the
        # LEFT wall — daylight rakes across the navy cabinetry instead of coming from behind it.
        room.place_window_standard("left_wall", position="center",
                                   curtain="white linen roman shade")
        room.place_on_wall_front_left(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        # add_lighting takes no asset_id (corridor's lint); modulate_scale is the size lever — the
        # retrieved flush fixture is a ~1.2 m drum otherwise.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01,
                          modulate_scale=0.4)

scene.export("kitchen_set_v2.blend")
