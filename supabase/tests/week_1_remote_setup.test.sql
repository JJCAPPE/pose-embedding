\set ON_ERROR_STOP on

begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(20);

insert into public.projects (
  id, slug, title, research_question, start_date, end_date, visibility
) values (
  'pose-embed', 'pose-embed', 'Pose Embed', 'Research question?',
  '2026-09-15', '2026-12-18', 'public'
);

insert into public.weeks (
  id, project_id, number, start_date, end_date, phase, title, objective,
  deliverable, reflection, planned_minutes, actual_minutes, state, version
) values (
  'week-01', 'pose-embed', 1, '2026-09-15', '2026-09-20',
  'Protocol', 'Protocol and access', 'Objective.', 'Deliverable.',
  'Pre-setup reflection.', 480, 0, 'blocked', 2
);

insert into public.tasks (
  id, project_id, week_id, position, title, state, completion_note,
  completed_at, version
) values
  ('w01-task-01', 'pose-embed', 'week-01', 1, 'Finalize protocol',
   'done', 'Approval recorded.', '2026-09-11T00:00:00Z', 3),
  ('w01-task-02', 'pose-embed', 'week-01', 2, 'Verify licensed inputs',
   'blocked', 'Pre-setup input note.', null, 4),
  ('w01-task-03', 'pose-embed', 'week-01', 3, 'Profile GPU',
   'done', 'Profile recorded.', '2026-09-16T00:00:00Z', 2),
  ('w01-task-04', 'pose-embed', 'week-01', 4, 'Record governance decisions',
   'done', 'Blocking record published.', '2026-09-16T00:00:00Z', 3),
  ('w01-task-05', 'pose-embed', 'week-01', 5, 'Close weekly record',
   'blocked', 'Pre-setup closeout note.', null, 2);

insert into public.gates (
  id, project_id, week_id, position, criterion, state, evidence, version
) values
  ('w01-gate-02', 'pose-embed', 'week-01', 2,
   'Dataset and checkpoint inputs are readable and checksummed.',
   'pending', 'Pre-setup input evidence.', 3),
  ('w01-gate-04', 'pose-embed', 'week-01', 4,
   'Required BU governance determination is recorded.',
   'pending', 'A scope statement is not a BU determination.', 2);

create temporary table remote_setup_initial_weeks as
  select * from public.weeks where project_id = 'pose-embed';
create temporary table remote_setup_initial_tasks as
  select * from public.tasks where project_id = 'pose-embed';
create temporary table remote_setup_initial_gates as
  select * from public.gates where project_id = 'pose-embed';

select unnest(statements)
  from supabase_migrations.schema_migrations
 where version = '20260924152343'
\gexec

select is(
  (select jsonb_build_object('state', state, 'version', version,
    'completed_at', completed_at, 'evidence_url', evidence_url)
   from public.tasks where id = 'w01-task-02'),
  jsonb_build_object('state', 'done', 'version', 5,
    'completed_at', '2026-09-24T15:35:26Z'::timestamptz,
    'evidence_url', 'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md'),
  'input verification completes with the verified evidence and expected version'
);
select matches(
  (select completion_note from public.tasks where id = 'w01-task-02'),
  '113,945.*535.*w01-gate-02 remains pending',
  'the completed task preserves the source count and unresolved protocol gate'
);
select matches(
  (select completion_note from public.tasks where id = 'w01-task-05'),
  'researcher-supplied actual minutes.*advisor-approved input-contract amendment.*BU governance determination',
  'closeout still requires actual minutes and both external decisions'
);
select is(
  (select jsonb_build_object('state', state, 'version', version,
    'completed_at', completed_at, 'evidence_url', evidence_url)
   from public.tasks where id = 'w01-task-05'),
  jsonb_build_object('state', 'blocked', 'version', 3,
    'completed_at', null,
    'evidence_url', 'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md'),
  'closeout advances its evidence without claiming completion'
);
select is(
  (select jsonb_build_object('state', state, 'version', version,
    'actual_minutes', actual_minutes, 'closed_at', closed_at)
   from public.weeks where id = 'week-01'),
  jsonb_build_object('state', 'blocked', 'version', 3,
    'actual_minutes', 0, 'closed_at', null),
  'the week advances without inventing hours or closing'
);
select matches(
  (select reflection from public.weeks where id = 'week-01'),
  'GPU host.*amendment draft is unapproved.*novel test remains sealed',
  'the reflection records remote setup and the remaining test seal'
);
select is(
  (select jsonb_build_object('state', state, 'version', version,
    'criterion', criterion, 'waiver_reason', waiver_reason, 'decided_at', decided_at)
   from public.gates where id = 'w01-gate-02'),
  jsonb_build_object('state', 'pending', 'version', 4,
    'criterion', 'Verified input inventory matches the approved protocol input contract.',
    'waiver_reason', '', 'decided_at', null),
  'the input-contract gate remains undecided under its explicit criterion'
);
select matches(
  (select evidence from public.gates where id = 'w01-gate-02'),
  '113,945.*535.*unapproved draft',
  'gate evidence distinguishes verified inputs from the unapproved amendment'
);
select is(
  (select to_jsonb(gate_row) from public.gates gate_row where id = 'w01-gate-04'),
  (select to_jsonb(gate_row) from remote_setup_initial_gates gate_row where id = 'w01-gate-04'),
  'the BU gate is entirely untouched'
);
select is(
  (select jsonb_build_object('done', count(*) filter (where state = 'done'),
    'required', count(*)) from public.tasks where week_id = 'week-01' and required),
  jsonb_build_object('done', 4, 'required', 5),
  'progress is four of five required tasks, with closeout still blocked'
);

