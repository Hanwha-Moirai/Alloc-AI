from typing import List, Protocol

from domain.models import SearchResult


class VectorStore(Protocol):
    def search(self, query: str, k: int) -> List[SearchResult]:
        ...

    def upsert(self, doc_id: str, chunks: List[str], vectors: List[List[float]], metadata: dict) -> None:
        ...


class Reranker(Protocol):
    def rerank(self, query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        ...


class LLM(Protocol):
    def generate(self, prompt: str) -> str:
        ...


class PromptBuilder(Protocol):
    def build(self, query: str, contexts: List[SearchResult]) -> str:
        ...


class SafetyPolicy(Protocol):
    def ensure_safe(self, prompt: str) -> None:
        ...


class DocumentRepository(Protocol):
    def fetch_metadata(self, doc_id: str) -> dict:
        ...
