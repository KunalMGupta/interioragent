"""Cozy hearth-centric living room — guided-flow build (plan: tmp/plan_a_cozy_living_room).

Layout (single-room residential lounge, hero-in-the-middle):
- BACK wall = the FOCAL wall: fireplace with a burning fire (pinned — cozy glow),
  framed photo gallery hung above it (wall-mounted art + floor fireplace occupy
  independent slots).
- CENTER = seating hero facing the hearth: cream three-piece sectional, rustic
  wood coffee table between sofa and fire, caramel leather chair + ottoman nook
  angled into the conversation (a seat always gets a table + its own light — the
  nook carries a side table and a brass floor lamp), all grounded on the pinned
  flat beige wool rug.
- LEFT wall = tall filled bookcase (visual mass balancing the fireplace).
- RIGHT wall = standard window with plum curtains (the plan's plum accent;
  standard, not floor-to-ceiling — the black-void lesson).
- FRONT wall = door (left) + framed landscape art (center).
- Lighting: ONE central flush-mount over the seating (density=0 — the chandelier
  ban: tall fixtures hang into the room and blow out exposure), plus the fire
  glow and the nook's floor lamp + a table lamp for the warm layer.

Phase-gated (IDSDL/phases.py): --phase 1 = floor anchors only (~1 min layout
check); phase 2 adds surface dressing; phase 3 adds walls/window/lighting/mood.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("CozyLivingRoom", seed=42)

# --- pinned assets (previews eyeballed at the audit gate) ---
FIREPLACE = "hssd/afbe5bf0c84434cd80351009cc16cc741d9900e2"   # beige straight fireplace, wooden mantel, tile surround
# (first pick hssd/9a81f950... has a stronger fire but is a CORNER mesh — placed at
#  the back wall center its angled wings read wrong; swapped for the straight unit)
SECTIONAL = "hssd/61caf268af6aea6f3b38858bc4ed01788a1ae7c6"   # cream 3-piece sectional w/ accent pillows
LCHAIR    = "hssd/826d4c38300442629340bbff015870594a65234a"   # vintage tan leather club armchair
OTTOMAN   = "future/f741c7dc-be51-4e60-b173-31c982c7f18c"     # cognac leather footstool
COFFEE    = "hssd/836a3d87a62dbfa117b375204a498ec1b4c9dcbf"   # rustic block wood coffee table, flat top
BOOKCASE  = "future/81f093b2-a506-41f2-b260-bf2e2eae8176"     # warm wood bookcase, shelves filled
RUG       = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"   # flat beige wool rug (known-flat, no slab)

scene.prefetch_assets([
    "a small round dark wood side table",
    "a warm brass floor lamp with a fabric shade",
    "a modern table lamp with a warm fabric shade",
    "a stack of decorative books",
    "a white ceramic vase with branches",
    "a leafy potted plant in a ceramic planter",
    "a collage of black framed photographs gallery wall",
    "a framed traditional landscape painting",
    "a flat round LED flush mount ceiling light",
])

# --- leather reading nook: chair + ottoman + side table + task light, one unit ---
lchair = scene.AddAsset("a vintage tan leather club armchair", asset_id=LCHAIR)
with scene.RelativeGroup() as nook:
    nook.set_anchor(lchair)
    nook.place_on_front_adjacent(
        scene.AddAsset("a cognac leather ottoman footstool", asset_id=OTTOMAN,
                       modulate_scale=0.7))   # phase-1 render: near chair-sized; shrink uniformly
    side_table = scene.AddAsset("a small round dark wood side table")
    nook.place_on_left(side_table)
    nook.place_on_back(scene.AddAsset("a warm brass floor lamp with a fabric shade"))
    if PHASE >= 2:
        nook.place_on_top(scene.AddAsset("a modern table lamp with a warm fabric shade"))

# --- seating hero: sectional faces the hearth across the coffee table ---
sectional = scene.AddAsset("a cream three-piece sectional corner sofa",
                           asset_id=SECTIONAL)
with scene.RelativeGroup() as seating:
    seating.set_anchor(sectional)
    coffee = scene.AddAsset("a rustic rectangular solid wood coffee table",
                            asset_id=COFFEE, width=1.2)
    seating.place_on_front(coffee)
    seating.place_on_front_right_further(nook)   # nook flanks the cluster
    seating.face(nook, toward=coffee)            # side placements bake ±90° — angle it in
    if PHASE >= 2:
        seating.place_on_top([
            scene.AddAsset("a stack of decorative books"),
            scene.AddAsset("a white ceramic vase with branches"),
        ])
        seating.place_rug("a flat beige wool area rug", size=0.75, asset_id=RUG)
        # size=1.0 read as wall-to-wall carpet (cluster bbox ~ whole floor); 0.75
        # lets the dark walnut show around the seating zone
    if PHASE >= 3:
        seating.add_lighting("a flat round LED flush mount ceiling light", density=0)

# --- the room ------------------------------------------------------------------
fireplace = scene.AddAsset("a fireplace with a burning fire and a textured stone base",
                           asset_id=FIREPLACE, width=1.6)
bookcase = scene.AddAsset("a tall wood bookcase filled with books",
                          asset_id=BOOKCASE)
bookcase.scale(bookcase.get_width() * 2.0 / bookcase.get_height())  # ~2 m tall, uniform

with scene.RoomGroup(modulate_scale=1.1, randomness=0.15) as room:
    # RoomProportions voted enlarge in EVERY phase (1.2/1.25/1.1/1.1, never flipped)
    # -> real signal, applied the final-phase 1.1 (act-on-size-last rule)
    room.place_walls(floor_texture="dark walnut wood plank floor",
                     ceiling_texture="soft white plaster",
                     wall_texture="cool light gray paint")
    room.place_on_back_wall_center(fireplace)          # focal wall (auto hearth clearance)
    room.place_on_center(seating, facing="back")       # sectional looks at the fire
    room.place_on_left_wall_center(bookcase)           # visual mass balancing the hearth
    room.place_door("front_wall", position="left")     # in phase 1: clearance shapes the solve
    if PHASE >= 3:
        room.place_on_back_right_corner(
            scene.AddAsset("a leafy potted plant in a ceramic planter"))
        room.place_on_wall_back_center(
            scene.AddAsset("a collage of black framed photographs gallery wall",
                           asset_id="future/e2b0dcb4-c660-415b-8b1e-cddeb905441b"))
        # (the first pick, future/09f28392..., is REVERSED — its photo front faced the
        #  wall, showing brown backing boards — and its true front is four EMPTY frames;
        #  front-cached 180 for future users and swapped to a collage with real content)
        art = scene.AddAsset("a framed traditional landscape painting",
                             asset_id="hssd/4192b93682edc3c5585701c1ba90a34e9fd2f75b")
        art.scale_only_width(1.1); art.scale_only_height(0.75); art.scale_only_depth(0.04)
        room.place_on_wall_front_center(art)
        room.place_window_standard("right_wall", position="center",
                                   curtain="plum purple linen curtains")

scene.export("living_room_cozy.blend")
