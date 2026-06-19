import os
import sys
import json
import trimesh
import numpy as np
from PIL import Image, ImageEnhance
from langchain_openai import OpenAIEmbeddings
from sceneprogllm import LLM
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Ensure the current directory is in the path

class SceneProgAssetRetrieverBase:
    def __init__(self):
        self.name = "SceneProgAssetRetrieverBase"
        self.description = "Retrieves assets for SceneProg from the LLM."
        self.examples = ""
        
    def __call__(self, query: str) -> str:
        path = ...
        scale = ...
        return path, scale
    
    def create_model(self, description):
        import os
        import requests
        from scipy.spatial.transform import Rotation as R
        import numpy as np
        import trimesh
        response = requests.post(os.getenv("GENERATE_GLB"), json={"text": description})
        cwd = os.getcwd()
        os.makedirs(f"{cwd}/tmp", exist_ok=True)
        random_name = os.urandom(16).hex()
        path = f"{cwd}/tmp/{random_name}.glb"
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
        else:
            raise Exception("Failed to generate 3D model")

        mesh = trimesh.load(path, force="mesh")
        rotation = R.from_euler('y', 30, degrees=True)
        rotation = np.hstack((rotation.as_matrix(), np.array([[0], [0], [0]])))
        rotation = np.vstack((rotation, np.array([0, 0, 0, 1])))
        mesh.apply_transform(rotation)
        mesh.export(path)
        return path

