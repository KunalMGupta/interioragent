"""
Restaurant — "Moody Warm Bistro" (planner headline). Built coarse-to-fine, asset-first.

Zoned single room (bar zone + banquette perimeter + center dining clusters + service/host):
  - BACK wall  = the BAR: a rigid bar-station (counter + a row of stools on the customer side +
    a tall back-bar cabinet composed BEHIND it, so the bartender aisle is geometric — the
    bar.md lesson, not a soft clearance).
  - LEFT wall  = a BANQUETTE run: high-back booths against the wall, each with a small table and
    a facing tub chair.
  - CENTER/RIGHT = intimate 2-top dining clusters (round table + two plush leather tub armchairs,
    AroundGroup place_circle(2), jittered), each dressed with a place setting + a candle, some lit
    by a single warm pendant.
  - Entrance/service = a host-stand podium by the door + a sideboard service station (POS + plates).
  - A brick fireplace anchors the right wall; tall greenery in the corners; chandelier over center.

Asset note: stress-tested the whole wishlist first (47/47 resolved, none < 0.30 sim) — restaurant
is a furniture-rich, low-risk category, NO ingest needed. Heroes pinned below were eyeballed via the
retrieve contact sheet; the only weak key asset (back-bar) was fixed by a query REPHRASE that routes
to CabinetandShelfRetriever (a real bottle-shelf hutch) instead of the generic shelving pick.

Build state: DONE / essentially VLM-clean (2026-07-06, seed=37). No rescale / no room-rescale / no
wall overlap; only the known-noisy RotationConstraint ("rotate chair to face table") remains, declined
as noise (place_circle + face() already seat the 2-tops correctly; the render is the arbiter). Two
retrieval traps fixed: (1) "a small round dining table" returned a cafe SET with baked-in folding
chairs -> double-seated the 2-tops; pinned a BARE pedestal table.

Kunal-feedback revision (2026-07-06): (a) the dining chairs were bulky LOUNGE tub chairs (W1.0xD0.97)
that read as living-room furniture -> swapped to a sleek TAUPE curved-back DINING armchair
(future/1805382c, W0.5xD0.53) matching the reference collage. (b) the bar stool mesh is 1.25 m tall,
nearly 2x the low (0.67 m) bar counter, so it towered -> _fit_height() uniformly scales each stool to
a 0.7 m total height (seat ~0.45 m). (c) two dining clusters had interpenetrated: a real DSL bug in
the gradient solver (snap-then-clamp could re-introduce an overlap the clamp created) — fixed in
IDSDL/constraints.py (GradSolver._settle alternates snap<->clamp) + a post-compile RoomGroup._warn_overlaps
that flags any residual overlap as "room too small".
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Restaurant", seed=37)

# --- pinned heroes (verified via retrieve contact sheet) ---
BAR_COUNTER = "hssd/b1c9d7321512686e02f2d0be978056456479e14c"   # wooden bar counter, dark flat top
BACKBAR     = "hssd/d13be6893c60fabc31729e397e85952d552d3d55"   # tall dark-wood bar hutch w/ bottle shelves
BARSTOOL    = "hssd/d10ff3f71a5e1a0534fc43132d54b5a083b8d17f"   # simple wooden bar stool w/ backrest (0.85 sim)
BOOTH       = "future/56f963cd-9ff6-48af-bd68-1db9411b1e6c"     # high-back upholstered booth bench
CHAIR       = "future/1805382c-8d97-452a-b546-59fdd5ddfeeb"     # sleek TAUPE curved-back dining armchair (W0.5xD0.53) — matches the reference
ROUND_TABLE = "future/aaea6776-7dd7-45fd-aa85-41b9b40da6fc"     # BARE warm-wood pedestal round table (no chairs)
HOST_STAND  = "hssd/2fa15bc31819eff32a29e592b6a71011266313a3"   # simple podium (best host-stand substitute)

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
    bar_group.add_lighting("a warm amber glass globe pendant light", density=0.2)
backbar = scene.AddAsset("a tall dark wood back bar cabinet with shelves of liquor bottles",
                         asset_id=BACKBAR, width=2.6)
with scene.RelativeGroup() as bar_station:
    bar_station.set_anchor(bar_group)
    bar_station.place_on_back(backbar)                    # seats the hutch a fixed gap BEHIND = the aisle


# --- an intimate 2-top dining cluster (round table + two sleek dining armchairs), dressed ---
def two_top(lit=False):
    with scene.AroundGroup(sparsity=0.2, jitter=0.4) as g:
        t = scene.AddAsset("a small round wooden bistro dining table", asset_id=ROUND_TABLE, width=0.8)
        g.set_anchor(t)
        chairs = 2 * scene.AddAsset("a sleek taupe upholstered dining armchair with a curved back", asset_id=CHAIR)
        g.place_circle(chairs)
        for c in chairs:
            g.face(c, toward=t)                           # settle the 2-top facing (quiets the rotation alarm)
        g.place_on_top([
            scene.AddAsset("an elegant table place setting with a plate, wine glass and cutlery"),
            scene.AddAsset("a lit candle in a small glass votive holder"),
        ])
        if lit:
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
    room.place_on_back_left_corner(scene.AddAsset("a tall potted indoor olive tree", width=0.9),
                                   facing="front")
    room.place_on_back_right_corner(service, facing="front")

    # LEFT wall = banquette run (booths' backs to the wall, seating extends into the room)
    room.place_on_left(banq_1, facing="right")
    room.place_on_front_left(banq_2, facing="right")

    # CENTER / RIGHT = dining clusters
    room.place_on_center(table_c, facing="front")
    room.place_on_right(table_r, facing="front")
    room.place_on_front_right(table_fr, facing="front")

    # entrance / greenery
    room.place_on_front(scene.AddAsset("a wooden host stand podium", asset_id=HOST_STAND), facing="back")

    # right wall = brick fireplace focal + poster above it; front wall = landscape; left wall = window
    room.place_on_right_wall_center(scene.AddAsset("a classic brick fireplace", width=1.6))
    room.place_on_wall_right_center(scene.AddAsset("a large framed vintage Casablanca movie poster"))
    room.place_on_wall_front_center(scene.AddAsset("a framed landscape painting"))
    room.place_window_standard("left_wall", position="center", curtain="olive green drapes")
    room.place_door("front_wall", position="right")

    # layered warm light: one key chandelier over the center (clusters carry their own pendants)
    room.add_lighting("an elegant warm dining chandelier", density=0)

scene.export("restaurant.blend")
