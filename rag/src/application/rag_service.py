from typing import List, Optional

from config import settings
from domain.models import SearchResult
from domain.ports import DocumentRepository, LLM, PromptBuilder, Reranker, SafetyPolicy, VectorStore


class RagService:
    def __init__(
        self,
        *,
        vector_store: VectorStore,
        reranker: Reranker,
        llm: LLM,
        prompt_builder: PromptBuilder,
        safety: SafetyPolicy,
        documents: Optional[DocumentRepository] = None,
    ) -> None:
        self._vector_store = vector_store
        self._reranker = reranker
        self._llm = llm
        self._prompt_builder = prompt_builder
        self._safety = safety
        self._documents = documents

    def search(self, query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        k = top_k or settings.top_k
        raw = self._vector_store.search(query, k=settings.rerank_k)
        ranked = self._reranker.rerank(query, raw, top_k=k)
        return self._enrich(ranked)

    def answer(self, query: str, top_k: Optional[int] = None) -> tuple[str, List[SearchResult]]:
        results = self.search(query, top_k=top_k)
        prompt = self._prompt_builder.build(query, results)
        self._safety.ensure_safe(prompt)
        response = self._llm.generate(prompt)
        return response, results

    def _enrich(self, results: List[SearchResult]) -> List[SearchResult]:
        if not self._documents:
            return results
        enriched: List[SearchResult] = []
        for item in results:
            metadata = {**item.metadata, **self._documents.fetch_metadata(item.doc_id)}
            enriched.append(SearchResult(doc_id=item.doc_id, score=item.score, text=item.text, metadata=metadata))
        return enriched
