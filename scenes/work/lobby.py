"""
Lobby — "Polished Corporate Lobby: Reception Anchor + Open Lounge" (planner-driven).

Layout pattern: single room, zoned (like executive_office) —
  * Reception anchor: the ingested wood+marble reception desk in the back third,
    staff chair tucked behind it, desk front facing the room; a colourful focal
    art panel on the wall behind it.
  * Waiting lounge: a symmetric AroundGroup (two 3-seat sofas + two accent
    armchairs around a coffee table) on a rug, dead-centre — the plan's open lounge.
  * Tall plants in the back corners, secondary art on the right wall,
    floor-to-ceiling windows on the left wall, glass entrance door front-centre,
    warm flush ceiling lighting (NOT a chandelier — exec-office lesson).

Reception desk hero = ingested custom/cffded... (wood frame + dark marble panels),
one of three reception desks the user supplied for this scene.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Lobby", seed=13)

# --- pinned assets (from the retrieval stress test) ---
_DESK   = "custom/cffdedd8d354e346e510f227b4a6bc5b65dc3dcb"  # ingested wood+marble reception desk (hero)
_SOFA   = "hssd/05206ad5b8ad9956a076ab73038089b964ddb2fd"    # straight beige 3-seat sofa (0.82)
_ARMCH  = "future/1c8dfc96-1144-4be8-8894-e064d672a86c"      # grey bouclé tub accent chair
_COFFEE = "future/40860cf0-4d90-409e-92dc-14e57ee94d70"      # minimalist wood coffee table
_SIDET  = "future/76d7a78e-2b24-45a3-aac6-f6ab2d7bcd57"      # round wood/metal side table (0.76)
_PLANT  = "hssd/08d9ae37bc8bc5e0dc07942d0c3ceaa0ea076f0c"    # tall potted plant (0.83)
_VASE   = "future/c6da6c9b-9b15-4c3e-a93b-2ae2f7266a01"      # white ceramic vase w/ branches
_RUG    = "hssd/249bbdc71be0aaa75d68f5a63cdb74b7a441aeda"    # flat beige wool rug
_FOCAL  = "hssd/5e9d4d4d61e99ba9604ea74dbab640f487771502"    # colourful abstract art (focal wall)
_ART    = "hssd/2b54eedde60d311599e833173ef0757ea4931ef9"    # B&W abstract art (right wall)

scene.prefetch_assets([
    "a black leather office task chair on casters",
    "a desktop computer",
    "a small potted plant",
])

# --- reception anchor: desk + staff chair behind + computer on top ---
with scene.RelativeGroup() as reception:
    desk = scene.AddAsset("a modern reception desk with a marble front", asset_id=_DESK, width=2.2)
    reception.set_anchor(desk)
    chair = scene.AddAsset("a black leather office task chair on casters")
    reception.place_on_back(chair)                 # staff side (behind the desk)
    computer = scene.AddAsset("a desktop computer")
    reception.place_on_top([computer, scene.AddAsset("a small potted plant")])
    # chair + computer orientation is fixed at room level below (face-to-wall needs a RoomGroup)

# --- waiting lounge: symmetric sofas + armchairs around a coffee table ---
with scene.AroundGroup(sparsity=0.4, jitter=0.3) as lounge:
    coffee = scene.AddAsset("a low minimalist wood coffee table", asset_id=_COFFEE, width=0.95)  # VLM: rescale coffee table by 0.8
    lounge.set_anchor(coffee)
    lounge.place_rectilinear(
        longer_side1=[scene.AddAsset("a straight modern beige three-seat sofa", asset_id=_SOFA)],
        longer_side2=[scene.AddAsset("a straight modern beige three-seat sofa", asset_id=_SOFA)],
        shorter_side1=[scene.AddAsset("a modern accent lounge armchair", asset_id=_ARMCH)],
        shorter_side2=[scene.AddAsset("a modern accent lounge armchair", asset_id=_ARMCH)])
    lounge.place_on_top(scene.AddAsset("an elegant white ceramic vase with branches", asset_id=_VASE))
    lounge.place_rug("a flat beige wool area rug", size=0.95, asset_id=_RUG)

# --- room: zone the reception (back) + lounge (centre), walls, decor, light ---
with scene.RoomGroup(modulate_scale=1.0, randomness=0.12) as room:   # 1.0 = acted on VLM "rescale room by 0.9"
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white ceiling",
                     wall_texture="warm greige painted wall")
    room.place_on_back(reception, facing="front")      # back third, desk faces the room
    room.face(chair, toward="front_wall")              # receptionist faces the room / entrance
    room.face(computer, toward="back_wall")            # VLM: screen was toward customers; turn it to face staff
    room.place_on_center(lounge, facing="front")       # waiting lounge centre
    room.place_on_back_left_corner(scene.AddAsset("a tall potted indoor plant in a planter", asset_id=_PLANT))
    room.place_on_back_right_corner(scene.AddAsset("a tall potted indoor plant in a planter", asset_id=_PLANT))
    room.place_on_front_left_corner(scene.AddAsset("a round wood and metal accent side table", asset_id=_SIDET))
    # focal + secondary art (pre-scaled via width= so the mount height doesn't clip the ceiling)
    room.place_on_wall_back_center(scene.AddAsset("a large vibrant colourful abstract framed wall art", asset_id=_FOCAL, width=1.8))
    room.place_on_wall_right_center(scene.AddAsset("a large framed abstract wall art print", asset_id=_ART, width=1.2))
    room.place_window_floor_to_ceiling("left_wall", curtain=None)   # bare glazing: curtain meshes render as ghost drapes over the night void
    room.place_door("front_wall", position="center")
    # Clean flush DISC + modulate_scale to enlarge each + very low density -> ~9 tidy fixtures.
    # (N = 1 + (max_lights-1)*density; max_lights ~ ceiling_area / fixture_area, so a bigger
    # fixture AND a low density are both needed. "square panel" retrieved a spotlight-on-arm; the
    # round flush-mount disc is the clean mesh.)
    room.add_lighting("a flat round LED flush mount ceiling light", density=0.03, modulate_scale=2.2)

scene.export("lobby.blend")
