from application.ingestion_service import IngestionService
from application.prompt_builder import DefaultPromptBuilder
from application.rag_service import RagService
from application.safety import DefaultSafetyPolicy
from application.risk_report_service import RiskReportService
from infrastructure.llm_client import LLMClient
from infrastructure.mariadb_repo import MariaDBRepository
from infrastructure.qdrant_store import QdrantAdapter
from infrastructure.reranker import Reranker


def get_rag_service() -> RagService:
    return RagService(
        vector_store=QdrantAdapter(),
        reranker=Reranker(),
        llm=LLMClient(),
        prompt_builder=DefaultPromptBuilder(),
        safety=DefaultSafetyPolicy(),
        documents=MariaDBRepository(),
    )


def get_ingestion_service() -> IngestionService:
    return IngestionService()


def get_risk_report_service() -> RiskReportService:
    return RiskReportService()
