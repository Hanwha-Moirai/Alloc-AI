from __future__ import annotations

from qdrant_client import QdrantClient

from config import settings


def health() -> dict:
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    collections = client.get_collections()
    return {
        "collection_exists": client.collection_exists(settings.qdrant_collection),
        "collections": [item.name for item in collections.collections],
    }
