"""Chemistry lab — the acquisition dial at `acquire="high"` (search, then GENERATE).

The companion to chapel_acquire_mid.py, and the case that forces the second rung of the ladder.
A chemistry lab is the worst case for this dataset: it is an interior full of equipment that a
FURNITURE dataset has no reason to contain, and — as we found the hard way — that Sketchfab's free
tier does not really carry either. So `mid` is not enough here; the gaps have to be generated.

Measured before writing this (top-1 similarity, and what the dataset would hand you instead):

    HAVE 0.58  a chemical storage cabinet     -> a white locker cabinet          (close enough)
    GAP  0.45  a chemistry fume hood          -> A KITCHEN CHIMNEY HOOD
    GAP  0.45  a laboratory centrifuge        -> a stainless steel autoclave
    GAP  0.50  a laboratory microscope        -> a surgical microscope            (nearly right)

At `acquire="low"` this room silently contains a kitchen extractor hood, and no lint, no
constraint and no VLM pass in this codebase would ever complain — the hood is a perfectly good
mesh, it is just not a fume hood. At `"high"` the retriever measures the gap, fails to find one on
Sketchfab (we checked: "fume hood" returns 3 hits and none survive triage), escalates to Meshy,
generates one, normalizes it, verifies its front, and keeps it ONLY if the gap closes.

That last clause is the one that matters. An earlier run generated a "fume hood" that the captioner
read as a "recessed fireplace insert" — the gap did not close, so it was rolled back out of the
library and the room fell back to the chimney hood. A generated asset is not automatically a good
asset, and this scene is where that gets decided.

COSTS MONEY: every generation spends Meshy credits (~5 preview + ~10 refine). The budget cap
(IDSDL_ACQUIRE_BUDGET, default 6) is what stops a bad prompt from emptying the account.

    PYTHONPATH=. python workbench.py run scenes/work/lab_acquire_high.py --phase 1
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()

# acquire="high": dataset -> Sketchfab -> Meshy. Still gated on a MEASURED gap at every step.
scene = SceneProgRoom("LabAcquireHigh", seed=13, acquire="high")

scene.prefetch_assets([
    "a chemical storage cabinet",     # HAVE — the dial must leave this alone
    "a stainless steel work table",   # HAVE — the bench the instruments sit on
    "a chemistry fume hood",          # GAP (the dataset offers a kitchen chimney hood)
    "a laboratory centrifuge",        # GAP
    "a laboratory microscope",        # GAP
])

# The bench: a dataset work table carrying two instruments the dataset does not have.
with scene.RelativeGroup() as bench:
    bench.set_anchor(scene.AddAsset("a stainless steel work table"))
    if PHASE >= 2:
        bench.place_on_top(scene.AddAsset("a laboratory microscope"))
        bench.place_on_top(scene.AddAsset("a laboratory centrifuge"))

# modulate_scale=1.2 — acquired lab equipment arrives at true scale (the fume hood is 1.55 m), so
# the room needs air around it or a wall-centre camera ends up inside the hood (the chapel taught
# this the hard way).
with scene.RoomGroup(modulate_scale=1.2, randomness=0.1) as room:
    room.place_walls(floor_texture="pale grey seamless vinyl lab flooring",
                     ceiling_texture="white acoustic ceiling tiles",
                     wall_texture="solid pale grey smooth uniform wall")

    # --- PHASE 1: all the floor mass ---
    # The fume hood is the test asset. It goes on the back wall but OFF-CENTRE (back-left), so the
    # back-wall camera — which sits at the wall centre — is not staring into it (bakery/closet
    # camera rule; acquired assets are big enough that this matters).
    room.place_on_back_wall_left(scene.AddAsset("a chemistry fume hood"), facing="front")
    room.place_on_center(bench, facing="front")
    room.place_on_left_wall_center(scene.AddAsset("a chemical storage cabinet"), facing="right")
    room.place_door("front_wall", position="right")

    if PHASE >= 3:
        room.add_lighting("a rectangular recessed LED ceiling panel light", density=0.04,
                          modulate_scale=0.8)

scene.export("lab_acquire_high.blend")

from IDSDL.shop.acquire import report            # noqa: E402
for a in report():
    print(f"[lab] acquired: {a}")
