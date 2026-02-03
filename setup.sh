#!/bin/bash

echo "1. 시스템 패키지 업데이트 및 필수 도구 설치 (RAG)"
sudo apt update -y
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    libmariadb-dev \
    gcc \
    g++ \
    pkg-config \
    git \
    curl \
    unzip \
    build-essential

echo "2. 프로젝트용 Python 가상환경 생성"
python3 -m venv .venv
. ./.venv/bin/activate

echo "3. Python 패키지 의존성 설치 (rag)"
pip install --upgrade pip
pip install -r rag/requirements.txt

echo "모든 Python 패키지 설치 완료"

echo "4. FastAPI 서버 실행 예시 (RAG)"
echo "source .venv/bin/activate && cd rag/src && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo "전체 설정 완료!"
