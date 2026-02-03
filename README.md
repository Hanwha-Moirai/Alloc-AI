# Alloc-AI (RAG)

## Quickstart (Ubuntu)

1. Clone

```bash
git clone <REPO_URL>
cd Alloc-AI
```

2. Setup (venv + deps)

```bash
bash setup.sh
```

3. Run (local)

```bash
source alloc-ai/bin/activate
cd rag/src
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker Image (RAG)

```bash
docker build -t alloc-ai-rag:local ./rag
docker run --rm -p 8000:8000 alloc-ai-rag:local
```

## Docker Compose (RAG + Qdrant)

```bash
docker compose up -d --build
docker compose logs -f rag
docker compose down
```
