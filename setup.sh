#!/bin/bash

echo "1. 시스템 패키지 업데이트 및 필수 도구 설치"
sudo apt update -y
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    poppler-utils \
    git \
    curl \
    unzip \
    build-essential

echo "2. 프로젝트용 Python 가상환경 생성"
python3 -m venv venv
source venv/bin/activate

echo "3. Python 패키지 의존성 설치"
pip install --upgrade pips

# 설치할 패키지 리스트
REQUIREMENTS=$(cat <<EOF
fastapi
uvicorn
pydantic
requests
python-dotenv
Pillow
langchain
langchain-community
langchain-huggingface
huggingface_hub
sentence-transformers
qdrant-client
google-ai-generativelanguage==0.6.18
tiktoken
EOF
)

# requirement를 모두 text로 작성
echo "$REQUIREMENTS" > requirements.txt
pip install -r requirements.txt

echo "모든 Python 패키지 설치 완료"

echo "4. 테스트용 "

echo "5. FastAPI 서버 실행 예시 (기본 uvicorn)"
echo "source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo "전체 설정 완료!"