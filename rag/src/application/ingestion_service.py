import logging
from pathlib import Path

from infrastructure.ingestion.chunk import chunk_text
from infrastructure.ingestion.docs_loader import DocumentPayload, iter_pdfs_from_dir, load_pdf
from infrastructure.ingestion.keywords import extract_keywords
from infrastructure.langchain_store import upsert_chunks
from infrastructure.mariadb_repo import MariaDBRepository
from application.type_extraction import extract_risk_profile

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self) -> None:
        self._repo = MariaDBRepository()

    def ingest(self, doc_id: str, text: str, metadata: dict) -> None:
        # 2단계: 원문 -> 청크
        chunks = chunk_text(text)
        chunk_keywords = [extract_keywords(chunk, top_n=10) for chunk in chunks]
        # 3단계: 청크 -> 임베딩 -> 벡터 DB 저장 (LangChain VectorStore)
        upsert_chunks(doc_id, chunks, metadata, chunk_keywords=chunk_keywords)

    def ingest_data_dir(self, data_dir: str) -> None:
        saw_any = False
        for payload in iter_pdfs_from_dir(data_dir):
            saw_any = True
            if not payload.text:
                continue
            self.ingest(payload.doc_id, payload.text, payload.metadata)
        if not saw_any:
            logger.warning("No PDF files found under data dir: %s", data_dir)

    def extract_raw_texts(self, data_dir: str | None = None) -> list[DocumentPayload]:
        resolved_dir = data_dir or str(Path(__file__).resolve().parents[1] / "data")
        payloads = list(iter_pdfs_from_dir(resolved_dir))
        if not payloads:
            logger.warning("No PDF files found under data dir: %s", resolved_dir)
        return payloads

    def ingest_pdf_file(self, file_path: Path, base_dir: Path) -> None:
        print(f"[Ingestion] start file={file_path}", flush=True)
        payload = load_pdf(file_path, base_dir)
        if not payload.text:
            print(f"[Ingestion] empty text file={file_path}", flush=True)
            logger.warning("Empty PDF text extracted: %s", file_path)
            return
        # Extract risk profile (types + factors) from PDF and persist for later use.
        try:
            profile = extract_risk_profile(payload.text)
            if profile:
                self._repo.upsert_risk_profile(
                    doc_id=payload.doc_id,
                    risk_profile=profile,
                )
        except Exception as exc:
            logger.warning("Failed to extract risk profile: %s", exc)
        print(f"[Ingestion] extracted chars={len(payload.text)} file={file_path}", flush=True)
        self.ingest(payload.doc_id, payload.text, payload.metadata)
        print(f"[Ingestion] upsert done doc_id={payload.doc_id}", flush=True)
