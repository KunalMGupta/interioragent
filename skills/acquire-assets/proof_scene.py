"""The fixture that produced `proof_render.png` — a shop-ingested asset behaving like a native one.

This is a RECIPE, not a live scene program: the four asset ids below were minted by one specific
shop run and were removed from the library afterwards (they were mangled duplicates of dataset
assets, kept only long enough to prove the pipeline). To re-run the proof, regenerate them and
paste the new ids in — they change every run, because the front and size come from a VLM.

    # 1. make 'internet-messy' inputs out of four known-good dataset assets: rotate each by a
    #    known angle about Z (90 / 180 / -90 / 0) and blow the units up 100x. Ground truth is
    #    then known exactly, and the pipeline is told none of it.
    # 2. python -m IDSDL.shop run --from-dir <messy_dir> --batch shops/proof
    # 3. answer anything on shops/proof/HELP.md, then: python -m IDSDL.shop apply shops/proof
    # 4. paste the four custom/<sha> ids here
    # 5. PYTHONPATH=. python workbench.py run skills/acquire-assets/proof_scene.py --phase 1

Why a rendered room and not an assertion: a wrong FRONT is invisible to every numeric check in
the codebase. The placement code will happily turn an asset's back to the room and report no
overlap, no rotation error, nothing. The only thing that can catch it is looking. So the render
IS the assertion — if the pipeline got the fronts right, the sofa's seat and the bookshelf's
OPENINGS face into the room; if it got the sizes right, the sofa reads as a sofa next to the
chair rather than a bus.

Result (proof_render.png, 2026-07-14): all four correct, and the build's own VLM pass came back
"no rotation / no wall overlap" — with three of the four fronts and all four sizes chosen with no
human in the loop.
"""
from IDSDL.phases import current_phase
from IDSDL.scene import SceneProgRoom

PHASE = current_phase()

scene = SceneProgRoom("ShopProof", seed=5)

# --- ingested by IDSDL.shop from the mangled set (see the batch's HELP.md) ----------------------
SHELF = "custom/f4d21e3533f697c6b7cf1ed3d2c599ae756589f2"   # answered by hand: front = panel 4
SOFA = "custom/c14628c2e62abce7b128289f0caa7a34e9f5d19e"    # auto: front panel 1, 2.35 m
CHAIR = "custom/c745760dbc580f45d341a31b83c4b3a1544bc66b"   # auto: front panel 3, 0.60 m
TABLE = "custom/674a52a7cd37355192ec62c63e33bddc242ac7d3"   # auto: front panel 1, 1.35 m

scene.prefetch_assets([
    "a dark wood wall bookshelf",
    "a charcoal three seat sofa",
    "a black lounge chair",
    "a wooden coffee table",
])

with scene.RelativeGroup() as seating:
    seating.set_anchor(scene.AddAsset("a charcoal three seat sofa", asset_id=SOFA))
    seating.place_on_front(scene.AddAsset("a wooden coffee table", asset_id=TABLE))

with scene.RoomGroup(modulate_scale=0.85, randomness=0.1) as room:
    room.place_walls(floor_texture="warm oak wood flooring",
                     ceiling_texture="soft white",
                     wall_texture="solid warm grey smooth uniform wall")
    # The bookshelf is the real test: it is a FLAT wall unit whose front and back look alike from
    # the side, and whose front was the one the VLM called wrong before the lighting fix.
    room.place_on_back_wall_center(scene.AddAsset("a dark wood wall bookshelf", asset_id=SHELF))
    room.place_on_front_wall_center(seating, facing="back")   # sofa faces the shelf
    room.place_on_left_wall_center(scene.AddAsset("a black lounge chair", asset_id=CHAIR),
                                   facing="right")
    room.place_door("right_wall", position="center")

    if PHASE >= 3:
        room.add_lighting("a flat round LED flush mount ceiling light", density=0.02,
                          modulate_scale=0.5)

scene.export("shop_proof.blend")
