from __future__ import annotations

import json
from typing import Any, Dict, List

from application.risk_report_retriever import RiskReportContext


class RiskReportPromptBuilder:
    # 리스크 리포트 프롬프트 및 근거(citations) 생성 전담
    def build_prompt(self, context: RiskReportContext, citations: List[Dict[str, str]]) -> str:
        return (
            "너는 IT 프로젝트 리스크 관리 전문가다. 아래 문서들을 근거로 "
            "일정 지연 리스크를 PI 매트릭스(발생 가능성/영향도 1~5)로 평가하라.\n"
            "사내 리스크 데이터가 충분하지 않아 몬테카를로 대신 정성적 PI 매트릭스를 사용한다.\n"
            "문서 기반 정성 분석은 LLM이 잘하기 때문에 RAG로 근거를 요약한다.\n\n"
            "응답은 JSON만 출력하고, 다음 키를 포함하라:\n"
            '{"likelihood": 1, "impact": 1, "summary": "...", "rationale": "..."}\n\n'
            f"[프로젝트 메타]\n{json.dumps(context.project, ensure_ascii=False, default=str)}\n\n"
            f"[주간 보고]\n{json.dumps(context.weekly_reports, ensure_ascii=False, default=str)}\n\n"
            f"[회의록]\n{json.dumps(context.meeting_records, ensure_ascii=False, default=str)}\n\n"
            f"[일정 변경 로그]\n{json.dumps(context.events_logs, ensure_ascii=False, default=str)}\n\n"
            f"[태스크 변경 로그]\n{json.dumps(context.task_update_logs, ensure_ascii=False, default=str)}\n\n"
            f"[마일스톤 변경 로그]\n{json.dumps(context.milestone_update_logs, ensure_ascii=False, default=str)}\n\n"
            f"[프로젝트 문서]\n{json.dumps(context.project_documents, ensure_ascii=False, default=str)}\n\n"
            f"[벡터 검색 결과]\n{json.dumps(context.vector_evidence, ensure_ascii=False, default=str)}\n\n"
            f"[참고 문서 목록]\n{json.dumps(citations, ensure_ascii=False, default=str)}\n"
        )

    def build_citations(self, context: RiskReportContext) -> List[Dict[str, str]]:
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
        for item in context.vector_evidence:
            citations.append(self._citation("vector_evidence", item.get("doc_id"), item.get("text")))
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
