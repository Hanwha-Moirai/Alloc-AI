from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import requests

from config import settings


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
    text, page_count = _extract_via_service(path)
    rel_path = path.resolve().relative_to(base_dir).as_posix()
    metadata = {
        "source_path": rel_path,
        "file_name": path.name,
        "page_count": page_count,
    }
    return DocumentPayload(doc_id=rel_path, text=text, metadata=metadata)


def _extract_via_service(path: Path) -> tuple[str, int]:
    url = f"{settings.pdf_service_url.rstrip('/')}/pdf/extract"
    with path.open("rb") as fp:
        files = {"file": (path.name, fp, "application/pdf")}
        response = requests.post(url, files=files, timeout=60)
    response.raise_for_status()
    payload = response.json()
    return payload.get("text", ""), int(payload.get("page_count", 0))
