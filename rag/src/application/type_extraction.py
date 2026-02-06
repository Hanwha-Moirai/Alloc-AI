from __future__ import annotations

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


RISK_TYPE_FACTORS: Dict[str, List[str]] = {
    "schedule": ["일정", "지연", "마일스톤", "기한", "QA", "테스트 일정", "완료율"],
    "cost": ["예산", "비용", "초과", "증액", "투입", "재작업"],
    "quality": ["품질", "결함", "버그", "테스트 실패", "리워크", "검수"],
    "scope": ["범위", "요구사항", "변경", "추가", "스코프"],
    "resource": ["인력", "리소스", "인원", "부족", "이탈", "병가"],
    "vendor": ["벤더", "외주", "협력사", "하도급", "납기", "연동"],
    "compliance": ["규정", "법규", "계약", "위반", "감사"],
    "security": ["보안", "취약", "사고", "침해", "인증"],
}


def extract_risk_profile(text: str) -> List[Dict[str, object]]:
    if not text:
        return []
    lowered = text.lower()
    profile: List[Dict[str, object]] = []
    for risk_type, factors in RISK_TYPE_FACTORS.items():
        if any(factor.lower() in lowered for factor in factors):
            profile.append({"risk_type": risk_type, "factors": factors})
    if not profile:
        # Fallback to default core types when no signal is detected.
        profile = [
            {"risk_type": "schedule", "factors": RISK_TYPE_FACTORS["schedule"]},
            {"risk_type": "cost", "factors": RISK_TYPE_FACTORS["cost"]},
            {"risk_type": "quality", "factors": RISK_TYPE_FACTORS["quality"]},
        ]
    logger.info("Extracted risk profile types=%s", [item["risk_type"] for item in profile])
    return profile
