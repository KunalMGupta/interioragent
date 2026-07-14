"""Casino — "Red-Gold Opulent Gaming Floor" (planner target: tmp/casino/plan/plan.png).

Planner target: deep-red gold-damask carpet, ebony + gold wall panelling, a grand crystal
chandelier over a CENTRAL blackjack hub ringed with red-velvet swivel seating; perimeter rows of
amber-glowing slot machines line the long walls; a luxe black-marble/gold BAR is the secondary
anchor. Palette: deep red + gold, ebony + brass. Opulent, sealed, lit entirely by its fixtures.

Layout — LARGE MULTI-ZONE: a table HUB in the middle, repeated ROWS on the long walls, a BAR on
a short wall (say WHY each slot is what it is):
- CENTRE     : the HERO blackjack hub — a felt card table ringed 360 degrees with red velvet
               swivel chairs (AroundGroup.place_circle), the grand chandelier directly above.
               A gaming table is engaged from every side, so it cannot live on a wall.
- LEFT wall  : a perimeter SLOT bank (a GridGroup row), faced INTO the room (facing="right" —
               a wall-backed machine's screen must point at the OPPOSITE side, not at its wall).
- RIGHT wall : the mirror-image slot bank (facing="left"). Long strips on the LONG walls are what
               size the room correctly — a long slot row on a short wall would square the floor.
- BACK wall  : the BAR (secondary anchor). The counter sits flush; stools + bottles project into
               the room. Its gilded back-bar mirror hangs above it.
- FRONT wall : the entry door (right) + the gilded framed art. The short walls are the ONLY walls
               with headroom for art — the slot machines are ~2 m tall in a 3 m room.
- WINDOWS    : NONE, deliberately. An authentic casino floor is sealed and windowless; the mood is
               carried entirely by add_lighting (a statement chandelier + a low warm ambient fill).
               Expect the phase-1/2 renders to look dark until the phase-3 light pass.

Identity comes from the two REPEATED ROWS of slot machines (the one asset the dataset gets
unambiguously right) plus the 360-degree ring of red velvet around the hub — not from the card
table, which is an honest substitute (no green-felt casino table exists in the pool).

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/casino_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 dresses the surfaces; phase 3 adds the wall decor + lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Casino", seed=29)

# ---- pinned assets (audited previews; the audit table is scenes/work/casino.md) ----------------
SLOT   = "hssd/f06d7023a43b441a5c82402fc63b90932a749cb6"  # IGT CrystalDual gaming machine — GOOD,
                                                          # a genuine slot cabinet; the one asset
                                                          # that names the room, so it is duplicated
TABLE  = "hssd/81f092c5722ae67b49104b660bcf3f0fec3c69f0"  # flat-top walnut card table — WEAK but
                                                          # pinned: a green FELT table is an ingest
                                                          # gap (the pool has pool/foosball only)
CHAIR  = "hssd/c4423cf1fade284d5fa91fea7e50a15d54c9cc2d"  # red tufted velvet swivel chair (sim .75)
                                                          # — the plan's hero seat; the unpinned
                                                          # "padded casino chair" query resolved to a
                                                          # LEGLESS floor cushion (wrong seat height)
BAR_CT = "hssd/b1c9d7321512686e02f2d0be978056456479e14c"  # long straight bar counter — GOOD,
                                                          # against-wall placeable

scene.prefetch_assets([
    "a colorful slot machine",
    "a green felt blackjack card table",
    "a red velvet tufted swivel armchair",
    "a long bar counter",
    "a bar stool with a red cushioned seat",
    "a tall liquor bottle",
    "a large ornate gold-framed wall mirror",
    "an ornate gold-framed classical oil painting",
    "a framed vintage playing-cards poster in a gold frame",
])

# ============================ CENTRE: the blackjack hub (hero) ============================
with scene.AroundGroup(sparsity=0.25, jitter=0.4) as hub:
    hub.set_anchor(scene.AddAsset("a green felt blackjack card table", asset_id=TABLE))
    hub.place_circle(6 * scene.AddAsset("a red velvet tufted swivel armchair", asset_id=CHAIR))
    # (no on-table prop: "poker chips"/"playing cards" aren't in the dataset — the query pulled a
    #  children's book rack. A real casino-chip tray is an ingest target; the felt top reads fine
    #  bare. This is why PHASE 2 adds NOTHING to the hero table.)
    if PHASE >= 3:
        # the grand statement fixture, directly over the hub. density=0 => exactly ONE fixture.
        hub.add_lighting("an ornate gold and crystal chandelier", density=0)

# ==================== PERIMETER: slot banks (one row per LONG wall) =======================
left_slots  = 5 * scene.AddAsset("a colorful slot machine", asset_id=SLOT)
right_slots = 5 * scene.AddAsset("a colorful slot machine", asset_id=SLOT)
with scene.GridGroup(sparsity=0.35, randomness=0.12) as slots_left:
    slots_left.place_row(left_slots)
with scene.GridGroup(sparsity=0.35, randomness=0.12) as slots_right:
    slots_right.place_row(right_slots)

# ==================== BACK short wall: the BAR (secondary anchor) =========================
# The stools are FLOOR geometry, so they stay in PHASE 1 with the counter: deferring them would
# change the bar slot's depth and therefore the shell the phase-1 build validated.
# Stools = ONE nested row, not place_on_front_left/front/front_right — the three per-corner verbs
# split them to the two ENDS of the counter, which reads wrong for a bar.
with scene.GridGroup(sparsity=0.5, randomness=0.1) as stool_row:            # 3 stools in ONE row
    stool_row.place_row(3 * scene.AddAsset("a bar stool with a red cushioned seat"))
with scene.RelativeGroup() as bar:
    bar.set_anchor(scene.AddAsset("a long bar counter", asset_id=BAR_CT))
    bar.place_on_front(stool_row)                          # the whole row in front of the counter
    if PHASE >= 2:
        # the surface layer that turns a counter into a BAR. Gated INSIDE the with-block: a group
        # compiles on __exit__, so a place_on_top gated outside it never runs — the prop is simply
        # GONE and the lints/VLM loop stay clean (prison_cell's bug).
        bar.place_on_top(4 * scene.AddAsset("a tall liquor bottle"))
    if PHASE >= 3:
        bar.add_lighting("warm recessed ambient ceiling downlights", density=0.02)  # room fill

# ================================== ROOM =================================================
with scene.RoomGroup(modulate_scale=1.0, randomness=0.12) as room:
    room.place_walls(floor_texture="deep red carpet with gold floral damask pattern",
                     ceiling_texture="dark ebony ceiling with gold trim",
                     wall_texture="dark ebony wood panelling with gold inlay")
    # CENTRE hero
    room.place_on_center(hub)
    # LEFT + RIGHT long walls = slot rows facing INTO the room
    room.place_on_left_wall_center(slots_left, facing="right")
    room.place_on_right_wall_center(slots_right, facing="left")
    # BACK short wall = the bar (counter flush to the wall, stools + bottles project into the room)
    room.place_on_back_wall_center(bar, facing="front")
    # FRONT short wall = entry. UNGATED: the door's automatic clearance shapes the floor solve, so
    # deferring it to phase 3 would change the layout phase 1 validated.
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # --- gilded wall decor: opulent framed art on the SHORT walls only (the slot walls have
        # no headroom — the machines are ~2 m tall in a 3 m room). Three distinct wall slots,
        # no overlap. No window: a casino floor is sealed (see the docstring).
        room.place_on_wall_back_center(
            scene.AddAsset("a large ornate gold-framed wall mirror"))              # back-bar mirror
        room.place_on_wall_front_left(
            scene.AddAsset("an ornate gold-framed classical oil painting"))        # entry wall art
        room.place_on_wall_front_center(
            scene.AddAsset("a framed vintage playing-cards poster in a gold frame"))

scene.export("casino_v1.blend")
