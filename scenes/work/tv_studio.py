"""
TV studio — "Anchor-Centric Curved Desk Studio Core" (planner headline). Built via the guided
9-gate flow: plan -> retrieve -> asset audit -> phased build.

Layout = the procedural signature's hero-set-piece + camera-lane split, down the room centerline:
  - BACK    = the SET: the curved anchor desk (hero) with two anchor chairs seated behind it,
              facing across the desk into the camera. Grounded on a dark studio carpet.
  - BACK WALL = the backdrop: a geometric panel field flanked by two large wall monitors
              (the focal background every camera shot frames).
  - FRONT   = the CAMERA LANE: the studio camera on its tripod on the centerline, aimed at the
              desk, flanked by a key and a fill light on stands. The front third stays clear.
  - RIGHT WALL = the gear spine: a stocked equipment rack (offset off-center so it doesn't blind
              the right-wall interior camera — bakery lesson).
  - LEFT/RIGHT walls = light acoustic treatment only; FRONT wall = the entry door + greenery.
  - No windows: a broadcast studio is deliberately blacked out (and it dodges the render's
              black-void window limit entirely).

Asset audit notes (gate 3) — three real gaps, all substituted, none blocking:
  * No professional BROADCAST CAMERA exists (the query returns telescopes, tripod LAMPS and
    handheld camcorders). The one true camera-on-tripod mesh is hssd/6d5c2629 ("antique metal
    camera with a tripod") — a boxy body + lens on a splayed tripod. Pinned AND scaled to a real
    1.5 m height (garage-car rule: pin the id, then pin a real-world dimension).
  * No SOFTBOX / LED panel on a light stand. hssd/4c5ab0e1 (a tripod-base floor lamp whose head
    is a tilted disc) is the studio light-stand silhouette; two of them = key + fill.
  * No true NEWS DESK. future/8f7519b8 is a curved SOLID-front desk (closed modesty panel) —
    stretched to width=2.4 it is an anchor desk, and its facade faces the camera.
Chairs pinned for PALETTE (an unpinned pick flips colour between runs — jewelry_shop lesson).

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor layout.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("TVStudio", seed=42)

ANCHOR_DESK  = "future/8f7519b8-9e6f-4712-a3c0-659866828ca8"   # curved solid-front dark wood desk (the news desk)
ANCHOR_CHAIR = "hssd/b1b3d0674a74eacaddf0beea66e5679eba96e9d3"  # navy blue swivel chair, metal base
CAMERA       = "hssd/6d5c2629c7b850db989fbd29612e451dc1a25f69"  # camera body + lens on a tripod (the studio camera)
LIGHT_STAND  = "hssd/4c5ab0e1837626c90f8ab2431ea54013d0245ca4"  # tilted disc head on a tripod stand (the studio light)
WALL_TV      = "hssd/576f0a57271ccc62554b2603a48047854254119d"  # large flat-screen display (1.2 m -> scale up)
BACKDROP     = "future/2ab78653-2dc7-49ad-b1fd-524b494347b6"    # black geometric wall panel (thin, wall-hang safe)
PANEL_GRID   = "future/540e8add-3553-485e-bee6-bb56a5b86aac"    # upholstered grid acoustic panel
GEAR_RACK    = "future/9f6fd95f-f16b-409b-a34b-dd7668545e63"    # tall black shelf cabinet (the equipment rack)
RACK_GEAR    = "future/4c6888e5-5e3d-410b-8401-f5264243871d"    # stereo system w/ dual speakers (rack gear)
LAPTOP       = "hssd/57d2b6c1b3bb6903c7683cff9ba9016a8c50ff70"  # open silver laptop
MIC          = "hssd/7b2ed578ddbdebd16402325998289f48bc91ed06"  # black microphone on a stand

scene.prefetch_assets([
    "a curved modern news anchor desk with a solid front panel",
    "a blue upholstered swivel office chair",
    "a professional video camera on a black tripod",
    "a studio light on a black tripod stand",
    "a large wall-mounted flat screen display",
    "a black geometric acoustic wall panel",
    "an upholstered grid pattern acoustic wall panel",
    "a tall black studio equipment rack cabinet",
    "a modern black stereo system with dual speakers",
    "an open silver laptop computer",
    "a black microphone on a silver stand",
    "a white ceramic coffee mug",
    "a large dark grey commercial area rug",
    "a flat square LED flush mount ceiling light panel",
])

# --- the SET: curved anchor desk + two anchors seated behind it, facing the camera ---
desk = scene.AddAsset("a curved modern news anchor desk with a solid front panel",
                      asset_id=ANCHOR_DESK, width=2.4)
chair_l = scene.AddAsset("a blue upholstered swivel office chair", asset_id=ANCHOR_CHAIR)
chair_r = scene.AddAsset("a blue upholstered swivel office chair", asset_id=ANCHOR_CHAIR)
with scene.GridGroup(sparsity=0.5) as seat_pair:      # the two anchors, side by side
    seat_pair.place_row([chair_l, chair_r])

with scene.RelativeGroup() as anchor_set:
    anchor_set.set_anchor(desk)
    # the anchors sit BEHIND the desk (v1 bug: place_on_back_left/right stranded them out at the
    # desk's ENDS) and look across it into the camera
    anchor_set.place_on_back_adjacent(seat_pair)
    anchor_set.face(seat_pair, toward=desk)
    if PHASE >= 2:
        # the desk reads as a NEWS desk through its props (empty-fixture rule).
        # (No desk mics: the only mic mesh is a FLOOR mic-on-stand, and place_on_top's tournament
        #  height-fits it to the desk regardless of modulate_scale -> two oversized lollipops.)
        laptop = scene.AddAsset("an open silver laptop computer", asset_id=LAPTOP)
        anchor_set.place_on_top([
            laptop,
            scene.AddAsset("a white ceramic coffee mug"),   # ("a stack of papers" -> Post-it blob)
        ])
        # place_on_top BAKES a rotation and never aims the item — an orientation-sensitive prop
        # needs an explicit face() (computer_room's monitors). The laptop screen faces its user.
        anchor_set.face(laptop, toward=seat_pair)
        anchor_set.place_rug("a large dark grey commercial area rug", size=0.8)

# --- the CAMERA LANE: studio camera on the centerline, key + fill lights flanking it ---
camera = scene.AddAsset("a professional video camera on a black tripod", asset_id=CAMERA)
camera.scale(camera.get_width() * 1.5 / camera.get_height())   # uniform -> a real 1.5 m camera height
key_light = scene.AddAsset("a studio light on a black tripod stand", asset_id=LIGHT_STAND)
fill_light = scene.AddAsset("a studio light on a black tripod stand", asset_id=LIGHT_STAND)
for _lt in (key_light, fill_light):
    _lt.scale(_lt.get_width() * 1.85 / _lt.get_height())        # light stands tower over the desk

# (the lights are NOT nested in a camera group: the *_further verbs bake +-90 deg, which turned
#  one dish's black back to the set. As room-level floor objects they take facing="back" and both
#  dishes aim at the desk — clean by construction.)

# --- the gear spine: a STOCKED equipment rack (an empty rack names the fixture, not the studio) ---
rack = scene.AddAsset("a tall black studio equipment rack cabinet", asset_id=GEAR_RACK)
rack.scale(rack.get_width() * 1.8 / rack.get_height())   # -> a real 1.8 m rack (it loads short)
with scene.RelativeGroup() as rack_station:
    rack_station.set_anchor(rack)
    if PHASE >= 2:
        rack_station.place_inside([
            scene.AddAsset("a modern black stereo system with dual speakers", asset_id=RACK_GEAR),
        ])

# --- the room ---
# modulate_scale: RoomProportions voted 0.8 / 0.8 / 0.82 across phases 1-2 (unidirectional and
# stable, and the render agreed the grey walls read empty) -> ONE decisive application, at the vote.
with scene.RoomGroup(modulate_scale=0.82, randomness=0.15) as room:
    room.place_walls(floor_texture="smooth dark grey concrete floor",
                     ceiling_texture="dark grey painted ceiling",
                     wall_texture="soft cool grey painted wall")

    # The set sits in the BACK FLOOR SLOT, a stride off the wall — the camera needs to see the
    # backdrop BEHIND the anchors' heads. (Tried flush to the wall via place_on_back_wall_center
    # to make the panel inherit the desk's width: the anchors' chair-backs then rose above the
    # panel's bottom edge and the wall-object clearance pass could not resolve it —
    # "[RoomGroup] WARNING: 'RelativeGroup' occludes wall-hung panel". The set must stand clear.)
    room.place_on_back(anchor_set, facing="front")
    room.place_on_front(camera, facing="back")
    room.place_on_front_left(key_light, facing="back")
    room.place_on_front_right(fill_light, facing="back")

    # facing="back" only points the stands at the back WALL — from the lane's left and right corners
    # that still turns a dish away from the anchors. face() runs at the END of compile, off the
    # settled positions, so it angles each dish IN at the set (the real key/fill pose).
    room.face(key_light, toward=desk)
    room.face(fill_light, toward=desk)
    room.face(camera, toward=desk)

    # gear rack against the right wall, OFF-CENTER: a >1.4 m fixture at a wall center sits inside
    # that wall's interior camera and blinds the view (bakery lesson). Default wall-facing.
    room.place_on_right_wall_left(rack_station)

    # entry door on the front wall (auto-clearance keeps the camera lane's corner walkable)
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # THE BACKDROP: the graphic panel flanked by the two studio monitors, as ONE freeform run.
        # (The three back-wall SLOTS were tried instead — they hang bigger, but they mount LOW:
        # the panel's bottom edge fell below the anchors' chair-backs, so the wall-object clearance
        # pass tried to slide the whole set out of its span, failed, and cascaded a second warning
        # onto the left-wall panel. Freeform mounts at mid-wall and clears the set cleanly.)
        room.place_on_wall_freeform("back_wall", [
            scene.AddAsset("a large wall-mounted flat screen display", asset_id=WALL_TV),
            scene.AddAsset("a black geometric acoustic wall panel", asset_id=BACKDROP),
            scene.AddAsset("a large wall-mounted flat screen display", asset_id=WALL_TV),
        ])

        # side walls stay light: one acoustic panel each
        room.place_on_wall_left_center(
            scene.AddAsset("an upholstered grid pattern acoustic wall panel", asset_id=PANEL_GRID))
        room.place_on_wall_right_center(
            scene.AddAsset("an upholstered grid pattern acoustic wall panel", asset_id=PANEL_GRID))

        # ONE calm flush layer overhead (a studio ceiling is a grid of panels, not a starfield);
        # the two light stands carry the actual studio-lighting read.
        anchor_set.add_lighting("a flat square LED flush mount ceiling light panel", density=0.01)

scene.export("tv_studio.blend")
