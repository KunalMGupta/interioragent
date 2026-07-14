"""
Flower shop — "Sun-Kissed Florist" (planner target, tmp/plan_a_charming_flower_shop___florist/plan.png).

A charming florist boutique. Warm-wood + cream + brass palette, blush/green blooms everywhere.
Retrieval stress-tested first (scenes/notes/florist_shop.md): the dataset is RICH in vase-bouquet
arrangements (tulips/ranunculus/peonies/roses) but has NO galvanized-bucket-of-loose-stems mesh, so
the florist read is built by MASSING vase-bouquets densely on tiered stands, plinths and a display
table — that clustering reads as a flower shop's stock without the (missing) buckets.

Zoning (front wall = storefront; room auto-sizes to fit):
  - back (service) wall = the WRAPPING/CHECKOUT COUNTER (hub) flanked by two potted trees; sun art above.
  - left (display) wall = a glass display cabinet (blooms inside + on top) + a bloom table + a tall plant.
  - right (display) wall = two bloom tables + the entry door (front slot) + a round mirror.
  - front (storefront) wall = a floor-to-ceiling shop window; two bloom tables fill the display bay.
  - centre = the hero DISPLAY TABLE massed with bouquets (open circulation around it + the counter).

Reusable idea: a "bloom table" = a rustic display table with a LIST of bouquets dropped via
place_on_top (which distributes the list along the surface, VLM tournament), so N * variety reads as
a brimming florist display from one call. Six of these massed around the shop = the florist read
(the dataset has no galvanized-bucket-of-loose-stems mesh; dense vase-bouquets stand in for it).

LESSONS (v1 -> v2 -> v3):
  1. AVOID the black-wire "tiered plant stand" (9ae7a2c2...): it renders as a GIANT glossy-black
     étagère, scaled huge; place_on_top fits its bouquets to that width -> giant tulips, and it fills
     the right-wall camera so wall_right.png comes out pure black. Use low matching display tables.
  2. A small round plinth (cbc857cb...) dwarfs its blooms; the "wooden wall shelf" (770eae5e...) ships
     with BOOKS baked in (wrong for a florist). Both dropped.
  3. A floor-to-ceiling storefront window occupies ALL THREE front-wall slots -> the door must go on a
     SIDE wall. Its unlit exterior renders BLACK (expected). A wall_*.png that is all-black is a camera
     artifact when that wall carries the window/door (cam shoots through the glass) -> verify via a
     corner_* view, not the flat wall view.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("FlowerShop", seed=48)

# --- pinned assets (audited previews; retrieval stress test in scenes/notes/florist_shop.md) ---
# blooms: vase-bouquet arrangements (the dataset's strength — mass them for the florist read)
_BLOOMS = [
    "hssd/69930e5f83e7d839142b15ca089f2a2ea90f6e1f",  # colorful tulips, green vase
    "hssd/e731fbf018152a31b13eb29c1f97081695e2ddfe",  # ranunculus + roses, white vase
    "hssd/53317cc22d22eeb608e3cad7d45aa9c9153ed17b",  # peonies + roses, flared vase
    "hssd/232e1b606f846a1f300acc9d6f4a5daddfaec0af",  # roses + hydrangeas, white vase
    "hssd/997ce68fa0cfdb85d563ae16162ae96ccd99b29f",  # mixed tulips, white vase
    "hssd/aac9ddbfb7a26260f0fedcf12110b61fa0d042de",  # pink + purple arrangement
]
_BUNDLE  = "hssd/0f26b905fee27370294875f1868203002d90f8f3"        # red rose bundle (wrapped, no vase)
_COUNTER = "hssd/7499145eb110f57094d4715bdca49edafc680ff6"        # traditional wooden counter
_CABINET = "hssd/d3fd1b00ebe22586ca981e3107a0b1f70d6d41c2"        # warm oak glass display cabinet
_TABLE   = "hssd/f72c0e86085c6b6f48b82d47d5066248be8b7c4a"        # rustic wooden console/display table
_TREE    = "future/82d06f8e-c9d0-40dd-852b-59524ab16225"          # tall leafy potted plant
_OLIVE   = "hssd/9d6f7ffc13419fcf23d54f272a6ef3f87684e53b"        # potted olive tree
_FERN    = "future/244c96f3-85b0-44f7-b8f8-bca659e87c92"          # tall potted fern
_POS     = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"        # point-of-sale terminal
_SUN     = "hssd/b93304c78146fa3a7ed3afbd99c7a2ce7f8962a8"        # sunburst metal wall art
_MIRROR  = "hssd/5ee88522c5f6f1723c413f3ba4b485602d3ed861"        # round decorative wall mirror

_bloom_i = [0]
def bouquet():
    """A fresh bouquet, rotating through the pinned variety so each cluster is mixed."""
    aid = _BLOOMS[_bloom_i[0] % len(_BLOOMS)]
    _bloom_i[0] += 1
    return scene.AddAsset("a vase of fresh cut flowers", asset_id=aid)

# --- HERO: a central display table brimming with bouquets ---
# A bloom-massed DISPLAY TABLE, built once and reused around the shop. A rustic console with 3-4
# bouquets dropped via place_on_top (which distributes the list along the top). Controlled scale —
# v1's tall black wire "tiered stand" rendered as a giant glossy-black étagère that dwarfed its
# bouquets and blacked out the right-wall camera; low matching tables read as a florist and behave.
def bloom_table(n=3):
    with scene.RelativeGroup() as t:
        t.set_anchor(scene.AddAsset("a rustic wooden display table", asset_id=_TABLE))
        t.place_on_top([bouquet() for _ in range(n)])
    return t
center_display = bloom_table(5)   # the hero, in the middle
left_display   = bloom_table(4)   # against the left wall
right_display  = bloom_table(4)   # against the right wall
window_display = bloom_table(4)   # the storefront window display
bay_display    = bloom_table(4)   # a second table in the storefront bay
side_display   = bloom_table(4)   # a second table filling the right wall

# --- glass display cabinet with premium bouquets shown INSIDE it ---
with scene.RelativeGroup() as cabinet:
    cabinet.set_anchor(scene.AddAsset("a glass display cabinet", asset_id=_CABINET))
    cabinet.place_inside([bouquet(), bouquet(), bouquet()])

# --- the wrapping / checkout counter (service hub): POS + a wrapped bundle on top ---
with scene.RelativeGroup() as counter:
    counter.set_anchor(scene.AddAsset("a wooden shop checkout counter", asset_id=_COUNTER))
    counter.place_on_top([scene.AddAsset("a point of sale terminal", asset_id=_POS),
                          scene.AddAsset("a bundle of wrapped cut roses", asset_id=_BUNDLE)])

with scene.RoomGroup(modulate_scale=1.0, randomness=0.1) as room:
    room.place_walls(floor_texture="warm honey oak wood plank flooring",
                     ceiling_texture="warm white",
                     wall_texture="soft cream plaster")
    # NOTE on facing: omit facing on place_on_<wall>_* — the heuristic already faces each asset
    # INTO the room (counter/cabinet access side toward customers). Only override deliberately.
    # back (service) wall = the counter hub, flanked by two potted trees (lush framing)
    room.place_on_back_wall_center(counter)
    room.place_on_back_left_corner(scene.AddAsset("a potted olive tree", asset_id=_OLIVE))
    room.place_on_back_right_corner(scene.AddAsset("a tall potted fern", asset_id=_FERN))
    # left (display) wall = glass cabinet (center) + a bloom table (left) + a tall plant (right)
    room.place_on_left_wall_center(cabinet)
    room.place_on_left_wall_left(left_display)
    room.place_on_left_wall_right(scene.AddAsset("a tall leafy potted plant", asset_id=_TREE))
    # right (display) wall = two bloom tables (center + right); the entry door tucks into its front slot
    room.place_on_right_wall_center(right_display)
    room.place_on_right_wall_right(side_display)
    room.place_door("right_wall", position="left")
    # centre = the hero display table of blooms (open circulation rings it + the counter)
    room.place_on_center(center_display)
    # front (storefront) wall = a floor-to-ceiling shop window; two bloom tables fill the display bay
    room.place_window_floor_to_ceiling("front_wall")
    room.place_on_front_left(window_display)
    room.place_on_front(bay_display)
    # walls & decor: sunburst art over the counter; a round mirror on the right wall
    room.place_on_wall_back_center(scene.AddAsset("a decorative sunburst wall art", asset_id=_SUN))
    room.place_on_wall_right_center(scene.AddAsset("a round decorative wall mirror", asset_id=_MIRROR))
    # ceiling = warm recessed downlights (even, glare-free boutique wash)
    room.add_lighting("a recessed ceiling downlight", density=0.12)

scene.export("florist_shop.blend")
