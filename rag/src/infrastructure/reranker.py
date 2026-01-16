from typing import List

from domain.models import SearchResult


class Reranker:
    def rerank(self, query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        # Stub reranker: keep order and trim
        return results[:top_k]
