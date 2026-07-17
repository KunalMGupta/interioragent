"""Multi-scene benchmark for the VLM proposal/critic scale solver.

Eight ensembles from settings we've built before (bedroom, ramen counter, dining
set, desk, living room, kitchen island, bakery display) plus one clean control.
Each scene injects KNOWN scale corruptions (both directions, 0.5x-2.4x) into some
members and leaves others clean; the solver must undo the corruption without
touching the clean members. Ground truth -> per-member recovery error.

Stages (so layouts can be eyeballed before spending LLM budget):
  python tools/scale_bench.py --stage layout            # build + render initial state only
  python tools/scale_bench.py --stage solve             # run the solver on every scene
  python tools/scale_bench.py --stage solve --scenes ramen_counter,desk_setup
  python tools/scale_bench.py --stage report            # aggregate summary table

Artifacts per scene in /work/tmp/scalebench/<scene>/ (solver outputs: initial.png,
final.png, evolution.png, match_log.json) + summary.json with the recovery metrics.

Run env:
  set -a && source /work/.env && set +a
  BLENDER_PATH=/work/blender-4.5.4-linux-x64/blender PYTHONPATH=/work \
    /opt/conda/envs/interioragent/bin/python tools/scale_bench.py --stage ...
"""
import argparse
import json
import os
import sys
sys.path.insert(0, "/work")

import numpy as np
import trimesh

ROOT = "/work/tmp/scalebench"

# satellites get one WIDE symmetric band (never hints at the answer's direction);
# anchors stay tight — the room is solved around them.
SAT_BOUNDS = (0.35, 2.2, 0.70, 1.40)

BED = "hssd/bb415be5d1f00f21489c63546acffc44d7c42933"
NIGHTSTAND = "hssd/830e2ed47548d8372294609fe7eeca11fb384b29"
TLAMP = "hssd/d0fcbd969e1e93da41a1f6561a02a803daf52aed"
COUNTER = "hssd/b1c9d7321512686e02f2d0be978056456479e14c"
STOOL = "hssd/612bd96482db881c089aa26e4a5a3c34ed702955"
RAMENBOWL = "hssd/e823268a535d8d7aaaf7db9e7cf769c689e7b4f0"
TEAPOT = "hssd/bbf4aa8262d369bc6b16a1669d7acf4c2a4d7b89"

