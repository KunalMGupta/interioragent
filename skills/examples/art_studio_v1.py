"""
Art studio — "North-Light Painter's Loft" (planner target:
tmp/plan_An_art_studio___painter_s_loft__/plan.png).

Supersedes the 29-line auto-generated draft (a place_circle of 4 easels around a supply
table), which was never built. The planner's brief is a different, better room: ONE hero
painting zone worked in daylight, not a ring of easels.

Zone map (the studio procedural signature: work zone on the glass, storage backbone opposite):
  LEFT (long, GLAZED)  = the north light. Floor-to-ceiling glazing + the two EASELS standing
                         in it, turned to face the room so the camera sees the canvases.
  CENTRE               = the hub: the paint-splattered work table + the painter's stool, the
                         brushes/palette/paint-tube still life on the top, an architect lamp,
                         a jute rug under it all.
  RIGHT (long)         = the storage backbone: the stocked shelf + the loaded supply cart,
                         with one finished painting hung between them.
  BACK (short)         = the drying/leaning wall: a packed row of canvases standing on the floor.
  FRONT (short)        = the door.

v2 -- REBUILT ON INGESTED EASELS (Kunal supplied art_done.zip, 2026-07-13).

  The hero of this room is now a REAL floor easel holding a REAL painting (custom/fa1ed245,
  2.00 m). Everything v1 fought is simply gone, and the diff is the whole lesson:

  * v1 had to hunt by silhouette for the one bare wood A-frame in the dataset, because the visual
    picker's rank-1 for "an artist easel with a canvas" was a KIDS' easel holding a crayon drawing
    of a sunny house (fine geometry, fine caption, fatal semantics -- it would have made this room
    read as a kindergarten, and no VLM constraint can see that).
  * v1 then could not put a canvas ON that easel: `place_on_top` SHATTERS on a skeletal A-frame
    (no substantial horizontal region -> the tiler clamps the canvas to a crossbar sliver ->
    a postage-stamp canvas), and there is no vertical lift on an anchor-group placement.
    So v1 stood the canvas on the FLOOR against the easel, and had to anchor the composed unit on
    the CANVAS (not the easel) to stop the placement verb turning its blank back to the room.
  * ALL OF THAT IS DELETED. The canvas is modelled into the mesh. No composition, no tournament,
    no facing puzzle -- one AddAsset, one placement.

  THE LESSON (operating_room's, escalated): when a scene is "clean but doesn't convince", the
  answer is usually ASSETS, not placement. One correct mesh removed ~40 lines of workaround.

Still true, and still carrying the room:

1. CANVASES LEANING ON A WALL are not a mesh -- but a canvas IS a flat upright slab
   (d = 0.02 m). Standing several of them as FLOOR objects flush to the back wall, packed in a
   deterministic GridGroup row, reads exactly as canvases lined up against the wall. It costs
   ONE floor slot for four canvases (the greenhouse plant-bed trick, applied to canvases).

2. THE EASELS ARE 2.00 m -- well above the ~1.4 m interior cameras -- so they are kept OUT of the
   left wall's CENTRE slot (back_left + front_left instead). A tall fixture at a wall centre
   blinds that view and hallucinates rotation flags (bakery). v1's easels were 1.65 m and already
   loomed in the left view; at 2.00 m the centre slot is not survivable.

3. Two ingested meshes were REJECTED at the contact sheet, exactly as the rule predicts (filenames
   lie; the preview is the evidence): `canvas_stretcher` renders as a grey tapered MONOLITH, not a
   canvas; `easel_stool_and_canvases` is flat-shaded stylised red/blue artwork that would clash
   with a photoreal room. 11 of 13 art meshes usable -- a good yield.

Daylight: the brief's "big north-facing window light" is a SKY problem, not an add_lighting
problem (add_lighting spends a fixed 500 W across N fixtures, so density only ever buys more,
dimmer lamps). Glaze the long wall floor-to-ceiling and let the sky in -- the black-void lore
is obsolete since the greenhouse renderer fix. The ceiling fixtures are a calm flush row; the
architect lamp on the table is the warm task layer.

Palette (from the collage): concrete floor + calm white gallery walls + warm wood (easel,
table, shelf) + the paintings as the only colour. The colour lives on the PROPS, never in a
wall-texture accent clause (classroom v1's teal disaster).

Phase-gated (IDSDL/phases.py): `workbench run scenes/art_studio.py --phase 1` builds only the
floor layout (~1 min) instead of the full ~8.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("ArtStudio", seed=13)

# --- INGESTED heroes (art_done.zip -> IDSDL.ingest; every preview eyeballed on the contact sheet).
# Pinning by id is MANDATORY for ingested assets, not a preference: the ingest VLM's caption is a
# guess, and a mis-captioned mesh is invisible to NL retrieval (operating_room v2).
EASEL_ART  = "custom/fa1ed2452840e6ccdbd1d6245c1873894686df04"  # THE HERO: wood floor easel holding a PAINTED landscape (0.96 x 2.00)
EASEL_BLNK = "custom/3ae587371564779c57537d23392c240602aa70e7"  # wood floor easel holding a BLANK canvas (0.96 x 2.00)
PROPS      = "custom/65b641003dcd65f9e65ff7388e35f3be67df4977"  # open wooden paint box + palette + brushes (0.50)
PAINTBOX   = "custom/b1b89b40c0321f59bf7ffdc09810cc76abb6cb78"  # closed paint case + a paint-smeared palette (0.51)
CART       = "custom/4d5c0810966a3a085ad0b1fa46e2a331a96ae9bf"  # rusty red 3-tier rolling art supply cart (0.58 x 1.00)
# REJECTED at the contact sheet: custom/cd21f376... ("canvas_stretcher") renders as a grey tapered
# MONOLITH on a base, not a canvas; custom/bbe6683f... ("easel_stool_and_canvases") is flat-shaded
# STYLISED red/blue art that would clash with a photoreal room. Filenames lie; the preview decides.

# --- dataset pins (kept from v1) ---
TABLE    = "hssd/b752a35d7bd02b5d35fef7d25e9b18f8158e67d0"   # rustic warm-wood trestle table, FLAT single top (1.50 x 0.63)
STOOL    = "hssd/5cbddc4215af577a945d42dae708197b48a6a14e"   # three-legged wooden painter's stool (0.40 x 0.63)
SHELF    = "hssd/2db50fb1f8120974d6157ae9aff704a4fc9d181f"   # warm-wood shelf, shelves modelled FULL (1.20 x 1.60 x 0.32)
SUPPLIES = "future/4a9dc3a5-297a-4dae-9fc8-6683e52a0606"     # brushes in a glass jar + palette + paint tubes
LAMP     = "hssd/a980ba02a55b4f8bd67d9e1c6dc2231679bc82c9"   # black articulated architect task lamp (office_modern's pin)
# the four canvases -- all verified to carry REAL artwork, not blank frames (office_modern's
# empty-frame trap: an empty frame and a reversed front look identical from behind)
CANVAS_A = "hssd/c96b33101041fa3ab53246e8b73fc9d37d092a1a"   # multicolour banded oil (0.50 x 0.75 x 0.02) -- the work in progress
CANVAS_B = "hssd/4820e7f84385d1e39347154daecad22645d10e3f"   # vibrant square abstract (0.30 -- small, height-fit)
CANVAS_C = "hssd/88228361dca94dc02e640c3ee16d008d918fb635"   # green/blue abstract portrait (0.30 x 0.40 -- small, height-fit)
CANVAS_D = "hssd/7acc577508ee43db1a2c574c901a1b56e10f2d30"   # sunflowers oil (0.40 x 0.80) -- the warm note

scene.prefetch_assets([
    "a rustic wooden work table with a flat top",
    "a three legged wooden painter's stool",
    "a tall wooden shelf filled with books and supplies",
    "paintbrushes in a glass jar with a paint palette and tubes",
    "a black articulated architect task lamp",
    "a colourful abstract oil painting on canvas",
    "a vibrant square abstract canvas",
    "an abstract portrait canvas in green and blue",
    "an oil painting of sunflowers on canvas",
    "a natural jute woven area rug",
    "a slim linear LED tube ceiling light",
])


def fit_height(obj, h):
    """Scale UNIFORMLY to a target HEIGHT (dsl_reference: scale(width * H / height)).

    Used on the easel and the canvases, which are TALL forms -- the greenhouse rule is
    height-fit only things that are tall, width-fit anything that might be flat, because a
    uniform height-fit on a flat trough detonates it. NB obj.scale() returns None: never chain.
    """
    obj.scale(obj.get_width() * h / obj.get_height())
    return obj


# --- LEFT: the two easels, standing in the north light, turned to face the room ---
# ONE AddAsset each. The canvas is modelled INTO the mesh, so there is no composed unit, no
# place_on_top tournament to lose, no anchor-facing puzzle, and no height-fit: these load at a
# true 2.00 m. This is the ~40 lines that the right asset deleted.
easel_1 = scene.AddAsset("a wooden artist easel holding a painted canvas in progress",
                         asset_id=EASEL_ART)
easel_2 = scene.AddAsset("a wooden artist easel holding a blank white canvas",
                         asset_id=EASEL_BLNK)

# --- CENTRE: the hub -- the paint-splattered work table + the painter's stool ---
# A RelativeGroup anchored on the TABLE so place_on_top seats the still life on the TABLE's
# top, not on the stool's seat (living_room_cozy v3: a lamp landed on an armchair cushion).
work_table = scene.AddAsset("a rustic wooden work table with a flat top", asset_id=TABLE)
fit_height(work_table, 0.76)         # 0.63 m native -> a real 0.76 m bench height (w -> ~1.81 m)
stool = scene.AddAsset("a three legged wooden painter's stool", asset_id=STOOL)
fit_height(stool, 0.68)

with scene.RelativeGroup() as bench:
    bench.set_anchor(work_table)
    bench.place_on_front(stool)      # the painter's seat, on the room side of the table
    bench.face(stool, toward=work_table)

    if PHASE >= 2:
        # The still life IS the scene's product (jewelry_shop: an empty fixture names the
        # fixture, not the room). THREE on-top items -- the cap -- so the table reads worked-at:
        # the ingested open paint box + palette + brushes, the jar of brushes, and the lamp.
        bench.place_on_top([
            scene.AddAsset("a set of paint tubes brushes and a palette", asset_id=PROPS),
            scene.AddAsset("paintbrushes in a glass jar with a paint palette and tubes",
                           asset_id=SUPPLIES),
            scene.AddAsset("a black articulated architect task lamp", asset_id=LAMP),
        ])
        # the rug zones the work floor; kept well under the cluster bbox so the concrete still
        # reads around it (living_room_cozy: an over-sized rug becomes wall-to-wall carpet)
        bench.place_rug("a natural jute woven area rug", size=0.75)

    if PHASE >= 3:
        # A calm row of flush tubes. density is a fixture COUNT that grows with floor area, and
        # this is a ~40 m2 room: 0.01 is the calibrated band (music_studio tripped the starfield
        # lint at 0.02 on 38 m2). Brightness comes from the SKY through the glazing, never here.
        bench.add_lighting("a slim linear LED tube ceiling light", density=0.01)

# --- BACK: the leaning wall -- four canvases standing on the floor against it ---
# No 'leaning canvas' mesh exists. A canvas is a flat upright slab, so standing them as FLOOR
# objects flush to the wall reads as canvases lined up against it. A GridGroup is deterministic
# (no overlap solve), so a near-zero sparsity packs them until they nearly touch -- the
# greenhouse plant-bed trick: FOUR canvases for ONE floor slot, so the shell does not balloon.
lean = [
    fit_height(scene.AddAsset("an oil painting of sunflowers on canvas", asset_id=CANVAS_D), 1.15),
    fit_height(scene.AddAsset("a vibrant square abstract canvas", asset_id=CANVAS_B), 0.85),
    fit_height(scene.AddAsset("a colourful abstract oil painting on canvas", asset_id=CANVAS_A), 1.05),
    fit_height(scene.AddAsset("an abstract portrait canvas in green and blue", asset_id=CANVAS_C), 0.95),
]
with scene.GridGroup(sparsity=0.04, randomness=0.3) as canvas_stack:
    canvas_stack.place_row(lean)     # mixed heights + jittered gaps = a working stack, not a CAD array

# A SECOND canvas stack by the door was built, measured and CUT. It was meant as the "fill the
# floor rather than shrink" answer to the room-size vote (children_room/kindergarten), but the
# shell grew 5.60 -> 6.86 m wide the moment it existed -- in a front-WALL slot AND in a corner
# floor slot alike (both measured off the exported floor mesh). Filling only beats shrinking when
# the fill is free: a bed of plants costs one slot because it is ONE object, whereas a composed
# row lands in a row/column the shell must then grow to fit. So the room-size thread is settled
# with modulate_scale below, not with more furniture.

# --- RIGHT: the storage backbone ---
shelf = scene.AddAsset("a tall wooden shelf filled with books and supplies", asset_id=SHELF)
# The cart stays on the WALL. Parking it in the `right` FLOOR slot (v1) read better in theory --
# a rolling cart lives at arm's reach of the painting hand -- but the middle slot-row then had to
# fit easel + table + cart, and the shell blew out 5.60 -> 6.70 m wide while the DEPTH collapsed
# to 4.39 m, jamming the back camera against the table. Room size is a consequence of slot
# occupancy (kitchen's bloated-cluster lesson): one extra item in an occupied ROW costs a metre
# of width. A wall placement costs no floor slot, so the cart goes back to the wall.
cart = scene.AddAsset("a rolling metal art supply tool cart with drawers", asset_id=CART)

# modulate_scale=0.85: the shrink vote never once flipped across seven builds (0.75 / 0.7 / 0.81 /
# 0.5 / 0.7 / 0.65 / 0.75) -- unidirectional, so it is signal, not noise (living_room_cozy's
# vote-train rule) -- but its MAGNITUDE bounces, and obeying the 0.5 would give a 2.8 x 2.5 m
# closet. A painter has to STEP BACK to judge a canvas; that open floor is the category, not
# emptiness, exactly like the garage's vehicle lane and the corridor's centre lane. So: shrink
# TOWARD the vote and stop short of it (operating_room). 0.85 takes 5.60 x 4.97 -> ~4.76 x 4.22 m,
# which still clears the rigid back-wall canvas row (2.2 m) and the shelf+cart run, so it cannot
# trip the locker_room overflow.
with scene.RoomGroup(modulate_scale=0.85, randomness=0.15) as room:
    # Plain colour + material words, all three verified wordings from earlier scenes. The
    # palette's colour is carried by the PAINTINGS -- an accent clause smuggled into a wall
    # string recolours the whole room (classroom v1's teal disaster).
    room.place_walls(floor_texture="smooth cool grey concrete floor",
                     ceiling_texture="smooth white ceiling",
                     wall_texture="smooth white painted plaster wall")

    # -- Phase 1: the floor masses. Four occupied slots => a real studio, not a hall. --
    room.place_on_center(bench, facing="front")
    # The easels stand IN the daylight and turn their canvases toward the room (facing="right"
    # points them at the room centre from the left side). Lining furniture along a wall you also
    # glaze is established (greenhouse's bench runs on the glass).
    # They are kept OUT of the `left` (mid-wall) slot: the interior cameras sit at each wall's
    # CENTRE at ~1.4 m, and these easels are 2.00 m. v1's 1.65 m easels already loomed over the
    # left view from that slot; at 2.00 m it would blind it outright and hallucinate rotation
    # flags on a correct layout (bakery). back_left + front_left keep the sightline open.
    room.place_on_back_left(easel_1, facing="right")
    room.place_on_front_left(easel_2, facing="right")
    # The canvas row goes flush to the wall as a composed group -- a floor SLOT would let it
    # drift mid-room (bakery's window bar, kindergarten's stranded nook). At ~1.15 m it stays
    # under the ~1.4 m interior camera, so it never blinds the back view (bakery).
    room.place_on_back_wall_center(canvas_stack)

    # The backbone. The shelf is 1.60 m -- ABOVE the interior camera that sits at each wall's
    # CENTRE, so it goes in the LEFT slot and the centre stays clear (office_modern applied the
    # bakery blinded-view rule preventively; do the same here).
    room.place_on_right_wall_left(shelf)     # facing OMITTED: the heuristic already faces it into the room
    room.add_clearance(shelf, distance=0.6, dir="front")   # reach/standing space at the shelves
    room.place_on_right_wall_right(cart)     # a wall slot, not a floor slot -- see the note above

    room.place_door("front_wall", position="right")        # door clearance is automatic

    if PHASE >= 3:
        # THE NORTH LIGHT. Glaze the long wall floor-to-ceiling: place_window_floor_to_ceiling
        # tiles a real mullion frame and REMOVES the wall, and since the greenhouse renderer fix
        # (opaque film + raised sky) that reads as daylight, not as a black void. No curtain --
        # a painter's north window is never dressed; you want the light.
        room.place_window_floor_to_ceiling("left_wall", curtain=None)
        # One finished painting hung on the backbone wall, in the CENTRE slot the shelf and cart
        # leave free. Genuinely flat (0.02 m) so it is a legitimate wall hang, and nothing tall
        # stands in its span, so the auto wall-object clearance has nothing to slide.
        room.place_on_wall_right_center(scene.AddAsset("an oil painting of sunflowers on canvas",
                                                      asset_id=CANVAS_D, width=0.9))

scene.export("art_studio.blend")
