\set ON_ERROR_STOP on

begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(11);

insert into public.projects (
  id, slug, title, research_question, start_date, end_date, visibility
) values (
  'pose-embed', 'pose-embed', 'Pose Embed', 'Research question?',
  '2026-09-15', '2026-12-18', 'public'
);

insert into public.weeks (
  id, project_id, number, start_date, end_date, phase, title, objective,
  deliverable, planned_minutes, actual_minutes, state, version
) values (
  'week-01', 'pose-embed', 1, '2026-09-15', '2026-09-20',
  'Protocol', 'Protocol and access', 'Objective.', 'Deliverable.',
  480, 0, 'blocked', 2
);

insert into public.tasks (
  id, project_id, week_id, position, title, expected_output, state,
  completion_note, evidence_url, completed_at, version
) values (
  'w01-task-04', 'pose-embed', 'week-01', 4, 'Record governance decisions',
  'Approval evidence or a visible blocking record.', 'blocked',
  'Researcher-authored scope statement recorded on 2026-09-15: the project performs computational model training and evaluation on existing licensed pose annotations. It involves no participant recruitment, interaction, intervention, prospective data collection, direct identifiers, re-identification, or animal work. Because the source poses were derived from recordings of people, the statement does not itself establish BU human-subjects/data-governance status. The existing protocol advisor approval remains recorded separately. Unresolved condition (verbatim): ''BU provides the applicable human-subjects/data-governance determination.''',
  'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md',
  null, 2
);

insert into public.gates (
  id, project_id, week_id, position, criterion, state, evidence,
  waiver_reason, decided_at, version
) values (
  'w01-gate-04', 'pose-embed', 'week-01', 4,
  'Required BU governance determination is recorded.', 'pending',
  'The visible record is not a BU determination.', '', null, 2
);

select unnest(statements)
  from supabase_migrations.schema_migrations
 where version = '20260921154248'
\gexec

select is(
  (select version from public.tasks where id = 'w01-task-04'),
  3,
  'the migration advances the expected task version'
);
select is(
  (select state from public.tasks where id = 'w01-task-04'),
  'done',
  'the visible governance record completes the recording task'
);
select is(
  (select completed_at from public.tasks where id = 'w01-task-04'),
  '2026-09-16T16:07:48Z'::timestamptz,
  'the task uses the evidence publication time'
);
select matches(
  (select completion_note from public.tasks where id = 'w01-task-04'),
  'w01-gate-04 remains pending',
  'the task note preserves the unresolved BU gate'
);
select is(
  (select jsonb_build_object(
    'state', state,
    'waiver_reason', waiver_reason,
    'decided_at', decided_at,
    'version', version
  ) from public.gates where id = 'w01-gate-04'),
  jsonb_build_object(
    'state', 'pending',
    'waiver_reason', '',
    'decided_at', null,
    'version', 2
  ),
  'completing the record task does not decide or waive the BU gate'
);

select count(*) as activity_count
  from public.activity_log
 where project_id = 'pose-embed'
\gset

select unnest(statements)
  from supabase_migrations.schema_migrations
 where version = '20260921154248'
\gexec

select is(
  (select version from public.tasks where id = 'w01-task-04'),
  3,
  'an idempotent rerun does not advance the task version'
);
select is(
  (select count(*) from public.activity_log where project_id = 'pose-embed'),
  :activity_count::bigint,
  'an idempotent rerun creates no audit event'
);
select is(
  (select jsonb_build_object(
    'state', state,
    'waiver_reason', waiver_reason,
    'decided_at', decided_at,
    'version', version
  ) from public.gates where id = 'w01-gate-04'),
  jsonb_build_object(
    'state', 'pending',
    'waiver_reason', '',
    'decided_at', null,
    'version', 2
  ),
  'an idempotent rerun still leaves the BU gate untouched'
);

delete from public.tasks where project_id = 'pose-embed';

insert into public.tasks (
  id, project_id, week_id, position, title, expected_output, state,
  completion_note, evidence_url, completed_at, version
) values (
  'w01-task-04', 'pose-embed', 'week-01', 4, 'Record governance decisions',
  'Approval evidence or a visible blocking record.', 'blocked',
  'Concurrent edit.',
  'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md',
  null, 3
);

select throws_ok(
  (select statements[1]
     from supabase_migrations.schema_migrations
    where version = '20260921154248'),
  '40001',
  null,
  'a stale task version aborts with a concurrency conflict'
);
select is(
  (select version from public.tasks where id = 'w01-task-04'),
  3,
  'the conflict preserves the concurrent task version'
);
select is(
  (select completion_note from public.tasks where id = 'w01-task-04'),
  'Concurrent edit.',
  'the conflict preserves concurrent task content'
);

select * from finish();
rollback;
