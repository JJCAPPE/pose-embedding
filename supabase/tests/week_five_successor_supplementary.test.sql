\set ON_ERROR_STOP on
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(27);

create temporary table week_five_successor_supplementary_edits as
select value as edit from jsonb_array_elements((
  select split_part(array_to_string(statements, E'\n'), '$edits$', 2)::jsonb
  from supabase_migrations.schema_migrations where version = '20261013204121'
));
create function pg_temp.apply_week_five_successor_supplementary() returns void language plpgsql as $$
begin
  execute (select array_to_string(statements, E'\n')
    from supabase_migrations.schema_migrations where version = '20261013204121');
end;
$$;
truncate public.projects cascade;
select lives_ok('select pg_temp.apply_week_five_successor_supplementary()', 'empty databases defer to the current seed');

create function pg_temp.seed_week_five_successor_supplementary() returns void language plpgsql as $$
declare edit jsonb; columns_sql text; values_sql text; n integer;
begin
  truncate public.projects cascade;
  insert into public.projects (id,slug,title,research_question,start_date,end_date)
    values ('pose-embed','pose-embed','Preserved project','Preserved question','2026-09-15','2026-12-18');
  for n in 1..14 loop
    if n=5 then continue; end if;
    insert into public.weeks (id,project_id,number,start_date,end_date,phase,title,objective,deliverable,planned_minutes,state,closed_at,reflection)
      values ('week-' || lpad(n::text,2,'0'),'pose-embed',n,'2026-09-15','2026-10-11','Historical','Historical week','Objective','Deliverable',480,case when n<=4 then 'closed' else 'planned' end,case when n<=4 then now() else null end,'Preserved history');
  end loop;
  for edit in select e.edit from week_five_successor_supplementary_edits e where e.edit->>'operation'='update'
  loop
    select string_agg(format('%I', key), ', ' order by key), string_agg(format('v.%I', key), ', ' order by key)
      into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
    execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
      edit->>'table',columns_sql,values_sql,edit->>'table') using edit->'before';
  end loop;
  insert into public.tasks (id,project_id,week_id,position,title,expected_output,state,completion_note,completed_at) values
    ('w05-task-01','pose-embed','week-05',1,'Preserved geometry','Verified evidence','done','Preserved geometry evidence','2026-10-12T18:31:21.614571Z'),
    ('w05-task-03','pose-embed','week-05',3,'Preserved rehearsal','Verified evidence','done','Preserved rehearsal evidence','2026-10-11T22:44:38Z');
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
select pg_temp.seed_week_five_successor_supplementary();
create temporary table before_progress as select pg_temp.progress_snapshot() as content;
select lives_ok('select pg_temp.apply_week_five_successor_supplementary()', 'progress and public evidence apply atomically');
select is((select jsonb_build_array(state,version,actual_minutes,closed_at) from public.weeks where id='week-05'),
  '["active",30,0,null]'::jsonb, 'Week 5 remains active with unreported time and no closure');
select is((select jsonb_build_array(state,version,completed_at) from public.tasks where id='w05-task-02'),
  '["in_progress",27,null]'::jsonb, 'the measured blocker leaves scientific admission incomplete');
select is((select jsonb_build_array(state,version,completed_at) from public.tasks where id='w05-task-04'),
  '["blocked",10,null]'::jsonb, 'capacity task is blocked without invented completion');
select is((select jsonb_build_array(state,version,decided_at,waiver_reason) from public.gates where id='w05-gate-03'),
  '["pending",11,null,""]'::jsonb, 'required capacity gate stays unresolved without a waiver');
select ok((select evidence like '%measured-profile no-go%' and evidence like '%not a universal hardware lower bound%' and evidence like '%cd21652427c8918473b97ec7a58a31db4ebd3e94b5582f6c65f8912f9e898c9b%' from public.gates where id='w05-gate-03'),
  'gate evidence binds the verified measured-profile blocker without universal claims');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.tasks t where id in ('w05-task-01','w05-task-03')),
  (select jsonb_path_query_array(content,'$.tasks[*] ? (@.id == "w05-task-01" || @.id == "w05-task-03")') from before_progress),
  'completed geometry and rehearsal evidence remain unchanged');
select is((select to_jsonb(w) from public.weeks w where id='week-04'),
  (select jsonb_path_query_first(content,'$.weeks[*] ? (@.id == "week-04")') from before_progress),
  'closed history remains unchanged');
select is((select jsonb_agg(to_jsonb(t) order by id) from public.weeks t where id<>'week-05'),
  (select jsonb_path_query_array(content,'$.weeks[*] ? (@.id != "week-05")') from before_progress),
  'all thirteen other weeks remain byte-for-byte unchanged');
