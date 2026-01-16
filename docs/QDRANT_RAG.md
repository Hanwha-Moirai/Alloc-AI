# Qdrant 사용 방식 (RAG 관점)

이 문서는 이 저장소에서 Qdrant를 RAG 파이프라인에 어떻게 사용하는지에 대한 구현 방식을 정리한다.

## 1) 벡터 저장소 생성
- **벡터스토어 정의**: `app/chains/vector_store.py`
  - 임베딩: `sentence-transformers/all-MiniLM-L6-v2`
  - Qdrant 컬렉션: `fp_examples`
  - 클라이언트: `QdrantClient(host=QDRANT_HOST, port=6333)`
  - LangChain `Qdrant` 벡터스토어로 래핑

```python
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
client = QdrantClient(host=qdrant_host, port=6333)
vectorstore = Qdrant(
    client=client,
    collection_name="fp_examples",
    embeddings=embedding
)
```

## 2) 데이터 적재(벡터 업로드)
### 2-1. 서버 시작 시 자동 적재
- **진입점**: `main.py` → `startup_event()`
- **동작**: 서버 시작 시 `process_and_upload_to_qdrant()`를 호출하여 컬렉션을 재생성 후 업로드

```python
@app.on_event("startup")
async def startup_event():
    await process_and_upload_to_qdrant()
```

### 2-2. PDF 기반 예시 생성 후 업로드
- **스크립트**: `app/scripts/fp_generate_embedding.py`
- **흐름**:
  1) PDF 요구사항 문서에서 문장 추출
  2) LLM으로 각 문장을 FP 예시(JSON)로 변환
  3) `description`을 `page_content`로 `Document` 생성
  4) Qdrant 컬렉션 `fp_examples`에 업로드

```python
client.recreate_collection(
    collection_name="fp_examples",
    vectors_config={"size": 384, "distance": "Cosine"}
)
vectorstore.add_documents(documents)
```

### 2-3. API를 통한 수동 업로드
- **API**: `app/api/fp_embed.py`
- **동작**: 입력 리스트를 `Document`로 변환 후 `vectorstore.add_documents()`로 저장

```python
vectorstore.add_documents(documents)
```

## 3) RAG 검색 설정
- **리트리버 정의**: `app/chains/retriever.py`
- **검색 설정**:
  - `search_type`: `similarity_score_threshold`
  - `score_threshold`: `0.8`
  - `k`: `1`

```python
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8, "k": 1}
)
```

## 4) RAG 체인 구성
- **체인 정의**: `app/chains/chains.py`
- **구성**: `RetrievalQA` 사용
- **입력**: 질문(`query`) + 검색된 문맥(`context`)을 프롬프트에 주입

```python
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template}
)
```

## 5) RAG 호출 위치
- **서비스**: `app/services/fp_inference_service.py`
- **사용 방식**: OCR 문장(`ocr_text`)을 질문으로 전달해 RAG 호출

```python
raw_output = await asyncio.to_thread(rag_chain.invoke, {"query": ocr_text})
```

## 참고: Qdrant 연결 확인
- **헬스 체크**: `app/api/qdrant_test.py`
- `/ping-qdrant`에서 `get_collections()` 호출

```python
result = qdrant_client.get_collections()
```
