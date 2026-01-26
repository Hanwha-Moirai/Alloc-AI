from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List

import logging

from config import settings
from domain.models import SearchResult
from infrastructure.mariadb_repo import MariaDBRepository
from infrastructure.qdrant_store import QdrantAdapter


@dataclass(frozen=True)
class RiskReportContext:
    project: Dict[str, Any]
    weekly_reports: List[Dict[str, Any]]
    meeting_records: List[Dict[str, Any]]
    events_logs: List[Dict[str, Any]]
    task_update_logs: List[Dict[str, Any]]
    milestone_update_logs: List[Dict[str, Any]]
    project_documents: List[Dict[str, Any]]
    vector_evidence: List[Dict[str, Any]]


class RiskReportRetriever:
    # 리스크 리포트에 필요한 데이터를 MariaDB/Qdrant에서 수집하는 리트리버
    def __init__(self) -> None:
        self._repo = MariaDBRepository()
        self._vector = QdrantAdapter()

    def fetch(self, *, project_id: str, week_start: date, week_end: date) -> RiskReportContext:
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end, time.max)
        project = self._repo.fetch_project(project_id)
        weekly_reports = self._repo.fetch_weekly_reports(project_id, week_start, week_end)
        meeting_records = self._repo.fetch_meeting_records(project_id, start_dt, end_dt)
        events_logs = self._repo.fetch_events_logs(project_id, start_dt, end_dt)
        task_update_logs = self._repo.fetch_task_update_logs(project_id, start_dt, end_dt)
        milestone_update_logs = self._repo.fetch_milestone_update_logs(project_id, start_dt, end_dt)
        project_documents = self._repo.fetch_project_documents(project_id)
        vector_hits = self._fetch_vector_evidence(project_id, week_start, week_end)
        logger.info("RiskReport vector_evidence_count=%d", len(vector_hits))
        return RiskReportContext(
            project=project,
            weekly_reports=weekly_reports,
            meeting_records=meeting_records,
            events_logs=events_logs,
            task_update_logs=task_update_logs,
            milestone_update_logs=milestone_update_logs,
            project_documents=project_documents,
            vector_evidence=vector_hits,
        )

    def _fetch_vector_evidence(self, project_id: str, week_start: date, week_end: date) -> List[Dict[str, Any]]:
        query = f"프로젝트 {project_id} 일정 지연 리스크 분석 ({week_start}~{week_end})"
        results = self._vector.search(query, k=settings.top_k)
        return [self._to_evidence(item) for item in results]

    def _to_evidence(self, item: SearchResult) -> Dict[str, Any]:
        return {
            "doc_id": item.doc_id,
            "score": item.score,
            "text": item.text,
            "metadata": item.metadata,
        }
logger = logging.getLogger(__name__)
