"""
Bathroom — "Marble & Brass Spa Bath". White marble grounded with warm WOOD + brass; spa master bath.
Design brief (from the planner): luminous white marble warmed by brass hardware and natural wood; the
freestanding oval tub anchors the room under a big window with a statement brass chandelier over the
soak zone; a walk-in glass shower is the open counterpoint; a warm-wood double vanity with marble top
+ two brass-framed mirrors is the grooming zone; lush ferns/eucalyptus, candles and plush towels add
the spa ritual.

Coarse-to-fine (skills/workflow/coarse_to_fine.md):
  Phase 1 — major assets / proportions: the two HEROES (tub, vanity) face each other on the two LONG
    walls so each gets a generous wall; shower + toilet take the SHORT walls.
      - back  (long) : freestanding soaking tub HERO, under a window, brass chandelier over it.
      - front (long) : warm-wood double vanity (marble top), two brass mirrors above.
      - left  (short): walk-in glass shower + wall-hung toilet.
      - right (short): door + tall linen tower.
  Phase 2 — surface & floor details: vanity-top towels/soap/eucalyptus; bath caddy across the tub,
    a fern + a candle cluster beside it; corner palm; towel ladder; a woven jute bath mat.
  Phase 3 — walls & decor: two brass-framed mirrors + botanical art, the window + sheer shade, door.

NOTE: several bathroom fixtures carry broken real-world `scale` metadata (the pinned tub resolves to
0.2 m long!). We enforce realistic dimensions up front with `_dims` before building any group, so the
fixtures read at true size and their on-top / beside items are positioned against the right footprint.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("BathroomSpa", seed=21)

def _fit_width(o, target_w):
    """Scale an asset UNIFORMLY so its width == target_w — keeps the mesh's own proportions intact
    (the right way to fix bad scale metadata without distorting the geometry)."""
    w0, h0, d0 = o.get_width(), o.get_height(), o.get_depth()
    f = target_w / max(w0, 1e-6)
    o.scale_only_width(w0 * f); o.scale_only_height(h0 * f); o.scale_only_depth(d0 * f)
    return o

def _dims(o, w=None, h=None, d=None):
    """Force per-axis real-world dims — only for assets whose mesh proportions are genuinely wrong
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
    "a tall brass-framed wall mirror",
    "a brass drum chandelier",
    "a tall potted areca palm plant",
    "a lush potted fern in a white pot",
    "a eucalyptus stem arrangement in a white vase",
    "a wooden bathtub caddy tray",
    "a cluster of white spa pillar candles",
    "a brass soap dispenser and tray set",
    "a stack of rolled white bath towels",
    "a framed botanical wall art print",
])

# --- Phase 1 fixtures, sized to real-world dimensions (metadata scale is unreliable) ---
tub_asset = scene.AddAsset("a sleek white freestanding oval soaking bathtub",
                           asset_id="hssd/4106160be8e18d73aa704da0ed993aed8175b4d4")
# proportions are fine (0.20:0.10:0.06 ≈ real tub); scale uniformly so it's 1.6 m long.
_fit_width(tub_asset, 1.6)
# AddAsset auto-sizes any tagged vanity to its real width + records its mount (see SceneProgRoom).
# A 'double' -> 1.5 m wide, floor-mounted; a 'floating' would auto-narrow AND wall-mount, no extra code.
vanity_asset = scene.AddAsset("a modern wood double bathroom vanity with marble top and two sinks",
                              asset_id="hssd/44a88da97b60a73257237b8bfe6e87dbfe1106c8")
# toilet meshes often bundle a TP roll / brush / cistern into one bbox, so the real seat reads small;
# scale up uniformly (~1.5x its 0.4 m metadata width) so the seat itself looks right, undistorted.
toilet = _fit_width(scene.AddAsset("a modern white wall-hung toilet"), 0.90)
shower = _dims(scene.AddAsset("a walk-in glass shower enclosure"), w=1.0, h=2.0, d=0.9)
linen  = _dims(scene.AddAsset("a tall narrow bathroom linen cabinet with baskets"), h=1.9)

# NOTE: we deliberately DON'T place_on_top of the vanity — it's a complete set with a complex top
# (sinks/faucets), so stacked decor sits unreliably. If counter decor is wanted, retrieve a vanity
# variant that already bundles small items instead. The vanity is placed directly on its wall below.

# --- Phase 2 cluster: the hero freestanding tub — caddy across it, fern + candles beside, chandelier ---
with scene.RelativeGroup() as tub:
    tub.set_anchor(tub_asset)
    tub.place_on_top(scene.AddAsset("a wooden bathtub caddy tray",
                                    asset_id="hssd/c758aecbc16adc68977ef9f77c34adee2acd7b7d"))
    tub.place_on_left(scene.AddAsset("a lush potted fern in a white pot"))
    tub.place_on_right(scene.AddAsset("a cluster of white spa pillar candles"))
    # pin a verified-FLAT bath mat — many "bath mat" picks are modelled upright (thin in depth) and
    # blow up in height through place_rug, which can't lay them flat (yaw-only pipeline).
    tub.place_rug("a simple rectangular bath mat", size=0.8,
                  asset_id="hssd/a63f792f89c348735c6a4a2208e3881a869f68e6")
    tub.add_lighting("a brass drum chandelier", density=0)

with scene.RoomGroup(modulate_scale=0.72, randomness=0.1) as room:
    # warm the surfaces so the all-marble room doesn't blow out to white (and to ground it per the
    # brief): travertine floor + greige marble walls keep tonal range while staying light & luxe.
    # mid-tone sage walls (the brief's "pale sage accent") + grey marble floor keep the room from
    # blowing out to white — same trick as the salon's blush walls (a saturated mid-tone reads, an
    # all-marble white room inter-reflects daylight into a white-out).
    room.place_walls(floor_texture="honed grey marble tiles",
                     ceiling_texture="white", wall_texture="soft sage green")
    # Phase 1 — the two heroes on the two long walls, facing each other
    room.place_on_back_wall_center(tub)                                            # tub under the window
    room.place_on_front_wall_center(vanity_asset)                                   # vanity set (auto floor/floating)
    # Phase 1 — short walls: the wet zone + storage
    room.place_on_left_wall_left(shower)
    room.place_on_left_wall_right(toilet)
    room.place_on_right_wall_center(linen)
    # Phase 2 — floor: corner greenery + towel ladder (the jute mat rides with the tub group)
    room.place_on_back_left_corner(scene.AddAsset("a tall potted areca palm plant"))
    room.place_on_back_right_corner(scene.AddAsset("a wooden towel ladder with a white towel",
                                                   asset_id="hssd/f63203ce3955e3df53c4e59d9e73f9fff3a6c351"))
    # Phase 3 — walls & decor: the vanity is a complete SET that already includes its own wall
    # mirror, so we DON'T add separate mirrors (they overlapped it). One botanical print on the
    # right wall only — the left wall is full (shower + toilet), so no art there.
    room.place_on_wall_right_center(scene.AddAsset("a framed botanical wall art print"))
    # Phase 3 — openings: window over the tub, door on the storage wall
    room.place_window_standard("back_wall", position="center", curtain="sheer white curtains")
    room.place_door("right_wall", position="right")

scene.export("bathroom.blend")
