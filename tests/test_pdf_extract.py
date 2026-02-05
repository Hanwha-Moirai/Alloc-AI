from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAG_SRC = PROJECT_ROOT / "rag" / "src"
sys.path.insert(0, str(RAG_SRC))

from infrastructure.ingestion.docs_loader import load_pdf


def test_pdf_extract_loads_text() -> None:
    base_dir = Path(__file__).with_name("samples")
    pdf_path = base_dir / "iso_21500.pdf"
    if not pdf_path.exists():
        pytest.skip(f"sample PDF not found: {pdf_path}")
    payload = load_pdf(pdf_path, base_dir)
    text = payload.text or ""
    assert payload.doc_id
    assert len(text) > 0
