import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.params import File
from fastapi_pagination import Page, Params, create_page

from application.ingestion_service import IngestionService
from application.risk_report_service import RiskReportService
from config import settings
from infrastructure.qdrant_store import QdrantAdapter
from interface.api import schemas
from interface.api.deps import get_ingestion_service, get_risk_report_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/projects/{project_id}/docs/risk_report", response_model=schemas.RiskReportResponse)
def generate_risk_report(
    project_id: str,
    payload: schemas.RiskReportRequest,
    service: RiskReportService = Depends(get_risk_report_service),
) -> schemas.RiskReportResponse:
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


@router.get(
    "/api/projects/{project_id}/docs/risk_reports",
    response_model=Page[schemas.RiskReportListItem],
)
def list_risk_reports(
    project_id: str,
    params: Params = Depends(),
    service: RiskReportService = Depends(get_risk_report_service),
) -> Page[schemas.RiskReportListItem]:
    results, total = service.list(project_id=project_id, page=params.page, size=params.size)
    items = [
        schemas.RiskReportListItem(
            report_id=item["report_id"],
            project_id=item["project_id"],
            project_name=item["project_name"],
            summary=item["summary"],
            likelihood=item["likelihood"],
            impact=item["impact"],
            generated_at=item["generated_at"],
        )
        for item in results
    ]
    return create_page(items, total, params)


@router.get(
    "/api/projects/{project_id}/docs/risk_reports/{report_id}",
    response_model=schemas.RiskReportDetailResponse,
)
def get_risk_report(
    project_id: str,
    report_id: int,
    service: RiskReportService = Depends(get_risk_report_service),
) -> schemas.RiskReportDetailResponse:
    result = service.get_detail(project_id=project_id, report_id=report_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk report not found.")
    return schemas.RiskReportDetailResponse(
        report_id=result["report_id"],
        project_id=result["project_id"],
        project_name=result["project_name"],
        summary=result["summary"],
        likelihood=result["likelihood"],
        impact=result["impact"],
        rationale=result["rationale"],
        generated_at=result["generated_at"],
        citations=[schemas.RiskCitation(**item) for item in result["citations"]],
    )


@router.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    service: IngestionService = Depends(get_ingestion_service),
) -> dict:
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
    adapter = QdrantAdapter()
    try:
        detail = adapter.health()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Qdrant unavailable") from exc
    return {"status": "ok", **detail}
