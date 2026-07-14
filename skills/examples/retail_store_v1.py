"""Retail store — "Branded Focal Wall with Layered Boutique Flow" (planner headline).

Planner target: a modern apparel/clothing boutique. A BRANDED FOCAL WALL at the back with the
checkout/cash-wrap in front of it (the back-of-house service zone); a CENTRAL MERCHANDISING SPINE
down the middle — two rack ROWS of garment rails flanking a low display table — that guides the eye
and preserves open sightlines; PERIMETER MERCHANDISING along the side walls (wall shelf + shoe
display + a framed clothing rack + a fitting mirror); and a FRONT-WINDOW MANNEQUIN DISPLAY facing
the storefront. Varied display heights (floor mannequins, mid-height rails, low tables) build depth.
Palette (plan + dataset strengths): warm-gray / light beige walls, concrete-look floor, matte-black
metal fixtures with warm wood tops, one warm accent via clothing colour.

Layout — CENTRAL SPINE + PERIMETER LOOP (the reusable shop/showroom pattern):
- BACK wall  : the SERVICE wall. Cash-wrap at back-centre facing="front" (a counter turned into the
               store is what makes it read as a cash-wrap, not a desk); the glass accessory showcase
               beside it at back-left. The brand sign hangs above them — the back wall is the only
               wall allowed to be "about" the brand.
- LEFT wall  : perimeter merch, HUNG (bottom=0.4): the folded-clothes/hanging-rod shelf at centre,
               the shoe display at left. facing="right" turns them into the room.
- RIGHT wall : perimeter merch, FLOOR-STANDING: the framed boutique rack at centre and the
               full-length fitting mirror at right. facing="left" turns them into the room. The door
               also lives here (right), so the mirror doubles as the fitting-corner marker.
- CENTRE     : the SPINE — two rack rows (2 rails each) at place_on_left / place_on_right with
               facing="left", which runs each long rail FRONT-TO-BACK so the two rows are parallel
               and frame an aisle; the main display table sits in the aisle at place_on_center. A
               second folded-clothes table is set back at back-left. The back row and back-right are
               deliberately left OPEN so the fuller merch still reads airy (feedback #1).
- FRONT      : the WINDOW DISPLAY — three mannequins across front_left / front / front_right, all
               facing="front", staged in front of a standard pane. NEVER floor-to-ceiling glaze the
               storefront: a wall-sized window renders as a pure-black void with no exterior env.

Identity comes from the massed CLOTHING, not from any one hero: four double-sided rails of hanging
garments down the spine, folded stacks on two tables, a wall of folded/hanging merch, shoes, and
three dressed mannequins. Strip the merch and this is an empty concrete box. RAIL_H=0.7 keeps the
rails at boutique height — at full height they tower over the mannequins and the room reads
warehouse.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/retail_store_v1.py --phase 1` builds
only the floor layout (~1-2 min); phase 2 dresses the surfaces (on-top stacks, rug, plant); phase 3
adds the brand sign, the storefront window and the lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

# --- pinned hero pieces (settled in the asset-first kickoff + retrieval stress test) ---
SPINE_RAIL   = "future/a419b5a4-4bfe-4e04-a3f3-7c7e3e9fcd17"      # double-sided freestanding garment rail
                                                                  # — the VLM's #1 for "clothing rail" is
                                                                  # usually a coat VALET; this true two-arm
                                                                  # rack was #4
FRAMED_RACK  = "future/a3e8bf5a-c3dd-4211-bdda-483818d9d354"      # black-framed boutique clothing rack (perimeter)
WALL_MERCH   = "hssd/76ae9b47590b35c68e8ab908e4641d523f083b0c"    # wall shelf: folded clothes on top + hanging rod below
SHOE_SHELF   = "hssd/e9597e32600022ebbae20264d1fed4b7d6b89b37"    # white shelf displaying pairs of shoes
COUNTER      = "hssd/7379d8877fb6d9f4f83e0b0207b44746d23a1860"    # curved wood-front reception/cash-wrap counter — the
                                                                  # dataset has NO purpose-built cash-wrap; a reception
                                                                  # desk reads as one once the POS + bags are on top
MANNEQUIN    = "hssd/852f2364cdc28fde3b302da61a8d2e09d3d18a15"    # full-body standing clothing mannequin
DISPLAY_TABLE= "hssd/e7b5486297f2cfdaf1f4398fac6e425913f3124f"    # low wood-top + black-metal-frame display table (on-brand)
FOLDED       = "future/c17aa2e4-30f4-482a-badc-1c04309e487b"      # stack of neatly folded sweaters (on-top prop)
SHOWCASE     = "hssd/be0ea104f86eedb2424627de3e52a32af8d19c02"    # oak/glass display showcase cabinet (accessories)

scene = SceneProgRoom("RetailStore", seed=42)

RAIL_H = 0.7   # #4: rails rendered too tall — knock every rail down to 0.7 of its height


def rail():
    """A double-sided garment rail scaled to a shorter, boutique-height stand (#4)."""
    r = scene.AddAsset("a double-sided clothing display rail with hanging clothes", asset_id=SPINE_RAIL)
    r.scale_only_height(r.get_height() * RAIL_H)
    return r


def display_table(extra=None, rug=False):
    """A low display table with folded-clothes stacks shown on top (optional grounding rug).

    The stacks and the rug are the PHASE-2 dressing layer; the table itself is a phase-1 anchor.
    """
    with scene.RelativeGroup() as t:
        t.set_anchor(scene.AddAsset("a low wooden merchandise display table with a black metal frame",
                                    asset_id=DISPLAY_TABLE))
        if PHASE >= 2:
            stacks = [scene.AddAsset("a stack of folded sweaters", asset_id=FOLDED),
                      scene.AddAsset("a stack of folded shirts in muted colours")]
            if extra:
                stacks.append(scene.AddAsset(extra))
            t.place_on_top(stacks)
            if rug:
                t.place_rug("a large flat neutral wool area rug", size=0.9)
    return t


# --- checkout / cash-wrap: counter with a POS terminal + shopping bags on top (service zone) ---
pos = None   # the POS terminal only exists from phase 2 — feedback #2's rotate is gated with it
with scene.RelativeGroup() as checkout:
    checkout.set_anchor(scene.AddAsset("a modern retail store checkout counter service desk", asset_id=COUNTER))
    if PHASE >= 2:
        pos = scene.AddAsset("a point of sale touchscreen terminal")
        checkout.place_on_top([pos, scene.AddAsset("a paper retail shopping bag")])

# --- central spine: main display table (with a grounding rug) + a second folded-clothes table (#5) ---
table  = display_table(extra="a stack of folded blue jeans", rug=True)
table2 = display_table()

# --- two rack ROWS, two rails each, framing the aisle (#5 more hanging clothing) ---
with scene.GridGroup(sparsity=0.35, randomness=0.05) as left_rack:
    left_rack.place_row([rail(), rail()])
with scene.GridGroup(sparsity=0.35, randomness=0.05) as right_rack:
    right_rack.place_row([rail(), rail()])

with scene.RoomGroup(modulate_scale=1.2, randomness=0.1) as room:   # #1 bigger footprint = more spacious
    room.place_walls(floor_texture="polished concrete floor",
                     ceiling_texture="white", wall_texture="warm light greige")

    # Service wall: checkout on the brand wall, glass accessory showcase beside it.
    room.place_on_back_wall_center(checkout, facing="front")          # cash-wrap faces into the store
    room.place_on_back_wall_left(scene.AddAsset("an oak and glass display showcase cabinet", asset_id=SHOWCASE), facing="front")

    # Central merchandising: two rack rows (facing="left" runs them front-to-back, parallel) framing
    # the display table; a second folded-clothes table set back on the left. Back row kept OPEN (#1).
    room.place_on_left(left_rack, facing="left")
    room.place_on_center(table)
    room.place_on_right(right_rack, facing="left")
    room.place_on_back_left(table2)

    # Front-window display: three mannequins facing the storefront.
    room.place_on_front_left(scene.AddAsset("a full-body standing clothing mannequin", asset_id=MANNEQUIN), facing="front")
    room.place_on_front(scene.AddAsset("a full-body standing clothing mannequin", asset_id=MANNEQUIN), facing="front")
    room.place_on_front_right(scene.AddAsset("a full-body standing clothing mannequin", asset_id=MANNEQUIN), facing="front")

    # Perimeter merch (place_on_*_wall_* now clamps these to the wall span + ceiling — #3).
    room.place_on_left_wall_center(scene.AddAsset("a wall-mounted retail shelf with folded clothes and a hanging rod",
                                                  asset_id=WALL_MERCH), facing="right", bottom=0.4)
    room.place_on_left_wall_left(scene.AddAsset("a wall shoe display shelf", asset_id=SHOE_SHELF), facing="right", bottom=0.4)
    room.place_on_right_wall_center(scene.AddAsset("a black-framed boutique clothing rack with hanging garments", asset_id=FRAMED_RACK), facing="left")
    room.place_on_right_wall_right(scene.AddAsset("a full-length freestanding floor mirror"), facing="left")

    # door in PHASE 1: its auto clearance shapes the floor solve
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        room.place_on_back_right_corner(scene.AddAsset("a large potted indoor plant in a modern planter"))
        room.rotate(pos, 180)   # #2: turn the checkout screen back to face the approaching customer

    if PHASE >= 3:
        # Brand focal wall + storefront glazing + light.
        room.place_on_wall_back_center(scene.AddAsset("a neon store brand sign with glowing tube lettering"))
        room.place_window_standard("front_wall", position="center")     # storefront pane (full-height = black void)
        # `add_lighting` must be a FLAT/FLUSH fixture (a hanging/track rig blows out — see
        # skills/examples/executive_office.md). Density scales with FLOOR AREA, so the bigger room
        # drops to 0.06.
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.06)

scene.export("retail_store_v1.blend")
