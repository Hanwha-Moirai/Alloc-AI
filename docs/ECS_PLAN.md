# ECS Service 분리 아키텍처 설계 문서

## 1. 목적
본 문서는 Alloc 시스템을 구성하는 세 개의 모듈을  
**각각 독립적인 ECS Service(Fargate launch type)** 로 분리하여 운영하는 아키텍처를 정의한다.

서비스 분리의 목적은 다음과 같다.

- 독립 배포 및 롤백
- 부하 특성에 따른 독립 스케일링
- 장애 전파 최소화
- 리소스/비용 최적화
- 책임과 경계가 명확한 운영 구조

---

## 2. 서비스 구성 개요

| 서비스 | 이름 | 구현 | 주요 역할 |
|------|------|------|-----------|
| A | Alloc | Spring Framework | 비즈니스 로직 / 오케스트레이션 |
| B | PDF-to-Text | FastAPI | PDF 텍스트 추출 / 고부하 처리 |
| C | RAG API | FastAPI | 문서 검색 및 LLM 기반 질의 응답 |

모든 서비스는 다음 공통 조건을 가진다.

- ECS Cluster 내 독립 ECS Service
- Launch Type: FARGATE
- Task 단위로 실행 및 스케일링
- 서비스 간 통신은 내부 네트워크 기반

---

## 3. 전체 ECS 구조

```text
ECS Cluster (prod)
 ├─ Service A: alloc-service
 │   └─ Task A (Fargate, N개)
 │
 ├─ Service B: pdf-to-text-service
 │   └─ Task B (Fargate, M개)
 │
 └─ Service C: rag-api-service
     └─ Task C (Fargate, K개)
