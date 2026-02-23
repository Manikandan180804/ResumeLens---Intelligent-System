"""
Vector Database Manager - handles FAISS and Chroma for semantic similarity.
"""
import os
import json
import uuid
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from backend.config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers."""

    def __init__(self):
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def generate(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        self._load_model()
        if not text or not text.strip():
            return [0.0] * settings.EMBEDDING_DIM
        embedding = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        return embeddings.tolist()


class FAISSVectorStore:
    """FAISS-based vector store for semantic similarity search."""

    def __init__(self, index_path: str, dim: int = 384):
        self.index_path = index_path
        self.metadata_path = index_path + "_metadata.json"
        self.dim = dim
        self.index = None
        self.metadata: Dict[int, Dict] = {}
        self._id_map: Dict[str, int] = {}  # string ID -> faiss index position
        self._load_or_create()

    def _load_or_create(self):
        """Load existing index or create new one."""
        try:
            import faiss
            if os.path.exists(self.index_path + ".index"):
                self.index = faiss.read_index(self.index_path + ".index")
                if os.path.exists(self.metadata_path):
                    with open(self.metadata_path, "r") as f:
                        data = json.load(f)
                        self.metadata = {int(k): v for k, v in data.get("metadata", {}).items()}
                        self._id_map = data.get("id_map", {})
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                self.index = faiss.IndexFlatIP(self.dim)  # Inner product for cosine sim
                logger.info("Created new FAISS index")
        except ImportError:
            logger.warning("FAISS not available, using in-memory fallback")
            self.index = None
            self.vectors = []

    def _save(self):
        """Persist index to disk."""
        try:
            import faiss
            dir_name = os.path.dirname(self.index_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            faiss.write_index(self.index, self.index_path + ".index")
            with open(self.metadata_path, "w") as f:
                json.dump({"metadata": self.metadata, "id_map": self._id_map}, f)
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def add(self, embedding: List[float], metadata: Dict, doc_id: Optional[str] = None) -> str:
        """Add a vector to the store. Returns the string ID."""
        doc_id = doc_id or str(uuid.uuid4())
        vec = np.array([embedding], dtype=np.float32)

        if self.index is not None:
            pos = self.index.ntotal
            self.index.add(vec)
            self.metadata[pos] = metadata
            self._id_map[doc_id] = pos
            self._save()
        else:
            # Fallback in-memory
            if not hasattr(self, 'vectors'):
                self.vectors = []
            self.vectors.append((doc_id, embedding, metadata))

        return doc_id

    def search(self, query_embedding: List[float], k: int = 10) -> List[Dict]:
        """Search for k most similar vectors. Returns list of results with scores."""
        # FAISS path
        if self.index is not None:
            if self.index.ntotal == 0:
                return []
            query_vec = np.array([query_embedding], dtype=np.float32)
            k = min(k, self.index.ntotal)
            scores, indices = self.index.search(query_vec, k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx in self.metadata:
                    result = self.metadata[idx].copy()
                    result["similarity_score"] = float(score)
                    results.append(result)
            return results

        # In-memory fallback
        if not hasattr(self, 'vectors') or not self.vectors:
            return []
        query_vec = np.array(query_embedding)
        scored = []
        for doc_id, emb, meta in self.vectors:
            sim = self.get_similarity(query_embedding, emb)
            scored.append((sim, meta))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {**meta, "similarity_score": float(score)}
            for score, meta in scored[:k]
        ]

    def get_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        if not emb1 or not emb2:
            return 0.0
        v1 = np.array(emb1, dtype=np.float32)
        v2 = np.array(emb2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.clip(np.dot(v1, v2) / (norm1 * norm2), 0.0, 1.0))


# Singleton instances
_embedding_generator: Optional[EmbeddingGenerator] = None
_vector_store: Optional[FAISSVectorStore] = None


def get_embedding_generator() -> EmbeddingGenerator:
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator


def get_vector_store() -> FAISSVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(
            index_path=settings.FAISS_INDEX_PATH,
            dim=settings.EMBEDDING_DIM
        )
    return _vector_store
