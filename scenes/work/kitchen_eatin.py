"""
Kitchen — "Single-Set Eat-In" (planner-driven modern eat-in kitchen).

LESSON (Kunal, 2026-06-30): make do with a SINGLE complete fitted kitchen set rather than gluing a
run + range + hood + fridge + island together. A complete set bundles cabinets + cooktop + chimney +
(sometimes fridge) + a separate island/countertop as ONE mesh, so it reads cohesively and we only add
the genuine GAPS. Component labels live in datasets/assets/kitchen_components.json (tagged via
tools/build_kitchen_tagger.py).

The chosen set `future/a3cead55` (straight) bundles: base+wall cabinets, cooktop, oven, sink, AND an
island/peninsula WITH bar stools — all one mesh. So the ONLY gap for an eat-in kitchen is the dining
nook (Kunal: the set's bundled stools cover bar seating, the nook covers dining). We deliberately do
NOT bolt on a separate hood/fridge — that's the very "gluing separate pieces" the lesson warns against.

Sizing: a kitchen set should MAX OUT the room height (floor-to-ceiling) — room interior height is
3.0 m (RoomGroup clamps HEIGHT to 3.0). We UNIFORM-scale the set by HEIGHT (`_fit_height`), not width
(width-fitting a tall run overshoots and pokes it through the ceiling — the earlier bug). For a set
whose island+stools are part of the mesh, we don't over-scale (that would inflate the stools), so we
fit to a realistic floor-to-ceiling cabinet height rather than literally the 3.0 m ceiling.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("KitchenEatIn", seed=31)

def _fit_height(o, target_h):
    """Scale UNIFORMLY so height == target_h (preserves the mesh's proportions). The right tool for
    a floor-to-ceiling kitchen set — never width-fit a tall composite (it overshoots the ceiling)."""
    w0, h0, d0 = o.get_width(), o.get_height(), o.get_depth()
    f = target_h / max(h0, 1e-6)
    o.scale_only_width(w0 * f); o.scale_only_height(h0 * f); o.scale_only_depth(d0 * f)
    return o

def _fit_width(o, target_w):
    w0, h0, d0 = o.get_width(), o.get_height(), o.get_depth()
    f = target_w / max(w0, 1e-6)
    o.scale_only_width(w0 * f); o.scale_only_height(h0 * f); o.scale_only_depth(d0 * f)
    return o

scene.prefetch_assets([
    "a complete modern kitchen unit with a light wood island and bar stools",
    "a round natural oak pedestal dining table",
    "a cream upholstered dining chair",
    "a round jute area rug",
    "a brass globe pendant light",
    "a low modern wood credenza sideboard",
    "a tall ceramic vase with dried pampas grass",
    "a small potted trailing plant in a ceramic pot",
    "a tall potted fiddle leaf fig tree in a woven basket",
    "a tall potted areca palm in a ceramic planter",
    "a large framed abstract botanical print",
])

# --- THE single complete fitted kitchen set: light-wood cabinets + cooktop + oven + sink +
# island WITH bar stools, all one mesh. Floor-to-ceiling (kept realistic so the bundled stools
# don't inflate). ---
kitchen = _fit_height(scene.AddAsset(
    "a complete modern kitchen unit with a light wood island and bar stools",
    asset_id="future/a3cead55-0587-48a6-ab1b-7ab38a1b590d"), 2.6)

# Pendant lighting (from the refine target). The island is part of the set mesh, so we anchor to
# the whole set; a very low density keeps the count (and area-light energy) down — checking how it lands.
with scene.RelativeGroup() as kitchen_grp:
    kitchen_grp.set_anchor(kitchen)
    kitchen_grp.add_lighting("a brass globe pendant light", density=0.05)

# --- The ONLY gap to add: an eat-in dining nook (round oak table, cream chairs, jute rug) ---
nook_table = _fit_width(scene.AddAsset(
    "a round natural oak pedestal dining table",
    asset_id="hssd/5d70cc76c99acee4513ec5f7fad497d2baebca9e"), 1.2)
with scene.AroundGroup(sparsity=0.4, jitter=0.2) as nook:
    nook.set_anchor(nook_table)
    nook.place_arc(3 * scene.AddAsset("a cream upholstered dining chair"), dist=0.1)
    nook.place_rug("a round jute area rug", size=1.3)

# --- Phase 2 — greenery + a styled console fill the empty room. The set's island/shelf surfaces are
# sealed inside the mesh (can't style them), so we furnish the ROOM around it: a credenza against the
# bare left wall (styled with a vase, books and a trailing plant) and tall plants softening corners. ---
with scene.RelativeGroup() as console_grp:
    console = scene.AddAsset("a low modern wood credenza sideboard")
    console_grp.set_anchor(console)
    console_grp.place_on_top([scene.AddAsset("a tall ceramic vase with dried pampas grass"),
                              scene.AddAsset("a woven basket filled with fresh fruit"),
                              scene.AddAsset("a small stack of hardcover books")])
palm_tree  = scene.AddAsset("a tall potted areca palm in a ceramic planter")
# the set bundles no fridge, so add a generous standalone one (kitchen fridges read small at real width)
fridge = _fit_height(scene.AddAsset("a large modern stainless steel refrigerator",
                                    asset_id="future/fe773221-7030-449d-8551-72ba28182192"), 2.0)

with scene.RoomGroup(modulate_scale=0.75, randomness=0.1) as room:
    # warm oak floor + soft sage walls (brief's accent) keep the room from blowing out under daylight.
    room.place_walls(floor_texture="light warm oak wood planks",
                     ceiling_texture="white", wall_texture="soft sage green")
    # the complete set on the back wall; a tall fridge sits on the right (kitchen-adjacent) wall
    room.place_on_back_wall_center(kitchen_grp)
    room.place_on_right_wall_left(fridge)
    room.place_door("right_wall", position="right")
    # a picture window (NO curtains) on the LEFT wall, adjacent to the kitchen — light by the prep zone
    room.place_window_picture("left_wall")
    # the seating wall (front): the nook + the side table (console) together
    room.place_on_front_wall_center(nook)
    room.place_on_front_wall_left(console_grp)
    # greenery softening a far corner
    room.place_on_back_left_corner(palm_tree)
    # Furniture clearance is opt-in (only doors get it automatically): reserve floor in front of the
    # sideboard so nothing — e.g. the fig tree — blocks access to it during the solve.
    room.add_clearance(console_grp, distance=0.6, dir="front")
    # wall decor on the seating wall: a round clock over the nook, art over the console
    room.place_on_wall_front_center(scene.AddAsset("a large round modern wall clock"))
    room.place_on_wall_front_left(scene.AddAsset("a large framed abstract botanical print"))

scene.export("kitchen.blend")

# (Planner-style collection collage available via room.render_collection(...) — see groups.py;
#  omitted from the per-iteration build to keep renders fast.)
