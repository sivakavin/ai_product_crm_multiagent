import json
import os
import numpy as np

from utils.vectorstore import get_embeddings


CACHE_FILE = "data/semantic_cache.json"


class SemanticCache:

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.embedding_model = get_embeddings()
        self.cache = self._load()

    def _load(self) -> list:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

        return []

    def _save(self):
        # Make sure data directory exists
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

        with open(CACHE_FILE, "w") as f:
            json.dump(
                self.cache,
                f,
                indent=2
            )

    def _cosine_similarity(
        self,
        a: list,
        b: list
    ) -> float:

        a = np.array(a)
        b = np.array(b)

        denominator = np.linalg.norm(a) * np.linalg.norm(b)

        if denominator == 0:
            return 0.0

        return float(
            np.dot(a, b) / denominator
        )

    def get(self, question: str):

        if not self.cache:
            return None

        q_embedding = self.embedding_model.embed_query(
            question
        )

        for entry in self.cache:

            similarity = self._cosine_similarity(
                q_embedding,
                entry["embedding"]
            )

            if similarity >= self.threshold:
                return entry["response"]

        return None

    def set(
        self,
        question: str,
        response: dict
    ):

        q_embedding = self.embedding_model.embed_query(
            question
        )

        self.cache.append({
            "question": question,
            "embedding": q_embedding,
            "response": response
        })

        self._save()


cache = SemanticCache()