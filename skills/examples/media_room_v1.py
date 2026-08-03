"""
Home game media room — "Stadium-Style Home Game Media Room"
(planner target: tmp/plan_a_home_game_media_room_with_tier/plan.png)

Look (from the plan): a screen-centred theatre room in deep neutrals — charcoal walls,
grey acoustic carpet — where a projector wall is the single hero, TWO TIERS of black
cinema recliner rows face it (the back row lifted on a light-oak riser so the tier
actually READS), and a long walnut snack console runs down one side wall with a retro
popcorn maker and a drinks cooler.

LAYOUT — a focal-front cinema, staged front-to-back:
- FRONT wall  = THE PROJECTOR WALL. The projection screen is WALL-HUNG at the centre
                (genuinely flat mesh, D=0.07 m native), flanked by two slim tower
                speakers standing in the front wall's LEFT/RIGHT slots. The centre
                floor slot is left EMPTY on purpose — see the camera note below.
- CENTRE      = TIER 1: a 4-seat cinema recliner row on the floor, facing the screen,
                on a plush charcoal rug.
- BACK wall   = TIER 2: a light-oak riser (2.90 x 0.40 x 1.40 m) with an IDENTICAL
                recliner row lifted onto it via the `bottom=` lift, plus the ceiling
                projector mounted high on the same wall centre, aimed down the room.
- LEFT wall   = the SNACK CONSOLE run: walnut console (dressed in phase 2) + a retro
                bottle cooler. This is the "long, accessible snack console" of the brief.
- RIGHT wall  = the entry door at the centre (its 0.9 m auto-clearance IS the side
                aisle the plan asks for) + memorabilia-style framed art in the flanking
                wall slots.

=== THE THREE THINGS THAT ACTUALLY DECIDED THIS PROGRAM ===

1. CAMERA SAFETY (verified in IDSDL/renderer/utils.py:741, not taken on trust).
   `render_interior_walls` puts each view's camera at the OPPOSITE wall's CENTRE,
   `inset=0.92` (i.e. ~4% of the room dimension off that wall), at
   `eye = floor_z + 0.55*H`. With scene.py clamping height to 3.0 m the eye is 1.65 m.
   So ANY object taller than ~1.65 m standing at a wall CENTRE contains a camera and
   renders that view pure black. Every wall centre here is therefore deliberately low:
     - back wall centre  : riser 0.40 + recliner row 0.78 = 1.18 m top   (< 1.65) OK
     - front wall centre : wall-hung screen only, D ~ 0.09 m off the wall  OK
     - left wall centre  : snack console, 0.84 m tall                     OK
     - right wall centre : the door (an opening, no mass)                 OK
   The tall pieces (tower speakers) are pushed into the front wall's LEFT/RIGHT slots.
   This is the whole reason the back row uses the SHORT cinema row (H=0.78 m) rather
   than the taller reclining loveseat (H=1.36 m, which on a 0.40 m riser would top out
   at 1.76 m and blind the front-wall view from the back wall centre).

2. THE TIER IS A `bottom=` LIFT, AND `bottom=` IS AABB-REFERENCED (I read the source).
   `RoomGroup._wall_furniture_y` (groups.py:1396) returns `compute_obj_y(obj) + b`, and
   `compute_obj_y` (object.py:961) is `origin_y - aabb_min_y` — the offset that puts the
   mesh's AABB BOTTOM on the floor. So `bottom=0.42` lands the row's true lowest point at
   0.42 m regardless of where the mesh's origin sits. An off-centre origin therefore does
   NOT sink or float this riser seating, which is the usual way tiered seating dies.
   The two riders that path demands (both documented, both applied):
     - `ignore_overlap = True`  — else the 2D-footprint solver sees the row and the riser
       under it as interpenetrating and shoves them apart along the wall.
     - `is_static = True`       — else GradSolver's exploration floor random-walks a
       small-footprint piece along the wall (the living_room_cozy fireplace drift).
   `ignore_overlap` also exempts the lifted row from `lint_floaters`, which would
   otherwise (correctly, for ordinary floor furniture) call it a 0.42 m floater.

3. ALIGNMENT: `RoomGroup(randomness=0.0)`. Two rows facing one screen must share a centre
   line. Both rows land on `col_centers[2]` by construction (place_on_center and
   place_on_back_wall_center), and any room jitter would break that alignment invisibly —
   no VLM signal ever checks two rows are collinear. Zero jitter, then measured in the blend.

ASSET NOTES (every hero measured offline with get_whd, every pin eyeballed at its
TRUE-COLOUR catalog preview in datasets/futurehssd/{HSSD,3D-FUTURE}-images, because the
inspect contact sheet is exposure-washed and misreports colour):
  - CINEMA_ROW ships 2.50 x 0.78 x 0.81 m — a genuine 4-seat cinema recliner row, and its
    LOW height is what makes the riser tier camera-safe. Used for BOTH tiers.
  - The "tall floor-standing speaker" hero ships 3.12 m tall (hssd/185b765e) — it would
    have punched the ceiling and blinded a view. Swapped to future/09bafd1e (2.04 m) and
    height-fit UNIFORMLY to 1.15 m. (The reference-examples-are-not-safe rule, live.)
  - The riser slab is scaled per-axis on purpose: it is a plain rectangular block, so
    non-uniform scaling keeps it a rectangular block. This is the one safe use of the
    single-axis pins — it would be wrong on anything with a form to distort.
  - SCREEN is a flat (D=0.07 m) retractable screen mesh WITH a projected image on it, so
    the projector wall reads as switched-ON rather than as a blank grey rectangle.
  - SUBSTITUTION: there are NO framed sports jerseys / memorabilia cases in the pool
    (best hits are generic framed prints). The plan's memorabilia wall is carried by a
    framed-art collection + a baseball-themed canvas instead, and called out as a gap.

Phase-gated (IDSDL/phases.py): phase 1 = the whole floor layout incl. both tiers, the
riser, the console run and the door; phase 2 = the snack dressing + the rug; phase 3 =
the screen, the projector, wall art and the lighting layer.
"""
import os

