"""Children's room — "Playful Single-Bed Kids Room" (planner-driven).

Planner target: zone the room into SLEEP, STUDY and PLAY. A single bed on the main wall (light-wood
frame, colorful pastel bedding) defines the sleep zone; a small study desk + child chair with a task
lamp makes the study zone; open cubby storage with woven baskets + a low picture-book shelf makes the
toy/reading zone. A soft scalloped play rug grounds the floor. Wall art at kid height, a bright-
curtained window for daylight, layered warm lighting (flush ceiling + bedside mushroom lamp + desk
task lamp). Palette: gentle blues, pinks, neutrals, light wood.

Layout — THREE ZONES, ONE PER SIDE (each cluster its own RelativeGroup, so it travels as a unit):
- BACK wall  : the SLEEP zone — the bed HERO, with the nightstand+lamp unit at the HEAD
               (place_on_back_right), the grounding play rug and the room's ceiling light.
- RIGHT wall : the STORAGE/READING run — cubby unit (left) + low bookshelf (right). Long runs go on
               one long wall so the RoomGroup sizes a room with clear zones instead of a ring of
               furniture. The bean-bag reading seat sits OUT IN FRONT of it (place_on_right) — books
               within reach; a corner placement buried it.
- LEFT wall  : the STUDY zone — place_desk_chair(desk, chair), the desk styled with task lamp+pencils.
- FRONT wall : window (bright curtains) + door. No furniture: it stays the daylight source.
- CENTRE     : the PLAY floor, deliberately open — the rug and the bean bag do the grounding.

Identity comes from the KID-SCALE of everything: a pinned SINGLE bed (the shortlist is full of bunk
beds) that ships fully DRESSED as a set asset (so no separate bedding), pinned SMALL lamps, and wall
art pre-scaled to 0.5x so it hangs low, at a child's eye line, instead of adult-high. modulate_scale
=0.80 acts on the persistent RoomProportions shrink hint so the room reads cozy, not cavernous.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/children_room_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the surfaces (cubby baskets/toys, lamps, rug, bean
bag); phase 3 adds the kid-height wall art, the curtained window and the lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("ChildrenRoom", seed=7)

# ---- pinned assets (every pin is a mesh the generic query got wrong) --------------------------
BED         = "future/f65434b4-b939-4e48-8780-8bee03ba616a"  # clean SINGLE bed — the retrieval
                                                             # shortlist mixed in BUNK beds. SET
                                                             # asset: ships dressed, add no bedding.
DESK        = "hssd/49fcf2005b74d3a68855cfa604e43778e072349a"  # the KIDS desk with drawers; the
                                                               # generic query returned a plain
                                                               # adult table (flat top, no drawers)
MUSHROOM_LMP= "hssd/fd1e99da9dbf160083155092b75012e1f9724d5c"  # "mushroom night light" retrieved a
                                                               # metal LANTERN at the bedside
DESK_LAMP   = "hssd/5d1cede6d6501772f7508011931ba891eacba346"  # the generic desk-lamp query returned
                                                               # an oversized designer lamp that
                                                               # dwarfed the child's desk
BEANBAG     = "hssd/0d129d28eedc44412baecf233dfa67e62a255201"  # BAD scale metadata: loads at 0.15 m
                                                               # (native mesh 0.92 m) — see the
                                                               # modulate_scale=5.0 below
OCEAN_ART   = "hssd/8e37f5aec35bbac7aafa160df0aa6cded71af9b0"  # cheerful KID canvas; the generic
                                                               # picks were a moody sky + a
                                                               # deer-antler print
BLOSSOM_ART = "hssd/5ece73ced671e546797c2337876708b76f15daa4"  # a genuinely FLAT canvas (0.005 m
                                                               # deep). The earlier "planets" pick
                                                               # (12ef49da) is a wheeled EASEL/display
                                                               # 0.26 m deep — it read as a standing
                                                               # frame hung on the wall.

scene.prefetch_assets([
    "a kids single bed with colorful bedding",
    "a small light wood kids nightstand",
    "a low light wood kids cubby storage shelf",
    "a low kids bookshelf with picture books",
    "a kids wooden study desk with drawers",
    "a small child's wooden chair",
    "a soft scalloped cream kids play rug with pastel dots",
    "a warm flush kids ceiling light",
    "a mushroom shaped table lamp",
    "a small childrens desk lamp",
    "a cup full of colored pencils",
    "a woven seagrass storage basket",
    "a plush teddy bear toy",
    "a plush stuffed bunny toy",
    "a small potted green plant",
    "a childrens ocean animals wall canvas",
    "a colorful floral blossom canvas for a kids room",
    "a large yellow kids bean bag chair",
])

# ---- the majors (phase-1 floor anchors) ------------------------------------------------------
bed        = scene.AddAsset("a kids single bed with colorful bedding", asset_id=BED)
nightstand = scene.AddAsset("a small light wood kids nightstand")
desk       = scene.AddAsset("a kids wooden study desk with drawers", asset_id=DESK)
chair      = scene.AddAsset("a small child's wooden chair")
cubby      = scene.AddAsset("a low light wood kids cubby storage shelf")
bookshelf  = scene.AddAsset("a low kids bookshelf with picture books")

# ---- the study nook --------------------------------------------------------------------------
# place_desk_chair anchors the desk, seats the chair on its back, and rotates the desk 180 so its
# working front faces the chair. Then style the desk top with a task lamp + pencils.
with scene.RelativeGroup() as desk_group:
    desk_group.place_desk_chair(desk, chair)
    if PHASE >= 2:
        desk_group.place_on_top([
            scene.AddAsset("a small childrens desk lamp", asset_id=DESK_LAMP),
            scene.AddAsset("a cup full of colored pencils"),
        ])

# ---- the bedside unit ------------------------------------------------------------------------
# nightstand + lamp as its own group so the mushroom lamp sits ON the nightstand and the pair
# travels together when the bed group is placed.
with scene.RelativeGroup() as ns_group:
    ns_group.set_anchor(nightstand)
    if PHASE >= 2:
        ns_group.place_on_top(scene.AddAsset("a mushroom shaped table lamp",
                                             asset_id=MUSHROOM_LMP))

# ---- the cubby storage -----------------------------------------------------------------------
# Toys go place_inside (baskets tucked into the compartments), decor goes place_on_top.
# The baskets are ONE unit duplicated (3 * asset) — identical copies, one sizing tournament.
with scene.RelativeGroup() as cubby_group:
    cubby_group.set_anchor(cubby)
    if PHASE >= 2:
        cubby_group.place_inside(3 * scene.AddAsset("a woven seagrass storage basket"))
        cubby_group.place_on_top([
            scene.AddAsset("a plush teddy bear toy"),
            scene.AddAsset("a plush stuffed bunny toy"),
            scene.AddAsset("a small potted green plant"),
        ])

# ---- HERO: the bed arrangement ---------------------------------------------------------------
with scene.RelativeGroup() as bed_group:
    bed_group.set_anchor(bed)                                 # place_on_top seats items on the ANCHOR
    bed_group.place_on_back_right(ns_group)                   # bedside table+lamp beside the headboard
    if PHASE >= 2:
        bed_group.place_rug("a soft scalloped cream kids play rug with pastel dots", size=0.9)
    if PHASE >= 3:
        bed_group.add_lighting("a warm flush kids ceiling light", density=0)

# Final phase: act on the persistent RoomProportions shrink hint -> modulate 0.80 (and a bean bag
# fills the open play-zone floor, so the room reads cozy rather than empty).
with scene.RoomGroup(modulate_scale=0.80, randomness=0.15) as room:
    room.place_walls(floor_texture="light maple wood planks",
                     ceiling_texture="soft white", wall_texture="pale sky blue")
    # hero bed on the back wall; storage RUN on the right wall; study nook on the left wall
    room.place_on_back_wall_center(bed_group)
    room.place_on_right_wall_left(cubby_group)
    room.place_on_right_wall_right(bookshelf)
    room.place_on_left_wall_center(desk_group)
    # the door stays UNGATED: its auto clearance shapes the floor solve
    room.place_door("front_wall", position="right")

    if PHASE >= 2:
        # a bean-bag reading seat in the play zone, out in front of the bookshelf (books within
        # reach) so it reads as a reading nook and fills the open floor (corner placement buried it).
        # This bean bag's retriever scale metadata is ~6x too small (loads at 0.15 m); scale it up
        # UNIFORMLY to a real kids reading size (~0.75 m). width= alone would squash it flat.
        room.place_on_right(scene.AddAsset("a large yellow kids bean bag chair",
                                           asset_id=BEANBAG, modulate_scale=5.0))

    if PHASE >= 3:
        # kid-height art (ocean over the desk, blossom over the cubbies). PRE-SCALE small:
        # place_on_wall_* derives the mount height from the art's height, so a big print hangs
        # too high for a kid's room.
        ocean_art   = scene.AddAsset("a childrens ocean animals wall canvas", asset_id=OCEAN_ART)
        blossom_art = scene.AddAsset("a colorful floral blossom canvas for a kids room",
                                     asset_id=BLOSSOM_ART)
        for _a in (ocean_art, blossom_art):
            _a.scale_only_width(0.5); _a.scale_only_height(0.5); _a.scale_only_depth(0.03)
        room.place_on_wall_left_center(ocean_art)
        room.place_on_wall_right_center(blossom_art)
        room.place_window_standard("front_wall", position="center",
                                   curtain="bright cheerful patterned curtains")

scene.export("children_room_v1.blend")
