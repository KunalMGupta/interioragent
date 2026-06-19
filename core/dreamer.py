import os
from sceneprogllm import LLM
import matplotlib.pyplot as plt


class Dreamer:
    def __init__(self, id, model_name="gpt-5", reasoning_effort="medium"):
        self.text2img = LLM(system_desc="""
You generate ONLY photorealistic isometric cutaway renders of indoor rooms.

Your output must always follow these rules:

CAMERA / COMPOSITION RULES
- The image must be a true isometric-style 3D room render.
- Use a fixed elevated corner view, like an architectural dollhouse / room diorama.
- Show two walls and the floor, or a clean cutaway corner-room layout.
- The scene must have NO eye-level camera view.
- The scene must have NO cinematic perspective shot.
- The scene must have NO fisheye, NO wide-angle lens distortion, and NO vanishing-point perspective emphasis.
- The image should look like a carefully staged 3D interior visualization viewed from above at an angle.
- Keep the full room clearly visible inside the frame.
- The composition should feel like a miniature interior set or isometric architectural render.

STYLE RULES
- Photorealistic materials and lighting.
- Realistic indoor architecture, furniture, decor, and objects.
- Detailed textures for wood, fabric, glass, metal, walls, and flooring.
- Soft natural light from windows plus warm practical interior lighting.
- Clean layout, balanced object placement, believable scale.

SCENE RULES
- The image must represent the user's room description faithfully.
- The room should include architectural boundaries and furniture arranged in a realistic floorplan.
- The scene should feel complete, grounded, and physically plausible.

NEGATIVE RULES
- Do NOT generate a normal front-facing interior render.
- Do NOT generate a human eye-height shot.
- Do NOT generate a straight-on photograph of a room.
- Do NOT generate exterior views.
- Do NOT generate flat 2D illustrations, sketches, cartoons, or concept art.
- Do NOT crop too tightly into furniture.
- Do NOT use dramatic perspective lines.

OUTPUT FORMAT
- Return a single high-resolution photorealistic isometric indoor scene render.
- Default target style: architectural visualization, isometric room cutaway, photorealistic 3D render.

""",
            reasoning_effort=reasoning_effort,
            response_format="image",
            model_name=model_name
        )  

        self.img2img = LLM(system_desc="""
You are an expert in generating photorealistic isometric cutaway renders of indoor scenes based on textual descriptions and reference images.

Your outputs MUST strictly follow a consistent isometric architectural visualization style.

TASK:
Generate a photorealistic isometric render of an indoor scene that visually represents the described environment, using the provided reference image as the structural and compositional foundation.

CRITICAL CAMERA & GEOMETRY RULES (HIGHEST PRIORITY):
- The output MUST preserve the isometric camera angle from the reference image.
- Use an elevated 3/4 top-down view (dollhouse / architectural cutaway perspective).
- The scene must show a corner room layout (typically two walls + floor).
- Maintain the exact spatial orientation and viewing angle of the reference image.
- The full room must remain visible within the frame.
- NO eye-level views.
- NO cinematic or photographic perspective.
- NO wide-angle or fisheye distortion.
- NO strong vanishing-point perspective.

REFERENCE IMAGE USAGE:
- The reference image defines:
  - camera angle
  - room layout
  - composition
  - perspective (must be preserved exactly)
- You MUST reuse the same structural layout and viewpoint.
- Only modify objects, materials, decor, and lighting according to the user prompt.
- Do NOT change the camera position or scene framing.

STYLE REQUIREMENTS:
- Photorealistic 3D render (not illustration, not stylized, not cartoon).
- Realistic materials: wood, fabric, glass, metal, walls, flooring.
- Physically plausible lighting:
  - soft natural light from windows
  - warm interior lighting (lamps, ambient)
- Clean, believable furniture arrangement with proper scale and spacing.
- High detail and texture fidelity.

SCENE MODIFICATION RULES:
- Update the environment based on the user’s description.
- Add, remove, or modify furniture and decor while keeping layout consistent.
- Ensure all elements fit naturally within the existing room structure.
- Maintain realism and physical plausibility.

NEGATIVE CONSTRAINTS (STRICT):
- Do NOT generate a normal interior photograph.
- Do NOT switch to eye-level perspective.
- Do NOT create a front-facing room view.
- Do NOT crop into objects or zoom too close.
- Do NOT flatten the scene into 2D.
- Do NOT change the isometric angle from the reference.
- Do NOT introduce dramatic perspective distortion.

INPUTS:
1. Base image (existing isometric render): {insert base image or reference}
2. User text description: "{user_text_prompt}"

INSTRUCTIONS:
- Use the base image as a fixed isometric template.
- Preserve its camera angle, composition, and room structure exactly.
- Apply the user’s description by modifying objects, materials, and lighting only.
- Ensure the final image remains a clean, full-room isometric cutaway.

OUTPUT:
A high-resolution (1024×1024 or 2048×2048) photorealistic isometric indoor scene render that preserves the reference image’s geometry and composition while reflecting the user’s requested changes.""",
            reasoning_effort=reasoning_effort,
            model_name=model_name,
            response_format="image"
        )  

    def __call__(self, text, image=None):
        user_prompt = f"""
        Create a photorealistic isometric cutaway room render of the following indoor scene:

        {text}

        Important:
        - The result must be an isometric architectural visualization.
        - Show the room as a 3D corner cutaway / dollhouse-style interior.
        - Elevated angled top-down view.
        - No eye-level view.
        - No cinematic perspective.
        - No wide-angle lens look.
        - Full room visible in frame.
        """
        
        if image is not None:
            return self.img2img(user_prompt, image_paths=[image])
        else:
            return self.text2img(user_prompt)
        
if __name__ == "__main__":
    dreamer = Dreamer(id="test")
    text_prompt = "A large gym with a small station selling plants"
    result = dreamer(text_prompt)
    result.save("test.png")