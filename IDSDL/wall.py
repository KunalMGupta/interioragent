import math
import os
import numpy as np
import trimesh


class PlaneMesh:
    def __init__(self, width, height, cell_size=0.2, color=(0.8, 0.8, 0.8)):
        if width <= 0:
            raise ValueError(f"width must be positive, got {width}")
        if height <= 0:
            raise ValueError(f"height must be positive, got {height}")
        if cell_size <= 0:
            raise ValueError(f"cell_size must be positive, got {cell_size}")

        self.width = float(width)
        self.height = float(height)
        self.cell_size = float(cell_size)
        self.color = color
        self.nx = math.ceil(width / cell_size)
        self.ny = math.ceil(height / cell_size)
        self.holes = set()
        self._rebuild()

    def _rebuild(self):
        dx = self.width / self.nx
        dy = self.height / self.ny
        vertices = []
        faces = []
        face_colors = []

        for j in range(self.ny):
            for i in range(self.nx):
                if (i, j) in self.holes:
                    continue

                x0, y0 = i * dx, j * dy
                x1, y1 = (i + 1) * dx, (j + 1) * dy

                v0 = [x0, 0.0, y0]
                v1 = [x1, 0.0, y0]
                v2 = [x1, 0.0, y1]
                v3 = [x0, 0.0, y1]

                idx = len(vertices)
                vertices.extend([v0, v1, v2, v3])
                faces.append([idx, idx + 1, idx + 2])
                faces.append([idx, idx + 2, idx + 3])

                if self.color is not None:
                    rgba = tuple(int(c * 255) for c in self.color) + (255,)
                    face_colors.append(rgba)
                    face_colors.append(rgba)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.faces = np.array(faces, dtype=np.int32)
        self.face_colors = np.array(face_colors, dtype=np.uint8) if face_colors else None

    def to_trimesh(self):
        return trimesh.Trimesh(
            vertices=self.vertices,
            faces=self.faces,
            face_colors=self.face_colors,
            process=False,
        )

    def export(self, path):
        mesh = self.to_trimesh()
        mesh.export(path, include_normals=True)

    def _export_transformed(self, path, invert=False):
        mesh = self.to_trimesh()
        T = np.eye(4, dtype=np.float32)
        T[:3, :3] = self.rotation.as_matrix()
        mesh.apply_transform(T)
        mesh.apply_translation(self.translation)
        if invert:
            mesh.invert()
        mesh.export(path)

    def compute_vertical_bounds(self):
        fu = 1.90 - 3.0 * np.exp(-0.40 * self.height)
        vu = 2.90 - 3.0 * np.exp(-0.40 * self.height)

        fu = float(np.clip(fu, 0.0, self.height))
        vu = float(np.clip(vu, 0.0, self.height))
        if fu > vu:
            fu, vu = vu, fu
        return fu, vu
    
    def _collect_wall_objects(self, wall_name):
        objs = []

        # decorative wall assets
        wall_dict = self.wall_assets.get(wall_name, {})
        for key in ["left", "center", "right"]:
            objs.extend(wall_dict.get(key, []))

        # architectural wall objects
        for obj in getattr(self.group.scene, "wall_objects", []):
            if getattr(obj, "wall_name", None) == wall_name:
                objs.append(obj)

        return objs

    def get_partition_bounds_by_label(self, label, margin=0.0):
        if label == 'full':
            return (0, self.width), (0, self.height)

        fu, vu = self.compute_vertical_bounds()
        vertical_zones = {
            'top': (vu, self.height * 0.9),
            'middle': (fu, vu),
            'bottom': (self.height * 0.1, fu),
        }

        horizontal_zones = {
            'left': (self.width * 0.02, self.width / 3),
            'center': (self.width / 3, 2 * self.width / 3),
            'right': (2 * self.width / 3, self.width * 0.98),
        }

        parts = label.lower().split("-")
        if len(parts) == 1:
            vert_key = "middle" if parts[0] in horizontal_zones else parts[0]
            horz_key = "center" if parts[0] in vertical_zones else parts[0]
        elif len(parts) == 2:
            vert_key, horz_key = (parts[0], parts[1]) if parts[0] in vertical_zones else (parts[1], parts[0])
        else:
            raise ValueError("Invalid partition label")

        if vert_key not in vertical_zones or horz_key not in horizontal_zones:
            raise ValueError("Label must include one vertical (top/middle/bottom) and one horizontal (left/center/right) part")

        y0, y1 = vertical_zones[vert_key]
        x0, x1 = horizontal_zones[horz_key]

        return (x0 + margin, x1 - margin), (y0 + margin, y1 - margin)

    def get_partition_cells_by_label(self, label, margin=0.0):
        (x_min, x_max), (y_min, y_max) = self.get_partition_bounds_by_label(label, margin)

        dx = self.width / self.nx
        dy = self.height / self.ny

        i_min = max(0, int(x_min / dx))
        i_max = min(self.nx - 1, int(x_max / dx))
        j_min = max(0, int(y_min / dy))
        j_max = min(self.ny - 1, int(y_max / dy))

        return [
            (i, j)
            for i in range(i_min, i_max + 1)
            for j in range(j_min, j_max + 1)
        ]

    def flip_horizontal_label(self, label):
        replacements = {'left': 'right', 'right': 'left'}
        parts = label.lower().split("-")
        flipped = [replacements.get(p, p) for p in parts]
        return "-".join(flipped)

    def get_partition_dimensions_by_label(self, label, margin=0.0):
        (x0, x1), (y0, y1) = self.get_partition_bounds_by_label(label, margin)
        return x1 - x0, y1 - y0

    def get_partition_center_by_label(self, label, margin=0.0):
        (x0, x1), (y0, y1) = self.get_partition_bounds_by_label(label, margin)
        return (x0 + x1) / 2, (y0 + y1) / 2


