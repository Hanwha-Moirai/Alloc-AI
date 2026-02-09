import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from fastapi.params import Form
from fastapi.params import File
from fastapi_pagination import Page, Params, create_page

from application.ingestion_service import IngestionService
from application.risk_report_service import RiskReportService
from config import settings
from infrastructure.qdrant_health import health as qdrant_health
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


@router.get(
    "/api/projects/{project_id}/docs/risk_types",
    response_model=list[schemas.RiskTypeSummaryItem],
)
def get_risk_type_summary(
    project_id: str,
    service: RiskReportService = Depends(get_risk_report_service),
) -> list[schemas.RiskTypeSummaryItem]:
    items = service.risk_type_summary(project_id=project_id)
    return [
        schemas.RiskTypeSummaryItem(
            risk_type=str(item.get("risk_type") or ""),
            count=int(item.get("cnt") or 0),
        )
        for item in items
    ]


@router.post("/upload/pdf", status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
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
    # 파일 저장을 스트리밍으로 처리해서 메모리 사용/응답 지연을 줄임
    with target_path.open("wb") as out_file:
        file.file.seek(0)
        shutil.copyfileobj(file.file, out_file)
    print(f"[Upload] saved path={target_path}", flush=True)

    def _background_ingest() -> None:
        # 업로드 기록 저장 및 파싱/청킹/임베딩 적재를 백그라운드로 이동
        service.register_pdf_upload(
            doc_id=safe_name,
            file_name=safe_name,
            file_path=str(target_path),
        )
        service.ingest_pdf_file(target_path, data_dir, project_id=project_id)

    # 업로드는 즉시 응답하고, 이후 처리는 백그라운드에서 수행
    background_tasks.add_task(_background_ingest)
    return {"status": "accepted", "doc_id": safe_name, "path": str(target_path)}


@router.get("/api/docs/pdf", response_model=list[schemas.PdfDocumentListItem])
def list_pdf_documents(
    service: IngestionService = Depends(get_ingestion_service),
) -> list[schemas.PdfDocumentListItem]:
    items = service.list_pdf_documents()
    return [
        schemas.PdfDocumentListItem(
            doc_id=str(item.get("doc_id") or ""),
            file_name=str(item.get("file_name") or ""),
            upload_status=str(item.get("upload_status") or ""),
            uploaded_at=item.get("uploaded_at"),
            summary_text=item.get("summary_text"),
        )
        for item in items
    ]


@router.get("/health/qdrant")
def health_qdrant() -> dict:
    try:
        detail = qdrant_health()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Qdrant unavailable") from exc
    return {"status": "ok", **detail}


@router.get("/health")
def health_basic() -> dict:
    # ELB 헬스 체크용: 외부 의존성 없이 즉시 200 응답
    return {"status": "ok"}
