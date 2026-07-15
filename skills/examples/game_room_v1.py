"""Game room / recreation lounge — "Central Play Nexus" (planner-driven).

Planner target: a moody home rec lounge in walnut / charcoal / brass with a green feature wall —
billiards as the social hero, a bar, an arcade corner, a media lounge, foosball at the window and a
poker corner. Every game piece comes off the shelf: no ingestion, no new DSL, pure composition.

LESSON this scene encodes: a rec room is a set of PLAY ZONES ringed around ONE hero. The billiards
table is the social anchor at the CENTRE; its cue-stroke clearance (space to draw a cue on every
side) is what actually sizes the room, so put it down first with an all-round clearance and let the
other zones settle around it. Cardio-faces-the-view logic from the gym applies here too: the lounge
sofa faces its TV, the foosball players face the window.

Layout — HERO IN THE MIDDLE, ZONES RINGED AROUND IT (window = RIGHT wall, media = LEFT wall):
- CENTRE            : BILLIARDS. The 8-ft pool table cannot live against a wall — it is played from
                      all four sides, so it takes the middle and its 1.3 m cue clearance sizes the
                      floor. A bordered rug grounds it; one pendant (density=0) hangs directly over.
- BACK wall         : the BAR social hub — counter + back-bar bottle cabinet + a straight 3-stool
                      row. It is the room's second gathering point, so it faces INTO the room; the
                      gallery photos + a colourful painting hang above it.
- BACK-RIGHT corner : ARCADE. A pair of upright cabinets, backs to the wall, screens to the room —
                      a corner is exactly what a two-cabinet row wants (no circulation cost).
- LEFT wall         : MEDIA / LOUNGE. The TV is wall-hung over a low console, so the sofa must face
                      the WALL (gym's cardio-faces-the-view rule); two armchairs flank it and are
                      angled into a coffee-table cluster with face().
- RIGHT wall        : the WINDOW, and FOOSBALL in front of it — the players get the view. The only
                      wall with no storage or seating on it, so it stays the daylight source.
- FRONT-LEFT        : POKER — walnut card table, four chairs faced at it.
- FRONT wall        : the entry door (CENTRE, so you walk in at the hero), the trophy cabinet (left)
                      and the wall dartboard (right), whose throwing lane runs into the open
                      front-right quadrant — the one piece of floor left deliberately empty.

Identity comes from the GAME PIECES themselves — pool table, arcade cabinets, foosball, dartboard,
poker table — massed as five legible zones. Strip them out and this is a lounge; they are what names
the room. The palette (hunter-green feature wall, dark stone tile, walnut/charcoal/brass) carries
the mood, not the identity.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/game_room_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 lays the billiards rug; phase 3 adds the wall decor, the window
and the whole lighting layer. NOTE: this room's identity is almost entirely PHASE 1 — the game
pieces are floor anchors — so phase 2 is deliberately near-empty (see game_room.md).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("GameRoom", seed=17)

# ---- pinned assets --------------------------------------------------------------------------
# Ids preserved verbatim from the original build (scenes/work/game_room.py). Only the pool table
# recorded a per-pin rationale; the rest are pinned because these are the meshes the shipped scene
# was validated on, and an unpinned pick is NOT stable across runs even at a fixed seed
# (jewelry_shop's rule). What each one is, is what the query says it is:
POOL      = "hssd/988e19a926492231c05b5d9b542f6d6cc0c1d3ca"  # 8-ft espresso frame, GREEN FELT — the
                                                             # hero; the felt is what makes it read
                                                             # as billiards and not as a table
FOOSBALL  = "hssd/99c1832511c8703634b467fa82a70442eb3040c0"  # classic wooden foosball table
ARCADE    = "hssd/3873f4b8fbf7b568ed6dca1b5d8878edb57e8e3d"  # upright retro cabinet; duplicated 2x
DARTBOARD = "hssd/8b1f720d6bab266f0442535240773c3520eaba0b"  # wall dartboard cabinet, doors open
POKER     = "hssd/81f092c5722ae67b49104b660bcf3f0fec3c69f0"  # walnut card table w/ padded rail
                                                             # (the same flat-top table casino_v1
                                                             # pins as its blackjack substitute)
# ---- bar ----
BARCOUNTER = "hssd/96aa481c97443d17b9946bc68e188bfd877c2ebf"  # home bar counter, wood front
BACKBAR    = "future/f92b65d2-a2d3-4430-a5cb-34a7b5bce7f3"    # glass-door bottle cabinet
BARSTOOL   = "hssd/d10ff3f71a5e1a0534fc43132d54b5a083b8d17f"  # wooden stool w/ backrest; 3x
# ---- lounge ----
SOFA     = "future/c9856517-b011-42f7-9a40-5da16d0b6f43"     # vintage brown leather 3-seat
ARMCHAIR = "hssd/bf96d2cce0097d4eeb20de5e736103b626baf0ac"   # green velvet accent chair; 2x
TV       = "hssd/52676f400fb7e2b9181f70a0fa1f53eb686a05b4"   # slim black flat-screen (wall-hung)
MEDIA    = "future/12b76671-ce59-4685-a05c-1e7819a83f66"     # low dark wood media console
TROPHY   = "hssd/80bfb59e9d68cc3b03a1b04e626640e5d4e4396d"   # glass-door display cabinet

scene.prefetch_assets([
    "an 8-foot billiards pool table with green felt and wooden frame",
    "a classic wooden foosball table",
    "a classic upright retro arcade video game cabinet",
    "a walnut poker card table with a padded rail",
    "a brown leather dining chair",
    "a home bar counter with a wood front and storage",
    "a wooden bar stool with a backrest",
    "a vintage brown leather three-seat sofa",
    "a green velvet accent armchair",
    "a low walnut coffee table",
])

# ============================ BILLIARDS (centre hero) ============================
# Pool table on a bordered rug with a single billiards pendant directly overhead.
pool_table = scene.AddAsset("an 8-foot billiards pool table with green felt and wooden frame", asset_id=POOL)
with scene.RelativeGroup() as billiards:
    billiards.set_anchor(pool_table)
    if PHASE >= 2:
        # The rug is FLOOR DRESSING (phase 2), and the gate must sit INSIDE this with-block: a group
        # compiles on __exit__, so an op gated outside it registers too late and simply never runs —
        # silently, with a clean lint and a clean VLM loop (prison_cell's bug).
        billiards.place_rug("a large charcoal wool area rug with a dark green border", size=3.0)
    if PHASE >= 3:
        # density=0 => exactly ONE fixture, hung on the group's (tight) footprint: the pool table.
        billiards.add_lighting("a billiards table hanging light fixture with three shades over a pool table", density=0)

# ============================ BAR (back wall, social hub) ============================
# Proven bar pattern (from the cocktail lounge): a compact STRAIGHT stool row on the counter's
# customer side via place_rectilinear (spreading stools with per-side placements balloons the
# lighting footprint, scattering the pendants), the back-bar behind the whole line as one rigid
# station (RelativeGroup.place_on_back bakes a guaranteed service aisle), a tight pendant cluster.
bar_counter = scene.AddAsset("a home bar counter with a wood front and storage", asset_id=BARCOUNTER, width=2.8)
with scene.AroundGroup(sparsity=0.15, jitter=0.2) as bar_line:
    bar_line.set_anchor(bar_counter)
    # The stools are FLOOR geometry: they stay in PHASE 1 with the counter, because deferring them
    # would change the bar station's depth and therefore the shell phase 1 validated.
    bar_stools = 3 * scene.AddAsset("a wooden bar stool with a backrest", asset_id=BARSTOOL)
    bar_line.place_rectilinear(longer_side1=bar_stools)              # one straight row of stools
    if PHASE >= 3:
        bar_line.add_lighting("a warm brass globe pendant light", density=0.18)   # tight cluster over the counter
with scene.RelativeGroup() as bar:
    bar.set_anchor(bar_line)
    bar.place_on_back(scene.AddAsset("a wooden back-bar cabinet with glass doors and liquor bottles",
                                     asset_id=BACKBAR, width=2.4))   # cellar behind -> service aisle

# ============================ ARCADE (back-right corner) ============================
arcades = 2 * scene.AddAsset("a classic upright retro arcade video game cabinet", asset_id=ARCADE)
with scene.GridGroup(sparsity=0.4, randomness=0.05) as arcade_row:
    arcade_row.place_row(arcades)

# ============================ LOUNGE (left wall, faces the TV) ============================
sofa = scene.AddAsset("a vintage brown leather three-seat sofa", asset_id=SOFA)
armchairs = 2 * scene.AddAsset("a green velvet accent armchair", asset_id=ARMCHAIR)
with scene.RelativeGroup() as lounge:
    lounge.set_anchor(sofa)
    coffee = scene.AddAsset("a low walnut coffee table")
    lounge.place_on_front(coffee)   # between sofa and TV
    lounge.place_on_left(armchairs[0])
    lounge.place_on_right(armchairs[1])
    lounge.face(armchairs[0], toward=coffee)   # angle the flanking chairs into the conversation cluster
    lounge.face(armchairs[1], toward=coffee)

# ============================ POKER (front-left) ============================
poker_table = scene.AddAsset("a walnut poker card table with a padded rail", asset_id=POKER)
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
    # UNGATED: the shell is what every phase is placed into.
    room.place_walls(floor_texture="dark grey stone tile flooring",
                     ceiling_texture="matte charcoal ceiling",
                     wall_texture="deep hunter green wall")

    # CENTRE: the billiards hero
    room.place_on_center(billiards)

    # BACK wall: bar social hub, facing into the room
    room.place_on_back(bar, facing="front")

    # BACK-RIGHT corner: arcade cabinets against the back wall, facing into the room
    room.place_on_back_right_corner(arcade_row, facing="front")

    # LEFT wall: the media console is FLOOR furniture (phase 1); its TV is wall-hung (phase 3).
    room.place_on_left_wall_center(scene.AddAsset("a low dark wood media console cabinet", asset_id=MEDIA))
    room.place_on_left(lounge, facing="left")   # sofa faces the TV wall

    # RIGHT wall: foosball in front of the window (players face the view). The glazing is phase 3,
    # but the foosball table is a floor anchor and stays here.
    foosball = scene.AddAsset("a classic wooden foosball table", asset_id=FOOSBALL)
    room.place_on_right(foosball, facing="left")

    # FRONT-LEFT: poker zone
    room.place_on_front_left(poker, facing="back")

    # FRONT wall: entry door (centre) + the trophy cabinet (floor furniture, left).
    # The door is UNGATED: its automatic clearance shapes the floor solve, so deferring it to a
    # later phase would change the layout that phase 1 validated.
    room.place_door("front_wall", position="center")
    room.place_on_front_wall_left(scene.AddAsset("a dark wood display cabinet with glass doors and trophies", asset_id=TROPHY), facing="back")

    # ---- clearances (PHASE 1: they are what shape the floor solve) ----
    # Pool (1.3 all — this is what SIZES the room), foosball and poker (0.5 all) all get their
    # surround clearance AUTOMATICALLY now: those descriptions keyword-match the auto layer
    # (default_constraints.py, frozen 2026-07-14). No manual add_clearance needed.

    if PHASE >= 3:
        # ---- wall layer. Every asset below is CREATED INSIDE this block, so nothing is orphaned
        # into a phase-1 or phase-2 build. Four distinct wall slots, no overlap with the door.
        room.place_on_wall_back_center(scene.AddAsset("a grid of framed black and white photographs"))
        room.place_on_wall_back_right(scene.AddAsset("a large colourful abstract painting"))
        room.place_on_wall_left_center(scene.AddAsset("a large slim black flat-screen television",
                                                      asset_id=TV))        # over the media console
        room.place_on_wall_front_right(scene.AddAsset("a wall-mounted dartboard cabinet with open doors",
                                                      asset_id=DARTBOARD))  # throwing lane -> front-right
        # RIGHT wall glazing: the foosball players' view.
        room.place_window_floor_to_ceiling("right_wall")

        # ---- lighting: moody, layered (the billiards pendant + the bar cluster are gated in their
        # own groups above; this is the ambient fill).
        room.add_lighting("warm recessed ambient ceiling downlights", density=0.02)

scene.export("game_room_v1.blend")
