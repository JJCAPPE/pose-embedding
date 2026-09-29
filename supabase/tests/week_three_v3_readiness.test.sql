\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(28);

create temporary table week3_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20260929205436'
));
create function pg_temp.apply_week3_v3() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20260929205436');
end;
$$;

truncate public.projects cascade;
select lives_ok('select pg_temp.apply_week3_v3()',
  'an unseeded database defers to the canonical v3 import');
insert into auth.users (id, email)
values ('44444444-4444-4444-4444-444444444444', 'week3-v3-owner@example.com');

create function pg_temp.seed_week3_predecessor(content_change boolean default false)
returns void language plpgsql as $$
declare predecessor jsonb; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  insert into public.projects (id, slug, title, research_question, start_date, end_date)
  values ('pose-embed', 'pose-embed', 'Preserved project', 'Preserved question',
    '2026-09-15', '2026-12-18');
  select edit->'before' into predecessor from week3_edits where edit->>'table' = 'weeks';
  if content_change then
    predecessor := predecessor || '{"objective":"Concurrent researcher content"}'::jsonb;
  end if;
  select string_agg(format('%I', key), ', ' order by key),
         string_agg(format('v.%I', key), ', ' order by key)
    into columns_sql, values_sql from jsonb_object_keys(predecessor) key;
  execute format('insert into public.weeks (%s) select %s from jsonb_populate_record(null::public.weeks, $1) v',
    columns_sql, values_sql) using predecessor;
  insert into public.weeks (id, project_id, number, start_date, end_date, phase,
    title, objective, deliverable, reflection, planned_minutes, actual_minutes)
  select 'week-0' || n, 'pose-embed', n, '2026-09-15', '2026-10-11',
    'Preserved phase', 'Preserved week', 'Preserved objective',
    'Preserved deliverable', 'Preserved reflection', 480,
    case when n = 1 then 167 else 0 end from unnest(array[1, 2, 4]) n;
  insert into public.tasks (id, project_id, week_id, position, title, state,
    completion_note, evidence_url, completed_at)
  select 'w03-task-0' || n, 'pose-embed', 'week-03', n,
    'Historical task ' || n, 'done', 'Preserved evidence ' || n,
    'https://example.com/evidence/' || n, '2026-09-28T12:00:00Z'
    from generate_series(1, 5) n;
  insert into public.gates (id, project_id, week_id, position, criterion, state,
    evidence, decided_at)
  select 'w03-gate-0' || n, 'pose-embed', 'week-03', n,
    'Historical gate ' || n, 'met', 'Preserved evidence ' || n,
    '2026-09-28T12:00:00Z' from generate_series(1, 5) n;
  update public.weeks set state = 'closed', closed_at = '2026-09-28T13:00:00Z'
    where id in ('week-01', 'week-02');
  insert into private.project_owners (project_id, owner_id)
  values ('pose-embed', '44444444-4444-4444-4444-444444444444');
  insert into public.sources (id, project_id, title, canonical_url, verified_at)
  values ('source-plan-v3', 'pose-embed', 'Final v3 plan',
    'https://example.com/plan-v3', '2026-09-29'),
    ('source-historical', 'pose-embed', 'Historical evidence',
    'https://example.com/history', '2026-09-28');
  insert into public.week_sources (project_id, week_id, source_id, purpose)
  values ('pose-embed', 'week-03', 'source-historical', 'Preserved historical link');
end;
$$;
create function pg_temp.week3_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'projects', (select jsonb_agg(to_jsonb(t) order by id) from public.projects t),
    'weeks', (select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates', (select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'sources', (select jsonb_agg(to_jsonb(t) order by id) from public.sources t),
    'week_sources', (select jsonb_agg(to_jsonb(t) order by week_id, source_id) from public.week_sources t),
    'owners', (select jsonb_agg(to_jsonb(t) order by project_id) from private.project_owners t),
    'activity', (select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t)
  );
$$;
select pg_temp.seed_week3_predecessor();
create temporary table week3_before as select pg_temp.week3_snapshot() as content;
select count(*) as audit_count from public.activity_log \gset

select lives_ok('select pg_temp.apply_week3_v3()', 'the captured Week 3 predecessor adopts v3 readiness');
select is((select title from public.weeks where id = 'week-03'),
  'Verified v3 implementation and sealed preparation', 'Week 3 adopts its current v3 objective');
select is((select version from public.weeks where id = 'week-03'), 7,
  'the version trigger advances Week 3 exactly once');
select is((select jsonb_agg(to_jsonb(w) order by id) from public.weeks w where id <> 'week-03'),
  (select jsonb_agg(value order by value->>'id') from week3_before,
    jsonb_array_elements(content->'weeks') where value->>'id' <> 'week-03'),
  'closed Weeks 1/2 and future Week 4 remain byte-identical');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where position <= 5),
  (select content->'tasks' from week3_before), 'all five historical tasks retain their evidence and versions');
