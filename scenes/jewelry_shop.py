"""
Jewelry shop — "Luxe Jewelry Boutique" (rebuilt on the new ShopFixtureRetriever assets).

v3 REBUILD (2026-07-10): Kunal added a `ShopFixtureRetriever` + ingested purpose-built retail
meshes, including REAL jewelry fixtures. That dissolves the whole earlier workaround (empty glass
vitrines + improvised geode/agate/cloche props that only *approximated* jewelry). Now the shop is
built from actual jewelry furniture whose PRODUCT is modelled into the mesh:
  - a walnut JEWELRY DISPLAY COUNTER (custom/1028be7d…) — glass top with rings/earrings on it and a
    branded back panel; massed around the room = an instant, legible jewelry showroom.
  - a curved CASH-WRAP with an integrated POS + glass jewelry section (custom/eedaa74b…).
  - black-velvet NECKLACE BUSTS with gold chains (single custom/3add6d78…, triple custom/df9fc6e6…),
    a glass RING-DISPLAY CUBE (custom/dec1d5a8…) and a velvet beaded CUSHION (custom/53ec24cb…) —
    the visible hero pieces, on the featured table + cash-wrap + window pedestals.

Carries forward the standing lessons: a shop reads by its PRODUCT at viewing height (now baked into
the fixtures); jewelry counters are LOW so many of them enrich without congesting (unlike the tall
wardrobe-vitrines that congested v1); pin the palette (emerald armchair); flush ceiling light, low
density; storefront window = standard pane (full-height = black void). Assets pinned by custom/<id>
(reliable; the warm MCP retrieve can't see the new retriever until a restart, but run_scene can, and
pinning sidesteps routing entirely).

Palette: warm walnut + glass + brass, black-velvet displays, sapphire/emerald velvet accents;
polished-stone floor, greige walls.
"""
from IDSDL.scene import SceneProgRoom

# --- purpose-built jewelry fixtures (new ShopFixtureRetriever / ingested customs) ---
JCOUNTER = "custom/1028be7dddc5b7e1a0c4339582223f5d787400c3"   # walnut jewelry display counter w/ rings+earrings on a glass top (HERO, massed)
CASHWRAP = "custom/eedaa74ba03140b24a6629be7ce4be699bd96307"   # curved reception counter w/ integrated POS + glass jewelry section
NBUST3   = "custom/df9fc6e68ff291495a9fcf53945c3cda10e14e16"   # triple black-velvet necklace display bust (featured centrepiece)
NBUST1   = "custom/3add6d78d7bb91dc7f29c1b18c1a6449972f1fdc"   # single black-velvet bust w/ a gold chain necklace
RINGCUBE = "custom/dec1d5a87920cce3073622b19b6d2ad7737befdc"   # glass display cube w/ a diamond ring
CUSHION  = "custom/53ec24cbbfdeeef36447b4b3c575c6497827f38b"   # black-velvet cushion w/ a beaded necklace
# --- supporting cast (pinned earlier) ---
DISPLAY_TABLE = "hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f"   # low wood-top table (flat top for the featured busts)
STOOL         = "hssd/670c0caf8cb7df8466c675d7c91f7877840f9513"   # sapphire barstool w/ gold frame
ARMCHAIR      = "hssd/1672e0bc1abcdde2fd45c13b85d7bcf74f2f8236"   # emerald tufted velvet accent chair (pinned for palette)

scene = SceneProgRoom("JewelryShop", seed=42)


def jcounter():
    """One walnut jewelry display counter — the low, product-laden hero, repeated around the room."""
    return scene.AddAsset("a glass-top jewelry display counter showcase with rings and earrings", asset_id=JCOUNTER)


def bust1():
    return scene.AddAsset("a black velvet necklace display bust with a gold chain", asset_id=NBUST1)


