from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import fitz


@dataclass(frozen=True)
class DocumentPayload:
    doc_id: str
    text: str
    metadata: dict


def load_pdfs_from_dir(data_dir: str) -> List[DocumentPayload]:
    base = Path(data_dir).resolve()
    if not base.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # 1단계: 문서 인입(원문 PDF)
    pdf_paths = sorted(base.rglob("*.pdf"))
    return [load_pdf(path, base) for path in pdf_paths]


def iter_pdfs_from_dir(data_dir: str) -> Iterable[DocumentPayload]:
    base = Path(data_dir).resolve()
    if not base.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    # 1단계: 문서 인입(원문 PDF)
    for path in sorted(base.rglob("*.pdf")):
        yield load_pdf(path, base)


def load_pdf(path: Path, base_dir: Path) -> DocumentPayload:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text("text"))
    doc.close()
    text = "\n".join(texts).strip()
    rel_path = path.resolve().relative_to(base_dir).as_posix()
    metadata = {
        "source_path": rel_path,
        "file_name": path.name,
        "page_count": doc.page_count,
    }
    return DocumentPayload(doc_id=rel_path, text=text, metadata=metadata)
