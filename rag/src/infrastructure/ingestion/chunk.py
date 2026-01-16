from typing import List


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    chunks = []
    cursor = 0
    while cursor < len(text):
        chunks.append(text[cursor : cursor + max_chars])
        cursor += max_chars
    return chunks
