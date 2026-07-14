"""Flower shop — "Sun-Kissed Florist" (planner target,
tmp/plan_a_charming_flower_shop___florist/plan.png).

Planner target: a charming florist boutique. Warm-wood + cream + brass palette, blush/green blooms
everywhere. Retrieval was stress-tested FIRST (scenes/notes/florist_shop.md): the dataset is RICH in
vase-bouquet arrangements (tulips/ranunculus/peonies/roses) but has NO galvanized-bucket-of-loose-stems
mesh, so the florist read is built by MASSING vase-bouquets densely on repeated display tables — that
clustering reads as a flower shop's stock without the (missing) buckets.

Layout — zoned RETAIL BOX (front wall = storefront; room auto-sizes to fit):
- BACK wall  : the service zone — the WRAPPING/CHECKOUT COUNTER hub (POS + a wrapped bundle), flanked
               by two potted trees for lush framing; the sunburst "sun" art hangs above it.
- LEFT wall  : display — a glass display cabinet (blooms INSIDE it, or it reads bare) at center, a
               bloom table left, a tall plant right.
- RIGHT wall : display — two bloom tables (center + right); the entry DOOR takes the front slot,
               because the storefront window eats the whole front wall; a round mirror above.
- FRONT wall : the storefront — a floor-to-ceiling shop window occupying ALL THREE front slots; two
               bloom tables fill the display bay in front of it (floating front placements, fine for
               compact single items).
- CENTRE     : the hero bloom table, massed with 5 bouquets; open circulation rings it and the counter.

Identity comes from MASSING one abundant prop: a reusable "bloom table" = a rustic display table with
a LIST of bouquets dropped via place_on_top (which distributes the list along the surface). Six of them
(~25 bouquets) around the shop ARE the florist read — density is the design, not a single hero mesh.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/florist_shop_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 masses the bouquets on every surface (the identity layer); phase 3
adds the storefront window, wall decor and lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("FlowerShop", seed=48)

# ---- pinned assets (audited previews; retrieval stress test in scenes/notes/florist_shop.md) ----
# blooms: vase-bouquet arrangements (the dataset's strength — mass them for the florist read)
BLOOMS = [
    "hssd/69930e5f83e7d839142b15ca089f2a2ea90f6e1f",  # colorful tulips, green vase
    "hssd/e731fbf018152a31b13eb29c1f97081695e2ddfe",  # ranunculus + roses, white vase
    "hssd/53317cc22d22eeb608e3cad7d45aa9c9153ed17b",  # peonies + roses, flared vase
    "hssd/232e1b606f846a1f300acc9d6f4a5daddfaec0af",  # roses + hydrangeas, white vase
    "hssd/997ce68fa0cfdb85d563ae16162ae96ccd99b29f",  # mixed tulips, white vase
    "hssd/aac9ddbfb7a26260f0fedcf12110b61fa0d042de",  # pink + purple arrangement
]
BUNDLE  = "hssd/0f26b905fee27370294875f1868203002d90f8f3"        # red rose bundle (wrapped, no vase)
COUNTER = "hssd/7499145eb110f57094d4715bdca49edafc680ff6"        # traditional wooden counter
CABINET = "hssd/d3fd1b00ebe22586ca981e3107a0b1f70d6d41c2"        # warm oak glass display cabinet
TABLE   = "hssd/f72c0e86085c6b6f48b82d47d5066248be8b7c4a"        # rustic wooden console/display table
TREE    = "future/82d06f8e-c9d0-40dd-852b-59524ab16225"          # tall leafy potted plant
OLIVE   = "hssd/9d6f7ffc13419fcf23d54f272a6ef3f87684e53b"        # potted olive tree
FERN    = "future/244c96f3-85b0-44f7-b8f8-bca659e87c92"          # tall potted fern
POS     = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"        # point-of-sale terminal
SUN     = "hssd/b93304c78146fa3a7ed3afbd99c7a2ce7f8962a8"        # sunburst metal wall art
MIRROR  = "hssd/5ee88522c5f6f1723c413f3ba4b485602d3ed861"        # round decorative wall mirror
# DROPPED, and why (all retrieval traps, not layout bugs):
#   - the black-wire "tiered plant stand" (9ae7a2c2...) renders as a GIANT glossy-black étagère, scaled
#     huge; place_on_top fits its bouquets to that width -> giant tulips, and it fills the right-wall
#     camera so wall_right.png comes out pure black. Low matching display tables instead.
#   - a small round plinth (cbc857cb...) dwarfs its blooms; the "wooden wall shelf" (770eae5e...) ships
#     with BOOKS baked into the mesh (wrong for a florist).

_bloom_i = [0]
def bouquet():
    """A fresh bouquet, rotating through the pinned variety so each cluster is mixed."""
    aid = BLOOMS[_bloom_i[0] % len(BLOOMS)]
    _bloom_i[0] += 1
    return scene.AddAsset("a vase of fresh cut flowers", asset_id=aid)

# ---- the BLOOM TABLE: the composed unit that carries the whole identity ----
# A rustic console + a LIST of bouquets via place_on_top (the list is distributed along the top), built
# once and reused six times around the shop. The bouquets are the PRODUCT AT VIEWING HEIGHT — the
# identity layer — so they are gated at PHASE 2, INSIDE the group's `with` block. (A place_on_top gated
# outside the block never runs and the props are simply GONE.) Phase 1 gives the six bare tables: the
# floor layout you actually want to check first.
def bloom_table(n=3):
    with scene.RelativeGroup() as t:
        t.set_anchor(scene.AddAsset("a rustic wooden display table", asset_id=TABLE))
        if PHASE >= 2:
            t.place_on_top([bouquet() for _ in range(n)])
    return t
center_display = bloom_table(5)   # the hero, in the middle
left_display   = bloom_table(4)   # against the left wall
right_display  = bloom_table(4)   # against the right wall
window_display = bloom_table(4)   # the storefront window display
bay_display    = bloom_table(4)   # a second table in the storefront bay
side_display   = bloom_table(4)   # a second table filling the right wall

# ---- glass display cabinet with premium bouquets shown INSIDE it ----
# Fill glass furniture or it reads bare (its glass also picks up the mirror/sun-art reflections).
with scene.RelativeGroup() as cabinet:
    cabinet.set_anchor(scene.AddAsset("a glass display cabinet", asset_id=CABINET))
    if PHASE >= 2:
        cabinet.place_inside([bouquet(), bouquet(), bouquet()])

# ---- the wrapping / checkout counter (service hub): POS + a wrapped bundle on top ----
with scene.RelativeGroup() as counter:
    counter.set_anchor(scene.AddAsset("a wooden shop checkout counter", asset_id=COUNTER))
    if PHASE >= 2:
        counter.place_on_top([scene.AddAsset("a point of sale terminal", asset_id=POS),
                              scene.AddAsset("a bundle of wrapped cut roses", asset_id=BUNDLE)])

with scene.RoomGroup(modulate_scale=1.0, randomness=0.1) as room:
    room.place_walls(floor_texture="warm honey oak wood plank flooring",
                     ceiling_texture="warm white",
                     wall_texture="soft cream plaster")
    # NOTE on facing: omit facing on place_on_<wall>_* — the heuristic already faces each asset
    # INTO the room (counter/cabinet access side toward customers). Only override deliberately.
    # back (service) wall = the counter hub
    room.place_on_back_wall_center(counter)
    # left (display) wall = glass cabinet (center) + a bloom table (left)
    room.place_on_left_wall_center(cabinet)
    room.place_on_left_wall_left(left_display)
    # right (display) wall = two bloom tables (center + right); the entry door tucks into its front slot
    room.place_on_right_wall_center(right_display)
    room.place_on_right_wall_right(side_display)
    # the door in PHASE 1: the storefront window will eat all three FRONT slots, so the door must live
    # on a SIDE wall — and its auto clearance shapes the floor solve, so it is placed with the anchors.
    room.place_door("right_wall", position="left")
    # centre = the hero display table of blooms (open circulation rings it + the counter)
    room.place_on_center(center_display)
    # the storefront bay: two bloom tables in front of the (phase-3) shop window
    room.place_on_front_left(window_display)
    room.place_on_front(bay_display)

    if PHASE >= 2:
        # greenery: potted trees flanking the counter (lush framing) + a left-wall accent
        room.place_on_back_left_corner(scene.AddAsset("a potted olive tree", asset_id=OLIVE))
        room.place_on_back_right_corner(scene.AddAsset("a tall potted fern", asset_id=FERN))
        room.place_on_left_wall_right(scene.AddAsset("a tall leafy potted plant", asset_id=TREE))

    if PHASE >= 3:
        # front (storefront) wall = a floor-to-ceiling shop window. It occupies ALL THREE front-wall
        # slots. Its unlit exterior renders BLACK — expected: a wall_*.png that is entirely black is a
        # CAMERA ARTIFACT whenever that wall carries the window/door (the cam shoots through the glass).
        # Verify that wall from a corner_* view instead.
        room.place_window_floor_to_ceiling("front_wall")
        # walls & decor: sunburst art over the counter; a round mirror on the right wall
        room.place_on_wall_back_center(scene.AddAsset("a decorative sunburst wall art", asset_id=SUN))
        room.place_on_wall_right_center(scene.AddAsset("a round decorative wall mirror",
                                                       asset_id=MIRROR))
        # ceiling = warm recessed downlights (even, glare-free boutique wash)
        room.add_lighting("a recessed ceiling downlight", density=0.12)

scene.export("florist_shop_v1.blend")
