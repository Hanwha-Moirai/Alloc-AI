from typing import List

from infrastructure.qdrant_store import QdrantAdapter


def index_embeddings(doc_id: str, chunks: List[str], vectors: List[List[float]], metadata: dict) -> None:
    adapter = QdrantAdapter()
    adapter.upsert(doc_id, chunks, vectors, metadata)
