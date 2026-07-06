"""
Warehouse v2 — now with real material-handling gear (Kunal's ingested custom GLBs, 2026-07-06).

Plan: the racking is the structure — two loaded rack WALLS on the back+center thirds give a WIDE
double-loaded forklift aisle (back faces front, center faces back → both loaded faces flank the aisle).
The open FRONT third is a working LOADING DOCK: a FORKLIFT (hero) flanked by traffic cones, a row of
staged crates/boxes, a packing bench with a pallet jack + gas cylinder. A roller-shutter dock door on
the front wall, a green EXIT sign above it, a personnel door on the right wall. Concrete floor, grey
industrial walls, exposed steel ceiling with linear high-bay lighting.

Custom ingested assets (custom/…): forklift, pallet jack, traffic cone, roller shutter, exit sign, gas
cylinder, wooden crate, factory tanks. See memory [[ingested-warehouse-office-assets]].

Build state: DONE / VLM-clean (2026-07-06, seed=31). Forklift dock + factory-tank backdrop + roller
shutter + exit sign + double-loaded rack aisle. Final compile: no rescale / no rotation / no wall
overlap. GOTCHA baked in below: the ingested vehicle GLBs (forklift, pallet jack) have front on -Z, so
`facing` reads flipped — the forklift is placed facing "front" and the pallet jack rides a GridGroup row
(rotation 0) so both orient correctly.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("Warehouse", seed=31)

# --- pinned assets ---
RACK       = "hssd/44935cd7942c9a256e13286fd3c07e148fb3e5aa"   # loaded industrial rack (dark frame)
PALLET     = "hssd/a5d4b9f023a6a7686c5f973a53cb554e8d108d84"
BOXES_CARD = "hssd/71e625e1cc238c233bc67dc7014766281b317e22"
BOXES_GRAY = "future/ae9821aa-3659-40a2-84fa-c884d854faa3"
WORKBENCH  = "hssd/81ad56baea5922cb91f466da624c11903d99d201"
# ingested custom warehouse gear
TANKS      = "custom/58ad2b42c254545ddef252936c3890e988dc3697"
FORKLIFT   = "custom/96aaadef0ac4e06d76a4d130abc55f166d7db7c7"
PALLET_JACK= "custom/ac9be2e873be38bccad6a1c058a4280847f37647"
CONE       = "custom/3d013e88f2977a1a98d3dd73cecf0d1cb3c3ad9f"
SHUTTER    = "custom/77209bcbf628ab88f537f7b1983e42ba1cde49fb"
EXIT_SIGN  = "custom/e750dc69c392d8205805e7a0653c276f5ee5dd49"
GAS        = "custom/ebe6d0a7f2bacdb4ed39b6b43617fbb34ee7933e"
CRATE      = "custom/eb9d3e7bc84027186dadc23ce1dcd332429eed11"

scene.prefetch_assets([
    "a heavy-duty industrial warehouse pallet racking bay loaded with boxes",
    "a stack of brown cardboard shipping boxes",
    "a wooden shipping crate", "an industrial warehouse forklift",
    "an orange traffic safety cone", "an orange pallet jack",
    "an industrial gas cylinder", "a heavy-duty industrial steel workbench",
])


def _fit_w(obj, w):
    W, H, D = (float(v) for v in obj.get_whd())
    if W > 1e-6:
        f = w / W
        obj.scale_only_width(W * f); obj.scale_only_height(H * f); obj.scale_only_depth(D * f)
    return obj


def rack_wall(n):
    """A butted horizontal row of n loaded racks -> one continuous rack wall (deterministic group)."""
    racks = n * scene.AddAsset("a heavy-duty industrial warehouse pallet racking bay loaded with boxes",
                               asset_id=RACK)
    with scene.GridGroup(sparsity=0.05, randomness=0.0) as w:
        w.place_row(racks)
    return w


wall_back = rack_wall(4)
wall_mid  = rack_wall(4)

# --- the FORKLIFT (hero), flanked by two traffic cones. NOTE: the ingested vehicle GLBs have their
# front on -Z (opposite the +Z ingest convention), so `facing` reads flipped -> place facing "front". ---
with scene.RelativeGroup() as fork_grp:
    fork_grp.set_anchor(scene.AddAsset("an industrial warehouse forklift", asset_id=FORKLIFT))
    fork_grp.place_on_left(scene.AddAsset("an orange traffic safety cone", asset_id=CONE))
    fork_grp.place_on_right(scene.AddAsset("an orange traffic safety cone", asset_id=CONE))

# --- staged goods row on the dock: crates + cardboard + a parked pallet jack. A GridGroup row sets
# rotation 0, which is "front" for the -Z-front custom pallet jack, so it parks facing the right way. ---
staged = [
    scene.AddAsset("a wooden shipping crate", asset_id=CRATE),
    scene.AddAsset("an orange pallet jack for moving pallets", asset_id=PALLET_JACK),
    _fit_w(scene.AddAsset("a stack of brown cardboard shipping boxes", asset_id=BOXES_CARD), 1.1),
    scene.AddAsset("a wooden shipping crate", asset_id=CRATE),
]
with scene.GridGroup(sparsity=0.5, randomness=0.12) as dock:
    dock.place_row(staged)

# --- packing station: workbench (box on top) + a gas cylinder ---
with scene.RelativeGroup() as packing:
    packing.set_anchor(scene.AddAsset("a heavy-duty industrial steel workbench", asset_id=WORKBENCH))
    packing.place_on_top(scene.AddAsset("a stack of brown cardboard shipping boxes", asset_id=BOXES_CARD))
    packing.place_on_left(scene.AddAsset("an industrial gas cylinder canister", asset_id=GAS))

with scene.RoomGroup(modulate_scale=0.9, randomness=0.05, max_height=5.0) as room:
    room.place_walls(floor_texture="polished grey concrete warehouse floor with painted safety lines",
                     ceiling_texture="light grey exposed industrial ceiling with steel beams",
                     wall_texture="light grey industrial corrugated metal wall")

    # the double-loaded rack aisle
    room.place_on_back(wall_back, facing="front")
    room.place_on_center(wall_mid, facing="back")

    # front third = the loading DOCK
    room.place_on_front_left(fork_grp, facing="front")    # forklift (its -Z front now points into room)
    room.place_on_front(dock, facing="back")              # staged crates/boxes
    room.place_on_front_right(packing, facing="back")     # packing bench + jack + gas

    # background industrial: a factory boiler + tanks tucked in the back-right corner
    room.place_on_back_right_corner(scene.AddAsset("a rusty factory boiler with stacked metal tanks",
                                                   asset_id=TANKS), facing="front")

    # roller-shutter dock door on the front wall, green EXIT sign above-right, personnel door on the right
    room.place_on_front_wall_center(scene.AddAsset("a grey metal roller shutter dock door", asset_id=SHUTTER))
    room.place_on_front_wall_right(scene.AddAsset("a green emergency exit sign", asset_id=EXIT_SIGN), bottom=2.2)
    room.place_door("right_wall", position="center")

    # industrial linear high-bays (scaled up so they read as fixtures, low density)
    room.add_lighting("a row of bright industrial linear ceiling lights", density=0.02, modulate_scale=2.4)

scene.export("warehouse.blend")
