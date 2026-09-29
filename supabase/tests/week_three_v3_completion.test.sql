\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(18);

create temporary table completion_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20260929213127'
));
create function pg_temp.apply_completion() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20260929213127');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_completion()', 'empty databases defer to the v3 seed');

create function pg_temp.seed_completion() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  insert into public.projects (id, slug, title, research_question, start_date, end_date)
  values ('pose-embed', 'pose-embed', 'Preserved project', 'Preserved question',
    '2026-09-15', '2026-12-18');
  insert into public.weeks (id, project_id, number, start_date, end_date, phase,
    title, objective, deliverable, reflection, planned_minutes, actual_minutes)
  select 'week-0' || n, 'pose-embed', n, '2026-09-15', '2026-10-11',
    'Preserved phase', 'Preserved week', 'Preserved objective',
    'Preserved deliverable', 'Preserved reflection', 480, 137 from unnest(array[1, 2, 4]) n;
  update public.weeks set state = 'closed' where id in ('week-01', 'week-02');
  for edit in select e.edit from completion_edits e
    order by case when e.edit->>'table' = 'weeks' then 0 else 1 end
  loop
    select string_agg(format('%I', key), ', ' order by key),
      string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table', columns_sql, values_sql, edit->>'table') using edit->'before';
  end loop;
  insert into public.tasks (id, project_id, week_id, position, title, state, completion_note)
  select 'w03-task-0' || n, 'pose-embed', 'week-03', n,
    'Historical task ' || n, 'done', 'Preserved task evidence ' || n from generate_series(1,6) n;
  insert into public.gates (id, project_id, week_id, position, criterion, state, evidence)
  select 'w03-gate-0' || n, 'pose-embed', 'week-03', n,
    'Historical gate ' || n, 'met', 'Preserved gate evidence ' || n from generate_series(1,6) n;
end;
$$;
create function pg_temp.completion_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'projects', (select jsonb_agg(to_jsonb(t) order by id) from public.projects t),
    'weeks', (select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates', (select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'activity', (select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t)
  );
$$;
select pg_temp.seed_completion();
create temporary table before_completion as select pg_temp.completion_snapshot() as content;
select count(*) as audit_count from public.activity_log \gset
select lives_ok('select pg_temp.apply_completion()', 'verified SCC preparation closes Week 3');
select is((select state from public.weeks where id='week-03'), 'closed', 'Week 3 closes');
select is((select version from public.weeks where id='week-03'), 8, 'week version advances once');
select is((select actual_minutes from public.weeks where id='week-03'),
  (select (edit->'before'->>'actual_minutes')::integer from completion_edits where edit->>'table'='weeks'),
  'unreported researcher time is preserved without invention');
select is((select state from public.tasks where id='w03-task-07'), 'done', 'preparation task is done');
select is((select state from public.gates where id='w03-gate-07'), 'met', 'design freeze gate is met');
select is((select count(*) from public.activity_log), :audit_count::bigint+3, 'all three changes are audited');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where id<>'w03-task-07'),
  (select jsonb_agg(value order by value->>'id') from before_completion,
    jsonb_array_elements(content->'tasks') where value->>'id'<>'w03-task-07'), 'earlier task evidence is unchanged');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.gates t where id<>'w03-gate-07'),
  (select jsonb_agg(value order by value->>'id') from before_completion,
    jsonb_array_elements(content->'gates') where value->>'id'<>'w03-gate-07'), 'earlier gate evidence is unchanged');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.weeks t where id<>'week-03'),
  (select jsonb_agg(value order by value->>'id') from before_completion,
    jsonb_array_elements(content->'weeks') where value->>'id'<>'week-03'), 'other weeks are unchanged');
create temporary table after_completion as select pg_temp.completion_snapshot() as content;
select lives_ok('select pg_temp.apply_completion()', 'an identical retry is safe after closure');
select is(pg_temp.completion_snapshot(), (select content from after_completion), 'retry changes no rows or audit events');

select pg_temp.seed_completion();
update public.weeks set reflection='Concurrent researcher progress' where id='week-03';
create temporary table concurrent_completion as select pg_temp.completion_snapshot() as content;
select throws_ok('select pg_temp.apply_completion()', '40001',
  'week-03 changed or Week 3 is closed; refusing to overwrite progress', 'concurrent week content is rejected');
select is(pg_temp.completion_snapshot(), (select content from concurrent_completion), 'conflict rolls back both child updates');

select pg_temp.seed_completion();
update public.gates set state='pending' where id='w03-gate-01';
select throws_ok('select pg_temp.apply_completion()', '23514',
  'all required gates must be met or waived before closing a week', 'an unresolved historical gate prevents closure');

select pg_temp.seed_completion();
update public.tasks set state='done' where id='w03-task-07';
update public.gates set state='met' where id='w03-gate-07';
update public.weeks set state='closed' where id='week-03';
create temporary table closed_completion as select pg_temp.completion_snapshot() as content;
select throws_ok('select pg_temp.apply_completion()', '40001',
  'w03-task-07 changed or Week 3 is closed; refusing to overwrite progress', 'a different closed record is never rewritten');
select is(pg_temp.completion_snapshot(), (select content from closed_completion), 'closed-week conflict preserves all rows');
select * from finish();
rollback;
