\set ON_ERROR_STOP on

begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(18);

select lives_ok(
  (select statements[1] from supabase_migrations.schema_migrations
   where version = '20260929023601'),
  'an unseeded database defers to the canonical v2 plan'
);

insert into public.projects (id, slug, title, research_question, start_date, end_date)
values ('pose-embed', 'pose-embed', 'Pose Embed', 'Question?', '2026-09-15', '2026-12-18');
insert into public.weeks (
  id, project_id, number, start_date, end_date, phase, title, objective,
  deliverable, reflection, planned_minutes, actual_minutes, state, closed_at
) values
  ('week-01', 'pose-embed', 1, '2026-09-15', '2026-09-20', 'Protocol',
   'Protocol and access', 'Objective', 'Deliverable',
   'Actual minutes remain unreported.', 480, 0, 'closed', '2026-09-28T17:34:00Z'),
  ('week-02', 'pose-embed', 2, '2026-09-21', '2026-09-27', 'Data',
   'Immutable data manifests', 'Objective', 'Deliverable',
   '', 480, 0, 'closed', '2026-09-28T17:35:00Z');

-- Recreate the two exact live-open Week 3 predecessor subsets embedded in the
-- guarded migration. Closed Weeks 1 and 2 stay outside its edit list.
do $fixture$
declare
  edits jsonb;
  edit jsonb;
  table_name text;
  columns_sql text;
  values_sql text;
begin
  select split_part(statements[1], '$edits$', 2)::jsonb into edits
    from supabase_migrations.schema_migrations
   where version = '20260929023601';
  for table_name in select unnest(array['weeks', 'gates']) loop
    for edit in select value from jsonb_array_elements(edits)
      where value->>'table' = table_name
    loop
      select string_agg(format('%I', key), ', ' order by key),
             string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, values_sql from jsonb_object_keys(edit->'before') key;
      execute format(
        'insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
        table_name, columns_sql, values_sql, table_name)
        using edit->'before';
    end loop;
  end loop;
end
$fixture$;

create temporary table closed_weeks_before as
  select jsonb_agg(to_jsonb(w) order by number) as content
  from public.weeks w where number in (1, 2);
select is((select jsonb_agg(jsonb_build_array(id, state, actual_minutes)
  order by number) from public.weeks where number in (1, 2)),
  jsonb_build_array(jsonb_build_array('week-01', 'closed', 0),
    jsonb_build_array('week-02', 'closed', 0)),
  'the fixture includes the observed closed weeks with ambiguous zero minutes');
select lives_ok(
  (select statements[1] from supabase_migrations.schema_migrations
   where version = '20260929023601'),
  'the migration updates only the open Week 3 predecessor'
);
select is((select objective from public.weeks where id = 'week-03'),
  'Build a deterministic frozen MotionBERT feature path and independently verify historical one-shot and current v2 multi-positive retrieval behavior.',
  'the Week 3 objective distinguishes the historical and v2 evaluators');
select is((select deliverable from public.weeks where id = 'week-03'),
  'Repeatable clean auxiliary feature caches, independent retrieval and test-seal fixtures, and measured extraction cost.',
  'the Week 3 deliverable describes verified technical work');
select is((select advisor_prompt from public.weeks where id = 'week-03'),
  'What further fine-tuning, quota, and full-roster measurements are needed before the v2 campaign can launch?',
  'the Week 3 review prompt addresses the remaining capacity decision');
select matches((select reflection from public.weeks where id = 'week-03'),
  'hosted Week 1 and 2 records were closed later on September 28 with zero minutes.*researcher reconciliation',
  'the open Week 3 reflection records the hosted closure discrepancy');
select is((select criterion from public.gates where id = 'w03-gate-04'),
  'Measured extraction time and storage fit the Week 3 limits.',
  'the extraction gate claims only measured Week 3 feasibility');
select is((select jsonb_build_array(
  (select version from public.weeks where id = 'week-03'),
  (select version from public.gates where id = 'w03-gate-04'))),
  jsonb_build_array(6, 4), 'the two live rows each advance one database version');
select is((select jsonb_build_array(state, actual_minutes, closed_at)
  from public.weeks where id = 'week-03'),
  jsonb_build_array('planned', 0, null),
  'Week 3 remains open without invented researcher time');
select is((select jsonb_agg(to_jsonb(w) order by number)
  from public.weeks w where number in (1, 2)),
  (select content from closed_weeks_before),
  'closed Weeks 1 and 2 remain byte-for-byte unchanged');
with edits as (
  select value as edit from supabase_migrations.schema_migrations m,
    jsonb_array_elements(split_part(m.statements[1], '$edits$', 2)::jsonb)
  where m.version = '20260929023601'
), actual_rows as (
  select 'weeks' as table_name, id, to_jsonb(w) as content from public.weeks w
  union all select 'gates', id, to_jsonb(g) from public.gates g
)
select is((select count(*) from edits e join actual_rows a
  on a.table_name = e.edit->>'table' and a.id = e.edit->>'id'
  where (a.content - 'version') @>
    (((e.edit->'before') || (e.edit->'values')) - 'version')),
  2::bigint, 'both target rows match declared content, excluding version counters');

create temporary table reconciled_snapshot as select jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
) as content;
select count(*) as audit_count from public.activity_log \gset
select lives_ok(
  (select statements[1] from supabase_migrations.schema_migrations
   where version = '20260929023601'),
  'an exact replay is idempotent');
select is(jsonb_build_object(
  'weeks', (select jsonb_agg(to_jsonb(w) order by id) from public.weeks w),
  'gates', (select jsonb_agg(to_jsonb(g) order by id) from public.gates g)
), (select content from reconciled_snapshot),
  'an exact replay preserves row content and versions');
select is((select count(*) from public.activity_log), :audit_count::bigint,
  'an exact replay creates no audit event');

update public.gates set criterion = 'Concurrent researcher edit' where id = 'w03-gate-04';
select throws_ok(
  (select statements[1] from supabase_migrations.schema_migrations
   where version = '20260929023601'),
  '40001', 'w03-gate-04 changed; refusing to overwrite live progress',
  'a concurrent gate edit aborts the reconciliation');
select is((select criterion from public.gates where id = 'w03-gate-04'),
  'Concurrent researcher edit', 'the concurrent gate edit is preserved');

update public.weeks set state = 'closed' where id = 'week-03';
select throws_ok(
  (select statements[1] from supabase_migrations.schema_migrations
   where version = '20260929023601'),
  '40001', 'week-03 is missing or closed; an audited reopen is required',
  'a closed Week 3 requires audited reopening');

select * from finish();
rollback;
