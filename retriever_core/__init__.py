"""retriever_core — the TACIT-KNOWLEDGE retrieval layer above IDSDL/ (part of *_core).

`TraceRetriever` reasons over a markdown KNOWLEDGE CATALOG of lessons/recipes (an LLM reads the
catalog; NO embeddings). This is deliberately distinct from IDSDL.datasets.retrievers, which does
embedding-based 3D-MESH retrieval — same word "retriever", different domain (design knowledge vs.
furniture meshes). Consumed by generator_core and IDSDL.service.core.
"""
from .catalog import KnowledgeCatalog
from .retriever import TraceRetriever, ContextBundle

__all__ = ["KnowledgeCatalog", "TraceRetriever", "ContextBundle"]
