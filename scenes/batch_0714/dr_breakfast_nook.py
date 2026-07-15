"""Sunny breakfast nook — batch_0714 (seed=23).

Layout (the table-hub pattern at its smallest domestic scale):
- CENTER     = the nook hub: a small ROUND light-oak tripod dining table ringed
  by 4 woven-seat chairs on place_circle — the sanctioned round-table case
  (dining_room's "rectilinear NOT circle" lesson is about RECTANGULAR tables,
  where the circle flings chairs wide; coffee_shop/kindergarten ring round
  tables with place_circle + per-chair face()). Jitter a touch higher than a
  formal dining room — a breakfast nook reads lived-in, not laid.
  Phase 2 sets the table for BREAKFAST: coffee cups + a small flower vase
  (the category rides the props on the surface — jewelry_shop's product rule).
- BACK wall  = the service wall: white sideboard with a natural wood top,
  height-fit to 0.85 m (sideboard picks skew tall; a tall piece at a wall
  centre blinds that camera — dining_room lesson 6), dressed in phase 2 with
  the vignette the brief asks for: fruit bowl + flowers + a trailing pothos.
- FRONT wall = the window, standard + white sheer curtains — opposite the
  service wall so the morning light rakes across the table (the "sunny" in the
  brief is the WINDOW + pale palette, not extra fixtures — brightness is never
  an add_lighting setting).
- LEFT wall  = the door.  RIGHT wall = one framed landscape (pinned, real
  painted content — the empty-frame trap).
- Corner     = one tall leafy plant (floor mass -> phase 1).
- Lighting   = ONE woven rattan dome pendant over the table (density=0).

Palette: light oak floor, verified warm-beige walls (light and airy without
gambling on an unverified "white" texture match), white/wood furniture, greens.

Phase-gated (IDSDL/phases.py): --phase 1 = floor anchors + door; phase 2 =
surface dressing; phase 3 = wall art / window / lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BreakfastNook", seed=23)

# --- pinned assets (every preview eyeballed at the audit gate; scores noted) ---
TABLE     = "hssd/5d70cc76c99acee4513ec5f7fad497d2baebca9e"  # 0.67 minimalist round light-oak table, BARE
#  (rank-2 for the same query is a table with two chairs BAKED IN — the dining
#   SET trap; the "no chairs" clause + the contact sheet is what dodged it)
CHAIR     = "hssd/35e45879a756f1a6b91371b38b0f97133045356d"  # 0.75 light wood chair, woven seat + back
SIDEBOARD = "hssd/35f0ae254da01b15ebcd5f5d7b52410aa7367e6f"  # 0.73 white sideboard, natural wood top
FRUIT     = "hssd/51a22c69abd300c67c0b53c7045d1e7f2db52cfb"  # 0.64 white pedestal bowl, REAL fruit mesh
LANDSCAPE = "hssd/4192b93682edc3c5585701c1ba90a34e9fd2f75b"  # framed landscape painting (known real content)

scene.prefetch_assets([
    "a small round light wood dining table, no chairs",
    "a light wood dining chair with a woven seat",
    "a narrow white wooden sideboard console with a flat top",
    "a bowl of fresh fruit",
    "a small vase of fresh flowers",
    "a white coffee cup and saucer",
    "a trailing potted pothos plant",
    "a tall leafy potted plant in a ceramic planter",
    "a neutral woven jute round rug",
    "a white woven rattan dome pendant light",
])

# --- the nook hub: round table + 4 chairs ---------------------------------------
with scene.AroundGroup(sparsity=0.15, jitter=0.3) as nook:
    table = scene.AddAsset("a small round light wood dining table, no chairs",
                           asset_id=TABLE, width=1.1)
    nook.set_anchor(table)
    chairs = 4 * scene.AddAsset("a light wood dining chair with a woven seat",
                                asset_id=CHAIR)
    nook.place_circle(chairs)
    for c in chairs:
        nook.face(c)   # place_circle inherits the anchor's rotation and seats
                       # chairs sideways; default face target = the anchor
    if PHASE >= 2:
        # breakfast ON the table — anchor is the table, so place_on_top lands
        # on the tabletop (always ask "what is this group's anchor?")
        nook.place_on_top([
            scene.AddAsset("a white coffee cup and saucer"),
            scene.AddAsset("a small vase of fresh flowers"),
        ])
        nook.place_rug("a neutral woven jute round rug", size=1.1)
        # a round rug slightly wider than the ring defines the zone
        # (coffee_shop's 2-top recipe at breakfast scale)
    if PHASE >= 3:
        # ONE rattan dome over the table; small emissive area, short drop
        nook.add_lighting("a white woven rattan dome pendant light", density=0)

# --- the sideboard as a dressed unit: anchor = the sideboard, so its TOP gets
# the vignette (place_on_top targets the group ANCHOR — living_room_cozy v3) ----
sideboard = scene.AddAsset("a narrow white wooden sideboard console with a flat top",
                           asset_id=SIDEBOARD)
sideboard.scale(sideboard.get_width() * 0.85 / sideboard.get_height())
# uniform height-fit to ~0.85 m: a real buffet height, under the camera band
with scene.RelativeGroup() as service:
    service.set_anchor(sideboard)
    if PHASE >= 2:
        service.place_on_top([
            scene.AddAsset("a bowl of fresh fruit", asset_id=FRUIT),
            scene.AddAsset("a small vase of fresh flowers"),
            scene.AddAsset("a trailing potted pothos plant"),
        ])

# --- the room -------------------------------------------------------------------
with scene.RoomGroup(modulate_scale=1.0, randomness=0.15) as room:
    # start neutral; the builder tunes modulate_scale from the vote train later.
    # "airy white" walls are an unverified match AND an exposure trap in a pale
    # room with a big window (nursery); the VERIFIED warm beige reads light
    # without blowing out — palette lightness comes from the white furniture.
    room.place_walls(floor_texture="light oak planks",
                     ceiling_texture="soft white plaster",
                     wall_texture="solid warm beige smooth uniform wall")
    room.place_on_center(nook, facing="front")
    room.place_on_back_wall_center(service)        # service wall, faces the room
    room.place_on_back_right_corner(
        scene.AddAsset("a tall leafy potted plant in a ceramic planter"))
    # floor mass -> phase 1 (never gate floor mass to >=2)
    room.place_door("left_wall", position="left")  # phase 1: clearance shapes the solve

    if PHASE >= 3:
        landscape = scene.AddAsset("a framed traditional landscape painting",
                                   asset_id=LANDSCAPE)
        landscape.scale_only_width(1.0); landscape.scale_only_height(0.7); landscape.scale_only_depth(0.04)
        room.place_on_wall_right_center(landscape)  # nothing stands under it
        # the window IS the "sunny" — standard, opposite the service wall,
        # sheers so the pane still reads while the light diffuses
        room.place_window_standard("front_wall", position="center",
                                   curtain="white sheer curtains")

scene.export("dr_breakfast_nook.blend")
