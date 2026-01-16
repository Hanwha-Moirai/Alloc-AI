from typing import List

from domain.models import SearchResult


class QdrantAdapter:
    def search(self, query: str, k: int) -> List[SearchResult]:
        # Stub: return empty results
        return []

    def upsert(self, doc_id: str, chunks: List[str], vectors: List[List[float]], metadata: dict) -> None:
        _ = (doc_id, chunks, vectors, metadata)
