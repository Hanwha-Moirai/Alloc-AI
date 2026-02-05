from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List


RISK_KEYWORDS: Dict[str, List[str]] = {
    "schedule": ["delay", "slip", "deadline", "milestone", "일정", "지연", "마일스톤", "기한"],
    "cost": ["budget", "cost", "overrun", "예산", "비용", "초과", "증액"],
    "quality": ["defect", "bug", "quality", "테스트", "결함", "버그", "품질"],
    "scope": ["scope", "change", "요구사항", "범위", "변경", "추가"],
    "resource": ["resource", "staff", "인력", "인원", "부족", "vacancy"],
    "vendor": ["vendor", "supplier", "외주", "협력사", "하도급"],
    "compliance": ["compliance", "regulation", "법규", "규정", "위반", "계약"],
    "security": ["security", "vulnerability", "보안", "취약", "사고"],
}


def score_risk_types(keyword_lists: Iterable[List[str]]) -> Dict[str, float]:
    scores: Dict[str, float] = defaultdict(float)
    for keywords in keyword_lists:
        kw_set = set(keywords or [])
        if not kw_set:
            continue
        for risk_type, lexicon in RISK_KEYWORDS.items():
            matches = kw_set.intersection(lexicon)
            if matches:
                scores[risk_type] += float(len(matches))
    return dict(scores)
