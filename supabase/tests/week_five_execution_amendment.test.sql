\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(18);

create temporary table week_five_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20261011205818'
));
create function pg_temp.apply_week_five() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20261011205818');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_week_five()', 'empty databases defer to the current seed');

create function pg_temp.seed_week_five() returns void language plpgsql as $$
declare row_data jsonb; edit jsonb; n integer; columns_sql text; values_sql text;
begin
  truncate public.projects cascade;
  insert into public.projects (id, slug, title, research_question, start_date, end_date)
  values ('pose-embed','pose-embed','Preserved project','Preserved question','2026-09-15','2026-12-18');
  for n in 1..14 loop
    select e.edit->'before' into row_data from week_five_edits e
      where e.edit->>'table'='weeks' and e.edit->>'id'='week-' || lpad(n::text,2,'0');
    if row_data is null then
      insert into public.weeks (id,project_id,number,start_date,end_date,phase,title,objective,deliverable,planned_minutes)
      values ('week-' || lpad(n::text,2,'0'),'pose-embed',n,'2026-09-15','2026-12-18',
        'Preserved phase','Preserved title','Preserved objective','Preserved deliverable',480);
    else
      select string_agg(format('%I', key), ', ' order by key), string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, values_sql from jsonb_object_keys(row_data) key;
      execute format('insert into public.weeks (%s) select %s from jsonb_populate_record(null::public.weeks, $1) v',
        columns_sql,values_sql) using row_data;
    end if;
  end loop;
  insert into public.tasks (id,project_id,week_id,position,title,state,completion_note)
    values ('historical-task','pose-embed','week-04',1,'Historical task','done','Preserved historical evidence');
  for n in 1..4 loop
    update public.weeks set state='closed',reflection='Preserved closed reflection' where id='week-' || lpad(n::text,2,'0');
  end loop;
  for edit in select e.edit from week_five_edits e
    where e.edit->>'operation'='update' and e.edit->>'table'<>'weeks'
  loop
    select string_agg(format('%I', key), ', ' order by key), string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table',columns_sql,values_sql,edit->>'table') using edit->'before';
  end loop;
  insert into public.sources (id,project_id,title,authors,year,canonical_url,purpose,verified_at)
    values ('historical-source','pose-embed','Preserved source','Author',2020,'https://example.com/source','Historical evidence','2026-09-15');
end;
$$;
create function pg_temp.week_five_snapshot() returns jsonb language sql as $$
  select jsonb_build_object(
    'projects',(select jsonb_agg(to_jsonb(t) order by id) from public.projects t),
    'weeks',(select jsonb_agg(to_jsonb(t) order by id) from public.weeks t),
    'tasks',(select jsonb_agg(to_jsonb(t) order by id) from public.tasks t),
    'gates',(select jsonb_agg(to_jsonb(t) order by id) from public.gates t),
    'sources',(select jsonb_agg(to_jsonb(t) order by id) from public.sources t),
    'links',(select jsonb_agg(to_jsonb(t) order by week_id,source_id) from public.week_sources t),
    'activity',(select jsonb_agg(to_jsonb(t) order by id) from public.activity_log t));
$$;
select pg_temp.seed_week_five();
create temporary table before_week_five as select pg_temp.week_five_snapshot() as content;
select lives_ok('select pg_temp.apply_week_five()', 'adopted amendment and initial progress apply atomically');
select is((select jsonb_build_array(state,version,actual_minutes) from public.weeks where id='week-05'),
  '["active",4,0]'::jsonb, 'Week 5 starts without fabricating time');
select is((select jsonb_build_array(state,version,completed_at) from public.tasks where id='w05-task-03'),
  '["in_progress",5,null]'::jsonb, 'implementation starts without claiming completion');
select ok((select bool_and(state='pending' and decided_at is null) from public.gates), 'no scientific gate passes');
select is((select count(*) from public.sources where id<>'historical-source'),3::bigint,'three adopted sources are added');
select is((select count(*) from public.week_sources),6::bigint,'six open-week source links are added');
select is((select jsonb_agg(to_jsonb(w) order by id) from public.weeks w where number<=4),
  (select jsonb_path_query_array(content,'$.weeks[*] ? (@.number <= 4)') from before_week_five),
  'closed weeks and recorded time remain byte-for-byte unchanged');
select is((select to_jsonb(t) from public.tasks t where id='historical-task'),
  (select jsonb_path_query_first(content,'$.tasks[*] ? (@.id == "historical-task")') from before_week_five),
  'historical task evidence remains unchanged');
select is((select count(*) from public.activity_log),
  (select jsonb_array_length(content->'activity')::bigint+28 from before_week_five), 'exactly the 28 intended changes are audited');
create temporary table after_week_five as select pg_temp.week_five_snapshot() as content;
select lives_ok('select pg_temp.apply_week_five()', 'an exact retry succeeds');
select is(pg_temp.week_five_snapshot(),(select content from after_week_five),'exact retry has no side effects');

select pg_temp.seed_week_five();
update public.tasks set completion_note='Concurrent researcher evidence' where id='w05-task-03';
create temporary table conflicting_week_five as select pg_temp.week_five_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five()','40001',
  'w05-task-03 changed; refusing to overwrite live progress','concurrent evidence blocks publication');
select is(pg_temp.week_five_snapshot(),(select content from conflicting_week_five),'conflict rolls back every earlier update');

select pg_temp.seed_week_five();
update public.tasks set state='done',completion_note='Separate completion' where week_id='week-05';
update public.gates set state='met',evidence='Separate completion' where week_id='week-05';
update public.weeks set state='closed' where id='week-05';
create temporary table closed_week_five as select pg_temp.week_five_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five()','40001',
  'week-05 is missing or closed; an audited reopen is required','closed future weeks require an audited reopen');
select is(pg_temp.week_five_snapshot(),(select content from closed_week_five),'closed-week rejection has no side effects');

select pg_temp.seed_week_five();
update public.weeks set state='active',reopen_reason='Test unresolved prior week' where id='week-04';
create temporary table prerequisite_week_five as select pg_temp.week_five_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five()','40001',
  'Week 4 must be closed before starting Week 5','unresolved prior week blocks progress');
select is(pg_temp.week_five_snapshot(),(select content from prerequisite_week_five),'prerequisite rejection has no side effects');
select * from finish();
rollback;
