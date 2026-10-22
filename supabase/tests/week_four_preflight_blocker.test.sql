\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(20);

create temporary table preflight_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20261008190007'
));
create function pg_temp.apply_preflight() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20261008190007');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_preflight()', 'empty databases defer to the v3 seed');

create function pg_temp.seed_preflight() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  insert into public.projects (id, slug, title, research_question, start_date, end_date)
  values ('pose-embed', 'pose-embed', 'Preserved project', 'Preserved question',
    '2026-09-15', '2026-12-18');
  insert into public.weeks (id, project_id, number, start_date, end_date, phase,
    title, objective, deliverable, reflection, planned_minutes, actual_minutes, version)
  select 'week-0' || n, 'pose-embed', n, '2026-09-15', '2026-10-04',
    'Preserved phase', 'Preserved week', 'Preserved objective',
    'Preserved deliverable', 'Preserved reflection', 480, 0, 3 from unnest(array[1,2,3]) n;
  update public.weeks set state='closed' where id='week-01';
  update public.weeks set state='closed' where id='week-02';
  update public.weeks set state='closed' where id='week-03';
  for edit in select e.edit from preflight_edits e order by e.edit->>'table' = 'weeks' desc
  loop
    select string_agg(format('%I', key), ', ' order by key),
      string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table', columns_sql, values_sql, edit->>'table') using edit->'before';
  end loop;
  insert into public.gates (id, project_id, week_id, position, criterion, state)
  values ('w04-gate-02','pose-embed','week-04',2,'Independent fixture gate','pending'),
    ('w04-gate-03','pose-embed','week-04',3,'Fresh cache and pilot gate','pending');
end;
$$;
create function pg_temp.preflight_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'weeks', (select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates', (select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'activity', (select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t)
  );
$$;
select pg_temp.seed_preflight();
create temporary table before_preflight as select pg_temp.preflight_snapshot() as content;
select count(*) as audit_count from public.activity_log \gset
select lives_ok('select pg_temp.apply_preflight()', 'unresolved registered roots block fresh execution');
select is((select jsonb_build_array(state, version, closed_at, actual_minutes) from public.weeks where id='week-04'),
  '["blocked",4,null,0]'::jsonb, 'Week 4 is blocked and remains open with unreported time');
select is((select jsonb_agg(state order by position) from public.tasks where week_id='week-04'),
  '["blocked","in_progress","blocked","blocked"]'::jsonb, 'only independent fixture work remains in progress');
select ok((select bool_and(completed_at is null) from public.tasks where week_id='week-04'),
  'blocked and in-progress tasks have no current completion timestamps');
select is((select jsonb_build_array(state, decided_at, version) from public.gates where id='w04-gate-01'),
  '["pending",null,5]'::jsonb, 'the design gate requires current seal revalidation');
select ok((select bool_and(case when edit->>'table'='tasks' then
    (select completion_note from public.tasks where id=edit->>'id') like (edit->'before'->>'completion_note') || '%'
  else (select evidence from public.gates where id=edit->>'id') like (edit->'before'->>'evidence') || '%' end)
  from preflight_edits where edit->>'id' in ('w04-task-01','w04-gate-01')),
  'September 29 task and gate evidence remain verbatim prefixes');
select is((select jsonb_agg(to_jsonb(w) order by id) from public.weeks w where number<4),
  (select jsonb_path_query_array(content, '$.weeks[*] ? (@.number < 4)') from before_preflight),
  'all previous weeks remain unchanged');
select is((select jsonb_agg(to_jsonb(g) order by id) from public.gates g where id in ('w04-gate-02','w04-gate-03')),
  (select jsonb_path_query_array(content, '$.gates[*] ? (@.position > 1)') from before_preflight),
  'remaining gates remain pending and unchanged');
select is((select count(*) from public.activity_log), :audit_count::bigint+6, 'all six updates are automatically audited');
select ok((select bool_and(actor_id is null) from public.activity_log), 'administrative audit events permit a null actor');
create temporary table after_preflight as select pg_temp.preflight_snapshot() as content;
select lives_ok('select pg_temp.apply_preflight()', 'an identical retry succeeds');
select is(pg_temp.preflight_snapshot(), (select content from after_preflight), 'retry has no side effects');
select throws_ok($$update public.weeks set state='closed' where id='week-04'$$, '23514',
  'all required tasks must be done before closing a week', 'the blocked week cannot close');

select pg_temp.seed_preflight();
update public.gates set evidence='Concurrent researcher evidence' where id='w04-gate-01';
create temporary table concurrent_preflight as select pg_temp.preflight_snapshot() as content;
select throws_ok('select pg_temp.apply_preflight()', '40001',
  'w04-gate-01 changed or Week 4 is closed; refusing to overwrite progress', 'concurrent evidence is protected');
select is(pg_temp.preflight_snapshot(), (select content from concurrent_preflight), 'conflict rolls back all preceding task updates');

select pg_temp.seed_preflight();
update public.weeks set state='active', reopen_reason='Test predecessor gate' where id='week-03';
select throws_ok('select pg_temp.apply_preflight()', '40001',
  'Week 3 must be closed before this preflight update', 'the predecessor must remain closed');

select pg_temp.seed_preflight();
update public.tasks set state='done', completion_note='Separate closeout evidence' where week_id='week-04';
update public.gates set state='met', evidence='Separate closeout evidence' where week_id='week-04';
update public.weeks set state='closed' where id='week-04';
create temporary table closed_preflight as select pg_temp.preflight_snapshot() as content;
select throws_ok('select pg_temp.apply_preflight()', '40001',
  'w04-task-01 changed or Week 4 is closed; refusing to overwrite progress', 'closed Week 4 evidence is protected');
select is(pg_temp.preflight_snapshot(), (select content from closed_preflight), 'closed records remain unchanged');
select ok((select bool_and(actual_minutes=0) from public.weeks), 'no researcher hours are invented');
select * from finish();
rollback;
