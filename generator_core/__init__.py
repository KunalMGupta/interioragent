"""generator_core — the end-to-end text->scene ORCHESTRATION layer, one level ABOVE IDSDL/.

Layering (dependencies flow *_core -> IDSDL, never the reverse):
    generator_core   this package: SceneGenerator runs plan -> retrieve -> audit -> author ->
                     build -> critic, looping on feedback.
      -> planner_core   the design brief + reference collage (LLM)
      -> retriever_core the tacit-knowledge lesson retrieval (no embeddings)
      -> IDSDL          the scene DSL + build engine (via IDSDL.service.core + IDSDL.lints)

IDSDL/ is the engine; this package is the agent that drives it. Entry point: SceneGenerator.
"""
from .authors import Author, AuthorTask, LLMAuthor, CommandAuthor
from .pipeline import SceneGenerator

__all__ = ["Author", "AuthorTask", "LLMAuthor", "CommandAuthor", "SceneGenerator"]
