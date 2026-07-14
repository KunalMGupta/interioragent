"""Writer's studio — "Morning-Light Writing Room" (calm warm palette, desk by the window).

A small studio for one writer: a flat wooden desk WorkstationGroup pulled to the back of the
room under the window (daylight over the shoulder, writer facing the room — the lobby/
executive power seating, which also keeps the render from staring at a chair back), a
cushioned daybed against the left wall for reading drafts, a low stocked bookshelf, plants,
and framed prints. NO typewriter exists in the dataset (retrieval stress-tested: 0.52 best,
all rotary phones/desk clocks) — the desk carries an open laptop plus the CLASSIC BLACK
ROTARY PHONE as the vintage cue instead. A cork pinboard also does not exist (0.47, all
classroom chalk/whiteboards) — dropped rather than forced; framed prints carry the walls.

Layout:
- BACK third : the desk WorkstationGroup at `place_on_back(..., facing="back")` — NOT a
               wall-flush placement, so there is real floor behind the desk for the chair
               (lobby.md's reception rule), with the window centred above/behind it (phase 3).
- LEFT wall  : the daybed/chaise, centre slot (it is LOW, so the wall-centre camera sees
               over it — the tall-at-centre rule only bites above ~1.4 m).
- RIGHT wall : the low bookshelf in the LEFT slot (off-centre out of habit; camera-safe).
- FRONT      : door right; tall plant in the front-left corner.

Phase-gated: phase 1 = all floor mass + door; phase 2 = desktop items, rug, plants, shelf-top
props; phase 3 = window + light curtain, framed prints, ceiling lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("StWriterStudio", seed=43)

# --- pinned assets (fresh retrievals for the studio pieces; desk reused from executive_office) --
DESK = "hssd/6804953904df94d4abdb0776ad6d55c2a5b8aeaa"      # warm-wood FLAT desk (WorkstationGroup-
                                                            # safe writing surface)
DAYBED = "hssd/2c130c69724b4ddcfae07653a045c830e27aeb02"    # beige chaise lounge with cushions
                                                            # (retrieved 0.68, the one clearly
                                                            # INDOOR daybed — most hits are patio)
LOWSHELF = "hssd/2db50fb1f8120974d6157ae9aff704a4fc9d181f"  # classic wooden bookshelf, three
                                                            # shelves FILLED with books (0.66)
PHONE = "hssd/898f2c044e0db9027b73df25702b624881b0b330"     # classic black rotary telephone — the
                                                            # honest vintage substitute for the
                                                            # nonexistent typewriter

scene.prefetch_assets([
    "a modern warm wood writing desk with slim metal legs",
    "a simple wooden chair with a woven seat",
    "a modern beige chaise lounge daybed with cushions",
    "a small low wooden bookshelf filled with books",
    "a classic black rotary dial telephone",
    "a tall leafy potted plant in a woven basket",
])

# --- the writing desk: anchor + chair + the writer's tools (phase 2, gated INSIDE the block) ----
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a modern warm wood writing desk with slim metal legs",
                                      asset_id=DESK))
    station.place_chair(scene.AddAsset("a simple wooden chair with a woven seat"))
    if PHASE >= 2:
        station.place_computer(scene.AddAsset("an open laptop computer"))
        station.place_accessories([   # <= 3 on-top items total
            scene.AddAsset("a classic black rotary dial telephone", asset_id=PHONE),
            scene.AddAsset("a stack of paper notebooks", modulate_scale=0.5),
        ])
        station.place_rug("a flat woven jute rug in warm cream tones", size=0.75)

# --- the low bookshelf, wrapped so phase 2 can dress its top ------------------------------------
with scene.RelativeGroup() as shelf:
    shelf.set_anchor(scene.AddAsset("a small low wooden bookshelf filled with books",
                                    asset_id=LOWSHELF))
    if PHASE >= 2:
        shelf.place_on_top(scene.AddAsset("a small potted plant in a terracotta pot",
                                          modulate_scale=0.6))

with scene.RoomGroup(modulate_scale=0.9, randomness=0.1) as room:
    room.place_walls(floor_texture="warm herringbone parquet oak wood flooring",
                     ceiling_texture="soft cream plaster ceiling",
                     wall_texture="warm cream painted plaster wall")

    # Phase 1 — all floor mass + door.
    # Desk NEAR the window wall but on a floor third (not wall-flush): the chair needs floor
    # behind the desk. facing="back" puts the operator (+Z) side to the back wall -> the writer
    # sits under the window facing the room.
    room.place_on_back(station, facing="back")
    room.place_on_left_wall_center(scene.AddAsset("a modern beige chaise lounge daybed with cushions",
                                                  asset_id=DAYBED), facing="right")
    room.place_on_right_wall_left(shelf)
    room.place_door("front_wall", position="right")

    if PHASE >= 2:
        # corner greenery (corner slots exempt from the floor-mass gating rule)
        room.place_on_front_left_corner(scene.AddAsset("a tall leafy potted plant in a woven basket"))

    if PHASE >= 3:
        # the window the desk sits under — light curtain, standard pane (modest void)
        room.place_window_standard("back_wall", position="center",
                                   curtain="sheer white linen curtains")
        # framed prints instead of the nonexistent pinboard; one over the daybed (low run ->
        # headroom is free, laundromat's art-over-a-low-run), one on the right wall
        room.place_on_wall_left_center(
            scene.AddAsset("a framed watercolor landscape print in a light wood frame", width=0.9))
        room.place_on_wall_right_center(
            scene.AddAsset("a framed vintage botanical illustration print", width=0.7))
        # calm warm ceiling light: compact flush fixture, enlarged + low density (starfield lint)
        # Build 1: the picked flush mount rendered as a giant ceiling DISC spanning half the
        # room (kitchen v2's drum class) — shrink the fixture, don't touch density.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.02,
                          modulate_scale=0.4)

scene.export("st_writer_studio.blend")