class BackWall(PlaneMesh):
    def __init__(self, WIDTH, HEIGHT, DEPTH, texture, cell_size=0.2, color=(0.9, 0.9, 0.8)):
        super().__init__(width=WIDTH, height=HEIGHT, cell_size=cell_size, color=color)
        self.name = "back_wall"
        from scipy.spatial.transform import Rotation as R
        self.rotation = R.from_euler('x', -90, degrees=True)
        self.translation = np.array([0, 0, 0], dtype=np.float32)
        self.texture_path = texture
        self.res = int(1.5 * max(WIDTH, HEIGHT, DEPTH))

    def export(self, path):
        self._export_transformed(path, invert=False)


class FrontWall(PlaneMesh):
    def __init__(self, WIDTH, HEIGHT, DEPTH, texture, cell_size=0.2, color=(0.9, 0.9, 0.8)):
        super().__init__(width=WIDTH, height=HEIGHT, cell_size=cell_size, color=color)
        self.name = "front_wall"
        from scipy.spatial.transform import Rotation as R
        self.rotation = R.from_euler('x', -90, degrees=True)
        self.translation = np.array([0, 0, DEPTH], dtype=np.float32)
        self.texture_path = texture
        self.res = int(1.5 * max(WIDTH, HEIGHT, DEPTH))

    def export(self, path):
        self._export_transformed(path, invert=True)

    def get_partition_bounds_by_label(self, label, margin=0.0):
        label = self.flip_horizontal_label(label)
        return super().get_partition_bounds_by_label(label, margin)


class LeftWall(PlaneMesh):
    def __init__(self, WIDTH, HEIGHT, DEPTH, texture, cell_size=0.2, color=(0.9, 0.9, 0.8)):
        super().__init__(width=DEPTH, height=HEIGHT, cell_size=cell_size, color=color)
        self.name = "left_wall"
        from scipy.spatial.transform import Rotation as R
        self.rotation = R.from_euler('z', -90, degrees=True) * R.from_euler('y', -90, degrees=True)
        self.translation = np.array([0, 0, 0], dtype=np.float32)
        self.texture_path = texture
        self.res = int(1.5 * max(WIDTH, HEIGHT, DEPTH))

    def export(self, path):
        self._export_transformed(path, invert=True)

    def get_partition_bounds_by_label(self, label, margin=0.0):
        label = self.flip_horizontal_label(label)
        return super().get_partition_bounds_by_label(label, margin)


class RightWall(PlaneMesh):
    def __init__(self, WIDTH, HEIGHT, DEPTH, texture, cell_size=0.2, color=(0.9, 0.9, 0.8)):
        super().__init__(width=DEPTH, height=HEIGHT, cell_size=cell_size, color=color)
        self.name = "right_wall"
        from scipy.spatial.transform import Rotation as R
        self.rotation = (
            R.from_euler('y', -180, degrees=True)
            * R.from_euler('z', 90, degrees=True)
            * R.from_euler('y', 90, degrees=True)
        )
        self.translation = np.array([WIDTH, 0, 0], dtype=np.float32)
        self.texture_path = texture
        self.res = int(1.5 * max(WIDTH, HEIGHT, DEPTH))

    def export(self, path):
        self._export_transformed(path, invert=False)


