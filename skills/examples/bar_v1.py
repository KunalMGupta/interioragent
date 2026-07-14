"""Bar — "Moody Luxe Bar & Lounge" (planner-driven cocktail bar).

Planner target: a long, front-facing bar line as the room's central social anchor; a row of stools
along its front; a tall back-bar lined with bottles/glassware behind it as the focal wall; warm globe
pendants over the bar; a couple of small velvet lounge nooks in the corners. Palette: charcoal walls,
espresso wood, brass, ivory marble, dark herringbone floor. Mood: sophisticated, evening-ready.

Layout — WIDE + SHALLOW, one LONG RUN on the long wall (the archetypal bar shape):
- BACK wall  : the whole BAR STATION as ONE rigid unit — back-bar cabinet flush on the wall, then a
               baked-in service aisle, then the counter with its stool row. Composed with
               RelativeGroup.place_on_back rather than placed as two separate pieces, because that
               is the only way to GUARANTEE the bartender aisle (see bar.md).
- LEFT wall  : a large gold-framed mirror. The short walls stay LIGHT — the long run already carries
               the room, so hanging furniture on the short walls would crowd the circulation.
- RIGHT wall : a framed cocktail print. Same reason: decor only.
- CENTRE     : deliberately OPEN — the aisle between the bar line and the lounge is the circulation
               spine of a bar; a bar that solves to a full floor reads like a furniture showroom.
- FRONT      : the lounge half — two identical velvet nooks (built once, duplicated), both facing
               BACK toward the bar so the room has one direction of attention. The door sits on the
               front wall between them.

Identity comes from the bar LINE reading as a serving bar: a lengthened counter (width=3.6, NOT a
uniform scale, which would make it absurdly tall), a straight uniform row of stools on the customer
side, and a back-bar cabinet that already ships loaded with glassware — so nothing needs to be
place_on_top'd onto it.

LIGHTING LESSON: `add_lighting(desc, density)` copies the retrieved light mesh N times, where
N = 1 + (max_lights-1)*density. Query a SINGULAR pendant ("a warm brass globe pendant light") — a
plural/"row of" query returns a mesh that is ALREADY a cluster of globes, so N copies of it = a cloud
of ~30 (the Phase-1 bug). density~0.2 over the counter gives a tight cluster of ~4-6 single globes.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/bar_v1.py --phase 1` builds only the
floor layout (~1-2 min); phase 2 dresses the floor (rugs, greenery); phase 3 adds the wall decor and
the layered pendant lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BarLounge", seed=26)

# ---- pinned assets (browsed + eyeballed; the hero fixtures ARE the scene, so none are left to a
#      cold NL query) --------------------------------------------------------------------------
COUNTER = "future/dd75f4ed-53e0-463b-8861-5c6206bdb847"  # vintage paneled front — reads
                                                         # unmistakably as a serving bar
STOOL   = "future/84e8c226-6030-4a8f-b4d7-3784e949428c"  # tufted leather WITH a backrest = luxe
BACKBAR = "future/f92b65d2-a2d3-4430-a5cb-34a7b5bce7f3"  # tall glass-door cabinet ALREADY displaying
                                                         # glassware — a self-contained focal wall,
                                                         # so no fiddly place_on_top bottle clusters.
                                                         # (It renders dusty-mauve, not espresso; swap
                                                         # the id if a stricter palette is wanted.)

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

# --- the bar line. Counter is the hero anchor; stools row along its FRONT (customer) side. ---
# width=3.6 lengthens the counter into a proper long bar (non-uniform, keeps a realistic low height).
counter = scene.AddAsset("a long vintage solid wood bar counter with a paneled front",
                         asset_id=COUNTER, width=3.6)

with scene.AroundGroup(sparsity=0.15, jitter=0.25) as bar_group:
    bar_group.set_anchor(counter)
    stools = 5 * scene.AddAsset("a tall tufted leather bar stool with a backrest",
                                asset_id=STOOL)
    # place_rectilinear already gives a uniform STRAIGHT facing (all rotated anchor-180 -> parallel,
    # facing the bar). Keep that default: an explicit face(toward=counter) would aim each stool at the
    # counter's centre point and fan the end stools inward. We want them all looking straight.
    bar_group.place_rectilinear(longer_side1=stools)   # a single row on one long side
    if PHASE >= 3:
        # warm globe pendants over the bar (SINGULAR query -> one globe per copy). Low density: the
        # group footprint includes the stool depth, so a higher count spreads the globes forward into
        # the room as a cloud; ~0.2 keeps a tight cluster of ~4 over the counter.
        bar_group.add_lighting("a warm brass globe pendant light", density=0.2)

# --- The focal back-bar ("cellar"): a tall bottle-display cabinet behind the counter. ---
# GAP FIX: rather than lean on a clearance constraint (which only fought the stool-row overlap to a
# ~0.16 m compromise — verified numerically), compose the back-bar BEHIND the whole bar line as one
# rigid station via RelativeGroup.place_on_back. That bakes a fixed geometric aisle (FRONT_BACK_GAP,
# ~0.45 m from the anchor's back face; ~0.84 m here since the anchor is the counter+stool group) that
# the solver can't collapse — a guaranteed, generous bartender/service aisle in front of the cellar.
backbar = scene.AddAsset("a tall wooden back-bar cabinet with glass doors displaying liquor bottles",
                         asset_id=BACKBAR, width=2.6)
with scene.RelativeGroup() as bar_station:
    bar_station.set_anchor(bar_group)          # anchor = the counter + stool line
    bar_station.place_on_back(backbar)         # cellar 0.45 m behind the line's back face -> a real aisle

# --- an intimate lounge nook (round marble 2-top + a pair of velvet tub chairs + rug + a small
# pendant). Build ONE composed unit, then duplicate with 2*nook so both nooks are identical. ---
with scene.AroundGroup(sparsity=0.3, jitter=0.4) as nook:
    ctable = scene.AddAsset("a small round marble cocktail table with a brass pedestal base")
    nook.set_anchor(ctable)
    nook.place_circle(2 * scene.AddAsset("a dark green velvet tub lounge chair"))
    if PHASE >= 2:
        nook.place_rug("a dark patterned wool area rug", size=1.0)
    if PHASE >= 3:
        nook.add_lighting("a small brass pendant light", density=0)   # single pendant over the 2-top
nook_l, nook_r = 2 * nook

# modulate_scale=0.85 = final-phase room shrink (RoomProportions asked 0.8; a bar keeps some open floor).
with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:
    room.place_walls(floor_texture="dark walnut herringbone wood",
                     ceiling_texture="charcoal", wall_texture="deep charcoal")
    # back (long) wall: the whole bar station (cellar + aisle + counter + stool row) as one unit;
    # the back-bar lands flush against the wall, the built-in gap becomes the service aisle.
    room.place_on_back(bar_station, facing="front")
    # front half: the two lounge nooks, facing back toward the bar
    room.place_on_front_left(nook_l, facing="back")
    room.place_on_front_right(nook_r, facing="back")
    # entrance on the front wall (between the nooks) — kept in PHASE 1: its auto clearance shapes
    # the floor solve, so moving it later would move phase-1 geometry.
    room.place_door("front_wall", position="center")

    if PHASE >= 2:
        # greenery softening the back-left corner
        room.place_on_back_left_corner(
            scene.AddAsset("a large potted areca palm in a brass planter"))

    if PHASE >= 3:
        # short walls stay light: a large gold mirror (left) + a framed cocktail print (right)
        room.place_on_wall_left_center(scene.AddAsset("a large gold-framed vintage mirror"))
        room.place_on_wall_right_center(
            scene.AddAsset("a framed vintage cocktail print in a brass frame"))

scene.export("bar_v1.blend")