# member: name, query, pin, role, count, place=(kind, ref), corrupt, note
# place kinds: anchor | flank(ref) | front_row(ref) | around(ref) | on_top(ref)
SCENES = [
    {"name": "bedroom_small",
     "desc": "a cozy bedroom ensemble: a double bed flanked by two matching "
             "nightstands, with a table lamp on each nightstand",
     "members": [
         {"name": "bed", "query": "a modern double bed with a wooden frame and a headboard",
          "pin": BED, "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "nightstand", "query": "a classic dark wood nightstand", "pin": NIGHTSTAND,
          "place": ("flank", "bed"), "count": 2, "corrupt": 0.62,
          "note": "two identical copies flank the bed"},
         {"name": "lamp", "query": "a classic urn table lamp with a pleated shade",
          "pin": TLAMP, "place": ("on_top", "nightstand"), "count": 2, "corrupt": 0.55,
          "note": "one on each nightstand"},
     ]},
    {"name": "ramen_counter",
     "desc": "a ramen bar: a long wooden counter with a row of stools on the "
             "customer side and ceramic ramen bowls and a teapot on the countertop",
     "members": [
         {"name": "counter", "query": "a long rustic warm wood bar counter with a paneled front",
          "pin": COUNTER, "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "stool", "query": "a round wooden backless bar stool with black metal legs",
          "pin": STOOL, "place": ("front_row", "counter"), "count": 4, "corrupt": 1.4,
          "note": "a straight row of four on the customer side"},
         {"name": "bowl", "query": "a ceramic ramen noodle bowl with chopsticks",
          "pin": RAMENBOWL, "place": ("on_top", "counter"), "count": 2, "corrupt": 2.4,
          "note": "serving bowls on the countertop"},
         {"name": "teapot", "query": "a small ceramic teapot", "pin": TEAPOT,
          "place": ("on_top", "counter"), "count": 1, "corrupt": 1.0,
          "note": "on the countertop"},
     ]},
    {"name": "dining_set",
     "desc": "a dining set: a dark wood dining table with four matching chairs "
             "around it and a candlestick holder at its center",
     "members": [
         {"name": "table", "query": "a round dark wood dining table",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "chair", "query": "a wooden dining chair with a high back",
          "place": ("around", "table"), "count": 4, "corrupt": 1.35,
          "note": "four identical chairs around the table"},
         {"name": "candlestick", "query": "a brass candlestick holder",
          "place": ("on_top", "table"), "count": 1, "corrupt": 1.8,
          "note": "at the table center"},
     ]},
    {"name": "desk_setup",
     "desc": "a home office desk setup: a wooden writing desk with an office "
             "chair, a desk lamp and a small potted plant on the desktop",
     "members": [
         {"name": "desk", "query": "a wooden writing desk",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "chair", "query": "a black office chair",
          "place": ("front_row", "desk"), "count": 1, "corrupt": 1.0,
          "note": "pulled up to the desk"},
         {"name": "desklamp", "query": "a small metal desk lamp",
          "place": ("on_top", "desk"), "count": 1, "corrupt": 1.9,
          "note": "on the desktop"},
         {"name": "plant", "query": "a small potted succulent plant",
          "place": ("on_top", "desk"), "count": 1, "corrupt": 0.5,
          "note": "on the desktop"},
     ]},
    {"name": "living_room",
     "desc": "a living room seating group: a three-seat sofa with a coffee table "
             "in front of it and a floor lamp beside it",
     "members": [
         {"name": "sofa", "query": "a modern grey fabric three seat sofa",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "coffeetable", "query": "a rectangular wooden coffee table",
          "place": ("front_row", "sofa"), "count": 1, "corrupt": 1.45,
          "note": "centered in front of the sofa"},
         {"name": "floorlamp", "query": "a modern floor lamp with a fabric shade",
          "place": ("flank", "sofa"), "count": 1, "corrupt": 0.7,
          "note": "standing beside the sofa"},
     ]},
    {"name": "kitchen_island",
     "desc": "a kitchen island scene: an island with a wooden countertop, a row "
             "of bar stools on one side and a kettle on the counter",
     "members": [
         {"name": "island", "query": "a kitchen island with a wooden countertop",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "stool", "query": "a metal bar stool with a round seat",
          "place": ("front_row", "island"), "count": 3, "corrupt": 0.65,
          "note": "a row of three at the island"},
         {"name": "kettle", "query": "a stainless steel kettle",
          "place": ("on_top", "island"), "count": 1, "corrupt": 1.8,
          "note": "on the countertop"},
     ]},
    {"name": "bakery_display",
     "desc": "a bakery display: a rustic wooden display table stacked with woven "
             "bread baskets, with a standing chalkboard sign beside it",
     "members": [
         {"name": "table", "query": "a rustic wooden bakery display table",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "basket", "query": "a woven bread basket with bread",
          "place": ("on_top", "table"), "count": 3, "corrupt": 2.0,
          "note": "three baskets on the display table"},
         {"name": "sign", "query": "a small standing chalkboard sign",
          "place": ("flank", "table"), "count": 1, "corrupt": 1.0,
          "note": "on the floor beside the table"},
     ]},
    {"name": "bedroom_control",
     "desc": "a cozy bedroom ensemble: a double bed flanked by two matching "
             "nightstands, with a table lamp on each nightstand",
     "members": [
         {"name": "bed", "query": "a modern double bed with a wooden frame and a headboard",
          "pin": BED, "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "nightstand", "query": "a classic dark wood nightstand", "pin": NIGHTSTAND,
          "place": ("flank", "bed"), "count": 2, "corrupt": 1.0,
          "note": "two identical copies flank the bed"},
         {"name": "lamp", "query": "a classic urn table lamp with a pleated shade",
          "pin": TLAMP, "place": ("on_top", "nightstand"), "count": 2, "corrupt": 1.0,
          "note": "one on each nightstand"},
     ]},
    # ---------------- wave 2: 15 groups, heavier small-object coverage ----------
    {"name": "coffee_shop",
     "desc": "a coffee shop service counter with an espresso machine and a coffee "
             "mug on the countertop and a cafe stool at the front",
     "members": [
         {"name": "counter", "query": "a wooden coffee shop service counter",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "espresso", "query": "a commercial espresso machine",
          "place": ("on_top", "counter"), "count": 1, "corrupt": 1.7,
          "note": "on the countertop"},
         {"name": "mug", "query": "a white ceramic coffee mug",
          "place": ("on_top", "counter"), "count": 1, "corrupt": 2.2,
          "note": "on the countertop"},
         {"name": "stool", "query": "a wooden cafe bar stool",
          "place": ("front_row", "counter"), "count": 2, "corrupt": 0.75,
          "note": "two at the customer side"},
     ]},
    {"name": "wine_display",
     "desc": "a wine display: a tall wooden wine rack with wine bottles on top "
             "and a bar cart beside it",
     "members": [
         {"name": "rack", "query": "a tall wooden wine rack",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "bottle", "query": "a wine bottle",
          "place": ("on_top", "rack"), "count": 3, "corrupt": 2.0,
          "note": "standing on top of the rack"},
         {"name": "cart", "query": "a wooden bar cart",
          "place": ("flank", "rack"), "count": 1, "corrupt": 0.7,
          "note": "beside the rack"},
     ]},
    {"name": "reading_corner",
     "desc": "a reading corner: a tall bookshelf with an armchair and a reading "
             "floor lamp beside it",
     "members": [
         {"name": "bookshelf", "query": "a tall wooden bookshelf",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "armchair", "query": "a comfortable upholstered armchair",
          "place": ("flank", "bookshelf"), "count": 1, "corrupt": 1.4,
          "note": "beside the shelf"},
         {"name": "floorlamp", "query": "a classic reading floor lamp",
          "place": ("front_row", "bookshelf"), "count": 1, "corrupt": 0.65,
          "note": "next to the armchair"},
     ]},
    {"name": "bathroom_vanity",
     "desc": "a bathroom vanity with a soap dispenser on the counter, a laundry "
             "basket beside it and a small step stool in front",
     "members": [
         {"name": "vanity", "query": "a modern bathroom vanity with a sink",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "soap", "query": "a soap dispenser bottle",
          "place": ("on_top", "vanity"), "count": 1, "corrupt": 2.5,
          "note": "on the vanity counter"},
         {"name": "basket", "query": "a woven laundry basket",
          "place": ("flank", "vanity"), "count": 1, "corrupt": 1.3,
          "note": "on the floor beside the vanity"},
         {"name": "stool", "query": "a small wooden step stool",
          "place": ("front_row", "vanity"), "count": 1, "corrupt": 0.7,
          "note": "in front of the vanity"},
     ]},
    {"name": "kids_room",
     "desc": "a kids room corner: a children's bed with a toy box beside it, a "
             "teddy bear on the bed and a small kids chair nearby",
     "members": [
         {"name": "bed", "query": "a children's bed with a colorful frame",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "toybox", "query": "a wooden toy storage box",
          "place": ("flank", "bed"), "count": 1, "corrupt": 1.6,
          "note": "beside the bed"},
         {"name": "teddy", "query": "a plush teddy bear toy",
          "place": ("on_top", "bed"), "count": 1, "corrupt": 0.4,
          "note": "sitting on the bed"},
         {"name": "kidschair", "query": "a small children's chair",
          "place": ("front_row", "bed"), "count": 1, "corrupt": 1.5,
          "note": "near the bed"},
     ]},
    {"name": "classroom_desk",
     "desc": "a classroom teacher station: a teacher desk with a student chair "
             "in front, a desk globe on the desktop and a wastebasket beside it",
     "members": [
         {"name": "desk", "query": "a classic wooden teacher desk",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "chair", "query": "a simple wooden school chair",
          "place": ("front_row", "desk"), "count": 1, "corrupt": 1.3,
          "note": "facing the desk"},
         {"name": "globe", "query": "a desk globe on a stand",
          "place": ("on_top", "desk"), "count": 1, "corrupt": 1.8,
          "note": "on the desktop"},
         {"name": "bin", "query": "a metal wastebasket",
          "place": ("flank", "desk"), "count": 1, "corrupt": 0.55,
          "note": "on the floor beside the desk"},
     ]},
    {"name": "reception",
     "desc": "an office reception: a reception desk with an office chair behind "
             "it, a desk telephone on the counter and a potted plant beside it",
     "members": [
         {"name": "desk", "query": "a modern office reception desk",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "chair", "query": "a black office chair",
          "place": ("front_row", "desk"), "count": 1, "corrupt": 0.7,
          "note": "at the desk"},
         {"name": "phone", "query": "a desk telephone",
          "place": ("on_top", "desk"), "count": 1, "corrupt": 2.2,
          "note": "on the counter"},
         {"name": "plant", "query": "a large potted plant in a ceramic pot",
          "place": ("flank", "desk"), "count": 1, "corrupt": 1.5,
          "note": "on the floor beside the desk"},
     ]},
    {"name": "gym_corner",
     "desc": "a home gym corner: a weight bench with a pair of dumbbells on it, "
             "an exercise ball beside it and a water bottle on the bench",
     "members": [
         {"name": "bench", "query": "a gym weight bench",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "dumbbell", "query": "a pair of dumbbells",
          "place": ("on_top", "bench"), "count": 1, "corrupt": 2.0,
          "note": "resting on the bench"},
         {"name": "ball", "query": "a rubber exercise ball",
          "place": ("flank", "bench"), "count": 1, "corrupt": 0.6,
          "note": "on the floor beside the bench"},
         {"name": "bottle", "query": "a plastic water bottle",
          "place": ("on_top", "bench"), "count": 1, "corrupt": 3.0,
          "note": "on the bench"},
     ]},
    {"name": "music_studio",
     "desc": "a music practice corner: an upright piano with a piano bench in "
             "front, a metronome on top and a guitar stand beside it",
     "members": [
         {"name": "piano", "query": "an upright piano",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "bench", "query": "a wooden piano bench",
          "place": ("front_row", "piano"), "count": 1, "corrupt": 1.4,
          "note": "in front of the piano"},
         {"name": "metronome", "query": "a wooden metronome",
          "place": ("on_top", "piano"), "count": 1, "corrupt": 2.5,
          "note": "on top of the piano"},
         {"name": "guitarstand", "query": "an acoustic guitar on a stand",
          "place": ("flank", "piano"), "count": 1, "corrupt": 0.7,
          "note": "beside the piano"},
     ]},
    {"name": "patio_set",
     "desc": "an outdoor patio set: a garden table with two outdoor chairs, a "
             "lantern on the table and a planter beside the set",
     "members": [
         {"name": "table", "query": "a round outdoor garden table",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "chair", "query": "an outdoor patio chair",
          "place": ("around", "table"), "count": 2, "corrupt": 0.7,
          "note": "two chairs at the table"},
         {"name": "lantern", "query": "a decorative outdoor lantern",
          "place": ("on_top", "table"), "count": 1, "corrupt": 2.0,
          "note": "on the table"},
         {"name": "planter", "query": "a large outdoor planter with a plant",
          "place": ("flank", "table"), "count": 1, "corrupt": 1.4,
          "note": "beside the set"},
     ]},
    {"name": "kitchen_prep",
     "desc": "a restaurant prep station: a stainless steel prep table with a "
             "stock pot and a chef knife on it and a trash bin beside it",
     "members": [
         {"name": "preptable", "query": "a stainless steel kitchen prep table",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "pot", "query": "a large stainless steel stock pot",
          "place": ("on_top", "preptable"), "count": 1, "corrupt": 1.9,
          "note": "on the table"},
         {"name": "knife", "query": "a chef knife",
          "place": ("on_top", "preptable"), "count": 1, "corrupt": 2.5,
          "note": "lying on the table"},
         {"name": "bin", "query": "a kitchen trash bin",
          "place": ("flank", "preptable"), "count": 1, "corrupt": 0.65,
          "note": "beside the table"},
     ]},
    {"name": "hotel_console",
     "desc": "a hotel lobby vignette: a marble console table with a table lamp "
             "and a flower vase on it and an ottoman in front",
     "members": [
         {"name": "console", "query": "a marble console table",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "lamp", "query": "an elegant table lamp",
          "place": ("on_top", "console"), "count": 1, "corrupt": 1.6,
          "note": "on the console"},
         {"name": "vase", "query": "a flower vase with flowers",
          "place": ("on_top", "console"), "count": 1, "corrupt": 0.45,
          "note": "on the console"},
         {"name": "ottoman", "query": "a round upholstered ottoman",
          "place": ("front_row", "console"), "count": 1, "corrupt": 1.45,
          "note": "in front of the console"},
     ]},
    {"name": "florist_stand",
     "desc": "a florist display: a wooden plant display stand with flower vases "
             "on it and a watering can on the floor beside it",
     "members": [
         {"name": "stand", "query": "a wooden plant display stand",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "vase", "query": "a flower vase with flowers",
          "place": ("on_top", "stand"), "count": 3, "corrupt": 2.0,
          "note": "three vases on the stand"},
         {"name": "wateringcan", "query": "a metal watering can",
          "place": ("flank", "stand"), "count": 1, "corrupt": 1.8,
          "note": "on the floor beside the stand"},
     ]},
    {"name": "home_bar",
     "desc": "a home bar: a bar cabinet with a cocktail shaker on top and two "
             "bar stools in front",
     "members": [
         {"name": "cabinet", "query": "a home bar cabinet",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "shaker", "query": "a stainless steel cocktail shaker",
          "place": ("on_top", "cabinet"), "count": 1, "corrupt": 2.4,
          "note": "on the cabinet top"},
         {"name": "stool", "query": "a leather bar stool",
          "place": ("front_row", "cabinet"), "count": 2, "corrupt": 1.35,
          "note": "two in front of the cabinet"},
     ]},
    {"name": "dining_control",
     "desc": "a dining set: a rectangular wooden dining table with four chairs "
             "and a fruit bowl at its center",
     "members": [
         {"name": "table", "query": "a rectangular wooden dining table",
          "role": "anchor", "place": ("anchor",), "count": 1, "corrupt": 1.0},
         {"name": "chair", "query": "a wooden dining chair",
          "place": ("around", "table"), "count": 4, "corrupt": 1.0,
          "note": "four chairs around the table"},
         {"name": "fruitbowl", "query": "a bowl of fruit",
          "place": ("on_top", "table"), "count": 1, "corrupt": 1.0,
          "note": "at the table center"},
     ]},
]

