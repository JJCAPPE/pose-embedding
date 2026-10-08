\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(20);

create temporary table week_four_completion_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20261008222524'
));
create function pg_temp.apply_week_four_completion() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20261008222524');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_week_four_completion()', 'empty databases defer to the v3 seed');

create function pg_temp.seed_week_four_completion() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  insert into public.projects (id, slug, title, research_question, start_date, end_date)
  values ('pose-embed', 'pose-embed', 'Preserved project', 'Preserved question', '2026-09-15', '2026-12-18');
  insert into public.weeks (id, project_id, number, start_date, end_date, phase, title, objective, deliverable, planned_minutes)
  select 'week-0' || n, 'pose-embed', n, '2026-09-15', '2026-10-04', 'Preserved phase',
    'Preserved week', 'Preserved objective', 'Preserved deliverable', 480 from unnest(array[1,2,3,5]) n;
  update public.weeks set state='closed' where id='week-01';
  update public.weeks set state='closed' where id='week-02';
  update public.weeks set state='closed' where id='week-03';
  for edit in select e.edit from week_four_completion_edits e order by e.edit->>'table' = 'weeks' desc
  loop
    select string_agg(format('%I', key), ', ' order by key), string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table', columns_sql, values_sql, edit->>'table') using edit->'before';
  end loop;
  insert into public.tasks (id,project_id,week_id,position,title,state)
  select 'w04-task-0' || n,'pose-embed','week-04',n,'Verified prerequisite','done' from unnest(array[1,2,3]) n;
  insert into public.gates (id,project_id,week_id,position,criterion,state,evidence)
  select 'w04-gate-0' || n,'pose-embed','week-04',n,'Verified prerequisite','met','Prior verified evidence'
  from unnest(array[1,2]) n;
  insert into public.tasks (id,project_id,week_id,position,title,state)
  values ('w05-task-01','pose-embed','week-05',1,'Unstarted next-week task','todo');
end;
$$;
create function pg_temp.week_four_completion_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'weeks', (select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks', (select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates', (select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'activity', (select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t)
  );
$$;
select pg_temp.seed_week_four_completion();
create temporary table before_week_four_completion as select pg_temp.week_four_completion_snapshot() as content;
select count(*) as audit_count from public.activity_log \gset
select lives_ok('select pg_temp.apply_week_four_completion()', 'verified pilots complete the final task, gate and week atomically');
select is((select jsonb_build_array(state,version,completed_at is not null) from public.tasks where id='w04-task-04'),
  '["done",8,true]'::jsonb, 'the final pilot task is complete and timestamped');
select is((select jsonb_build_array(state,version,decided_at is not null) from public.gates where id='w04-gate-03'),
  '["met",4,true]'::jsonb, 'the final gate is met and timestamped');
select is((select jsonb_build_array(state,version,closed_at is not null,actual_minutes) from public.weeks where id='week-04'),
  '["closed",10,true,0]'::jsonb, 'Week 4 closes without inventing researcher time');
select ok((select bool_and(row_data @> (edit->'before' || edit->'values'
    || jsonb_build_object('version',(edit->'before'->>'version')::integer+1)))
  from week_four_completion_edits cross join lateral (
    select to_jsonb(t) as row_data from public.tasks t where edit->>'table'='tasks' and t.id=edit->>'id'
    union all select to_jsonb(g) from public.gates g where edit->>'table'='gates' and g.id=edit->>'id'
    union all select to_jsonb(w) from public.weeks w where edit->>'table'='weeks' and w.id=edit->>'id'
  ) changed), 'all intended evidence and timestamps match the reviewed values');
select is((select count(*) from public.activity_log), :audit_count::bigint+3, 'only the three intended updates are audited');
select is(jsonb_build_object(
    'weeks',(select jsonb_agg(to_jsonb(w) order by id) from public.weeks w where id<>'week-04'),
    'tasks',(select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where id<>'w04-task-04'),
    'gates',(select jsonb_agg(to_jsonb(g) order by id) from public.gates g where id<>'w04-gate-03')),
  (select jsonb_build_object(
    'weeks',jsonb_path_query_array(content,'$.weeks[*] ? (@.id != "week-04")'),
    'tasks',jsonb_path_query_array(content,'$.tasks[*] ? (@.id != "w04-task-04")'),
    'gates',jsonb_path_query_array(content,'$.gates[*] ? (@.id != "w04-gate-03")')) from before_week_four_completion),
  'other weeks, prior evidence and all next-week work remain unchanged');
create temporary table after_week_four_completion as select pg_temp.week_four_completion_snapshot() as content;
select lives_ok('select pg_temp.apply_week_four_completion()', 'an identical retry succeeds after closure');
select is(pg_temp.week_four_completion_snapshot(), (select content from after_week_four_completion), 'retry has no side effects');

select pg_temp.seed_week_four_completion();
update public.weeks set reflection='Concurrent researcher reflection' where id='week-04';
create temporary table concurrent_week_four_completion as select pg_temp.week_four_completion_snapshot() as content;
select throws_ok('select pg_temp.apply_week_four_completion()', '40001',
  'week-04 changed or Week 4 is closed; refusing to overwrite progress', 'concurrent reflection is protected');
select is(pg_temp.week_four_completion_snapshot(), (select content from concurrent_week_four_completion), 'week conflict rolls back the task and gate updates');

select pg_temp.seed_week_four_completion();
update public.tasks set completion_note='Concurrent pilot evidence' where id='w04-task-04';
create temporary table concurrent_task_completion as select pg_temp.week_four_completion_snapshot() as content;
select throws_ok('select pg_temp.apply_week_four_completion()', '40001',
  'w04-task-04 changed or Week 4 is closed; refusing to overwrite progress', 'concurrent pilot evidence is protected');
select is(pg_temp.week_four_completion_snapshot(), (select content from concurrent_task_completion), 'task conflict has no side effects');

select pg_temp.seed_week_four_completion();
update public.tasks set state='in_progress' where id='w04-task-03';
create temporary table incomplete_task_completion as select pg_temp.week_four_completion_snapshot() as content;
select throws_ok('select pg_temp.apply_week_four_completion()', '23514',
  'all required tasks must be done before closing a week', 'another incomplete required task blocks closure');
select is(pg_temp.week_four_completion_snapshot(), (select content from incomplete_task_completion), 'incomplete prerequisite rolls back the task and gate updates');

select pg_temp.seed_week_four_completion();
update public.gates set state='pending' where id='w04-gate-02';
create temporary table pending_gate_completion as select pg_temp.week_four_completion_snapshot() as content;
select throws_ok('select pg_temp.apply_week_four_completion()', '23514',
  'all required gates must be met or waived before closing a week', 'another pending required gate blocks closure');
select is(pg_temp.week_four_completion_snapshot(), (select content from pending_gate_completion), 'pending prerequisite rolls back the task and gate updates');

select pg_temp.seed_week_four_completion();
update public.tasks set state='done', completion_note='Separate closeout evidence' where id='w04-task-04';
update public.gates set state='met', evidence='Separate closeout evidence' where id='w04-gate-03';
update public.weeks set state='closed' where id='week-04';
create temporary table closed_week_four_completion as select pg_temp.week_four_completion_snapshot() as content;
select throws_ok('select pg_temp.apply_week_four_completion()', '40001',
  'w04-task-04 changed or Week 4 is closed; refusing to overwrite progress', 'a different closed Week 4 record is protected');
select is(pg_temp.week_four_completion_snapshot(), (select content from closed_week_four_completion), 'closed records remain unchanged');
select * from finish();
rollback;