class Floor(PlaneMesh):
    def __init__(self, WIDTH, HEIGHT, DEPTH, texture, cell_size=0.2, color=(0.9, 0.9, 0.8)):
        super().__init__(width=WIDTH, height=DEPTH, cell_size=cell_size, color=color)
        self.name = "floor"
        from scipy.spatial.transform import Rotation as R
        self.rotation = R.from_euler('x', 0, degrees=True)
        self.translation = np.array([0, 0, 0], dtype=np.float32)
        self.texture_path = texture
        self.res = int(1.5 * max(WIDTH, HEIGHT, DEPTH))

    def export(self, path):
        self._export_transformed(path, invert=True)


class Ceiling(PlaneMesh):
    def __init__(self, WIDTH, HEIGHT, DEPTH, texture, cell_size=0.2, color=(0.9, 0.9, 0.8)):
        super().__init__(width=WIDTH, height=DEPTH, cell_size=cell_size, color=color)
        self.name = "ceiling"
        from scipy.spatial.transform import Rotation as R
        self.rotation = R.from_euler('x', 0, degrees=True)
        self.translation = np.array([0, HEIGHT, 0], dtype=np.float32)
        self.texture_path = texture
        self.res = int(1.5 * max(WIDTH, HEIGHT, DEPTH))

    def export(self, path):
        self._export_transformed(path, invert=False)


class WallTextureRetriever:
    def __init__(self, dataset_path):
        from sceneprogllm import LLM
        from langchain_openai import OpenAIEmbeddings

        self.dataset_path = dataset_path
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        self.desc_path = os.path.join(self.assets_dir, "wall_textures.json")
        self.emb_path = os.path.join(self.assets_dir, "wall_textures_embeddings.npz")

        self.llm = LLM(
            system_desc="""
Given an image of a texture, return a description of the texture in 1-2 sentences.
Be specific about the color, pattern, and any notable features.
Do not include any other information or context.
""",
            response_format="text",
        )

        self.embd = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-3-large",
        )

    def describe_texture(self, texture_dir):
        path = os.path.join(self.dataset_path, texture_dir, "texture.png")
        try:
            desc = self.llm("Describe the texture in this image.", image_paths=[path])
        except Exception as e:
            desc = f"Error: {e}"
        return texture_dir, desc

    def build_desc(self, max_threads=4, limit=None):
        import json
        from tqdm import tqdm
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if os.path.exists(self.desc_path):
            print("Wall textures already built.")
            return

        all_dirs = []
        for d in os.listdir(self.dataset_path):
            texture_path = os.path.join(self.dataset_path, d, "texture.png")
            full_dir = os.path.join(self.dataset_path, d)
            if d.startswith('.'):
                continue
            if not os.path.isdir(full_dir):
                continue
            if not os.path.isfile(texture_path):
                continue
            all_dirs.append(d)

        if limit:
            all_dirs = all_dirs[:limit]

        textures = {}

        print(f"Processing {len(all_dirs)} textures with {max_threads} threads...")
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(self.describe_texture, d) for d in all_dirs]
            for future in tqdm(as_completed(futures), total=len(futures)):
                dir_name, desc = future.result()
                textures[dir_name] = desc

        os.makedirs(self.assets_dir, exist_ok=True)
        with open(self.desc_path, 'w') as f:
            json.dump(textures, f, indent=4)

        print(f"Descriptions saved to {self.desc_path}")

    def build_embeddings(self, max_threads=8):
        import json
        from tqdm import tqdm
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with open(self.desc_path, 'r') as f:
            textures = json.load(f)

        def embed_task(name, desc):
            try:
                emb = self.embd.embed_query(desc)
                return name, emb
            except Exception as e:
                print(f"Error embedding {name}: {e}")
                return name, None

        embeddings = {}

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(embed_task, name, desc) for name, desc in textures.items()]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Building embeddings"):
                name, emb = future.result()
                embeddings[name] = emb

        embeddings_cleaned = {k: v for k, v in embeddings.items() if v is not None}
        np.savez(self.emb_path, **embeddings_cleaned)

    def build(self):
        if not os.path.exists(self.desc_path):
            self.build_desc()
        if not os.path.exists(self.emb_path):
            self.build_embeddings()

    def __call__(self, query):
        self.build()
        data = np.load(self.emb_path)
        names = list(data.files)
        matrix = np.stack([data[name] for name in names])

        query_emb = np.asarray(self.embd.embed_query(query), dtype=np.float32)

        matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        matrix_norms = np.where(matrix_norms == 0, 1e-8, matrix_norms)
        matrix_norm = matrix / matrix_norms

        query_norm_value = np.linalg.norm(query_emb)
        if query_norm_value == 0:
            raise ValueError("Query embedding has zero norm.")
        query_norm = query_emb / query_norm_value

        similarities = matrix_norm @ query_norm
        best_idx = np.argmax(similarities)
        best_name = names[best_idx]

        return os.path.join(self.dataset_path, best_name, "texture.png")