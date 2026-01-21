from typing import List
import logging

from config import settings
from domain.models import SearchResult
from infrastructure.ingestion.embed import embed_text

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

logger = logging.getLogger(__name__)


class QdrantAdapter:
    def __init__(self) -> None:
        self.url = settings.qdrant_url
        self.api_key = settings.qdrant_api_key
        self.collection = settings.qdrant_collection
        self.client = QdrantClient(url=self.url, api_key=self.api_key or None)

    def search(self, query: str, k: int) -> List[SearchResult]:
        if not self._collection_exists():
            return []
        query_vector = embed_text([query])[0]
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=k,
            with_payload=True,
        )
        return [self._to_search_result(point) for point in results]

    def upsert(self, doc_id: str, chunks: List[str], vectors: List[List[float]], metadata: dict) -> None:
        if not chunks or not vectors:
            return
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors must be the same length.")
        self._ensure_collection(len(vectors[0]))
        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            payload = {
                "doc_id": doc_id,
                "chunk_index": idx,
                "text": chunk,
                "metadata": metadata,
            }
            point_id = f"{doc_id}:{idx}"
            points.append(rest.PointStruct(id=point_id, vector=vector, payload=payload))
        self.client.upsert(collection_name=self.collection, points=points)

    def health(self) -> dict:
        collections = self.client.get_collections()
        return {
            "collection_exists": self.client.collection_exists(self.collection),
            "collections": [item.name for item in collections.collections],
        }

    def _collection_exists(self) -> bool:
        try:
            return self.client.collection_exists(self.collection)
        except Exception:
            logger.exception("Failed to check Qdrant collection existence.")
            return False

    def _ensure_collection(self, vector_size: int) -> None:
        if self._collection_exists():
            return
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
        )

    def _to_search_result(self, point: rest.ScoredPoint) -> SearchResult:
        payload = point.payload or {}
        metadata = payload.get("metadata", {})
        metadata = {**metadata, "chunk_index": payload.get("chunk_index")}
        return SearchResult(
            doc_id=payload.get("doc_id", str(point.id)),
            score=point.score or 0.0,
            text=payload.get("text", ""),
            metadata=metadata,
        )
