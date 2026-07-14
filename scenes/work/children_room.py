"""
Children's room — "Playful Single-Bed Kids Room" (planner-driven).

Design brief (planner): zone the room into SLEEP, STUDY, and PLAY. A single bed anchored to the
main wall (light-wood frame, colorful pastel bedding) defines the sleep zone; a small study desk +
child chair with a task lamp makes the study zone; open cubby storage with woven baskets + a low
picture-book shelf makes the toy/reading zone. A soft scalloped play rug grounds the floor. Wall
art at kid height, a bright-curtained window for daylight, and layered warm lighting (flush ceiling
+ bedside mushroom lamp + desk task lamp). Palette: gentle blues, pinks, neutrals, light wood.

Coarse-to-fine (skills/workflow/coarse_to_fine.md):
  Phase 1 — floor anchors: single bed (+ nightstand) hero group with play rug + ceiling light;
    cubby storage + low bookshelf run along the right wall; desk+chair study nook on the left wall.
  Phase 2 — surface/floor: bedside mushroom lamp, desk lamp + pencils, woven baskets + toys INSIDE
    the cubbies, stuffed animals + a small plant on top, a low bookshelf styled with a plant.
  Phase 3 — walls: kid-height cloud/animal art, a bright-curtained window, a door.

Beds are "set assets" — the mesh comes fully DRESSED, so we pin a clean SINGLE bed (the shortlist
had several bunk beds) and do NOT add separate bedding. place_on_top / place_inside run the full
VLM-tournament smart placement (core DSL behaviour — never disabled for speed).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ChildrenRoom", seed=7)

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

# --- Phase 1 majors ---
# Pin a clean SINGLE bed (retrieval shortlist mixed in bunk beds); beds carry real-world scale.
bed = scene.AddAsset("a kids single bed with colorful bedding",
                     asset_id="future/f65434b4-b939-4e48-8780-8bee03ba616a")
nightstand = scene.AddAsset("a small light wood kids nightstand")
# Pin the KIDS desk with drawers (generic query returned a plain adult table); flat top + drawers.
desk       = scene.AddAsset("a kids wooden study desk with drawers",
                            asset_id="hssd/49fcf2005b74d3a68855cfa604e43778e072349a")
chair      = scene.AddAsset("a small child's wooden chair")
cubby      = scene.AddAsset("a low light wood kids cubby storage shelf")
bookshelf  = scene.AddAsset("a low kids bookshelf with picture books")

# --- Phase 2 surface pieces (pin clean small lamps — the generic queries returned an oversized
# designer lamp on the desk and a metal lantern at the bedside) ---
mushroom_lamp = scene.AddAsset("a mushroom shaped table lamp",
                               asset_id="hssd/fd1e99da9dbf160083155092b75012e1f9724d5c")
desk_lamp     = scene.AddAsset("a small childrens desk lamp",
                               asset_id="hssd/5d1cede6d6501772f7508011931ba891eacba346")
pencils       = scene.AddAsset("a cup full of colored pencils")
baskets       = 3 * scene.AddAsset("a woven seagrass storage basket")   # identical copies for the cubbies
teddy         = scene.AddAsset("a plush teddy bear toy")
bunny         = scene.AddAsset("a plush stuffed bunny toy")
shelf_plant   = scene.AddAsset("a small potted green plant")
# This bean bag's retriever scale metadata is ~6x too small (loads at 0.15 m); scale it up
# UNIFORMLY to a real kids reading size (~0.75 m). width= alone would squash it flat.
beanbag       = scene.AddAsset("a large yellow kids bean bag chair",
                               asset_id="hssd/0d129d28eedc44412baecf233dfa67e62a255201",
                               modulate_scale=5.0)

# --- Phase 3 wall art: pin cheerful KID canvases (generic picks were a moody sky + deer-antler
# print). Pre-scale small — place_on_wall_* derives mount height from the art height, so a big
# print lands too high; kids' art hangs low and small. ---
ocean_art   = scene.AddAsset("a childrens ocean animals wall canvas",
                             asset_id="hssd/8e37f5aec35bbac7aafa160df0aa6cded71af9b0")
# NB: the earlier "planets" pick (12ef49da) is a wheeled EASEL/display (0.26 m deep), not a flat
# print — it read as a standing frame on the wall. Use a genuinely FLAT canvas (0.005 m deep).
blossom_art = scene.AddAsset("a colorful floral blossom canvas for a kids room",
                             asset_id="hssd/5ece73ced671e546797c2337876708b76f15daa4")
for _a in (ocean_art, blossom_art):
    _a.scale_only_width(0.5); _a.scale_only_height(0.5); _a.scale_only_depth(0.03)

# study nook: place_desk_chair anchors the desk, seats the chair on its back, and rotates the desk
# 180 so its working front faces the chair. Then style the desk top with a task lamp + pencils.
with scene.RelativeGroup() as desk_group:
    desk_group.place_desk_chair(desk, chair)
    desk_group.place_on_top([desk_lamp, pencils])

# bedside nightstand+lamp as its own unit so the mushroom lamp sits ON the nightstand
with scene.RelativeGroup() as ns_group:
    ns_group.set_anchor(nightstand)
    ns_group.place_on_top(mushroom_lamp)

# cubby storage: woven baskets tucked INSIDE the cubbies, soft toys + a plant styled on top
with scene.RelativeGroup() as cubby_group:
    cubby_group.set_anchor(cubby)
    cubby_group.place_inside(baskets)
    cubby_group.place_on_top([teddy, bunny, shelf_plant])

# HERO: the bed arrangement (nightstand+lamp at the head, grounding play rug, room ceiling light)
with scene.RelativeGroup() as bed_group:
    bed_group.set_anchor(bed)
    bed_group.place_on_back_right(ns_group)                   # bedside table+lamp beside the headboard
    bed_group.place_rug("a soft scalloped cream kids play rug with pastel dots", size=0.9)
    bed_group.add_lighting("a warm flush kids ceiling light", density=0)

# Final phase: act on the persistent RoomProportions shrink hint -> modulate 0.80 (and a bean bag
# fills the open play-zone floor, so the room reads cozy rather than empty).
with scene.RoomGroup(modulate_scale=0.80, randomness=0.15) as room:
    room.place_walls(floor_texture="light maple wood planks",
                     ceiling_texture="soft white", wall_texture="pale sky blue")
    # Phase 1 — hero bed on the back wall; storage RUN on the right wall; study nook on the left wall
    room.place_on_back_wall_center(bed_group)
    room.place_on_right_wall_left(cubby_group)
    room.place_on_right_wall_right(bookshelf)
    room.place_on_left_wall_center(desk_group)
    # Phase 2 — a bean-bag reading seat in the play zone, out in front of the bookshelf (books within
    # reach) so it reads as a reading nook and fills the open floor (corner placement buried it).
    room.place_on_right(beanbag)
    # Phase 3 — kid-height art (ocean over the desk, blossom over the cubbies), window + curtains, door
    room.place_on_wall_left_center(ocean_art)
    room.place_on_wall_right_center(blossom_art)
    room.place_window_standard("front_wall", position="center", curtain="bright cheerful patterned curtains")
    room.place_door("front_wall", position="right")

scene.export("children_room.blend")
