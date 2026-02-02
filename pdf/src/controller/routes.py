from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.params import File

from pdf.domain.schemas import PdfExtractResponse, PdfIngestResponse
from pdf.service.pdf_service import extract_pdf_text_from_bytes, upload_pdf_to_s3

router = APIRouter()


@router.post("/pdf/extract", response_model=PdfExtractResponse)
async def extract_pdf(file: UploadFile = File(...)) -> PdfExtractResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type.")
    content = await file.read()
    text, page_count = extract_pdf_text_from_bytes(content)
    return PdfExtractResponse(
        file_name=file.filename,
        page_count=page_count,
        text=text,
    )


@router.post("/pdf/ingest", response_model=PdfIngestResponse)
async def ingest_pdf(file: UploadFile = File(...)) -> PdfIngestResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type.")
    content = await file.read()
    s3_key = upload_pdf_to_s3(file.filename, content)
    text, page_count = extract_pdf_text_from_bytes(content)
    return PdfIngestResponse(
        file_name=file.filename,
        s3_key=s3_key,
        page_count=page_count,
        text=text,
    )
