import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.params import File

from application.ingestion_service import IngestionService
from application.rag_service import RagService
from application.risk_report_service import RiskReportService
from config import settings
from infrastructure.qdrant_store import QdrantAdapter
from interface.api import schemas
from interface.api.deps import get_ingestion_service, get_rag_service, get_risk_report_service

router = APIRouter()
logger = logging.getLogger(__name__)

# 검색/생성/적재 API 라우팅 모음
@router.post("/search", response_model=schemas.SearchResponse)
def search(
    payload: schemas.SearchRequest,
    service: RagService = Depends(get_rag_service),
) -> schemas.SearchResponse:
    # 쿼리 기반 검색 결과 반환
    results = service.search(payload.query, top_k=payload.top_k)
    return schemas.SearchResponse(results=[schemas.SearchResult.from_domain(item) for item in results])


@router.post("/answer", response_model=schemas.AnswerResponse)
def answer(
    payload: schemas.AnswerRequest,
    service: RagService = Depends(get_rag_service),
) -> schemas.AnswerResponse:
    # 검색 결과를 근거로 LLM 답변 생성
    response, results = service.answer(payload.query, top_k=payload.top_k)
    return schemas.AnswerResponse(
        answer=response,
        citations=[schemas.SearchResult.from_domain(item) for item in results],
    )


@router.post("/ingest")
def ingest(
    payload: schemas.IngestRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> dict:
    # 텍스트 입력을 청크/임베딩 후 벡터 DB에 적재
    service.ingest(payload.doc_id, payload.text, payload.metadata)
    return {"status": "ok"}


@router.post("/api/projects/{project_id}/docs/risk_report", response_model=schemas.RiskReportResponse)
def generate_risk_report(
    project_id: str,
    payload: schemas.RiskReportRequest,
    service: RiskReportService = Depends(get_risk_report_service),
) -> schemas.RiskReportResponse:
    # PI 매트릭스 기반 리스크 분석 요청 처리
    logger.info("RiskReport request project_id=%s week_start=%s week_end=%s", project_id, payload.week_start, payload.week_end)
    result = service.generate(project_id=project_id, week_start=payload.week_start, week_end=payload.week_end)
    return schemas.RiskReportResponse(
        project_id=project_id,
        likelihood=result.likelihood,
        impact=result.impact,
        summary=result.summary,
        rationale=result.rationale,
        generated_at=result.generated_at,
        citations=[schemas.RiskCitation(**item) for item in result.citations],
    )


@router.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    service: IngestionService = Depends(get_ingestion_service),
) -> dict:
    # 업로드된 PDF 파일을 data 디렉터리에 저장
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type.")
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    target_path = data_dir / safe_name
    content = await file.read()
    target_path.write_bytes(content)
    print(f"[Upload] saved path={target_path}", flush=True)
    service.ingest_pdf_file(target_path, data_dir)
    return {"status": "ok", "path": str(target_path)}


@router.get("/health/qdrant")
def health_qdrant() -> dict:
    # Qdrant 연결 상태 및 컬렉션 목록 확인
    adapter = QdrantAdapter()
    try:
        detail = adapter.health()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Qdrant unavailable") from exc
    return {"status": "ok", **detail}
