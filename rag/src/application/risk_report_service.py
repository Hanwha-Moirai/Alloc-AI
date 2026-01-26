from __future__ import annotations

import logging
import time as time_module
from datetime import date, datetime, time, timedelta
from typing import Any, Dict
from zoneinfo import ZoneInfo

from application.risk_report_parser import RiskReportParser
from application.risk_report_prompt_builder import RiskReportPromptBuilder
from application.risk_report_retriever import RiskReportContext, RiskReportRetriever
from config import settings
from domain.models import RiskAnalysisResult
from infrastructure.llm_client import LLMClient
from infrastructure.mariadb_repo import MariaDBRepository

logger = logging.getLogger(__name__)


class RiskReportService:
    # 리스크 리포트 생성 유스케이스를 오케스트레이션(수집/프롬프트/파싱/저장)하는 서비스
    def __init__(self) -> None:
        self._retriever = RiskReportRetriever()
        self._prompt_builder = RiskReportPromptBuilder()
        self._parser = RiskReportParser()
        self._llm = LLMClient()
        self._repo = MariaDBRepository()

    def generate(self, *, project_id: str, week_start: date, week_end: date) -> RiskAnalysisResult:
        print("[RiskReport] start generate", flush=True)

        def log_step(label: str, start: float) -> float:
            elapsed = time_module.perf_counter() - start
            logger.info("RiskReport step=%s elapsed_ms=%.2f", label, elapsed * 1000)
            return time_module.perf_counter()

        t0 = time_module.perf_counter()
        t0 = log_step("range_build", t0)
        print("[RiskReport] range_build done", flush=True)
        context = self._retriever.fetch(project_id=project_id, week_start=week_start, week_end=week_end)
        t0 = log_step("fetch_context", t0)
        print("[RiskReport] fetch_context done", flush=True)
        if settings.environment.lower() == "test":
            context = self._apply_test_limits(context, week_start=week_start, week_end=week_end)
            t0 = log_step("apply_test_limits", t0)
            print("[RiskReport] apply_test_limits done", flush=True)
        citations = self._prompt_builder.build_citations(context)
        t0 = log_step("build_citations", t0)
        print("[RiskReport] build_citations done", flush=True)
        prompt = self._prompt_builder.build_prompt(context, citations)
        logger.info("RiskReport prompt_preview=%s", prompt[:1000])
        t0 = log_step("build_prompt", t0)
        print("[RiskReport] build_prompt done", flush=True)
        raw = self._llm.generate(prompt)
        t0 = log_step("llm_generate", t0)
        print("[RiskReport] llm_generate done", flush=True)
        parsed = self._parser.parse(raw)
        t0 = log_step("parse_json", t0)
        print("[RiskReport] parse_json done", flush=True)

        likelihood = self._clamp_score(parsed.get("likelihood", 3))
        impact = self._clamp_score(parsed.get("impact", 3))
        summary = str(parsed.get("summary", "")).strip() or "요약을 생성하지 못했습니다."
        rationale = str(parsed.get("rationale", "")).strip() or "근거를 생성하지 못했습니다."

        generated_at = datetime.now(ZoneInfo("Asia/Seoul"))
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
        log_step("save_risk_analysis", t0)
        print("[RiskReport] save_risk_analysis done", flush=True)
        return result

    def _apply_test_limits(
        self, context: RiskReportContext, *, week_start: date, week_end: date
    ) -> RiskReportContext:
        max_docs = 5
        max_chars = 800
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end, time.max)
        end_dt = min(end_dt, datetime.now())
        start_dt = max(start_dt, end_dt - timedelta(days=2))

        weekly_reports = [
            self._trim_weekly_report(item, max_chars)
            for item in context.weekly_reports
            if self._within_date(item.get("week_start_date"), start_dt.date(), end_dt.date())
        ][:max_docs]
        meeting_records = [
            self._trim_meeting_record(item, max_chars)
            for item in context.meeting_records
            if self._within_datetime(item.get("meeting_date"), start_dt, end_dt)
        ][:max_docs]

        return RiskReportContext(
            project=context.project,
            weekly_reports=weekly_reports,
            meeting_records=meeting_records,
            events_logs=[self._trim_text_field(item, "log_description", max_chars) for item in context.events_logs[:max_docs]],
            task_update_logs=[self._trim_text_field(item, "update_reason", max_chars) for item in context.task_update_logs[:max_docs]],
            milestone_update_logs=[
                self._trim_text_field(item, "update_reason", max_chars)
                for item in context.milestone_update_logs[:max_docs]
            ],
            project_documents=[
                self._trim_text_field(item, "extracted_text", max_chars) for item in context.project_documents[:max_docs]
            ],
            vector_evidence=[self._trim_text_field(item, "text", max_chars) for item in context.vector_evidence[:max_docs]],
        )

    def _within_date(self, value: Any, start: date, end: date) -> bool:
        if not isinstance(value, date):
            return True
        return start <= value <= end

    def _within_datetime(self, value: Any, start: datetime, end: datetime) -> bool:
        if not isinstance(value, datetime):
            return True
        return start <= value <= end

    def _trim_weekly_report(self, item: Dict[str, Any], max_chars: int) -> Dict[str, Any]:
        trimmed = dict(item)
        trimmed["summary_text"] = self._truncate_text(trimmed.get("summary_text"), max_chars)
        trimmed["change_of_plan"] = self._truncate_text(trimmed.get("change_of_plan"), max_chars)
        return trimmed

    def _trim_meeting_record(self, item: Dict[str, Any], max_chars: int) -> Dict[str, Any]:
        trimmed = dict(item)
        trimmed["agenda_summary"] = self._truncate_text(trimmed.get("agenda_summary"), max_chars)
        return trimmed

    def _trim_text_field(self, item: Dict[str, Any], key: str, max_chars: int) -> Dict[str, Any]:
        trimmed = dict(item)
        trimmed[key] = self._truncate_text(trimmed.get(key), max_chars)
        return trimmed

    def _truncate_text(self, value: Any, max_chars: int) -> str:
        text = str(value or "").strip().replace("\n", " ")
        if len(text) > max_chars:
            return text[:max_chars] + "..."
        return text

    def _clamp_score(self, value: Any) -> int:
        try:
            score = int(value)
        except (ValueError, TypeError):
            return 3
        return max(1, min(5, score))