GAP = 0.08  # standard clearance between neighbouring pieces [m]


def bake(obj):
    """Object's world mesh WITH MATERIALS, re-based: centered in x/z, on y=0."""
    sc = trimesh.load(obj.mesh_path)
    if not isinstance(sc, trimesh.Scene):
        sc = trimesh.Scene(sc)
    sc.apply_transform(obj.get_world_transform().compute_matrix())
    lo, hi = sc.bounds
    sc.apply_translation([-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2])
    return sc


def scaled(mesh, f):
    m = mesh.copy()
    m.apply_transform(np.diag([f["s"], f["s"] * f["h"], f["s"], 1.0]))
    return m


def merge(master, member_scene, prefix):
    for i, g in enumerate(member_scene.dump()):
        master.add_geometry(g, geom_name=f"{prefix}_{i}")


def load_members(spec):
    """Retrieve + bake + corrupt every member's mesh. Returns solver members."""
    from IDSDL.scene import SceneProgRoom
    scene = SceneProgRoom(f"bench_{spec['name']}", seed=42)
    members = []
    for m in spec["members"]:
        obj = scene.AddAsset(m["query"], asset_id=m.get("pin"))
        mesh = bake(obj)
        if m["corrupt"] != 1.0:
            mesh.apply_scale(m["corrupt"])
        lo, hi = mesh.bounds
        members.append({
            "name": m["name"], "desc": m["query"],
            "role": m.get("role", "satellite"),
            "whd": (float(hi[0] - lo[0]), float(hi[1] - lo[1]), float(hi[2] - lo[2])),
            "mesh": mesh, "note": m.get("note"),
            "bounds": None if m.get("role") == "anchor" else SAT_BOUNDS,
            "corrupt": m["corrupt"], "count": m["count"], "place": m["place"],
            "model": obj.retrieval_model,
        })
    return members


