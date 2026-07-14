"""Hair salon — "Luxe Row-Station Salon Spine" (asset-first kickoff + a custom placement group).

Planner target: blush + brass + concrete. The hero is a STYLING ROW — a line of identical stations
(chair facing a wall mirror, console under it, trolley beside it) along one long wall; a prominent
reception and a blush-velvet waiting nook face it from the opposing long wall. Luxe but working:
polished concrete underfoot, soft blush walls, brass pendants.

Layout — MOTIF-GROUP SPINE (a repeated custom station, rowed and seated FLUSH on the long wall).
The room shape is a CONSEQUENCE of this distribution: the RoomGroup sizes each wall from what sits
on it, so loading the two LONG walls and keeping the two SHORT walls light is what makes the room
come out WIDE and shallow — which is what a real salon is.
- BACK wall  (long) : the styling row — 5 MirrorStationGroup units in a GridGroup, placed with
                      place_on_back_wall_center(..., facing="back") so the row sits ON the wall.
                      place_on_back would leave a wall-row-deep gap and the mirrors would float.
- FRONT wall (long) : the opposing long load — reception (left) + waiting nook, both facing in.
                      Two clusters here, not one, because the front wall has to be as long as the
                      styling row for the room to stay wide.
- LEFT wall  (short): light. The retail shelf, at the front (reception) end. The door.
- RIGHT wall (short): light. The backwash pair, center/front — deliberately AWAY from the styling
                      row, since a client lying back into a shampoo bowl is a separate zone.
- CENTRE            : deliberately OPEN — the working floor between the row and the reception.

Identity comes from the styling row: five mirrors at head height, all in a line, is the one image
that says "salon" and nothing else. The blush wall + brass + the velvet pair carry the "pretty".

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/hair_salon_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the surfaces (trolleys, plant, vase, rack, rug);
phase 3 adds the wall decor, the window and the pendants.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("HairSalon", seed=77)

# ---- pinned assets ---------------------------------------------------------------------------
# The salon's iconic fixtures do not exist in the home-furniture-biased pool; five were sourced as
# free glbs and INGESTED (styling chair, backwash unit, arched mirror, neon sign, retail shelf).
# Only the chair needs an id here — the other four are reachable by query through the curated
# HairSalonRetriever pool (assets/hair_salon.json).
STYLING_CHAIR = "custom/59a3f803acb6e00ec8e3637e862c879cf03c06be"  # the ingested barber chair. The
                                                                   # visual picker kept drifting to a
                                                                   # low tub chair for "a salon styling
                                                                   # chair"; pinning fixed it durably.
TUB_CHAIR     = "hssd/3b522b2a379a3a5248dbaa0159cc5ddfbf43a2e0"    # pinned in the source build (the
                                                                   # reason was not recorded). It is
                                                                   # the only seat carrying the blush
                                                                   # of the palette — don't unpin it
                                                                   # without re-rendering.

# ---- PHASE 1: back (long) wall — 5 styling stations (chair + console + mirror + side trolley) ---
# One MirrorStationGroup per station. The group builds the station in a local frame whose +Z is the
# VIEWING AXIS (anchor faces +Z; mirror + counter sit on the +Z wall side, facing back at it), so a
# row of them can be dropped flush on a wall as one rigid unit. It also auto-fits under the ceiling
# (console capped to desk height, mirror shrunk so its top stays under max_top) and stands the mirror
# MIRROR_WALL_OFFSET proud of the wall so the glass reads instead of going coplanar.
# The mirror is UNGATED: it is not wall decor, it is the station — place_mirror() is REQUIRED before
# compile, and its auto-fit is exactly what phase 1 exists to check.
def styling_station():
    with scene.MirrorStationGroup() as st:
        st.set_anchor(scene.AddAsset("a salon styling chair", asset_id=STYLING_CHAIR))
        st.place_counter(scene.AddAsset("a narrow styling station console"))
        st.place_mirror(scene.AddAsset("an arched gold-framed salon wall mirror"))
        if PHASE >= 2:
            # the beside-anchor floor detail — created INSIDE the gate so it never orphans
            st.place_beside(scene.AddAsset("a rolling salon tool trolley cart"), side="right")
    return st

stations = [styling_station() for _ in range(5)]
with scene.GridGroup(sparsity=0.4) as spine:
    spine.place_row(stations)

# ---- PHASE 1: the "cabinets" for the short walls ----------------------------------------------
backwash = 2 * scene.AddAsset("a salon backwash shampoo unit")

# ---- PHASE 1: front (long) wall cluster 1 — a prominent reception: big desk + chair behind ------
with scene.RelativeGroup() as reception:
    desk = scene.AddAsset("a large curved salon reception desk")
    w0, h0, d0 = (float(v) for v in desk.get_whd())
    f = max(2.2 / max(w0, 0.1), 1.0)                       # scale up to >=2.2m wide, proportionally
    desk.scale_only_width(w0 * f); desk.scale_only_height(h0 * f); desk.scale_only_depth(d0 * f)
    reception.set_anchor(desk)
    reception.place_on_back(scene.AddAsset("an ergonomic reception office chair"))   # receptionist behind
    if PHASE >= 2:
        reception.place_on_right(scene.AddAsset("a tall potted plant"))              # decor beside
        reception.place_on_top(scene.AddAsset("a small decorative flower vase"))     # decor on desk
    if PHASE >= 3:
        reception.add_lighting("a brass pendant light", density=0)                   # one pendant

# ---- PHASE 1: front (long) wall cluster 2 — waiting nook: blush velvet pair + brass table -------
with scene.RelativeGroup() as waiting:
    side = scene.AddAsset("a round brass side table")
    waiting.set_anchor(side)                              # place_on_top seats items on the ANCHOR
    tubs = 2 * scene.AddAsset("a blush old-rose velvet accent chair", asset_id=TUB_CHAIR)
    waiting.place_on_left_further(tubs[0])
    waiting.place_on_right_further(tubs[1])
    waiting.face(tubs[0], toward=side); waiting.face(tubs[1], toward=side)
    if PHASE >= 2:
        waiting.place_on_top(scene.AddAsset("a gold magazine rack"))
        waiting.place_rug("a soft blush wool area rug", size=0.8)
    if PHASE >= 3:
        waiting.add_lighting("a brass pendant light", density=0)

with scene.RoomGroup(modulate_scale=0.92, randomness=0.12) as room:
    # UNGATED: the shell has to exist in every phase. Blush walls + polished concrete + white
    # ceiling ARE the palette — the texture strings are the cheapest identity in the program.
    room.place_walls(floor_texture="polished concrete floor",
                     ceiling_texture="white", wall_texture="soft blush pink")
    # PHASE 1 — back (long): styling stations FLUSH against the wall (mirrors sit on it, not floating).
    # facing="back" both orients the spine (rotation 180) AND tells the auto-sizer how deep the back
    # wall row must be — so no redundant room.face() is needed.
    room.place_on_back_wall_center(spine, facing="back")
    # PHASE 1 — front (long): reception + waiting clusters across the opposing wide wall, facing in
    room.place_on_front_left(reception, facing="back")
    room.place_on_front(waiting)
    # PHASE 1 — left/right (short): the cabinets. Retail shelf at the front (reception) end of the left
    # wall; backwash at the center/front of the right wall, away from the styling row.
    room.place_on_left_wall_left(scene.AddAsset("a salon retail product display shelf"))
    room.place_on_right_wall_center(backwash[0])
    room.place_on_right_wall_right(backwash[1])
    # UNGATED: the door's automatic clearance shapes the floor solve, so deferring it to phase 3
    # would change the layout phase 1 is supposed to validate.
    room.place_door("left_wall", position="right")

    if PHASE >= 3:
        # walls & decor: a beauty-salon portrait over the reception, neon at center; the window.
        # This layer is what makes the room read as a BEAUTY salon rather than a barbershop.
        room.place_on_wall_front_left(scene.AddAsset("a large framed fashion portrait of an elegant woman"))
        room.place_on_wall_front_center(scene.AddAsset("a neon salon sign"))
        room.place_window_standard("right_wall", position="center", curtain="sheer white curtains")

scene.export("hair_salon_v1.blend")