# A projector room is a DIM brief, but the renderer's interior sky is the dominant source
# and MCP `run_scene` binds it at import on a warm server (wine_cellar's tooling gotcha) —
# so this line only bites on a SHELL build. Kept deliberately MODERATE (1.4, not the
# cellar's 0.6): the failure mode for a charcoal room full of BLACK leather seating is an
# unreadable black box, not blowout. Mood comes mostly from light_budget below.
os.environ.setdefault("IDSDL_SKY", "1.4")

from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("GameMediaRoom", seed=31)

# Dimmer than the 500 W default (a cinema is lit low) but NOT the cellar's 90 W: every
# seat in this room is black leather against a charcoal wall, so the room has very little
# albedo to work with and over-dimming it renders an unreadable void.
scene.light_budget = 320.0

# ---- pinned assets (true-colour previews eyeballed; dims measured offline) -------------
CINEMA_ROW = "hssd/9d698f28231c5674548da3fc925d48c57bf3af4e"  # 2.50x0.78x0.81 black 4-seat cinema recliner row (HERO, x2)
RISER      = "hssd/e7c8865d65579f6108b9aacc04491bfb1dea3948"  # light-oak rectangular stage platform slab (scaled to the riser)
SCREEN     = "custom/049182127609e8712ab86df11e06180a626afe87"  # 2.00x1.04x0.14 FLAT 16:9 retractable projector screen
# (was hssd/f1ccc58e, a 4:3 screen: correct-looking, but see the aspect note at the
#  placement below — a 4:3 mesh CANNOT be hung large, and this one can.)
PROJECTOR  = "custom/574d85991b53e5bb44fbc58914626d950c5a4d1d"  # 0.40x0.13x0.32 black matte projector w/ exposed lens
SPEAKER    = "future/09bafd1e-e457-49a2-972e-8a34cc2d04d6"    # 0.30x2.04x0.30 black tower speaker (height-fit to 1.15 m)
CONSOLE    = "hssd/7abd74b8300c96386861ddd3f62dbca5b4b093a8"  # 2.00x0.84x0.50 warm walnut media/snack console
COOLER     = "hssd/cecab63706032928094ec5b80cde48d9f61e2ca4"  # 1.20x0.95x0.72 retro red bottle cooler (the palette's accent)
POPCORN    = "hssd/507324eb1a7679fd53fff3e1bb9e7317ac35e23e"  # 0.20x0.38x0.21 retro red+chrome popcorn maker
SNACKBAGS  = "hssd/fc41b57d334f2d68b613d903b0216097ba33b938"  # assorted snack bags
POPBOX     = "hssd/02c784e528d209e63cfeb98944ae483256338bc5"  # striped popcorn box + soda bottle
AVRECEIVER = "hssd/21806f13dc30d82eacea33a27e22536022938c52"  # black AV home-cinema receiver
ARTWALL    = "future/2fccf8e7-9886-4a59-b167-c3fb905aeb0f"    # collection of framed pieces (the memorabilia SUBSTITUTE)
BALLART    = "hssd/08fc501fafd4ce4f52d8507bf28a925bd530f2dc"  # baseball-themed canvas print (the one sports asset in pool)

