"""
Kitchen — "Navy Anchor Kitchen with Breakfast Bar" — the SET-PIECE recipe.

THE RULE THIS SCENE EXISTS TO ENCODE: a kitchen is built on ONE complete fitted kitchen UNIT SET,
never assembled from a run + range + hood + fridge. Assembling gives redundant cooktops, mismatched
styles and endless scale fights; the set gives a coherent kitchen in a single mesh. (kitchen.md
recipe A. The modular build in kitchen_v1.py converged VLM-clean and STILL took ~5 builds and a
bespoke hood-mounting mechanic to get there — this is the same room in one asset.)

Picking the set — use the component ANNOTATIONS, not a text query:
`IDSDL/datasets/assets/kitchen_components.json` hand-tags all 68 units in the `kitchen_set` pool
(the `KitchenUnitRetriever` pool) with `components` + `shape`. Rank by completeness and the choice
makes itself — only two units carry a near-complete kitchen. This one, `future/3c2bf09e`, is
10/11: base_cabinets, wall_cabinets, countertop, cooktop, oven, range_hood, sink, fridge,
dishwasher, microwave — U-shaped, navy. **Because the tags say the fridge/dishwasher/microwave/oven
are already integrated, this scene adds ZERO extra appliances.** That is the entire payoff of the
annotations: they tell you exactly what is left to add, which here is nothing.

THREE HARD PROHIBITIONS (why this program has an EMPTY phase 2):
1. NOTHING goes on, in, or around the SET. No `place_on_top`, no `place_inside`, no `place_rug`,
   and NO `add_lighting` anchored to it — the set is one mesh, so a pendant group anchored to it
   spreads fixtures across the entire U footprint and clips them into the cabinets. Placement onto
   a bundled set is a nightmare; don't attempt it.
2. A separate breakfast counter is allowed ONLY because this set has **no island** (the `island`
   tag is absent — only 3 units in the whole pool have one). Had we taken `future/7f4cdaf8` (the
   11/11 unit, which DOES bundle an island), a separate counter would be forbidden.
3. NOTHING goes on the breakfast counter either. Stools AT it are the point; smallwares ON it are
   not. The counter mesh was chosen BARE for this reason — the better-matching blue island
   (`future/a360edba`) has bowls and a jug modelled INTO the mesh.

So the whole "vibe layer" is FLOOR and WALL only: a runner rug, a floor plant, framed art, a
window, and the brass pendant anchored to the COUNTER group (never the set).

Scaling the set: BY HEIGHT, never by width. Room HEIGHT is hard-clamped to 3.0 m
(`RoomGroup.max_height`, groups.py:1287), and width-fitting a tall fitted run overshoots and pokes
the mesh THROUGH the ceiling. `obj.scale(w * H / h)` is the uniform scale-to-height idiom.

Layout: a set-piece hero (dental_office pattern) — the U-set wraps the back wall and IS the kitchen;
the breakfast counter sits parallel in front of it with its stool row on the room side (bar.md's
straight counter + aligned seating), leaving a clear work aisle between the two.

Phase-gated (IDSDL/phases.py). Phase 2 is intentionally empty — see above.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces (EMPTY here, by design) / 3 walls+mood

scene = SceneProgRoom("KitchenSet", seed=3)

# The hero. 10/11 components per kitchen_components.json -> no appliance gaps to fill.
KITCHEN_SET = "future/3c2bf09e-eb79-4a8f-a3f4-36446e9ea656"   # navy U, all appliances integrated
COUNTER = "hssd/f8b8235c6e241b3ef1922a7560736535d9c9219c"     # navy paneled island, BARE marble top
STOOL = "hssd/ce64089b08a3ba3e5a2c4c8e70c627c71c64cccc"       # rustic wood barstool, woven seat
PENDANT = "hssd/bf898898fd1d92bc217a8b8943d178589c2b316f"     # vintage brass dome pendant

scene.prefetch_assets([
    "a complete navy blue fitted kitchen unit with integrated appliances",
    "a navy blue kitchen island counter with a marble top",
    "a rustic wooden bar stool with a woven seat",
    "a warm brass dome pendant light",
    "a flat round LED flush mount ceiling light",
    "a patterned woven runner rug",
    "a tall leafy potted plant in a woven basket",
    "a framed botanical print in a light wood frame",
])

# =============================================================================
# PHASE 1 — the anchors
# =============================================================================

# --- the SET: the whole kitchen, in one mesh. Placed, and then left alone. -----
# Scale BY HEIGHT to 2.4 m (uniform): native 2.40w x 2.02h x 2.52d -> 2.85w x 3.00d, a real
# U-kitchen footprint whose wings project into the room. NEVER width-fit (ceiling punch-through).
kitchen = scene.AddAsset("a complete navy blue fitted kitchen unit with integrated appliances",
                         asset_id=KITCHEN_SET)
kitchen.scale(kitchen.get_width() * 2.4 / kitchen.get_height())

# --- the BREAKFAST COUNTER: the one thing the set does not provide -------------
# Legal only because this set has no `island` component (see the docstring). Its top stays BARE.
counter = scene.AddAsset("a navy blue kitchen island counter with a marble top", asset_id=COUNTER)
with scene.AroundGroup(sparsity=0.12, jitter=0.15) as bar:
    bar.set_anchor(counter)
    stools = 3 * scene.AddAsset("a rustic wooden bar stool with a woven seat", asset_id=STOOL)
    # place_rectilinear puts the whole row on ONE long side (the room side) and already gives them
    # a uniform straight facing square to the counter. Do NOT face() each stool at the counter —
    # that aims them at its centre POINT and fans the end stools inward (bar.md; and the kitchen_v1
    # build proved the resulting "rotate the stools by 180" VLM vote is noise to be declined).
    bar.place_rectilinear(longer_side1=stools)
    if PHASE >= 3:
        # The pendant hangs over the BAR, never over the set. Singular query + low density: a plural
        # query returns a mesh that is ALREADY a cluster of globes and add_lighting copies it N
        # times into a cloud (bar.md).
        bar.add_lighting("a warm brass dome pendant light", density=0.12)
        # the plan's runner, under the bar zone — floor treatment, not counter dressing
        bar.place_rug("a patterned woven runner rug", size=0.9)

# =============================================================================
# PHASE 2 — DELIBERATELY EMPTY.
# No place_on_top / place_inside anywhere in this scene. Not on the set (prohibition 1), not on
# the counter (prohibition 3). The set already models its own sink, hob and appliances; the
# counter is meant to read as a clean working bar. This is the inverted vibe layer — like
# operating_room, the room reads BETTER bare.
# =============================================================================

# =============================================================================
# the room
# =============================================================================
# modulate_scale=1.10 — NOT the "inflate the room to dodge overlaps" anti-pattern (there are no
# overlaps). The fitted SET is a 2.85 x 3.00 x 2.40 m block, and RoomGroup auto-sizes a shell that
# merely FITS its furniture — which for a hero this large means the set's wings reach both side
# walls and there is no circulation at all. Worse, it blinds the renders: the interior cameras sit
# on the room's centreline at 0.55 x ceiling ~= 1.65 m, just inside each wall, so a 2.4 m-tall
# hero that spans most of the room width puts TWO cameras INSIDE the cabinetry (phase-1 v1: the
# front view came back solid black and the left view was a wall of larder door). This is game_room's
# rule — the hero's own clearance sizes the room — applied to a set-piece: a full-height fitted
# kitchen needs a shell bigger than its own footprint, or you cannot see it, let alone cook in it.
# Calibrated by eye across phase-1 builds: 1.00 (auto) = two blinded cameras; 1.25 = every camera
# clear but a ring of dead floor (the VLM duly voted 0.8, i.e. straight back to the blind size);
# 1.10 = cameras clear AND a working aisle. The occupancy vote cannot see the camera problem, so
# this is one to settle with the eye and hold.
with scene.RoomGroup(modulate_scale=1.10, randomness=0.12) as room:
    # Plain colour + material words only — an accent clause recolours all four walls (classroom v1).
    # The navy is carried entirely by the SET and the counter (pin-for-palette), never by a texture.
    # Both "warm oak ..." and "medium brown oak ..." embed to a genuinely SALMON-PINK plank
    # texture — verified offline by resolving the string through WallTextureRetriever and opening
    # the matched texture.png (5 s, vs an 8-min build per guess: office_modern's rule). So this was
    # a MATCHING problem, not the renderer washing a correct match out (bakery's opposite case).
    # "dark brown hardwood floor" matches a real warm oak.
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="white plaster",
                     wall_texture="soft white painted plaster wall")

    room.place_on_back_wall_center(kitchen)      # the U wraps the back wall; omit facing (the
                                                 # wall heuristic already turns it into the room)
    room.place_on_center(bar, facing="front")    # counter parallel to the run, stools on the room side
    # The plant is a PHASE-1 floor anchor, not phase-3 decor: it occupies a side slot, and room size
    # is a CONSEQUENCE of slot occupancy — with only the set and the bar (both centre-column) the
    # shell had nothing pushing its width out. It also happens to be the plan's greenery.
    room.place_on_front_left_corner(
        scene.AddAsset("a tall leafy potted plant in a woven basket"), facing="back")
    # the door goes in at PHASE 1 — its auto-clearance shapes the floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # decor is WALL only (nothing may land on the set or the counter)
        room.place_on_wall_left_center(
            scene.AddAsset("a framed botanical print in a light wood frame"))
        # a modest punched pane, never a full-height glaze: an opening renders as a BLACK void
        # (no exterior environment), and a big pane = a wall of black (retail_store/exec_office).
        room.place_window_standard("right_wall", position="center",
                                   curtain="white linen roman shade")
        # a FLUSH fixture for the ambient fill, never a hanging chandelier (add_lighting caps a
        # fixture's height at 1.5 m but pins its origin at the ceiling, so a long-drop fixture
        # hangs into the room). density is a fixture COUNT that scales with FLOOR AREA — a small
        # room wants the bottom of the band (0.01-0.02).
        # modulate_scale=0.4: the fixture retrieval came back a ~1.2 m DRUM shade that dominated
        # the ceiling in every view. add_lighting takes no asset_id (corridor's lint), so the size
        # lever is modulate_scale — the third arg exists for exactly this.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.01,
                          modulate_scale=0.4)

scene.export("kitchen_set_v1.blend")