def make_build_fn(members):
    """Generic layout: anchor at origin; satellites by placement rule, contacts
    recomputed from the scaled AABBs so any factor combination stays valid."""
    by_name = {m["name"]: m for m in members}

    def build(factors):
        sc = trimesh.Scene()
        placed = {}   # name -> list of (x, z, top_y, half_w, half_d)

        def put(mesh, name, x, y, z):
            inst = mesh.copy()
            inst.apply_translation([x, y, z])
            merge(sc, inst, f"{name}_{len(placed.get(name, []))}")

        anchor = next(m for m in members if m["role"] == "anchor")
        a = scaled(anchor["mesh"], factors[anchor["name"]])
        alo, ahi = a.bounds
        merge(sc, a, anchor["name"])
        placed[anchor["name"]] = [(0.0, 0.0, float(ahi[1]),
                                   float(ahi[0] - alo[0]) / 2, float(ahi[2] - alo[2]) / 2)]
        lanes = {}  # per-ref count of independent on_top member groups (lane offsets)

        for m in members:
            if m["role"] == "anchor":
                continue
            mesh = scaled(m["mesh"], factors[m["name"]])
            lo, hi = mesh.bounds
            w, h, d = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
            kind = m["place"][0]
            ref = placed[m["place"][1]]
            slots = []
            if kind == "flank":
                rx, rz, _, rhw, _ = ref[0]
                sides = [-1, 1][:m["count"]] if m["count"] > 1 else [1]
                slots = [(rx + s * (rhw + w / 2 + GAP), 0.0, rz) for s in sides]
            elif kind == "front_row":
                rx, rz, _, rhw, rhd = ref[0]
                n = m["count"]
                span = 2 * rhw
                xs = [rx - span / 2 + span * (i + 0.5) / n for i in range(n)]
                slots = [(x, 0.0, rz + rhd + d / 2 + GAP) for x in xs]
            elif kind == "around":
                rx, rz, _, rhw, rhd = ref[0]
                sides = [(0, 1), (0, -1), (-1, 0), (1, 0)][:m["count"]]
                slots = [(rx + sx * (rhw + w / 2 + GAP),
                          0.0,
                          rz + sz * (rhd + d / 2 + GAP)) for sx, sz in sides]
            elif kind == "on_top":
                if len(ref) > 1:      # one per ref instance (lamps on nightstands)
                    slots = [(r[0], r[2], r[1]) for r in ref[:m["count"]]]
                else:                 # spread along the ref top
                    rx, rz, rtop, rhw, _ = ref[0]
                    n = m["count"]
                    lane = lanes.get(m["place"][1], 0)
                    lanes[m["place"][1]] = lane + 1
                    off = [0.0, 0.45 * rhw, -0.45 * rhw][lane % 3]
                    span = 2 * rhw * 0.7
                    xs = [rx + off] if n == 1 else \
                        [rx - span / 2 + span * i / (n - 1) for i in range(n)]
                    slots = [(x, rtop, rz) for x in xs]
            else:
                raise ValueError(f"unknown placement {kind}")
            placed[m["name"]] = []
            for (x, y, z) in slots:
                put(mesh, m["name"], x, y, z)
                placed[m["name"]].append((x, z, y + float(h), w / 2, d / 2))

        # snug floor under everything
        lo, hi = sc.bounds
        floor = trimesh.creation.box(
            extents=[float(hi[0] - lo[0]) + 0.5, 0.02, float(hi[2] - lo[2]) + 0.5])
        floor.apply_translation([float(lo[0] + hi[0]) / 2, -0.01,
                                 float(lo[2] + hi[2]) / 2])
        sc.add_geometry(floor, geom_name="floor")
        return sc

    return build


