"""
Wall-art MESH CERTIFICATION probe.

Established by the two earlier rounds of this probe:
  * PLACEMENT IS CORRECT on all four walls (a control painting hangs face-out on back/front/left/right)
    -- after the two core fixes to place_on_wall_freeform (wall plane + along-wall sizing).
  * Some dataset canvases are DUDS regardless of the wall: they hang as an EMPTY FRAME or a BLACK
    PANEL because their canvas material does not survive export.
        hssd/b9c49bfc...  -> empty frame (front_cache 180 just turns it into a black panel)
        future/7b0ad909... -> renders BLACK on the front/right walls
    An empty/black canvas is therefore an ASSET defect, not a placement bug.

This round certifies REPLACEMENT canvases: one candidate per wall, so a single build tells us which
render their picture and which are duds. Anything that comes back black/empty is struck off.
The known-good rococo portrait rides along on each wall's left slot as the control.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("ArtCertify", seed=11)

_CONTROL = "future/d8f2e7b8-c201-4b29-aec9-7fe402dc1b5c"   # rococo portrait — proven on all 4 walls

CANDIDATES = {
    "back_wall":  "hssd/54c900dd531bc8517ffe514964f6666190d3344a",   # floral oil, wooden frame
    "front_wall": "hssd/6a669a569d70b5701f415b02175b52c04313b087",   # horse, wooden frame
    "left_wall":  "future/4d8d0fa9-5007-48e6-afd9-4a187d2fc1e1",     # yellow/black/grey abstract
    "right_wall": "future/d689b740-4e99-4d78-9435-1f16388964a8",     # grey geometric abstract
}


def art(asset_id, w):
    a = scene.AddAsset("a large framed painting", asset_id=asset_id)
    a.scale(w)
    return a


with scene.RoomGroup(modulate_scale=1.0) as room:
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white plaster ceiling",
                     wall_texture="warm ivory plaster wall")
    room.place_on_center(scene.AddAsset("a small round wooden table"))

    for wall, aid in CANDIDATES.items():
        room.place_on_wall_freeform(wall, [art(aid, 1.0)])

    room.place_on_wall_back_left(art(_CONTROL, 0.7))
    room.place_on_wall_front_left(art(_CONTROL, 0.7))
    room.place_on_wall_left_left(art(_CONTROL, 0.7))
    room.place_on_wall_right_left(art(_CONTROL, 0.7))

scene.export("_art_wall_test.blend")
