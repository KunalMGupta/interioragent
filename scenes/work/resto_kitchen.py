"""
Restaurant kitchen (commercial back-of-house) — "The Stainless Line".

The last uncovered dataset category (Restaurant-Kitchen). A commercial kitchen is the
LICENSED recipe-B kitchen: there is no fitted "set" asset for a resto line, so the room is
COMPOSED from stainless modules — which is also what a real commercial kitchen is (runs of
interchangeable NSF units). The domestic fitted-set rule (kitchen.md recipe A) does NOT
apply here; the recipe-B composition rules do (compose around mis-sized modules, place props
on a RUN not a module, flat flush lighting).

Layout — the classic three-zone line-and-island plan:
- BACK wall  : the COOK LINE — 6-burner range + industrial oven + 2-burner stove as ONE
               GridGroup run, flush on the wall; the wide stainless hood WALL-MOUNTED above
               it in phase 3 (kitchen.md's upper-row mount: bottom= + ignore_overlap +
               is_static — geometry, not a constraint).
- CENTRE     : the PREP ISLAND — two stainless worktables end-to-end as one run; the pots /
               pans / red enamel accent are massed ON THE RUN in phase 2 (RelativeGroup
               anchored on the whole GridGroup so the props spread along the counter —
               kitchen.md). Identity lives at working height (laboratory's product rule).
- LEFT wall  : the WASH/SERVICE side — chrome wire rack (dry store) + the commercial
               counter with integrated sink.
- RIGHT wall : the COLD side — tall stainless freezer + side-by-side fridge, plus a second
               wire rack.
- FRONT      : the Bain-Marie hot pass facing back into the kitchen (the service handoff),
               door front-right. WINDOWLESS by design (a resto kitchen is back-of-house;
               also sidesteps the black-void limit entirely — casino's rule).

Phase 1: every floor module above (all of it is layout mass) + the door.
Phase 2: the cookware massed on the prep run (created inside the gate).
Phase 3: the hood mount + the hanging utensil rack + flat flush lighting.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("RestoKitchen", seed=17)

# ---- pinned line equipment (audited via browse 2026-07-13; all native HSSD, no ingest needed) ----
RANGE6   = "hssd/b9ab4cf85f96a453ae2c668ed5b9e0cac8025827"  # stainless 6-burner range cooker
OVEN     = "hssd/605c225872965509014c7ed4338b5c046f6c3214"  # industrial gray oven on a stand
STOVE2   = "hssd/52fe6858b0eaab18be1fa9bc5c195147ade55a1a"  # stainless 2-burner stove w/ lower shelf
WORKTBL  = "hssd/3298290022261948ac907bf264d6d622a9af5145"  # stainless worktable (the prep module)
SINKCT   = "hssd/79bf13063599b7fff88cc250d8fe76a2e46e9683"  # commercial stainless counter w/ integrated sink
BAIN     = "hssd/381a6e138a9fd613507af6c51fcc9db47271bc25"  # Bain-Marie wagon — the hot pass
FREEZER  = "hssd/3a9f78af8ca7d45294c89244ce9fb37a386b6468"  # tall stainless freezer
FRIDGE   = "hssd/f5a154e8d963064a8e43960374e4b5be523d68b0"  # stainless side-by-side fridge freezer
RACK     = "hssd/afac556a45574d445236962a9e625298aea43f47"  # chrome wire shelving, 4 tiers
HOOD     = "hssd/ac5f78e5a9d057ec76e544c6e74ffa00ec82ae13"  # WIDE stainless range hood (the most
                                                             # canopy-like of the chimney hoods)
UTENSIL  = "hssd/fc34254f2aac6da46964ede7efc727a33a755919"  # hanging utensil set on a rail (wall)
PANSET   = "hssd/2edd0fa056bc632cab9c69b7accb99a9094179c3"  # 4-piece stainless pan set
STOCKPOT = "hssd/bc273df69e9d7941f7124094ed0fae196305c41e"  # big stockpot with lid
ENAMEL   = "hssd/e3331c6c184747171470e9e5eb7b0f589b3c61b6"  # red enamel pot set — the ONE warm accent

scene.prefetch_assets([
    "a stainless steel six burner commercial range cooker",
    "an industrial oven on a metal stand",
    "a stainless steel two burner stove",
    "a stainless steel kitchen worktable",
    "a commercial stainless steel counter with an integrated sink",
    "a stainless steel bain-marie service wagon",
    "a tall stainless steel commercial freezer",
    "a stainless steel side-by-side fridge freezer",
    "a chrome wire shelving storage rack",
    "a wide stainless steel range extraction hood",
    "a stainless steel kitchen utensil set hanging on a rail",
    "a stainless steel cooking pan set",
    "a large stainless steel stockpot with a lid",
    "a red enamel cooking pot set",
    "a flat round LED flush mount ceiling light",
])

# ---- the COOK LINE: three modules as one rigid run (recipe-B composition) ----
with scene.GridGroup(sparsity=0.08, randomness=0.03) as cook_line:
    cook_line.place_row([
        scene.AddAsset("a stainless steel six burner commercial range cooker", asset_id=RANGE6),
        scene.AddAsset("an industrial oven on a metal stand", asset_id=OVEN),
        scene.AddAsset("a stainless steel two burner stove", asset_id=STOVE2),
    ])

# ---- the PREP ISLAND: two worktables end-to-end; props mass on the RUN in phase 2 ----
with scene.GridGroup(sparsity=0.05, randomness=0.02) as prep_run:
    prep_run.place_row([
        scene.AddAsset("a stainless steel kitchen worktable", asset_id=WORKTBL),
        scene.AddAsset("a stainless steel kitchen worktable", asset_id=WORKTBL),
    ])
with scene.RelativeGroup() as prep_station:
    prep_station.set_anchor(prep_run)          # place_on_top seats onto the ANCHOR = the whole run
    if PHASE >= 2:
        prep_station.place_on_top([
            scene.AddAsset("a stainless steel cooking pan set", asset_id=PANSET),
            scene.AddAsset("a large stainless steel stockpot with a lid", asset_id=STOCKPOT),
            scene.AddAsset("a red enamel cooking pot set", asset_id=ENAMEL),
        ])

# ---- the HOT PASS: bain-marie wagon, facing back into the kitchen ----
bain = scene.AddAsset("a stainless steel bain-marie service wagon", asset_id=BAIN)

# ---- cold + storage + wash modules (all floor mass -> all phase 1) ----
# The COLD PAIR is one rigid run so it sits in ONE wall slot — and that slot is the wall's
# LEFT (back) end, never the CENTRE: the interior camera sits at ~1.4 m at each wall's centre
# and a tall fridge there blinds the whole view solid black (bakery rule; caught in this
# scene's first phase-1 render — the right-wall view WAS black).
with scene.GridGroup(sparsity=0.05, randomness=0.02) as cold_pair:
    cold_pair.place_row([
        scene.AddAsset("a tall stainless steel commercial freezer", asset_id=FREEZER),
        scene.AddAsset("a stainless steel side-by-side fridge freezer", asset_id=FRIDGE),
    ])
rack_l  = scene.AddAsset("a chrome wire shelving storage rack", asset_id=RACK)
rack_r  = scene.AddAsset("a chrome wire shelving storage rack", asset_id=RACK)
sink_ct = scene.AddAsset("a commercial stainless steel counter with an integrated sink", asset_id=SINKCT)

# 0.9, not the voted 0.8: the working aisles around the island ARE the room's circulation
# (garage/corridor rule) and the line/island runs are fixed-size GridGroups that overflow a
# shell shrunk below their footprint (kitchen.md's 0.85-over-0.80 precedent) — ONE decisive
# application, then stop.
with scene.RoomGroup(modulate_scale=0.9, randomness=0.08) as room:
    room.place_walls(floor_texture="smooth grey concrete floor",
                     ceiling_texture="plain white ceiling",
                     wall_texture="plain white tile wall")

    # BACK: the cook line flush on the wall, burners facing the room
    room.place_on_back(cook_line, facing="front")

    # CENTRE: the prep island (the working aisle around it is legitimate circulation —
    # expect the empty-floor shrink vote and decline it, garage/corridor rule)
    room.place_on_center(prep_station, facing="front")

    # LEFT: dry store rack + the wash counter
    room.place_on_left_wall_left(rack_l, facing="right")
    room.place_on_left_wall_center(sink_ct, facing="right")

    # RIGHT: the cold run at the back end, the rack at the front end — the CENTRE stays clear
    # for the camera (see the cold_pair note above)
    room.place_on_right_wall_left(cold_pair, facing="left")
    room.place_on_right_wall_right(rack_r, facing="left")

    # FRONT: the pass, and the door beside it
    room.place_on_front(bain, facing="back")
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # the hood over the range — kitchen.md's geometric wall mount, not a constraint.
        # bottom=1.95, NOT 1.55: the interior camera sits at ~1.4-1.5 m at the wall centre and
        # the first full build hung the deep canopy right in its face — the whole back view
        # rendered as a grey slab. Above ~1.9 the camera looks UNDER the canopy.
        hood = scene.AddAsset("a wide stainless steel range extraction hood", asset_id=HOOD)
        hood.scale(1.6)                     # width ~ the range module below it
        hood.ignore_overlap = True
        hood.is_static = True
        room.place_on_back_wall_center(hood, bottom=1.95)
        # NOTE: the hanging utensil rail was tried on the left wall and is DROPPED — the wall
        # scaler re-derived it 0.36 m deep (> the 0.25 m limit) and the build warned it would
        # read as furniture floating in mid-air (museum's mask rule). Utensils want a low
        # anchor or a real rail mesh, not the art band.
        # FLAT flush fixture only (kitchen.md); medium room -> moderate density
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.06)

scene.export("resto_kitchen.blend")
