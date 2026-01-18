from typing import List

from config import settings

from domain.models import SearchResult


class QdrantAdapter:
    def __init__(self) -> None:
        self.url = settings.qdrant_url
        self.api_key = settings.qdrant_api_key

    def search(self, query: str, k: int) -> List[SearchResult]:
        # Stub: return empty results
        return []

    def upsert(self, doc_id: str, chunks: List[str], vectors: List[List[float]], metadata: dict) -> None:
        _ = (doc_id, chunks, vectors, metadata)
