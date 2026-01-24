# 리스크 리포트 생성 흐름 (RAG 기준)

이 문서는 `POST /api/projects/{project_id}/docs/risk_report` 요청이 들어온 이후의 처리 흐름을 코드 기준으로 정리한다.

## 처리 흐름
1) 라우터 진입
- 파일: `rag/src/interface/api/routes.py`
- `POST /api/projects/{project_id}/docs/risk_report`에서 `RiskReportService.generate()` 호출

2) 주간 범위 확정
- 파일: `rag/src/application/risk_report_service.py`
- `week_start`, `week_end`를 `datetime` 범위로 변환

3) MariaDB 문서/메타 수집
- 파일: `rag/src/infrastructure/mariadb_repo.py`
- 프로젝트 메타: `fetch_project()`
- 주간보고: `fetch_weekly_reports()`
- 회의록: `fetch_meeting_records()` + `agenda` 텍스트 결합
- 일정 변경 로그: `fetch_events_logs()`
- 태스크 변경 로그: `fetch_task_update_logs()`
- 마일스톤 변경 로그: `fetch_milestone_update_logs()`
- 프로젝트 문서: `fetch_project_documents()`

4) 근거 목록(citations) 구성
- 파일: `rag/src/application/risk_report_service.py`
- `_build_citations()`에서 `source_type/source_id/excerpt` 생성

5) LLM 프롬프트 구성
- 파일: `rag/src/application/risk_report_service.py`
- 수집 데이터/근거 목록을 JSON으로 넣고 PI 매트릭스 평가 요청
- 응답은 JSON만 출력하도록 지시

6) LLM 호출
- 파일: `rag/src/infrastructure/llm_client.py`
- `llm_provider=gemini`일 때 `google-generativeai` SDK 호출

7) JSON 파싱 및 점수 보정
- 파일: `rag/src/application/risk_report_service.py`
- `_parse_json()`으로 파싱
- `likelihood`, `impact`는 1~5 범위로 보정

8) 결과 저장 (별도 엔티티)
- 파일: `rag/src/infrastructure/mariadb_repo.py`
- `save_risk_analysis()`에서 `risk_analysis` 테이블에 저장

9) 응답 반환
- 파일: `rag/src/interface/api/routes.py`
- `RiskReportResponse` JSON 응답 반환
