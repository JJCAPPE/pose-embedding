\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(20);

select lives_ok(
  (select statements[1] from supabase_migrations.schema_migrations
    where version = '20260924160756'),
  'unseeded databases defer the tracker state to the canonical plan'
);

insert into public.projects
  (id, slug, title, research_question, start_date, end_date, visibility)
values ('pose-embed', 'pose-embed', 'Pose Embed', 'Question?',
  '2026-09-15', '2026-12-18', 'public');
insert into public.weeks
  (id, project_id, number, start_date, end_date, phase, title, objective,
   deliverable, planned_minutes, actual_minutes, state, reflection, version)
values
  ('week-01', 'pose-embed', 1, '2026-09-15', '2026-09-20', 'Protocol',
   'Week 1', 'Objective', 'Deliverable', 480, 0, 'blocked', 'Prior reflection', 4),
  ('week-02', 'pose-embed', 2, '2026-09-21', '2026-09-27', 'Data',
   'Week 2', 'Objective', 'Deliverable', 480, 0, 'planned', 'Unchanged reflection', 1);
insert into public.tasks
  (id, project_id, week_id, position, title, state, completion_note,
   completed_at, version)
values
  ('w01-task-01', 'pose-embed', 'week-01', 1, 'Finalize protocol', 'done',
   'Prior hash', '2026-09-11T17:41:08Z', 4),
  ('w01-task-02', 'pose-embed', 'week-01', 2, 'Verify inputs', 'done',
   'Prior pending-gate note', '2026-09-24T15:35:26Z', 6),
  ('w01-task-05', 'pose-embed', 'week-01', 5, 'Close weekly record', 'blocked',
   'Prior closeout note', null, 4);
insert into public.gates
  (id, project_id, week_id, position, criterion, state, evidence,
   decided_at, version)
values
  ('w01-gate-01', 'pose-embed', 'week-01', 1, 'Protocol hash', 'met',
   'Prior protocol hash', '2026-09-11T17:41:08Z', 3),
  ('w01-gate-02', 'pose-embed', 'week-01', 2, 'Input contract', 'pending',
   'Amendment pending', null, 5),
  ('w01-gate-04', 'pose-embed', 'week-01', 4, 'BU determination', 'pending',
   'Not provided', null, 2),
  ('w02-gate-01', 'pose-embed', 'week-02', 1, 'Seven manifests', 'pending',
   'Amendment pending', null, 3);

create temporary table input_contract_initial_weeks as select * from public.weeks;
create temporary table input_contract_initial_tasks as select * from public.tasks;
create temporary table input_contract_initial_gates as select * from public.gates;

select unnest(statements) from supabase_migrations.schema_migrations
where version = '20260924160756'
\gexec

select is((select version from public.weeks where id = 'week-01'), 5,
  'Week 1 reflection advances exactly one version');
select is((select jsonb_build_object('state', state, 'actual_minutes', actual_minutes,
  'closed_at', closed_at) from public.weeks where id = 'week-01'),
  jsonb_build_object('state', 'blocked', 'actual_minutes', 0, 'closed_at', null),
  'Week 1 remains open without invented time');
select is((select to_jsonb(w) from public.weeks w where id = 'week-02'),
  (select to_jsonb(w) from input_contract_initial_weeks w where id = 'week-02'),
  'Week 2 progress remains untouched');
select is((select jsonb_build_object('state', state, 'version', version,
  'completed_at', completed_at) from public.tasks where id = 'w01-task-02'),
  jsonb_build_object('state', 'done', 'version', 7,
    'completed_at', '2026-09-24T15:35:26Z'::timestamptz),
  'the verified-input task retains its original completion time');
select is((select jsonb_build_object('state', state, 'version', version,
  'completed_at', completed_at) from public.tasks where id = 'w01-task-05'),
  jsonb_build_object('state', 'blocked', 'version', 5, 'completed_at', null),
  'closeout stays blocked on BU governance and actual time');
