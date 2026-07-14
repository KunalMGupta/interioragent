"""Warehouse — "Industrial Warehouse Merchandising Rhythm" (guided 9-gate flow, v2 gear).

Planner target: tall steel pallet racking loaded with boxes, DOUBLE-LOADED forklift aisles, a
loading/staging zone with stacked pallets, concrete + neutral-grey + steel palette, linear
industrial lighting, painted safety floor markings. (A Costco-ish merchandising warehouse —
legible rows.)

Layout — the racking IS the structure, and the ROOM's THIRDS make the aisle (GridGroup.place_grid
cannot: its inter-row gap is sparsity*row_depth and racks are only ~0.6 m deep, so the widest aisle
it can open is ~0.6 m — far too tight for a forklift):
- BACK third  : a butted rack WALL (4 racks in a frozen GridGroup row), facing="front".
- CENTER third: a second rack WALL, facing="back" — the two loaded faces flank the SAME gap, so the
                aisle between the back and center thirds is double-loaded (the money shot).
- FRONT third : left OPEN by the racking, and dressed as a working LOADING DOCK — the FORKLIFT hero
                flanked by traffic cones (front-left), a staged row of crates/boxes/pallet jack
                (front-center), a packing bench + pallet gas cylinder (front-right).
- BACK-RIGHT  : a factory boiler + tanks backdrop for depth. 4-wide (not 5-wide) rack walls keep the
                back corners free of rack ends so it fits.
- WALLS       : roller-shutter DOCK door on the front wall (reads warehouse where a house door does
                not) + a green EXIT sign mounted high above-right; a personnel door on the right wall.

Identity comes from the ingested custom material-handling gear (forklift, pallet jack, cones,
roller shutter, exit sign, gas cylinder, crates, factory tanks) turning the open front third from
"a floor with boxes" into a working dock — that is what lifts the scene from credible to
unmistakable. GOTCHA baked in: the ingested vehicle GLBs (forklift, pallet jack) have their front on
-Z (opposite the +Z ingest convention), so `facing` reads FLIPPED — the forklift is placed
facing="front" to actually face into the room, and the pallet jack rides a GridGroup row (which sets
rotation 0 = its real forward) so it parks correctly.

Phase-gated (IDSDL/phases.py): `workbench run skills/examples/warehouse_v1.py --phase 1` builds only
the floor layout (~1-2 min); phase 2 dresses the surfaces; phase 3 adds the wall gear and lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Warehouse", seed=31)

# ---- pinned assets (gate-3 audit: every mesh eyeballed on a contact sheet) --------------------
RACK       = "hssd/44935cd7942c9a256e13286fd3c07e148fb3e5aa"   # loaded industrial rack (dark frame,
                                                               # plank decking); its goods are baked
                                                               # CYAN and it is a complete mesh, so it
                                                               # cannot be recoloured — balanced by
                                                               # pushing brown cardboard to the dock
PALLET     = "hssd/a5d4b9f023a6a7686c5f973a53cb554e8d108d84"
BOXES_CARD = "hssd/71e625e1cc238c233bc67dc7014766281b317e22"
BOXES_GRAY = "future/ae9821aa-3659-40a2-84fa-c884d854faa3"
WORKBENCH  = "hssd/81ad56baea5922cb91f466da624c11903d99d201"    # a THICK anchor — place_on_top works
                                                                # on it (a flat pallet does not)
# ingested custom warehouse gear — the home-furniture pool has no real material-handling gear
# ("forklift" retrieved wooden TOYS, "traffic cone" retrieved orange CUSHIONS)
TANKS      = "custom/58ad2b42c254545ddef252936c3890e988dc3697"
FORKLIFT   = "custom/96aaadef0ac4e06d76a4d130abc55f166d7db7c7"  # -Z front: `facing` reads flipped
PALLET_JACK= "custom/ac9be2e873be38bccad6a1c058a4280847f37647"  # -Z front: park it in a Grid row
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
    """Size a small prop UP to palletized-load scale — the box-stack mesh is desk-parcel sized."""
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
    packing.place_on_left(scene.AddAsset("an industrial gas cylinder canister", asset_id=GAS))
    if PHASE >= 2:
        # gate INSIDE the with-block: a place_on_top gated outside it never runs and the prop is GONE
        packing.place_on_top(scene.AddAsset("a stack of brown cardboard shipping boxes",
                                            asset_id=BOXES_CARD))

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

    # personnel door in PHASE 1: its auto clearance shapes the floor solve
    # (NB: `position` is a wall label — left/center/right — NOT "front")
    room.place_door("right_wall", position="center")

    if PHASE >= 3:
        # roller-shutter dock door on the front wall, green EXIT sign above-right
        room.place_on_front_wall_center(scene.AddAsset("a grey metal roller shutter dock door",
                                                       asset_id=SHUTTER))
        room.place_on_front_wall_right(scene.AddAsset("a green emergency exit sign",
                                                      asset_id=EXIT_SIGN), bottom=2.2)

        # industrial linear high-bays: modulate_scale is the fixture-SIZE lever — small fixtures over a
        # high ceiling render as a scattered starfield, so scale UP (2.4x) at LOW density (0.02)
        room.add_lighting("a row of bright industrial linear ceiling lights",
                          density=0.02, modulate_scale=2.4)

scene.export("warehouse_v1.blend")