select is((select jsonb_agg(to_jsonb(g) order by id) from public.gates g where position <= 5),
  (select content->'gates' from week3_before), 'all five historical gates retain their evidence and versions');
select ok((select starts_with(reflection, (select edit->'before'->>'reflection'
  from week3_edits where edit->>'table' = 'weeks')) from public.weeks where id = 'week-03'),
  'the original reflection remains an exact prefix');
select is((select jsonb_build_array(planned_minutes, actual_minutes, state, closed_at)
  from public.weeks where id = 'week-03'), '[480, 0, "active", null]'::jsonb,
  'Week 3 is active without changing time or claiming closure');
select is((select state from public.tasks where id = 'w03-task-06'), 'done',
  'implemented software is recorded separately');
select is((select state from public.gates where id = 'w03-gate-06'), 'met',
  'software checks have a separate gate');
select is((select jsonb_build_array(state, completed_at) from public.tasks where id = 'w03-task-07'),
  '["todo", null]'::jsonb, 'real SCC preparation and design freeze are incomplete');
select is((select jsonb_build_array(state, decided_at) from public.gates where id = 'w03-gate-07'),
  '["pending", null]'::jsonb, 'real SCC evidence remains a pending gate');
select is((pg_temp.week3_snapshot())->'owners', (select content->'owners' from week3_before),
  'private ownership is unchanged');
select is((select jsonb_agg(to_jsonb(a) order by id) from public.activity_log a
  where id in (select (value->>'id')::bigint from week3_before,
    jsonb_array_elements(content->'activity'))),
  (select content->'activity' from week3_before), 'previous audit events remain unchanged');
select is((select count(*) from public.activity_log), :audit_count::bigint + 6,
  'the six declared mutations each create an audit event');
select is((select jsonb_agg(to_jsonb(t) order by week_id, source_id)
  from public.week_sources t where source_id = 'source-historical'),
  (select content->'week_sources' from week3_before), 'historical source links remain unchanged');
select is((select priority from public.week_sources where week_id = 'week-03'
  and source_id = 'source-plan-v3'), 'required', 'Week 3 links its current final v3 plan');
create temporary table week3_after as select pg_temp.week3_snapshot() as content;
select lives_ok('select pg_temp.apply_week3_v3()', 'an exact replay is accepted');
select is(pg_temp.week3_snapshot(), (select content from week3_after),
  'replay preserves every row, version and audit event');

select pg_temp.seed_week3_predecessor();
update public.weeks set objective = objective where id = 'week-03';
create temporary table week3_version_conflict as select pg_temp.week3_snapshot() as content;
select throws_ok('select pg_temp.apply_week3_v3()', '40001',
  'week-03 changed; refusing to overwrite live progress', 'a changed version refuses migration');
select is(pg_temp.week3_snapshot(), (select content from week3_version_conflict),
  'a version conflict preserves all progress and audit history');

select pg_temp.seed_week3_predecessor(true);
create temporary table week3_content_conflict as select pg_temp.week3_snapshot() as content;
select throws_ok('select pg_temp.apply_week3_v3()', '40001',
  'week-03 changed; refusing to overwrite live progress', 'changed content at the expected version refuses migration');
select is(pg_temp.week3_snapshot(), (select content from week3_content_conflict),
  'a content conflict preserves the researcher edit');

select pg_temp.seed_week3_predecessor();
insert into public.gates (id, project_id, week_id, position, criterion)
values ('w03-gate-07', 'pose-embed', 'week-03', 7, 'Concurrent researcher gate');
create temporary table week3_late_conflict as select pg_temp.week3_snapshot() as content;
select throws_ok('select pg_temp.apply_week3_v3()', '40001',
  'w03-gate-07 already exists with different content', 'a late child conflict refuses migration');
select is(pg_temp.week3_snapshot(), (select content from week3_late_conflict),
  'late conflict rolls back the earlier update, child inserts and audit events');

select pg_temp.seed_week3_predecessor();
update public.weeks set state = 'closed', closed_at = '2026-09-29T12:00:00Z' where id = 'week-03';
create temporary table week3_closed_conflict as select pg_temp.week3_snapshot() as content;
select throws_ok('select pg_temp.apply_week3_v3()', '40001',
  'week-03 is missing or closed; an audited reopen is required', 'closed Week 3 requires an explicit audited reopen');
select is(pg_temp.week3_snapshot(), (select content from week3_closed_conflict),
  'closed-week rejection preserves all history and ownership');

select * from finish();
rollback;
