from typing import List


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    # 2단계: 파싱/청킹(stub) - 현재는 원문 그대로 1개 청크로 사용
    _ = max_chars
    stripped = text.strip()
    return [stripped] if stripped else []
