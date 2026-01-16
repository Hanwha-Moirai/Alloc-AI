from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
