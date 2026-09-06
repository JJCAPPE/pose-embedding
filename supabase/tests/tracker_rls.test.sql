begin;

create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to anon, authenticated;
grant execute on all functions in schema extensions to anon, authenticated;
set local search_path = public, extensions;
select plan(45);

insert into auth.users (id, email)
values
  ('11111111-1111-1111-1111-111111111111', 'owner@example.com'),
  ('22222222-2222-2222-2222-222222222222', 'stranger@example.com');

insert into public.projects (
  id, slug, title, research_question, summary, start_date, end_date,
  visibility
) values
  (
    'public-project', 'public-project', 'Public project', 'Question?', '',
    '2026-09-15', '2026-12-18', 'public'
  ),
  (
    'private-project', 'private-project', 'Private project', 'Private question?', '',
    '2026-09-15', '2026-12-18', 'private'
  );

select private.assign_project_owner('public-project', 'owner@example.com');
select private.assign_project_owner('private-project', 'owner@example.com');

insert into public.weeks (
  id, project_id, number, start_date, end_date, phase, title, objective,
  deliverable, planned_minutes
) values
  (
    'week-01', 'public-project', 1, '2026-09-15', '2026-09-20',
    'Protocol', 'Week one', 'Lock the protocol', 'A locked protocol', 480
  ),
  (
    'week-02', 'public-project', 2, '2026-09-21', '2026-09-27',
    'Data', 'Week two', 'Build manifests', 'Verified manifests', 480
  );

insert into public.tasks (
  id, project_id, week_id, position, title, required, state
) values (
  'w01-task-01', 'public-project', 'week-01', 1, 'Finish required work', true, 'todo'
);

insert into public.gates (
  id, project_id, week_id, position, criterion, required, state
) values (
  'w01-gate-01', 'public-project', 'week-01', 1, 'Approval recorded', true, 'pending'
);

insert into public.sources (
  id, project_id, title, authors, year, canonical_url, purpose, verified_at
) values (
  'source-one', 'public-project', 'Source one', 'Researcher', 2026,
  'https://example.com/source-one', 'Test source', '2026-09-06'
);

insert into public.week_sources (project_id, week_id, source_id, purpose, priority)
values ('public-project', 'week-01', 'source-one', 'Protocol grounding', 'required');

select is(
  (select count(*)::integer
     from pg_class
    where relnamespace = 'public'::regnamespace
      and relname in ('projects', 'weeks', 'tasks', 'gates', 'sources', 'week_sources', 'activity_log')
      and relrowsecurity),
  7,
  'RLS is enabled on every exposed tracker table'
);
select ok(
  (select relrowsecurity
     from pg_class
    where oid = 'private.project_owners'::regclass),
  'RLS is enabled on the private ownership mapping'
);
select is(
  (select count(*)
     from information_schema.columns
    where table_schema = 'public'
      and table_name = 'projects'
      and column_name = 'owner_id'),
  0::bigint,
  'public project rows have no owner UUID column'
);

select ok(
  not has_function_privilege('anon', 'private.import_research_plan(jsonb)', 'execute'),
  'anonymous callers cannot invoke the privileged plan importer'
);
select ok(
  not has_schema_privilege('anon', 'public', 'create')
  and not has_schema_privilege('authenticated', 'public', 'create'),
  'Data API roles cannot create objects in the exposed schema'
);

set local role anon;
select results_eq(
  $$select id from public.projects order by id$$,
  array['public-project'::text],
  'anonymous readers see only public projects'
);
select results_eq(
  $$select id from public.weeks order by id$$,
  array['week-01'::text, 'week-02'::text],
  'anonymous readers can see published week content'
);
select is(
  (select to_jsonb(project) ? 'owner_id'
     from public.projects as project
    where project.id = 'public-project'),
  false,
  'anonymous project payloads contain no owner UUID'
);
select throws_ok(
  $$select * from public.owner_access$$,
  '42501',
  null,
  'anonymous readers cannot query the owner-access view'
);
select throws_ok(
  $$select * from public.activity_log$$,
  '42501',
  null,
  'anonymous readers cannot access the private activity log'
);
select throws_ok(
  $$update public.tasks set title = 'tampered' where id = 'w01-task-01'$$,
  '42501',
  null,
  'anonymous readers have no task write grant'
);

set local role authenticated;
set local request.jwt.claim.sub = '22222222-2222-2222-2222-222222222222';
select results_eq(
  $$select id from public.projects order by id$$,
  array['public-project'::text],
  'a signed-in stranger can still read the public project'
);
select is_empty(
  $$select id from public.activity_log$$,
  'a signed-in stranger cannot read owner audit entries'
);
select is_empty(
  $$select project_id from public.owner_access$$,
  'a signed-in stranger receives no owner-access rows'
);
select throws_ok(
  $$select * from private.project_owners$$,
  '42501',
  null,
  'a signed-in stranger cannot read the private ownership mapping'
);
select throws_ok(
  $$insert into public.projects (
      id, slug, title, research_question, start_date, end_date, visibility
    ) values (
      'stranger-project', 'stranger-project', 'Stranger project', 'Question?',
      '2026-09-15', '2026-12-18', 'public'
    )$$,
  '42501',
  null,
  'a signed-in stranger cannot create a project'
);
select is_empty(
  $$update public.tasks set title = 'tampered' where id = 'w01-task-01' returning id$$,
  'a signed-in stranger updates no task rows'
);
select results_eq(
  $$select title from public.tasks where id = 'w01-task-01'$$,
  array['Finish required work'::text],
  'the denied stranger update left the task intact'
);
select throws_ok(
  $$insert into public.tasks (id, project_id, week_id, position, title)
    values ('stolen-task', 'public-project', 'week-01', 2, 'Stolen task')$$,
  '42501',
  null,
  'a signed-in stranger cannot insert into another owner project'
);

