from dataclasses import dataclass
from pathlib import Path
from sceneprogllm import LLM
from .rag import SkillsRAG

_BASE = Path(__file__).parent.parent

_SKILL_COMPOSER_SYSTEM = """
You are a skill-composition model for interior image generation. You operate in two modes:

**Synthesis mode** — Given a user prompt and a set of reference skills, synthesize them into one coherent, reusable conditioning skill that matches the user prompt.

**Edit mode** — Given an existing conditioning skill and an edit instruction, refine the skill to incorporate the requested changes while preserving everything that was not explicitly asked to change.

**Refinement mode** — Given the CURRENT room as actually built (the first reference image is a collage of real 3D renders from several angles), optionally a prior design target image, and the current conditioning skill, critique the gap between intent and what was built, then produce an IMPROVED conditioning skill. Keep what already works; add concrete, image-generation-friendly improvements to layout, circulation, focal composition, material/textile layering, lighting, and surface styling — and address weaknesses visible in the renders (bare or sparse zones, flat lighting, missing decor, awkward spacing). Preserve the room's identity (type, purpose, major furniture anchors, core palette); this is a refinement, not a different room.

In all modes:
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


_IMAGE_REFINE_PROMPT = """
Create a photorealistic 2x4 editorial interior-design collage showing an IMPROVED version of the SAME room shown in the reference images.

Reference images, in order: the FIRST image is a collage of the CURRENT room as actually built — real 3D renders from several angles (treat it as the ground-truth current state). Any remaining images are PRIOR design targets for the same room.

User prompt: {user_prompt}

Conditioning skill (the improvement direction): {skill}

Requirements:
- Keep the SAME room identity: same room type and purpose, the same major furniture anchors, and the overall material/color family visible in the current renders. This is a refinement of THIS room, not a different room.
- Explore concrete IMPROVEMENTS over the current state: better layout and circulation, a stronger focal composition, richer textile/material layering, considered lighting, and decor/styling that fills the gaps visible in the current renders (bare surfaces, sparse zones, flat lighting, empty walls).
- Show one coherent room across all eight panels; a simple cuboid room (straight walls, ceiling, floor).
- Each panel focuses on one distinct design element (focal zone, primary anchor, materials/textiles, rug/floor zone, window/natural light, lighting fixture, surface styling, overall composition), at varied camera distances.
- Photorealistic interior-design photography, editorial blog style, natural perspective, realistic lighting and shadows.
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
        model_name: str | None = None,
    ):
        self._top_k = retrieval_top_k
        self._rag = SkillsRAG(skills_path=skills_path, cache_path=cache_path)
        # model_name steers the skill-composer (text) LLM only; the dreamer is an image
        # model and picks its own backend from response_format="image".
        composer_kwargs = dict(system_desc=_SKILL_COMPOSER_SYSTEM, response_format="text")
        if model_name:
            composer_kwargs["model_name"] = model_name
        self._skill_composer = LLM(**composer_kwargs)
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

    def refine(self, render_paths, prior_paths=None, instruction: str | None = None,
               prompt: str | None = None) -> DesignResult:
        """Generate a NEW visual target that IMPROVES the current built scene.

        Feeds the planner three things and explores how to do better next iteration:
          * `render_paths` — renders of what was actually built (e.g. a collection collage),
          * `prior_paths` (or the in-memory prior target) — the planner's own prior visual(s),
          * the retrieved/sythesized skills — the design knowledge.
        It revises the conditioning skill grounded in the visual gap (the composer SEES the
        renders), then image-conditions a fresh 2x4 target on the same images. Returns the
        new DesignResult and updates state so refine() can be chained.
        """
        import tempfile
        prompt = prompt or self._last_prompt or ""
        render_paths = list(render_paths)
        prior_paths = list(prior_paths or [])

        # the planner's own prior target: from the CLI, or saved from in-memory state
        if not prior_paths and self._state is not None:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            self._state.image.save(tmp.name)
            prior_paths = [tmp.name]

        # skills: reuse the prior retrieval if we have one, else RAG the prompt fresh
        retrieved = self._state.retrieved if self._state else self._rag(prompt, top_k=self._top_k)
        base_skill = self._state.skill if self._state else "\n".join(r["skills"] for r in retrieved)

        image_paths = render_paths + prior_paths       # current renders FIRST, priors after
        instruction = instruction or (
            "explore improvements to layout, circulation, focal composition, material/textile "
            "layering, lighting, and surface styling; address anything sparse or unfinished in "
            "the current renders"
        )
        revised_skill = self._skill_composer(
            f"Refinement mode.\nUser prompt: {prompt}\n"
            f"Current conditioning skill:\n{base_skill}\n\n"
            f"Improvement focus: {instruction}",
            image_paths=image_paths,
        )
        image = self._dreamer(
            _IMAGE_REFINE_PROMPT.format(user_prompt=prompt, skill=revised_skill),
            image_paths=image_paths,
        )
        self._last_prompt = prompt
        self._state = DesignResult(image=image, skill=revised_skill, retrieved=retrieved)
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