def run_scene(spec, layout_only=False):
    from tools.scale_solver import solve_relative_scales, render_corner
    from tools.planar_regions import _GLB2BLEND, glb_to_blend

    out = os.path.join(ROOT, spec["name"])
    os.makedirs(out, exist_ok=True)
    members = load_members(spec)
    for m in members:
        w, h, d = m["whd"]
        print(f"  {m['name']:12s} corrupt={m['corrupt']:<4} model={m['model']} "
              f"{w:.2f}w x {h:.2f}h x {d:.2f}d m")
    build = make_build_fn(members)

    if layout_only:
        with open(os.path.join(out, "_glb2blend.py"), "w") as f:
            f.write(_GLB2BLEND)
        ident = {m["name"]: {"s": 1.0, "h": 1.0} for m in members}
        sc = build(ident)
        glb = os.path.join(out, "layout.glb")
        sc.export(glb)
        render_corner(glb_to_blend(glb, out), os.path.join(out, "layout.png"), sc.bounds)
        print(f"  layout render -> {out}/layout.png")
        return

    best, match_log = solve_relative_scales(
        members, build, spec["desc"], out, rounds=3, k=4)

    rows = []
    for m in members:
        f = best[m["name"]]
        ideal = 1.0 / m["corrupt"]
        eff_h = f["s"] * f["h"]
        rows.append({
            "member": m["name"], "role": m["role"], "corrupt": m["corrupt"],
            "ideal": round(ideal, 3), "found_s": f["s"], "found_h": f["h"],
            "eff_height": round(eff_h, 3),
            "height_err_pct": round(100 * abs(eff_h - ideal) / ideal, 1),
            "footprint_err_pct": round(100 * abs(f["s"] - ideal) / ideal, 1),
        })
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump({"scene": spec["name"], "rows": rows,
                   "matches": len(match_log),
                   "tiebreaks": sum(1 for r in match_log if r.get("tiebreak"))}, f,
                  indent=2)
    for r in rows:
        print(f"  {r['member']:12s} ideal={r['ideal']:<5} -> s={r['found_s']} "
              f"h={r['found_h']} (eff height {r['eff_height']}); "
              f"height err {r['height_err_pct']}%")


