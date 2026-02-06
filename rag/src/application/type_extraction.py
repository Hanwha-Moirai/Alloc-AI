from __future__ import annotations

import json
import logging
from typing import Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.langchain_llm import get_gemini_llm

logger = logging.getLogger(__name__)


def extract_risk_profile(text: str) -> List[Dict[str, object]]:
    if not text:
        return []
    # Limit prompt size to avoid excessive token usage.
    sample = text[:8000]
    prompt = (
        "너는 IT 프로젝트 리스크 분석가다. 다음 PDF 텍스트에서 프로젝트 리스크 유형과 "
        "각 유형별 평가 요소(체크포인트)를 추출하라.\n"
        "응답은 JSON 배열만 출력하고, 각 항목은 다음 구조를 가진다:\n"
        '[{"risk_type":"...", "factors":["...","..."]}, ...]\n'
        "risk_type은 간결한 한/영 단어로 표기하라.\n\n"
        f"[PDF 텍스트]\n{sample}\n"
    )
    chain = ChatPromptTemplate.from_messages([("human", "{input}")]) | get_gemini_llm() | StrOutputParser()
    raw = chain.invoke({"input": prompt})
    profile = _parse_profile(raw)
    logger.info("Extracted risk profile types=%s", [item.get("risk_type") for item in profile])
    return profile


def _parse_profile(raw: str) -> List[Dict[str, object]]:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(raw[start : end + 1])
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return []
    return []
