from datetime import date, datetime
from typing import List

from pydantic import BaseModel, Field

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


class RiskReportListItem(BaseModel):
    report_id: int
    project_id: str
    project_name: str
    summary: str
    likelihood: int
    impact: int
    generated_at: datetime


class RiskReportDetailResponse(BaseModel):
    report_id: int
    project_id: str
    project_name: str
    summary: str
    likelihood: int
    impact: int
    rationale: str
    generated_at: datetime
    citations: List[RiskCitation]
