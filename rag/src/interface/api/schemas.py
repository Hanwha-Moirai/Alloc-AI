from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from domain.models import SearchResult as DomainSearchResult


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = None


class SearchResult(BaseModel):
    doc_id: str
    score: float
    text: str
    metadata: dict = Field(default_factory=dict)

    @classmethod
    def from_domain(cls, result: DomainSearchResult) -> "SearchResult":
        return cls(
            doc_id=result.doc_id,
            score=result.score,
            text=result.text,
            metadata=result.metadata,
        )


class SearchResponse(BaseModel):
    results: List[SearchResult]


class AnswerRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = None


class AnswerResponse(BaseModel):
    answer: str
    citations: List[SearchResult]


class IngestRequest(BaseModel):
    doc_id: str
    text: str
    metadata: dict = Field(default_factory=dict)


class WeeklyReportGenerateRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    week_start: date
    week_end: date
    as_of_timestamp: datetime


class WeeklyReportGenerateResponse(BaseModel):
    weekly_report_draft: str
    schedule_risk_report: str
