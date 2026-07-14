"""Restaurant — "Moody Warm Bistro" (planner headline). Built coarse-to-fine, asset-first.

Planner target: intimate dining clusters + a banquette-first perimeter; candlelit tables with
glassware; sleek curved-back chairs; a continuous bar with stools + back-bar shelving; a discreet
host stand + service station; greenery at the edges; layered amber light (pendants over the
clusters + a key chandelier). Palette: cognac, olive, taupe, charcoal; warm wood floor, brick accent.

Layout — a ZONED SINGLE ROOM (bar wall + banquette wall + a field of 2-top clusters):
- BACK wall  : the BAR. A rigid bar-station — counter (anchor) + a customer-side stool ROW +
               a tall back-bar hutch composed BEHIND it, so the bartender aisle is GEOMETRIC (the
               bar.md lesson), not a soft clearance. The busy back wall is deliberately art-free.
               Its corners take the greenery (left) and the service sideboard (right).
- LEFT wall  : the BANQUETTE run — booths' backs to the wall (facing="right"), seating extending
               into the room, each booth with its own table + a facing chair. The window lives here
               because this is the only wall whose furniture is low-backed enough to sit under it.
- RIGHT wall : the brick FIREPLACE — the warm focal that makes the room read "bistro" and not
               "canteen" — with the Casablanca poster hung ABOVE it.
- CENTRE     : the 2-top cluster field. The money shot, so it stays furniture-only: bare round
               table + two chairs on a place_circle, jittered, some lit by a single pendant.
- FRONT      : the entrance. Host-stand podium facing back into the room + the door (right); the
               third 2-top fills the front-right so the entrance zone is not a dead strip.

Identity comes from the REPEATED UNIT, not from any one hero: build ONE 2-top (table + two chairs +
its place setting + candle) and duplicate it three times, so every cluster is dressed identically
and the room reads as a service floor. The table is pinned BARE (a generic "bistro table" query
returns a cafe SET with folding chairs baked in, which double-seats every cluster).

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/restaurant_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the surfaces (place settings, candles, POS,
greenery); phase 3 adds the wall decor, the window and all the lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Restaurant", seed=37)

# --- pinned heroes (verified via the retrieve contact sheet) ---
BAR_COUNTER = "hssd/b1c9d7321512686e02f2d0be978056456479e14c"   # wooden bar counter, dark flat top
BACKBAR     = "hssd/d13be6893c60fabc31729e397e85952d552d3d55"   # tall dark-wood bar hutch w/ bottle shelves;
                                                                # the ONLY weak retrieval (0.495) — the rephrase
                                                                # to "cabinet with shelves of liquor bottles"
                                                                # routes to CabinetandShelfRetriever (0.62)
BARSTOOL    = "hssd/d10ff3f71a5e1a0534fc43132d54b5a083b8d17f"   # simple wooden bar stool w/ backrest (0.85 sim)
BOOTH       = "future/56f963cd-9ff6-48af-bd68-1db9411b1e6c"     # high-back upholstered booth bench
CHAIR       = "future/1805382c-8d97-452a-b546-59fdd5ddfeeb"     # sleek TAUPE curved-back DINING armchair
                                                                # (W0.5xD0.53) — the first pick was a LOUNGE tub
                                                                # chair (W1.0xD0.97) that read living-room; pin for
                                                                # dining footprint AND the plan's muted tone
ROUND_TABLE = "future/aaea6776-7dd7-45fd-aa85-41b9b40da6fc"     # BARE warm-wood pedestal round table (no chairs)
HOST_STAND  = "hssd/2fa15bc31819eff32a29e592b6a71011266313a3"   # simple podium — no true host stand in the pool

scene.prefetch_assets([
    "a small round wooden bistro dining table", "a small square bistro dining table",
    "a sleek taupe upholstered dining armchair with a curved back",
    "a high-back upholstered restaurant booth bench",
    "a long wooden restaurant bar counter with a paneled front",
    "a tall dark wood back bar cabinet with shelves of liquor bottles",
    "a wooden bar stool with a backrest",
    "an elegant table place setting with a plate, wine glass and cutlery",
    "a lit candle in a small glass votive holder",
    "a small vase with a single flower",
    "a warm amber glass globe pendant light", "an elegant warm dining chandelier",
    "a wooden host stand podium", "a dark wooden sideboard buffet cabinet",
    "a modern touchscreen point of sale terminal",
    "a tall potted indoor olive tree", "a large leafy potted plant",
    "a framed vintage Casablanca movie poster", "a framed landscape painting",
    "a classic brick fireplace", "a patterned area rug", "a wooden interior door",
])


def _fit_height(obj, h):
    """Uniformly scale (ALL dims) so the object's total HEIGHT == h — preserves the mesh's own
    proportions. The bar-stool mesh is 1.25 m tall, nearly 2x this low (0.67 m) bar counter, so a
    stool taller than ~0.7 m towers over the bar; cap it here."""
    W, H, D = (float(v) for v in obj.get_whd())
    if H > 1e-6:
        f = h / H
        obj.scale_only_width(W * f); obj.scale_only_height(H * f); obj.scale_only_depth(D * f)
    return obj


# --- the BAR station (counter + stool row + back-bar), one rigid unit -> geometric aisle ---
counter = scene.AddAsset("a long wooden restaurant bar counter with a paneled front",
                         asset_id=BAR_COUNTER, width=3.2)
with scene.AroundGroup(sparsity=0.15, jitter=0.2) as bar_group:
    bar_group.set_anchor(counter)
    # stool mesh is 1.25 m tall vs a 0.67 m counter -> cap total height at 0.7 m (seat ~0.45 m)
    stools = [_fit_height(scene.AddAsset("a wooden bar stool with a backrest", asset_id=BARSTOOL), 0.7)
              for _ in range(4)]
    bar_group.place_rectilinear(longer_side1=stools)      # one row, customer side, uniform facing (bar.md)
    if PHASE >= 3:
        bar_group.add_lighting("a warm amber glass globe pendant light", density=0.2)
backbar = scene.AddAsset("a tall dark wood back bar cabinet with shelves of liquor bottles",
                         asset_id=BACKBAR, width=2.6)
with scene.RelativeGroup() as bar_station:
    bar_station.set_anchor(bar_group)
    bar_station.place_on_back(backbar)                    # seats the hutch a fixed gap BEHIND = the aisle


# --- an intimate 2-top dining cluster (round table + two sleek dining armchairs), dressed ---
# Build ONE unit, then stamp it out: every cluster gets the same seating and the same dressing.
def two_top(lit=False):
    with scene.AroundGroup(sparsity=0.2, jitter=0.4) as g:
        t = scene.AddAsset("a small round wooden bistro dining table", asset_id=ROUND_TABLE, width=0.8)
        g.set_anchor(t)
        chairs = 2 * scene.AddAsset("a sleek taupe upholstered dining armchair with a curved back", asset_id=CHAIR)
        g.place_circle(chairs)
        for c in chairs:
            g.face(c, toward=t)                           # settle the 2-top facing (quiets the rotation alarm)
        if PHASE >= 2:
            g.place_on_top([
                scene.AddAsset("an elegant table place setting with a plate, wine glass and cutlery"),
                scene.AddAsset("a lit candle in a small glass votive holder"),
            ])
        if lit and PHASE >= 3:
            g.add_lighting("a warm amber glass globe pendant light", density=0)
    return g

table_c, table_r, table_fr = two_top(lit=True), two_top(lit=True), two_top()


# --- a banquette unit: high-back booth against the wall + table + a facing tub chair ---
def banquette():
    with scene.RelativeGroup() as g:
        booth = scene.AddAsset("a high-back upholstered restaurant booth bench", asset_id=BOOTH, width=1.4)
        g.set_anchor(booth)
        t = scene.AddAsset("a small square bistro dining table", width=0.7)
        g.place_on_front(t)
        chair = scene.AddAsset("a sleek taupe upholstered dining armchair with a curved back", asset_id=CHAIR)
        g.place_on_front_further(chair)
        g.face(chair, toward=booth)                       # far chair turns in to face the booth
    return g

banq_1, banq_2 = banquette(), banquette()


# --- service station: sideboard with a POS terminal + a stack of plates on top ---
with scene.RelativeGroup() as service:
    service.set_anchor(scene.AddAsset("a dark wooden sideboard buffet cabinet", width=1.4))
    if PHASE >= 2:
        service.place_on_top([
            scene.AddAsset("a modern touchscreen point of sale terminal"),
            scene.AddAsset("a small stack of white restaurant plates"),
        ])


with scene.RoomGroup(modulate_scale=0.8, randomness=0.2, max_height=3.4) as room:
    room.place_walls(floor_texture="warm walnut herringbone wood floor",
                     ceiling_texture="warm off-white plaster",
                     wall_texture="warm taupe plaster with a rustic exposed brick accent")

    # BACK wall = the bar line
    room.place_on_back(bar_station, facing="front")
    room.place_on_back_right_corner(service, facing="front")

    # LEFT wall = banquette run (booths' backs to the wall, seating extends into the room)
    room.place_on_left(banq_1, facing="right")
    room.place_on_front_left(banq_2, facing="right")

    # CENTER / RIGHT = dining clusters
    room.place_on_center(table_c, facing="front")
    room.place_on_right(table_r, facing="front")
    room.place_on_front_right(table_fr, facing="front")

    # entrance: the host stand faces back into the room; the door's auto clearance shapes the
    # floor solve, so it is placed in PHASE 1 and NOT gated
    room.place_on_front(scene.AddAsset("a wooden host stand podium", asset_id=HOST_STAND), facing="back")
    room.place_door("front_wall", position="right")

    # right wall = brick fireplace focal (floor furniture: place_on_<wall>_wall_<pos>)
    room.place_on_right_wall_center(scene.AddAsset("a classic brick fireplace", width=1.6))

    # UNGATED: the olive tree is FLOOR-standing and its corner footprint feeds the auto-size —
    # gating it to phase 2 shrank the phase-1 shell until two dining clusters could no longer
    # separate (RoomGroup overlap WARNING in the 2026-07-13 verification round).
    room.place_on_back_left_corner(scene.AddAsset("a tall potted indoor olive tree", width=0.9),
                                   facing="front")

    if PHASE >= 3:
        # hung art: place_on_wall_<wall>_<pos> — a different method family from the fireplace above
        room.place_on_wall_right_center(scene.AddAsset("a large framed vintage Casablanca movie poster"))
        room.place_on_wall_front_center(scene.AddAsset("a framed landscape painting"))
        room.place_window_standard("left_wall", position="center", curtain="olive green drapes")
        # layered warm light: one key chandelier over the center (clusters carry their own pendants)
        room.add_lighting("an elegant warm dining chandelier", density=0)

scene.export("restaurant_v1.blend")
