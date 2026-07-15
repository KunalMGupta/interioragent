"""Home office / study — "Warm-Wood Power Study" (executive_office's bones at domestic scale).

A single-room home office: a warm-wood desk WorkstationGroup in the middle of the floor with
the desk facing INTO the room (executive_office's power layout — the operator sits with their
back to the depth of the room and looks out at the door/window), a TALL stocked bookcase on
the left wall's LEFT slot (off the wall centre — the interior cameras stand at each wall's
centre at ~1.4 m, and a 2 m bookcase parked there blinds a view; closet/bakery rule applied
at design time), and a reading corner (leather armchair + brass floor lamp + side table) in
the back-right corner so the room reads study, not cubicle.

Layout:
- CENTRE     : the desk WorkstationGroup, `facing="back"` — WorkstationGroup's operator side
               is local +Z, so facing="back" seats the worker on the back side of the desk
               looking out at the room and the front window (the classic power layout;
               executive_office verified this reads right by eye — RotationConstraint can't).
- LEFT wall  : the tall walnut bookcase in the LEFT slot (off-centre for the camera rule).
- BACK-RIGHT : the reading nook — armchair + floor lamp + side table composed as ONE
               RelativeGroup, faced "front" into the room (the armchair faces the ROOM, never
               its own side table — the recurring VLM rotate-vote is noise, per library.md).
- FRONT wall : the daylight window (phase 3) — the wall the worker faces.
- RIGHT wall : the door (right slot) + framed print (phase 3) — the light wall.

Phase-gated (IDSDL/phases.py): phase 1 = ALL floor mass + door; phase 2 = desktop items, rug,
corner plant; phase 3 = wall art, window + curtain, ceiling lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("StHomeOffice", seed=41)

# --- pinned heroes (reused documented pins from executive_office.md / library.md — all audited) ---
DESK = "hssd/6804953904df94d4abdb0776ad6d55c2a5b8aeaa"       # warm-wood top, slim metal legs, FLAT —
                                                             # a WorkstationGroup needs a plain
                                                             # writing surface for place_on_top
BOOKCASE = "hssd/b356640d3d9d976c8ea2a29ae5ff48467e32262b"   # TALL dark-walnut bookcase, stocked with
                                                             # leather-bound books (library.md hero) —
                                                             # an empty shelf names the fixture, not
                                                             # the study
ARMCHAIR = "hssd/613ba909e59984d3a908ec4b52344bcd689fa79b"   # brown tufted leather reading armchair
FLOORLAMP = "hssd/69fa8415108e7438a412ec0a52a55983f39119df"  # slender brass floor reading lamp
SIDE_TABLE = "hssd/d4bff7307857a9634e9785ce7febc342217cce7c" # round mid-century wood side table

scene.prefetch_assets([
    "a modern warm wood writing desk with slim metal legs",
    "a black ergonomic office task chair on casters",
    "a tall wooden bookshelf full of books",
    "a cozy brown leather reading armchair",
    "a slender brass floor reading lamp",
    "a small round wooden side table",
])

# --- the desk workstation: desk anchor + task chair + computer + accessories --------------------
# Desktop items are the PHASE-2 layer, and the gate sits INSIDE the `with` block: gated outside
# it the ops are never recorded and the laptop/lamp simply vanish (prison_cell's silent trap).
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a modern warm wood writing desk with slim metal legs",
                                      asset_id=DESK))
    station.place_chair(scene.AddAsset("a black ergonomic office task chair on casters"))
    if PHASE >= 2:
        station.place_computer(scene.AddAsset("an open laptop computer"))
        station.place_accessories([   # <= 3 on-top items total (laptop + these two)
            scene.AddAsset("an articulated black desk task lamp"),
            scene.AddAsset("a small potted succulent for a desk"),
        ])
        # the rug grounds the desk zone; a group rug rides with the station wherever it lands
        station.place_rug("a flat woven wool rug in warm neutral tones", size=0.8)

# --- the reading corner: armchair + its task light + a table within reach, ONE nook -------------
# Design principle: a seat never travels without a table + its own light (library.md nook).
with scene.RelativeGroup() as nook:
    nook.set_anchor(scene.AddAsset("a cozy brown leather reading armchair", asset_id=ARMCHAIR))
    nook.place_on_right(scene.AddAsset("a small round wooden side table", asset_id=SIDE_TABLE))
    nook.place_on_back_left(scene.AddAsset("a slender brass floor reading lamp", asset_id=FLOORLAMP))
    if PHASE >= 2:
        nook.place_on_top(scene.AddAsset("a stack of hardcover books", modulate_scale=0.5))

with scene.RoomGroup(modulate_scale=0.9, randomness=0.1) as room:
    room.place_walls(floor_texture="warm herringbone parquet oak wood flooring",
                     ceiling_texture="soft cream plaster ceiling",
                     wall_texture="soft warm white painted wall")

    # Phase 1 — ALL floor mass (never gate floor-standing objects to phase >= 2: the phase-1
    # shell auto-size would never see their footprint and the layout solve breaks).
    room.place_on_center(station, facing="back")          # power layout: worker faces the room/window
    # TALL bookcase OFF the wall centre — left wall, LEFT slot (the camera at that wall's centre
    # keeps its view; a 2 m case at the centre would blind it).
    room.place_on_left_wall_left(scene.AddAsset("a tall wooden bookshelf full of books",
                                                asset_id=BOOKCASE))
    room.place_on_back_right_corner(nook, facing="front") # reading corner faces the room
    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        # greenery in the back-left corner — corner slots are exempt from the floor-mass rule
        # (the shell already reserves its corners; coarse_to_fine.md).
        room.place_on_back_left_corner(scene.AddAsset("a tall leafy potted plant in a woven basket"))

    if PHASE >= 3:
        # daylight on the wall the worker faces; a STANDARD pane keeps the void modest, and a
        # light sheer frames it (the brief's "window with light curtain").
        room.place_window_standard("front_wall", position="center",
                                   curtain="sheer white linen curtains")
        # framed prints on the two light walls (never on the bookcase wall's used slot)
        room.place_on_wall_right_center(
            scene.AddAsset("a framed abstract wall art print in warm earth tones", width=1.0))
        room.place_on_wall_left_right(
            scene.AddAsset("a framed vintage botanical illustration print", width=0.7))
        # compact FLUSH fixture, never a chandelier (add_lighting drops tall fixtures to head
        # height); fixture enlarged + density low so the count stays sane (starfield lint).
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.02,
                          modulate_scale=1.5)

scene.export("st_home_office.blend")
