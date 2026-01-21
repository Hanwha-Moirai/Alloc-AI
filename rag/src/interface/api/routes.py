from fastapi import APIRouter, Depends, HTTPException, status

from application.ingestion_service import IngestionService
from application.rag_service import RagService
from application.weekly_report_service import WeeklyReportService
from infrastructure.qdrant_store import QdrantAdapter
from interface.api import schemas
from interface.api.deps import get_ingestion_service, get_rag_service, get_weekly_report_service

router = APIRouter()


@router.post("/search", response_model=schemas.SearchResponse)
def search(
    payload: schemas.SearchRequest,
    service: RagService = Depends(get_rag_service),
) -> schemas.SearchResponse:
    results = service.search(payload.query, top_k=payload.top_k)
    return schemas.SearchResponse(results=[schemas.SearchResult.from_domain(item) for item in results])


@router.post("/answer", response_model=schemas.AnswerResponse)
def answer(
    payload: schemas.AnswerRequest,
    service: RagService = Depends(get_rag_service),
) -> schemas.AnswerResponse:
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
    service.ingest(payload.doc_id, payload.text, payload.metadata)
    return {"status": "ok"}


@router.post("/weekly-report/generate", response_model=schemas.WeeklyReportGenerateResponse)
def generate_weekly_report(
    payload: schemas.WeeklyReportGenerateRequest,
    service: WeeklyReportService = Depends(get_weekly_report_service),
) -> schemas.WeeklyReportGenerateResponse:
    try:
        result = service.generate(
            project_id=payload.project_id,
            week_start=payload.week_start,
            week_end=payload.week_end,
            as_of_timestamp=payload.as_of_timestamp,
        )
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc
    return schemas.WeeklyReportGenerateResponse(
        weekly_report_draft=result.weekly_report_draft,
        schedule_risk_report=result.schedule_risk_report,
    )


@router.get("/health/qdrant")
def health_qdrant() -> dict:
    adapter = QdrantAdapter()
    try:
        detail = adapter.health()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Qdrant unavailable") from exc
    return {"status": "ok", **detail}
