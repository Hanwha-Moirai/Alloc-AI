from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskAnalysisResult:
    project_id: str
    likelihood: int
    impact: int
    summary: str
    rationale: str
    citations: List[Dict[str, str]] = field(default_factory=list)
