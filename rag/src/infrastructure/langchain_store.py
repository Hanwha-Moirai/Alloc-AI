from __future__ import annotations

import uuid
from typing import List, Tuple

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient

from config import settings

_embeddings: HuggingFaceBgeEmbeddings | None = None
_client: QdrantClient | None = None
_vectorstore: QdrantVectorStore | None = None


class QdrantCollectionMissing(Exception):
    pass


def get_embeddings() -> HuggingFaceBgeEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceBgeEmbeddings(
            model_name=settings.embedding_model,
            encode_kwargs={"normalize_embeddings": settings.embedding_normalize},
        )
    return _embeddings


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    return _client


def get_vectorstore() -> QdrantVectorStore:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = QdrantVectorStore(
            client=get_qdrant_client(),
            collection_name=settings.qdrant_collection,
            embedding=get_embeddings(),
        )
    return _vectorstore


def upsert_chunks(
    doc_id: str,
    chunks: List[str],
    metadata: dict,
    *,
    chunk_keywords: List[List[str]] | None = None,
) -> None:
    if not chunks:
        return
    if chunk_keywords is not None and len(chunk_keywords) != len(chunks):
        raise ValueError("chunk_keywords length must match chunks length.")
    metadatas = []
    ids = []
    for idx, chunk in enumerate(chunks):
        payload = {**metadata, "doc_id": doc_id, "chunk_index": idx}
        if chunk_keywords is not None:
            payload["keywords"] = chunk_keywords[idx]
        metadatas.append(payload)
        ids.append(str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{idx}")))
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        global _vectorstore
        _vectorstore = QdrantVectorStore.from_texts(
            texts=chunks,
            embedding=get_embeddings(),
            metadatas=metadatas,
            ids=ids,
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            collection_name=settings.qdrant_collection,
        )
        return
    vectorstore = get_vectorstore()
    vectorstore.add_texts(chunks, metadatas=metadatas, ids=ids)


def similarity_search_with_score(query: str, k: int) -> List[Tuple[Document, float]]:
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        raise QdrantCollectionMissing(
            f"Qdrant collection not found: {settings.qdrant_collection}"
        )
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search_with_score(query, k=k)
