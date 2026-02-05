from typing import List


def chunk_text(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    # 2단계: 파싱/청킹 - recursive split + overlap
    stripped = text.strip()
    if not stripped:
        return []

    separators = ["\n\n", "\n", ". ", " "]
    chunks = _recursive_split(stripped, max_chars, separators)
    chunks = [c.strip() for c in chunks if c.strip()]
    return _apply_overlap(chunks, overlap)


def _recursive_split(text: str, max_chars: int, separators: List[str]) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    if not separators:
        return _hard_split(text, max_chars)

    sep = separators[0]
    parts = _split_keep_sep(text, sep)
    if len(parts) == 1:
        return _recursive_split(text, max_chars, separators[1:])

    chunks: List[str] = []
    buffer = ""
    for part in parts:
        if len(buffer) + len(part) <= max_chars:
            buffer += part
            continue
        if buffer:
            chunks.extend(_recursive_split(buffer, max_chars, separators[1:]))
            buffer = ""
        if len(part) > max_chars:
            chunks.extend(_recursive_split(part, max_chars, separators[1:]))
        else:
            buffer = part
    if buffer:
        chunks.extend(_recursive_split(buffer, max_chars, separators[1:]))
    return chunks


def _split_keep_sep(text: str, sep: str) -> List[str]:
    parts = text.split(sep)
    if len(parts) == 1:
        return [text]
    out: List[str] = []
    for idx, part in enumerate(parts):
        if idx < len(parts) - 1:
            out.append(part + sep)
        else:
            out.append(part)
    return out


def _hard_split(text: str, max_chars: int) -> List[str]:
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def _apply_overlap(chunks: List[str], overlap: int) -> List[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    out = [chunks[0]]
    for i in range(1, len(chunks)):
        prev = chunks[i - 1]
        prefix = prev[-overlap:] if len(prev) > overlap else prev
        out.append(prefix + chunks[i])
    return out
