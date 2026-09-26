\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(12);

create temporary table benchmark_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20260924223631'
));

-- Reconstruct the captured public predecessor without ownership or activity data.
create function pg_temp.seed_benchmark_predecessor() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text;
begin
  for edit in select e.edit from benchmark_edits e where e.edit->'before' <> 'null'::jsonb
  loop
    select string_agg(format('%I', key), ', ' order by key),
           string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table', columns_sql, values_sql, edit->>'table') using edit->'before';
  end loop;
end;
$$;
select pg_temp.seed_benchmark_predecessor();

create temporary table original_completed as
select id, state, completion_note, completed_at from public.tasks where state = 'done';
create temporary table original_bu as select to_jsonb(g) as row from public.gates g where id = 'w01-gate-04';
select unnest(statements) from supabase_migrations.schema_migrations where version = '20260924223631'
\gexec
select is((select title from public.projects where id = 'pose-embed'),
  'Metric learning for human-motion retrieval', 'project adopts the full motion comparison');
select is((select count(*) from public.tasks where state = 'done'), 9::bigint,
  'only eight historical tasks plus verified local metric software are complete');
select is((select count(*) from original_completed o join public.tasks t using (id)
  where (t.state, t.completion_note, t.completed_at) = (o.state, o.completion_note, o.completed_at)),
  8::bigint, 'all existing completed evidence is preserved');
select is((select to_jsonb(g) from public.gates g where id = 'w01-gate-04'),
  (select row from original_bu), 'confirmed BU determination remains unchanged');
select is((select actual_minutes from public.weeks where id = 'week-01'), 0,
  'no researcher hours are invented');
select is((select state from public.weeks where id = 'week-03'), 'planned',
  'Week 3 respects predecessor closure rather than importing blocked state');
select is((select state from public.gates where id = 'w03-gate-05'), 'pending',
  'v2 metrics do not inherit the historical one-shot completion');
select is((select count(*) from public.weeks where state = 'closed'), 0::bigint,
  'no week is implicitly closed');

create temporary table migrated_rows as select jsonb_agg(to_jsonb(t) order by id) as rows from public.tasks t;
select count(*) as audit_count from public.activity_log \gset
select unnest(statements) from supabase_migrations.schema_migrations where version = '20260924223631'
\gexec
select is((select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
  (select rows from migrated_rows), 'exact replay preserves task rows and versions');
select is((select count(*) from public.activity_log), :audit_count::bigint,
  'exact replay creates no audit events');

-- A normal concurrent edit increments version and must make the replay fail.
update public.tasks set completion_note = 'Concurrent researcher note' where id = 'w01-task-05';
select throws_ok((select array_to_string(statements, E'\n') from supabase_migrations.schema_migrations
  where version = '20260924223631'), '40001',
  'w01-task-05 changed; refusing to overwrite live progress', 'concurrent progress aborts migration');

-- A closed affected parent is rejected before any content can change.
-- Use a temporary predecessor reset within this rolled-back test transaction.
delete from public.week_sources;
delete from public.sources;
delete from public.tasks;
delete from public.gates;
delete from public.weeks;
delete from public.projects;
select pg_temp.seed_benchmark_predecessor();
update public.tasks set state = 'done' where week_id in ('week-01','week-02','week-03');
update public.gates set state = 'met', evidence = 'Test fixture completion' where week_id in ('week-01','week-02','week-03');
update public.weeks set state = 'closed' where id = 'week-01';
update public.weeks set state = 'closed' where id = 'week-02';
update public.weeks set state = 'closed' where id = 'week-03';
select throws_ok((select array_to_string(statements, E'\n') from supabase_migrations.schema_migrations
  where version = '20260924223631'), '40001',
  'week-03 is missing or closed; an audited reopen is required', 'closed-week plan edits require an audited reopen');
select * from finish();
rollback;
