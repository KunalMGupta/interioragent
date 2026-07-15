"""Chapel — the acquisition dial at `acquire="mid"` (search Sketchfab for real gaps).

THIS SCENE IS A TEST OF THE DIAL, and it is built so that both halves of the dial are exercised in
one room: some of what it asks for the dataset HAS, and some it demonstrably does NOT.

Measured against the library before this scene was written (top-1 similarity, and what the dataset
would actually hand you):

    HAVE 0.70  a wooden church pew bench      -> a white wooden pew bench          (correct)
    HAVE 0.67  a tall wrought iron candle stand -> a black cast iron candlestick   (correct)
    GAP  0.52  a stone baptismal font         -> a "cement stone vessel"
    GAP  0.49  a church altar table           -> a wooden pedestal with an eagle finial
    GAP  0.45  a church organ                 -> AN ORNATE BLACK GRAND PIANO
    GAP  0.41  a prayer kneeler               -> the same eagle pedestal again

That grand piano is the point of the whole feature. At `acquire="low"` (the default) this scene
builds with a piano standing in for the organ and nobody is ever told. At `"mid"` the retriever
measures the gap, goes and finds an organ, normalizes it, verifies its front on a re-render, and
only keeps it IF the gap actually closes — otherwise it puts the piano back and says so.

The two HAVE assets are the control: the dial must not touch them. Acquisition is slow (minutes
per gap) and this scene will take a while on its first build; afterwards the assets are in the
library and the seed cache, and it builds at normal speed.

    PYTHONPATH=. python workbench.py run scenes/work/chapel_acquire_mid.py --phase 1
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()

# acquire="mid": the DATASET GETS FIRST REFUSAL on every query. Only a measured gap (top-1
# similarity < 0.55) sends the retriever out to Sketchfab. "high" would also let it GENERATE.
scene = SceneProgRoom("ChapelAcquireMid", seed=11, acquire="mid")

scene.prefetch_assets([
    "a wooden church pew bench",          # HAVE — the dial must leave this alone
    "a tall wrought iron candle stand",   # HAVE — ditto
    "a church altar table",               # GAP
    "a stone baptismal font",             # GAP
    "a church organ",                     # GAP (the dataset offers a grand piano)
])

# The altar is the hero, on the back wall, facing the congregation.
altar = scene.AddAsset("a church altar table")

# Two rows of pews down the middle, facing the altar. Pews come from the DATASET. Extra sparsity
# so the nave is DEEP: the acquired altar shrine came back at its true 2 m scale, and a wall-centre
# camera looking down a short nave face-plants straight into it (the bakery/closet camera rule).
with scene.GridGroup(sparsity=1.1, randomness=0.1) as pews:
    pews.place_grid(8 * scene.AddAsset("a wooden church pew bench"), cols=2)

# modulate_scale=1.5 — a chapel, not a chapel-shaped closet. Acquired ecclesiastical assets are
# BIG (altar shrine 2.1 m, pipe organ 1.6 m); the room has to be grand enough to stand back from
# them or every wall-centre camera ends up inside one.
with scene.RoomGroup(modulate_scale=1.5, randomness=0.1) as room:
    room.place_walls(floor_texture="worn grey stone flagstone floor",
                     ceiling_texture="pale lime plaster ceiling",
                     wall_texture="solid pale cream lime plaster wall")

    # --- PHASE 1: all the floor mass ---
    room.place_on_back_wall_center(altar, facing="front")     # faces the congregation
    room.place_on_center(pews, facing="back")                 # pews face the altar
    room.place_on_back_left_corner(scene.AddAsset("a tall wrought iron candle stand"))
    room.place_on_back_right_corner(scene.AddAsset("a tall wrought iron candle stand"))
    room.place_on_left_wall_center(scene.AddAsset("a stone baptismal font"), facing="right")
    # The organ against a side wall — the asset the dataset would have made a grand piano.
    room.place_on_right_wall_center(scene.AddAsset("a church organ"), facing="left")
    room.place_door("front_wall", position="center")

    if PHASE >= 3:
        room.place_window_standard("left_wall", position="center",
                                   curtain=None)
        room.add_lighting("a simple wrought iron ceiling pendant light", density=0.02,
                          modulate_scale=0.6)

scene.export("chapel_acquire_mid.blend")

# What did the dial actually do? Silence here would mean the dataset carried the whole room.
from IDSDL.shop.acquire import report            # noqa: E402
for a in report():
    print(f"[chapel] acquired: {a}")
