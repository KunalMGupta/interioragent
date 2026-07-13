"""
Fast food / burger joint — "Backlit Menus, Fixed Booths, Bold Red-Yellow Identity" (planner headline).

Zoned single room (restaurant.md's skeleton, QSR edition):
  - BACK wall  = the SERVICE LINE: a long solid-front counter (hero) + a self-order kiosk composed
    at its left as ONE rigid station, so the queue lane in front of it is geometric. The counter top
    IS the pickup display (there is no fast-food-counter mesh with food built in): burger-and-fries
    trays + POS + takeaway cups massed on it at viewing height.
  - LEFT wall  = the BOOTH RUN: fixed booth bench backing the wall + a bare pedestal table + a facing
    red chair, composed as one unit and duplicated (restaurant's banquette pattern).
  - RIGHT wall = the DRINK STATION: a short run of the same counter carrying the retro drink machine
    + cups, with the red waste/tray bin composed at its right (one station, one slot). The tall red
    Coca-Cola cooler stands in the back-right corner beside the counter's end (the bakery fridge rule:
    a TALL fixture goes in a corner, never a wall CENTER, or it swallows that wall's interior view).
  - CENTER   = the dining field: two 4-tops (bare black pedestal table + a 2-red/2-yellow chair ring).
  - FRONT wall = the glass STOREFRONT (floor-to-ceiling; it claims all three slots of its wall, so the
    door goes on the RIGHT wall — the two cannot share a wall without a wall-overlap warning).

Identity = the PRODUCT at viewing height (jewelry_shop/bakery rule). Three category gaps, all
substituted rather than shipped empty (audited at gate 3, previews eyeballed):
  - NO backlit menu board exists (best hits are chalkboards and retro tin signs; the top neon-sign
    pick previews as a BLANK white rectangle = the office_modern empty-frame trap). Substitute: the
    yellow 'Milkshake' product sign as the menu band over the counter + an ILLUMINATED 'DINER' sign.
  - NO soda fountain / drink dispenser exists (the query returns domestic fridges). Substitute: the
    red-and-white Coca-Cola display cooler + a retro red/white drink machine on the drink console.
  - NO fixed booth-and-table unit exists; composed from a booth bench + bare table + chair.
The one asset that actually makes the room read "burger joint" is hssd/e9b4c087 — takeaway burger and
fries in cardboard packaging — massed on every table and on the counter.

Palette: place_walls takes ONE wall texture, so the WALLS carry the red and the PROPS carry the yellow
(yellow chairs + yellow signage) — the music_studio accent-on-a-prop rule. Texture strings verified
OFFLINE against IDSDL/assets/wall_textures_embeddings.npz before building (office_modern rule): "solid
bright red smooth uniform wall" -> a true solid deep red (0.672), where the naive "bright red painted
wall" -> BRICK (0.499); "grey speckled terrazzo floor tiles" -> real terrazzo (0.701), as the plan asked.

Phase-gated (IDSDL/phases.py): `workbench run <this> --phase 1` builds only the floor layout.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("FastFood", seed=47)

# --- pinned heroes (every preview eyeballed on the contact sheet at gate 3) ---
COUNTER   = "custom/cffdedd8d354e346e510f227b4a6bc5b65dc3dcb"  # long solid-front service counter (0.87)
KIOSK     = "hssd/8cf3b150fceea0aed2af3f73b0f68839c4f41147"    # black touchscreen self-order kiosk
POS       = "hssd/9dbca04152892f2dbc8e82bf8ea3c94559e918af"    # touchscreen POS terminal
BOOTH     = "future/56f963cd-9ff6-48af-bd68-1db9411b1e6c"      # upholstered booth bench (restaurant's)
TABLE     = "hssd/5fa9eb631ea0ea89463b1c7b36ad8537310903fb"    # BARE black square pedestal cafe table
RED_CHAIR = "future/bc34a9bf-a55d-4044-b0a5-fab42919886c"      # red molded chair, metal sled legs
YEL_CHAIR = "future/89aa99b8-c388-4baa-b029-7a754cdd24dd"      # bright yellow molded chair (see note)
# (the rank-1 "yellow fiberglass chair" hssd/a21c5079… is a caption≠mesh trap: it renders as a CREAM
#  ROCKING chair with curved runners — wrong colour AND a lounge form. Caught in the phase-1 render.)
COOLER    = "hssd/595c9e233d3e72bb23b7cfa22a5cc3e2523a1350"    # red/white Coca-Cola display cooler
DRINKMACH = "hssd/58074cda1782f1631517f10cebd5eb9fb9edc38d"    # retro red/white drink (slush) machine
BURGER    = "hssd/e9b4c087f46bf372c890cf074de55fe974092378"    # takeaway burger + fries — THE identity prop
POPCORN   = "hssd/02c784e528d209e63cfeb98944ae483256338bc5"    # striped popcorn box + soda bottle
CUPS      = "hssd/7e72a52e8b412403169fb06803adf6882f5dcc78"    # takeaway cups in a carrier
MILKSHAKE = "hssd/79b224535ddd7ecdff06a86f9d17d98c08536592"    # YELLOW 'Milkshake' sign = the menu band
DINER     = "hssd/29a27d5893f1b3383204673903f1a385588e02ef"    # illuminated 'DINER' sign
DINERART  = "hssd/20af5e18cc65ec1537972cf28ba2bed7f4936c81"    # retro diner print (red booths, checker floor)
BIN       = "hssd/9523913c4c8438a9c184e378e101a8ac7ff067fe"    # red dome-lid waste bin (tray station)

TABLE_H = 0.75   # a dining table is ~0.75 m; this mesh ships at 0.96 (BAR height) — see _fit_height


def _fit_height(obj, h):
    """Uniformly scale (all axes) so the object's total HEIGHT == h, preserving its proportions.

    Why this is mandatory here: `AddAsset(..., width=…)` is a SINGLE-AXIS pin — it stretches the
    width and leaves the height ALONE. The cafe-table mesh ships 0.96 m tall (bar height), taller
    than these chairs are in total (0.68-0.71 m, seat ~0.43), so a width-pinned table towers over
    its own seats. Seat height tracks the surface it serves (restaurant's bar-stool rule), so fit
    the TABLE to dining height and the ring reads correctly.
    """
    W, H, D = (float(v) for v in obj.get_whd())
    if H > 1e-6:
        f = h / H
        obj.scale_only_width(W * f)
        obj.scale_only_height(H * f)
        obj.scale_only_depth(D * f)
    return obj


scene.prefetch_assets([
    "a long modern service counter with a solid front panel",
    "a black touchscreen self-order kiosk stand",
    "a modern touchscreen point of sale terminal",
    "a fast food restaurant booth bench seat with a high back",
    "a small square cafe dining table with a laminate top, no chairs",
    "a red molded plastic cafe chair with metal legs",
    "a bright yellow molded plastic dining chair",
    "a red and white Coca-Cola glass door display cooler",
    "a retro red and white drink machine",
    "a takeaway burger and fries in cardboard packaging",
    "a striped popcorn box with a bottle of soda",
    "a set of takeaway cups in a carrier",
    "a red metal waste bin with a dome lid",
    "a yellow retro milkshake wall sign",
    "an illuminated retro diner wall sign",
    "a retro framed print of a diner scene",
    "a flat round LED flush mount ceiling light",
    "a black cylinder pendant light",
    "a tall potted green plant in a planter",
])

# --- BACK: the service line. Counter (hero) + kiosk = ONE rigid station, ONE floor slot. --------
counter = scene.AddAsset("a long modern service counter with a solid front panel",
                         asset_id=COUNTER, width=3.0)
pos_terminal = scene.AddAsset("a modern touchscreen point of sale terminal", asset_id=POS)
with scene.RelativeGroup() as counter_group:
    counter_group.set_anchor(counter)
    if PHASE >= 2:
        # the counter top IS the pickup display — mass the product at viewing height
        counter_group.place_on_top([
            pos_terminal,
            scene.AddAsset("a takeaway burger and fries in cardboard packaging", asset_id=BURGER),
            scene.AddAsset("a takeaway burger and fries in cardboard packaging", asset_id=BURGER),
            scene.AddAsset("a set of takeaway cups in a carrier", asset_id=CUPS),
        ])
    if PHASE >= 3:
        counter_group.add_lighting("a black cylinder pendant light", density=0.1)  # SINGULAR query

kiosk = scene.AddAsset("a black touchscreen self-order kiosk stand", asset_id=KIOSK)
with scene.RelativeGroup() as service_line:
    service_line.set_anchor(counter_group)
    service_line.place_on_left(kiosk)          # order here, pick up at the counter

# --- LEFT: a fixed booth unit (bench + its own table + a facing chair). Built ONCE, duplicated. ---
def booth_unit():
    # the TABLE is its own sub-unit so PHASE-2 place_on_top seats the meal on the TABLE, not on the
    # bench cushion — place_on_top ALWAYS targets the group anchor (living_room_cozy v3 lesson)
    with scene.RelativeGroup() as table_unit:
        t = _fit_height(scene.AddAsset("a small square cafe dining table with a laminate top, no chairs",
                                       asset_id=TABLE), TABLE_H)
        table_unit.set_anchor(t)
        if PHASE >= 2:
            table_unit.place_on_top([
                scene.AddAsset("a takeaway burger and fries in cardboard packaging", asset_id=BURGER),
            ])
    with scene.RelativeGroup() as g:
        bench = scene.AddAsset("a fast food restaurant booth bench seat with a high back",
                               asset_id=BOOTH, width=1.4)
        g.set_anchor(bench)
        g.place_on_front(table_unit)
        chair = scene.AddAsset("a red molded plastic cafe chair with metal legs", asset_id=RED_CHAIR)
        g.place_on_front_further(chair)
        g.face(chair, toward=bench)            # the far chair turns in to face the booth
    return g

booth_1, booth_2 = booth_unit(), booth_unit()

# --- CENTER: a 4-top (bare table + a 2-red / 2-yellow chair ring). Built ONCE, duplicated. -------
# sparsity/jitter kept LOW: at 0.2/0.35 the phase-1 render showed the ring drifting off its table
with scene.AroundGroup(sparsity=0.05, jitter=0.15) as four_top:
    t = _fit_height(scene.AddAsset("a small square cafe dining table with a laminate top, no chairs",
                                   asset_id=TABLE), TABLE_H)
    four_top.set_anchor(t)
    chairs = (2 * scene.AddAsset("a red molded plastic cafe chair with metal legs", asset_id=RED_CHAIR)
              + 2 * scene.AddAsset("a bright yellow molded plastic dining chair",
                                   asset_id=YEL_CHAIR))
    four_top.place_circle(chairs)
    for c in chairs:
        four_top.face(c, toward=t)
    if PHASE >= 2:
        four_top.place_on_top([
            scene.AddAsset("a takeaway burger and fries in cardboard packaging", asset_id=BURGER),
            scene.AddAsset("a striped popcorn box with a bottle of soda", asset_id=POPCORN),
        ])

four_top_c, four_top_f = 2 * four_top

# --- RIGHT: the drink station (short counter run + drink machine on top) + the tray/waste bin -----
drink_top = scene.AddAsset("a long modern service counter with a solid front panel",
                           asset_id=COUNTER, width=1.5)
with scene.RelativeGroup() as drink_counter:
    drink_counter.set_anchor(drink_top)
    if PHASE >= 2:
        drink_counter.place_on_top([
            scene.AddAsset("a retro red and white drink machine", asset_id=DRINKMACH),
            scene.AddAsset("a set of takeaway cups in a carrier", asset_id=CUPS),
        ])

bin_ = scene.AddAsset("a red metal waste bin with a dome lid", asset_id=BIN)
with scene.RelativeGroup() as drink_station:
    drink_station.set_anchor(drink_counter)
    drink_station.place_on_right(bin_)         # bus your tray where you refill your drink

# --- the room ------------------------------------------------------------------------------------
# The room-shrink vote held steady (0.87 phase 1 -> 0.85 phase 2) = a real sparse read, not noise, so
# it is applied ONCE in the final phase (the render-wins-early rule; the shell is not furniture-packed,
# so a <1.0 shrink is safe here — the laundromat sparse-room case).
with scene.RoomGroup(modulate_scale=0.85 if PHASE >= 3 else 1.0, randomness=0.15) as room:
    room.place_walls(floor_texture="grey speckled terrazzo floor tiles",
                     ceiling_texture="solid white smooth ceiling",
                     wall_texture="solid bright red smooth uniform wall")

    room.place_on_back(service_line, facing="front")          # the service line faces the diners

    # BOOTHS: pin the run FLUSH to the wall with the wall-adjacent verbs. A floor SLOT
    # (place_on_left / place_on_front_left) leaves a visible gap behind the bench — the slot is a
    # third of the ROOM, not the wall, and jitter + the grad solve drift the group off it. A booth
    # backed by air is not a booth. (Omit `facing`: the wall heuristic already turns them into the
    # room; passing facing="left" would face them INTO the wall.)
    room.place_on_left_wall_left(booth_1)
    room.place_on_left_wall_right(booth_2)

    room.place_on_center(four_top_c, facing="front")
    room.place_on_front_right(four_top_f, facing="front")     # a 4-top at the storefront glass
    room.place_on_right_wall_center(drink_station)            # default facing = into the room
    room.place_on_back_right_corner(                          # TALL fixture -> corner, never a wall center
        scene.AddAsset("a red and white Coca-Cola glass door display cooler", asset_id=COOLER),
        facing="front")

    # door in PHASE 1 — its auto clearance shapes the floor solve. It cannot share the front wall
    # with the storefront glass (floor-to-ceiling claims all three slots), so it enters on the right.
    # NB: place_door positions are the wall's own left/center/right thirds — there is no "front".
    room.place_door("right_wall", position="right")

    if PHASE >= 2:
        # A SERVICE/RECEPTION DESK'S SCREEN FACES THE WALL THE DESK STANDS AGAINST — the operator
        # works from the wall side, so the customer sees the monitor's BACK. place_on_top's
        # tournament optimizes position, not semantic orientation, and had left the POS broadside
        # to the room. face(..., toward=<wall>) is RoomGroup-only and 90°-snapped, and it applies
        # at the END of compile, so it overrides the rotation the placement baked in.
        room.face(pos_terminal, toward="back_wall")

    if PHASE >= 3:
        # vibe layer: the plan's one softening element — a tall plant in a corner, against the
        # hard laminate/terrazzo/molded-plastic envelope (a corner, so it claims no wall slot)
        room.place_on_front_left_corner(
            scene.AddAsset("a tall potted green plant in a planter"), facing="right")
        # the menu band over the counter: the yellow product sign + the illuminated diner sign
        room.place_on_wall_back_center(scene.AddAsset("a yellow retro milkshake wall sign",
                                                     asset_id=MILKSHAKE))
        room.place_on_wall_back_left(scene.AddAsset("an illuminated retro diner wall sign",
                                                    asset_id=DINER))
        room.place_on_wall_left_center(scene.AddAsset("a retro framed print of a diner scene",
                                                      asset_id=DINERART))
        room.place_window_floor_to_ceiling("front_wall", curtain=None)   # the storefront
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.015)

scene.export("fast_food_v1.blend")
