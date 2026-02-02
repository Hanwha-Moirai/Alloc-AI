from pathlib import Path
from typing import Tuple
import uuid

import fitz

from config import settings


def extract_pdf_text(path: Path) -> Tuple[str, int]:
    doc = fitz.open(path)
    try:
        text = _extract_text(doc)
        page_count = doc.page_count
    finally:
        doc.close()
    return text, page_count


def extract_pdf_text_from_bytes(content: bytes) -> Tuple[str, int]:
    doc = fitz.open(stream=content, filetype="pdf")
    try:
        text = _extract_text(doc)
        page_count = doc.page_count
    finally:
        doc.close()
    return text, page_count


def upload_pdf_to_s3(file_name: str, content: bytes) -> str:
    if not settings.s3_bucket:
        raise RuntimeError("PDF_S3_BUCKET must be set for PDF ingest.")
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for PDF ingest. Install it and retry.") from exc
    s3 = boto3.client(
        "s3",
        region_name=settings.s3_region or None,
        aws_access_key_id=settings.s3_access_key_id or None,
        aws_secret_access_key=settings.s3_secret_access_key or None,
    )
    suffix = Path(file_name).suffix.lower() or ".pdf"
    key = f"{settings.s3_prefix}{uuid.uuid4().hex}{suffix}"
    s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=content, ContentType="application/pdf")
    return key


def _extract_text(doc: fitz.Document) -> str:
    try:
        import pymupdf4llm
    except Exception:
        pymupdf4llm = None

    if pymupdf4llm is not None:
        try:
            text = pymupdf4llm.to_markdown(doc)
            return text.strip()
        except Exception:
            pass

    texts = [page.get_text("text") for page in doc]
    return "\n".join(texts).strip()
