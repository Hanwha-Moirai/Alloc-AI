from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List

_TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣]+")



def extract_keywords(text: str, *, top_n: int = 10) -> List[str]:
    segments = _split_segments(text)
    if not segments:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except Exception:
        tokens = _tokenize(text)
        if not tokens:
            return []
        counts = Counter(tokens)
        return [token for token, _ in counts.most_common(top_n)]

    vectorizer = TfidfVectorizer(tokenizer=_tokenize, token_pattern=None, lowercase=False)
    matrix = vectorizer.fit_transform(segments)
    if matrix.shape[1] == 0:
        return []
    scores = matrix.mean(axis=0).A1
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda item: item[1], reverse=True)
    return [term for term, _ in ranked[:top_n]]


def _tokenize(text: str) -> Iterable[str]:
    raw_tokens = _TOKEN_RE.findall(text)
    for token in raw_tokens:
        if token.isdigit():
            continue
        norm = token.lower()
        if len(norm) < 2:
            continue
        yield norm


def _split_segments(text: str) -> List[str]:
    if not text:
        return []
    segments = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        segments.append(line)
    if segments:
        return segments
    return [text]
