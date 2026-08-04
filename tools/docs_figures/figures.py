"""Figure programs for the docs site — one entry per figure (or before/after pair).

Each build_fn mirrors the code snippet shown on the docs page. Where the
natural-language retrieval picks a poor mesh for illustration purposes, the call
pins a proven asset with asset_id — the docs snippet text stays natural-language.
Output names match the filenames referenced by the docs markdown.
"""
FIGURES = {}


def fig(name, mode="group", views=("persp", "top"), seed=7, vlm=False):
    def reg(fn):
        FIGURES[name] = {"build": fn, "mode": mode, "views": views, "seed": seed,
                         "vlm": vlm}
        return fn
    return reg


# ------------------------------------------------------------------
# Object registration
# ------------------------------------------------------------------

@fig("reg_single", views=("persp",))
def reg_single(scene):
    sofa = scene.AddAsset("a modern gray sofa")
    scene.bind(sofa)


@fig("reg_copies", views=("persp", "top"))
def reg_copies(scene):
    with scene.GridGroup(sparsity=0.4) as row:
        chair = scene.AddAsset("an elegant dining chair with a cushioned seat")
        row.place_row(4 * chair)
    scene.bind(row)


@fig("reg_rotation", views=("persp", "top"))
def reg_rotation(scene):
    table = scene.AddAsset("a rectangular wooden coffee table")
    chair_default = scene.AddAsset("a cozy lounge chair")
    chair_rotated = scene.AddAsset("a cozy lounge chair")
    chair_facing = scene.AddAsset("a cozy lounge chair")
    chair_default.set_location(0.0, 0, 0.0)
    chair_rotated.set_location(1.5, 0, 0.0)
    chair_rotated.set_rotation(90)
    chair_facing.set_location(3.0, 0, 0.0)
    table.set_location(3.1, 0, 1.4)
    chair_facing.face_towards(table)
    for o in (table, chair_default, chair_rotated, chair_facing):
        scene.bind(o)


@fig("reg_scaling", views=("persp", "top"))
def reg_scaling(scene):
    default = scene.AddAsset("a modern gray sofa")
    modulated = scene.AddAsset("a modern gray sofa", modulate_scale=0.5)
    narrow = scene.AddAsset("a modern gray sofa", width=1.1)
    shallow = scene.AddAsset("a modern gray sofa", depth=0.55)
    cursor = 0.0
    for o in (default, modulated, narrow, shallow):
        w = o.get_width()
        o.set_location(cursor + w / 2, 0, 0.0)
        cursor += w + 0.55
        scene.bind(o)


@fig("retrieval_custom", views=("persp",))
def retrieval_custom(scene):
    cart = scene.AddAsset("a street food cart with a striped awning")
    scene.bind(cart)


# ------------------------------------------------------------------
# RelativeGroup
# ------------------------------------------------------------------

@fig("rel_basic")
def rel_basic(scene):
    with scene.RelativeGroup() as seating:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        table = scene.AddAsset("a rectangular wooden coffee table")
        chair_l = scene.AddAsset("a cozy lounge chair")
        chair_r = scene.AddAsset("a cozy lounge chair")
        seating.set_anchor(sofa)
        seating.place_on_front(table)
        seating.place_on_left(chair_l)
        seating.place_on_right(chair_r)
    scene.bind(seating)


@fig("rel_corners")
def rel_corners(scene):
    with scene.RelativeGroup() as bedside:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        bedside.set_anchor(bed)
        ns = scene.AddAsset("a small wooden nightstand with a drawer")
        nightstands = 4 * ns
        bedside.place_on_back_left(nightstands[0])
        bedside.place_on_back_right(nightstands[1])
        bedside.place_on_front_left(nightstands[2])
        bedside.place_on_front_right(nightstands[3])
    scene.bind(bedside)


