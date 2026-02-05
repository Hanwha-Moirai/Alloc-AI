from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Iterable, List

from langchain_community.document_loaders import PyPDFLoader

logger = logging.getLogger(__name__)


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
    print(f"[Loader] open pdf={path}", flush=True)
    text, page_count = _extract_via_loader(path)
    rel_path = path.resolve().relative_to(base_dir).as_posix()
    metadata = {
        "source_path": rel_path,
        "file_name": path.name,
        "page_count": page_count,
    }
    return DocumentPayload(doc_id=rel_path, text=text, metadata=metadata)


def _extract_via_loader(path: Path) -> tuple[str, int]:
    try:
        loader = PyPDFLoader(str(path))
        pages = loader.load()
    except Exception as exc:
        logger.warning("PDF load failed: %s", exc)
        return "", 0
    page_count = len(pages)
    text = "\n\n".join(page.page_content for page in pages if page.page_content)
    return text, page_count
