USE hawking_test;

DELETE FROM risk_analysis;
DELETE FROM agenda;
DELETE FROM meeting_record;
DELETE FROM weekly_report;
DELETE FROM events_log;
DELETE FROM events;
DELETE FROM task_update_log;
DELETE FROM task;
DELETE FROM milestone_update_log;
DELETE FROM milestone;
DELETE FROM project_document;
DELETE FROM project;

INSERT INTO project (
  project_id, name, start_date, end_date, project_status, description, predicted_cost, project_type, partners
) VALUES (
  1, 'Alloc 샘플 프로젝트', '2024-01-01', '2024-03-31', 'IN_PROGRESS',
  '사내 리소스 부족과 외부 벤더 연동 지연 이슈가 있는 프로젝트. 핵심 목표는 일정 준수와 품질 확보.',
  1000000, 'INTERNAL', '파트너 A'
);

INSERT INTO weekly_report (
  report_id, user_id, project_id, week_start_date, week_end_date, report_status,
  change_of_plan, summary_text, task_completion_rate, is_deleted
) VALUES (
  1, 100, 1, '2024-01-01', '2024-01-07', 'SUBMITTED',
  '외부 API 스펙 변경으로 개발 계획을 일부 재조정함. QA 일정이 2일 밀릴 가능성 있음.',
  '이번 주에는 핵심 API 3개 중 1개만 완료. 코드 리뷰 지연 및 테스트 환경 불안정 이슈 발생.',
  0.35, FALSE
);

INSERT INTO meeting_record (
  meeting_id, project_id, created_by, progress, meeting_date, meeting_time, is_deleted
) VALUES (
  1, 1, 'alice', 0.2, '2024-01-03 10:00:00', '2024-01-03 10:00:00', FALSE
);

INSERT INTO meeting_record (
  meeting_id, project_id, created_by, progress, meeting_date, meeting_time, is_deleted
) VALUES (
  2, 1, 'bob', 0.25, '2024-01-05 15:00:00', '2024-01-05 15:00:00', FALSE
);

INSERT INTO agenda (
  agenda_id, meeting_id, discussion_title, discussion_content, discussion_result, agenda_type
) VALUES (
  1, 1, '일정 지연 위험', '외부 벤더 응답 지연으로 통합 테스트가 최소 3일 밀릴 가능성.', '대체 벤더 검토 및 병행 개발 결정.', 'RISK'
);

INSERT INTO agenda (
  agenda_id, meeting_id, discussion_title, discussion_content, discussion_result, agenda_type
) VALUES (
  2, 1, '리소스 부족', '핵심 개발자 1명이 병가로 1주 이탈 예정.', '우선순위 낮은 기능 개발을 연기하기로 합의.', 'RESOURCE'
);

INSERT INTO agenda (
  agenda_id, meeting_id, discussion_title, discussion_content, discussion_result, agenda_type
) VALUES (
  3, 2, '품질 이슈', '테스트 환경에서 데이터 불일치로 회귀 테스트 실패 빈도 증가.', '테스트 데이터 정합성 점검 및 배포 일정 재조정.', 'QUALITY'
);

INSERT INTO events (
  event_id, project_id, user_id, event_name, event_state, start_date, end_date, event_type, event_place, event_description, is_deleted
) VALUES (
  1, 1, 100, 'Milestone 1', 'PLANNED', '2024-01-10 09:00:00', '2024-01-10 18:00:00',
  'MILESTONE', 'Office', '요구사항 확정 및 API 설계 완료 목표', FALSE
);

INSERT INTO events_log (
  event_log_id, event_id, actor_user_id, change_type, log_description,
  before_start_date, after_start_date, before_end_date, after_end_date, created_at
) VALUES (
  1, 1, 100, 'UPDATE', 'Start date moved by 2 days.',
  '2024-01-10 09:00:00', '2024-01-12 09:00:00', '2024-01-10 18:00:00', '2024-01-12 18:00:00', '2024-01-04 09:00:00'
);

INSERT INTO events_log (
  event_log_id, event_id, actor_user_id, change_type, log_description,
  before_start_date, after_start_date, before_end_date, after_end_date, created_at
) VALUES (
  2, 1, 100, 'UPDATE', '테스트 환경 불안정으로 마일스톤 종료일이 추가로 1일 연장됨.',
  '2024-01-12 09:00:00', '2024-01-12 09:00:00', '2024-01-12 18:00:00', '2024-01-13 18:00:00', '2024-01-06 11:00:00'
);

INSERT INTO milestone (
  milestone_id, project_id, milestone_name, start_date, end_date, achievement_rate, is_deleted, is_completed
) VALUES (
  1, 1, 'Phase 1', '2024-01-01', '2024-01-31', 20, FALSE, FALSE
);

INSERT INTO task (
  task_id, milestone_id, user_id, task_category, task_name, task_description, task_status, start_date, end_date, is_completed, is_deleted
) VALUES (
  1, 1, 100, 'DEV', 'Core API', 'Implement core API endpoints.', 'IN_PROGRESS',
  '2024-01-01', '2024-01-15', FALSE, FALSE
);

INSERT INTO task (
  task_id, milestone_id, user_id, task_category, task_name, task_description, task_status, start_date, end_date, is_completed, is_deleted
) VALUES (
  2, 1, 101, 'TEST', '통합 테스트', '외부 API 연동 통합 테스트 시나리오 작성 및 수행.', 'BLOCKED',
  '2024-01-04', '2024-01-14', FALSE, FALSE
);

INSERT INTO task_update_log (
  task_update_log_id, task_id, update_reason, created_at
) VALUES (
  1, 1, '스키마 변경으로 재작업 필요. 일정 2일 지연 예상.', '2024-01-05 12:00:00'
);

INSERT INTO task_update_log (
  task_update_log_id, task_id, update_reason, created_at
) VALUES (
  2, 2, '외부 API 인증 이슈로 테스트가 진행되지 않음.', '2024-01-06 16:00:00'
);

INSERT INTO milestone_update_log (
  milestone_update_log_id, milestone_id, update_reason, created_at
) VALUES (
  1, 1, '스코프 확대: 보고서 기능 추가로 완료 기준 변경.', '2024-01-06 14:00:00'
);

INSERT INTO project_document (
  doc_id, file_path, extracted_text, uploaded_at
) VALUES (
  1, '/docs/sample.pdf',
  '리스크 요약: 벤더 응답 지연, 테스트 환경 불안정, 리소스 부족으로 일정 지연 가능성 높음. '
  '대응 방안: 대체 벤더 검토, 테스트 데이터 정합성 점검, 우선순위 조정.',
  '2024-01-05 09:00:00'
);
