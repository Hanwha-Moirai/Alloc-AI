from application.ingestion_service import IngestionService
from application.risk_report_service import RiskReportService


def get_ingestion_service() -> IngestionService:
    return IngestionService()


def get_risk_report_service() -> RiskReportService:
    return RiskReportService()