@fig("rel_further")
def rel_further(scene):
    # identical chairs so the near-vs-further distance contrast is unmistakable
    with scene.RelativeGroup() as g:
        table = scene.AddAsset("a rectangular wooden coffee table")
        g.set_anchor(table)
        chairs = 2 * scene.AddAsset("a cozy lounge chair")
        g.place_on_left(chairs[0])            # near ring
        g.place_on_left_further(chairs[1])    # further ring: clears the near chair
    scene.bind(g)


@fig("rel_top")
def rel_top(scene):
    with scene.RelativeGroup() as console:
        sideboard = scene.AddAsset("a mid-century wooden sideboard")
        console.set_anchor(sideboard)
        console.place_on_top([
            scene.AddAsset("a modern table lamp with a white shade"),
            scene.AddAsset("a small decorative ceramic vase"),
        ])
    scene.bind(console)


@fig("rel_rug")
def rel_rug(scene):
    with scene.RelativeGroup() as bed_area:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        bed_area.set_anchor(bed)
        bed_area.place_on_back_left(
            scene.AddAsset("a small wooden nightstand with a drawer"))
        bed_area.place_on_back_right(
            scene.AddAsset("a small wooden nightstand with a drawer"))
        bed_area.place_rug("a soft neutral area rug", size=0.9)
    scene.bind(bed_area)


# ------------------------------------------------------------------
# AroundGroup
# ------------------------------------------------------------------

@fig("around_circle")
def around_circle(scene):
    with scene.AroundGroup() as seating:
        table = scene.AddAsset("a round wooden coffee table")
        chair = scene.AddAsset("an upholstered accent chair")
        seating.set_anchor(table)
        seating.place_circle(objects=4 * chair)
    scene.bind(seating)


@fig("around_rectilinear")
def around_rectilinear(scene):
    with scene.AroundGroup() as dining:
        table = scene.AddAsset(
            "a large rectangular dining table with a dark wood finish")
        chair = scene.AddAsset("an elegant dining chair with a cushioned seat")
        dining.set_anchor(table)
        dining.place_rectilinear(
            longer_side1=3 * chair, longer_side2=3 * chair,
            shorter_side1=1 * chair, shorter_side2=1 * chair,
        )
    scene.bind(dining)


@fig("around_arc")
def around_arc(scene):
    with scene.AroundGroup(sparsity=0.5) as seating:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        chair = scene.AddAsset("a cozy lounge chair")
        seating.set_anchor(sofa)
        seating.place_arc(objects=3 * chair)
    scene.bind(seating)


def _sparsity_circle(scene, sparsity):
    with scene.AroundGroup(sparsity=sparsity) as seating:
        table = scene.AddAsset("a round wooden coffee table")
        chair = scene.AddAsset("an upholstered accent chair")
        seating.set_anchor(table)
        seating.place_circle(objects=6 * chair)
    scene.bind(seating)


@fig("around_sparsity_dense", views=("top",))
def around_sparsity_dense(scene):
    _sparsity_circle(scene, 0.0)


@fig("around_sparsity_sparse", views=("top",))
def around_sparsity_sparse(scene):
    _sparsity_circle(scene, 1.0)


# ------------------------------------------------------------------
# GridGroup
# ------------------------------------------------------------------

@fig("grid_row")
def grid_row(scene):
    with scene.GridGroup(sparsity=0.5) as g:
        chair = scene.AddAsset("a standard classroom chair")
        g.place_row(4 * chair)
    scene.bind(g)


@fig("grid_grid")
def grid_grid(scene):
    with scene.GridGroup(sparsity=0.5) as classroom:
        chair = scene.AddAsset("a standard classroom chair")
        classroom.place_grid(6 * chair, cols=3)
    scene.bind(classroom)


@fig("grid_rectilinear")
def grid_rectilinear(scene):
    with scene.GridGroup(sparsity=0.4) as border:
        chair = scene.AddAsset("an elegant dining chair with a cushioned seat")
        border.place_rectilinear(
            width1=3 * chair, width2=3 * chair,
            depth1=2 * chair, depth2=2 * chair,
        )
    scene.bind(border)


