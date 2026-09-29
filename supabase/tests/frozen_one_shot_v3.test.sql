\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(25);

create temporary table v3_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20260929174130'
));
create function pg_temp.apply_v3() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20260929174130');
end;
$$;

select lives_ok('select pg_temp.apply_v3()',
  'an unseeded database defers to the canonical v3 import');

insert into auth.users (id, email)
values ('33333333-3333-3333-3333-333333333333', 'v3-owner@example.com');

-- Reconstruct touched public rows from the migration's captured predecessor.
-- Unchanged references and historical rows are small, explicit test fixtures.
create function pg_temp.seed_v3_predecessor() returns void language plpgsql as $$
declare table_name text; edit jsonb; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  for table_name in select unnest(array['projects', 'weeks', 'tasks', 'gates', 'sources', 'week_sources'])
  loop
    if table_name = 'week_sources' then
      insert into public.sources (id, project_id, title, canonical_url, verified_at)
      select distinct e.edit->>'source_id', 'pose-embed', 'Unchanged reference',
        'https://example.com/' || (e.edit->>'source_id'), '2026-09-15'::date
      from v3_edits e where e.edit->>'table' = 'week_sources'
        and not exists (select 1 from v3_edits s where s.edit->>'table' = 'sources'
          and s.edit->>'id' = e.edit->>'source_id');
    end if;
    for edit in select e.edit from v3_edits e
      where e.edit->>'table' = table_name and e.edit->'before' <> 'null'::jsonb
    loop
      select string_agg(format('%I', key), ', ' order by key),
             string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
      execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
        table_name, columns_sql, values_sql, table_name) using edit->'before';
    end loop;
  end loop;
  insert into public.weeks (id, project_id, number, start_date, end_date, phase,
    title, objective, deliverable, reflection, planned_minutes, actual_minutes)
  select 'week-0' || n, 'pose-embed', n, '2026-09-15', '2026-10-04',
    'Historical evidence', 'Preserved week', 'Preserved objective',
    'Preserved deliverable', 'Researcher time remains unreconciled.', 480,
    case when n = 1 then 167 else 0 end from generate_series(1, 3) n;
  insert into public.tasks (id, project_id, week_id, position, title, state,
    completion_note, evidence_url, completed_at)
  select 'w0' || n || '-task-01', 'pose-embed', 'week-0' || n, 1,
    'Verified historical work', 'done', 'Preserved completion evidence',
    'https://example.com/evidence', '2026-09-28T12:00:00Z' from generate_series(1, 3) n;
  insert into public.gates (id, project_id, week_id, position, criterion, state,
    evidence, decided_at)
  select 'w0' || n || '-gate-01', 'pose-embed', 'week-0' || n, 1,
    'Verified historical gate', 'met', 'Preserved gate evidence',
    '2026-09-28T12:00:00Z' from generate_series(1, 3) n;
  insert into public.week_sources (project_id, week_id, source_id, purpose)
  values ('pose-embed', 'week-03', 'source-benchmark-v2', 'Historical v2 record');
  update public.weeks set state = 'closed', closed_at = '2026-09-28T13:00:00Z'
    where id = 'week-01';
  update public.weeks set state = 'closed', closed_at = '2026-09-28T14:00:00Z'
    where id = 'week-02';
  insert into private.project_owners (project_id, owner_id)
  values ('pose-embed', '33333333-3333-3333-3333-333333333333');
end;
$$;

create function pg_temp.v3_snapshot() returns jsonb language sql as $$
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
select pg_temp.seed_v3_predecessor();
create temporary table v3_before as select pg_temp.v3_snapshot() as content;
select count(*) as audit_count from public.activity_log \gset

select lives_ok('select pg_temp.apply_v3()', 'the captured predecessor adopts v3');
select is((select title from public.projects where id = 'pose-embed'),
  'Frozen one-shot pose robustness', 'the public project adopts the frozen one-shot scope');
select matches((select summary from public.projects where id = 'pose-embed'),
  'three paired seeds, 20 epochs.*27 selection runs, nine fresh final heads, and 180 locked evaluation cells',
  'the public campaign has the fixed seed, horizon, run and evaluation counts');
select is((select jsonb_agg(to_jsonb(w) order by id) from public.weeks w where number <= 3),
  (select jsonb_agg(value order by value->>'id') from v3_before,
    jsonb_array_elements(content->'weeks') where (value->>'number')::integer <= 3),
  'Weeks 1-3 retain all content, dates, state, time and versions');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where week_id < 'week-04'),
  (select jsonb_agg(value order by value->>'id') from v3_before,
    jsonb_array_elements(content->'tasks') where value->>'week_id' < 'week-04'),
  'historical task completions and evidence remain unchanged');
select is((select jsonb_agg(to_jsonb(g) order by id) from public.gates g where week_id < 'week-04'),
  (select jsonb_agg(value order by value->>'id') from v3_before,
    jsonb_array_elements(content->'gates') where value->>'week_id' < 'week-04'),
  'historical gate decisions and evidence remain unchanged');
