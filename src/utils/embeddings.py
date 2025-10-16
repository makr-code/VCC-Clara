"""Embedding Backend Stub

Erweiterbar für Phase 2 Routing (Semantische Ähnlichkeit).
Aktuell Dummy Implementierung, die konstante Vektoren oder Hash-basierte Pseudo-Werte liefert.
"""
from __future__ import annotations
from typing import List, Sequence, Optional
import hashlib
import math

class EmbeddingBackend:
    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        raise NotImplementedError

class DummyEmbeddingBackend(EmbeddingBackend):
    def __init__(self, dim: int = 16) -> None:
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        vecs = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # Nimm die ersten dim Bytes und normiere grob
            raw = [b / 255.0 for b in h[: self.dim]]
            # L2 Normalisierung
            norm = math.sqrt(sum(x * x for x in raw)) or 1.0
            vecs.append([x / norm for x in raw])
        return vecs

class SentenceTransformerEmbeddingBackend(EmbeddingBackend):  # pragma: no cover - optional heavy dependency
    """Wrapper um sentence-transformers (optional).

    Lazy Import um Importkosten zu minimieren, wenn Feature nicht genutzt wird.
    Fällt still auf DummyEmbeddingBackend zurück, wenn Bibliothek fehlt.
    """

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device: Optional[str] = None):
        self.model_name = model_name
        self.device = device
        self._model = None  # type: ignore

    def _ensure_model(self):
        if self._model is not None:
            return
        try:  # pragma: no cover
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(self.model_name, device=self.device)
        except Exception:
            # Fallback: Nutze Dummy Backend intern
            self._model = DummyEmbeddingBackend(dim=16)

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        self._ensure_model()
        if isinstance(self._model, DummyEmbeddingBackend):  # type: ignore
            return self._model.embed(texts)  # type: ignore
        try:  # pragma: no cover
            embs = self._model.encode(list(texts), normalize_embeddings=True)  # type: ignore
            return [list(map(float, v)) for v in embs]
        except Exception:
            # Graceful degrade
            dummy = DummyEmbeddingBackend(dim=16)
            return dummy.embed(texts)

__all__ = ["EmbeddingBackend", "DummyEmbeddingBackend", "SentenceTransformerEmbeddingBackend"]
