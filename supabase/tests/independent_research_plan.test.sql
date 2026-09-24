\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(15);

-- Construct a minimal seeded predecessor at the migration's expected versions.
create temporary table governance_edits as
  select value as edit from jsonb_array_elements((
    select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
    from supabase_migrations.schema_migrations where version = '20260924154741'
  ));
insert into public.projects
  (id, slug, title, research_question, start_date, end_date, visibility)
values ('pose-embed', 'pose-embed', 'Pose Embed', 'Question?', '2026-09-15', '2026-12-18', 'public');
insert into public.weeks
  (id, project_id, number, start_date, end_date, phase, title, objective,
   deliverable, planned_minutes, actual_minutes, state, version)
select parent_id, 'pose-embed', right(parent_id, 2)::integer, '2026-09-15',
  '2026-12-18', 'Research', 'Week', 'Old objective', 'Old deliverable', 480, 167,
  case when parent_id = 'week-01' then 'blocked' else 'planned' end,
  coalesce((select (edit->>'version')::integer from governance_edits
    where edit->>'table' = 'weeks' and edit->>'id' = parent_id), 1)
from (select distinct edit->>'week_id' as parent_id from governance_edits) parents;
insert into public.tasks
  (id, project_id, week_id, position, title, state, completed_at, version)
select edit->>'id', 'pose-embed', edit->>'week_id', right(edit->>'id', 2)::integer,
  'Old task', edit->>'state',
  case when edit->>'state' = 'done' then '2026-09-16T00:00:00Z'::timestamptz end,
  (edit->>'version')::integer
from governance_edits where edit->>'table' = 'tasks';
insert into public.gates
  (id, project_id, week_id, position, criterion, evidence, state, decided_at, version)
select edit->>'id', 'pose-embed', edit->>'week_id', right(edit->>'id', 2)::integer,
  'Old criterion', 'Existing evidence', edit->>'state',
  case when edit->>'state' = 'met' then '2026-09-16T00:00:00Z'::timestamptz end,
  (edit->>'version')::integer
from governance_edits where edit->>'table' = 'gates';
insert into public.gates
  (id, project_id, week_id, position, criterion, state, evidence, version)
values ('w01-gate-04', 'pose-embed', 'week-01', 4, 'BU determination', 'pending', 'Not provided', 2);

create temporary table governance_initial_weeks as select * from public.weeks;
create temporary table governance_initial_tasks as select * from public.tasks;
create temporary table governance_initial_gates as select * from public.gates;

select unnest(statements) from supabase_migrations.schema_migrations
where version = '20260924154741'
\gexec

select is((select criterion from public.gates where id = 'w01-gate-01'),
  'Protocol-v1 is documented under researcher control and its hash is recorded.',
  'protocol gate requires a researcher record, not an advisor');
select is((select criterion from public.gates where id = 'w07-gate-02'),
  'Final hashes, fairness audit, and analysis plan are recorded before test opening.',
  'later scientific lock retains evidence requirements without advisor approval');
select is((select actual_minutes from public.weeks where id = 'week-01'), 167,
  'actual minutes are preserved, not reset or invented');
select is((select to_jsonb(g) from public.gates g where id = 'w01-gate-04'),
  (select to_jsonb(g) from governance_initial_gates g where id = 'w01-gate-04'),
  'the BU determination is untouched');
select is((select jsonb_agg(jsonb_build_array(id, state, completed_at) order by id) from public.tasks),
  (select jsonb_agg(jsonb_build_array(id, state, completed_at) order by id) from governance_initial_tasks),
  'all task states and completion timestamps are preserved');
select is((select jsonb_agg(jsonb_build_array(id, state, decided_at) order by id) from public.gates),
  (select jsonb_agg(jsonb_build_array(id, state, decided_at) order by id) from governance_initial_gates),
  'all gate decisions and timestamps are preserved');
select ok(not exists (
  select 1 from governance_edits e join (
    select 'weeks' as kind, id, version from public.weeks union all
    select 'tasks', id, version from public.tasks union all
    select 'gates', id, version from public.gates
  ) rows on rows.kind = edit->>'table' and rows.id = edit->>'id'
  where rows.version <> (edit->>'version')::integer + 1
), 'each edited row advances exactly one version');

create temporary table governance_completed_snapshot as select jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
) as snapshot;
select count(*) as audit_count from public.activity_log \gset
select unnest(statements) from supabase_migrations.schema_migrations
where version = '20260924154741'
\gexec
select is(jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
), (select snapshot from governance_completed_snapshot), 'exact reruns are idempotent');
select is((select count(*) from public.activity_log), :audit_count::bigint,
  'exact reruns create no audit events');

delete from public.gates;
delete from public.tasks;
delete from public.weeks;
insert into public.weeks select * from governance_initial_weeks;
insert into public.tasks select * from governance_initial_tasks;
insert into public.gates select * from governance_initial_gates;
update public.gates set evidence = 'Owner edit' where id = 'w13-gate-02';
select count(*) as audit_count from public.activity_log \gset
select throws_ok((select statements[1] from supabase_migrations.schema_migrations where version = '20260924154741'),
  '40001', null, 'a stale late row aborts the entire migration');
select is((select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  (select jsonb_agg(to_jsonb(w) order by id) from governance_initial_weeks w),
  'a late conflict rolls back earlier week updates');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  (select jsonb_agg(to_jsonb(t) order by id) from governance_initial_tasks t),
  'a late conflict rolls back earlier task updates');
select is((select evidence from public.gates where id = 'w13-gate-02'), 'Owner edit',
  'the owner edit is preserved');
select is((select count(*) from public.activity_log), :audit_count::bigint,
  'a late conflict rolls back intermediate audit events');

-- Closed weeks must still be explicitly reopened with an audited reason.
delete from public.gates where week_id = 'week-01';
delete from public.tasks where week_id = 'week-01';
update public.weeks set state = 'closed', closed_at = '2026-09-24T15:00:00Z'
where id = 'week-01';
select throws_ok((select statements[1] from supabase_migrations.schema_migrations where version = '20260924154741'),
  '40001', 'week-01 is closed; an audited reopen is required',
  'closed-week safeguards remain mandatory');
select * from finish();
rollback;
