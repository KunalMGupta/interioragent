"""
Game room / recreation lounge — "Central Play Nexus".

LESSON this scene encodes: a rec room is a set of PLAY ZONES ringed around one hero. The billiards
table is the social anchor at the CENTRE; its cue-stroke clearance (space to draw a cue on every
side) is what actually sizes the room, so put it down first with an all-round clearance and let the
other zones settle around it. Cardio-faces-the-view logic from the gym applies here too: the lounge
sofa faces its TV, the foosball players face the window.

Zone map (window = RIGHT wall, feature/media = LEFT wall):
  - CENTRE            = BILLIARDS: 8-ft pool table on a bordered rug, one billiards pendant above.
  - BACK wall         = BAR social hub: counter + back-bar bottle cabinet + 3 stools; gallery
                        photos + a colourful painting above.
  - BACK-RIGHT corner = ARCADE: a pair of upright cabinets.
  - LEFT wall         = MEDIA/LOUNGE: wall TV over a low console; leather sofa facing it, flanked by
                        two green-velvet armchairs, coffee table between.
  - RIGHT wall        = window; FOOSBALL in front of it (players get the view).
  - FRONT-LEFT        = POKER: walnut card table with four chairs.
  - FRONT wall        = entry door (centre), trophy display cabinet (left), wall dartboard (right)
                        with an open throwing lane into the front-right.

Moody walnut / charcoal / brass palette, green feature wall behind the bar.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("GameRoom", seed=17)


def _fit_height(obj, target_h):
    """Uniformly scale obj so its height == target_h (m) -- pin real sizes for props whose
    description-driven scale can come out wrong."""
    w, h, d = (float(v) for v in obj.get_whd())
    if h > 1e-6:
        f = target_h / h
        obj.scale_only_width(w * f)
        obj.scale_only_height(h * f)
        obj.scale_only_depth(d * f)
    return obj


# ---- hero / games ----
_POOL      = "hssd/988e19a926492231c05b5d9b542f6d6cc0c1d3ca"   # 8-ft espresso, green felt
_FOOSBALL  = "hssd/99c1832511c8703634b467fa82a70442eb3040c0"
_ARCADE    = "hssd/3873f4b8fbf7b568ed6dca1b5d8878edb57e8e3d"
_DARTBOARD = "hssd/8b1f720d6bab266f0442535240773c3520eaba0b"
_POKER     = "hssd/81f092c5722ae67b49104b660bcf3f0fec3c69f0"
# ---- bar ----
_BARCOUNTER = "hssd/96aa481c97443d17b9946bc68e188bfd877c2ebf"
_BACKBAR    = "future/f92b65d2-a2d3-4430-a5cb-34a7b5bce7f3"
_BARSTOOL   = "hssd/d10ff3f71a5e1a0534fc43132d54b5a083b8d17f"
# ---- lounge ----
_SOFA     = "future/c9856517-b011-42f7-9a40-5da16d0b6f43"
_ARMCHAIR = "hssd/bf96d2cce0097d4eeb20de5e736103b626baf0ac"
_TV       = "hssd/52676f400fb7e2b9181f70a0fa1f53eb686a05b4"
_MEDIA    = "future/12b76671-ce59-4685-a05c-1e7819a83f66"
_TROPHY   = "hssd/80bfb59e9d68cc3b03a1b04e626640e5d4e4396d"

# ============================ BILLIARDS (centre hero) ============================
# Pool table on a bordered rug with a single billiards pendant directly overhead.
pool_table = scene.AddAsset("an 8-foot billiards pool table with green felt and wooden frame", asset_id=_POOL)
with scene.RelativeGroup() as billiards:
    billiards.set_anchor(pool_table)
    billiards.place_rug("a large charcoal wool area rug with a dark green border", size=3.0)
    billiards.add_lighting("a billiards table hanging light fixture with three shades over a pool table", density=0)

# ============================ BAR (back wall, social hub) ============================
# Proven bar pattern (from the cocktail lounge): a compact STRAIGHT stool row on the counter's
# customer side via place_rectilinear (spreading stools with per-side placements balloons the
# lighting footprint, scattering the pendants), the back-bar behind the whole line as one rigid
# station (RelativeGroup.place_on_back bakes a guaranteed service aisle), a tight pendant cluster.
bar_counter = scene.AddAsset("a home bar counter with a wood front and storage", asset_id=_BARCOUNTER, width=2.8)
with scene.AroundGroup(sparsity=0.15, jitter=0.2) as bar_line:
    bar_line.set_anchor(bar_counter)
    bar_stools = 3 * scene.AddAsset("a wooden bar stool with a backrest", asset_id=_BARSTOOL)
    bar_line.place_rectilinear(longer_side1=bar_stools)              # one straight row of stools
    bar_line.add_lighting("a warm brass globe pendant light", density=0.18)   # tight cluster over the counter
with scene.RelativeGroup() as bar:
    bar.set_anchor(bar_line)
    bar.place_on_back(scene.AddAsset("a wooden back-bar cabinet with glass doors and liquor bottles",
                                     asset_id=_BACKBAR, width=2.4))   # cellar behind -> service aisle

# ============================ ARCADE (back-right corner) ============================
arcades = 2 * scene.AddAsset("a classic upright retro arcade video game cabinet", asset_id=_ARCADE)
with scene.GridGroup(sparsity=0.4, randomness=0.05) as arcade_row:
    arcade_row.place_row(arcades)

# ============================ LOUNGE (left wall, faces the TV) ============================
sofa = scene.AddAsset("a vintage brown leather three-seat sofa", asset_id=_SOFA)
armchairs = 2 * scene.AddAsset("a green velvet accent armchair", asset_id=_ARMCHAIR)
with scene.RelativeGroup() as lounge:
    lounge.set_anchor(sofa)
    coffee = scene.AddAsset("a low walnut coffee table")
    lounge.place_on_front(coffee)   # between sofa and TV
    lounge.place_on_left(armchairs[0])
    lounge.place_on_right(armchairs[1])
    lounge.face(armchairs[0], toward=coffee)   # angle the flanking chairs into the conversation cluster
    lounge.face(armchairs[1], toward=coffee)

# ============================ POKER (front-left) ============================
poker_table = scene.AddAsset("a walnut poker card table with a padded rail", asset_id=_POKER)
poker_chairs = 4 * scene.AddAsset("a brown leather dining chair")
with scene.RelativeGroup() as poker:
    poker.set_anchor(poker_table)
    poker.place_on_front(poker_chairs[0])
    poker.place_on_back(poker_chairs[1])
    poker.place_on_left(poker_chairs[2])
    poker.place_on_right(poker_chairs[3])
    for _ch in poker_chairs:                 # seat the players facing the table
        poker.face(_ch, toward=poker_table)

# ============================ ROOM ============================
with scene.RoomGroup(modulate_scale=0.9, randomness=0.08) as room:
    room.place_walls(floor_texture="dark grey stone tile flooring",
                     ceiling_texture="matte charcoal ceiling",
                     wall_texture="deep hunter green wall")

    # CENTRE: the billiards hero
    room.place_on_center(billiards)

    # BACK wall: bar social hub, facing into the room; gallery + painting above
    room.place_on_back(bar, facing="front")
    room.place_on_wall_back_center(scene.AddAsset("a grid of framed black and white photographs"))
    room.place_on_wall_back_right(scene.AddAsset("a large colourful abstract painting"))

    # BACK-RIGHT corner: arcade cabinets against the back wall, facing into the room
    room.place_on_back_right_corner(arcade_row, facing="front")

    # LEFT wall: media + lounge. TV wall-mounted over a low console; sofa faces the wall.
    room.place_on_left_wall_center(scene.AddAsset("a low dark wood media console cabinet", asset_id=_MEDIA))
    room.place_on_wall_left_center(scene.AddAsset("a large slim black flat-screen television", asset_id=_TV))
    room.place_on_left(lounge, facing="left")

    # RIGHT wall: window with foosball in front of it (players face the view)
    room.place_window_floor_to_ceiling("right_wall")
    foosball = scene.AddAsset("a classic wooden foosball table", asset_id=_FOOSBALL)
    room.place_on_right(foosball, facing="left")

    # FRONT-LEFT: poker zone
    room.place_on_front_left(poker, facing="back")

    # FRONT wall: entry door (centre), trophy cabinet (left), dartboard (right)
    room.place_door("front_wall", position="center")
    room.place_on_front_wall_left(scene.AddAsset("a dark wood display cabinet with glass doors and trophies", asset_id=_TROPHY), facing="back")
    room.place_on_wall_front_right(scene.AddAsset("a wall-mounted dartboard cabinet with open doors", asset_id=_DARTBOARD))

    # ---- clearances ----
    # Billiards: room to draw a cue on every side -> this is what sizes the room.
    room.add_clearance(pool_table, distance=1.3, dir="all")
    # Foosball: standing room for players around the table.
    room.add_clearance(foosball, distance=0.5, dir="all")
    # Poker: a clear approach around the table (chairs pull out).
    room.add_clearance(poker_table, distance=0.5, dir="all")

    # ---- lighting: moody, layered ----
    room.add_lighting("warm recessed ambient ceiling downlights", density=0.02)

scene.export("game_room.blend")
