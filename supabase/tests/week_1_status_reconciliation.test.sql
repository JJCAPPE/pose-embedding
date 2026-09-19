\set ON_ERROR_STOP on

begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(14);

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
  'Protocol', 'Unblock Week 1: Protocol and access',
  'Turn the prospectus into a signed, testable protocol.',
  'A signed protocol and verified inputs.', 480, 0, 'planned', 1
);

insert into public.tasks (
  id, project_id, week_id, position, title, expected_output, state,
  completed_at, version
) values
  (
    'w01-task-01', 'pose-embed', 'week-01', 1, 'Lock protocol',
    'Signed protocol document.', 'done', '2026-09-10 00:00:00+00', 2
  ),
  (
    'w01-task-05', 'pose-embed', 'week-01', 5, 'Close out Week 1',
    'Week 1 closeout.', 'todo', null, 1
  );

select unnest(statements)
  from supabase_migrations.schema_migrations
 where version = '20260916214230'
\gexec

select is(
  (select version from public.weeks where id = 'week-01'),
  2,
  'the reconciliation increments the expected week version'
);
select is(
  (select state from public.weeks where id = 'week-01'),
  'blocked',
  'the reconciliation records the truthful blocked week state'
);
select is(
  (select actual_minutes from public.weeks where id = 'week-01'),
  0,
  'the reconciliation does not invent actual research time'
);
select is(
  (select jsonb_build_object(
    'objective', objective,
    'deliverable', deliverable,
    'reflection', reflection
  ) from public.weeks where id = 'week-01'),
  jsonb_build_object(
    'objective',
      'Turn the prospectus into an advisor-approved, hash-bound, testable protocol and prove that the required data and compute are reachable.',
    'deliverable',
      'An advisor-approved, hash-bound protocol-v1, verified data and checkpoint inventory, and measured GPU profile.',
    'reflection',
      'Week 1 established an advisor-approved, hash-bound protocol, verified the licensed HRNet aggregate, official one-shot split, and MotionBERT checkpoint, and confirmed physical batch 32 on an SCC A40. The input audit found a result-blind contract mismatch: the authorized aggregate has 113,945 usable annotations and the official missing-skeleton list accounts for all 535 omitted captures, while protocol v1 still binds 114,480. The novel test remains sealed pending advisor approval of that amendment. BU''s governance determination and the researcher''s actual-hours record also remain pending.'
  ),
  'the reconciliation writes the reviewed public Week 1 summary'
);
select is(
  (select version from public.tasks where id = 'w01-task-01'),
  3,
  'the protocol task advances from the expected version'
);
select is(
  (select jsonb_build_object(
    'state', state,
    'expected_output', expected_output,
    'evidence_url', evidence_url
  ) from public.tasks where id = 'w01-task-01'),
  jsonb_build_object(
    'state', 'done',
    'expected_output', 'Advisor-approved, hash-bound protocol document.',
    'evidence_url',
      'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/protocol-v1-approval.md'
  ),
  'the protocol task points to its approval record without changing completion'
);
select is(
  (select version from public.tasks where id = 'w01-task-05'),
  2,
  'the closeout task advances from the expected version'
);
select is(
  (select jsonb_build_object(
    'state', state,
    'completed_at', completed_at,
    'evidence_url', evidence_url
  ) from public.tasks where id = 'w01-task-05'),
  jsonb_build_object(
    'state', 'blocked',
    'completed_at', null,
    'evidence_url', null
  ),
  'the closeout task remains incomplete and does not claim evidence'
);

select count(*) as activity_count
  from public.activity_log
 where project_id = 'pose-embed'
\gset

select unnest(statements)
  from supabase_migrations.schema_migrations
 where version = '20260916214230'
\gexec

select is(
  (select version from public.weeks where id = 'week-01'),
  2,
  'an idempotent rerun does not advance the week version'
);
select is(
  (select array_agg(version order by id)
     from public.tasks
    where id in ('w01-task-01', 'w01-task-05')),
  array[3, 2],
  'an idempotent rerun does not advance task versions'
);
select is(
  (select count(*) from public.activity_log where project_id = 'pose-embed'),
  :activity_count::bigint,
  'an idempotent rerun creates no audit events'
);

delete from public.tasks where project_id = 'pose-embed';
delete from public.weeks where project_id = 'pose-embed';

insert into public.weeks (
  id, project_id, number, start_date, end_date, phase, title, objective,
  deliverable, planned_minutes, actual_minutes, state, version
) values (
  'week-01', 'pose-embed', 1, '2026-09-15', '2026-09-20',
  'Protocol', 'Unblock Week 1: Protocol and access',
  'Pre-migration objective.', 'Pre-migration deliverable.',
  480, 0, 'planned', 1
);

insert into public.tasks (
  id, project_id, week_id, position, title, expected_output, state,
  completed_at, version
) values
  (
    'w01-task-01', 'pose-embed', 'week-01', 1, 'Lock protocol',
    'Concurrent edit.', 'done', '2026-09-10 00:00:00+00', 3
  ),
  (
    'w01-task-05', 'pose-embed', 'week-01', 5, 'Close out Week 1',
    'Week 1 closeout.', 'todo', null, 1
  );

select throws_ok(
  (select statements[1]
     from supabase_migrations.schema_migrations
    where version = '20260916214230'),
  '40001',
  null,
  'a stale task version aborts reconciliation with a concurrency conflict'
);
select is(
  (select jsonb_build_object('version', version, 'objective', objective)
     from public.weeks
    where id = 'week-01'),
  jsonb_build_object('version', 1, 'objective', 'Pre-migration objective.'),
  'the stale-version failure rolls back the earlier week update'
);
select is(
  (select jsonb_build_object('version', version, 'expected_output', expected_output)
     from public.tasks
    where id = 'w01-task-01'),
  jsonb_build_object('version', 3, 'expected_output', 'Concurrent edit.'),
  'the stale-version failure preserves the concurrent task edit'
);

select * from finish();
rollback;
