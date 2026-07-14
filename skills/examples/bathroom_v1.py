"""Bathroom — "Marble & Brass Spa Bath" (planner-driven).

Planner target: luminous white marble WARMED by brass hardware and natural wood; the freestanding
oval tub anchors the room under a big window with a statement brass chandelier over the soak zone;
a walk-in glass shower is the open counterpoint; a warm-wood double vanity with a marble top is the
grooming zone; lush ferns/eucalyptus, candles and plush towels add the spa ritual. Palette: white
marble, warm wood, brass, a pale sage accent.

Layout — TWO HEROES FACING ACROSS THE LONG AXIS (the two long walls get the two big fixtures, the
two short walls get the wet zone and the storage/entry):
- BACK wall  (long) : the freestanding tub HERO. It gets a whole generous wall because a soaking
                      tub only reads as a spa if it is FREESTANDING — pushed into a corner it turns
                      back into a builder's alcove bath. The window sits over it; the brass
                      chandelier hangs over the soak zone.
- FRONT wall (long) : the warm-wood double vanity, facing the tub across the room. The second-widest
                      run in the plan, so it takes the second long wall — and the two heroes look at
                      each other down the short axis instead of fighting for one wall.
- LEFT wall  (short): the WET ZONE — walk-in glass shower + wall-hung toilet. Both are short, boxy
                      and plumbing-bound, so they share the short wall and keep the long walls for
                      the heroes.
- RIGHT wall (short): the door + the tall linen tower. The entry wall does the storage: a linen
                      tower is a vertical strip, the only thing that fits beside a door.
- CENTRE            : deliberately OPEN — the barefoot lane between tub and vanity. A bathroom you
                      cannot walk through is not a spa.

Identity comes from the FIXTURES BEING SET ASSETS and from the surface ritual — the caddy across
the tub, the fern and the candle cluster beside it, the corner palm, the towel ladder. The vanity
already ships with its own mirror, so nothing is stacked on it and no second mirror is hung.

NOTE (the reason this program has helpers at all): several bathroom fixtures carry broken real-world
`scale` metadata — the pinned tub resolves to 0.2 m long. Dimensions are enforced up front with
`_fit_width` / `_dims` BEFORE any group is built, so the fixtures read at true size and their
on-top / beside items are positioned against the right footprint.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/bathroom_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 dresses the surfaces and the floor; phase 3 adds the wall
decor, the window and the chandelier.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("BathroomSpa", seed=21)

# ---- pinned assets (audited previews; the fixture pins exist because CAPTIONS and SCALE both lie) -
TUB     = "hssd/4106160be8e18d73aa704da0ed993aed8175b4d4"  # sleek white freestanding oval tub. Its
                                                           # PROPORTIONS are right (0.20:0.10:0.06 ~
                                                           # a real tub) but its metadata scale says
                                                           # 0.2 m LONG — pinned so the uniform
                                                           # width-fit below is applied to a known
                                                           # mesh, not to whatever retrieval returns.
VANITY  = "hssd/44a88da97b60a73257237b8bfe6e87dbfe1106c8"  # warm-wood DOUBLE vanity, marble top. A
                                                           # SET asset: the mesh spans cabinet ->
                                                           # sinks -> its OWN wall mirror. Pinned so
                                                           # the vanity tagger's `double` -> 1.5 m /
                                                           # floor-mount metadata is the one applied.
CADDY   = "hssd/c758aecbc16adc68977ef9f77c34adee2acd7b7d"  # wooden bath caddy tray — the one prop
                                                           # that names the tub as a SOAK.
BATH_MAT= "hssd/a63f792f89c348735c6a4a2208e3881a869f68e6"  # a verified-FLAT mat. Many "bath mat"
                                                           # picks are modelled UPRIGHT (thin in
                                                           # depth); place_rug scales width+depth and
                                                           # the upright height survives as a giant
                                                           # slab, and the export is yaw-only so it
                                                           # cannot be tilted down.
LADDER  = "hssd/f63203ce3955e3df53c4e59d9e73f9fff3a6c351"  # wooden towel ladder that actually CARRIES
                                                           # a towel — the bare-ladder picks read as
                                                           # a stepladder in a bathroom.


def _fit_width(o, target_w):
    """Scale an asset UNIFORMLY so its width == target_w — keeps the mesh's own proportions intact
    (the right way to fix bad scale metadata without distorting the geometry)."""
    w0, h0, d0 = o.get_width(), o.get_height(), o.get_depth()
    f = target_w / max(w0, 1e-6)
    o.scale_only_width(w0 * f); o.scale_only_height(h0 * f); o.scale_only_depth(d0 * f)
    return o


def _dims(o, w=None, h=None, d=None):
    """Force per-axis real-world dims — only for assets whose mesh PROPORTIONS are genuinely wrong
    (e.g. a shower enclosure modelled too short, a linen tower modelled too tall)."""
    if w is not None: o.scale_only_width(w)
    if h is not None: o.scale_only_height(h)
    if d is not None: o.scale_only_depth(d)
    return o


scene.prefetch_assets([
    "a sleek white freestanding oval soaking bathtub",
    "a modern wood double bathroom vanity with marble top and two sinks",
    "a walk-in glass shower enclosure",
    "a modern white wall-hung toilet",
    "a tall narrow bathroom linen cabinet with baskets",
    "a wooden towel ladder with rolled towels",
    "a brass drum chandelier",
    "a tall potted areca palm plant",
    "a lush potted fern in a white pot",
    "a wooden bathtub caddy tray",
    "a cluster of white spa pillar candles",
    "a framed botanical wall art print",
])

# ---- PHASE 1 — the fixtures, sized to real-world dimensions (metadata scale is unreliable) -------
tub_asset = scene.AddAsset("a sleek white freestanding oval soaking bathtub", asset_id=TUB)
# proportions are fine; scale UNIFORMLY so it is 1.6 m long (never per-axis — that distorts the rim).
_fit_width(tub_asset, 1.6)

# AddAsset auto-sizes any tagged vanity to its real width + records its mount (see SceneProgRoom).
# A 'double' -> 1.5 m wide, floor-mounted; a 'floating' would auto-narrow AND wall-mount, no extra code.
vanity_asset = scene.AddAsset("a modern wood double bathroom vanity with marble top and two sinks",
                              asset_id=VANITY)

# toilet meshes often bundle a TP roll / brush / cistern into one bbox, so the real seat reads small;
# scale up uniformly (~1.5x its 0.4 m metadata width) so the seat itself looks right, undistorted.
toilet = _fit_width(scene.AddAsset("a modern white wall-hung toilet"), 0.90)
shower = _dims(scene.AddAsset("a walk-in glass shower enclosure"), w=1.0, h=2.0, d=0.9)
linen  = _dims(scene.AddAsset("a tall narrow bathroom linen cabinet with baskets"), h=1.9)

# NOTE: we deliberately DON'T place_on_top of the vanity — it's a complete set with a complex top
# (sinks/faucets), so stacked decor sits unreliably. If counter decor is wanted, retrieve a vanity
# variant that already bundles small items instead. The vanity is placed directly on its wall below.

# ---- the HERO unit: the freestanding tub, and the spa ritual that hangs off it --------------------
with scene.RelativeGroup() as tub:
    tub.set_anchor(tub_asset)            # place_on_top / place_rug seat items on the ANCHOR
    if PHASE >= 2:
        # Every asset below is CREATED INSIDE the gate — nothing orphans at phase 1.
        # These gates MUST live inside the `with` block: a group compiles on __exit__, so an
        # op registered after the block never runs and the prop is silently GONE.
        tub.place_on_top(scene.AddAsset("a wooden bathtub caddy tray", asset_id=CADDY))
        tub.place_on_left(scene.AddAsset("a lush potted fern in a white pot"))
        tub.place_on_right(scene.AddAsset("a cluster of white spa pillar candles"))
        tub.place_rug("a simple rectangular bath mat", size=0.8, asset_id=BATH_MAT)
    if PHASE >= 3:
        # The statement brass chandelier, hung over the SOAK ZONE (density=0 -> exactly one fixture).
        tub.add_lighting("a brass drum chandelier", density=0)

# modulate_scale=0.72 — a spa bath must feel enclosed; a full-size shell reads as a changing room.
with scene.RoomGroup(modulate_scale=0.72, randomness=0.1) as room:
    # A mid-tone SATURATED wall is what stops an all-marble room from blowing out to white under
    # window daylight (every surface is high-albedo and inter-reflects the sky). Soft sage is also
    # the brief's accent; the honed GREY marble floor keeps the tonal range — the same trick as the
    # hair salon's blush walls.
    room.place_walls(floor_texture="honed grey marble tiles",
                     ceiling_texture="white", wall_texture="soft sage green")

    # --- PHASE 1 — the two heroes on the two long walls, facing each other across the open lane ---
    room.place_on_back_wall_center(tub)                    # tub under the window
    room.place_on_front_wall_center(vanity_asset)          # vanity set (auto floor/floating mount)
    # --- PHASE 1 — the short walls: the wet zone + storage ---
    room.place_on_left_wall_left(shower)
    room.place_on_left_wall_right(toilet)
    room.place_on_right_wall_center(linen)
    # The door is UNGATED — its automatic clearance shapes the floor solve, so deferring it to
    # phase 3 would change the very layout phase 1 exists to validate.
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        # Floor dressing: corner greenery + the towel ladder (the bath mat rides with the tub group).
        room.place_on_back_left_corner(scene.AddAsset("a tall potted areca palm plant"))
        room.place_on_back_right_corner(scene.AddAsset("a wooden towel ladder with a white towel",
                                                       asset_id=LADDER))

    if PHASE >= 3:
        # Walls & decor: the vanity is a complete SET that already includes its own wall mirror, so
        # we DON'T add separate mirrors (they overlapped it). ONE botanical print, on the right wall
        # only — the left wall is full (shower + toilet), so no art there.
        room.place_on_wall_right_center(scene.AddAsset("a framed botanical wall art print"))
        # Openings: the window over the tub (the door is already placed, in phase 1).
        room.place_window_standard("back_wall", position="center",
                                   curtain="sheer white curtains")

scene.export("bathroom_v1.blend")