select is((select jsonb_agg(to_jsonb(s) order by week_id, source_id)
  from public.week_sources s where week_id < 'week-04'),
  (select jsonb_agg(value order by value->>'week_id', value->>'source_id') from v3_before,
    jsonb_array_elements(content->'week_sources') where value->>'week_id' < 'week-04'),
  'historical source links remain unchanged');
select is((select jsonb_agg(jsonb_build_array(id, actual_minutes, planned_minutes, state, closed_at, reflection)
  order by id) from public.weeks),
  (select jsonb_agg(jsonb_build_array(value->'id', value->'actual_minutes', value->'planned_minutes',
    value->'state', value->'closed_at', value->'reflection') order by value->>'id')
    from v3_before, jsonb_array_elements(content->'weeks')),
  'all time, closure and reflection fields are preserved without invented hours');
select is((select jsonb_agg(jsonb_build_array(id, state, completion_note, evidence_url, completed_at)
  order by id) from public.tasks),
  (select jsonb_agg(jsonb_build_array(value->'id', value->'state', value->'completion_note',
    value->'evidence_url', value->'completed_at') order by value->>'id')
    from v3_before, jsonb_array_elements(content->'tasks')),
  'future planning changes preserve all task progress');
select is((select jsonb_agg(jsonb_build_array(id, state, evidence, waiver_reason, decided_at)
  order by id) from public.gates),
  (select jsonb_agg(jsonb_build_array(value->'id', value->'state', value->'evidence',
    value->'waiver_reason', value->'decided_at') order by value->>'id')
    from v3_before, jsonb_array_elements(content->'gates')),
  'future planning changes preserve all gate decisions');
select is((pg_temp.v3_snapshot())->'owners', (select content->'owners' from v3_before),
  'private ownership is preserved');
select is((select count(*) from public.week_sources where source_id = 'source-plan-v3'),
  11::bigint, 'each future week links the final v3 plan');
select is((select count(*) from public.week_sources where source_id = 'source-benchmark-v2'),
  1::bigint, 'v2 remains linked only as historical evidence');
select matches((select purpose from public.sources where id = 'source-benchmark-v2'),
  '^Historical 26-configuration v2 benchmark', 'the preserved v2 source is explicitly historical');
select is((select count(*) from public.activity_log),
  :audit_count::bigint + (select count(*) from v3_edits),
  'each of the 126 declared mutations adds exactly one audit event');
select is((select jsonb_agg(to_jsonb(a) order by id) from public.activity_log a
  where id in (select (value->>'id')::bigint from v3_before,
    jsonb_array_elements(content->'activity'))),
  (select content->'activity' from v3_before), 'preexisting audit history is preserved');

create temporary table v3_after as select pg_temp.v3_snapshot() as content;
select lives_ok('select pg_temp.apply_v3()', 'an exact migration replay is accepted');
select is(pg_temp.v3_snapshot(), (select content from v3_after),
  'exact replay preserves every row, version and audit event');

-- Exercise conflicts at the end of the edit list, after earlier writes occurred.
select pg_temp.seed_v3_predecessor();
update public.week_sources set purpose = purpose
where week_id = 'week-14' and source_id = 'source-benchmark-v2';
create temporary table v3_version_conflict as select pg_temp.v3_snapshot() as content;
select throws_ok('select pg_temp.apply_v3()', '40001',
  'week-14:source-benchmark-v2 changed; refusing to overwrite live progress',
  'a changed version alone rejects the migration');
select is(pg_temp.v3_snapshot(), (select content from v3_version_conflict),
  'a late version conflict rolls back content, inserted sources and audit events');

select pg_temp.seed_v3_predecessor();
-- Reinsert this row with unchanged version to test the independent content guard.
delete from public.week_sources where week_id = 'week-14' and source_id = 'source-benchmark-v2';
insert into public.week_sources (project_id, week_id, source_id, purpose, priority, version)
select edit->'before'->>'project_id', edit->'before'->>'week_id',
  edit->'before'->>'source_id', 'Concurrent researcher content',
  edit->'before'->>'priority', (edit->'before'->>'version')::integer
from v3_edits where edit->>'id' = 'week-14:source-benchmark-v2';
create temporary table v3_content_conflict as select pg_temp.v3_snapshot() as content;
select throws_ok('select pg_temp.apply_v3()', '40001',
  'week-14:source-benchmark-v2 changed; refusing to overwrite live progress',
  'changed predecessor content rejects migration even at the expected version');
select is(pg_temp.v3_snapshot(), (select content from v3_content_conflict),
  'a late content conflict preserves the researcher edit and rolls back all other writes');

select pg_temp.seed_v3_predecessor();
update public.weeks set state = 'closed' where id = 'week-03';
update public.tasks set state = 'done' where week_id = 'week-04';
update public.gates set state = 'met', evidence = 'Test fixture completion' where week_id = 'week-04';
update public.weeks set state = 'closed' where id = 'week-04';
create temporary table v3_closed_conflict as select pg_temp.v3_snapshot() as content;
select throws_ok('select pg_temp.apply_v3()', '40001',
  'week-04 is missing or closed; an audited reopen is required',
  'a closed affected future week requires explicit audited reopening');
select is(pg_temp.v3_snapshot(), (select content from v3_closed_conflict),
  'closed-week rejection preserves the complete plan, ownership and audit history');

select * from finish();
rollback;
