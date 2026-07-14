"""
Corridor — "Long Gallery Corridor with Reflective Floor" (planner target:
tmp/plan_a_corridor/plan.png).

Look (from the plan): a luminous gallery-like hallway. A glossy black-and-white
checkerboard tile floor forms the visual spine; one long wall carries a gallery
of thin monochrome prints + a round gold mirror over a slim console with vases;
the opposite long wall carries the deep-green storage cue (green cabinets) —
the plan's green accent side. Linear black ceiling light bars run the axis;
a window caps the far sightline; doors connect to adjoining rooms. Palette:
pale ivory walls, deep green, black/white floor, warm wood + brass.

Zone map (corridor runs front<->back; LONG walls = LEFT + RIGHT — loading them
is what elongates the auto-sized shell; the short end walls stay light):
  - RIGHT (long) = the GALLERY side: console + vases + round mirror + framed prints.
  - LEFT  (long) = the GREEN side: a run of green cabinets + a side door + a print.
  - BACK  (short) = the sightline cap: standard window + sheer curtain + tall plant.
  - FRONT (short) = the entry door.
  - CENTER        = kept EMPTY: the clear travel lane (corridor circulation rule).

Phase 1: console + green cabinet run + doors + shell (floor layout, room shape).
Phase 2: vases on the console, the tall plant (surface/floor details).
Phase 3: mirror + gallery prints, window + curtain, linear ceiling lights (mood).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Corridor", seed=21)

# --- pinned assets (audited previews, gate 3) ---
_CONSOLE = "hssd/c33165b9d06aab9e2e162cd54b047883a80d5f00"   # slim wood-top console, black metal legs
_MIRROR  = "hssd/f303d22d219dfb8878d74923c6d147fa02d0f64d"   # round mirror, champagne/gold frame (thin)
_FRAME_A = "hssd/xxxxd8a7930dx2e42x4a8bxbff9x5d6f100cd1fc"   # abstract line art, black frame (flat)
_FRAME_B = "hssd/32a0a1818c04208ac457579c89c2276f2f7f85a4"   # b/w abstract graphic, black frame (flat)
_FRAME_C = "hssd/b42c22f3523f5f99a962e313aa2290dd6d5f9053"   # b/w abstract graphic, black frame (flat)
_LIGHT   = "hssd/fb227c11d11cce96646739bba47c9997510d9e35"   # black linear spotlight bar (flush, small emissive)
_CABINET = "future/024ee5bd-f5b5-4c2c-8c6e-ab6673c28faa"     # green 2-door cabinet (the green storage cue)
_VASES   = "future/5a70fef8-a568-4138-b98f-6eba2af38d97"     # ceramic vase trio with greenery

scene.prefetch_assets([
    "a slim dark wood console table with black metal legs",
    "a round wall mirror with a thin gold frame",
    "an abstract line art print in a thin black frame",
    "a black and white abstract graphic art print in a black frame",
    "a modern green storage cabinet with a wooden texture",
    "a ceramic vase trio with green stems",
    "a tall potted plant with lush green leaves",
    "a slim linear black LED flush mount ceiling light bar",
    "a stack of hardcover books",
    "a small potted green plant in a white pot",
])

# --- RIGHT long wall: the gallery-side console (one rigid unit, one wall slot) ---
console = scene.AddAsset("a slim dark wood console table with black metal legs",
                         asset_id=_CONSOLE, width=1.4)
with scene.RelativeGroup() as console_group:
    console_group.set_anchor(console)
    if PHASE >= 2:
        # the vase trio reads small — place_on_top oversizes small props (library lamp lesson)
        console_group.place_on_top(
            scene.AddAsset("a ceramic vase trio with green stems",
                           asset_id=_VASES, modulate_scale=0.5))

# --- LEFT long wall: the green storage run (a row of 3 identical cabinets) ---
_cab = scene.AddAsset("a modern green storage cabinet with a wooden texture",
                      asset_id=_CABINET)
# future/ scale metadata is unreliable (loaded ~2x) AND the mesh is wardrobe-tall;
# the plan wants LOW perimeter storage — uniform-scale to ~0.9 m tall (sideboard height)
_cab.scale(_cab.get_width() * 0.9 / _cab.get_height())
# dress the cabinet tops (vibe layer): compose ONE unit, duplicate — the on-top
# tournament runs once and all three read identical (locker_room cubby pattern)
with scene.RelativeGroup() as cab_unit:
    cab_unit.set_anchor(_cab)
    if PHASE >= 2:
        cab_unit.place_on_top([
            scene.AddAsset("a stack of hardcover books", modulate_scale=0.45),
            scene.AddAsset("a small potted green plant in a white pot", modulate_scale=0.4),
        ])
cabinets = 3 * cab_unit
with scene.GridGroup(sparsity=0.12) as green_run:
    green_run.place_row(cabinets)

# --- the room: long walls loaded, short walls light, center = clear travel lane ---
# RoomProportions voted 0.69-0.76 every phase; held per render-wins-early. Applied
# 0.75 in the final phase -> cramped (cameras jammed on the cabinets, vote flipped
# to 0.95). 0.85 is the converged middle: corridor-tight but with a clear lane.
with scene.RoomGroup(modulate_scale=0.85, randomness=0.05) as room:
    # texture library has no b/w checkerboard (4 wordings: pale planks / dark grey /
    # multicolor checker x2). The dark reflective tile reads closest to the plan's
    # "glossy reflective spine" — this wording is the one that produced it:
    room.place_walls(floor_texture="black and white checkered tile floor",
                     ceiling_texture="soft white plaster ceiling",
                     wall_texture="pale ivory plaster wall")
    # long walls carry the runs (omit facing -> heuristic faces them into the room)
    room.place_on_right_wall_center(console_group)
    room.place_on_left_wall_center(green_run)
    # doors in PHASE 1: their auto clearance shapes the floor solve
    room.place_door("front_wall", position="center")   # the entry
    room.place_door("left_wall", position="right")     # a side room off the corridor
    if PHASE >= 2:
        room.place_on_back_right_corner(
            scene.AddAsset("a tall potted plant with lush green leaves"))
    if PHASE >= 3:
        # gallery side: mirror over the console (center), prints flanking it
        room.place_on_wall_right_center(
            scene.AddAsset("a round wall mirror with a thin gold frame",
                           asset_id=_MIRROR, width=0.7))   # statement size over the console
        room.place_on_wall_right_left(
            scene.AddAsset("an abstract line art print in a thin black frame", asset_id=_FRAME_A))
        room.place_on_wall_right_right(
            scene.AddAsset("a black and white abstract graphic art print in a black frame",
                           asset_id=_FRAME_B))
        # green side: one print over the low cabinet run (left slot; the door claims right)
        room.place_on_wall_left_left(
            scene.AddAsset("a black and white abstract graphic art print in a black frame",
                           asset_id=_FRAME_C))
        # the sightline cap: a modest window (standard, not picture — black-void lesson)
        room.place_window_standard("back_wall", position="center",
                                   curtain="light ivory sheer curtains")
        # linear black light bars down the axis: flush fixture, small-room density
        # (add_lighting takes no asset_id; the audited bar hssd/fb227c11 is this
        #  query's top retrieval pick)
        room.add_lighting("a slim linear black LED flush mount ceiling light bar",
                          density=0.015)

scene.export("corridor.blend")
