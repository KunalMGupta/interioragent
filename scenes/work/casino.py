"""
Casino — "Red-Gold Opulent Gaming Floor" (planner target: tmp/casino/plan/plan.png).

Look (from the plan): deep-red gold-damask carpet, ebony + gold wall panelling, a grand crystal
chandelier over a CENTRAL blackjack hub ringed with red-velvet swivel seating; perimeter rows of
amber-glowing slot machines line the long walls; a luxe black-marble/gold BAR is the secondary
anchor. No windows (an authentic casino floor is sealed and lit entirely by the chandelier + warm
ambient light) — mood comes from the fixtures, not daylight.

Zone map:
  - CENTRE            = the HERO blackjack hub: a felt card table ringed 360° with red velvet
                        swivel chairs, the grand chandelier directly above.
  - LEFT+RIGHT (long) = perimeter SLOT banks: a row of machines against each long wall facing in.
  - BACK (short)      = the BAR: long counter + stools + bottles, backlit gilded art above.
  - FRONT (short)     = entry door + neon casino sign + gilded framed art.

Phase 1: blackjack hub + the two perimeter slot rows + bar counter (floor anchors, layout).
Phase 2: bar cluster (stools + bottles) + on-table decor + chandelier/ambient lighting (details).
Phase 3: neon sign, gilded art, door, final finishes (walls & decor).
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Casino", seed=29)

# --- pinned assets (audited previews; see scenes/work/casino.md) ---
_SLOT  = "hssd/f06d7023a43b441a5c82402fc63b90932a749cb6"   # IGT CrystalDual gaming machine (GOOD)
_TABLE = "hssd/81f092c5722ae67b49104b660bcf3f0fec3c69f0"   # flat-top walnut card table (felt table = ingest gap)
_CHAIR = "hssd/c4423cf1fade284d5fa91fea7e50a15d54c9cc2d"   # red tufted velvet swivel chair (sim .75 — the plan's hero seat)
_BAR   = "hssd/b1c9d7321512686e02f2d0be978056456479e14c"   # long straight bar counter (GOOD)

# ============================ CENTRE: the blackjack hub (hero) ============================
with scene.AroundGroup(sparsity=0.25, jitter=0.4) as hub:
    hub.set_anchor(scene.AddAsset("a green felt blackjack card table", asset_id=_TABLE))
    hub.place_circle(6 * scene.AddAsset("a red velvet tufted swivel armchair", asset_id=_CHAIR))
    # (no on-table prop: "poker chips"/"playing cards" aren't in the dataset — the query pulled a
    #  children's book rack. A real casino-chip tray is an ingest target; the felt top reads fine bare.)
    hub.add_lighting("an ornate gold and crystal chandelier", density=0)   # grand statement fixture over the hub

# ============================ PERIMETER: slot banks (one row per long wall) ============================
left_slots  = 5 * scene.AddAsset("a colorful slot machine", asset_id=_SLOT)
right_slots = 5 * scene.AddAsset("a colorful slot machine", asset_id=_SLOT)
with scene.GridGroup(sparsity=0.35, randomness=0.12) as slots_left:
    slots_left.place_row(left_slots)
with scene.GridGroup(sparsity=0.35, randomness=0.12) as slots_right:
    slots_right.place_row(right_slots)

# ============================ BACK short wall: the BAR (secondary anchor) ============================
# Ph2: counter -> a real bar. Bottles on the top, a single row of stools along the front, warm fill.
with scene.GridGroup(sparsity=0.5, randomness=0.1) as stool_row:            # 3 stools lined up in ONE row
    stool_row.place_row(3 * scene.AddAsset("a bar stool with a red cushioned seat"))
with scene.RelativeGroup() as bar:
    bar.set_anchor(scene.AddAsset("a long bar counter", asset_id=_BAR))
    bar.place_on_top(4 * scene.AddAsset("a tall liquor bottle"))
    bar.place_on_front(stool_row)                                          # the whole row in front of the counter
    bar.add_lighting("warm recessed ambient ceiling downlights", density=0.02)   # ambient fill for the room

# ============================ ROOM ============================
with scene.RoomGroup(modulate_scale=1.0, randomness=0.12) as room:
    room.place_walls(floor_texture="deep red carpet with gold floral damask pattern",
                     ceiling_texture="dark ebony ceiling with gold trim",
                     wall_texture="dark ebony wood panelling with gold inlay")
    # CENTRE hero
    room.place_on_center(hub)
    # LEFT + RIGHT long walls = slot rows facing into the room
    room.place_on_left_wall_center(slots_left, facing="right")
    room.place_on_right_wall_center(slots_right, facing="left")
    # BACK short wall = the bar (counter flush to the wall, stools + bottles project into the room)
    room.place_on_back_wall_center(bar, facing="front")
    # FRONT short wall = entry
    room.place_door("front_wall", position="right")

    # --- Phase 3: gilded wall decor (opulent framed art on the short walls; slot walls have no headroom) ---
    room.place_on_wall_back_center(scene.AddAsset("a large ornate gold-framed wall mirror"))         # back-bar mirror
    room.place_on_wall_front_left(scene.AddAsset("an ornate gold-framed classical oil painting"))    # entry wall art
    room.place_on_wall_front_center(scene.AddAsset("a framed vintage playing-cards poster in a gold frame"))

scene.export("casino.blend")
