"""
Bar — "Moody Luxe Bar & Lounge" (planner-driven cocktail bar).

Plan (Phase 0): a long, front-facing bar line as the room's central social anchor; a row of stools
along its front; a tall back-bar lined with bottles/glassware behind it as the focal wall; warm globe
pendants over the bar; a couple of small velvet lounge nooks in the corners. Palette: charcoal walls,
espresso wood, brass, ivory marble, dark herringbone floor. Mood: sophisticated, evening-ready.

Room shape: WIDE + SHALLOW — the long bar run (counter + back-bar) goes on the long BACK wall; the
short walls stay light (mirror, art). Stools sit on the customer (front) side of the counter, facing it;
the lounge nooks fill the front half, facing back toward the bar.

Build state: Phase 1 anchors (counter + stools + back-bar) VALIDATED; Phase 2 lounge nooks + rugs;
Phase 3 mirror/art/greenery/door + layered pendant lighting.

LIGHTING LESSON: `add_lighting(desc, density)` copies the retrieved light mesh N times, where
N = 1 + (max_lights-1)*density. Query a SINGULAR pendant ("a warm brass globe pendant light") — a
plural/"row of" query returns a mesh that is ALREADY a cluster of globes, so N copies of it = a cloud
of ~30 (the Phase-1 bug). density~0.5 over the 3.6 m counter gives a clean row of ~5-6 single globes.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("BarLounge", seed=26)

# Warm the retrieval cache for every asset the finished scene wants; a missed/extra entry is harmless.
scene.prefetch_assets([
    "a long vintage solid wood bar counter with a paneled front",
    "a tall tufted leather bar stool with a backrest",
    "a tall wooden back-bar cabinet with glass doors displaying liquor bottles",
    "a warm brass globe pendant light",
    "a dark green velvet tub lounge chair",
    "a small round marble cocktail table with a brass pedestal base",
    "a small brass pendant light",
    "a large gold-framed vintage mirror",
    "a framed vintage cocktail print in a brass frame",
    "a large potted areca palm in a brass planter",
    "a dark patterned wool area rug",
])

# --- Phase 1: the bar line. Counter is the hero anchor; stools row along its FRONT (customer) side. ---
# width=3.6 lengthens the counter into a proper long bar (non-uniform, keeps a realistic low height).
counter = scene.AddAsset("a long vintage solid wood bar counter with a paneled front",
                         asset_id="future/dd75f4ed-53e0-463b-8861-5c6206bdb847", width=3.6)

with scene.AroundGroup(sparsity=0.15, jitter=0.25) as bar_group:
    bar_group.set_anchor(counter)
    stools = 5 * scene.AddAsset("a tall tufted leather bar stool with a backrest",
                                asset_id="future/84e8c226-6030-4a8f-b4d7-3784e949428c")
    # place_rectilinear already gives a uniform STRAIGHT facing (all rotated anchor-180 -> parallel,
    # facing the bar). Keep that default: an explicit face(toward=counter) would aim each stool at the
    # counter's centre point and fan the end stools inward. We want them all looking straight.
    bar_group.place_rectilinear(longer_side1=stools)   # a single row on one long side
    # warm globe pendants over the bar (SINGULAR query -> one globe per copy). Low density: the group
    # footprint includes the stool depth, so a higher count spreads the globes forward into the room as
    # a cloud; ~0.2 keeps a tight cluster of ~4 over the counter.
    bar_group.add_lighting("a warm brass globe pendant light", density=0.2)

# --- The focal back-bar: a tall bottle-display cabinet against the back wall, behind the counter. ---
backbar = scene.AddAsset("a tall wooden back-bar cabinet with glass doors displaying liquor bottles",
                         asset_id="future/f92b65d2-a2d3-4430-a5cb-34a7b5bce7f3", width=2.6)

# --- Phase 2: an intimate lounge nook (round marble 2-top + a pair of velvet tub chairs + rug + a small
# pendant). Build ONE composed unit, then duplicate with 2*nook so both nooks are identical. ---
with scene.AroundGroup(sparsity=0.3, jitter=0.4) as nook:
    ctable = scene.AddAsset("a small round marble cocktail table with a brass pedestal base")
    nook.set_anchor(ctable)
    nook.place_circle(2 * scene.AddAsset("a dark green velvet tub lounge chair"))
    nook.place_rug("a dark patterned wool area rug", size=1.0)
    nook.add_lighting("a small brass pendant light", density=0)   # single pendant over the 2-top
nook_l, nook_r = 2 * nook

# modulate_scale=0.85 = final-phase room shrink (RoomProportions asked 0.8; a bar keeps some open floor).
with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:
    room.place_walls(floor_texture="dark walnut herringbone wood",
                     ceiling_texture="charcoal", wall_texture="deep charcoal")
    # back (long) wall: the bar line — focal back-bar with the counter+stools in front of it
    room.place_on_back_wall_center(backbar)
    room.place_on_back(bar_group, facing="front")
    # keep the space in front of the back-bar ("cellar") somewhat free -> a bartender/service aisle
    # between it and the counter (manual gradient constraint; pushes floor objects out of the zone).
    room.add_clearance(backbar, distance=1.5, dir="front")
    # front half: the two lounge nooks, facing back toward the bar
    room.place_on_front_left(nook_l, facing="back")
    room.place_on_front_right(nook_r, facing="back")
    # Phase 3 — short walls stay light: a large gold mirror (left) + a framed cocktail print (right)
    room.place_on_wall_left_center(scene.AddAsset("a large gold-framed vintage mirror"))
    room.place_on_wall_right_center(scene.AddAsset("a framed vintage cocktail print in a brass frame"))
    # greenery softening the back-left corner; entrance on the front wall (between the nooks)
    room.place_on_back_left_corner(scene.AddAsset("a large potted areca palm in a brass planter"))
    room.place_door("front_wall", position="center")

scene.export("bar_lounge.blend")
