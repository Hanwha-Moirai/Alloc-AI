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


class RiskReportRequest(BaseModel):
    week_start: date
    week_end: date


class RiskCitation(BaseModel):
    source_type: str
    source_id: str
    excerpt: str


class RiskReportResponse(BaseModel):
    project_id: str
    likelihood: int
    impact: int
    summary: str
    rationale: str
    generated_at: datetime
    citations: List[RiskCitation]
