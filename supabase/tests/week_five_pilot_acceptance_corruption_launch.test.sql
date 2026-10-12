\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(15);

create temporary table week_five_pilot_acceptance_corruption_launch_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20261012162733'
));
create function pg_temp.apply_week_five_pilot_acceptance_corruption_launch() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20261012162733');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_week_five_pilot_acceptance_corruption_launch()', 'empty databases defer to the current seed');

create function pg_temp.seed_week_five_pilot_acceptance_corruption_launch() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text; n integer;
begin
  truncate public.projects cascade;
  insert into public.projects (id,slug,title,research_question,start_date,end_date)
    values ('pose-embed','pose-embed','Preserved project','Preserved question','2026-09-15','2026-12-18');
  for n in 1..4 loop
    insert into public.weeks (id,project_id,number,start_date,end_date,phase,title,objective,deliverable,planned_minutes,state,closed_at,reflection)
      values ('week-' || lpad(n::text,2,'0'),'pose-embed',n,'2026-09-15','2026-10-11','Historical','Historical week','Objective','Deliverable',480,'closed',now(),'Preserved history');
  end loop;
  for edit in select e.edit from week_five_pilot_acceptance_corruption_launch_edits e where e.edit->>'operation'='update'
  loop
    select string_agg(format('%I', key), ', ' order by key), string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table',columns_sql,values_sql,edit->>'table') using edit->'before';
  end loop;
  insert into public.gates (id,project_id,week_id,position,criterion,state)
    values ('w05-test-gate','pose-embed','week-05',1,'Measured evidence','pending');
end;
$$;
create function pg_temp.progress_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'projects',(select jsonb_agg(to_jsonb(t) order by id) from public.projects t),
    'weeks',(select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks',(select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates',(select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'sources',(select jsonb_agg(to_jsonb(t) order by id) from public.sources t),
    'links',(select jsonb_agg(to_jsonb(t) order by week_id,source_id) from public.week_sources t),
    'activity',(select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t));
$$;
select pg_temp.seed_week_five_pilot_acceptance_corruption_launch();
create temporary table before_progress as select pg_temp.progress_snapshot() as content;
select lives_ok('select pg_temp.apply_week_five_pilot_acceptance_corruption_launch()', 'progress and public evidence apply atomically');
select is((select jsonb_build_array(state,version,actual_minutes,closed_at) from public.weeks where id='week-05'),
  '["active",21,0,null]'::jsonb, 'Week 5 remains active with unreported time and no closure');
select is((select jsonb_build_array(state,version,completed_at) from public.tasks where id='w05-task-02'),
  '["in_progress",18,null]'::jsonb, 'accepted pilot validation leaves the complete Week 5 task in progress');
select is((select to_jsonb(w) from public.weeks w where id='week-04'),
  (select jsonb_path_query_first(content,'$.weeks[*] ? (@.id == "week-04")') from before_progress),
  'closed history remains unchanged');
select is((select state from public.gates where id='w05-test-gate'),'pending','scientific gate remains pending');
select ok((select reflection like '%Normal availability is 5 hours weekly, with up to 10 if necessary%' and reflection like '%no guaranteed Thanksgiving hours%' from public.weeks where id='week-05'),
  'confirmed availability is distinguished from hours worked');
select ok((select completion_note like '%Compatible-runtime retry 8035829 passed full independent three-pilot validation%' and completion_note like '%separate preserved post-failure seal check passed%' and completion_note like '%Failed attempt 8028119 and independent-validator 8035576 remain preserved%' from public.tasks where id='w05-task-02'),'diagnostic preserves failed attempts and independent validation requirements');
select ok((select reflection like '%researcher explicitly requested that actual time remain unreported%' from public.weeks where id='week-05'),
  'the researcher request preserves unreported actual time');
create temporary table after_progress as select pg_temp.progress_snapshot() as content;
select lives_ok('select pg_temp.apply_week_five_pilot_acceptance_corruption_launch()', 'exact retry succeeds');
select is(pg_temp.progress_snapshot(),(select content from after_progress),'retry is side-effect free');

select pg_temp.seed_week_five_pilot_acceptance_corruption_launch();
update public.weeks set reflection='Concurrent researcher note' where id='week-05';
create temporary table conflicting_progress as select pg_temp.progress_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five_pilot_acceptance_corruption_launch()','40001',
  'week-05 changed; refusing to overwrite live progress','concurrent notes block overwrite');
select is(pg_temp.progress_snapshot(),(select content from conflicting_progress),'conflict rolls back publication');

select pg_temp.seed_week_five_pilot_acceptance_corruption_launch();
update public.tasks set state='done',completion_note='Separate verified completion' where week_id='week-05';
update public.gates set state='met',evidence='Separate verified completion' where week_id='week-05';
update public.weeks set state='closed' where id='week-05';
create temporary table closed_progress as select pg_temp.progress_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five_pilot_acceptance_corruption_launch()','40001',
  'week-05 is missing or closed; an audited reopen is required','closed week requires audited reopen before task/source editing');
select is(pg_temp.progress_snapshot(),(select content from closed_progress),'closed-week rejection preserves all history');
select * from finish();
rollback;
