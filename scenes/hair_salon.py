"""
Hair salon — "Luxe Row-Station Salon Spine". Blush + brass + concrete.

Built coarse-to-fine (see skills/workflow/coarse_to_fine.md + skills/examples/hair_salon.md):
  Phase 1 — major assets / proportions: load the two LONG walls, keep the two SHORT walls light, so
    the room comes out WIDE and shallow (real salons are).
      - back (long) : the styling row — 5 MirrorStationGroup units (chair + console + mirror + trolley),
                      seated FLUSH so the mirrors sit on the wall, not floating.
      - front (long): a prominent reception (desk + chair + decor) and the waiting nook.
      - left/right (short): the "cabinets" — retail shelf (by reception) + backwash row (away from
                      the styling row). Openings tuck onto the short walls.
  Phase 2 — surface & floor details: on-desk vase + plant + receptionist chair; waiting nook's
    magazine rack + rug; per-station trolley; brass pendants.
  Phase 3 — walls & decor: a beauty-salon portrait + neon sign, door, window + curtain.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("HairSalon", seed=77)

# --- Phase 1: back (long) wall — 5 styling stations (chair + console + mirror + side trolley) ---
def styling_station():
    with scene.MirrorStationGroup() as st:
        st.set_anchor(scene.AddAsset("a salon styling chair",
                                     asset_id="custom/59a3f803acb6e00ec8e3637e862c879cf03c06be"))
        st.place_counter(scene.AddAsset("a narrow styling station console"))
        st.place_mirror(scene.AddAsset("an arched gold-framed salon wall mirror"))
        st.place_beside(scene.AddAsset("a rolling salon tool trolley cart"), side="right")
    return st

stations = [styling_station() for _ in range(5)]
with scene.GridGroup(sparsity=0.4) as spine:
    spine.place_row(stations)

# --- Phase 1: the "cabinets" for the short walls ---
backwash = 2 * scene.AddAsset("a salon backwash shampoo unit")

# --- Phase 2: front (long) wall cluster 1 — a prominent reception: big desk + chair behind + decor ---
with scene.RelativeGroup() as reception:
    desk = scene.AddAsset("a large curved salon reception desk")
    w0, h0, d0 = (float(v) for v in desk.get_whd())
    f = max(2.2 / max(w0, 0.1), 1.0)                       # scale up to >=2.2m wide, proportionally
    desk.scale_only_width(w0 * f); desk.scale_only_height(h0 * f); desk.scale_only_depth(d0 * f)
    reception.set_anchor(desk)
    reception.place_on_back(scene.AddAsset("an ergonomic reception office chair"))   # receptionist behind
    reception.place_on_right(scene.AddAsset("a tall potted plant"))                  # decor beside
    reception.place_on_top(scene.AddAsset("a small decorative flower vase"))         # decor on desk
    reception.add_lighting("a brass pendant light", density=0)

# --- Phase 2: front (long) wall cluster 2 — waiting nook: blush velvet pair + brass table + rug ---
with scene.RelativeGroup() as waiting:
    side = scene.AddAsset("a round brass side table")
    waiting.set_anchor(side)
    tubs = 2 * scene.AddAsset("a blush old-rose velvet accent chair",
                              asset_id="hssd/3b522b2a379a3a5248dbaa0159cc5ddfbf43a2e0")
    waiting.place_on_left_further(tubs[0])
    waiting.place_on_right_further(tubs[1])
    waiting.face(tubs[0], toward=side); waiting.face(tubs[1], toward=side)
    waiting.place_on_top(scene.AddAsset("a gold magazine rack"))
    waiting.place_rug("a soft blush wool area rug", size=0.8)
    waiting.add_lighting("a brass pendant light", density=0)

with scene.RoomGroup(modulate_scale=0.92, randomness=0.12) as room:
    room.place_walls(floor_texture="polished concrete floor",
                     ceiling_texture="white", wall_texture="soft blush pink")
    # Phase 1 — back (long): styling stations FLUSH against the wall (mirrors sit on it, not floating).
    # facing="back" both orients the spine (rotation 180) AND tells the auto-sizer how deep the back
    # wall row must be — so no redundant room.face() is needed.
    room.place_on_back_wall_center(spine, facing="back")
    # Phase 2 — front (long): reception + waiting clusters across the opposing wide wall, facing in
    room.place_on_front_left(reception, facing="back")
    room.place_on_front(waiting)
    # Phase 1 — left/right (short): the cabinets. Retail shelf at the front (reception) end of the left
    # wall; backwash at the center/front of the right wall, away from the styling row.
    room.place_on_left_wall_left(scene.AddAsset("a salon retail product display shelf"))
    room.place_on_right_wall_center(backwash[0])
    room.place_on_right_wall_right(backwash[1])
    # Phase 3 — walls & decor: a beauty-salon portrait over the reception, neon at center; openings
    room.place_on_wall_front_left(scene.AddAsset("a large framed fashion portrait of an elegant woman"))
    room.place_on_wall_front_center(scene.AddAsset("a neon salon sign"))
    room.place_door("left_wall", position="right")
    room.place_window_standard("right_wall", position="center", curtain="sheer white curtains")

scene.export("hair_salon.blend")
