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

    def fetch_risk_profile(self) -> List[Dict[str, Any]]:
        sql = "SELECT risk_type, factors_json, source_doc_id, extracted_at FROM project_risk_profile"
        try:
            return self._query(sql, {})
        except Exception:
            return []

    def upsert_risk_profile(self, *, doc_id: str, risk_profile: List[Dict[str, Any]]) -> None:
        self._ensure_risk_profile_table()
        sql = (
            "INSERT INTO project_risk_profile (risk_type, factors_json, source_doc_id, extracted_at) "
            "VALUES (:risk_type, :factors_json, :source_doc_id, NOW())"
        )
        for item in risk_profile:
            try:
                self._execute(
                    sql,
                    {
                        "risk_type": str(item.get("risk_type") or ""),
                        "factors_json": json.dumps(item.get("factors") or [], ensure_ascii=False),
                        "source_doc_id": doc_id,
                    },
                )
            except Exception as exc:
                logger.warning("Failed to upsert risk profile: %s", exc)

    def _ensure_risk_profile_table(self) -> None:
        sql = (
            "CREATE TABLE IF NOT EXISTS project_risk_profile ("
            "  risk_profile_id INT PRIMARY KEY AUTO_INCREMENT,"
            "  risk_type VARCHAR(50) NOT NULL,"
            "  factors_json TEXT,"
            "  source_doc_id VARCHAR(255),"
            "  extracted_at DATETIME"
            ")"
        )
        try:
            self._execute(sql, {}, fetch=False)
        except Exception as exc:
            logger.warning("Failed to ensure risk profile table: %s", exc)

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

    def create_pdf_document(
        self,
        *,
        doc_id: str,
        file_name: str,
        file_path: str,
        upload_status: str,
    ) -> None:
        self._ensure_pdf_document_table()
        sql = (
            "INSERT INTO pdf_document (doc_id, file_name, file_path, upload_status, uploaded_at, updated_at) "
            "VALUES (:doc_id, :file_name, :file_path, :upload_status, NOW(), NOW())"
        )
        try:
            self._execute(
                sql,
                {
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "file_path": file_path,
                    "upload_status": upload_status,
                },
            )
        except Exception as exc:
            logger.warning("Failed to create pdf_document: %s", exc)

    def update_pdf_document_status(
        self,
        *,
        doc_id: str,
        upload_status: str,
        summary_text: str | None = None,
    ) -> None:
        self._ensure_pdf_document_table()
        sql = (
            "UPDATE pdf_document "
            "SET upload_status = :upload_status, summary_text = :summary_text, updated_at = NOW() "
            "WHERE doc_id = :doc_id"
        )
        try:
            self._execute(
                sql,
                {
                    "doc_id": doc_id,
                    "upload_status": upload_status,
                    "summary_text": summary_text,
                },
            )
        except Exception as exc:
            logger.warning("Failed to update pdf_document status: %s", exc)

    def _ensure_pdf_document_table(self) -> None:
        sql = (
            "CREATE TABLE IF NOT EXISTS pdf_document ("
            "  pdf_document_id INT PRIMARY KEY AUTO_INCREMENT,"
            "  doc_id VARCHAR(255) NOT NULL,"
            "  file_name VARCHAR(255) NOT NULL,"
            "  file_path TEXT NOT NULL,"
            "  summary_text TEXT,"
            "  upload_status VARCHAR(20) NOT NULL,"
            "  uploaded_at DATETIME,"
            "  updated_at DATETIME,"
            "  UNIQUE KEY uq_pdf_document_doc_id (doc_id)"
            ")"
        )
        try:
            self._execute(sql, {}, fetch=False)
        except Exception as exc:
            logger.warning("Failed to ensure pdf_document table: %s", exc)

    def fetch_risk_analysis_summaries(self, project_id: str, limit: int, offset: int) -> List[Dict[str, Any]]:
        sql = (
            "SELECT ra.risk_analysis_id, ra.project_id, p.name AS project_name, "
            "ra.summary_text, ra.likelihood, ra.impact, ra.created_at "
            "FROM risk_analysis ra "
            "LEFT JOIN project p ON p.project_id = ra.project_id "
            "WHERE ra.project_id = :project_id "
            "ORDER BY ra.created_at DESC "
            "LIMIT :limit OFFSET :offset"
        )
        rows = self._query(sql, {"project_id": project_id, "limit": limit, "offset": offset})
        return [
            {
                "report_id": row.get("risk_analysis_id"),
                "project_id": str(row.get("project_id")),
                "project_name": str(row.get("project_name") or ""),
                "summary": str(row.get("summary_text") or ""),
                "likelihood": int(row.get("likelihood") or 0),
                "impact": int(row.get("impact") or 0),
                "generated_at": row.get("created_at"),
            }
            for row in rows
        ]

    def fetch_risk_analysis_detail(self, project_id: str, report_id: int) -> Dict[str, Any] | None:
        sql = (
            "SELECT ra.risk_analysis_id, ra.project_id, p.name AS project_name, "
            "ra.summary_text, ra.rationale_text, ra.likelihood, ra.impact, "
            "ra.citations_json, ra.created_at "
            "FROM risk_analysis ra "
            "LEFT JOIN project p ON p.project_id = ra.project_id "
            "WHERE ra.project_id = :project_id AND ra.risk_analysis_id = :report_id"
        )
        rows = self._query(sql, {"project_id": project_id, "report_id": report_id})
        if not rows:
            return None
        row = rows[0]
        citations_raw = row.get("citations_json") or "[]"
        try:
            citations = json.loads(citations_raw)
        except (TypeError, json.JSONDecodeError):
            citations = []
        return {
            "report_id": row.get("risk_analysis_id"),
            "project_id": str(row.get("project_id")),
            "project_name": str(row.get("project_name") or ""),
            "summary": str(row.get("summary_text") or ""),
            "rationale": str(row.get("rationale_text") or ""),
            "likelihood": int(row.get("likelihood") or 0),
            "impact": int(row.get("impact") or 0),
            "generated_at": row.get("created_at"),
            "citations": citations,
        }

    def count_risk_analyses(self, project_id: str) -> int:
        sql = "SELECT COUNT(*) AS total FROM risk_analysis WHERE project_id = :project_id"
        rows = self._query(sql, {"project_id": project_id})
        if not rows:
            return 0
        try:
            return int(rows[0].get("total") or 0)
        except (TypeError, ValueError):
            return 0

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
            # SSL 옵션을 넘기기 위한 연결 파라미터 초기화
            connect_args: Dict[str, Any] = {}
            # CA 경로가 설정된 경우에만 SSL 검증 옵션을 활성화
            if settings.mariadb_ssl_ca:
                connect_args["ssl_ca"] = settings.mariadb_ssl_ca
                connect_args["ssl_verify_cert"] = settings.mariadb_ssl_verify
            MariaDBRepository._engine = create_engine(
                self.dsn,
                pool_pre_ping=True,
                # SSL 옵션이 없으면 기본 연결, 있으면 SSL 적용
                connect_args=connect_args,
            )
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