class FutureHSSDAssetRetriever(SceneProgAssetRetrieverBase):
    def __init__(self):
        self.name = "FutureHSSDAssetRetriever"
        self.description = f"""
Retrieves assets from Future-3D and HSSD (habitat) datasets.
This is the default retriever for SceneProg. Unless specified otherwise, always use this retriever.
"""
        self.examples = """
1. A red sports car
2. A beige sofa
3. A simple wooden table
4. A modern lounge chair
"""
        self.encoder = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY"))
        data = np.load(os.path.join(os.path.dirname(__file__), "assets/futurehssd.npz"))
        self.all_embeddings = data["all_embeddings"]
        self.all_models = data["all_models"]
        # breakpoint()
        self.config = {
            "FUTURE_PATH_MODELS" : os.path.join(os.path.dirname(__file__), "futurehssd/3D-FUTURE-models"),
            "HSSD_PATH_MODELS" : os.path.join(os.path.dirname(__file__), "futurehssd/HSSD-models"),
        }
        # with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as f:
            # self.config = json.load(f)
        with open(os.path.join(os.path.dirname(__file__), "assets/futurehssd.json"), "r") as f:
            self.metadata = json.load(f)

        self.bad_assets = [
            "hssd/8be974a24717e214eede244a635af9b5d8ca20c",
            "hssd/2665c18655d09ed5c0d9149c78b0f72c93cbe860",
            "future/d1571866-191b-46d0-b0bc-e486fc24f263",
            "hssd/1e4e58bf53e51df27beeb774b5d70818de124068",
            "hssd/0f123a681f597d75bdec3319293b54b9090b4caa"
        ]
        
        self.llm = LLM(
            system_desc="""
Given a list of asset descriptions, pick the best one that matches the query. Respond by giving the name of the asset example: "hssd/b0bb0cce08a2dbc01c8e3b64ac59fffe10c73015", "future/fcb7b0b7-e74f-4397-907c-37cd2fe9efbc", etc.
""",
            response_format="json",
            response_params={"asset": "str"},
        )

    def remove_bad_assets(self, top_models, top_similarities):
        # Filter out bad assets
        filtered_models = []
        filtered_similarities = []
        for model, similarity in zip(top_models, top_similarities):
            if model not in self.bad_assets and similarity > 0.4:
                filtered_models.append(model)
                filtered_similarities.append(similarity)
        
        top_models = filtered_models
        top_similarities = np.array(filtered_similarities)

        return top_models, top_similarities
    
    def get_likely_asset(self, query: str) -> str:
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(self.all_embeddings, embd)

        # Get top 20 most similar models
        top_indices = np.argsort(similarities)[-20:][::-1]
        top_models = [self.all_models[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
    def build_context(self, models):
        context = ""
        for model in models:
            desc = self.metadata[model]["description"]
            context += f"{model}: {desc}\n"
        return context
    
    def select_best_model(self, query, top_models, top_similarities):
        prompt = f"""
{self.build_context(top_models)}

Query: {query}
"""
        
        response = self.llm(prompt)
        try:
            model = response["asset"]
        except:
            model = response.asset
        return model

    def model_to_path_scale(self, model: str) -> tuple[str, float]:
        """
        Convert model name to path and scale.
        """
        if "future" in model:
            path = os.path.join(self.config["FUTURE_PATH_MODELS"], model.split('/')[1]+'.glb')
            scale = self.metadata[model]["scale"]
        elif "hssd" in model:
            path = os.path.join(self.config["HSSD_PATH_MODELS"], model.split('/')[1]+'.glb')
            scale = self.metadata[model]["scale"]
        else:
            raise ValueError(f"Unknown model type: {model}")

        return path, scale

    def __call__(self, query: str) -> tuple[str, float]:

        top_models, top_similarities = self.get_likely_asset(query)
        top_models, top_similarities = self.remove_bad_assets(top_models, top_similarities)
        model = self.select_best_model(query, top_models, top_similarities)
        path, scale = self.model_to_path_scale(model)

        if hasattr(self, "floor_plants"):
            scale = np.random.uniform(0.6, 1)  # Random scale for floor plants

        print(f"Selected model: {model} with path: {path} and scale: {scale}")
        return path, scale

class CaseGoodsRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "CaseGoodsRetriever"
        self.description = f"""
Retrieves case goods assets that are placed on the floor. Must be used when specifically looking for case goods and nothing else.
Typically, this includes furniture like cabinets, tables, dressers, sideboards, nightstands, end tables, shelfs, desks, etc.
"""
        self.examples = """
1. A wooden cabinet
2. A coffee table with marble top
3. A dresser with a mirror
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/case_goods.json"), "r") as f:
            self.case_goods = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        case_goods_idx = [self.all_models.tolist().index(model) for model in self.case_goods if model in self.all_models]
        case_goods_embds = np.array([self.all_embeddings[i] for i in case_goods_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(case_goods_embds, embd)

        # Get top 20 most similar models
        top_indices = np.argsort(similarities)[-20:][::-1]
        top_models = [self.case_goods[i] for i in top_indices]
        top_similarities = similarities[top_indices]

        filtered_models = []
        filtered_similarities = []
        for model, similarity in zip(top_models, top_similarities):
            freetop = self.metadata[model]["freetop"]
            if freetop:
                filtered_models.append(model)
                filtered_similarities.append(similarity)
        top_models = filtered_models
        top_similarities = filtered_similarities

        return top_models, np.array(top_similarities)
    
class CeilingObjectRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "CeilingObjectRetriever"
        self.description = f"""
Retrieves ceiling objects that are placed on the ceiling. Must be used when specifically looking for ceiling objects and nothing else.
"""
        self.examples = """
1. A ceiling fan
2. A chandelier
3. A ceiling light
"""
    def get_likely_asset(self, query: str) -> str:
        top_models, top_similarities = super().get_likely_asset(query)

        filtered_models = []
        filtered_similarities = []
        for model, similarity in zip(top_models, top_similarities):
            placement = self.metadata[model]["placement"]
            if placement == "ceiling":
                filtered_models.append(model)
                filtered_similarities.append(similarity)
        top_models = filtered_models
        top_similarities = np.array(filtered_similarities)

        return top_models, top_similarities
    
class CabinetandShelfRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "CabinetandShelfRetriever"
        self.description = f"""
Retrieves cabinet and shelf objects that are placed on the floor or wall. Must be used when specifically looking for cabinets and shelves and nothing else.
Typically, this includes furniture like cabinets, shelves, bookcases, etc.
"""
        self.examples = """
1. An empty wooden cabinet. 
2. A shelf with books and decorative items.
3. An empty wall mounted wooden shelf.
4. A wall mounted shelf with decorative items.
"""
        self.classifier = LLM(
            system_desc="""
Given a query, you should tell me whether the request is for a floor cabinet/shelf or a wall mounted shelf. Also tell me whether the request is for an empty cabinet/shelf or a cabinet/shelf with items on it. 
Must respond by giving a JSON object with the keys "placement" and "empty". Lastly, you also need to reword the query removing references to empty or placement, while focusing only on the characteristics of the cabinet/shelf.
example: an empty wooden cabinet for floor --> {"placement": "floor", "empty": true, "query": "wooden cabinet"}
placement can be "floor" or "wall", empty can be true or false.
Unless specified, assume the request is for a filled cabinet/shelf.
""",
            response_format="json",
            response_params={"placement": "str", "empty": "bool", "query": "str"},  
        )
        with open(os.path.join(os.path.dirname(__file__), "assets/shelfs_or_cabinets.json"), "r") as f:
            self.shelfs_or_cabinets = json.load(f)
        
        with open(os.path.join(os.path.dirname(__file__), "assets/wall_shelfs.json"), "r") as f:
            self.wall_shelfs = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        response = self.classifier(query)
        try:
            query = response["query"]
            placement = response["placement"]
            empty = response["empty"]
        except:
            query = response.query
            placement = response.placement
            empty = response.empty
        
        if placement == "floor":
            if empty:
                candidate_models = self.shelfs_or_cabinets["empty"]
            else:
                candidate_models = self.shelfs_or_cabinets["filled"]
        elif placement == "wall":
            if empty:
                candidate_models = self.wall_shelfs["empty"]
            else:
                candidate_models = self.wall_shelfs["filled"]
        else:
            candidate_models = self.shelfs_or_cabinets["filled"]

        candidate_idxs = [self.all_models.tolist().index(model) for model in candidate_models if model in self.all_models]
        candidate_embds = np.array([self.all_embeddings[i] for i in candidate_idxs])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(candidate_embds, embd)
        # Get top 20 most similar models
        top_indices = np.argsort(similarities)[-20:][::-1]
        top_models = [candidate_models[i] for i in top_indices]
        top_similarities = similarities[top_indices]

        return top_models, top_similarities
    
class ClockRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "ClockRetriever"
        self.description = f"""
Retrieves clock objects that are placed on the wall or table. Must be used when specifically looking for clocks and nothing else.
Typically, this includes wall clocks, table clocks, and alarm clocks.
"""
        self.examples = """
1. A wall clock with a wooden frame
2. A table clock with a metal frame
3. An alarm clock with a digital display
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/clocks.json"), "r") as f:
            self.clocks = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        clocks_idx = [self.all_models.tolist().index(model) for model in self.clocks if model in self.all_models]
        clocks_embds = np.array([self.all_embeddings[i] for i in clocks_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(clocks_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.clocks[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities

class MirrorRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "MirrorRetriever"
        self.description = f"""
Retrieves mirror objects that are placed on the wall or table. Must be used when specifically looking for mirrors and nothing else.
Typically, this includes wall mirrors, table mirrors, and decorative mirrors.
"""
        self.examples = """
1. A wall mirror with a wooden frame
2. A table mirror with a metal frame
3. A decorative mirror with a vintage design
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/mirrors.json"), "r") as f:
            self.mirrors = json.load(f)
    def get_likely_asset(self, query: str) -> str:
        mirrors_idx = [self.all_models.tolist().index(model) for model in self.mirrors if model in self.all_models]
        mirrors_embds = np.array([self.all_embeddings[i] for i in mirrors_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(mirrors_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.mirrors[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class KitchenUnitRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "KitchenUnitRetriever"
        self.description = f"""
Retrieves kitchen unit which is a complete kitchen set that includes cabinets, shelves, and appliances. Must be used when specifically looking for kitchen units and nothing else.
"""
        self.examples = """
1. A modern kitchen unit with white cabinets and a black countertop
2. A rustic kitchen unit with wooden cabinets and a farmhouse sink
3. A compact kitchen unit with a microwave, fridge, and sink
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/kitchen_set.json"), "r") as f:
            self.kitchen_units = json.load(f)
    def get_likely_asset(self, query: str) -> str:
        kitchen_units_idx = [self.all_models.tolist().index(model) for model in self.kitchen_units if model in self.all_models]
        kitchen_units_embds = np.array([self.all_embeddings[i] for i in kitchen_units_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(kitchen_units_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.kitchen_units[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    

class Painting:
    def __init__(self):
        self.canvas_path = os.path.join(os.path.dirname(__file__), "assets/canvas.obj")
        
        self.canvas = trimesh.load(self.canvas_path, force="mesh", process=False)

        vertices = self.canvas.vertices
        vertices -= np.min(vertices, axis=0)
        max_vals = np.max(vertices, axis=0)
        vertices /= np.array([max_vals[0], max_vals[1], 1])
        vertices[:,0] *= 1.0
        vertices[:,1] *= 1.0

        self.llm = LLM(
            system_desc="""
Given a description of a painting or a scenery, generate a high quality image. 
""",
response_format="image", 
)       
    
    def resize_image(self, texture, width, height):

        # Step 1: Calculate the New Size
        aspect_ratio = texture.width / texture.height
        if width / height > aspect_ratio:
            # Image is limited by height, so scale height to fit and adjust width accordingly
            new_height = height
            new_width = int(aspect_ratio * height)
        else:
            # Image is limited by width, so scale width to fit and adjust height accordingly
            new_width = width
            new_height = int(width / aspect_ratio)

        # Step 2: Resize the Image
        texture_resized = texture.resize((new_width, new_height), Image.LANCZOS)

        # Step 3: Create a Background Canvas (assuming a white background, change as needed)
        canvas = Image.new('RGB', (width, height), 'black')

        # Step 4: Paste the Image onto the Canvas
        x_offset = (width - new_width) // 2
        y_offset = (height - new_height) // 2
        canvas.paste(texture_resized, (x_offset, y_offset))

        # Apply any additional transformations like rotation or flipping
        canvas = canvas.transpose(Image.ROTATE_90)
        canvas = canvas.transpose(Image.FLIP_TOP_BOTTOM)

        # Enhance brightness
        enhancer = ImageEnhance.Brightness(canvas)
        texture_final = enhancer.enhance(1.5)

        return texture_final
    
    def __call__(self, query: str) -> str:
        image = self.llm(query)
        image = image.transpose(Image.ROTATE_90)
        image = image.transpose(Image.ROTATE_90)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)

        image = self.resize_image(image, 512, 512)

        uv_coordinates = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        
        self.canvas.visual = trimesh.visual.TextureVisuals(uv=uv_coordinates, image=image)
        self.mesh_visual = self.canvas.visual
        self.canvas.vertices += np.array([0, 0, 0.055])  # Adjust the canvas position slightly above the ground
        picture_window_path = os.path.join(os.path.dirname(__file__), "assets/canvas.glb")
        frame = trimesh.load(picture_window_path, force='mesh',process=False)
        vertices = frame.vertices

        vertices -= np.min(vertices, axis=0)
        vertices /= np.max(vertices, axis=0)
        vertices[:,0] *= 1.0
        vertices[:,1] *= 1.0
        vertices[:,-1] *= 0.05

        uid = np.random.randint(0, 1e6)
        frame = trimesh.Trimesh(vertices=vertices, faces=frame.faces, process=False)  
        self.mesh = trimesh.util.concatenate([self.canvas, frame])

        os.makedirs(os.path.join(os.path.dirname(__file__), "/tmp"), exist_ok=True)        
        self.mesh.export(os.path.join(os.path.dirname(__file__), f"/tmp/painting_{uid}.glb"))

        self.mesh = trimesh.load(os.path.join(os.path.dirname(__file__), f"/tmp/painting_{uid}.glb"), force='mesh', process=False)
        vertices = self.mesh.vertices
        vertices -= np.mean(vertices, axis=0)
        self.mesh.vertices = vertices
        self.mesh.export(os.path.join(os.path.dirname(__file__), f"/tmp/painting_{uid}.glb"))

        return os.path.join(os.path.dirname(__file__), f"/tmp/painting_{uid}.glb"), 1.0
    
class WallArtRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "WallArtRetriever"
        self.description = f"""
Retrieves wall art objects that are placed on the wall. These include paintings, posters, and other decorative items. Only use this retriever when specifically looking for wall art.
"""
        self.examples = """
1. A painting of a sunset
2. A poster of a famous movie
3. A decorative wall hanging
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/wall_art.json"), "r") as f:
            self.wall_art = json.load(f)
        self.painting_generator = Painting()

    def get_likely_asset(self, query: str) -> str:
        wall_art_idx = [self.all_models.tolist().index(model) for model in self.wall_art if model in self.all_models]
        wall_art_embds = np.array([self.all_embeddings[i] for i in wall_art_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(wall_art_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.wall_art[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
        
    def __call__(self, query: str) -> tuple[str, float]:

        top_models, top_similarities = self.get_likely_asset(query)
        if top_similarities.max() < 0.5:
            # If no suitable model is found, generate a painting
            path, scale = self.painting_generator(query)
            return path, scale
        model = self.select_best_model(query, top_models, top_similarities)
        path, scale = self.model_to_path_scale(model)
        return path, np.min((scale, 1.5))

class TableTopDecorRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "TableTopDecorRetriever"
        self.description = f"""
Retrieves table top decor objects that are placed on tables or shelves. These include vases, books, small decorative items, candles, small sculptures, cutlery, and other small items.
Only use this retriever when specifically looking for table top decor. 
""" 
        self.examples = """
1. A vase with flowers
2. A decorative candle holder
3. A small sculpture
4. A decorative bowl
5. A set of cutlery
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/table_top_decor.json"), "r") as f:
            self.table_top_decor = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        table_top_idx = [self.all_models.tolist().index(model) for model in self.table_top_decor if model in self.all_models]
        table_top_embds = np.array([self.all_embeddings[i] for i in table_top_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(table_top_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.table_top_decor[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class FloorPlantsRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "FloorPlantsRetriever"
        self.description = f"""
Retrieves large floor plants that are placed on the floor as part of the room decor. These include potted plants, large succulents, and other similar items.
"""
        self.examples = """
1. A large potted plant
2. A tall succulent in a decorative pot
3. A floor plant with a decorative stand
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/floor_plants.json"), "r") as f:
            self.floor_plants = json.load(f)
            
    def get_likely_asset(self, query: str) -> str:
        floor_plants_idx = [self.all_models.tolist().index(model) for model in self.floor_plants if model in self.all_models]
        floor_plants_embds = np.array([self.all_embeddings[i] for i in floor_plants_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(floor_plants_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.floor_plants[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    

class HumansAndSculpturesRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "HumansAndSculpturesRetriever"
        self.description = f"""
Retrieves humans and human sized sculptures that are placed on the floor as part of the room decor. These include models of man, woman, child as well as human sculptures, statues, and other similar items.
"""
        self.examples = """
1. A man standing
2. A woman sitting
3. A child playing
4. A human sculpture
5. A statue of a man
""" 

        with open(os.path.join(os.path.dirname(__file__), "assets/humans_and_sculptures.json"), "r") as f:
            self.humans_and_sculptures = json.load(f)
        
    def get_likely_asset(self, query: str) -> str:
        humans_and_sculptures_idx = [self.all_models.tolist().index(model) for model in self.humans_and_sculptures if model in self.all_models]
        humans_and_sculptures_embds = np.array([self.all_embeddings[i] for i in humans_and_sculptures_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(humans_and_sculptures_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.humans_and_sculptures[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class ClothesRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "ClothesRetriever"
        self.description = f"""
Retrieves clothes that are either hanging on a wall, from a rod or neatly folded in a stack. 
Note that coat hangers are not included in this retriever, they are considered as furniture.
"""
        self.examples = """
1. A red dress 
2. A blue shirt
3. A pair of jeans
4. A neatly folded sweater
5. A stack of t-shirts
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/clothes.json"), "r") as f:
            self.clothes = json.load(f)
    def get_likely_asset(self, query: str) -> str:
        clothes_idx = [self.all_models.tolist().index(model) for model in self.clothes if model in self.all_models]
        clothes_embds = np.array([self.all_embeddings[i] for i in clothes_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(clothes_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.clothes[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class BathroomVanityUnitRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "BathroomVanityUnitRetriever"
        self.description = f"""
Retrieves bathroom vanity units that are complete sets including cabinets, shelves, mirrors, and sinks.
Only use this retriever when specifically looking for bathroom vanity units. Note that this retriever is not used for individual bathroom items like sinks, faucets, or mirrors.
"""
        self.examples = """
1. A modern bathroom vanity unit with a white sink and a large mirror
2. A rustic bathroom vanity unit with a wooden cabinet and a round mirror
3. A compact bathroom vanity unit with a small sink and a shelf
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/bathroom_vanity_unit.json"), "r") as f:
            self.bathroom_vanity_units = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        bathroom_vanity_units_idx = [self.all_models.tolist().index(model) for model in self.bathroom_vanity_units if model in self.all_models]
        bathroom_vanity_units_embds = np.array([self.all_embeddings[i] for i in bathroom_vanity_units_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(bathroom_vanity_units_embds, embd)
        # Get top 5 most similar models
        top_indices = np.argsort(similarities)[-5:][::-1]
        top_models = [self.bathroom_vanity_units[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class DressingVanityUnitRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "DressingVanityUnitRetriever"
        self.description = f"""
Retrieves dressing vanity units that are complete sets including mirror, table, and makeup items.
Notably, it does not include a stool or chair, as these are considered furniture. Only use this retriever when specifically looking for dressing vanity units.
"""
        self.examples = """
1. A modern dressing vanity unit with a large mirror and a makeup table
2. A rustic dressing vanity unit with a wooden table and a round mirror
3. A compact dressing vanity unit with a small mirror and a shelf
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/dressing_vanity_unit.json"), "r") as f:
            self.dressing_vanity_units = json.load(f)
    def get_likely_asset(self, query: str) -> str:
        dressing_vanity_units_idx = [self.all_models.tolist().index(model) for model in self.dressing_vanity_units if model in self.all_models]
        dressing_vanity_units_embds = np.array([self.all_embeddings[i] for i in dressing_vanity_units_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(dressing_vanity_units_embds, embd)
        # Get top 5 most similar models
        top_indices = np.argsort(similarities)[-5:][::-1]
        top_models = [self.dressing_vanity_units[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities

class ApplianceRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "ApplianceRetriever"
        self.description = f"""
Retrieves appliances that are typically found in a home, such as refrigerators, washing machines, microwaves, ovens, including personal electronics like TVs, computers, etc. 
Only use this retriever when specifically looking for appliances.
"""
        self.examples = """
1. A stainless steel refrigerator
2. A white washing machine
3. A black microwave oven
4. A smart TV
5. A desktop computer
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/appliances.json"), "r") as f:
            self.appliances = json.load(f)
    def get_likely_asset(self, query: str) -> str:
        appliances_idx = [self.all_models.tolist().index(model) for model in self.appliances if model in self.all_models]
        appliances_embds = np.array([self.all_embeddings[i] for i in appliances_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(appliances_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.appliances[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class GymEquipmentRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "GymEquipmentRetriever"
        self.description = f"""
Retrieves gym equipment that is typically found in a gym such as treadmills, exercise bikes, weights, lockers, etc.
Only use this retriever when specifically looking for gym equipment.
"""
        self.examples = """
1. A treadmill
2. An exercise bike
3. A set of dumbbells
4. A weight bench
5. A yoga mat
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/gym_equipment.json"), "r") as f:
            self.gym_equipment = json.load(f)
    def get_likely_asset(self, query: str) -> str:
        gym_equipment_idx = [self.all_models.tolist().index(model) for model in self.gym_equipment if model in self.all_models]
        gym_equipment_embds = np.array([self.all_embeddings[i] for i in gym_equipment_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(gym_equipment_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.gym_equipment[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
        
class BathroomFurnitureAndMiscellaneousRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "BathroomFurnitureAndMiscellaneousRetriever"
        self.description = f"""
Retrieves bathroom furniture and miscellaneous items that are typically found in a bathroom such as cabinets, shelves, toilets, bathtubs, etc. 
Note that vanities are not included in this retriever, as they are considered as complete sets and must be retrieved using the BathroomVanityUnitRetriever.
Only use this retriever when specifically looking for bathroom furniture and miscellaneous items.
"""
        self.examples = """
1. A wooden bathroom cabinet
2. A modern toilet
3. A standing shower
4. A bathtub
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/bathroom.json"), "r") as f:
            self.bathroom = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        bathroom_idx = [self.all_models.tolist().index(model) for model in self.bathroom if model in self.all_models]
        bathroom_embds = np.array([self.all_embeddings[i] for i in bathroom_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(bathroom_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.bathroom[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class GameEquipmentRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "GameEquipmentRetriever"
        self.description = f"""
Retrieves game equipment that is typically found in indoor situations such as pool tables, ping pong tables, foosball tables, chess etc. 
Only use this retriever when specifically looking for game equipment.
"""
        self.examples = """
1. A pool table
2. A ping pong table
3. A foosball table
4. A chess set
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/game_equipment.json"), "r") as f:
            self.game_equipment = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        game_equipment_idx = [self.all_models.tolist().index(model) for model in self.game_equipment if model in self.all_models]
        game_equipment_embds = np.array([self.all_embeddings[i] for i in game_equipment_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(game_equipment_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.game_equipment[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities
    
class CountersRetriever(FutureHSSDAssetRetriever):
    def __init__(self):
        super().__init__()
        self.name = "CountersRetriever"
        self.description = f"""
Retrieves reception counters, bakery display cum counters, bar counters, and other similar items that are typically found in commercial settings.
Only use this retriever when specifically looking for counters.
"""
        self.examples = """
1. A reception counter with a wooden finish
2. A bakery display counter with glass shelves
3. A bar counter with a marble top
"""
        with open(os.path.join(os.path.dirname(__file__), "assets/counters.json"), "r") as f:
            self.counters = json.load(f)

    def get_likely_asset(self, query: str) -> str:
        counters_idx = [self.all_models.tolist().index(model) for model in self.counters if model in self.all_models]
        counters_embds = np.array([self.all_embeddings[i] for i in counters_idx])
        embd = np.array(self.encoder.embed_query(query))
        similarities = np.dot(counters_embds, embd)
        # Get top 10 most similar models
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_models = [self.counters[i] for i in top_indices]
        top_similarities = similarities[top_indices]
        return top_models, top_similarities

class CherryBlossomRetriever(SceneProgAssetRetrieverBase):
    def __init__(self):
        super().__init__()
        self.name = "CherryBlossomRetriever"
        self.description = f"""
Retrieves cherry blossom tree
"""
        self.examples = """
1. A cherry blossom tree in full bloom
"""
        self.path = os.path.join(os.path.dirname(__file__), "assets/cherry_blossom.glb")

    def __call__(self, query: str) -> tuple[str, float]:
        return self.path, 1.8
    

class SceneMotifCoderObject(SceneProgAssetRetrieverBase):
    def __init__(self):
        super().__init__()
        self.name = "SceneMotifCoderObject"
        self.description = f"""
This tool returns 'stacked' objects based on an input description which can be used like any other objects in the scene program. 
Particularly useful when the user wants to add a specific arrangement of objects in the scene, for example, a stack of "5" books instead of just "a stack of books" for which the TableTopDecorRetriever can be used.
The SceneMotifCoderObject is helpful in generating specific arrangements of objects that are not easily retrievable using the other retrievers. It can generate arrangements like stacks, rows, grids, etc. based on the input description.
"""
        self.examples = """
Following are a few examples of this tool in action:
Example 1:
scene.SceneMotifCoderObject('A table with a chair in front of it')
## Adds a new object to the scene where a chair is placed in front of a table
Example 2:
scene.SceneMotifCoderObject('A stack of 5 cups')
## Adds a new object to the scene where 5 cups are stacked on top of each other
Example 3:
scene.SceneMotifCoderObject('A grid of 5x5 chairs')
## Adds a new object to the scene where 25 chairs are arranged in a 5x5 grid
"""

    def __call__(self, query):
        code = f"""
#!/bin/bash
# Path to the Python executable
PYTHON_EXECUTABLE="/opt/miniconda3/envs/smc/bin/python"
# Path to the inference script
SCRIPT_PATH="/<path to smc>/smc/inference.py"

# Arguments for the script
DESC="{query}"
OUT_DIR="/<path to sceneprog>/sceneprog/tmp/"

cd /<path to smc>/smc
# Execute the Python script with the arguments
$PYTHON_EXECUTABLE $SCRIPT_PATH --desc "$DESC" --out_dir "$OUT_DIR"

# Wait for the program to complete and check exit status
if [ $? -eq 0 ]; then
    echo "Inference completed successfully."
else
    echo "Inference failed with exit code $?."
    exit 1
fi
"""
        with open("tmp/smc_run.sh", "w") as f:
            f.write(code)
        import os
        os.system(f"bash tmp/smc_run.sh")
        import trimesh
        mesh = trimesh.load("tmp/stacked.glb", process=False, force='mesh')
        scale = mesh.bounds[1,0] - mesh.bounds[0,0]
        return "tmp/stacked.glb", scale
    
FUTURE_HSSD_ASSET_RETRIEVERS = [
    FutureHSSDAssetRetriever(),
    CaseGoodsRetriever(),
    CeilingObjectRetriever(),
    CabinetandShelfRetriever(),
    ClockRetriever(),
    MirrorRetriever(),
    KitchenUnitRetriever(),
    WallArtRetriever(),
    TableTopDecorRetriever(),
    FloorPlantsRetriever(),
    HumansAndSculpturesRetriever(),
    ClothesRetriever(),
    BathroomVanityUnitRetriever(),
    DressingVanityUnitRetriever(),
    ApplianceRetriever(),
    GymEquipmentRetriever(),
    BathroomFurnitureAndMiscellaneousRetriever(),
    CountersRetriever(),
    GameEquipmentRetriever(),
    CherryBlossomRetriever(),
    SceneMotifCoderObject(),
]

class SceneProgAssetRetriever:
    def __init__(self, seed=None):
        self.seed = seed

        self.retrievers = {}
        for retriever in FUTURE_HSSD_ASSET_RETRIEVERS:
            self.retrievers[retriever.name] = retriever

        retriever_context = ""
        for retriever in self.retrievers.values():
            retriever_context += f"""
Name: {retriever.name}
Description: {retriever.description}
Example Queries: {retriever.examples}
"""

        self.llm = LLM(
            system_desc=f"""
Given a query, you need to select the most relevant asset retriever from the list of available asset retrievers.
Here is the list of available asset retrievers:
{retriever_context}

Following are a few examples of queries and the expected output format:
Query: A beige sofa with a modern design
retriever: FutureHSSDAssetRetriever
reasoning: ...

""",
            response_format="json",
            response_params={"retriever": "str", "reasoning": "str"},
        )

        self._cache_path = None
        self._cache = {}
        if self.seed is not None:
            import os, json
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", ".cache")
            os.makedirs(cache_dir, exist_ok=True)
            self._cache_path = os.path.join(cache_dir, f"retrieval_seed_{self.seed}.json")
            if os.path.exists(self._cache_path):
                with open(self._cache_path, "r") as f:
                    self._cache = json.load(f)

    def _save_cache(self):
        import json
        with open(self._cache_path, "w") as f:
            json.dump(self._cache, f, indent=2)

    def __call__(self, query: str):
        if self.seed is not None and query in self._cache:
            path, scale = self._cache[query]
            print(f"Cache hit (seed={self.seed}): {query}")
            return path, scale

        response = self.llm(query)
        try:
            retriever_name = response["retriever"]
        except:
            retriever_name = response.retriever

        if retriever_name not in self.retrievers:
            raise ValueError(f"Retriever '{retriever_name}' not found in available retrievers.")

        print("Using retriever:", retriever_name)
        retriever = self.retrievers[retriever_name]
        path, scale = retriever(query)

        if self.seed is not None:
            self._cache[query] = [path, scale]
            self._save_cache()

        return path, scale
