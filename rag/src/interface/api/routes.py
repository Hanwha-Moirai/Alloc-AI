from fastapi import APIRouter, Depends

from application.ingestion_service import IngestionService
from application.rag_service import RagService
from interface.api import schemas
from interface.api.deps import get_ingestion_service, get_rag_service

router = APIRouter()


@router.post("/search", response_model=schemas.SearchResponse)
def search(
    payload: schemas.SearchRequest,
    service: RagService = Depends(get_rag_service),
) -> schemas.SearchResponse:
    results = service.search(payload.query, top_k=payload.top_k)
    return schemas.SearchResponse(results=[schemas.SearchResult.from_domain(item) for item in results])


@router.post("/answer", response_model=schemas.AnswerResponse)
def answer(
    payload: schemas.AnswerRequest,
    service: RagService = Depends(get_rag_service),
) -> schemas.AnswerResponse:
    response, results = service.answer(payload.query, top_k=payload.top_k)
    return schemas.AnswerResponse(
        answer=response,
        citations=[schemas.SearchResult.from_domain(item) for item in results],
    )


@router.post("/ingest")
def ingest(
    payload: schemas.IngestRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> dict:
    service.ingest(payload.doc_id, payload.text, payload.metadata)
    return {"status": "ok"}
