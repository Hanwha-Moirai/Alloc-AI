import logging

from infrastructure.ingestion.chunk import chunk_text
from infrastructure.ingestion.docs_loader import iter_pdfs_from_dir
from infrastructure.ingestion.embed import embed_text
from infrastructure.ingestion.index import index_embeddings

logger = logging.getLogger(__name__)


class IngestionService:
    def ingest(self, doc_id: str, text: str, metadata: dict) -> None:
        # 1/2단계: 원문 -> 청크
        chunks = chunk_text(text)
        # 3단계: 청크 -> 임베딩
        vectors = embed_text(chunks)
        # 3단계: 임베딩 -> 벡터 DB 저장
        index_embeddings(doc_id, chunks, vectors, metadata)

    def ingest_data_dir(self, data_dir: str) -> None:
        saw_any = False
        for payload in iter_pdfs_from_dir(data_dir):
            saw_any = True
            if not payload.text:
                continue
            self.ingest(payload.doc_id, payload.text, payload.metadata)
        if not saw_any:
            logger.warning("No PDF files found under data dir: %s", data_dir)
