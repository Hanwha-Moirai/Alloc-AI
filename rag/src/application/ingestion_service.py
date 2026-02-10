import logging
from pathlib import Path

from infrastructure.ingestion.chunk import chunk_text
from infrastructure.ingestion.docs_loader import DocumentPayload, iter_pdfs_from_dir, load_pdf
from infrastructure.ingestion.keywords import extract_keywords
from infrastructure.langchain_store import delete_doc_chunks, upsert_chunks
from infrastructure.mariadb_repo import MariaDBRepository
from application.type_extraction import extract_risk_profile

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self) -> None:
        self._repo = MariaDBRepository()

    def register_pdf_upload(self, *, doc_id: str, file_name: str, file_path: str) -> None:
        # 업로드 직후 상태는 PROCESSING 으로 저장
        self._repo.create_pdf_document(
            doc_id=doc_id,
            file_name=file_name,
            file_path=file_path,
            upload_status="PROCESSING",
        )

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

    def ingest_pdf_file(self, file_path: Path, base_dir: Path, project_id: str | None = None) -> None:
        print(f"[Ingestion] start file={file_path}", flush=True)
        try:
            payload = load_pdf(file_path, base_dir)
            if not payload.text:
                print(f"[Ingestion] empty text file={file_path}", flush=True)
                logger.warning("Empty PDF text extracted: %s", file_path)
                self._repo.update_pdf_document_status(
                    doc_id=payload.doc_id,
                    upload_status="FAILED",
                )
                return
            # Extract risk profile (types + factors) from PDF and persist for later use.
            try:
                profile = extract_risk_profile(payload.text)
                if profile:
                    self._repo.upsert_risk_profile(
                        doc_id=payload.doc_id,
                        project_id=project_id,
                        risk_profile=profile,
                    )
            except Exception as exc:
                logger.warning("Failed to extract risk profile: %s", exc)
            print(f"[Ingestion] extracted chars={len(payload.text)} file={file_path}", flush=True)
            self.ingest(payload.doc_id, payload.text, payload.metadata)
            self._repo.update_pdf_document_status(
                doc_id=payload.doc_id,
                upload_status="SUCCESS",
            )
            print(f"[Ingestion] upsert done doc_id={payload.doc_id}", flush=True)
        except Exception as exc:
            logger.exception("PDF ingestion failed: %s", exc)
            try:
                self._repo.update_pdf_document_status(
                    doc_id=file_path.name,
                    upload_status="FAILED",
                )
            except Exception:
                logger.warning("Failed to update pdf_document status for %s", file_path.name)

    def list_pdf_documents(self) -> list[dict]:
        return self._repo.fetch_pdf_documents()

    def delete_pdf_document(self, *, doc_id: str) -> bool:
        record = self._repo.fetch_pdf_document(doc_id=doc_id)
        if record is None:
            return False
        file_path = record.get("file_path")
        try:
            delete_doc_chunks(doc_id)
        except Exception as exc:
            logger.warning("Failed to delete qdrant chunks for %s: %s", doc_id, exc)
        if file_path:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("Failed to delete pdf file %s: %s", file_path, exc)
        return self._repo.delete_pdf_document(doc_id=doc_id)
