"""Laboratory — "Bench Rows with a Service Perimeter" (research / teaching wet lab).

Pattern: computer_room's REPEATED-UNIT GRID (a bench unit tiled across the floor) wearing
operating_room's CLINICAL DISCIPLINE (service walls, inverted vibe layer, hard floor, no
greenery). What makes it read as a LAB rather than as a classroom or a computer lab — which
share the identical grid bones — is the PRODUCT on the benches: a microscope + a set of
reagent bottles on every bench, massed at working height (jewelry_shop's product rule, and
greenhouse v2's "the density grain of the product is what differentiates two scenes that
share a layout pattern").

ASSET REALITY (36-query retrieval stress test, tmp/lab_stress.out). The dataset has the
FURNITURE but almost none of the SCIENCE. Twelve of the category's identity props return
NOTHING AT ALL (empty candidate list, sim 0.000): fume hood, eyewash station, microscope,
centrifuge, bunsen burner, hot plate stirrer, beaker, flask set, test tube rack, petri
dishes, slide box, safety sign. Two things rescue the scene:

  1. The custom/ pool ALREADY HAS the science, ingested for the operating room — a real
     binocular MICROSCOPE, a lab AUTOCLAVE, and a gas-cylinder cart. They are invisible to
     NL retrieval ("a laboratory microscope" -> 0.000 while the mesh sits in the dataset),
     so they are PINNED BY ID. That is mandatory, not a preference (operating_room v2).
  2. The glassware was found by SILHOUETTE, not by caption (tv_studio's rule): no beaker or
     flask exists, but "a set of three decorative glass DECANTERS with stoppers" (one amber)
     is exactly a row of reagent bottles at room scale. Search the shape, not the category.

The FUME HOOD is the one gap with no honest substitute — the top "stainless steel cabinet"
hit is literally a BARBECUE GRILL. Shipping it would be the casino poker-chip trap, so the
room is built as a bio/analytical lab (which the library CAN carry) rather than a chem lab
whose hero mesh does not exist. Logged as the #1 ingest candidate; see the example file.

Zoning (near-square; the bench grid sizes the floor, the perimeter does the work):
- CENTRE     = four BENCH UNITS in a 2x2 GridGroup. One unit = bench + stool + (phase 2)
               microscope + reagent bottles. Built ONCE and duplicated `4 *` so the on-top
               tournament runs once and all four benches come out identical.
- BACK wall  = STERILE/STORAGE: the autoclave (left) + a tall glass-door reagent cabinet
               (right), STOCKED via place_inside — an empty glass cabinet reads as furniture,
               not as a lab (jewelry_shop's empty-vitrine trap, kitchen's empty uppers).
- LEFT wall  = WET BENCH: the long stainless sink counter (centre, low) + the gas-cylinder
               cart, under the window.
- RIGHT wall = HAZMAT/COLD: the yellow flammables cabinet + the lab refrigerator.
- FRONT wall = ENTRY: the door, a rolling trolley, and the whiteboard hung between them.
- Tall fixtures NEVER take a wall centre: the interior cameras sit at ~1.4-1.5 m at each
  wall's centre, and a taller fixture there blinds that view AND hallucinates rotation votes
  from the blinded strip (bakery). Every wall centre here is either empty or <= 0.95 m.
- INVERTED VIBE LAYER (operating_room): no rug, no plants, no warm accent. A lab earns its
  read by being hard and bare. The only colour is functional — the yellow safety cabinet and
  the red gas cylinders.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor layout.
Gates live INSIDE each `with` block — a place_on_top gated after the block exits registers
too late to run, and NOTHING catches it (prison_cell).
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Laboratory", seed=27)

# --- dataset pins (all measured offline with get_whd() before the first build) ----------
BENCH    = "hssd/81ad56baea5922cb91f466da624c11903d99d201"   # black workbench, bottom shelf; H=0.68 -> 0.90
STOOL    = "hssd/3e5b80fa279112c4c407bed02c7ffb555d6dc66a"   # black saddle stool on casters; H=0.52 -> 0.68
REAGENTS = "hssd/0d16ac77fb67e31f3754e6116fa58cf6a24c7222"   # "3 glass decanters w/ stoppers" = REAGENT BOTTLES
SINKCTR  = "hssd/79bf13063599b7fff88cc250d8fe76a2e46e9683"   # stainless counter + integrated sink; H=0.58 -> 0.92
REAGCAB  = "hssd/d898715b817ee6c34958abada9ca65d8a40439e5"   # tall white glass-door cabinet (STOCK IT)
FLAMCAB  = "hssd/9fee5e7b92edf3026fc491b252701dfb06ed46cf"   # zinc-YELLOW cabinet = the flammables locker
FRIDGE   = "hssd/416c68a89eda39033eb729fa72f7058802555a9e"   # lab refrigerator
TROLLEY  = "hssd/491b7091a828edecf83eaa865059e3a680d0d728"   # 3-tier rolling cart
WHTBOARD = "hssd/1b37271d2d52124cf69fa91a2acb11a6dde262f2"   # whiteboard; D=0.06 -> genuinely FLAT, wall-safe
CLOCK    = "hssd/e1725f63ab8658c1a31edbf0be78375fa93770ee"   # round wall clock
BIN      = "hssd/9523913c4c8438a9c184e378e101a8ac7ff067fe"   # red pedal bin = the biohazard waste bin

# --- ingested pins (custom/, from the operating-room hospital.zip) ----------------------
# Captions and auto-scales of ingested meshes are both VLM GUESSES (operating_room v2), so
# these are pinned by id and height-fitted from a real get_whd() measurement. The microscope
# is captioned "surgical microscope" and the gas cart "gas delivery system" — the previews
# are the evidence, and both are exactly right for a lab.
MICROSCP = "custom/d0b407b0d9f123f5b1b105f5980c910d3da4cabf"  # binocular microscope; W=0.25
# ^ This mesh had to be REPAIRED before it could be used (tmp/fix_lab_glbs.py). Its geometry sat
# ENTIRELY ABOVE its origin (y-bounds +0.444..+1.094 — an offset of +118% of its own height), so
# place_on_top seated it by an origin that isn't its centre and the microscope SANK 0.23 m through
# the bench top, its base poking out underneath: at room scale it read as standing on the FLOOR.
# The VLM loop was clean about it (geometry is "fine"; a sunk prop is semantics). Caught by eye,
# then diagnosed exactly in one offline probe — print the anchor's AABB top against the item's AABB
# bottom (computer_room's method) — never by guessing. Fixed at the SOURCE in Blender
# (origin_set BOUNDS, which preserves the material slots a trimesh round-trip would strip).
AUTOCLV  = "custom/aec28f56f031931bc434b6f1689224d7000cb5ee"  # lab autoclave + 2 red gas cylinders; H=1.55
GASCYL   = "custom/ebe6d0a7f2bacdb4ed39b6b43617fbb34ee7933e"  # orange gas cylinder; H=1.33
# NOT custom/66cdc7ba… ("gas delivery cart"): phase 1 flagged `[Lint] FLOATS 0.62 m` on it. It is
# the SAME MESH as the autoclave above (both exactly 2.66 m tall in the glb) ingested TWICE, and
# the duplicate's origin sits 25.8% off-centre (y-bounds -2.019..+0.645 vs the autoclave's
# symmetric -1.332..+1.332) — i.e. one copy escaped the recentring pass of the operating-room
# ingest. Diagnosed offline in 5 s by reading the glb bounds. SWAP the mesh, never compensate
# with a translate hack (coffee_shop's floating bench, hospital_room's floating vanity).
TRAY     = "custom/23791b62e98e76788a4b41fa405eae9167cbbf73"  # compartment tray WITH contents (not the
                                                              # empty "trough planter" c9cbd96a — that one
                                                              # is the OR's tray and previews EMPTY)

scene.prefetch_assets([
    "a heavy duty black laboratory workbench",
    "a black adjustable laboratory stool on casters",
    "a binocular laboratory microscope",
    "a set of glass reagent bottles with stoppers",
    "a tray of laboratory instruments",
    "a stainless steel laboratory sink counter",
    "a tall glass-door laboratory reagent cabinet",
    "a yellow flammable liquids safety cabinet",
    "a laboratory refrigerator",
    "a laboratory autoclave sterilizer",
    "a tall orange compressed gas cylinder",
    "a stainless steel rolling laboratory trolley",
    "a large wall-mounted whiteboard",
    "a round wall clock",
    "a red biohazard waste bin with a foot pedal",
    "a flat rectangular LED ceiling panel light",
])


def _fit_height(obj, target_h):
    """Uniform scale so the mesh stands target_h m tall (aspect preserved).
    scale(w) sets WIDTH uniformly, so drive it from the width/height ratio. Fit by HEIGHT
    for things that are TALL; never for a flat mesh (greenhouse v2: a height-fit detonates
    a flat tray into a slab)."""
    return obj.scale(obj.get_width() * target_h / obj.get_height())


# --- THE BENCH UNIT: built once, then duplicated 4x ------------------------------------
# place_on_top ALWAYS targets the group's ANCHOR, so the bench must be the anchor of the
# group the microscope goes into (living_room_cozy v3: the lamp that landed on the armchair).
# `4 * unit` deep-copies the realized transforms -> the sizing tournament runs ONCE and all
# four benches come out identical (design_principles).
with scene.RelativeGroup() as bench_unit:
    _bench = scene.AddAsset("a heavy duty black laboratory workbench", asset_id=BENCH)
    _fit_height(_bench, 0.90)                      # loads 0.68 m — a bench is 0.90 m
    bench_unit.set_anchor(_bench)
    _stool = scene.AddAsset("a black adjustable laboratory stool on casters", asset_id=STOOL)
    _fit_height(_stool, 0.68)                      # loads 0.52 m — seat height for a 0.90 m bench
    bench_unit.place_on_front_adjacent(_stool)
    if PHASE >= 2:
        # THE PRODUCT, at working height. This is the whole reason the room reads as a lab and
        # not as a classroom with the same grid. Both props verified to EXIST before use
        # (casino's poker-chip rule / kindergarten's crayon cup): the microscope is a pinned
        # ingest, the "decanters" are the reagent bottles found by silhouette.
        bench_unit.place_on_top([
            scene.AddAsset("a binocular laboratory microscope", asset_id=MICROSCP),
            scene.AddAsset("a set of glass reagent bottles with stoppers", asset_id=REAGENTS),
        ])

# sparsity 0.12, not 0.3: an over-sparse cluster is what auto-sizes a cavernous room, and the
# occupancy vote never tells you WHICH group did it (kitchen v1). Phase 1 at 0.3 spread the four
# benches into a bbox the shell had to grow to fit and voted `rescale room by 0.5`; tightening
# the aisles is the structural fix, and it costs nothing — benches in a real lab stand close.
with scene.GridGroup(sparsity=0.12, randomness=0.15) as benches:
    benches.place_grid(4 * bench_unit, cols=2)

# The gas bank: a PAIR of cylinders reads as lab gas supply where one reads as a stray canister.
# A GridGroup row (not two separate wall placements) so it claims ONE wall slot.
with scene.GridGroup(sparsity=0.15) as gas_bank:
    _cyls = 2 * scene.AddAsset("a tall orange compressed gas cylinder", asset_id=GASCYL)
    for _c in _cyls:
        _fit_height(_c, 1.35)                      # loads 1.33 m — already right, fitted for safety
    gas_bank.place_row(_cyls)

# --- the wet bench: the sink counter is its own anchor unit so the tray lands ON IT -----
with scene.RelativeGroup() as wet_bench:
    _counter = scene.AddAsset("a stainless steel laboratory sink counter", asset_id=SINKCTR)
    _fit_height(_counter, 0.92)                    # loads 0.58 m
    wet_bench.set_anchor(_counter)
    if PHASE >= 2:
        wet_bench.place_on_top(scene.AddAsset("a tray of laboratory instruments", asset_id=TRAY))

# --- the reagent cabinet: STOCK IT, or it reads as furniture ---------------------------
with scene.RelativeGroup() as reagent_cab:
    _cab = scene.AddAsset("a tall glass-door laboratory reagent cabinet", asset_id=REAGCAB)
    _fit_height(_cab, 1.90)                        # loads 1.36 m
    reagent_cab.set_anchor(_cab)
    if PHASE >= 2:
        # A glass-door cabinet with nothing in it names the FIXTURE, not the room
        # (jewelry_shop's empty vitrines; kitchen's empty glass uppers).
        reagent_cab.place_inside(
            scene.AddAsset("a set of glass reagent bottles with stoppers", asset_id=REAGENTS))

# --- the room ---------------------------------------------------------------------------
# modulate_scale=0.92 — ONE decisive application in the FINAL phase (render wins early).
# The vote train was `0.5` (Ph1) -> `0.88` (Ph1, after the grid fix) -> `0.9` (full): the 0.5 was
# not a room-size signal at all, it was the over-sparse bench grid inflating the shell, and fixing
# THAT moved the vote 0.38 in one build. Landed just SHORT of the 0.9 vote because the centre
# bench block is a rigid GridGroup, and a shell shrunk below the footprint its placements dictate
# makes fixed-size rows overflow their slots (locker_room/kitchen).
with scene.RoomGroup(modulate_scale=0.92, randomness=0.15) as room:
    # Plain colour + material words: texture strings are embedding-matched against captions,
    # and jargon drifts (computer_room's "anti-static vinyl" -> a WOOD floor).
    room.place_walls(floor_texture="smooth grey epoxy floor",
                     ceiling_texture="white",
                     wall_texture="smooth white painted plaster wall")

    room.place_on_center(benches, facing="front")

    # BACK = sterile / storage. Both are TALL -> the LEFT/RIGHT slots; the wall centre stays
    # clear so the back camera can see the room (office_modern, applied at design time).
    autoclave = scene.AddAsset("a laboratory autoclave sterilizer", asset_id=AUTOCLV)
    _fit_height(autoclave, 1.70)                   # loads 1.55 m
    room.place_on_back_wall_left(autoclave)
    room.place_on_back_wall_right(reagent_cab)

    # LEFT = the wet bench + the gas supply. The counter (0.92 m) is safely below camera
    # height, so it can hold the wall CENTRE. facing omitted everywhere on wall placements:
    # the default heuristic already turns a wall asset into the room (locker-room bug).
    room.place_on_left_wall_center(wet_bench)
    room.place_on_left_wall_left(gas_bank)

    # RIGHT = hazmat / cold storage. Tall again -> the corner slots.
    flam_cab = scene.AddAsset("a yellow flammable liquids safety cabinet", asset_id=FLAMCAB)
    _fit_height(flam_cab, 1.90)                    # loads 2.08 m
    room.place_on_right_wall_right(flam_cab)
    room.place_on_right_wall_left(scene.AddAsset("a laboratory refrigerator", asset_id=FRIDGE))

    # FRONT = entry. The door goes in PHASE 1: its auto clearance shapes the floor solve.
    room.place_on_front_wall_left(scene.AddAsset("a stainless steel rolling laboratory trolley",
                                                 asset_id=TROLLEY))
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        # The whiteboard hangs on the FRONT wall between the door and the trolley: it is
        # genuinely flat (D=0.06) and its bottom edge clears the 0.81 m trolley, so the
        # wall-object clearance pass has nothing to slide (prison_cell's rule — check a wall
        # object's AABB bottom against the TOPS of the furniture near that wall).
        room.place_on_wall_front_center(scene.AddAsset("a large wall-mounted whiteboard",
                                                       asset_id=WHTBOARD, width=1.6))
        room.place_on_wall_back_center(scene.AddAsset("a round wall clock", asset_id=CLOCK))
        # NO lab coat on the right wall. The coat-hook mesh is 0.28 m deep and the DSL warned it
        # would "read as furniture FLOATING in mid-air" — the render agreed (a garment hovering
        # off the wall). Wall-hung means FLAT (<0.25 m). Dropped rather than faked: a bare wall
        # centre is also the clinical read (operating_room's inverted vibe layer) AND keeps the
        # right-hand interior camera unobstructed.
        room.place_on_back_left_corner(scene.AddAsset("a red biohazard waste bin with a foot pedal",
                                                      asset_id=BIN))
        # Daylight over the wet bench. The "black void" that six older examples worked around
        # was a renderer bug and is FIXED (greenhouse) — glaze freely. A standard pane takes a
        # single slot, so it cannot collide with the counter's or the cart's floor slots.
        room.place_window_standard("left_wall", position="right", curtain=None)
        # Flush panels, never a pendant (executive_office). density is a fixture COUNT that
        # scales with FLOOR AREA — 0.015 is the ~50 m² band (bookstore's lint datapoint).
        room.add_lighting("a flat rectangular LED ceiling panel light", density=0.015)

scene.export("laboratory_v1.blend")
