"""
Museum — "Harmonic Gallery Rhythm" (planner target: tmp/plan_A_museum_gallery_room__sculpture/plan.png).

Look (from the plan): a calm, light-controlled sculpture gallery. Warm ivory walls and a polished
pale stone floor; a field of white marble PLINTHS carrying busts and statues holds the middle of the
room; the long walls carry large framed paintings (classical + warm colour-field abstracts) with a
low leather VIEWING BENCH beneath each run, and a third bench on the axis at the entrance; black
track SPOTLIGHT bars wash the art. Palette: ivory plaster, pale stone, white marble, cognac leather,
bronze/black frames, ochre + rust canvases.

Zone map (gallery axis runs front<->back; LONG walls = LEFT + RIGHT):
  - CENTRE             = the SCULPTURE FIELD: six marble plinths (3x2) carrying six distinct works.
  - LEFT + RIGHT walls = the gallery ART RUNS (5 large works), each with a low VIEWING BENCH beneath.
  - FRONT (short)      = the visitors' BENCH on the axis + the entrance door (short walls stay light).
  - BACK (short)       = the FOCAL classical portrait + a tall palm in each corner.

Why the sculptures stand in the MIDDLE and not along the walls (the load-bearing layout lesson):
every `place_on_wall_*` artwork must keep its wall patch visible, so floor furniture near a wall and
tall enough to occlude a painting is slid along the wall out of the art's span. v3 flanked the aisle
with two RANKS of plinths under the art runs — what the plan collage shows — and the build refused it:
    WARNING: 'GridGroup' occludes wall-hung '<painting>' on left_wall and no along-wall slot can
             clear it — move one of them to a different wall/slot
A rank spanning the length of a wall occludes EVERY slot on it, so a long wall cannot carry the
sculptures AND the paintings. The sculptures therefore stand in the centre of the floor (where museum
sculptures actually stand) and the perimeter belongs to the art — which is what the retrieved
procedural signature prescribed all along: "perimeter art walls; central sculpture field".
The two SIDE BENCHES then do real structural work: at 0.47 m they sit below the paintings without
occluding them, they hold the shell wide enough to keep the central field out of the 0.75 m wall band,
and they are what a real gallery puts under a picture wall.

WALL ART — TWO CORE BUGS FIXED + A DUD-MESH LIST (all found by an isolated 4-wall probe,
`scenes/work/_art_wall_test.py`; a control painting now hangs face-out on all four walls):
  1. `place_on_wall_freeform` put RIGHT-wall pieces at x=0 (the LEFT wall) and FRONT-wall pieces at
     z~0 (the BACK wall), rotated to face away — they hung backwards inside the opposite wall and
     rendered as BLACK BARS. Only back/left were ever exercised by a shipped scene, so it survived.
  2. On side walls it packed and SIZED each piece by its DEPTH — for a canvas, its 2 cm THICKNESS —
     so every painting on a left/right wall collapsed to a sliver. (back_wall correctly used width.)
  Both fixed in IDSDL/groups.py::place_on_wall_freeform.
  3. NOT a placement bug: several dataset canvases are DUDS whose picture does not survive export —
     they hang as an EMPTY FRAME or a BLACK PANEL on any wall. Struck off: hssd/b9c49bfc (empty),
     future/7b0ad909 (black), hssd/6a669a56 (empty), future/4d8d0fa9 (empty). CERTIFIED good: the
     six pinned below. An empty frame in a render = a dud mesh or a reversed front; flipping it with
     front_cache tells you which (if 180 gives you a BLACK backing, the mesh itself is the problem).

NOTE — velvet rope stanchions are DROPPED (asset gap). The dataset has no barrier post + rope (best
match 0.44: a bare white metal rod; the picker itself reports "no true brass barrier post with red
rope is present"), and the DSL cannot span a rope between two posts. A lone pole reads as a random
rod, not a stanchion, so the ropes are cut rather than smuggled in (corridor's "drop the accent, don't
smuggle it"). A stanchion .glb is the single worthwhile ingest if we want the cordons back.

No window: a light-controlled gallery legitimately has none (and a bare pane renders as a black night
void — the executive_office/lobby lesson). The track spots carry the whole light layer.

Phase 1: the plinth field + the three benches + the door + the shell (floor layout, room shape).
Phase 2: the busts/statues seated on their plinths + the corner palms.
Phase 3: the wall art runs + the focal portrait + the track spotlights.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()   # 1 anchors / 2 surfaces / 3 walls+mood (default 3 = all)

scene = SceneProgRoom("Museum", seed=27)

# --- pinned assets (audited previews, gate 3) ---
_PLINTH  = "future/58d2d3ee-5743-41e7-92dd-92d646e84938"   # plain white/veined marble plinth (the ONLY true pedestal:
                                                           # "pedestal/plinth" queries otherwise route to architectural COLUMNS)
# SIX distinct BARE sculptures — one per plinth, so the gallery shows six works, not three shown twice.
# (v2 used future/552692f0, whose catalog caption reads "white sculpture of a stylized human figure":
#  in-render it is a FLOWER-CROWNED FACE VASE, kitsch, not a museum bust. Caption != mesh — found only
#  by looking at the build. Replaced with the two genuine classical busts below.)
_BUST_A  = "hssd/0d65e4a8e88bbd6cba57f3ce115e0e85d54da9c3" # classic white bust, smooth features
_BUST_B  = "hssd/74463d608aaebeac19efc6c0609ea64599368a56" # white marble bust of a woman
_STATUE  = "hssd/a858cdf5b8cb7e6317133eac88be532e0615c04c" # classical figure holding a trident
_FLUTE   = "hssd/40e02b56e04ffa8731991ba50249a1f1a0f0d81e" # white figure of a female flute player
_SEATED  = "future/86e05ca5-1cb6-4d34-a8bc-f094e4500f78"   # abstract white seated figure (the modern piece)
_FIGURE  = "hssd/54142b3debb81cb03d03c8b021f959b78e166091" # white minimalist standing figure (the modern piece;
                                                           # replaces a "marbled torso" that rendered as a small PINK
                                                           # object — the one non-white work broke the marble palette)
_BENCH   = "hssd/8466b0bcd50deb8ff1a03e8d90bef577a44b201e" # oak bench + saddle-brown leather top (the plan's cognac bench:
                                                           # v2's "tan leather basketweave" mesh rendered as a flat ORANGE MAT)
_FOCAL   = "future/d8f2e7b8-c201-4b29-aec9-7fe402dc1b5c"   # classical portrait of a woman (the focal back-wall work)
_CLASSIC = "hssd/5d4c5918e8f7d301d36d21970d18786716dbbb1d" # classical figure scene, dark frame
_FLORAL  = "hssd/54c900dd531bc8517ffe514964f6666190d3344a" # framed floral oil, wooden frame (CERTIFIED: renders its
                                                           # canvas — see the mesh-certification probe below)
# _LAND = "future/7b0ad909-2f00-4f34-a176-966d990f84ab" — DUD, do not use: the ornate landscape renders
#   BLACK (its back) on the front/right walls. It happened to render on the LEFT wall, which is exactly
#   how a dud sneaks into a scene — so it is struck off rather than relied on.
_ART_A   = "hssd/950c82d2ac17a015cc5e063b664f78c965247743" # vibrant abstract colour-field
# _ART_B = "hssd/b9c49bfce9696145e4328cd3e23b5b3e9eeb5b78" — DEAD MESH, do not use. Its catalog preview
#   is a warm ochre watercolour, but in-engine it hangs as an EMPTY FRAME: the canvas texture does not
#   survive export. Confirmed it is NOT the usual reversed-front bug (living_room_cozy v2) — front_cache
#   180 turned the empty frame into a BLACK panel (i.e. we were already seeing its front). Swapped out
#   for _LAND. Lesson: an empty frame in the render means either a reversed front OR a texture-less mesh,
#   and flipping tells you which — if 180 gives you the dark backing, the mesh itself is the problem.
_ART_C   = "hssd/e63f2f68c0d0de795e8a71d0f834b637502bb7db" # bold abstract, geometric shapes
# NOTE: the bust query's #4/#6 (future/0a48b81e, future/1847b0ef) are busts with a pedestal BAKED IN —
# the "SET trap". They would double my plinth, so every sculpture pinned above is a BARE piece.

scene.prefetch_assets([
    "a tall potted palm tree in a planter",
    "a slim black linear LED track spotlight ceiling light bar",
])

PLINTH_W, PLINTH_H = 0.45, 1.05   # a real plinth BOX: square-ish in plan, sculpture base at eye-ish level

# ============================ the display unit: ONE plinth + ONE sculpture ============================
# place_on_top ALWAYS seats onto the group's ANCHOR (living_room_cozy v3: a lamp landed on an armchair
# seat because the chair was the anchor). So the PLINTH is the anchor and the sculpture goes on top of
# it — never the other way round.
def display(sculpture):
    p = scene.AddAsset("a white marble museum display pedestal", asset_id=_PLINTH)
    # The mesh is a SLENDER block (aspect ~1:4). Height-retargeting alone (v1) gave a 0.26 m-wide
    # slab — it rendered as a thin post and left the room reading cavernous. A plinth is just a
    # rectangular box, so distorting its aspect is free: set the WIDTH uniformly, then squash the
    # HEIGHT to display height. Result: a proper 0.45 x 1.05 m plinth with a real footprint.
    p.scale(PLINTH_W)
    p.scale_only_height(PLINTH_H)
    with scene.RelativeGroup() as g:
        g.set_anchor(p)
        if PHASE >= 2:
            g.place_on_top(sculpture)
    return g

# THREE plinths per rank (v1 used two: four skinny plinths could not fill the shell they forced, and
# the VLM voted 0.57). A rank of three also reads as a RHYTHM down the aisle rather than a stray pair.
#
# SIZING: aim each sculpture at ~0.55-0.75 m so plinth+work totals ~1.6-1.8 m (a viewing height that
# reads as a museum). v2 shrank everything with modulate_scale=0.5/0.6 and got 0.3 m FIGURINES marooned
# on big plinths — the busts (0.56-0.58 m native) and the trident figure (0.68 m) are already the right
# size, so they ship UNSCALED; only the two natively-tall pieces are brought down.
def _bust_a(): return scene.AddAsset("a classic white marble bust sculpture", asset_id=_BUST_A)                       # 0.56 m
def _bust_b(): return scene.AddAsset("a white marble bust of a woman", asset_id=_BUST_B)                              # 0.58 m
def _statue(): return scene.AddAsset("a white classical statue of a figure holding a trident", asset_id=_STATUE)      # 0.68 m
def _flute():  return scene.AddAsset("an elegant white statue of a female flute player", asset_id=_FLUTE,
                                     modulate_scale=0.8)                                                              # 0.92 -> 0.74 m
def _seated(): return scene.AddAsset("an abstract white sculpture of a seated figure", asset_id=_SEATED)              # 0.48 m
def _figure(): return scene.AddAsset("a white minimalist sculpture of a standing figure", asset_id=_FIGURE,
                                     modulate_scale=0.5)                                                              # 1.56 -> 0.78 m

# THE SCULPTURE FIELD — six plinths as a 3x2 grid down the CENTRE of the room.
#
# v3 put the plinths in the LEFT/RIGHT floor thirds (ranks flanking the aisle, art on the wall above
# them — what the plan collage shows). The build refused it:
#     WARNING: 'GridGroup' occludes wall-hung '<painting>' on left_wall and no along-wall slot can
#              clear it — move one of them to a different wall/slot
# Every `place_on_wall_*` artwork must keep its wall patch visible, and a rank of 1.6-1.8 m plinths
# running the length of a wall occludes EVERY slot on it — so the long walls cannot carry both the
# sculptures and the paintings. The DSL is right and the retrieved signature said so from the start:
# "perimeter art walls; central sculpture field". So the sculptures move to the middle of the floor
# (where museum sculptures actually stand) and the walls are left to the art.
sculpture_units = [display(_bust_a()), display(_statue()), display(_figure()),
                   display(_seated()), display(_bust_b()), display(_flute())]
# sparsity 0.65 (was 0.5): at 0.5 the six plinths crowded each other and the flanking benches — a
# gallery needs air BETWEEN the works, not just around the field.
with scene.GridGroup(sparsity=0.65, randomness=0.08) as sculpture_field:
    sculpture_field.place_grid(sculpture_units, cols=2)

# ============================ CENTRE: the visitors' bench (on the axis) ============================
# THE BENCHES — one on the axis + one under each art run.
#
# The native mesh is 1.2 m — too short to hold a gallery's axis. Grow it with a UNIFORM scale(), not
# width=: width= pins that ONE axis, which is how v2 stretched the old bench into a 1.9 x 0.38 m plank
# that rendered as a flat orange MAT on the floor. scale(1.5) keeps the proportions and lands a proper
# 1.5 m bench at a 0.47 m seat height.
def gallery_bench():
    b = scene.AddAsset("a long backless bench with a saddle brown leather seat", asset_id=_BENCH)
    b.scale(1.5)
    with scene.RelativeGroup() as g:
        g.set_anchor(b)
    return g

def art(asset_id, desc, hung_width):
    """A canvas sized for the wall.

    NEVER size wall art with `width=` — it pins that ONE axis and so DISTORTS the canvas: width=2.0
    turned a 0.9x0.6 m painting into a 2.0x0.6 m letterbox, and `_place_on_wall`'s scale computer
    faithfully preserves that broken aspect (it optimises for the target width while holding w/h), so
    the piece landed as a 0.72 x 0.18 m SLIVER on the wall. `scale()` is uniform: it sets the width and
    carries the height along with it, keeping the painting a painting.

    Sizes are chosen so each canvas lands just under the core's ~1 m height ceiling (the scale
    computer penalises h > 1 by 10*(h-1)^2, which no scene-level call can override): a 1.9-aspect
    canvas maxes out at ~1.9 m wide, a square one at ~1.1 m. That is what "as large as this DSL hangs"
    means today — genuinely monumental art needs a core change (see NOTES).
    """
    a = scene.AddAsset(desc, asset_id=asset_id)
    a.scale(hung_width)
    return a


bench = gallery_bench()                       # the visitors' bench, on the room's axis
# The two SIDE benches are what let the art runs exist at all: they occupy the left/right floor thirds
# with furniture SHORT enough (0.47 m) to sit UNDER a painting without occluding it ("a console below a
# painting stays"), which (a) holds the shell wide enough that the central sculpture field stays clear
# of the 0.75 m wall band, and (b) is exactly what a real gallery puts under its picture walls.
side_benches = 2 * gallery_bench()

# ============================ ROOM ============================
# A gallery is DELIBERATELY sparse — the open aisle IS the category (corridor/laundromat: expect the
# RoomProportions shrink vote to persist and decline it once the render reads right). v1 at 0.95 voted
# 0.57; the real fix was furniture MASS (bigger plinths, 6 of them, a longer bench), not scale alone —
# that alone moved the vote to 0.75. Once the side benches arrived the vote went QUIET ("no rescale")
# — the room was never too big, it was under-furnished. Nudged 0.80 -> 0.88 because the renders (my
# eye, not the vote) showed the plinths crowding the benches: a gallery must breathe.
with scene.RoomGroup(modulate_scale=0.88, randomness=0.08) as room:
    room.place_walls(floor_texture="polished beige marble floor",
                     ceiling_texture="smooth white plaster ceiling",
                     wall_texture="warm ivory plaster wall")
    # the sculpture field owns the middle of the floor; the walls are left clear for the art
    room.place_on_center(sculpture_field)
    # a viewing bench under each art run (low enough to sit below a painting), turned to face the
    # sculptures; and the visitors' bench on the axis at the entrance end, looking down the gallery
    room.place_on_left(side_benches[0], facing="right")
    room.place_on_right(side_benches[1], facing="left")
    room.place_on_front(bench, facing="back")
    # the door is the only thing on the front short wall (short walls stay light)
    room.place_door("front_wall", position="right")

    if PHASE >= 2:
        room.place_on_back_left_corner(scene.AddAsset("a tall potted palm tree in a planter"))
        room.place_on_back_right_corner(scene.AddAsset("a tall potted palm tree in a planter"))

    if PHASE >= 3:
        # THE GALLERY RUNS — the long walls do the heavy hang (library/corridor), pre-scaled via
        # width= so the mount height clears the ceiling ([[wall-art-mount-height]]).
        # THE HANG — `place_on_wall_freeform`, NOT the slot verbs. This is the whole reason the art
        # finally reads as MUSEUM art:
        #   * the slot verbs (place_on_wall_<wall>_<pos>) hard-cap a piece at
        #     `min(target, (WALL_LEN/3) * 0.6)` = a FIFTH of the wall (groups.py:_place_on_wall), and
        #     they IGNORE the width= you pass. v4 asked for 2.0 m canvases and got ~0.8 m ones — the
        #     paintings read as postcards adrift on a big wall, which is not a gallery.
        #   * freeform instead passes each piece's OWN width as the target and spaces the run evenly
        #     along the wall, only shrinking if the pieces TOTAL more than half the wall. So fewer,
        #     bigger works win — which is exactly how a gallery hangs: two commanding canvases per
        #     long wall rather than six little ones.
        # (A ~1 m height ceiling still applies via the scale computer's h>1 penalty, so these land as
        #  broad landscape-format canvases. Genuinely monumental art needs a core change — see NOTES.)
        room.place_on_wall_freeform("left_wall", [art(_CLASSIC, "a large framed classical oil painting of figures", 1.5),
                                                  art(_FLORAL, "a framed floral still life oil painting", 1.0)])
        room.place_on_wall_freeform("right_wall", [art(_ART_A, "a large framed vibrant abstract colour field painting", 1.9),
                                                   art(_ART_C, "a large framed bold abstract painting", 1.1)])
        # the focal work caps the sightline down the aisle
        room.place_on_wall_freeform("back_wall", [art(_FOCAL, "a large framed classical portrait painting", 0.9)])
        # warm gallery spots: a FLAT track bar (never a hanging fixture — the chandelier blowout).
        # DENSITY IS A COUNT, AND THE COUNT SCALES WITH FLOOR AREA — so the published ladder (a ~56 m2
        # bookstore wants 0.015) runs the WRONG WAY on a small room: at 0.015 this ~20 m2 gallery got
        # exactly ONE track bar (report: ceiling_lights=1), which is not a lit gallery. 0.08 gives a
        # run of ~4 bars washing the art. The starfield lint is the arbiter and stays clean.
        room.add_lighting("a slim black linear LED track spotlight ceiling light bar", density=0.08)

scene.export("museum.blend")
