from IDSDL.scene import SceneProgRoom

scene_dense = SceneProgRoom("dense")
with scene_dense.AroundGroup(sparsity=1.0) as seating:
        table = scene_dense.AddAsset("a round coffee table")
        chair = scene_dense.AddAsset("an upholstered accent chair")
        seating.set_anchor(table)
        seating.place_circle(objects=4 * chair)
with scene_dense.RoomGroup() as room:
    room.place_on_center(seating, facing="front")
scene_dense.export("test.blend")