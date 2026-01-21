from infrastructure.ingestion.chunk import chunk_text
from infrastructure.ingestion.docs_loader import iter_pdfs_from_dir
from infrastructure.ingestion.embed import embed_text
from infrastructure.ingestion.index import index_embeddings


class IngestionService:
    def ingest(self, doc_id: str, text: str, metadata: dict) -> None:
        chunks = chunk_text(text)
        vectors = embed_text(chunks)
        index_embeddings(doc_id, chunks, vectors, metadata)

    def ingest_docs_dir(self, docs_dir: str) -> None:
        for payload in iter_pdfs_from_dir(docs_dir):
            if not payload.text:
                continue
            self.ingest(payload.doc_id, payload.text, payload.metadata)
