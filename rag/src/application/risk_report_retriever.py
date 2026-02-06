from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List

import logging

from config import settings
from application.risk_type_classifier import score_risk_types
from langchain_core.documents import Document

from infrastructure.langchain_store import similarity_search_with_score
from infrastructure.mariadb_repo import MariaDBRepository
from infrastructure.ingestion.keywords import extract_keywords


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
    risk_type_scores: Dict[str, float]
    risk_profile: List[Dict[str, Any]]


class RiskReportRetriever:
    # 리스크 리포트에 필요한 데이터를 MariaDB/Qdrant에서 수집하는 리트리버
    def __init__(self) -> None:
        self._repo = MariaDBRepository()

    def fetch(self, *, project_id: str, week_start: date, week_end: date) -> RiskReportContext:
        print("[RiskReport] retriever start", flush=True)
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end, time.max)
        print("[RiskReport] retriever range ready", flush=True)
        project = self._repo.fetch_project(project_id)
        print("[RiskReport] retriever fetch_project done", flush=True)
        weekly_reports = self._repo.fetch_weekly_reports(project_id, week_start, week_end)
        print("[RiskReport] retriever fetch_weekly_reports done", flush=True)
        meeting_records = self._repo.fetch_meeting_records(project_id, start_dt, end_dt)
        print("[RiskReport] retriever fetch_meeting_records done", flush=True)
        events_logs = self._repo.fetch_events_logs(project_id, start_dt, end_dt)
        print("[RiskReport] retriever fetch_events_logs done", flush=True)
        task_update_logs = self._repo.fetch_task_update_logs(project_id, start_dt, end_dt)
        print("[RiskReport] retriever fetch_task_update_logs done", flush=True)
        milestone_update_logs = self._repo.fetch_milestone_update_logs(project_id, start_dt, end_dt)
        print("[RiskReport] retriever fetch_milestone_update_logs done", flush=True)
        project_documents = self._repo.fetch_project_documents(project_id)
        print("[RiskReport] retriever fetch_project_documents done", flush=True)
        risk_profile = self._repo.fetch_risk_profile()
        vector_hits = self._fetch_vector_evidence(
            project_id=project_id,
            week_start=week_start,
            week_end=week_end,
            risk_profile=risk_profile,
            weekly_reports=weekly_reports,
            meeting_records=meeting_records,
            events_logs=events_logs,
            task_update_logs=task_update_logs,
            milestone_update_logs=milestone_update_logs,
            project_documents=project_documents,
        )
        print(f"[RiskReport] retriever vector_hits={len(vector_hits)}", flush=True)
        logger.info("RiskReport vector_evidence_count=%d", len(vector_hits))
        risk_type_scores = score_risk_types(self._collect_keywords(vector_hits))
        return RiskReportContext(
            project=project,
            weekly_reports=weekly_reports,
            meeting_records=meeting_records,
            events_logs=events_logs,
            task_update_logs=task_update_logs,
            milestone_update_logs=milestone_update_logs,
            project_documents=project_documents,
            vector_evidence=vector_hits,
            risk_type_scores=risk_type_scores,
            risk_profile=risk_profile,
        )

    def _fetch_vector_evidence(
        self,
        *,
        project_id: str,
        week_start: date,
        week_end: date,
        risk_profile: List[Dict[str, Any]],
        weekly_reports: List[Dict[str, Any]],
        meeting_records: List[Dict[str, Any]],
        events_logs: List[Dict[str, Any]],
        task_update_logs: List[Dict[str, Any]],
        milestone_update_logs: List[Dict[str, Any]],
        project_documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        # 4단계: 벡터 검색 (query -> top_k 청크)
        base = f"프로젝트 {project_id} 일정 지연 리스크 분석 ({week_start}~{week_end})"
        queries = self._build_queries_from_profile(
            base=base,
            risk_profile=risk_profile,
            weekly_reports=weekly_reports,
            meeting_records=meeting_records,
            events_logs=events_logs,
            task_update_logs=task_update_logs,
            milestone_update_logs=milestone_update_logs,
            project_documents=project_documents,
        )
        all_results: List[Dict[str, Any]] = []
        seen_keys = set()
        for query in queries:
            print(f"[RiskReport] retriever vector_query={query} top_k={settings.top_k}", flush=True)
            logger.info("RiskReport vector_query=%s top_k=%d", query, settings.top_k)
            results = similarity_search_with_score(query, k=settings.top_k)
            for doc, score in results:
                metadata = doc.metadata or {}
                key = (metadata.get("doc_id"), metadata.get("chunk_index"))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                all_results.append(self._to_evidence(doc, score))
        print(f"[RiskReport] retriever vector_search_results={len(all_results)}", flush=True)
        return all_results

    def _build_queries_from_profile(
        self,
        *,
        base: str,
        risk_profile: List[Dict[str, Any]],
        weekly_reports: List[Dict[str, Any]],
        meeting_records: List[Dict[str, Any]],
        events_logs: List[Dict[str, Any]],
        task_update_logs: List[Dict[str, Any]],
        milestone_update_logs: List[Dict[str, Any]],
        project_documents: List[Dict[str, Any]],
    ) -> List[str]:
        keywords: List[str] = []
        seed_texts: List[str] = []
        seed_texts.extend(item.get("summary_text", "") for item in weekly_reports)
        seed_texts.extend(item.get("change_of_plan", "") for item in weekly_reports)
        seed_texts.extend(item.get("agenda_summary", "") for item in meeting_records)
        seed_texts.extend(item.get("log_description", "") for item in events_logs)
        seed_texts.extend(item.get("update_reason", "") for item in task_update_logs)
        seed_texts.extend(item.get("update_reason", "") for item in milestone_update_logs)
        seed_texts.extend(item.get("extracted_text", "") for item in project_documents)
        for text in seed_texts:
            if not text:
                continue
            keywords.extend(_tokenize_keywords(text))
        for item in risk_profile or []:
            factors = item.get("factors") or []
            if isinstance(factors, list):
                keywords.extend([str(factor) for factor in factors])
        unique = _dedupe_keywords(keywords)
        if not unique:
            return [base]
        return [f"{base} 핵심 키워드: {' '.join(unique[:12])}"]

    def _to_evidence(self, doc: Document, score: float) -> Dict[str, Any]:
        metadata = doc.metadata or {}
        return {
            "doc_id": metadata.get("doc_id", ""),
            "score": score,
            "text": doc.page_content,
            "metadata": metadata,
        }

    def _collect_keywords(self, items: List[Dict[str, Any]]) -> List[List[str]]:
        keywords: List[List[str]] = []
        for item in items:
            metadata = item.get("metadata") or {}
            kws = metadata.get("keywords") or []
            if isinstance(kws, list):
                keywords.append(kws)
        return keywords


def _tokenize_keywords(text: str) -> List[str]:
    return extract_keywords(text, top_n=6)


def _dedupe_keywords(items: List[str]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
logger = logging.getLogger(__name__)
