from typing import List


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    # 2단계: 파싱/청킹(naive 고정 길이)
    chunks = []
    cursor = 0
    while cursor < len(text):
        chunks.append(text[cursor : cursor + max_chars])
        cursor += max_chars
    return chunks
