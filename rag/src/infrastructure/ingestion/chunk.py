from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_text(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    # 2단계: 파싱/청킹 - LangChain recursive splitter + overlap
    stripped = text.strip()
    if not stripped:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
    )
    return [chunk.strip() for chunk in splitter.split_text(stripped) if chunk.strip()]