select matches((select completion_note from public.tasks where id = 'w01-task-05'),
  'actual minutes and the BU governance determination',
  'the closeout note lists only genuine remaining blockers');
select is((select to_jsonb(g) from public.gates g where id = 'w01-gate-04'),
  (select to_jsonb(g) from input_contract_initial_gates g where id = 'w01-gate-04'),
  'the BU gate remains entirely untouched');
select is((select jsonb_build_object('state', state, 'version', version,
  'waiver_reason', waiver_reason, 'decided_at', decided_at)
  from public.gates where id = 'w01-gate-02'),
  jsonb_build_object('state', 'met', 'version', 6, 'waiver_reason', '',
    'decided_at', '2026-09-24T16:25:10Z'::timestamptz),
  'Week 1 input-contract gate is met at the recorded decision time');
select is((select jsonb_build_object('state', state, 'version', version,
  'waiver_reason', waiver_reason, 'decided_at', decided_at)
  from public.gates where id = 'w02-gate-01'),
  jsonb_build_object('state', 'met', 'version', 4, 'waiver_reason', '',
    'decided_at', '2026-09-24T16:25:10Z'::timestamptz),
  'Week 2 manifest gate is met at the same decision time');
select matches((select evidence from public.gates where id = 'w01-gate-02'),
  '113,945.*535.*114,480.*input-contract-amendment.v1.md.*c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f',
  'input evidence binds the count, source contract, and protocol hash');
select matches((select evidence from public.gates where id = 'w02-gate-01'),
  'Seven immutable.*113,945.*535.*114,480.*c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f.*ntu-manifest-audit.v2.md',
  'manifest evidence binds the release and adopted protocol hash');
select matches((select evidence from public.gates where id = 'w01-gate-01'),
  'c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f',
  'the existing protocol gate records the current hash');

create temporary table input_contract_completed_snapshot as select jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
) as snapshot;
select count(*) as activity_count from public.activity_log \gset
select unnest(statements) from supabase_migrations.schema_migrations
where version = '20260924160756'
\gexec
select is(jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
), (select snapshot from input_contract_completed_snapshot),
  'exact reruns do not alter rows or versions');
select is((select count(*) from public.activity_log), :activity_count::bigint,
  'exact reruns create no audit event');

delete from public.gates;
delete from public.tasks;
delete from public.weeks;
insert into public.weeks select * from input_contract_initial_weeks;
insert into public.tasks select * from input_contract_initial_tasks;
insert into public.gates select * from input_contract_initial_gates;
update public.gates set evidence = 'Concurrent owner edit' where id = 'w02-gate-01';
select count(*) as activity_count from public.activity_log \gset
select throws_ok((select statements[1] from supabase_migrations.schema_migrations
  where version = '20260924160756'), '40001',
  'w02-gate-01 changed; refusing to overwrite live progress',
  'a late gate edit rejects the entire migration');
select is((select to_jsonb(w) from public.weeks w where id = 'week-01'),
  (select to_jsonb(w) from input_contract_initial_weeks w where id = 'week-01'),
  'a late conflict rolls back the earlier Week 1 change');
select is((select evidence from public.gates where id = 'w02-gate-01'),
  'Concurrent owner edit', 'the owner edit is preserved');
select is((select count(*) from public.activity_log), :activity_count::bigint,
  'the failed migration rolls back intermediate audit events');

delete from public.gates where week_id = 'week-01';
delete from public.tasks where week_id = 'week-01';
update public.weeks set state = 'closed', closed_at = '2026-09-24T16:00:00Z'
where id = 'week-01';
select throws_ok((select statements[1] from supabase_migrations.schema_migrations
  where version = '20260924160756'), '40001',
  'week-01 is closed; an audited reopen is required',
  'closed weeks require an audited reopen before migration updates');
select * from finish();
rollback;
