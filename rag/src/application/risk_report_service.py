from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List

from domain.models import RiskAnalysisResult
from infrastructure.llm_client import LLMClient
from infrastructure.mariadb_repo import MariaDBRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskReportContext:
    project: Dict[str, Any]
    weekly_reports: List[Dict[str, Any]]
    meeting_records: List[Dict[str, Any]]
    events_logs: List[Dict[str, Any]]
    task_update_logs: List[Dict[str, Any]]
    milestone_update_logs: List[Dict[str, Any]]
    project_documents: List[Dict[str, Any]]


class RiskReportService:
    def __init__(self) -> None:
        self._repo = MariaDBRepository()
        self._llm = LLMClient()

    def generate(self, *, project_id: str, week_start: date, week_end: date) -> RiskAnalysisResult:
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end, time.max)
        context = RiskReportContext(
            project=self._repo.fetch_project(project_id),
            weekly_reports=self._repo.fetch_weekly_reports(project_id, week_start, week_end),
            meeting_records=self._repo.fetch_meeting_records(project_id, start_dt, end_dt),
            events_logs=self._repo.fetch_events_logs(project_id, start_dt, end_dt),
            task_update_logs=self._repo.fetch_task_update_logs(project_id, start_dt, end_dt),
            milestone_update_logs=self._repo.fetch_milestone_update_logs(project_id, start_dt, end_dt),
            project_documents=self._repo.fetch_project_documents(project_id),
        )
        citations = self._build_citations(context)
        prompt = self._build_prompt(context, citations)
        raw = self._llm.generate(prompt)
        parsed = self._parse_json(raw)

        likelihood = self._clamp_score(parsed.get("likelihood", 3))
        impact = self._clamp_score(parsed.get("impact", 3))
        summary = str(parsed.get("summary", "")).strip() or "요약을 생성하지 못했습니다."
        rationale = str(parsed.get("rationale", "")).strip() or "근거를 생성하지 못했습니다."

        generated_at = datetime.utcnow()
        result = RiskAnalysisResult(
            project_id=project_id,
            likelihood=likelihood,
            impact=impact,
            summary=summary,
            rationale=rationale,
            generated_at=generated_at,
            citations=citations,
        )
        self._repo.save_risk_analysis(result)
        return result

    def _build_prompt(self, context: RiskReportContext, citations: List[Dict[str, str]]) -> str:
        return (
            "너는 IT 프로젝트 리스크 관리 전문가다. 아래 문서들을 근거로 "
            "일정 지연 리스크를 PI 매트릭스(발생 가능성/영향도 1~5)로 평가하라.\n"
            "사내 리스크 데이터가 충분하지 않아 몬테카를로 대신 정성적 PI 매트릭스를 사용한다.\n"
            "문서 기반 정성 분석은 LLM이 잘하기 때문에 RAG로 근거를 요약한다.\n\n"
            "응답은 JSON만 출력하고, 다음 키를 포함하라:\n"
            '{"likelihood": 1, "impact": 1, "summary": "...", "rationale": "..."}\n\n'
            f"[프로젝트 메타]\n{json.dumps(context.project, ensure_ascii=False)}\n\n"
            f"[주간 보고]\n{json.dumps(context.weekly_reports, ensure_ascii=False)}\n\n"
            f"[회의록]\n{json.dumps(context.meeting_records, ensure_ascii=False)}\n\n"
            f"[일정 변경 로그]\n{json.dumps(context.events_logs, ensure_ascii=False)}\n\n"
            f"[태스크 변경 로그]\n{json.dumps(context.task_update_logs, ensure_ascii=False)}\n\n"
            f"[마일스톤 변경 로그]\n{json.dumps(context.milestone_update_logs, ensure_ascii=False)}\n\n"
            f"[프로젝트 문서]\n{json.dumps(context.project_documents, ensure_ascii=False)}\n\n"
            f"[참고 문서 목록]\n{json.dumps(citations, ensure_ascii=False)}\n"
        )

    def _build_citations(self, context: RiskReportContext) -> List[Dict[str, str]]:
        citations: List[Dict[str, str]] = []
        for item in context.weekly_reports:
            citations.append(self._citation("weekly_report", item.get("report_id"), item.get("summary_text")))
        for item in context.meeting_records:
            citations.append(self._citation("meeting_record", item.get("meeting_id"), item.get("agenda_summary")))
        for item in context.events_logs:
            citations.append(self._citation("events_log", item.get("event_log_id"), item.get("log_description")))
        for item in context.task_update_logs:
            citations.append(self._citation("task_update_log", item.get("task_update_log_id"), item.get("update_reason")))
        for item in context.milestone_update_logs:
            citations.append(
                self._citation("milestone_update_log", item.get("milestone_update_log_id"), item.get("update_reason"))
            )
        for item in context.project_documents:
            citations.append(self._citation("project_document", item.get("doc_id"), item.get("extracted_text")))
        return [item for item in citations if item["excerpt"]]

    def _citation(self, source_type: str, source_id: Any, text: Any) -> Dict[str, str]:
        excerpt = str(text or "").strip().replace("\n", " ")
        if len(excerpt) > 240:
            excerpt = excerpt[:240] + "..."
        return {
            "source_type": source_type,
            "source_id": str(source_id) if source_id is not None else "",
            "excerpt": excerpt,
        }

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from LLM output.")
        return {}

    def _clamp_score(self, value: Any) -> int:
        try:
            score = int(value)
        except (ValueError, TypeError):
            return 3
        return max(1, min(5, score))
