from pathlib import Path
from typing import Tuple
import uuid

import fitz

from pdf.config import settings


def extract_pdf_text(path: Path) -> Tuple[str, int]:
    doc = fitz.open(path)
    try:
        texts = [page.get_text("text") for page in doc]
        page_count = doc.page_count
    finally:
        doc.close()
    text = "\n".join(texts).strip()
    return text, page_count


def extract_pdf_text_from_bytes(content: bytes) -> Tuple[str, int]:
    doc = fitz.open(stream=content, filetype="pdf")
    try:
        texts = [page.get_text("text") for page in doc]
        page_count = doc.page_count
    finally:
        doc.close()
    text = "\n".join(texts).strip()
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