scene.prefetch_assets([
    "a black four seat cinema recliner sofa row",
    "a light wood rectangular stage platform",
    "a large projection screen displaying an image",
    "a slim black floor standing tower speaker",
    "a long walnut media console cabinet",
    "a retro red bottled drinks cooler",
    "a retro red and chrome popcorn maker",
    "a black audio video home cinema receiver",
    "a plush dark charcoal shag area rug",
    "a flat round LED flush mount ceiling light",
])


def fit_height(obj, h):
    """Uniform height fit — preserves the mesh's own proportions (never `width=`)."""
    obj.scale(obj.get_width() * h / obj.get_height())
    return obj


# ============================ TIER 1 — the front row (floor) ============================
# The rug belongs to this cluster, so it travels with the front row rather than being a
# stray floor object. size<=0.9: a room-dominating cluster rug at 1.0 reads wall-to-wall.
front_row = scene.AddAsset("a black four seat cinema recliner sofa row", asset_id=CINEMA_ROW)
with scene.RelativeGroup() as tier1:
    tier1.set_anchor(front_row)
    if PHASE >= 2:
        # size is relative to the GROUP bbox, and this group is ONE row (2.50x0.81) — not
        # the room-dominating cluster the <=0.8 rule is about, so 0.85 rendered a 2.78x0.90
        # mat barely wider than the seats. 1.15 pushes it forward into the aisle so it
        # reads as the zone the front tier sits in.
        tier1.place_rug("a plush dark charcoal shag area rug", size=1.15)

# ============================ TIER 2 — the riser + the lifted back row ==================
# The riser is a plain rectangular slab, so per-axis scaling is safe here (it stays a
# rectangular slab). 0.40 m is a real single-step riser: high enough that the tier reads
# from every camera, low enough that the seated sightline over the front row still works.
RISER_H = 0.40
riser = scene.AddAsset("a light wood rectangular stage platform", asset_id=RISER)
riser.scale_only_width(2.90)
riser.scale_only_height(RISER_H)
riser.scale_only_depth(1.40)

# The back row is lifted onto the riser. bottom = RISER_H + 0.02 so its AABB bottom sits
# just PROOF of the riser top rather than exactly coincident with it — a hair of clearance
# keeps lint_embedded_wall_objects' 3D AABB test unambiguous (seat ABOVE riser = legal).
back_row = scene.AddAsset("a black four seat cinema recliner sofa row", asset_id=CINEMA_ROW)
back_row.ignore_overlap = True   # else the 2D solver shoves the row off its own riser
back_row.is_static = True        # else the exploration floor drifts it along the wall

# The projector: mounted high on the back wall, looking down the room at the screen.
projector = scene.AddAsset("a black video projector with an exposed lens", asset_id=PROJECTOR)
projector.ignore_overlap = True
projector.is_static = True

