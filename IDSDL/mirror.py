"""
Floor-to-ceiling mirrored wall.

Architectural companion to the floor-to-ceiling *window* (see window.py): a flat, reflective
panel sized to a whole wall, mounted flush against it. Unlike a window it does NOT cut the wall
(a mirror hangs on the wall, it isn't an opening), and unlike the retrieved "gym wall mirror"
prop it spans the entire wall as one surface.

The reflection is a real Cycles reflection: the exported glb carries a metallic, near-zero
roughness PBR material, which the gltf importer maps onto a Blender Principled BSDF
(Metallic=1, Roughness~0) -- a mirror under the Cycles engine the renderer already uses.

Build (pure trimesh, like Window's own mesh) happens at scene-compile time; _build_blend then
imports the glb as a wall_object with its baked-in material.
"""
import trimesh
import numpy as np

from IDSDL.window import SceneProgObjectWall


class Mirror(SceneProgObjectWall):
    # a thin panel; near-full-bleed with a hair of reveal so corners don't clip adjacent walls
    THICKNESS = 0.04
    WIDTH_FRAC = 0.98
    HEIGHT_FRAC = 0.99
    PROUD = 0.03      # stand this far proud of the wall (toward the room) to avoid z-fighting

    def __init__(self, WIDTH, HEIGHT, DEPTH):
        super().__init__(WIDTH, HEIGHT, DEPTH)
        uid = self.get_uid()
        self.mesh_path = f"tmp/mirror{uid}.glb"

    def add_mirror_floor_to_ceiling(self, wall):
        # wall.width is the along-wall span (room WIDTH for back/front, room DEPTH for left/right);
        # wall.height is the room height. Same convention the floor-to-ceiling window relies on.
        wall_width, wall_height = wall.width, wall.height

        panel_w = wall_width * self.WIDTH_FRAC
        panel_h = wall_height * self.HEIGHT_FRAC

        # a box centred at the origin: x = along-wall, y = up, z = thickness (out of wall)
        self.mesh = trimesh.creation.box(extents=[panel_w, panel_h, self.THICKNESS])
        self._apply_mirror_material(self.mesh)

        # orient the panel to the wall, then centre it on the wall face, stood slightly proud.
        # transform_position maps (along, up, out) -> world, so a positive "out" always points
        # into the room for every wall (see SceneProgObjectWall.transform_position).
        self.mesh = self.rotate(self.mesh, wall)
        pos = (wall_width / 2.0, wall_height / 2.0, self.THICKNESS / 2.0 + self.PROUD)
        pos = self.transform_position(pos, wall)
        self.mesh = self.translate(self.mesh, pos)

        self.mesh.export(self.mesh_path)
        return self

    @staticmethod
    def _apply_mirror_material(mesh):
        mat = trimesh.visual.material.PBRMaterial(
            name="MirrorGlass",
            baseColorFactor=[218, 222, 228, 255],
            metallicFactor=1.0,
            roughnessFactor=0.04,
        )
        # UVs aren't needed for constant PBR factors; a TextureVisuals carries the material
        # through the glTF export cleanly.
        mesh.visual = trimesh.visual.TextureVisuals(
            uv=np.zeros((len(mesh.vertices), 2), dtype=np.float32),
            material=mat,
        )