create temporary table remote_setup_completed_snapshot as
  select jsonb_build_object(
    'week', (select to_jsonb(w) from public.weeks w where id = 'week-01'),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where week_id = 'week-01'),
    'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g where week_id = 'week-01')
  ) as snapshot;
select count(*) as activity_count from public.activity_log where project_id = 'pose-embed'
\gset

select unnest(statements)
  from supabase_migrations.schema_migrations
 where version = '20260924152343'
\gexec

select is(
  jsonb_build_object(
    'week', (select to_jsonb(w) from public.weeks w where id = 'week-01'),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where week_id = 'week-01'),
    'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g where week_id = 'week-01')
  ),
  (select snapshot from remote_setup_completed_snapshot),
  'an exact rerun leaves every row and version unchanged'
);
select is(
  (select count(*) from public.activity_log where project_id = 'pose-embed'),
  :activity_count::bigint,
  'an exact rerun produces no new audit event'
);

delete from public.gates where project_id = 'pose-embed';
delete from public.tasks where project_id = 'pose-embed';
delete from public.weeks where project_id = 'pose-embed';
insert into public.weeks select * from remote_setup_initial_weeks;
insert into public.tasks select * from remote_setup_initial_tasks;
insert into public.gates select * from remote_setup_initial_gates;
update public.gates set evidence = 'Concurrent edit.' where id = 'w01-gate-02';
select count(*) as activity_count from public.activity_log where project_id = 'pose-embed'
\gset

select throws_ok(
  (select statements[1] from supabase_migrations.schema_migrations where version = '20260924152343'),
  '40001', null,
  'a stale final gate row aborts the complete migration'
);
select is(
  (select to_jsonb(w) from public.weeks w where id = 'week-01'),
  (select to_jsonb(w) from remote_setup_initial_weeks w where id = 'week-01'),
  'the late conflict rolls back the earlier week update'
);
select is(
  (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where week_id = 'week-01'),
  (select jsonb_agg(to_jsonb(t) order by id) from remote_setup_initial_tasks t where week_id = 'week-01'),
  'the late conflict rolls back both earlier task updates'
);
select is(
  (select jsonb_build_object('version', version, 'evidence', evidence)
   from public.gates where id = 'w01-gate-02'),
  jsonb_build_object('version', 4, 'evidence', 'Concurrent edit.'),
  'the late conflict preserves the concurrent gate edit'
);
select is(
  (select count(*) from public.activity_log where project_id = 'pose-embed'),
  :activity_count::bigint,
  'the late conflict also rolls back intermediate audit events'
);

delete from public.gates where project_id = 'pose-embed';
delete from public.tasks where project_id = 'pose-embed';
update public.weeks set state = 'closed', closed_at = '2026-09-24T15:00:00Z'
 where id = 'week-01';
create temporary table remote_setup_closed_snapshot as
  select to_jsonb(w) as snapshot from public.weeks w where id = 'week-01';
select count(*) as activity_count from public.activity_log where project_id = 'pose-embed'
\gset

select throws_ok(
  (select statements[1] from supabase_migrations.schema_migrations where version = '20260924152343'),
  '40001',
  'week-01 is closed; an audited reopen is required before recording remote setup',
  'a closed week must be explicitly reopened before any migration update'
);
select is(
  (select to_jsonb(w) from public.weeks w where id = 'week-01'),
  (select snapshot from remote_setup_closed_snapshot),
  'closed-week rejection preserves the entire week record'
);
select is(
  (select count(*) from public.activity_log where project_id = 'pose-embed'),
  :activity_count::bigint,
  'closed-week rejection creates no audit event'
);

select * from finish();
rollback;
