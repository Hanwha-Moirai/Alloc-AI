from infrastructure.ingestion.chunk import chunk_text
from infrastructure.ingestion.embed import embed_text
from infrastructure.ingestion.index import index_embeddings


class IngestionService:
    def ingest(self, doc_id: str, text: str, metadata: dict) -> None:
        chunks = chunk_text(text)
        vectors = embed_text(chunks)
        index_embeddings(doc_id, chunks, vectors, metadata)
