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
  1, 'Alloc Sample Project', '2024-01-01', '2024-03-31', 'IN_PROGRESS',
  'Sample project for risk report testing', 1000000, 'INTERNAL', 'Partner A'
);

INSERT INTO weekly_report (
  report_id, user_id, project_id, week_start_date, week_end_date, report_status,
  change_of_plan, summary_text, task_completion_rate, is_deleted
) VALUES (
  1, 100, 1, '2024-01-01', '2024-01-07', 'SUBMITTED',
  'Delayed due to dependency changes.', 'Scope updated for sprint 1.', 0.35, FALSE
);

INSERT INTO meeting_record (
  meeting_id, project_id, created_by, progress, meeting_date, meeting_time, is_deleted
) VALUES (
  1, 1, 'alice', 0.2, '2024-01-03 10:00:00', '2024-01-03 10:00:00', FALSE
);

INSERT INTO agenda (
  agenda_id, meeting_id, discussion_title, discussion_content, discussion_result, agenda_type
) VALUES (
  1, 1, 'Schedule risk', 'Vendor delay impacts critical path.', 'Mitigation required.', 'RISK'
);

INSERT INTO events (
  event_id, project_id, user_id, event_name, event_state, start_date, end_date, event_type, event_place, event_description, is_deleted
) VALUES (
  1, 1, 100, 'Milestone 1', 'PLANNED', '2024-01-10 09:00:00', '2024-01-10 18:00:00',
  'MILESTONE', 'Office', 'Initial milestone planning', FALSE
);

INSERT INTO events_log (
  event_log_id, event_id, actor_user_id, change_type, log_description,
  before_start_date, after_start_date, before_end_date, after_end_date, created_at
) VALUES (
  1, 1, 100, 'UPDATE', 'Start date moved by 2 days.',
  '2024-01-10 09:00:00', '2024-01-12 09:00:00', '2024-01-10 18:00:00', '2024-01-12 18:00:00', '2024-01-04 09:00:00'
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

INSERT INTO task_update_log (
  task_update_log_id, task_id, update_reason, created_at
) VALUES (
  1, 1, 'Blocked by schema changes.', '2024-01-05 12:00:00'
);

INSERT INTO milestone_update_log (
  milestone_update_log_id, milestone_id, update_reason, created_at
) VALUES (
  1, 1, 'Milestone scope increased.', '2024-01-06 14:00:00'
);

INSERT INTO project_document (
  doc_id, file_path, extracted_text, uploaded_at
) VALUES (
  1, '/docs/sample.pdf', 'Risk notes: vendor delay and scope increase.', '2024-01-05 09:00:00'
);
