"""
Modern private office — "Daylight-Driven Green-Enclosed Office Nook" (planner headline).

Built on the executive_office skeleton (storage backbone + desk hero) but re-cut for the
plan's smaller, greener, daylight-forward brief: no lounge zone, one hero work zone.

Layout (the private-office procedural signature):
  CENTER    = the hero work zone -- a WorkstationGroup (warm-wood desk + black task chair +
              iMac + articulated task lamp + pen cup) on a woven rug, placed facing="back"
              so the operator sits on the storage side and looks OUT at the window wall.
  BACK wall = the storage backbone: the tall book-filled bookcase (LEFT) + the 3-drawer
              filing cabinet with a plant on it (RIGHT). Back-CENTER is deliberately left
              EMPTY -- the interior cameras sit at each wall's center at ~1.4 m, and a 2.2 m
              bookcase parked there blinds that view and triggers phantom rotation flags
              (bakery v1 lesson).
  FRONT wall= daylight: a STANDARD punched window (never place_window_picture -- the renderer
              has no exterior environment, so a wide opening is a wall of black void) with a
              tall fiddle-leaf fig beside it.
  LEFT/RIGHT= the light walls: one framed print each (both meshes verified FLAT, d<=0.05 m),
              plus the entry door on the right.

Lighting: ONE compact FLUSH ceiling fixture at density=0.01 (small room). No chandelier --
add_lighting caps fixture height at 1.5 m but pins the origin at the ceiling, so a hanging
fixture drops into the room as giant emissive globes and blows the exposure out
(executive_office v1). The desk task lamp carries the warm/decorative layer.

Palette: warm oak floor + deep green walls + warm-wood desk + black task chair + greenery.
The green is carried by the WALL TEXTURE as a single colour+material string ("deep green
painted wall") -- an accent clause smuggled into a texture string recolours the whole room
(classroom v1) -- and reinforced by the plants, which is where a palette accent belongs.

Heroes measured offline with get_whd() before the first build (hospital_room lesson):
desk 1.50x0.82x0.66 (flat top), chair 0.50w/0.84h -> 0.6w, bookcase 0.80w/2.17h (BOOKS on the
shelves -- an empty fixture names the fixture, not the room), file cabinet 0.40w/0.61h -> 0.5w,
plant 0.40w/0.95h -> height-fit to ~1.6 m ("tall" plant), iMac 0.50x0.36 (bundles keyboard +
mouse; the dataset has no standalone keyboard), art 0.60x0.05 / 0.50x0.02 (flat = wall-safe).

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor layout.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("ModernOffice", seed=21)

# --- pinned heroes (audited by eye on the contact sheets, then measured) ---
DESK      = "future/4d763507-ca63-437a-827e-e66fcececbe8"     # warm-wood flat top (1.80x0.72x0.90), black metal legs
# (the executive_office desk hssd/68049539... is the same class but its top renders WHITE, which
#  kills the plan's warm-wood-against-green palette -- caught in the phase-1 render, not by the VLM)
CHAIR     = "hssd/2502dd408e62b2aa751080d4555d9b126f5a8d22"   # black mesh-back task chair on castors
BOOKSHELF = "hssd/2e29b3aa38387e1a9682778d64f27e8a9ec40296"   # tall bookcase, shelves FILLED with books
FILE      = "hssd/8090916af54ef2700b78f6a3ed489b4ab21f54a3"   # black 3-drawer filing cabinet
PLANT     = "future/f3a1cc15-c18b-49e7-be30-8f7698a26129"     # fiddle-leaf fig, white ceramic pot
IMAC      = "hssd/d41c6620aab11d8fde10b5e24b37b38e3c928c5b"   # all-in-one desktop (screen+keyboard+mouse)
LAMP      = "hssd/a980ba02a55b4f8bd67d9e1c6dc2231679bc82c9"   # black articulated desk task lamp
ART_LAND  = "hssd/b9c49bfce9696145e4328cd3e23b5b3e9eeb5b78"   # framed abstract landscape (real artwork)
ART_ABS   = "hssd/18a5ab4d9f66855d5fcf59051ec83820a4a49f14"   # framed textured abstract, neutral tones
# NOT used: hssd/fd940fdb... ranked #1 for "warm abstract print" but previews as a BLANK white
# rectangle -- the empty-frame trap (living_room_cozy v2); both pins above have visible art.

scene.prefetch_assets([
    "a modern warm wood writing desk with slim metal legs",
    "a modern black ergonomic office task chair with wheels",
    "a tall wooden open bookshelf with books on the shelves",
    "a low black office filing cabinet with drawers",
    "a tall potted fiddle leaf fig plant in a ceramic planter",
    "a desktop computer with monitor keyboard and mouse",
    "a black articulated desk task lamp",
    "a black pen cup with pens and pencils",
    "a small potted succulent in a ceramic pot",
    "a large framed abstract landscape art print",
    "a framed textured abstract art print in neutral tones",
    "a beige woven area rug with an abstract brown pattern",
    "a flat round LED flush mount ceiling light",
])

# --- CENTER: the hero work zone (desk + chair + screen + task lamp + pen cup) ---
# WorkstationGroup: operator side is the desk's local +Z and the chair faces the desk, so
# place_on_center(..., facing="back") seats the user on the storage-wall side looking out at
# the window wall -- the classic power layout (executive_office, reconfirmed).
with scene.WorkstationGroup() as station:
    desk = scene.AddAsset("a modern warm wood writing desk with slim metal legs", asset_id=DESK)
    station.set_anchor(desk)

    chair = scene.AddAsset("a modern black ergonomic office task chair with wheels", asset_id=CHAIR)
    chair.scale(0.6)                       # uniform: 0.50 m wide native -> 0.6 m (~1.0 m tall task chair)
    station.place_chair(chair)

    if PHASE >= 2:
        # <= 3 desktop items (MAX_DESKTOP_ITEMS): the screen + the two best accessories.
        # place_computer aims the screen at the operator for us -- an orientation-sensitive
        # on-top item never gets aimed by the placement tournament (computer_room v1).
        station.place_computer(scene.AddAsset("a desktop computer with monitor keyboard and mouse",
                                              asset_id=IMAC))
        station.place_accessories([
            scene.AddAsset("a black articulated desk task lamp", asset_id=LAMP),
            scene.AddAsset("a black pen cup with pens and pencils"),
        ])
        # the rug frames the work zone; kept well under the cluster bbox so the oak floor
        # still reads around it (living_room_cozy: an over-sized rug reads as wall-to-wall carpet)
        station.place_rug("a beige woven area rug with an abstract brown pattern", size=0.8)

    if PHASE >= 3:
        # ONE compact flush disc. density is a fixture COUNT that scales with floor area:
        # 0.01 for a room this small (0.02+ starfields -- music_studio/coffee_shop lessons).
        station.add_lighting("a flat round LED flush mount ceiling light", density=0.01)

# --- BACK wall: the storage backbone ---
bookshelf = scene.AddAsset("a tall wooden open bookshelf with books on the shelves",
                           asset_id=BOOKSHELF)

# the filing cabinet is its OWN unit so the succulent lands on the CABINET's top surface:
# place_on_top always targets the group's ANCHOR, never a child (living_room_cozy v3).
file_cabinet = scene.AddAsset("a low black office filing cabinet with drawers", asset_id=FILE)
file_cabinet.scale(0.5)                    # 0.40 m native -> 0.5 m wide (~0.76 m tall, a real 3-drawer unit)
with scene.RelativeGroup() as file_unit:
    file_unit.set_anchor(file_cabinet)
    if PHASE >= 2:
        file_unit.place_on_top(scene.AddAsset("a small potted succulent in a ceramic pot"))

# --- the greenery accent by the window ---
plant = scene.AddAsset("a tall potted fiddle leaf fig plant in a ceramic planter", asset_id=PLANT)
plant.scale(plant.get_width() * 1.6 / plant.get_height())   # uniform height-fit: 0.95 m -> ~1.6 m

# modulate_scale=0.8 acts ONCE, in the final phase, on a unidirectional shrink vote train
# (0.67 Ph1 -> 0.7 Ph1 -> 0.8 Ph2, decaying toward neutral as occupancy rose = converging).
# Held it through phases 1-2 per render-wins-early; 0.8 is picked AT the latest vote rather
# than below it (bakery: choosing a value near the vote converges in one step, not two).
with scene.RoomGroup(modulate_scale=0.8, randomness=0.15) as room:
    room.place_walls(floor_texture="warm oak wood flooring",
                     ceiling_texture="white",
                     wall_texture="solid deep green smooth uniform wall")
    # Texture strings are EMBEDDING-matched against the library's CAPTION text, so word them like
    # a caption, not like a paint chip -- and verify the match offline (embed the query against
    # IDSDL/assets/wall_textures_embeddings.npz, read the winning caption) rather than burning
    # 8-minute builds on re-wordings. Three wordings tried, and they separate the two failure modes:
    #   "deep green painted wall"  -> matched a PALE green stucco -> rendered BEIGE  (a WORDING bug)
    #   "a dark olive green color with subtle irregular brush strokes" -> matched the library's
    #      darkest green at 0.82 ... and still rendered GREY-TAUPE (a RENDERER limit: the room-scale
    #      tiling + light budget wash a dark olive out, exactly the bakery brick lesson) -- so a
    #      correct match is NOT a guarantee of the colour you asked for; check the render, and when
    #      the match is already right, stop re-wording and pick a colour that survives the wash.
    #   "solid deep green smooth uniform wall" (this one) -> a true saturated green that HOLDS under
    #      the light budget. It reads brighter than the plan's forest green, but it is the plan's
    #      defining "green enclosure"; the grey it would otherwise wash to is not.

    # Phase 1 — the floor masses. Five occupied slots = a cozy private office by construction.
    room.place_on_center(station, facing="back")      # operator faces the room/window
    room.place_on_back_wall_left(bookshelf)           # backbone LEFT, not center (keeps the back camera clear)
    room.place_on_back_wall_right(file_unit)
    room.place_on_front_left_corner(plant)            # greenery beside the daylight wall
    room.place_door("right_wall", position="right")   # door clearance is automatic

    if PHASE >= 3:
        # daylight on the wall the operator faces. STANDARD pane, not a picture window:
        # any opening renders as a black night void, so keep it modest and let the sheer
        # curtains frame it (executive_office / retail_store window lesson).
        room.place_window_standard("front_wall", position="center", curtain="sheer white curtains")
        # the light walls: one print each, in slots the door doesn't claim
        room.place_on_wall_left_center(scene.AddAsset("a large framed abstract landscape art print",
                                                      asset_id=ART_LAND))
        room.place_on_wall_right_center(scene.AddAsset("a framed textured abstract art print in neutral tones",
                                                       asset_id=ART_ABS))

scene.export("office_modern.blend")
