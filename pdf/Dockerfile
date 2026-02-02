FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/pdf/src

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/pdf

COPY requirements.txt /app/pdf/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY src /app/pdf/src

EXPOSE 8010

WORKDIR /app/pdf/src

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
