FROM python:3.10-slim

WORKDIR /app

COPY rag/ /app/rag/

RUN pip install --upgrade pip && pip install --no-cache-dir /app/rag

ENV PYTHONPATH=/app/rag/src

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
