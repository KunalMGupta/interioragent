import os
import trimesh
from IDSDL.window import SceneProgObjectWall


class Door(SceneProgObjectWall):
    def __init__(self, WIDTH, HEIGHT, DEPTH):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.door_path = os.path.join(base_dir, "assets", "door.glb")

        uid = self.get_uid()
        self.mesh_path = f"tmp/door_{uid}.glb"
        super().__init__(WIDTH, HEIGHT, DEPTH)

    def add_door(self, wall, position):
        height_ratio = 0.7
        floor_clearance = 0.05
        wall_offset = 0.05

        door_width, _ = wall.get_partition_dimensions_by_label(position, margin=0.05)
        door_height = height_ratio * wall.height

        if door_width <= 0:
            raise ValueError(f"Invalid door width for position '{position}': {door_width}")
        if door_height <= 0:
            raise ValueError(f"Invalid door height for wall '{wall.name}': {door_height}")

        if door_width > 0.5 * door_height:
            door_width = 0.5 * door_height

        self.mesh = trimesh.load(self.door_path, force="mesh", process=False)
        self.mesh = self.scale(self.mesh, door_width, door_height, scale_depth=True)
        self.mesh = self.rotate(self.mesh, wall)

        pos = wall.get_partition_center_by_label(position, margin=0.0)
        pos = (pos[0], door_height / 2 - floor_clearance, wall_offset)
        pos = self.transform_position(pos, wall)

        self.mesh = self.translate(self.mesh, pos)
        self.mesh.export(self.mesh_path)