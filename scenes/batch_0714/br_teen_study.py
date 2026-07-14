"""Teen bedroom with a study corner — "Denim & Maple Teen Room".

Brief: a single bed + nightstand, a real WORK zone (desk + chair + computer), a bookshelf, a
beanbag to flop on, posters. Playful but not childish: the colour comes from a denim-blue wall,
the bed's own colorful bedding and a green beanbag — no cartoon meshes anywhere.

Layout — the bedroom hero skeleton with ONE zone swapped for a WorkstationGroup:
- BACK wall  : the bed HERO, nightstand aligned to the HEADBOARD (place_on_back_left — placed on
               the bed's side it slides toward the foot, the bedroom_v1 lesson).
- LEFT side  : the study corner — a WorkstationGroup floor unit, facing="right" so the desk backs
               onto the left wall and the chair sits on the room side (screen auto-faces the
               chair; the lobby lesson — never hand-face() a monitor).
- BACK-RIGHT : the bookshelf, in the CORNER — it is ~2 m tall, and the interior cameras stand at
               ~1.4-1.5 m at each wall CENTRE, so a tall piece parked mid-wall blinds that view
               (bakery/closet camera rule). Corners are free.
- FRONT-RIGHT: the beanbag — the flop zone, floor-standing so it is PHASE 1 mass, not dressing.
- RIGHT wall : kept furniture-free — it takes the window, and stays the light wall.
- FRONT wall : the door, left.

Phase-gated: phase 1 = every floor-standing object + the door (floor mass gated later shrinks the
phase-1 shell and jams the solve); phase 2 = the desktop items + rug; phase 3 = posters, window,
ceiling light.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BedroomTeenStudy", seed=31)

# ---- pinned heroes (audited on the retrieve contact sheets, 2026-07-14) ------------------------
BED     = "future/f65434b4-b939-4e48-8780-8bee03ba616a"  # SET asset: grey frame + colorful bedding
                                                         # already ON the mesh — playful without
                                                         # being cartoon (#4 was teddy-bear print).
DESK    = "hssd/95ecb8436c547896a7d222d29d2a354c03837950"  # bare flat top on slim legs. The rank-1
                                                           # desk ships with a LAPTOP baked into the
                                                           # mesh (would double up with
                                                           # place_computer); #5 bundles a whole
                                                           # dressed desk set. Picker rules want ONE
                                                           # clean surface — this is it.
SHELF   = "hssd/2e29b3aa38387e1a9682778d64f27e8a9ec40296"  # tall bookcase actually FILLED with
                                                           # books — an empty lattice never reads
                                                           # as a bookshelf (empty-fixture rule).
BEANBAG = "future/27460e0c-af6e-49bc-8737-a8049a14759d"    # classic green beanbag; the top pick is
                                                           # a pink "fantasy" print (childish) and
                                                           # #5 is a football — both off-brief.

scene.prefetch_assets([
    "a modern single bed with colorful bedding",
    "a light wood nightstand with a drawer",
    "a simple wooden study desk with a flat top",
    "a modern ergonomic desk chair",
    "a desktop computer with monitor keyboard and mouse",
    "a black articulated desk task lamp",
    "a pen cup with pens and pencils",
    "a tall wooden bookshelf filled with books",
    "a bean bag chair",
    "a colorful geometric area rug",
    "a framed colorful graphic art poster",
    "a flat round LED flush mount ceiling light",
])

# ---- the study corner: a WorkstationGroup (desk + chair + computer + accessories) ---------------
# place_computer aims the screen at the chair deterministically — the reusable fix for "monitor on
# a desk" facing (lobby). The desktop layer is PHASE 2 and the gate sits INSIDE the `with` block:
# a group compiles on __exit__, so an op registered after the block silently never runs.
with scene.WorkstationGroup() as study:
    desk = scene.AddAsset("a simple wooden study desk with a flat top", asset_id=DESK)
    study.set_anchor(desk)
    study.place_chair(scene.AddAsset("a modern ergonomic desk chair"))
    if PHASE >= 2:
        study.place_computer(scene.AddAsset("a desktop computer with monitor keyboard and mouse"))
        study.place_accessories([
            scene.AddAsset("a black articulated desk task lamp"),
            scene.AddAsset("a pen cup with pens and pencils"),
        ])

# ---- the HERO: bed + headboard-aligned nightstand ----------------------------------------------
bed = scene.AddAsset("a modern single bed with colorful bedding", asset_id=BED)
with scene.RelativeGroup() as bed_group:
    bed_group.set_anchor(bed)
    # one nightstand for a single bed, aligned to the HEADBOARD (place_on_back_left) — on the
    # bed's plain left side it would drift toward the foot (bedroom_v1 lesson 2's sibling).
    bed_group.place_on_back_left(scene.AddAsset("a light wood nightstand with a drawer"))
    if PHASE >= 2:
        # the rug grounds the sleep zone; kept under the cluster bbox so the maple floor reads
        bed_group.place_rug("a colorful geometric area rug", size=0.9)

bookshelf = scene.AddAsset("a tall wooden bookshelf filled with books", asset_id=SHELF)
beanbag   = scene.AddAsset("a bean bag chair", asset_id=BEANBAG)

# modulate_scale=0.8 — a teen room that solves to a full shell reads like a dorm common room; the
# same intimacy dial as bedroom_v1.
with scene.RoomGroup(modulate_scale=0.8, randomness=0.1) as room:
    # playful-but-grown palette: warm maple floor + a solid denim-blue wall. Worded like a caption
    # ("solid ... smooth uniform wall"), the phrasing that survives the texture matcher AND the
    # light budget (office_modern's three-wordings lesson); a pastel would blow out (nursery).
    room.place_walls(floor_texture="warm maple wood flooring",
                     ceiling_texture="soft white",
                     wall_texture="solid soft denim blue smooth uniform wall")

    # --- PHASE 1: ALL the floor mass ---
    room.place_on_back_wall_center(bed_group)
    room.place_on_left(study, facing="right")       # desk backs onto the left wall, chair room-side
    room.place_on_back_right_corner(bookshelf)      # tall piece -> CORNER, off the camera centres
    room.place_on_front_right(beanbag)              # the flop zone; floor-standing = phase 1 mass
    # door in PHASE 1: its automatic clearance shapes the floor solve
    room.place_door("front_wall", position="left")

    if PHASE >= 3:
        # posters, pre-shrunk BEFORE place_on_wall_* (mount height derives from the UN-scaled
        # height, so a big print punches through the ceiling — bedroom_v1 lesson 3)
        poster1 = scene.AddAsset("a framed colorful graphic art poster")
        poster1.scale_only_width(0.8); poster1.scale_only_height(0.6); poster1.scale_only_depth(0.03)
        room.place_on_wall_back_center(poster1)          # over the headboard
        poster2 = scene.AddAsset("a framed colorful graphic art poster")
        poster2.scale_only_width(0.8); poster2.scale_only_height(0.6); poster2.scale_only_depth(0.03)
        room.place_on_wall_left_center(poster2)          # over the study corner
        # the right wall stays the light wall: window + curtain, no furniture in front of it
        room.place_window_standard("right_wall", position="center",
                                   curtain="simple grey curtains")
        # ONE flush disc per ~area: 0.015 for a small bedroom (0.02+ starfields)
        # Build 1: the picked flush mount rendered as a ~2 m ceiling DISC (the kitchen v2 drum
        # class — size lever is modulate_scale, add_lighting takes no asset_id).
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.015,
                          modulate_scale=0.4)

scene.export("br_teen_study.blend")
