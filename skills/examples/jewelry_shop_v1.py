"""Jewelry shop — "Luxe Jewelry Boutique" (v3 rebuild, on the real ShopFixtureRetriever fixtures).

Planner target: a gallery-spine fine-jewelry boutique — a showroom of glass-topped display banks, a
branded service wall behind a consultation cash-wrap, a featured centrepiece, a discreet lounge nook,
greenery, a storefront window display. Palette: warm walnut + glass + brass, black-velvet displays,
sapphire/emerald velvet accents; polished-stone floor, greige walls.

Layout — RETAIL SPINE + PERIMETER LOOP + BRANDED SERVICE WALL (the shop recipe from retail_store),
with the perimeter loop made of LOW jewelry counters, which is the whole trick:
- BACK wall  : the SERVICE / BRAND wall. Cash-wrap centred under the ornate gold focal mirror, a
               jewelry counter flanking it each side. The wall you look at from the door, so it is
               the wall that gets the branding.
- LEFT wall  : showroom run — two jewelry counters facing the aisle, plus the full-length floor
               mirror at the far end (a jewelry shop needs a mirror you can try a piece in front of).
               The neon brand sign hangs here because the back wall is already spoken for.
- RIGHT wall : showroom run — two more jewelry counters facing the aisle. The door lives here, at
               the front end, so the shopper enters INTO the loop rather than into a fixture.
- CENTRE     : the FEATURED table — a low table massed with necklace busts / ring cube / cushion on
               a cream rug. Low, so it is a display island and not a sightline blocker.
- FRONT      : the storefront. The window pane at centre, and two marble pedestals with necklace
               busts turned to FACE THE SHOPPER (facing="back") — the window display, read from in.

Identity comes from the PRODUCT, not the fixtures. Six LOW walnut jewelry counters whose rings and
earrings are modelled INTO the glass top, massed around the perimeter, plus the velvet busts and the
ring cube at viewing height on the featured table / cash-wrap / pedestals. (v1's tall EMPTY glass
vitrines read as a furniture showroom and congested the floor; low product-laden counters can line
every wall without congesting.) That massing is `place_on_top`, so it lives in PHASE 2 — phase 2 is
the layer that names this room.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/jewelry_shop_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the surfaces (the visible jewelry, the rug, the
plant); phase 3 adds the wall decor, the storefront window and the lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("JewelryShop", seed=42)

# ---- purpose-built jewelry fixtures (new ShopFixtureRetriever / ingested customs) --------------
# Pinned by custom/<id> on purpose: the warm MCP `retrieve` cannot see a newly-added retriever class
# until a server restart (run_scene / workbench.py can), and pinning sidesteps routing entirely.
JCOUNTER = "custom/1028be7dddc5b7e1a0c4339582223f5d787400c3"   # walnut jewelry display counter w/ rings+earrings on a glass top (HERO, massed)
CASHWRAP = "custom/eedaa74ba03140b24a6629be7ce4be699bd96307"   # curved reception counter w/ integrated POS + glass jewelry section
NBUST3   = "custom/df9fc6e68ff291495a9fcf53945c3cda10e14e16"   # triple black-velvet necklace display bust (featured centrepiece)
NBUST1   = "custom/3add6d78d7bb91dc7f29c1b18c1a6449972f1fdc"   # single black-velvet bust w/ a gold chain necklace
RINGCUBE = "custom/dec1d5a87920cce3073622b19b6d2ad7737befdc"   # glass display cube w/ a diamond ring
CUSHION  = "custom/53ec24cbbfdeeef36447b4b3c575c6497827f38b"   # black-velvet cushion w/ a beaded necklace
# ---- supporting cast (pinned earlier) ---------------------------------------------------------
DISPLAY_TABLE = "hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f"   # low wood-top table (flat top for the featured busts)
STOOL         = "hssd/670c0caf8cb7df8466c675d7c91f7877840f9513"   # sapphire barstool w/ gold frame
ARMCHAIR      = "hssd/1672e0bc1abcdde2fd45c13b85d7bcf74f2f8236"   # emerald tufted velvet accent chair (pinned for palette)


def jcounter():
    """One walnut jewelry display counter — the low, product-laden hero, repeated around the room."""
    return scene.AddAsset("a glass-top jewelry display counter showcase with rings and earrings", asset_id=JCOUNTER)


def bust1():
    return scene.AddAsset("a black velvet necklace display bust with a gold chain", asset_id=NBUST1)


# ---- PHASE 1: cash-wrap — curved counter with an integrated POS + LOW jewelry pieces on top -----
# (native H=1.70m incl. the POS screen; trim 0.85 and keep only low props so it doesn't tower — VLM v3.)
with scene.RelativeGroup() as checkout:
    cw = scene.AddAsset("a curved reception checkout counter with an integrated POS", asset_id=CASHWRAP)
    cw.scale(cw.get_width() * 0.85)
    checkout.set_anchor(cw)                    # place_on_top seats items on the ANCHOR
    if PHASE >= 2:
        # the visible jewelry ON the counter — created INSIDE the gate so it never orphans
        checkout.place_on_top([scene.AddAsset("a glass jewelry display cube with a diamond ring", asset_id=RINGCUBE),
                               scene.AddAsset("a black velvet cushion with a beaded necklace", asset_id=CUSHION)])

# ---- PHASE 1: two consultation stools at the counter (customer side, facing the brand wall) -----
with scene.GridGroup(sparsity=0.4, randomness=0.05) as stools:
    stools.place_row([scene.AddAsset("an upholstered barstool with a gold frame", asset_id=STOOL),
                      scene.AddAsset("an upholstered barstool with a gold frame", asset_id=STOOL)])

# ---- PHASE 1: featured centrepiece — a low table; PHASE 2 masses the jewelry on it + the rug ----
with scene.RelativeGroup() as featured:
    featured.set_anchor(scene.AddAsset("a low wooden display table with a black metal frame", asset_id=DISPLAY_TABLE))
    if PHASE >= 2:
        featured.place_on_top([scene.AddAsset("a triple black velvet necklace display bust", asset_id=NBUST3),
                               bust1(),
                               scene.AddAsset("a glass jewelry display cube with a diamond ring", asset_id=RINGCUBE),
                               scene.AddAsset("a black velvet cushion with a beaded necklace", asset_id=CUSHION)])
        featured.place_rug("a large flat luxury cream area rug", size=0.9)

# ---- PHASE 1: emerald-velvet lounge nook (seating + its side table — a seat never travels alone) -
with scene.GridGroup(sparsity=0.5, randomness=0.05) as lounge:
    lounge.place_row([scene.AddAsset("an emerald velvet accent armchair", asset_id=ARMCHAIR),
                      scene.AddAsset("a small round wooden side table")])


def pedestal_bust():
    """A tall marble pedestal with a necklace bust on top (storefront display)."""
    with scene.RelativeGroup() as p:
        p.set_anchor(scene.AddAsset("a tall rectangular marble pedestal display stand"))
        if PHASE >= 2:
            p.place_on_top([bust1()])          # the product on the plinth — the window display's point
    return p


with scene.RoomGroup(modulate_scale=0.88, randomness=0.1) as room:   # settled: rescale votes now straddle 1.0
    # UNGATED: the shell has to exist in every phase. Polished stone + greige IS the luxe palette.
    room.place_walls(floor_texture="polished stone floor",
                     ceiling_texture="white", wall_texture="warm light greige")

    # PHASE 1 — service / brand wall (back): cash-wrap centred, a jewelry counter each side.
    room.place_on_back_wall_center(checkout, facing="front")
    room.place_on_back_wall_left(jcounter(), facing="front")
    room.place_on_back_wall_right(jcounter(), facing="front")

    # PHASE 1 — jewelry showroom: LOW display counters lining both side walls, facing the aisle
    # (low = no congestion; this is where v1's six TALL vitrines went wrong).
    room.place_on_left_wall_left(jcounter(), facing="right")
    room.place_on_left_wall_center(jcounter(), facing="right")
    room.place_on_left_wall_right(scene.AddAsset("a full-length freestanding floor mirror"), facing="right")
    room.place_on_right_wall_left(jcounter(), facing="left")
    room.place_on_right_wall_center(jcounter(), facing="left")

    # PHASE 1 — interior: stools at the counter, the featured bust table centre, lounge back-left.
    room.place_on_back(stools, facing="back")
    room.place_on_center(featured)
    room.place_on_back_left(lounge, facing="front")

    # PHASE 1 — front display: two marble pedestals, turned to face the shopper (VLM 180).
    room.place_on_front_left(pedestal_bust(), facing="back")
    room.place_on_front_right(pedestal_bust(), facing="back")

    # UNGATED: the door's automatic clearance shapes the floor solve, so deferring it to phase 3
    # would change the layout phase 1 is supposed to validate.
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        # the greenery — floor detail, created inside its gate
        room.place_on_back_right(scene.AddAsset("a large potted indoor plant in a modern planter"))

    if PHASE >= 3:
        # wall decor: the ornate focal mirror over the cash-wrap; the neon brand sign on the left wall.
        room.place_on_wall_back_center(scene.AddAsset("an ornate gold-framed wall mirror"))
        room.place_on_wall_left_center(scene.AddAsset("a neon store brand sign with glowing tube lettering"))
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.06)   # medium room
        room.place_window_standard("front_wall", position="center")   # storefront pane (full-height = black void)

scene.export("jewelry_shop_v1.blend")