# --- cash-wrap: curved counter with integrated POS + LOW jewelry pieces on top ---
# (native H=1.70m incl. the POS screen; trim 0.85 and keep only low props so it doesn't tower — VLM v3.)
with scene.RelativeGroup() as checkout:
    cw = scene.AddAsset("a curved reception checkout counter with an integrated POS", asset_id=CASHWRAP)
    cw.scale(cw.get_width() * 0.85)
    checkout.set_anchor(cw)
    checkout.place_on_top([scene.AddAsset("a glass jewelry display cube with a diamond ring", asset_id=RINGCUBE),
                           scene.AddAsset("a black velvet cushion with a beaded necklace", asset_id=CUSHION)])

# two consultation stools at the counter (customer side, facing the brand wall)
with scene.GridGroup(sparsity=0.4, randomness=0.05) as stools:
    stools.place_row([scene.AddAsset("an upholstered barstool with a gold frame", asset_id=STOOL),
                      scene.AddAsset("an upholstered barstool with a gold frame", asset_id=STOOL)])

# --- featured centrepiece: a low table with the triple necklace bust + a single bust + ring cube + cushion, on a rug ---
with scene.RelativeGroup() as featured:
    featured.set_anchor(scene.AddAsset("a low wooden display table with a black metal frame", asset_id=DISPLAY_TABLE))
    featured.place_on_top([scene.AddAsset("a triple black velvet necklace display bust", asset_id=NBUST3),
                           bust1(),
                           scene.AddAsset("a glass jewelry display cube with a diamond ring", asset_id=RINGCUBE),
                           scene.AddAsset("a black velvet cushion with a beaded necklace", asset_id=CUSHION)])
    featured.place_rug("a large flat luxury cream area rug", size=0.9)

# --- emerald-velvet lounge nook (seating + its side table) ---
with scene.GridGroup(sparsity=0.5, randomness=0.05) as lounge:
    lounge.place_row([scene.AddAsset("an emerald velvet accent armchair", asset_id=ARMCHAIR),
                      scene.AddAsset("a small round wooden side table")])


def pedestal_bust():
    """A tall marble pedestal with a necklace bust on top (storefront display)."""
    with scene.RelativeGroup() as p:
        p.set_anchor(scene.AddAsset("a tall rectangular marble pedestal display stand"))
        p.place_on_top([bust1()])
    return p


with scene.RoomGroup(modulate_scale=0.88, randomness=0.1) as room:   # settled: rescale votes now straddle 1.0
    room.place_walls(floor_texture="polished stone floor",
                     ceiling_texture="white", wall_texture="warm light greige")

    # Service / brand wall (back): cash-wrap centred under the ornate focal mirror, a jewelry counter each side.
    room.place_on_back_wall_center(checkout, facing="front")
    room.place_on_back_wall_left(jcounter(), facing="front")
    room.place_on_back_wall_right(jcounter(), facing="front")
    room.place_on_wall_back_center(scene.AddAsset("an ornate gold-framed wall mirror"))

    # Jewelry showroom: LOW display counters lining both side walls, facing the aisle (low = no congestion).
    room.place_on_left_wall_left(jcounter(), facing="right")
    room.place_on_left_wall_center(jcounter(), facing="right")
    room.place_on_left_wall_right(scene.AddAsset("a full-length freestanding floor mirror"), facing="right")
    room.place_on_right_wall_left(jcounter(), facing="left")
    room.place_on_right_wall_center(jcounter(), facing="left")

    # Interior: stools at the counter, the featured bust table centre, lounge + plant in back corners.
    room.place_on_back(stools, facing="back")
    room.place_on_center(featured)
    room.place_on_back_left(lounge, facing="front")
    room.place_on_back_right(scene.AddAsset("a large potted indoor plant in a modern planter"))

    # Front display: two marble pedestals with necklace busts, turned to face the shopper (VLM 180).
    room.place_on_front_left(pedestal_bust(), facing="back")
    room.place_on_front_right(pedestal_bust(), facing="back")

    # Brand sign, openings, light.
    room.place_on_wall_left_center(scene.AddAsset("a neon store brand sign with glowing tube lettering"))
    room.add_lighting("a flat round LED flush mount ceiling light", density=0.06)   # medium room
    room.place_window_standard("front_wall", position="center")   # storefront pane (full-height = black void)
    room.place_door("right_wall", position="right")

scene.export("jewelry_shop.blend")