# ============================ the SNACK CONSOLE run (left wall) =========================
# place_on_top targets the group's ANCHOR, and the anchor here IS the console — which is
# exactly the surface the snacks belong on (the living_room_cozy lamp-on-the-chair trap is
# avoided by construction, not by luck).
console = scene.AddAsset("a long walnut media console cabinet", asset_id=CONSOLE)
with scene.RelativeGroup() as snack_bar:
    snack_bar.set_anchor(console)
    if PHASE >= 2:
        # A snack console that is BARE names the fixture, not the room (jewelry_shop's
        # empty-vitrine rule). The tournament height-fits these itself — `modulate_scale`
        # is a no-op on on-top items (tv_studio), so it is not spent here.
        snack_bar.place_on_top([
            scene.AddAsset("a retro red and chrome popcorn maker", asset_id=POPCORN),
            scene.AddAsset("a striped popcorn box with a soda bottle", asset_id=POPBOX),
            scene.AddAsset("assorted snack bags", asset_id=SNACKBAGS),
            scene.AddAsset("a black audio video home cinema receiver", asset_id=AVRECEIVER),
        ])

# ============================ the ROOM ==================================================
# randomness=0.0 — the two tiers must stay collinear with the screen (see note 3 above).
#
# modulate_scale=1.1: phases 1 and 2 both voted `no rescale`; the FULL build voted
# `rescale room by 1.1`, which is the only phase whose room-size vote is meaningful (a
# vote on a partial build is a vote on a room that does not exist yet). My own read of the
# blend agreed rather than deferred: the aisle between the snack console and the front row
# measured 0.72 m and the gap between the riser and the right wall 0.59 m — genuinely
# tight for a room people walk into in the dark. Applied ONCE, decisively, in the final
# phase. It also widens the front wall, which raises freeform's 50%-of-wall screen cap.
with scene.RoomGroup(modulate_scale=1.1, randomness=0.0) as room:
    # Plain colour+material words only: an "accent wall" clause drags the whole texture
    # match (classroom) and accents are better carried by a PROP (music_studio) — here the
    # red cooler and the oak riser carry them. Mid-charcoal, NOT near-black: the seating is
    # already black leather and the room needs something to silhouette it against.
    room.place_walls(floor_texture="dark grey acoustic carpet",
                     ceiling_texture="matte charcoal grey",
                     wall_texture="dark charcoal grey paint")

    # ---- FRONT wall: the projector wall. Speakers in the LEFT/RIGHT slots ONLY, so the
    # centre stays clear for the back-wall view's camera (it sits ~4% off this wall).
    spk_l = fit_height(scene.AddAsset("a slim black floor standing tower speaker", asset_id=SPEAKER), 1.15)
    spk_r = fit_height(scene.AddAsset("a slim black floor standing tower speaker", asset_id=SPEAKER), 1.15)
    room.place_on_front_wall_left(spk_l)
    room.place_on_front_wall_right(spk_r)

    # ---- TIER 1 centre, facing the screen on the front wall.
    room.place_on_center(tier1, facing="front")

    # ---- TIER 2 against the back wall: riser first (real floor mass, sizes the room),
    # then the row lifted onto it, then the projector above both. All three sit in the
    # SAME back-wall centre slot on purpose — they are one vertical stack, and they are
    # 3D-disjoint (0-0.40 / 0.42-1.20 / 2.45-2.58 m), which is what keeps
    # lint_embedded_wall_objects quiet.
    room.place_on_back_wall_center(riser)
    room.place_on_back_wall_center(back_row, bottom=RISER_H + 0.02)
    if PHASE >= 3:
        room.place_on_back_wall_center(projector, bottom=2.45)

    # ---- LEFT wall: the snack console run + the drinks cooler.
    # `facing` omitted throughout — the wall heuristic already turns wall furniture INTO
    # the room, and naming the wall's own direction would turn its access side to the wall.
    room.place_on_left_wall_center(snack_bar)
    room.place_on_left_wall_left(scene.AddAsset("a retro red bottled drinks cooler", asset_id=COOLER))

    # ---- RIGHT wall: the entry. The door's automatic ~0.9 m clearance IS the plan's side
    # aisle, so it is placed in PHASE 1 where it can shape the floor solve.
    room.place_door("right_wall", position="center")

    if PHASE >= 3:
        # THE HERO: the projection screen, hung dead centre on the front wall.
        #
        # FREEFORM, not place_on_wall_front_center, and that choice is the difference
        # between a projector wall and a television. `_place_on_wall` clamps a slot-verb
        # piece to its slot's third of the wall (groups.py:1615) — on this 4.62 m shell the
        # centre third is 1.50 m, which would have shrunk the screen to TV size and quietly
        # gutted the room's hero. `place_on_wall_freeform` passes no `along_bounds`, so no
        # slot clamp applies; its own cap is 50% of the wall (groups.py:2121), centred,
        # hung at wall mid-height.
        #
        # THE ASPECT IS LOAD-BEARING, and this cost a build to learn. Freeform alone was
        # NOT enough: `wall_obj_scale_computer` (groups.py:1896) minimises
        # L1 + 10*max(h-1,0)^2 + L3, i.e. it penalises any wall-hung piece taller than
        # 1 m by a factor of ten. A 4:3 screen 2.4 m wide is 1.76 m tall, so the solver
        # paid the penalty down and settled at 1.57 x 1.07 m — measured in the blend, a
        # TELEVISION on a 4.9 m wall, not a projector wall. The fix is not a bigger
        # number, it is a WIDER ASPECT: this 16:9 mesh at ~2.1 m wide is only ~1.1 m
        # tall, so it clears the height penalty almost for free and hangs nearly twice
        # as wide as the 4:3 mesh could. Pin the aspect, not the scale.
        screen = scene.AddAsset("a large projection screen displaying an image", asset_id=SCREEN)
        screen.scale(2.40)
        room.place_on_wall_freeform("front_wall", [screen])

        # Memorabilia SUBSTITUTE (no framed jerseys exist in the pool) — the framed
        # collection and the one baseball canvas, in the right wall's flanking slots so
        # neither lands in the door's centre slot.
        room.place_on_wall_right_left(scene.AddAsset("a collection of framed wall art pieces", asset_id=ARTWALL))
        room.place_on_wall_right_right(scene.AddAsset("a baseball themed canvas art print", asset_id=BALLART))

        # Lighting LAST, because it is downstream of room size (the fixture budget scales
        # with floor area, so the final modulate_scale silently re-prices any density).
        # DENSITY IS RELATIVE TO THE FIXTURE'S OWN FOOTPRINT, not to the room — the
        # published "small room = 0.01-0.02" band is only meaningful for a SMALL fixture.
        # object.py:1013 computes
        #     max_lights = floor(W*D*0.64 / (w_fixture*d_fixture)) / 4 ;  N = round(1+(max_lights-1)*d)
        # and the retrieved flush disc arrives 1.0 x 1.0 m, so on this 6.05x5.22 shell
        # max_lights = floor(20.2/1.0)/4 = 5 and EVERY density below ~0.13 rounds to N=1.
        # That is why both 0.01 and 0.006 rendered a single 1 m dish on the ceiling
        # (measured as ceiling_lights=1 in report.json across two builds) — I was tuning a
        # dial that could not move. Shrinking the fixture to 0.5 m raises max_lights to 20,
        # and 0.25 then gives N=6: a real recessed-downlight layout, still well under the
        # starfield budget (~9 for this area). Wattage is FIXED at scene.light_budget and
        # split across N, so this changes the ceiling's composition, never its brightness.
        # A FLUSH disc, never a hanging fixture: add_lighting pins the origin at the
        # ceiling but caps height at 1.5 m, so anything tall drops into the room.
        room.add_lighting("a flat round LED flush mount ceiling light",
                          density=0.25, modulate_scale=0.5)

scene.export("media_room_v1.blend")
