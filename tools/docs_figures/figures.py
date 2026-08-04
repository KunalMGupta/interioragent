"""Figure programs for the docs site — one entry per figure (or before/after pair).

Each build_fn mirrors the code snippet shown on the docs page. Where the
natural-language retrieval picks a poor mesh for illustration purposes, the call
pins a proven asset with asset_id — the docs snippet text stays natural-language.
Output names match the filenames referenced by the docs markdown.
"""
FIGURES = {}


def fig(name, mode="group", views=("persp", "top"), seed=7):
    def reg(fn):
        FIGURES[name] = {"build": fn, "mode": mode, "views": views, "seed": seed}
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
    with scene.RelativeGroup() as g:
        table = scene.AddAsset("a rectangular wooden coffee table")
        g.set_anchor(table)
        g.place_on_left(scene.AddAsset("a cozy lounge chair"))
        g.place_on_left_further(scene.AddAsset("a tall floor lamp"))
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
    lectern = scene.AddAsset("a wooden lectern podium")
    lectern.set_location(0, 0, -1.6)
    with scene.GridGroup(sparsity=0.4) as audience:
        chair = scene.AddAsset("a standard classroom chair")
        audience.place_arc(6 * chair, towards=lectern)
    scene.bind(lectern)
    scene.bind(audience)


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
    with scene.RoomGroup() as room:
        table = scene.AddAsset("a round wooden coffee table")
        room.place_on_center(table)
        for corner in ("back_left", "back_right", "front_left", "front_right"):
            plant = scene.AddAsset("a potted plant with bright green leaves",
                                   asset_id="future/c80cdc2c-d9d5-4da5-8c9d-b54fadf43003")
            getattr(room, f"place_on_{corner}_corner")(plant)
        room.place_on_left(scene.AddAsset("a tall floor lamp"))
        room.place_on_right(scene.AddAsset("a tall floor lamp"))
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
    sofa = scene.AddAsset("a modern 3-seat sofa")
    table = scene.AddAsset("a rectangular wooden coffee table")
    with _basic_room(scene) as room:
        room.place([sofa, table],
                   positions=[(3.0, sofa.get_height() / 2, 1.2),
                              (3.0, table.get_height() / 2, 2.1)],
                   rotations=[0, 0])
        _walls(room)
        if hook:
            room.add_clearance(sofa, distance=0.8, dir="front")


@fig("con_clearance_before", mode="room", views=("top",))
def con_clearance_before(scene):
    _con_clearance(scene, hook=False)


@fig("con_clearance_after", mode="room", views=("top",))
def con_clearance_after(scene):
    _con_clearance(scene, hook=True)


def _con_access(scene, hook):
    bed = scene.AddAsset("a queen-sized bed with a wooden frame")
    ns = scene.AddAsset("a small wooden nightstand with a drawer")
    with _basic_room(scene) as room:
        room.place([bed, ns],
                   positions=[(2.2, bed.get_height() / 2, 2.5),
                              (5.2, ns.get_height() / 2, 4.3)],
                   rotations=[0, 0])
        _walls(room)
        if hook:
            room.add_access(bed, ns, min_dist=0.05, max_dist=0.25, dir="sides")


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
        coffee_table = scene.AddAsset("a wooden coffee table")
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


@fig("reg_lighting", views=("persp",))
def reg_lighting(scene):
    sofa = scene.AddAsset("a modern gray sofa")
    sofa.add_lighting(desc="a simple pendant light", density=0.5)
    scene.bind(sofa)
