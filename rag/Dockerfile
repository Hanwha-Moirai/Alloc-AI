FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/rag/src

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       gcc \
       g++ \
       pkg-config \
       libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/rag

COPY requirements.txt /app/rag/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY src /app/rag/src

EXPOSE 8000

WORKDIR /app/rag/src

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