def report():
    print(f"{'scene':17s} {'member':13s} {'corrupt':>7} {'ideal':>6} "
          f"{'eff_h':>6} {'hErr%':>6} {'fpErr%':>7}")
    tot, n = 0.0, 0
    for spec in SCENES:
        p = os.path.join(ROOT, spec["name"], "summary.json")
        if not os.path.exists(p):
            print(f"{spec['name']:17s} (no summary yet)")
            continue
        d = json.load(open(p))
        for r in d["rows"]:
            print(f"{spec['name']:17s} {r['member']:13s} {r['corrupt']:>7} "
                  f"{r['ideal']:>6} {r['eff_height']:>6} {r['height_err_pct']:>6} "
                  f"{r['footprint_err_pct']:>7}")
            if r["role"] != "anchor":
                tot += r["height_err_pct"]
                n += 1
        print(f"{'':17s} ({d['matches']} matches, {d['tiebreaks']} tiebreaks)")
    if n:
        print(f"\nmean satellite height error: {tot / n:.1f}% over {n} members")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["layout", "solve", "report"], required=True)
    ap.add_argument("--scenes", default=None,
                    help="comma-separated subset of scene names")
    args = ap.parse_args()
    if args.stage == "report":
        report()
        return
    wanted = set(args.scenes.split(",")) if args.scenes else None
    for spec in SCENES:
        if wanted and spec["name"] not in wanted:
            continue
        print(f"\n=== {spec['name']} ===")
        try:
            run_scene(spec, layout_only=(args.stage == "layout"))
        except Exception as e:
            print(f"  SCENE FAILED: {e!r}")


if __name__ == "__main__":
    main()
