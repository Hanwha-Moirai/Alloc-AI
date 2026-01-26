import logging
from typing import List

from langchain_huggingface import HuggingFaceBgeEmbeddings

from config import settings

logger = logging.getLogger(__name__)

_embedder: HuggingFaceBgeEmbeddings | None = None


def _get_embedder() -> HuggingFaceBgeEmbeddings:
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceBgeEmbeddings(
            model_name=settings.embedding_model,
            encode_kwargs={"normalize_embeddings": settings.embedding_normalize},
        )
        logger.info("Embedding model loaded: %s", settings.embedding_model)
    return _embedder


def embed_text(texts: List[str]) -> List[List[float]]:
    # 3단계: 임베딩(BGE)
    if not texts:
        return []
    print(f"[Embedding] start batch={len(texts)} chars={sum(len(t) for t in texts)}", flush=True)
    embedder = _get_embedder()
    vectors = embedder.embed_documents(texts)
    print(f"[Embedding] done vectors={len(vectors)} dim={len(vectors[0]) if vectors else 0}", flush=True)
    return vectors