set local request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
select results_eq(
  $$update public.tasks
       set state = 'done'
     where id = 'w01-task-01' and version = 1
     returning state$$,
  array['done'::text],
  'the owner completes a task with an expected-version filter'
);
select ok(
  (select completed_at is not null from public.tasks where id = 'w01-task-01'),
  'task completion records its timestamp'
);
select is(
  (select version from public.tasks where id = 'w01-task-01'),
  2,
  'the database increments the task version'
);
select ok(
  exists (
    select 1 from public.activity_log
     where table_name = 'tasks'
       and row_id = 'w01-task-01'
       and action = 'UPDATE'
       and actor_id = '11111111-1111-1111-1111-111111111111'
  ),
  'the owner task update creates an attributed audit entry'
);
select throws_ok(
  $$update public.tasks set version = 99 where id = 'w01-task-01'$$,
  '40001',
  null,
  'clients cannot assign tracker versions directly'
);
select throws_ok(
  $$update public.tasks set state = 'skipped' where id = 'w01-task-01'$$,
  '23514',
  null,
  'a required task cannot be skipped'
);
select throws_ok(
  $$update public.tasks
       set required = false, completion_note = ''
     where id = 'w01-task-01'$$,
  '23514',
  null,
  'making a required task optional requires a recorded reason'
);
select throws_ok(
  $$update public.weeks set state = 'closed' where id = 'week-01'$$,
  '23514',
  null,
  'a week cannot close while a required gate is pending'
);
select throws_ok(
  $$update public.gates set state = 'met', evidence = '' where id = 'w01-gate-01'$$,
  '23514',
  null,
  'a met gate requires evidence'
);
select results_eq(
  $$update public.gates
       set state = 'met', evidence = 'https://example.com/approval'
     where id = 'w01-gate-01'
     returning state$$,
  array['met'::text],
  'the owner can meet a gate'
);
select ok(
  (select decided_at is not null from public.gates where id = 'w01-gate-01'),
  'a resolved gate records its decision time'
);
select results_eq(
  $$update public.weeks set state = 'closed' where id = 'week-01' returning state$$,
  array['closed'::text],
  'the owner closes a week after all required work passes'
);
select ok(
  (select closed_at is not null from public.weeks where id = 'week-01'),
  'closing a week records its timestamp'
);
select throws_ok(
  $$update public.tasks set completion_note = 'late edit' where id = 'w01-task-01'$$,
  '23514',
  null,
  'closed-week tasks cannot be changed'
);
select results_eq(
  $$update public.weeks set reflection = 'What we learned.' where id = 'week-01' returning reflection$$,
  array['What we learned.'::text],
  'a reflection can be added while the week stays closed'
);
select throws_ok(
  $$update public.weeks set objective = 'rewritten objective' where id = 'week-01'$$,
  '23514',
  null,
  'a closed week plan cannot change without reopening'
);
select throws_ok(
  $$update public.weeks set state = 'active' where id = 'week-01'$$,
  '23514',
  null,
  'a closed week cannot reopen without a new reason'
);
select results_eq(
  $$update public.weeks
       set state = 'active', reopen_reason = 'Advisor requested a correction.'
     where id = 'week-01'
     returning state$$,
  array['active'::text],
  'a reasoned reopen succeeds'
);
select ok(
  (select closed_at is null from public.weeks where id = 'week-01'),
  'reopening clears the closed timestamp'
);
select throws_ok(
  $$update public.weeks set state = 'active' where id = 'week-02'$$,
  '23514',
  null,
  'the next week cannot begin while the previous week is open'
);
select throws_ok(
  $$update public.gates
       set state = 'waived', waiver_reason = ''
     where id = 'w01-gate-01'$$,
  '23514',
  null,
  'a gate cannot be waived without a reason'
);
select throws_ok(
  $$insert into public.activity_log (
      project_id, actor_id, table_name, row_id, action
    ) values (
      'public-project',
      '11111111-1111-1111-1111-111111111111',
      'tasks', 'forged', 'INSERT'
    )$$,
  '42501',
  null,
  'even the owner cannot forge audit entries'
);
select throws_ok(
  $$select private.assign_project_owner('public-project', 'owner@example.com')$$,
  '42501',
  null,
  'the owner cannot call the administrative ownership function'
);
select results_eq(
  $$select id from public.projects order by id$$,
  array['private-project'::text, 'public-project'::text],
  'the owner can read their private and public projects'
);
select results_eq(
  $$select project_id from public.owner_access order by project_id$$,
  array['private-project'::text, 'public-project'::text],
  'the owner-access view reveals only project identifiers to the owner'
);
select ok(
  (select count(*) > 0 from public.activity_log),
  'the owner can read the append-only activity history'
);

reset role;
select * from finish();
rollback;
