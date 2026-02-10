from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass(frozen=True)
class RiskAnalysisResult:
    project_id: str
    likelihood: int
    impact: int
    risk_type: str | None
    summary: str
    rationale: str
    generated_at: datetime
    citations: List[Dict[str, str]] = field(default_factory=list)
