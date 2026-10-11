\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(13);

create temporary table pilot_progress_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20261008214009'
));
create function pg_temp.apply_pilot_progress() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20261008214009');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_pilot_progress()', 'empty databases defer to the v3 seed');

create function pg_temp.seed_pilot_progress() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  insert into public.projects (id, slug, title, research_question, start_date, end_date)
  values ('pose-embed', 'pose-embed', 'Preserved project', 'Preserved question', '2026-09-15', '2026-12-18');
  insert into public.weeks (id, project_id, number, start_date, end_date, phase, title, objective, deliverable, planned_minutes)
  select 'week-0' || n, 'pose-embed', n, '2026-09-15', '2026-10-04', 'Preserved phase',
    'Preserved week', 'Preserved objective', 'Preserved deliverable', 480 from unnest(array[1,2,3]) n;
  update public.weeks set state='closed' where id='week-01';
  update public.weeks set state='closed' where id='week-02';
  update public.weeks set state='closed' where id='week-03';
  for edit in select e.edit from pilot_progress_edits e order by e.edit->>'table' = 'weeks' desc
  loop
    select string_agg(format('%I', key), ', ' order by key), string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table', columns_sql, values_sql, edit->>'table') using edit->'before';
  end loop;
  insert into public.tasks (id,project_id,week_id,position,title,state)
  values ('w04-task-03','pose-embed','week-04',3,'Validated caches','done');
  insert into public.gates (id,project_id,week_id,position,criterion,state)
  values ('w04-gate-03','pose-embed','week-04',3,'Complete caches and pilots','pending');
end;
$$;
create function pg_temp.pilot_progress_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'weeks', (select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates', (select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'activity', (select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t)
  );
$$;
select pg_temp.seed_pilot_progress();
create temporary table before_pilot_progress as select pg_temp.pilot_progress_snapshot() as content;
select count(*) as audit_count from public.activity_log \gset
select lives_ok('select pg_temp.apply_pilot_progress()', 'two pilot completions are recorded without claiming independent validation');
select is((select jsonb_build_array(state,version,completed_at) from public.tasks where id='w04-task-04'),
  '["in_progress",7,null]'::jsonb, 'the three-pilot task remains incomplete');
select is((select jsonb_build_array(state,version,closed_at,actual_minutes) from public.weeks where id='week-04'),
  '["active",9,null,0]'::jsonb, 'Week 4 stays active with unchanged unreported time');
select is((select count(*) from public.activity_log), :audit_count::bigint+2, 'only the two intended rows are audited');
select is((select jsonb_agg(to_jsonb(w) order by id) from public.weeks w where number<4),
  (select jsonb_path_query_array(content, '$.weeks[*] ? (@.number < 4)') from before_pilot_progress),
  'previous weeks remain unchanged');
select is(jsonb_build_object('task', (select to_jsonb(t) from public.tasks t where id='w04-task-03'),
    'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)),
  (select jsonb_build_object('task', content->'tasks'->0, 'gates', content->'gates') from before_pilot_progress),
  'verified cache task and gates remain unchanged');
create temporary table after_pilot_progress as select pg_temp.pilot_progress_snapshot() as content;
select lives_ok('select pg_temp.apply_pilot_progress()', 'an identical retry succeeds');
select is(pg_temp.pilot_progress_snapshot(), (select content from after_pilot_progress), 'retry has no side effects');

select pg_temp.seed_pilot_progress();
update public.weeks set reflection='Concurrent researcher reflection' where id='week-04';
create temporary table concurrent_pilot_progress as select pg_temp.pilot_progress_snapshot() as content;
select throws_ok('select pg_temp.apply_pilot_progress()', '40001',
  'week-04 changed or Week 4 is closed; refusing to overwrite progress', 'concurrent reflection is protected');
select is(pg_temp.pilot_progress_snapshot(), (select content from concurrent_pilot_progress), 'conflict rolls back the task update');

select pg_temp.seed_pilot_progress();
update public.tasks set state='done', completion_note='Separate closeout evidence' where week_id='week-04';
update public.gates set state='met', evidence='Separate closeout evidence' where week_id='week-04';
update public.weeks set state='closed' where id='week-04';
create temporary table closed_pilot_progress as select pg_temp.pilot_progress_snapshot() as content;
select throws_ok('select pg_temp.apply_pilot_progress()', '40001',
  'w04-task-04 changed or Week 4 is closed; refusing to overwrite progress', 'closed Week 4 evidence is protected');
select is(pg_temp.pilot_progress_snapshot(), (select content from closed_pilot_progress), 'closed records remain unchanged');
select * from finish();
rollback;
