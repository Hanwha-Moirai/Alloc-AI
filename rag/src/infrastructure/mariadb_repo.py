from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List
from urllib.parse import quote_plus

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine

from config import settings
from domain.models import RiskAnalysisResult

logger = logging.getLogger(__name__)


class MariaDBRepository:
    _engine: Engine | None = None

    def __init__(self, dsn: str = "") -> None:
        self.dsn = dsn or self._build_dsn()

    def fetch_metadata(self, doc_id: str) -> dict:
        _ = doc_id
        # Stub: replace with read-only MariaDB queries.
        return {}

    def fetch_project(self, project_id: str) -> Dict[str, Any]:
        sql = (
            "SELECT project_id, name, start_date, end_date, project_status, "
            "project_type, description, predicted_cost, partners "
            "FROM project WHERE project_id = :project_id"
        )
        rows = self._query(sql, {"project_id": project_id})
        return rows[0] if rows else {}

    def fetch_weekly_reports(self, project_id: str, week_start: date, week_end: date) -> List[Dict[str, Any]]:
        sql = (
            "SELECT report_id, project_id, week_start_date, week_end_date, report_status, "
            "change_of_plan, summary_text, task_completion_rate "
            "FROM weekly_report "
            "WHERE project_id = :project_id AND is_deleted = 0 "
            "AND week_start_date >= :week_start AND week_end_date <= :week_end"
        )
        return self._query(
            sql,
            {"project_id": project_id, "week_start": week_start, "week_end": week_end},
        )

    def fetch_meeting_records(
        self, project_id: str, start_dt: datetime, end_dt: datetime
    ) -> List[Dict[str, Any]]:
        meetings = self._query(
            "SELECT meeting_id, project_id, created_by, progress, meeting_date, meeting_time "
            "FROM meeting_record "
            "WHERE project_id = :project_id AND is_deleted = 0 AND meeting_date BETWEEN :start_dt AND :end_dt",
            {"project_id": project_id, "start_dt": start_dt, "end_dt": end_dt},
        )
        if not meetings:
            return []
        meeting_ids = [row["meeting_id"] for row in meetings]
        agenda_rows = self._query(
            "SELECT meeting_id, discussion_title, discussion_content, discussion_result, agenda_type "
            "FROM agenda WHERE meeting_id IN :meeting_ids",
            {"meeting_ids": meeting_ids},
            expanding_params={"meeting_ids": meeting_ids},
        )
        agendas_by_meeting: Dict[int, List[Dict[str, Any]]] = {}
        for row in agenda_rows:
            agendas_by_meeting.setdefault(row["meeting_id"], []).append(row)
        for meeting in meetings:
            agendas = agendas_by_meeting.get(meeting["meeting_id"], [])
            meeting["agendas"] = agendas
            agenda_texts: List[str] = []
            for agenda in agendas:
                agenda_texts.extend(
                    [
                        agenda.get("discussion_title", ""),
                        agenda.get("discussion_content", ""),
                        agenda.get("discussion_result", ""),
                    ]
                )
            meeting["agenda_summary"] = " ".join(item for item in agenda_texts if item)
        return meetings

    def fetch_events_logs(self, project_id: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        sql = (
            "SELECT l.event_log_id, l.event_id, l.change_type, l.log_description, "
            "l.before_start_date, l.after_start_date, l.before_end_date, l.after_end_date, l.created_at "
            "FROM events_log l "
            "JOIN events e ON e.event_id = l.event_id "
            "WHERE e.project_id = :project_id AND l.created_at BETWEEN :start_dt AND :end_dt"
        )
        return self._query(sql, {"project_id": project_id, "start_dt": start_dt, "end_dt": end_dt})

    def fetch_task_update_logs(
        self, project_id: str, start_dt: datetime, end_dt: datetime
    ) -> List[Dict[str, Any]]:
        sql = (
            "SELECT l.task_update_log_id, l.task_id, l.update_reason, l.created_at "
            "FROM task_update_log l "
            "JOIN task t ON t.task_id = l.task_id "
            "JOIN milestone m ON m.milestone_id = t.milestone_id "
            "WHERE m.project_id = :project_id AND l.created_at BETWEEN :start_dt AND :end_dt"
        )
        return self._query(sql, {"project_id": project_id, "start_dt": start_dt, "end_dt": end_dt})

    def fetch_milestone_update_logs(
        self, project_id: str, start_dt: datetime, end_dt: datetime
    ) -> List[Dict[str, Any]]:
        sql = (
            "SELECT l.milestone_update_log_id, l.milestone_id, l.update_reason, l.created_at "
            "FROM milestone_update_log l "
            "JOIN milestone m ON m.milestone_id = l.milestone_id "
            "WHERE m.project_id = :project_id AND l.created_at BETWEEN :start_dt AND :end_dt"
        )
        return self._query(sql, {"project_id": project_id, "start_dt": start_dt, "end_dt": end_dt})

    def fetch_project_documents(self, project_id: str) -> List[Dict[str, Any]]:
        _ = project_id
        # project_document에는 project_id가 없어서 전체 문서를 반환
        sql = "SELECT doc_id, file_path, extracted_text, uploaded_at FROM project_document"
        return self._query(sql, {})

    def save_risk_analysis(self, result: RiskAnalysisResult) -> None:
        sql = (
            "INSERT INTO risk_analysis (project_id, likelihood, impact, summary_text, rationale_text, "
            "citations_json, created_at) "
            "VALUES (:project_id, :likelihood, :impact, :summary_text, :rationale_text, :citations_json, :created_at)"
        )
        citations_json = json.dumps(result.citations, ensure_ascii=False)
        try:
            self._execute(
                sql,
                {
                    "project_id": result.project_id,
                    "likelihood": result.likelihood,
                    "impact": result.impact,
                    "summary_text": result.summary,
                    "rationale_text": result.rationale,
                    "citations_json": citations_json,
                    "created_at": result.generated_at,
                },
            )
        except Exception as exc:
            logger.warning("Failed to save risk analysis result: %s", exc)

    def _build_dsn(self) -> str:
        password = quote_plus(settings.mariadb_password)
        return (
            f"mariadb+mariadbconnector://{settings.mariadb_user}:{password}"
            f"@{settings.mariadb_host}:{settings.mariadb_port}/{settings.mariadb_database}"
        )

    def _query(
        self, sql: str, params: dict[str, Any], expanding_params: dict[str, List[Any]] | None = None
    ) -> List[Dict[str, Any]]:
        return self._execute(sql, params, fetch=True, expanding_params=expanding_params)

    def _execute(
        self,
        sql: str,
        params: dict[str, Any],
        fetch: bool = False,
        expanding_params: dict[str, List[Any]] | None = None,
    ) -> Any:
        self._ensure_credentials()
        statement = text(sql)
        if expanding_params:
            for key in expanding_params.keys():
                statement = statement.bindparams(bindparam(key, expanding=True))
        engine = self._get_engine()
        with engine.begin() as conn:
            result = conn.execute(statement, params)
            if fetch:
                return [dict(row) for row in result.mappings().all()]
        return []

    def _get_engine(self) -> Engine:
        if MariaDBRepository._engine is None:
            MariaDBRepository._engine = create_engine(self.dsn, pool_pre_ping=True)
        return MariaDBRepository._engine

    def _ensure_credentials(self) -> None:
        missing = []
        if not settings.mariadb_user:
            missing.append("RAG_MARIADB_USER")
        if not settings.mariadb_password:
            missing.append("RAG_MARIADB_PASSWORD")
        if not settings.mariadb_database:
            missing.append("RAG_MARIADB_DATABASE")
        if missing:
            raise ValueError(f"Missing MariaDB settings: {', '.join(missing)}")
