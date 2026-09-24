\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(14);

insert into public.projects (id, slug, title, research_question, start_date, end_date)
values ('pose-embed', 'pose-embed', 'Pose Embed', 'Question?', '2026-09-15', '2026-12-18');
insert into public.weeks (id, project_id, number, start_date, end_date, phase,
  title, objective, deliverable, planned_minutes, actual_minutes, state, version)
values ('week-01', 'pose-embed', 1, '2026-09-15', '2026-09-20', 'Protocol',
  'Protocol and access', 'Objective', 'Deliverable', 480, 167, 'blocked', 5);
insert into public.tasks (id, project_id, week_id, position, title, state, completed_at, version)
values ('w01-task-04', 'pose-embed', 'week-01', 4, 'Governance record', 'done', '2026-09-16T16:07:48Z', 4),
  ('w01-task-05', 'pose-embed', 'week-01', 5, 'Close weekly record', 'blocked', null, 5);
insert into public.gates (id, project_id, week_id, position, criterion, state, evidence, version)
values ('w01-gate-04', 'pose-embed', 'week-01', 4, 'BU determination', 'pending', 'Pending', 2),
  ('w01-gate-02', 'pose-embed', 'week-01', 2, 'Input contract', 'met', 'Adopted', 6);
create temporary table bu_initial_weeks as select * from public.weeks;
create temporary table bu_initial_tasks as select * from public.tasks;
create temporary table bu_initial_gates as select * from public.gates;

select unnest(statements) from supabase_migrations.schema_migrations
where version = '20260924221320'
\gexec

select is((select jsonb_build_object('state', state, 'version', version,
  'decided_at', decided_at, 'waiver_reason', waiver_reason) from public.gates where id = 'w01-gate-04'),
  jsonb_build_object('state', 'met', 'version', 3, 'decided_at', '2026-09-24T22:13:07Z'::timestamptz, 'waiver_reason', ''),
  'BU gate is met on the recorded confirmation, not waived');
select matches((select evidence from public.gates where id = 'w01-gate-04'),
  'researcher confirmation.*no document attachment is required.*not independent document verification',
  'evidence states its source without inventing documentary verification');
select is((select jsonb_build_array(state, completed_at, version) from public.tasks where id = 'w01-task-04'),
  jsonb_build_array('done', '2026-09-16T16:07:48Z'::timestamptz, 5),
  'existing task completion time is preserved while its evidence advances');
select ok((select state = 'blocked' and completed_at is null and version = 6
  and completion_note like '%researcher-supplied actual minutes%' from public.tasks where id = 'w01-task-05'),
  'closeout remains blocked for time entry');
select is((select jsonb_build_array(actual_minutes, state, closed_at, version) from public.weeks where id = 'week-01'),
  jsonb_build_array(167, 'blocked', null, 6), 'actual time is preserved and the week remains open');
select is((select to_jsonb(g) from public.gates g where id = 'w01-gate-02'),
  (select to_jsonb(g) from bu_initial_gates g where id = 'w01-gate-02'), 'other gates are untouched');

create temporary table bu_completed_snapshot as select jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
) as snapshot;
select count(*) as audit_count from public.activity_log \gset
select unnest(statements) from supabase_migrations.schema_migrations
where version = '20260924221320'
\gexec
select is(jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
), (select snapshot from bu_completed_snapshot), 'exact reruns leave all records unchanged');
select is((select count(*) from public.activity_log), :audit_count::bigint, 'exact reruns create no audit event');

delete from public.gates;
delete from public.tasks;
delete from public.weeks;
insert into public.weeks select * from bu_initial_weeks;
insert into public.tasks select * from bu_initial_tasks;
insert into public.gates select * from bu_initial_gates;
update public.gates set evidence = 'Concurrent owner edit' where id = 'w01-gate-04';
select count(*) as audit_count from public.activity_log \gset
select throws_ok((select statements[1] from supabase_migrations.schema_migrations where version = '20260924221320'),
  '40001', 'w01-gate-04 changed; refusing to overwrite', 'a stale gate aborts the full update');
select is((select to_jsonb(w) from public.weeks w where id = 'week-01'),
  (select to_jsonb(w) from bu_initial_weeks w where id = 'week-01'), 'late conflict rolls back the reflection');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  (select jsonb_agg(to_jsonb(t) order by id) from bu_initial_tasks t), 'late conflict rolls back task notes');
select is((select evidence from public.gates where id = 'w01-gate-04'), 'Concurrent owner edit', 'owner edit is preserved');
select is((select count(*) from public.activity_log), :audit_count::bigint, 'late conflict rolls back intermediate audit events');

delete from public.gates;
delete from public.tasks;
update public.weeks set state = 'closed', closed_at = '2026-09-24T22:00:00Z' where id = 'week-01';
select throws_ok((select statements[1] from supabase_migrations.schema_migrations where version = '20260924221320'),
  '40001', 'week-01 is closed; an audited reopen is required', 'closed weeks cannot be silently edited');
select * from finish();
rollback;
