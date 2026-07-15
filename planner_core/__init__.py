"""planner_core — the DESIGN-PLANNING layer above IDSDL/ (part of the *_core orchestration tier).

`InteriorPlanner` turns a text prompt into a design brief + reference-image collage over an LLM
image model; `SkillsRAG` is embedding retrieval over the skills/ lesson library. Consumed by
generator_core and by IDSDL.service.core. It does NOT depend on IDSDL — the arrow points down
(generator_core -> planner_core -> [prompt/LLM], and generator_core -> IDSDL separately).
"""
from .planner import InteriorPlanner, DesignResult
from .rag import SkillsRAG

__all__ = ["InteriorPlanner", "DesignResult", "SkillsRAG"]
