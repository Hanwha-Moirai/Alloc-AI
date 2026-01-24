# Qdrant 사용 방식 (RAG 관점)

이 문서는 Alloc-AI RAG 서비스에서 Qdrant를 사용하는 흐름을 실제 코드 기준으로 정리한다.

## 1) 벡터 저장소 설정
- **설정 파일**: `rag/src/config.py`
  - `RAG_QDRANT_URL`: Qdrant 접속 URL (기본값: `http://localhost:6333`)
  - `RAG_QDRANT_API_KEY`: API Key (필요 시)
  - `RAG_QDRANT_COLLECTION`: 컬렉션 이름 (기본값: `rag_chunks`)

```python
class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "rag_chunks"
```

## 2) Qdrant 어댑터 초기화
- **구현 위치**: `rag/src/infrastructure/qdrant_store.py`
- **동작**:
  - `QdrantClient(url=..., api_key=...)`로 연결
  - 컬렉션 이름은 설정값 사용

```python
class QdrantAdapter:
    def __init__(self) -> None:
        self.url = settings.qdrant_url
        self.api_key = settings.qdrant_api_key
        self.collection = settings.qdrant_collection
        self.client = QdrantClient(url=self.url, api_key=self.api_key or None)
```

## 3) 벡터 업서트(적재)
- **호출 경로**:
  - `rag/src/application/ingestion_service.py` → `rag/src/infrastructure/ingestion/index.py`
  - `index_embeddings()`에서 `QdrantAdapter.upsert()` 호출
- **업서트 규칙**:
  - `doc_id`, `chunk_index`, `text`, `metadata`를 payload로 저장
  - point id는 `{doc_id}:{chunk_index}`
  - 컬렉션이 없으면 자동 생성 (벡터 차원 기반)

```python
point_id = f"{doc_id}:{idx}"
payload = {"doc_id": doc_id, "chunk_index": idx, "text": chunk, "metadata": metadata}
```

## 4) 검색 흐름
- **서비스 진입**: `rag/src/application/rag_service.py`
  - `RagService.search()`에서 `VectorStore.search()` 호출
- **Qdrant 검색**: `rag/src/infrastructure/qdrant_store.py`
  - 쿼리를 임베딩한 후 `client.search()` 수행
  - `SearchResult`로 매핑하여 반환

```python
results = self.client.search(
    collection_name=self.collection,
    query_vector=query_vector,
    limit=k,
    with_payload=True,
)
```

## 5) 임베딩 생성
- **임베더 위치**: `rag/src/infrastructure/ingestion/embed.py`
- **현재 상태**: 스텁 임베더 (실제 모델로 교체 필요)

```python
def embed_text(texts: List[str]) -> List[List[float]]:
    return [[0.0] * 4 for _ in texts]
```

## 6) 문서 적재 (PDF 기준, naive)
- **로더 위치**: `rag/src/infrastructure/ingestion/docs_loader.py`
- **동작**:
  - `data/` 하위 PDF를 순회하며 텍스트 추출
  - 페이지 텍스트를 단순 연결 후 chunking/업서트
  - `doc_id`는 `docs` 기준 상대 경로를 사용
- **호출 위치**: `rag/src/application/ingestion_service.py`

```python
service = IngestionService()
service.ingest_data_dir("data")
```

### 6-1. PDF 업로드 API (원문 적재 전 단계)
- **엔드포인트**: `POST /upload/pdf`
- **동작**: 업로드된 PDF를 `data/` 디렉터리에 저장
- **구현 위치**: `rag/src/interface/api/routes.py`

## 7) 연결 확인 (운영 체크)
### 6-1. 헬스 체크 API
- **엔드포인트**: `GET /health/qdrant`
- **구현 위치**: `rag/src/interface/api/routes.py`
- **동작**:
  - `QdrantAdapter.health()`로 컬렉션 목록과 존재 여부 확인
  - 연결 실패 시 `503` 반환
