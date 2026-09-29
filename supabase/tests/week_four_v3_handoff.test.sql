\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(14);

create temporary table handoff_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20260929223500'
));
create function pg_temp.apply_handoff() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20260929223500');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_handoff()', 'empty databases defer to the v3 seed');

create function pg_temp.seed_handoff() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  insert into public.projects (id, slug, title, research_question, start_date, end_date)
  values ('pose-embed', 'pose-embed', 'Preserved project', 'Preserved question',
    '2026-09-15', '2026-12-18');
  insert into public.weeks (id, project_id, number, start_date, end_date, phase,
    title, objective, deliverable, reflection, planned_minutes, actual_minutes, version)
  select 'week-0' || n, 'pose-embed', n, '2026-09-29', '2026-10-11',
    'Preserved phase', 'Preserved week', 'Preserved objective',
    'Preserved deliverable', 'Preserved reflection', 480, 0, 3 from unnest(array[1,2,3,4]) n;
  update public.weeks set state='closed' where id='week-01';
  update public.weeks set state='closed' where id='week-02';
  update public.weeks set state='closed' where id='week-03';
  for edit in select e.edit from handoff_edits e
  loop
    select string_agg(format('%I', key), ', ' order by key),
      string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table', columns_sql, values_sql, edit->>'table') using edit->'before';
  end loop;
  insert into public.tasks (id, project_id, week_id, position, title, state)
  values ('w04-task-02','pose-embed','week-04',2,'Remaining Week 4 work','todo');
  insert into public.gates (id, project_id, week_id, position, criterion, state)
  values ('w04-gate-02','pose-embed','week-04',2,'Remaining Week 4 gate','pending');
end;
$$;
create function pg_temp.handoff_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'weeks', (select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates', (select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'activity', (select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t)
  );
$$;
select pg_temp.seed_handoff();
create temporary table before_handoff as select pg_temp.handoff_snapshot() as content;
select count(*) as audit_count from public.activity_log \gset
select lives_ok('select pg_temp.apply_handoff()', 'verified Week 3 freeze satisfies the duplicate prerequisite');
select is((select state from public.tasks where id='w04-task-01'), 'done', 'design task is done');
select is((select state from public.gates where id='w04-gate-01'), 'met', 'design gate is met');
select is(pg_temp.handoff_snapshot()->'weeks', (select content->'weeks' from before_handoff),
  'Week 3 closure, Week 4 planned state, time and versions are unchanged');
select is(
  jsonb_build_array((select to_jsonb(t) from public.tasks t where id='w04-task-02'),
    (select to_jsonb(g) from public.gates g where id='w04-gate-02')),
  (select jsonb_build_array(content->'tasks'->1, content->'gates'->1) from before_handoff),
  'remaining Week 4 work stays unchanged');
select is((select count(*) from public.activity_log), :audit_count::bigint+2, 'both changes are audited');
create temporary table after_handoff as select pg_temp.handoff_snapshot() as content;
select lives_ok('select pg_temp.apply_handoff()', 'an identical retry succeeds');
select is(pg_temp.handoff_snapshot(), (select content from after_handoff), 'retry has no side effects');

select pg_temp.seed_handoff();
update public.gates set evidence='Concurrent researcher evidence' where id='w04-gate-01';
create temporary table concurrent_handoff as select pg_temp.handoff_snapshot() as content;
select throws_ok('select pg_temp.apply_handoff()', '40001',
  'w04-gate-01 changed or Week 4 is closed; refusing to overwrite progress', 'concurrent evidence is protected');
select is(pg_temp.handoff_snapshot(), (select content from concurrent_handoff), 'conflict rolls back the task update');

select pg_temp.seed_handoff();
update public.weeks set state='active', reopen_reason='Test predecessor gate' where id='week-03';
select throws_ok('select pg_temp.apply_handoff()', '40001',
  'Week 3 must be closed before this handoff', 'Week 3 closure is required');

select pg_temp.seed_handoff();
update public.tasks set state='done', completion_note='Separate closeout evidence' where week_id='week-04';
update public.gates set state='met', evidence='Separate closeout evidence' where week_id='week-04';
update public.weeks set state='closed' where id='week-04';
create temporary table closed_handoff as select pg_temp.handoff_snapshot() as content;
select throws_ok('select pg_temp.apply_handoff()', '40001',
  'w04-task-01 changed or Week 4 is closed; refusing to overwrite progress', 'closed Week 4 evidence is protected');
select is(pg_temp.handoff_snapshot(), (select content from closed_handoff), 'closed records remain unchanged');
select * from finish();
rollback;