@fig("grid_randomness")
def grid_randomness(scene):
    with scene.GridGroup(sparsity=0.5, randomness=0.9) as g:
        chair = scene.AddAsset("a standard classroom chair")
        g.place_grid(9 * chair, cols=3)
    scene.bind(g)


@fig("grid_arc")
def grid_arc(scene):
    # pinned: the natural pick has an off-center mesh origin (floats above the floor)
    fireplace = scene.AddAsset(
        "a brick fireplace with a glowing fire",
        asset_id="hssd/afbe5bf0c84434cd80351009cc16cc741d9900e2")
    fireplace.set_location(0, -fireplace.get_aabb()[0, 1], -2.4)  # rest on the floor
    with scene.GridGroup(sparsity=0.4) as seating:
        chair = scene.AddAsset("a cozy lounge chair")
        seating.place_arc(5 * chair, towards=fireplace)
    scene.bind(fireplace)
    scene.bind(seating)


# ------------------------------------------------------------------
# RoomGroup
# ------------------------------------------------------------------

@fig("room_walls", mode="room")
def room_walls(scene):
    with scene.RoomGroup() as room:
        with scene.RelativeGroup() as seating:
            sofa = scene.AddAsset("a modern 3-seat sofa")
            table = scene.AddAsset("a rectangular wooden coffee table")
            seating.set_anchor(sofa)
            seating.place_on_front(table)
        room.place_on_back_wall_center(seating, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


@fig("room_grid_points", mode="room")
def room_grid_points(scene):
    # orientation-bearing objects: the corner/edge facing heuristics are visible
    with scene.RoomGroup() as room:
        table = scene.AddAsset("a round wooden coffee table")
        room.place_on_center(table)
        chair = scene.AddAsset("an upholstered accent chair")
        chairs = 4 * chair
        room.place_on_back_left_corner(chairs[0])
        room.place_on_back_right_corner(chairs[1])
        room.place_on_front_left_corner(chairs[2])
        room.place_on_front_right_corner(chairs[3])
        lounge = scene.AddAsset("a cozy lounge chair")
        lounges = 2 * lounge
        room.place_on_left(lounges[0])
        room.place_on_right(lounges[1])
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


@fig("room_wall_art", mode="room")
def room_wall_art(scene):
    with scene.RoomGroup() as room:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        painting = scene.AddAsset("a large colorful abstract painting")
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_wall_back_center(painting)
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


# ------------------------------------------------------------------
# Hierarchical
# ------------------------------------------------------------------

@fig("hier_reuse", mode="room")
def hier_reuse(scene):
    # a frozen cluster duplicated with `*`, exactly like a single asset
    with scene.RelativeGroup() as nightstand_area:
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        lamp = scene.AddAsset("a modern table lamp with a white shade")
        nightstand_area.set_anchor(nightstand)
        nightstand_area.place_on_top(lamp)

    with scene.RelativeGroup() as bed_area:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        bed_area.set_anchor(bed)
        bed_area.place_on_back_left(nightstand_area)
        bed_area.place_on_back_right(1 * nightstand_area)   # a fresh copy

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(bed_area, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


@fig("hier_nested", mode="room")
def hier_nested(scene):
    with scene.AroundGroup() as dining:
        table = scene.AddAsset("a large rectangular dining table")
        chair = scene.AddAsset("an elegant dining chair")
        dining.set_anchor(table)
        dining.place_rectilinear(longer_side1=2 * chair, longer_side2=2 * chair)

    with scene.RelativeGroup() as seating:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        coffee = scene.AddAsset("a rectangular wooden coffee table")
        seating.set_anchor(sofa)
        seating.place_on_front(coffee)

    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating, facing="front")
        room.place_on_front_wall_center(dining, facing="back")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


# ------------------------------------------------------------------
# Gradient constraints (before/after pairs, top views)
# ------------------------------------------------------------------

def _basic_room(scene, w=6.0, d=5.0, h=3.0):
    return scene.BasicRoomGroup(w, d, h)


def _walls(room):
    room.place_walls(
        floor_texture="light oak wood floor",
        ceiling_texture="smooth white ceiling",
        wall_texture="warm off-white painted wall",
    )


def _con_overlap(scene, solve):
    sofa = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    chair = scene.AddAsset("a cozy lounge chair")
    with _basic_room(scene) as room:
        if not solve:
            room.grad_solver = None
        room.place([sofa, table, chair],
                   positions=[(2.3, sofa.get_height() / 2, 2.5),
                              (2.5, table.get_height() / 2, 2.5),
                              (2.7, chair.get_height() / 2, 2.5)],
                   rotations=[0, 0, 0])
        _walls(room)


@fig("con_overlap_before", mode="room", views=("top",))
def con_overlap_before(scene):
    _con_overlap(scene, solve=False)


@fig("con_overlap_after", mode="room", views=("top",))
def con_overlap_after(scene):
    _con_overlap(scene, solve=True)


def _con_oob(scene, solve):
    sofa = scene.AddAsset("a modern 3-seat sofa")
    with _basic_room(scene, w=5.0) as room:
        if not solve:
            room.grad_solver = None
        room.place([sofa], positions=[(5.2, sofa.get_height() / 2, 2.5)], rotations=[0])
        _walls(room)


@fig("con_outofbounds_before", mode="room", views=("top",))
def con_outofbounds_before(scene):
    _con_oob(scene, solve=False)


@fig("con_outofbounds_after", mode="room", views=("top",))
def con_outofbounds_after(scene):
    _con_oob(scene, solve=True)


def _con_clearance(scene, hook):
    # a lounge chair crowding the front of a wardrobe: the doors need room to swing
    cabinet = scene.AddAsset("a wide wooden wardrobe with double doors")
    chair = scene.AddAsset("a cozy lounge chair")
    with _basic_room(scene, w=4.5, d=4.0) as room:
        room.place([cabinet, chair],
                   positions=[(2.25, cabinet.get_height() / 2, 3.5),
                              (2.25, chair.get_height() / 2, 2.55)],
                   rotations=[180, 0])
        _walls(room)
        if hook:
            room.add_clearance(cabinet, distance=0.8, dir="front")


@fig("con_clearance_before", mode="room", views=("top",))
def con_clearance_before(scene):
    _con_clearance(scene, hook=False)


@fig("con_clearance_after", mode="room", views=("top",))
def con_clearance_after(scene):
    _con_clearance(scene, hook=True)


def _con_access(scene, hook):
    # a coffee table drifting out of reach of the sofa is pulled back within reach
    sofa = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    with _basic_room(scene) as room:
        room.place([sofa, table],
                   positions=[(3.0, sofa.get_height() / 2, 1.0),
                              (4.6, table.get_height() / 2, 3.6)],
                   rotations=[0, 0])
        _walls(room)
        if hook:
            room.add_access(sofa, table, min_dist=0.3, max_dist=0.45, dir="front")


@fig("con_access_before", mode="room", views=("top",))
def con_access_before(scene):
    _con_access(scene, hook=False)


@fig("con_access_after", mode="room", views=("top",))
def con_access_after(scene):
    _con_access(scene, hook=True)


def _con_visibility(scene, hook):
    sofa = scene.AddAsset("a modern 3-seat sofa")
    tv = scene.AddAsset("a wide TV console cabinet with a television on top")
    plant = scene.AddAsset("a potted plant with bright green leaves",
                           asset_id="future/c80cdc2c-d9d5-4da5-8c9d-b54fadf43003")
    with _basic_room(scene) as room:
        if not hook:
            room.grad_solver = None
        room.place([sofa, tv, plant],
                   positions=[(3.0, sofa.get_height() / 2, 0.8),
                              (3.0, tv.get_height() / 2, 4.3),
                              (3.0, plant.get_height() / 2, 2.6)],
                   rotations=[0, 180, 0])
        _walls(room)
        if hook:
            room.add_visibility(sofa, tv)


@fig("con_visibility_before", mode="room", views=("top",))
def con_visibility_before(scene):
    _con_visibility(scene, hook=False)


@fig("con_visibility_after", mode="room", views=("top",))
def con_visibility_after(scene):
    _con_visibility(scene, hook=True)


# ------------------------------------------------------------------
# SentenceASCIIGenerator
# ------------------------------------------------------------------

@fig("ascii_hi")
def ascii_hi(scene):
    with scene.SentenceASCIIGenerator() as ascii_gen:
        plant = scene.AddAsset("a small succulent plant in a pot")
        ascii_gen.place(plant, "HI")
    scene.bind(ascii_gen)


# ------------------------------------------------------------------
# Motif groups
# ------------------------------------------------------------------

@fig("extra_stack", views=("persp", "front"))
def extra_stack(scene):
    with scene.StackGroup() as stack:
        crate = scene.AddAsset("a wooden storage crate")
        stack.place_stack(3 * crate)
    scene.bind(stack)


@fig("extra_pyramid")
def extra_pyramid(scene):
    with scene.PyramidGroup() as pyr:
        crate = scene.AddAsset("a wooden storage crate")
        pyr.place_pyramid(6 * crate)
    scene.bind(pyr)


@fig("extra_pile")
def extra_pile(scene):
    with scene.PileGroup() as pile:
        cushion = scene.AddAsset("a square floor cushion")
        pile.place_pile(7 * cushion, spread=0.8)
    scene.bind(pile)


@fig("extra_symmetry")
def extra_symmetry(scene):
    with scene.SymmetryGroup() as sym:
        bed = scene.AddAsset("a queen-sized bed with a wooden frame")
        sym.set_anchor(bed)
        nightstand = scene.AddAsset("a small wooden nightstand with a drawer")
        sym.place_flanking(nightstand)
    scene.bind(sym)


@fig("extra_facing")
def extra_facing(scene):
    with scene.FacingGroup() as g:
        table = scene.AddAsset("a rectangular wooden coffee table")
        g.set_anchor(table)
        chair = scene.AddAsset("a cozy lounge chair")
        g.place_facing_rows(2 * chair, 2 * chair)
    scene.bind(g)


@fig("extra_rings")
def extra_rings(scene):
    with scene.RingsGroup(sparsity=0.3) as g:
        table = scene.AddAsset("a large round dining table with a dark wood finish")
        g.set_anchor(table)
        chair = scene.AddAsset("an upholstered accent chair")
        g.place_rings([4 * chair, 8 * chair])
    scene.bind(g)


# ------------------------------------------------------------------
# Legacy page figures
# ------------------------------------------------------------------

@fig("installation", mode="room", views=("persp",))
def installation(scene):
    with scene.RelativeGroup() as seating_area:
        sofa = scene.AddAsset("a modern gray sofa")
        # pinned: the natural pick ships with a baked-in tabletop tray that the
        # two-asset program can't explain to a first-time reader
        coffee_table = scene.AddAsset(
            "a wooden coffee table",
            asset_id="hssd/369c08f9b552f142e00f496b5c08f00324550496")
        seating_area.set_anchor(sofa)
        seating_area.place_on_front(coffee_table)
    with scene.RoomGroup() as room:
        room.place_on_back_wall_center(seating_area, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


@fig("rendered_views", views=("front", "right", "back", "left"))
def rendered_views(scene):
    sofa = scene.AddAsset("a modern gray sofa")
    scene.bind(sofa)


@fig("reg_lighting", mode="room", views=("persp",))
def reg_lighting(scene):
    # add_lighting is a ceiling-fixture verb: pendants centred over the caller
    sofa = scene.AddAsset("a modern gray sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    with _basic_room(scene, w=5.0, d=4.0) as room:
        room.place([sofa, table],
                   positions=[(2.5, sofa.get_height() / 2, 1.0),
                              (2.5, table.get_height() / 2, 2.2)],
                   rotations=[0, 0])
        room.add_lighting(desc="a simple pendant light", density=0.4)
        _walls(room)


# ------------------------------------------------------------------
# RoomGroup: against-the-wall, wall-mounted diversity, doors & windows
# ------------------------------------------------------------------

@fig("room_against_wall", mode="room")
def room_against_wall(scene):
    with scene.RoomGroup() as room:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        console = scene.AddAsset("a narrow wooden console table")
        bookshelf = scene.AddAsset("a tall wooden bookshelf")
        dresser = scene.AddAsset("a mid-century wooden sideboard")
        room.place_on_back_wall_center(sofa, facing="front")
        room.place_on_front_wall_center(console, facing="back")
        room.place_on_left_wall_center(bookshelf, facing="right")
        room.place_on_right_wall_center(dresser, facing="left")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


@fig("room_wall_tv", mode="room")
def room_wall_tv(scene):
    with scene.RoomGroup() as room:
        console = scene.AddAsset("a low wooden media console")
        tv = scene.AddAsset("a flat screen television")
        mirror = scene.AddAsset("a round framed wall mirror")
        shelf = scene.AddAsset("a small floating wall shelf")
        room.place_on_back_wall_center(console, facing="front")
        room.place_on_wall_back_center(tv)
        room.place_on_wall_left_center(mirror)
        room.place_on_wall_left_left(shelf)
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


@fig("room_wall_gallery", mode="room")
def room_wall_gallery(scene):
    with scene.RoomGroup() as room:
        bench = scene.AddAsset("a wooden entryway bench")
        room.place_on_back_wall_center(bench, facing="front")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )
        art = scene.AddAsset("a small framed art print")
        pieces = 5 * art
        room.place_on_wall_freeform("back_wall", pieces)


@fig("room_doors_windows", mode="room")
def room_doors_windows(scene):
    with scene.RoomGroup() as room:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        room.place_on_right_wall_center(sofa, facing="left")
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )
        room.place_door(wall="left_wall", position="left")
        room.place_window_picture(wall="back_wall")
        room.place_window_standard(wall="left_wall", position="right")


# ------------------------------------------------------------------
# Parameter sweeps (composited into arrow strips by composites.py)
# ------------------------------------------------------------------

def _sweep_around_jitter(scene, jitter):
    with scene.AroundGroup(sparsity=0.3, jitter=jitter) as seating:
        table = scene.AddAsset("a round wooden coffee table")
        chair = scene.AddAsset("an upholstered accent chair")
        seating.set_anchor(table)
        seating.place_circle(objects=6 * chair)
    scene.bind(seating)


@fig("sweep_around_jitter_00", views=("top",))
def sweep_around_jitter_00(scene):
    _sweep_around_jitter(scene, 0.0)


@fig("sweep_around_jitter_05", views=("top",))
def sweep_around_jitter_05(scene):
    _sweep_around_jitter(scene, 0.5)


@fig("sweep_around_jitter_10", views=("top",))
def sweep_around_jitter_10(scene):
    _sweep_around_jitter(scene, 1.0)


@fig("around_sparsity_mid", views=("top",))
def around_sparsity_mid(scene):
    _sparsity_circle(scene, 0.5)


def _sweep_grid_sparsity(scene, sparsity):
    with scene.GridGroup(sparsity=sparsity) as g:
        chair = scene.AddAsset("a standard classroom chair")
        g.place_grid(9 * chair, cols=3)
    scene.bind(g)


@fig("sweep_grid_sparsity_00", views=("top",))
def sweep_grid_sparsity_00(scene):
    _sweep_grid_sparsity(scene, 0.0)


@fig("sweep_grid_sparsity_04", views=("top",))
def sweep_grid_sparsity_04(scene):
    _sweep_grid_sparsity(scene, 0.4)


@fig("sweep_grid_sparsity_08", views=("top",))
def sweep_grid_sparsity_08(scene):
    _sweep_grid_sparsity(scene, 0.8)


def _sweep_grid_randomness(scene, randomness):
    with scene.GridGroup(sparsity=0.2, randomness=randomness) as g:
        chair = scene.AddAsset("a standard classroom chair")
        g.place_grid(9 * chair, cols=3)
    scene.bind(g)


@fig("sweep_grid_randomness_00", views=("top",))
def sweep_grid_randomness_00(scene):
    _sweep_grid_randomness(scene, 0.0)


@fig("sweep_grid_randomness_05", views=("top",))
def sweep_grid_randomness_05(scene):
    _sweep_grid_randomness(scene, 0.5)


@fig("sweep_grid_randomness_09", views=("top",))
def sweep_grid_randomness_09(scene):
    _sweep_grid_randomness(scene, 0.9)


def _sweep_rings_jitter(scene, jitter):
    with scene.RingsGroup(sparsity=0.3, jitter=jitter) as g:
        table = scene.AddAsset("a large round dining table with a dark wood finish")
        g.set_anchor(table)
        chair = scene.AddAsset("an upholstered accent chair")
        g.place_rings([4 * chair, 8 * chair])
    scene.bind(g)


@fig("sweep_rings_jitter_00", views=("top",))
def sweep_rings_jitter_00(scene):
    _sweep_rings_jitter(scene, 0.0)


@fig("sweep_rings_jitter_10", views=("top",))
def sweep_rings_jitter_10(scene):
    _sweep_rings_jitter(scene, 1.0)


def _sweep_room_randomness(scene, randomness):
    with scene.RoomGroup(randomness=randomness) as room:
        table = scene.AddAsset("a round wooden coffee table")
        room.place_on_center(table)
        chair = scene.AddAsset("an upholstered accent chair")
        chairs = 4 * chair
        room.place_on_back_left(chairs[0])
        room.place_on_back_right(chairs[1])
        room.place_on_front_left(chairs[2])
        room.place_on_front_right(chairs[3])
        room.place_walls(
            floor_texture="light oak wood floor",
            ceiling_texture="smooth white ceiling",
            wall_texture="warm off-white painted wall",
        )


@fig("sweep_room_randomness_00", mode="room", views=("top",))
def sweep_room_randomness_00(scene):
    _sweep_room_randomness(scene, 0.0)


@fig("sweep_room_randomness_05", mode="room", views=("top",))
def sweep_room_randomness_05(scene):
    _sweep_room_randomness(scene, 0.5)


@fig("sweep_room_randomness_10", mode="room", views=("top",))
def sweep_room_randomness_10(scene):
    _sweep_room_randomness(scene, 1.0)


# ------------------------------------------------------------------
# VLM constraints: a proportion failure, judged and corrected live
# ------------------------------------------------------------------

def _vlm_proportions(scene):
    # main-op placement: the VLM critique renders BEFORE delayed verbs like
    # place_on_top run, so the oversized object must be a main placement
    with scene.RelativeGroup() as seating:
        sofa = scene.AddAsset("a modern 3-seat sofa")
        seating.set_anchor(sofa)
        table = scene.AddAsset("a low rectangular oak coffee table",
                               modulate_scale=3.2)
        seating.place_on_front(table)
    scene.bind(seating)


@fig("vlm_proportions_before", views=("persp",))          # VLM stubbed: no rescale
def vlm_proportions_before(scene):
    _vlm_proportions(scene)


@fig("vlm_proportions_after", views=("persp",), vlm=True)  # real VLM critique runs
def vlm_proportions_after(scene):
    _vlm_proportions(scene)