select is((select state from public.gates where id='w05-test-gate'),'pending','scientific gate remains pending');
select ok((select reflection like '%Normal availability is 5 hours weekly, with up to 10 if necessary%' and reflection like '%no guaranteed Thanksgiving hours%' from public.weeks where id='week-05'),
  'confirmed availability is distinguished from hours worked');
select ok((select completion_note like '%Resident timing job 8038355 completed October 12%' and completion_note like '%separate preserved post-failure seal check passed%' and completion_note like '%Failed attempt 8028119 and independent-validator 8035576 remain preserved%' from public.tasks where id='w05-task-02'),'diagnostic preserves failed attempts and independent validation requirements');
select ok((select reflection like '%researcher explicitly requested that actual time remain unreported%' from public.weeks where id='week-05'),
  'the researcher request preserves unreported actual time');
select ok((select reflection like '%128 tests passed with no skips, failures or errors%' and reflection like '%963babe02eba70d34f3f9c9aa47af21145de387ca4d5a1ad6ccf9c226fb43381%' from public.weeks where id='week-05'), 'allocated rehearsal binds its accepted independent receipt');
select ok((select reflection like '%synthetic fixtures only%' and reflection like '%every scientific gate remains pending%' and reflection like '%no eligible successor final heads%' from public.weeks where id='week-05'), 'fixture rehearsal grants no scientific completion or eligible heads');
select ok((select reflection like '%8045152 completed October 13 at 00:31:55 UTC%' and reflection like '%0a3823e66a97192c5665185edbb908bf5b44c6dd9b451328d95d96476a84d785%' and reflection like '%all eight byte-identical original manifests%' from public.weeks where id='week-05'), 'accepted preparation binds original manifest identity and independent evidence');
select ok((select reflection like '%8048540 completed October 13 at 08:31:43.006302 UTC%' and reflection like '%All 86 fixture checks executed and passed without skips%' and reflection like '%108 metadata bindings, 616 source bindings%' and reflection like '%18,929 development queries and 18,884 primary novel query IDs%' and reflection like '%7703859e50361123de9054fba446c8384d423b8c549b69eab92720314c46c3d2%' from public.weeks where id='week-05'), 'supplementary completion binds independent review and actual metadata-only tables');
select ok((select reflection like '%8070391 was submitted October 13 at 20:46:55.956765 UTC%' and reflection like '%observed queued (qw), four CPU slots, at 20:49:22.424937 UTC%' and reflection like '%no outcome is claimed%' and reflection like '%5:55 PM EDT (21:55 UTC)%' from public.weeks where id='week-05'), 'geometry is a dated queued submission without an outcome or early polling');

create temporary table after_progress as select pg_temp.progress_snapshot() as content;
select lives_ok('select pg_temp.apply_week_five_successor_supplementary()', 'exact retry succeeds');
select is(pg_temp.progress_snapshot(),(select content from after_progress),'retry is side-effect free');

select pg_temp.seed_week_five_successor_supplementary();
update public.weeks set reflection='Concurrent researcher note' where id='week-05';
create temporary table conflicting_progress as select pg_temp.progress_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five_successor_supplementary()','40001',
  'week-05 changed; refusing to overwrite live progress','concurrent notes block overwrite');
select is(pg_temp.progress_snapshot(),(select content from conflicting_progress),'conflict rolls back publication');

select pg_temp.seed_week_five_successor_supplementary();
update public.tasks set completion_note='Concurrent researcher evidence' where id='w05-task-02';
create temporary table conflicting_task_progress as select pg_temp.progress_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five_successor_supplementary()','40001',
  'w05-task-02 changed; refusing to overwrite live progress','concurrent task evidence blocks overwrite');
select is(pg_temp.progress_snapshot(),(select content from conflicting_task_progress),'task conflict rolls back the earlier week update');

select pg_temp.seed_week_five_successor_supplementary();
update public.tasks set state='done',completion_note='Separate verified completion' where week_id='week-05';
update public.gates set state='met',evidence='Separate verified completion' where week_id='week-05';
update public.weeks set state='closed' where id='week-05';
create temporary table closed_progress as select pg_temp.progress_snapshot() as content;
select throws_ok('select pg_temp.apply_week_five_successor_supplementary()','40001',
  'week-05 is missing or closed; an audited reopen is required','closed week requires audited reopen before task/source editing');
select is(pg_temp.progress_snapshot(),(select content from closed_progress),'closed-week rejection preserves all history');
select * from finish();
rollback;
