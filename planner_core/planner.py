from dataclasses import dataclass
from pathlib import Path
from sceneprogllm import LLM
from .rag import SkillsRAG

_BASE = Path(__file__).parent.parent

_SKILL_COMPOSER_SYSTEM = """
You are a skill-composition model for interior image generation. You operate in two modes:

**Synthesis mode** — Given a user prompt and a set of reference skills, synthesize them into one coherent, reusable conditioning skill that matches the user prompt.

**Edit mode** — Given an existing conditioning skill and an edit instruction, refine the skill to incorporate the requested changes while preserving everything that was not explicitly asked to change.

In both modes:
- Output should describe design principles and visual/spatial cues, not a fixed final scene layout.
- Combine overlapping ideas into broader reusable concepts.
- Preserve strong recurring visual motifs, furniture relationships, materials, colors, lighting, and spatial patterns.
- Keep it image-generation-friendly: concrete nouns, textures, colors, furniture, lighting, and composition cues.
- Do not specify exact wall-by-wall placement unless essential to the style.
- Do not include captions, labels, people, or implementation notes.
- Return only one skill with a short headline and one dense description.

Output format:
Headline: <skill name>
Description: <conditioning skill>
"""

_IMAGE_GEN_PROMPT = """
Create a photorealistic 2x4 editorial interior-design collage showing eight detail-focused views of one consistent cuboid room based on the user prompt and synthesized conditioning skill.

User prompt: {user_prompt}

Conditioning skill: {skill}

Requirements:
- Show one coherent room, not eight different rooms.
- Use a simple cuboid room: straight walls, ceiling, and floor.
- Keep furniture, colors, materials, windows, doors, lighting, and decor consistent across all eight panels.
- Each panel should focus on one distinct design element, like an interior design blog feature:
  1. Main focal zone
  2. Primary furniture anchor
  3. Textile and material layering
  4. Rug or floor-zone definition
  5. Window treatment and natural light
  6. Lighting fixture or task-lighting detail
  7. Storage, surface styling, or utility moment
  8. Overall room composition / circulation view
- Use varied camera distances: wide, medium, and close-up detail shots.
- Translate the conditioning skill into visible design features.
- Maintain realistic spatial relationships and clear continuity across panels.
- Photorealistic interior design photography, editorial blog style, natural perspective, realistic lighting and shadows.
- No people, no captions, no text labels, no diagrams, no impossible architecture.
"""


@dataclass
class DesignResult:
    image: object
    skill: str
    retrieved: list[dict]

    def save(self, path: str) -> None:
        self.image.save(path)


class InteriorPlanner:
    def __init__(
        self,
        skills_path: str | Path = _BASE / "assets" / "skills.json",
        cache_path: str | Path = _BASE / "assets" / "rag_cache.npz",
        retrieval_top_k: int = 3,
    ):
        self._top_k = retrieval_top_k
        self._rag = SkillsRAG(skills_path=skills_path, cache_path=cache_path)
        self._skill_composer = LLM(system_desc=_SKILL_COMPOSER_SYSTEM, response_format="text")
        self._dreamer = LLM(response_format="image", response_params={"background": "opaque"})
        self._state: DesignResult | None = None
        self._last_prompt: str | None = None

    def __call__(self, prompt: str) -> DesignResult:
        return self.generate(prompt)

    def generate(self, prompt: str) -> DesignResult:
        """
        Retrieve relevant skills, synthesize a composite conditioning skill,
        and generate a 2x4 design collage. Resets internal state.
        """
        retrieved = self._rag(prompt, top_k=self._top_k)
        reference_skills = "\n".join(r["skills"] for r in retrieved)
        composite_skill = self._skill_composer(
            f"User prompt: {prompt}\nReference skills: {reference_skills}"
        )
        image = self._dreamer(
            _IMAGE_GEN_PROMPT.format(user_prompt=prompt, skill=composite_skill)
        )
        self._last_prompt = prompt
        self._state = DesignResult(image=image, skill=composite_skill, retrieved=retrieved)
        return self._state

    def edit(self, instruction: str) -> DesignResult:
        """
        Refine the current design based on an edit instruction.
        Keeps the original retrieved skills; only the conditioning skill and image are updated.
        Raises RuntimeError if generate() has not been called yet.
        """
        if self._state is None:
            raise RuntimeError("No current design to edit — call generate() first.")

        revised_skill = self._skill_composer(
            f"Current skill:\n{self._state.skill}\n\nEdit instruction: {instruction}"
        )
        image = self._dreamer(
            _IMAGE_GEN_PROMPT.format(user_prompt=self._last_prompt, skill=revised_skill)
        )
        self._state = DesignResult(image=image, skill=revised_skill, retrieved=self._state.retrieved)
        return self._state
