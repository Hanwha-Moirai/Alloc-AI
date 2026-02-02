from pydantic import BaseModel


class PdfExtractResponse(BaseModel):
    file_name: str
    page_count: int
    text: str


class PdfIngestResponse(BaseModel):
    file_name: str
    s3_key: str
    page_count: int
    text: str
