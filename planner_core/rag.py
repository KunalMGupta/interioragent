import json
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from sceneprogllm import LLM
from tqdm import tqdm

_BASE = Path(__file__).parent.parent


class SkillsRAG:
    def __init__(
        self,
        skills_path: str | Path = _BASE / "assets" / "skills.json",
        cache_path: str | Path = _BASE / "assets" / "rag_cache.npz",
    ):
        self._llm = LLM(response_format="embedding")
        self._skills = self._load_skills(Path(skills_path))
        self._embeddings = self._load_index(Path(cache_path))

    def __call__(self, query: str, top_k: int = 5) -> list[dict]:
        return self.retrieve(query, top_k=top_k)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Return the top_k skill cards most relevant to query, ranked by cosine similarity."""
        query_emb = np.array(self._llm([query])[0])
        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_emb)
        sims = self._embeddings @ query_emb / np.maximum(norms, 1e-10)
        top_indices = np.argsort(sims)[::-1][:top_k]
        return [{"score": float(sims[i]), **self._skills[i]} for i in top_indices]

    def _load_skills(self, skills_path: Path) -> list[dict]:
        with open(skills_path) as f:
            return json.load(f)

    def _load_index(self, cache_path: Path) -> np.ndarray:
        contexts = [s["context"] for s in self._skills]
        if cache_path.exists():
            cache = np.load(cache_path, allow_pickle=True)
            if list(cache["contexts"]) == contexts:
                return cache["embeddings"]
            print("Cache is stale — rebuilding...")
        return self._build_index(cache_path)

    def _build_index(self, cache_path: Path, batch_size: int = 512, max_workers: int = 8) -> np.ndarray:
        contexts = [s["context"] for s in self._skills]
        batches = [(i, contexts[i:i + batch_size]) for i in range(0, len(contexts), batch_size)]
        print(f"Encoding {len(contexts)} skill cards across {len(batches)} batches...")

        results: dict[int, np.ndarray] = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(lambda b: np.array(self._llm(b[1])), batch): batch[0] for batch in batches}
            with tqdm(total=len(futures), desc="Encoding batches", unit="batch") as pbar:
                for future in as_completed(futures):
                    results[futures[future]] = future.result()
                    pbar.update(1)

        embeddings = np.concatenate([results[i] for i in sorted(results)], axis=0)
        np.savez(cache_path, embeddings=embeddings, contexts=np.array(contexts, dtype=object))
        print(f"Saved embedding cache → {cache_path}")
        return embeddings
