from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List

_TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣]+")

_STOPWORDS = {
    # Korean
    "그리고",
    "그러나",
    "하지만",
    "또한",
    "및",
    "등",
    "수",
    "것",
    "등등",
    "관련",
    "대상",
    "자료",
    "문서",
    "프로젝트",
    "회의",
    "보고",
    "사항",
    "내용",
    "결과",
    "요약",
    "진행",
    "계획",
    "이슈",
    "리스크",
    "위험",
    # English
    "and",
    "or",
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "for",
    "on",
    "with",
    "by",
    "from",
    "is",
    "are",
    "be",
    "as",
    "this",
    "that",
    "it",
    "project",
    "report",
    "meeting",
    "summary",
    "issue",
    "risk",
}


def extract_keywords(text: str, *, top_n: int = 10) -> List[str]:
    tokens = _tokenize(text)
    if not tokens:
        return []
    counts = Counter(tokens)
    return [token for token, _ in counts.most_common(top_n)]


def _tokenize(text: str) -> Iterable[str]:
    raw_tokens = _TOKEN_RE.findall(text)
    for token in raw_tokens:
        if token.isdigit():
            continue
        norm = token.lower()
        if len(norm) < 2:
            continue
        if norm in _STOPWORDS:
            continue
        yield norm
