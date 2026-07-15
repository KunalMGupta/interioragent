"""Mid-century lounge for entertaining — batch_0714 (seed=22).

Layout (residential lounge, conversation-ring key):
- CENTER     = the conversation ring: tufted brown leather sofa + TWO mustard
  accent armchairs on an AroundGroup ring around a ROUND three-leg walnut
  coffee table, every seat explicitly faced at the table (place_circle bakes
  the anchor's rotation — coffee_shop/kindergarten), on the flat wool rug,
  glassware + books on the table in phase 2 (the "entertaining" read lives on
  the SURFACE — jewelry_shop's product rule on a domestic table).
- BACK wall  = the service wall: low mid-century walnut credenza (height-fit to
  0.85 m — sideboard picks skew TALL and a tall piece at a wall centre blinds
  that camera, dining_room lesson 6), the record player + a vase on its top in
  phase 2, the framed photo gallery hung above it in phase 3 (pre-scaled so its
  AABB bottom clears the credenza top — dining_room lesson 3).
- RIGHT wall = the bar cart (0.74, and the mesh ships STOCKED with bottles and
  a pitcher — the bar vignette comes baked in, no phase-2 dressing needed).
  Low (~0.8 m), so the right-wall-centre camera sees over it.
- FRONT wall = standard window (opposite the main furniture wall), teal linen
  curtains — the plan's teal accent delivered through a TEXTILE, where palette
  accents are cheap and safe (living_room_cozy's plum-curtain rule; classroom:
  never smuggle an accent colour into the wall texture string).
- LEFT wall  = the door; warm brass floor lamp in the back-left corner.
- Lighting   = flush ceiling fixtures at density 0.015 (the 0.01–0.02 band for
  flush room lighting) + the corner floor lamp for the warm layer.

Palette: warm walnut + caramel leather + mustard, dark hardwood floor, verified
warm-beige walls, teal curtain accent.

Phase-gated (IDSDL/phases.py): --phase 1 = floor anchors + door; phase 2 =
surface dressing; phase 3 = wall art / window / lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("MidCenturyLounge", seed=22)

# --- pinned assets (every preview eyeballed at the audit gate; scores noted) ---
SOFA     = "future/2e32e106-9bab-407b-ae47-db2940ea922e"   # 0.75 vintage tufted brown leather 3-seat
ARMCHAIR = "future/0fb25207-a5bf-45cc-8b52-cce170f682da"   # 0.79 mustard armchair, clean MCM lines, wood legs
COFFEE   = "future/b846f09b-b91f-44b0-9a85-5181f385302d"   # 0.61 round walnut coffee table, three legs, bare
#  (round-coffee-table coverage is thin: the whole sheet sat 0.61–0.63; this is
#   the one with the true MCM tripod silhouette — pinned for FORM, score noted)
CREDENZA = "hssd/3aef5476fb1c9b2f3cae1b2ca8b33c1bae7ec1d2"  # 0.76 walnut sideboard, angled tapered legs
BARCART  = "future/a3f0179c-7fca-4e15-bcc5-d586d3306d54"    # 0.74 black metal bar cart, SHIPS STOCKED
RECORD   = "hssd/b8af904ac858f2431a89ec7b1d3a44c25b444259"  # 0.72 vintage wooden record player (tabletop)
GALLERY  = "future/e2b0dcb4-c660-415b-8b1e-cddeb905441b"    # framed collage WITH real photo content
#  (its rank-1 sibling future/09f28392... is BOTH reversed-front and empty-frame)
GLASSWARE = "hssd/a9d615bcd75af8e73df80fe7df1c64c938fa21ae" # wine glasses + decanter set (dining_room pick)
RUG      = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"  # known-flat beige wool rug

scene.prefetch_assets([
    "a mid-century tufted brown leather sofa",
    "a mid-century armchair with mustard yellow upholstery and wooden legs",
    "a round walnut wood coffee table, bare top",
    "a mid-century walnut sideboard credenza with tapered legs",
    "a black metal bar cart with bottles and glasses",
    "a vintage record player turntable console",
    "a set of wine glasses and a decanter",
    "a stack of decorative books",
    "a white ceramic vase with branches",
    "a warm brass floor lamp with a fabric shade",
    "a leafy potted plant in a ceramic planter",
    "a flat beige wool area rug",
    "a flat round LED flush mount ceiling light",
])

# --- the conversation ring: sofa + two armchairs around the round table --------
# Low sparsity/jitter: at 0.2/0.35 a ring drifts off its table (fast_food catch);
# a round table is the sanctioned place_circle case (the kitchen v1 fling was a
# circle around a RECTANGULAR table at high sparsity).
with scene.AroundGroup(sparsity=0.12, jitter=0.2) as lounge:
    coffee = scene.AddAsset("a round walnut wood coffee table, bare top",
                            asset_id=COFFEE, width=0.95)
    lounge.set_anchor(coffee)
    sofa = scene.AddAsset("a mid-century tufted brown leather sofa", asset_id=SOFA)
    chairs = 2 * scene.AddAsset(
        "a mid-century armchair with mustard yellow upholstery and wooden legs",
        asset_id=ARMCHAIR)
    lounge.place_circle([sofa, chairs[0], chairs[1]])
    lounge.face(sofa)        # place_circle inherits the anchor's rotation and
    lounge.face(chairs[0])   # seats pieces sideways — face each at the table
    lounge.face(chairs[1])   # (default target = the anchor; kindergarten rule)
    if PHASE >= 2:
        # entertaining reads on the SURFACE: decanter + glasses, not more chairs
        lounge.place_on_top([
            scene.AddAsset("a set of wine glasses and a decanter", asset_id=GLASSWARE),
            scene.AddAsset("a stack of decorative books"),
        ])
        lounge.place_rug("a flat beige wool area rug", size=0.75, asset_id=RUG)
        # <=0.8 under a room-dominating cluster or it reads as carpet
    if PHASE >= 3:
        # flush fixtures, room-lighting band 0.01–0.02 — NOT a chandelier
        # (a tall globed fixture hangs into the room and blows the exposure out)
        lounge.add_lighting("a flat round LED flush mount ceiling light",
                            density=0.015)

# --- the credenza as a dressed unit: anchor = the credenza, so its TOP gets the
# record player (place_on_top targets the group ANCHOR — living_room_cozy v3) ---
credenza = scene.AddAsset("a mid-century walnut sideboard credenza with tapered legs",
                          asset_id=CREDENZA)
credenza.scale(credenza.get_width() * 0.85 / credenza.get_height())
# uniform height-fit to a real ~0.85 m buffet: far under the ~1.4 m camera band
with scene.RelativeGroup() as service:
    service.set_anchor(credenza)
    if PHASE >= 2:
        service.place_on_top([
            scene.AddAsset("a vintage record player turntable console", asset_id=RECORD),
            scene.AddAsset("a white ceramic vase with branches"),
        ])

barcart = scene.AddAsset("a black metal bar cart with bottles and glasses",
                         asset_id=BARCART)

# --- the room -------------------------------------------------------------------
with scene.RoomGroup(modulate_scale=1.0, randomness=0.15) as room:
    # start neutral; the builder tunes modulate_scale from the vote train later.
    room.place_walls(floor_texture="dark brown hardwood floor",
                     ceiling_texture="smooth white plaster",
                     wall_texture="solid warm beige smooth uniform wall")
    # both strings VERIFIED matches (dining_room lesson 4: "warm oak" floors
    # match a salmon plank; "warm greige" walls match light gray — avoided)
    room.place_on_center(lounge, facing="front")
    room.place_on_back_wall_center(service)        # service wall, faces the room
    room.place_on_right_wall_center(barcart)       # low, camera sees over it
    room.place_on_back_left_corner(
        scene.AddAsset("a warm brass floor lamp with a fabric shade"))
    room.place_on_back_right_corner(
        scene.AddAsset("a leafy potted plant in a ceramic planter"))
    # corners are floor mass -> phase 1 (never gate floor mass to >=2)
    room.place_door("left_wall", position="left")  # phase 1: clearance shapes the solve

    if PHASE >= 3:
        # gallery ABOVE the credenza — pre-scaled to 0.95 m high so its AABB
        # bottom (1.5 - 0.475 = 1.02 m) clears the 0.85 m credenza top; hung
        # native (1.66 m) it would trigger the wall-object clearance pass and
        # slide the credenza off its own wall (dining_room lesson 3)
        gallery = scene.AddAsset("a gallery wall of framed pictures", asset_id=GALLERY)
        gallery.scale_only_width(1.30); gallery.scale_only_height(0.95); gallery.scale_only_depth(0.04)
        room.place_on_wall_back_center(gallery)
        # window OPPOSITE the main furniture wall; the teal accent rides the
        # curtain textile, never the wall texture string
        room.place_window_standard("front_wall", position="center",
                                   curtain="teal blue linen curtains")

scene.export("lr_midcentury.blend")
