"""Japandi minimalist living room — batch_0714 (seed=21).

Layout (residential lounge, deliberately SPARSE — the emptiness is the design,
prison_cell's subtractive rule in its soft key: resist filling the floor, and
read a future "shrink the room" vote against the sparseness before obeying it):
- BACK wall  = the media wall: a LOW Japanese-style slatted TV console
  (~0.5 m tall — far under the ~1.4 m interior-camera eyeline, so the back
  view stays clear even at the wall CENTRE).
- CENTER     = the seating hero facing the media wall: low wood-frame sofa with
  cream cushions, low bare-top oak coffee table in front, ONE woven jute floor
  pouf angled in across the table (the brief's "floor cushions" — the flat
  white "floor cushion" meshes are featureless slabs, the pouf actually reads),
  paper-shade tripod floor lamp at the sofa's arm (a seat's task light belongs
  WITH the seat — design_principles).
- FRONT wall = standard window (opposite the main furniture wall, so daylight
  falls onto the media wall and the seating is lit from behind).
- LEFT wall  = the door.  RIGHT wall = ONE large framed ink-mountain artwork —
  the room's single piece of art, real printed content (empty-frame trap).
- Corner     = one large fiddle-leaf fig (the ONE plant; floor mass, so phase 1).
- Lighting   = ONE paper-lantern pendant over the seating (density=0) + the
  floor lamp. Nothing else — a Japandi room is lit low and warm.

Palette: light oak floor, warm cream walls (delivered via the VERIFIED beige
texture string — see the place_walls comment), charcoal carried by the ink art
and the console's dark wood, cream in the upholstery and rug.

Phase-gated (IDSDL/phases.py): --phase 1 = floor anchors + door (~1 min layout
check); phase 2 adds surface dressing; phase 3 adds walls art/window/lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("JapandiLivingRoom", seed=21)

# --- pinned assets (every preview eyeballed at the audit gate; scores noted) ---
SOFA    = "hssd/f9f2782899a7124ae07476db3dae629cf8f5742c"   # 0.71 low wood-frame sofa, beige cushions
COFFEE  = "hssd/3c227c098a3d53231dae30ea70ae09f10a1d4619"   # 0.72 simple low oak coffee table, BARE top
CONSOLE = "future/ad6c9cfb-e61f-4e14-bca3-777d00a8dbee"     # 0.68 Japanese-style low wooden TV stand
#  ("a low slatted wood TV media console cabinet" scored 0.62 and returned TALL
#   armoires — reworded to "TV stand", which routes to the right retriever)
POUF    = "hssd/5d38f9d6127aaf9819637d58b67dc6d23fb6ad85"   # 0.66 beige woven jute pouf (textured, reads)
LAMP    = "hssd/b314e028c0b084d9d3982a8b6ea4027b6d623be8"   # 0.72 white cylinder shade, wood tripod base
INKART  = "future/b55395b5-10c4-4e18-bce2-b9fc23aa1287"     # 0.67 framed b/w ink mountains — REAL content
RUG     = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"   # known-flat beige wool rug (the lobby pick)

scene.prefetch_assets([
    "a low profile wooden frame sofa with cream cushions",
    "a low rectangular light oak wood coffee table, bare top",
    "a low Japanese style wooden TV stand",
    "a beige woven jute floor pouf",
    "a paper lantern floor lamp with a wooden tripod base",
    "a stack of decorative books",
    "a large potted fiddle-leaf fig plant",
    "a flat beige wool area rug",
    "a round white paper lantern pendant light",
    "a framed minimalist ink brush art print",
])

# --- the coffee table as its own dressed unit: the TABLE must anchor its own
# dressing, because place_on_top seats items on a group's ANCHOR — dressing the
# table through the sofa-anchored seating group would put the books on the sofa
# CUSHION (the lamp-on-the-chair bug, living_room_cozy v3) ---------------------
coffee = scene.AddAsset("a low rectangular light oak wood coffee table, bare top",
                        asset_id=COFFEE, width=1.2)
with scene.RelativeGroup() as table_unit:
    table_unit.set_anchor(coffee)
    if PHASE >= 2:
        # ONE quiet object — a Japandi table is not "set"; sparse by design
        table_unit.place_on_top(scene.AddAsset("a stack of decorative books"))

# --- seating hero: sofa faces the media wall across the low table --------------
sofa = scene.AddAsset("a low profile wooden frame sofa with cream cushions",
                      asset_id=SOFA)
with scene.RelativeGroup() as seating:
    seating.set_anchor(sofa)
    seating.place_on_front(table_unit)          # table travels with its dressing
    pouf = scene.AddAsset("a beige woven jute floor pouf", asset_id=POUF)
    seating.place_on_front_left_further(pouf)   # the casual seat across the table
    seating.face(pouf, toward=coffee)           # side placements bake ±90° — angle it in
    seating.place_on_left(
        scene.AddAsset("a paper lantern floor lamp with a wooden tripod base",
                       asset_id=LAMP))          # task light travels with the seat
    if PHASE >= 2:
        seating.place_rug("a flat beige wool area rug", size=0.7, asset_id=RUG)
        # size 0.7: the group bbox spans sofa+pouf+table; bigger reads as
        # wall-to-wall carpet, and the oak floor showing around it IS the look
    if PHASE >= 3:
        # ONE paper lantern, dead over the cluster — also the room's main light
        seating.add_lighting("a round white paper lantern pendant light", density=0)

# --- the room -------------------------------------------------------------------
console = scene.AddAsset("a low Japanese style wooden TV stand",
                         asset_id=CONSOLE, width=1.6)
# width= is a single-axis pin: stretches the run along the wall, HEIGHT stays
# native (~0.5 m) — which is the point, the console must stay under the camera.

with scene.RoomGroup(modulate_scale=1.0, randomness=0.15) as room:
    # start neutral; the builder tunes modulate_scale from the vote train later.
    # "warm cream" as a texture string is a matching gamble — the VERIFIED
    # caption-worded beige ("solid warm beige..." matches a true beige at 0.744,
    # dining_room lesson 4) is one notch warmer and is what we actually get.
    room.place_walls(floor_texture="light oak planks",
                     ceiling_texture="soft white plaster",
                     wall_texture="solid warm beige smooth uniform wall")
    room.place_on_back_wall_center(console)        # media wall; low = camera-safe
    room.place_on_center(seating, facing="back")   # sofa looks at the console
    room.place_on_back_right_corner(
        scene.AddAsset("a large potted fiddle-leaf fig plant"))
    # the ONE plant — floor mass, so phase 1 (never gate floor mass to >=2)
    room.place_door("left_wall", position="left")  # phase 1: clearance shapes the solve

    if PHASE >= 3:
        # ONE large artwork, right wall centre — nothing stands under it, so
        # its AABB bottom (1.5 - 1.25/2 = 0.88 m) clears everything by inspection
        ink = scene.AddAsset("a framed minimalist ink brush art print",
                             asset_id=INKART)
        ink.scale_only_width(0.95); ink.scale_only_height(1.25); ink.scale_only_depth(0.04)
        room.place_on_wall_right_center(ink)
        # window OPPOSITE the main furniture wall (the media wall) — modest,
        # standard, with a linen curtain string carrying the cream textile layer
        room.place_window_standard("front_wall", position="center",
                                   curtain="white linen curtains")

scene.export("lr_japandi.blend")
