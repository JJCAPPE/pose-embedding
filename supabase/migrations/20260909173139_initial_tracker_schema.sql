-- Pose Embed tracker schema.
-- Generated with the Supabase CLI migration naming convention on 2026-09-06.

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
revoke create on schema public from public, anon, authenticated;

create table public.projects (
  id text primary key check (id ~ '^[a-z0-9][a-z0-9-]{1,79}$'),
  slug text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{1,79}$'),
  title text not null check (length(btrim(title)) between 1 and 160),
  research_question text not null check (length(btrim(research_question)) between 1 and 2000),
  summary text not null default '',
  start_date date not null,
  end_date date not null,
  timezone text not null default 'America/New_York',
  visibility text not null default 'public' check (visibility in ('public', 'private')),
  plan_version text not null default '1.0.0',
  version integer not null default 1 check (version >= 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint projects_date_order check (end_date >= start_date)
);

create table private.project_owners (
  project_id text primary key references public.projects(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  assigned_at timestamptz not null default now()
);

create table public.weeks (
  id text primary key check (id ~ '^[a-z0-9][a-z0-9-]{1,79}$'),
  project_id text not null references public.projects(id) on delete cascade,
  number smallint not null check (number between 1 and 14),
  start_date date not null,
  end_date date not null,
  phase text not null check (length(btrim(phase)) between 1 and 120),
  title text not null check (length(btrim(title)) between 1 and 160),
  objective text not null check (length(btrim(objective)) between 1 and 4000),
  deliverable text not null check (length(btrim(deliverable)) between 1 and 4000),
  risks text[] not null default '{}',
  advisor_prompt text not null default '',
  reflection text not null default '',
  reopen_reason text not null default '',
  planned_minutes integer not null check (planned_minutes between 0 and 10080),
  actual_minutes integer not null default 0 check (actual_minutes between 0 and 10080),
  state text not null default 'planned' check (state in ('planned', 'active', 'blocked', 'closed')),
  closed_at timestamptz,
  version integer not null default 1 check (version >= 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint weeks_project_number_unique unique (project_id, number),
  constraint weeks_id_project_unique unique (id, project_id),
  constraint weeks_date_order check (end_date >= start_date),
  constraint weeks_closed_timestamp check (
    (state = 'closed' and closed_at is not null)
    or (state <> 'closed' and closed_at is null)
  )
);

create table public.tasks (
  id text primary key check (id ~ '^[a-z0-9][a-z0-9-]{1,99}$'),
  project_id text not null references public.projects(id) on delete cascade,
  week_id text not null,
  position smallint not null check (position >= 0),
  title text not null check (length(btrim(title)) between 1 and 240),
  details text not null default '',
  expected_output text not null default '',
  required boolean not null default true,
  estimate_minutes integer not null default 0 check (estimate_minutes between 0 and 10080),
  state text not null default 'todo' check (state in ('todo', 'in_progress', 'blocked', 'done', 'skipped')),
  completion_note text not null default '',
  evidence_url text,
  completed_at timestamptz,
  version integer not null default 1 check (version >= 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tasks_week_project_fk
    foreign key (week_id, project_id)
    references public.weeks(id, project_id)
    on delete cascade,
  constraint tasks_week_position_unique unique (week_id, position),
  constraint tasks_required_not_skipped check (not (required and state = 'skipped')),
  constraint tasks_completion_timestamp check (
    (state = 'done' and completed_at is not null)
    or (state <> 'done' and completed_at is null)
  )
);

create table public.gates (
  id text primary key check (id ~ '^[a-z0-9][a-z0-9-]{1,99}$'),
  project_id text not null references public.projects(id) on delete cascade,
  week_id text not null,
  position smallint not null check (position >= 0),
  criterion text not null check (length(btrim(criterion)) between 1 and 2000),
  required boolean not null default true,
  state text not null default 'pending' check (state in ('pending', 'met', 'waived')),
  evidence text not null default '',
  waiver_reason text not null default '',
  decided_at timestamptz,
  version integer not null default 1 check (version >= 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint gates_week_project_fk
    foreign key (week_id, project_id)
    references public.weeks(id, project_id)
    on delete cascade,
  constraint gates_week_position_unique unique (week_id, position),
  constraint gates_waiver_reason check (state <> 'waived' or length(btrim(waiver_reason)) > 0),
  constraint gates_decision_timestamp check (
    (state = 'pending' and decided_at is null)
    or (state in ('met', 'waived') and decided_at is not null)
  )
);

create table public.sources (
  id text primary key check (id ~ '^[a-z0-9][a-z0-9-]{1,99}$'),
  project_id text not null references public.projects(id) on delete cascade,
  title text not null check (length(btrim(title)) between 1 and 500),
  authors text not null default '',
  year smallint check (year between 1900 and 2200),
  canonical_url text not null check (canonical_url ~ '^https://'),
  purpose text not null default '',
  verified_at date not null,
  version integer not null default 1 check (version >= 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint sources_project_url_unique unique (project_id, canonical_url),
  constraint sources_id_project_unique unique (id, project_id)
);

create table public.week_sources (
  project_id text not null references public.projects(id) on delete cascade,
  week_id text not null,
  source_id text not null,
  purpose text not null default '',
  priority text not null default 'recommended' check (priority in ('required', 'recommended')),
  version integer not null default 1 check (version >= 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (week_id, source_id),
  constraint week_sources_week_project_fk
    foreign key (week_id, project_id)
    references public.weeks(id, project_id)
    on delete cascade,
  constraint week_sources_source_project_fk
    foreign key (source_id, project_id)
    references public.sources(id, project_id)
    on delete cascade
);

create table public.activity_log (
  id bigint generated always as identity primary key,
  project_id text not null,
  actor_id uuid,
  table_name text not null check (table_name in ('projects', 'weeks', 'tasks', 'gates', 'sources', 'week_sources')),
  row_id text not null,
  action text not null check (action in ('INSERT', 'UPDATE', 'DELETE')),
  before_state jsonb,
  after_state jsonb,
  occurred_at timestamptz not null default now()
);

create index project_owners_owner_id_idx on private.project_owners(owner_id);
create index projects_visibility_idx on public.projects(visibility);
create index weeks_project_state_idx on public.weeks(project_id, state);
create index tasks_project_week_state_idx on public.tasks(project_id, week_id, state);
create index gates_project_week_state_idx on public.gates(project_id, week_id, state);
create index sources_project_verified_idx on public.sources(project_id, verified_at desc);
create index week_sources_project_source_idx on public.week_sources(project_id, source_id);
create index activity_log_project_time_idx on public.activity_log(project_id, occurred_at desc);

comment on table public.activity_log is
  'Append-only owner-visible audit trail. It is intentionally excluded from public exports.';
comment on table private.project_owners is
  'Non-exposed ownership mapping. Never copy owner UUIDs into public tracker tables.';
comment on column public.weeks.reopen_reason is
  'Required when reopening a closed week; the audit log preserves each prior value.';

create or replace function private.is_project_owner(target_project_id text)
returns boolean
language sql
stable
security definer
set search_path = pg_catalog
as $$
  select (select auth.uid()) is not null
    and exists (
      select 1
        from private.project_owners as ownership
       where ownership.project_id = target_project_id
         and ownership.owner_id = (select auth.uid())
    )
$$;

create view public.owner_access
with (security_invoker = true)
as
select project.id as project_id
  from public.projects as project
 where private.is_project_owner(project.id);

create or replace function private.manage_record_version()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
declare
  old_document jsonb := to_jsonb(old);
  new_document jsonb := to_jsonb(new);
begin
  if new.version <> old.version then
    raise exception using
      errcode = '40001',
      message = format('%I.version is managed by the database', tg_table_name),
      hint = 'Filter the update by the expected version and omit version from the update payload.';
  end if;

  if old_document ? 'id' and (new_document ->> 'id') is distinct from (old_document ->> 'id') then
    raise exception using errcode = '23514', message = format('%I.id is immutable', tg_table_name);
  end if;
  if old_document ? 'project_id'
     and (new_document ->> 'project_id') is distinct from (old_document ->> 'project_id') then
    raise exception using errcode = '23514', message = format('%I.project_id is immutable', tg_table_name);
  end if;
  if old_document ? 'week_id'
     and (new_document ->> 'week_id') is distinct from (old_document ->> 'week_id') then
    raise exception using errcode = '23514', message = format('%I.week_id is immutable', tg_table_name);
  end if;
  if old_document ? 'source_id'
     and (new_document ->> 'source_id') is distinct from (old_document ->> 'source_id') then
    raise exception using errcode = '23514', message = format('%I.source_id is immutable', tg_table_name);
  end if;

  new.version := old.version + 1;
  new.updated_at := now();
  return new;
end;
$$;

create or replace function private.enforce_week_integrity()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
declare
  project_start date;
  project_end date;
begin
  select p.start_date, p.end_date
    into project_start, project_end
    from public.projects as p
   where p.id = new.project_id;

  if new.start_date < project_start or new.end_date > project_end then
    raise exception using errcode = '23514', message = 'week dates must remain inside project dates';
  end if;

  if tg_op = 'UPDATE' and new.number <> old.number then
    raise exception using errcode = '23514', message = 'week number is immutable';
  end if;

  if tg_op = 'UPDATE' and old.state = 'closed' then
    if new.state = 'closed' then
      if row(
        new.start_date, new.end_date, new.phase, new.title, new.objective,
        new.deliverable, new.risks, new.advisor_prompt, new.planned_minutes
      ) is distinct from row(
        old.start_date, old.end_date, old.phase, old.title, old.objective,
        old.deliverable, old.risks, old.advisor_prompt, old.planned_minutes
      ) then
        raise exception using
          errcode = '23514',
          message = 'reopen a closed week before changing its plan';
      end if;
    elsif length(btrim(new.reopen_reason)) = 0
       or new.reopen_reason is not distinct from old.reopen_reason then
      raise exception using
        errcode = '23514',
        message = 'a new reopen_reason is required to reopen a closed week';
    end if;
  end if;

  if new.state in ('active', 'blocked', 'closed') and new.number > 1 then
    if not exists (
      select 1
        from public.weeks as previous_week
       where previous_week.project_id = new.project_id
         and previous_week.number = new.number - 1
         and previous_week.state = 'closed'
    ) then
      raise exception using
        errcode = '23514',
        message = format('week %s cannot begin before week %s is closed', new.number, new.number - 1);
    end if;
  end if;

  if new.state = 'closed' then
    if exists (
      select 1 from public.tasks as task
       where task.week_id = new.id
         and task.required
         and task.state <> 'done'
    ) then
      raise exception using errcode = '23514', message = 'all required tasks must be done before closing a week';
    end if;

    if exists (
      select 1 from public.gates as gate_item
       where gate_item.week_id = new.id
         and gate_item.required
         and gate_item.state not in ('met', 'waived')
    ) then
      raise exception using errcode = '23514', message = 'all required gates must be met or waived before closing a week';
    end if;

    new.closed_at := coalesce(new.closed_at, now());
  else
    new.closed_at := null;
  end if;

  return new;
end;
$$;

create or replace function private.enforce_task_integrity()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
declare
  target_week_id text;
begin
  target_week_id := case when tg_op = 'DELETE' then old.week_id else new.week_id end;
  if exists (
    select 1 from public.weeks as target_week
     where target_week.id = target_week_id
       and target_week.state = 'closed'
  ) then
    raise exception using errcode = '23514', message = 'reopen the week before changing its tasks';
  end if;

  if tg_op <> 'DELETE' then
    if tg_op = 'UPDATE'
       and old.required
       and not new.required
       and length(btrim(new.completion_note)) = 0 then
      raise exception using
        errcode = '23514',
        message = 'making a required task optional requires a reason in completion_note';
    end if;
    if new.required and new.state = 'skipped' then
      raise exception using errcode = '23514', message = 'a required task cannot be skipped';
    end if;
    if new.state = 'done' then
      new.completed_at := coalesce(new.completed_at, now());
    else
      new.completed_at := null;
    end if;
  end if;

  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create or replace function private.enforce_gate_integrity()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
declare
  target_week_id text;
begin
  target_week_id := case when tg_op = 'DELETE' then old.week_id else new.week_id end;
  if exists (
    select 1 from public.weeks as target_week
     where target_week.id = target_week_id
       and target_week.state = 'closed'
  ) then
    raise exception using errcode = '23514', message = 'reopen the week before changing its gates';
  end if;

  if tg_op <> 'DELETE' then
    if new.state = 'waived' and length(btrim(new.waiver_reason)) = 0 then
      raise exception using errcode = '23514', message = 'a waived gate requires a waiver reason';
    end if;
    if new.state = 'met' and length(btrim(new.evidence)) = 0 then
      raise exception using errcode = '23514', message = 'a met gate requires evidence';
    end if;
    if new.state = 'pending' then
      new.decided_at := null;
    else
      new.decided_at := coalesce(new.decided_at, now());
    end if;
  end if;

  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create or replace function private.guard_week_source_changes()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
declare
  target_week_id text;
begin
  target_week_id := case when tg_op = 'DELETE' then old.week_id else new.week_id end;
  if exists (
    select 1 from public.weeks as target_week
     where target_week.id = target_week_id
       and target_week.state = 'closed'
  ) then
    raise exception using errcode = '23514', message = 'reopen the week before changing its source links';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create or replace function private.audit_tracker_change()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare
  before_document jsonb := case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) end;
  after_document jsonb := case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) end;
  changed_document jsonb := coalesce(after_document, before_document);
  changed_project_id text;
  changed_row_id text;
begin
  if tg_table_name = 'projects' then
    changed_project_id := changed_document ->> 'id';
  else
    changed_project_id := changed_document ->> 'project_id';
  end if;

  if tg_table_name = 'week_sources' then
    changed_row_id := (changed_document ->> 'week_id') || ':' || (changed_document ->> 'source_id');
  else
    changed_row_id := changed_document ->> 'id';
  end if;

  insert into public.activity_log (
    project_id,
    actor_id,
    table_name,
    row_id,
    action,
    before_state,
    after_state
  ) values (
    changed_project_id,
    auth.uid(),
    tg_table_name,
    changed_row_id,
    tg_op,
    before_document,
    after_document
  );

  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create trigger projects_10_manage_version
before update on public.projects
for each row execute function private.manage_record_version();
create trigger weeks_10_manage_version
before update on public.weeks
for each row execute function private.manage_record_version();
create trigger tasks_10_manage_version
before update on public.tasks
for each row execute function private.manage_record_version();
create trigger gates_10_manage_version
before update on public.gates
for each row execute function private.manage_record_version();
create trigger sources_10_manage_version
before update on public.sources
for each row execute function private.manage_record_version();
create trigger week_sources_10_manage_version
before update on public.week_sources
for each row execute function private.manage_record_version();

create trigger weeks_20_integrity
before insert or update on public.weeks
for each row execute function private.enforce_week_integrity();
create trigger tasks_20_integrity
before insert or update or delete on public.tasks
for each row execute function private.enforce_task_integrity();
create trigger gates_20_integrity
before insert or update or delete on public.gates
for each row execute function private.enforce_gate_integrity();
create trigger week_sources_20_integrity
before insert or update or delete on public.week_sources
for each row execute function private.guard_week_source_changes();

create trigger projects_90_audit
after insert or update or delete on public.projects
for each row execute function private.audit_tracker_change();
create trigger weeks_90_audit
after insert or update or delete on public.weeks
for each row execute function private.audit_tracker_change();
create trigger tasks_90_audit
after insert or update or delete on public.tasks
for each row execute function private.audit_tracker_change();
create trigger gates_90_audit
after insert or update or delete on public.gates
for each row execute function private.audit_tracker_change();
create trigger sources_90_audit
after insert or update or delete on public.sources
for each row execute function private.audit_tracker_change();
create trigger week_sources_90_audit
after insert or update or delete on public.week_sources
for each row execute function private.audit_tracker_change();

create or replace function private.assign_project_owner(project_slug text, owner_email text)
returns void
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare
  selected_owner uuid;
  selected_project text;
  current_owner uuid;
  matching_users integer;
begin
  select count(*)
    into matching_users
    from auth.users as user_row
   where lower(user_row.email) = lower(owner_email);

  if matching_users <> 1 then
    raise exception using
      errcode = '22023',
      message = format('expected exactly one Auth user for %s, found %s', owner_email, matching_users);
  end if;

  select user_row.id
    into selected_owner
    from auth.users as user_row
   where lower(user_row.email) = lower(owner_email);

  select project.id
    into selected_project
    from public.projects as project
   where project.slug = project_slug;

  if selected_project is null then
    raise exception using
      errcode = '22023',
      message = 'project was not found or already belongs to a different Auth user';
  end if;

  select ownership.owner_id
    into current_owner
    from private.project_owners as ownership
   where ownership.project_id = selected_project;

  if current_owner is not null and current_owner <> selected_owner then
    raise exception using
      errcode = '22023',
      message = 'project was not found or already belongs to a different Auth user';
  end if;

  insert into private.project_owners (project_id, owner_id)
  values (selected_project, selected_owner)
  on conflict (project_id) do nothing;

  -- Produce a versioned, owner-visible audit event without publishing ownership.
  update public.projects as project
     set updated_at = project.updated_at
   where project.id = selected_project;
end;
$$;

create or replace function private.import_research_plan(plan_document jsonb)
returns void
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare
  project_document jsonb := plan_document -> 'project';
  project_key text := project_document ->> 'id';
  week_document jsonb;
  task_document jsonb;
  gate_document jsonb;
  source_document jsonb;
  link_document jsonb;
begin
  if plan_document ->> 'schemaVersion' <> '1.0.0' then
    raise exception using errcode = '22023', message = 'unsupported research plan schemaVersion';
  end if;
  if jsonb_typeof(plan_document -> 'weeks') <> 'array'
     or jsonb_array_length(plan_document -> 'weeks') <> 14 then
    raise exception using errcode = '22023', message = 'the tracker seed must contain exactly 14 weeks';
  end if;
  if project_key is null or project_key = '' then
    raise exception using errcode = '22023', message = 'the tracker seed requires project.id';
  end if;
  if exists (select 1 from public.projects as existing where existing.id = project_key) then
    raise exception using
      errcode = '23505',
      message = format('project %s is already seeded; refusing to overwrite live progress', project_key);
  end if;

  insert into public.projects (
    id, slug, title, research_question, summary, start_date, end_date,
    timezone, visibility, plan_version, version
  ) values (
    project_key,
    project_document ->> 'slug',
    project_document ->> 'title',
    project_document ->> 'researchQuestion',
    coalesce(project_document ->> 'summary', ''),
    (project_document ->> 'startDate')::date,
    (project_document ->> 'endDate')::date,
    coalesce(project_document ->> 'timezone', 'America/New_York'),
    coalesce(project_document ->> 'visibility', 'public'),
    plan_document ->> 'schemaVersion',
    coalesce((project_document ->> 'version')::integer, 1)
  );

  for week_document in select value from jsonb_array_elements(plan_document -> 'weeks') loop
    if week_document ->> 'projectId' <> project_key then
      raise exception using errcode = '22023', message = 'week.projectId does not match project.id';
    end if;

    insert into public.weeks (
      id, project_id, number, start_date, end_date, phase, title, objective,
      deliverable, risks, advisor_prompt, reflection, planned_minutes,
      actual_minutes, state, closed_at, version
    ) values (
      week_document ->> 'id',
      project_key,
      (week_document ->> 'number')::smallint,
      (week_document ->> 'startDate')::date,
      (week_document ->> 'endDate')::date,
      week_document ->> 'phase',
      week_document ->> 'title',
      week_document ->> 'objective',
      week_document ->> 'deliverable',
      array(select jsonb_array_elements_text(coalesce(week_document -> 'risks', '[]'::jsonb))),
      coalesce(week_document ->> 'advisorPrompt', ''),
      coalesce(week_document ->> 'reflection', ''),
      coalesce((week_document ->> 'plannedMinutes')::integer, 0),
      coalesce((week_document ->> 'actualMinutes')::integer, 0),
      coalesce(week_document ->> 'state', 'planned'),
      nullif(week_document ->> 'closedAt', '')::timestamptz,
      coalesce((week_document ->> 'version')::integer, 1)
    );

    for task_document in select value from jsonb_array_elements(coalesce(week_document -> 'tasks', '[]'::jsonb)) loop
      if task_document ->> 'weekId' <> week_document ->> 'id' then
        raise exception using errcode = '22023', message = 'task.weekId does not match its containing week';
      end if;
      insert into public.tasks (
        id, project_id, week_id, position, title, details, expected_output,
        required, estimate_minutes, state, completion_note, evidence_url,
        completed_at, version
      ) values (
        task_document ->> 'id',
        project_key,
        week_document ->> 'id',
        (task_document ->> 'position')::smallint,
        task_document ->> 'title',
        coalesce(task_document ->> 'details', ''),
        coalesce(task_document ->> 'expectedOutput', ''),
        coalesce((task_document ->> 'required')::boolean, true),
        coalesce((task_document ->> 'estimateMinutes')::integer, 0),
        coalesce(task_document ->> 'state', 'todo'),
        coalesce(task_document ->> 'completionNote', ''),
        nullif(task_document ->> 'evidenceUrl', ''),
        nullif(task_document ->> 'completedAt', '')::timestamptz,
        coalesce((task_document ->> 'version')::integer, 1)
      );
    end loop;

    for gate_document in select value from jsonb_array_elements(coalesce(week_document -> 'gates', '[]'::jsonb)) loop
      if gate_document ->> 'weekId' <> week_document ->> 'id' then
        raise exception using errcode = '22023', message = 'gate.weekId does not match its containing week';
      end if;
      insert into public.gates (
        id, project_id, week_id, position, criterion, required, state,
        evidence, waiver_reason, decided_at, version
      ) values (
        gate_document ->> 'id',
        project_key,
        week_document ->> 'id',
        (gate_document ->> 'position')::smallint,
        gate_document ->> 'criterion',
        coalesce((gate_document ->> 'required')::boolean, true),
        coalesce(gate_document ->> 'state', 'pending'),
        coalesce(gate_document ->> 'evidence', ''),
        coalesce(gate_document ->> 'waiverReason', ''),
        nullif(gate_document ->> 'decidedAt', '')::timestamptz,
        coalesce((gate_document ->> 'version')::integer, 1)
      );
    end loop;
  end loop;

  for source_document in select value from jsonb_array_elements(coalesce(plan_document -> 'sources', '[]'::jsonb)) loop
    insert into public.sources (
      id, project_id, title, authors, year, canonical_url, purpose, verified_at
    ) values (
      source_document ->> 'id',
      project_key,
      source_document ->> 'title',
      coalesce(source_document ->> 'authors', ''),
      nullif(source_document ->> 'year', '')::smallint,
      source_document ->> 'canonicalUrl',
      coalesce(source_document ->> 'purpose', ''),
      (source_document ->> 'verifiedAt')::date
    );
  end loop;

  for link_document in select value from jsonb_array_elements(coalesce(plan_document -> 'weekSources', '[]'::jsonb)) loop
    insert into public.week_sources (project_id, week_id, source_id, purpose, priority)
    values (
      project_key,
      link_document ->> 'weekId',
      link_document ->> 'sourceId',
      coalesce(link_document ->> 'purpose', ''),
      coalesce(link_document ->> 'priority', 'recommended')
    );
  end loop;

  if (select count(*) from public.weeks as imported where imported.project_id = project_key) <> 14 then
    raise exception using errcode = '22023', message = 'tracker seed did not create exactly 14 weeks';
  end if;
end;
$$;

revoke all on function private.manage_record_version() from public, anon, authenticated;
revoke all on function private.enforce_week_integrity() from public, anon, authenticated;
revoke all on function private.enforce_task_integrity() from public, anon, authenticated;
revoke all on function private.enforce_gate_integrity() from public, anon, authenticated;
revoke all on function private.guard_week_source_changes() from public, anon, authenticated;
revoke all on function private.audit_tracker_change() from public, anon, authenticated;
revoke all on function private.assign_project_owner(text, text) from public, anon, authenticated;
revoke all on function private.import_research_plan(jsonb) from public, anon, authenticated;
revoke all on function private.is_project_owner(text) from public, anon, authenticated;

-- This boolean helper is the sole private function callable by `authenticated`.
-- It is needed by RLS and the security-invoker owner_access view; the private
-- schema remains outside PostgREST's exposed schemas and the function reveals
-- no owner identifier.
grant usage on schema private to authenticated;
grant execute on function private.is_project_owner(text) to authenticated;

alter table private.project_owners enable row level security;
alter table public.projects enable row level security;
alter table public.weeks enable row level security;
alter table public.tasks enable row level security;
alter table public.gates enable row level security;
alter table public.sources enable row level security;
alter table public.week_sources enable row level security;
alter table public.activity_log enable row level security;

revoke all on table private.project_owners from public, anon, authenticated;
revoke all on table
  public.projects,
  public.weeks,
  public.tasks,
  public.gates,
  public.sources,
  public.week_sources,
  public.activity_log
from anon, authenticated;
revoke all on table public.owner_access from public, anon, authenticated;
revoke all on sequence public.activity_log_id_seq from anon, authenticated;

grant select on table
  public.projects,
  public.weeks,
  public.tasks,
  public.gates,
  public.sources,
  public.week_sources
to anon, authenticated;

grant select on table public.owner_access to authenticated;

grant update, delete on table public.projects to authenticated;

grant insert, update, delete on table
  public.weeks,
  public.tasks,
  public.gates,
  public.sources,
  public.week_sources
to authenticated;

grant select on table public.activity_log to authenticated;

create policy "anonymous readers see published projects"
on public.projects for select
to anon
using (visibility = 'public');

create policy "authenticated readers see published or owned projects"
on public.projects for select
to authenticated
using (visibility = 'public' or private.is_project_owner(id));

create policy "owners update projects"
on public.projects for update
to authenticated
using (private.is_project_owner(id))
with check (private.is_project_owner(id));

create policy "owners delete projects"
on public.projects for delete
to authenticated
using (private.is_project_owner(id));

create policy "anonymous readers see published weeks"
on public.weeks for select
to anon
using (
  exists (
    select 1 from public.projects as project
     where project.id = weeks.project_id
       and project.visibility = 'public'
  )
);

create policy "authenticated readers see published or owned weeks"
on public.weeks for select
to authenticated
using (
  exists (
    select 1 from public.projects as project
     where project.id = weeks.project_id
       and project.visibility = 'public'
  )
  or private.is_project_owner(weeks.project_id)
);

create policy "owners insert weeks"
on public.weeks for insert
to authenticated
with check (
  private.is_project_owner(weeks.project_id)
);

create policy "owners update weeks"
on public.weeks for update
to authenticated
using (private.is_project_owner(weeks.project_id))
with check (private.is_project_owner(weeks.project_id));

create policy "owners delete weeks"
on public.weeks for delete
to authenticated
using (private.is_project_owner(weeks.project_id));

create policy "anonymous readers see published tasks"
on public.tasks for select
to anon
using (
  exists (
    select 1 from public.projects as project
     where project.id = tasks.project_id
       and project.visibility = 'public'
  )
);

create policy "authenticated readers see published or owned tasks"
on public.tasks for select
to authenticated
using (
  exists (
    select 1 from public.projects as project
     where project.id = tasks.project_id
       and project.visibility = 'public'
  )
  or private.is_project_owner(tasks.project_id)
);

create policy "owners insert tasks"
on public.tasks for insert
to authenticated
with check (private.is_project_owner(tasks.project_id));

create policy "owners update tasks"
on public.tasks for update
to authenticated
using (private.is_project_owner(tasks.project_id))
with check (private.is_project_owner(tasks.project_id));

create policy "owners delete tasks"
on public.tasks for delete
to authenticated
using (private.is_project_owner(tasks.project_id));

create policy "anonymous readers see published gates"
on public.gates for select
to anon
using (
  exists (
    select 1 from public.projects as project
     where project.id = gates.project_id
       and project.visibility = 'public'
  )
);

create policy "authenticated readers see published or owned gates"
on public.gates for select
to authenticated
using (
  exists (
    select 1 from public.projects as project
     where project.id = gates.project_id
       and project.visibility = 'public'
  )
  or private.is_project_owner(gates.project_id)
);

create policy "owners insert gates"
on public.gates for insert
to authenticated
with check (private.is_project_owner(gates.project_id));

create policy "owners update gates"
on public.gates for update
to authenticated
using (private.is_project_owner(gates.project_id))
with check (private.is_project_owner(gates.project_id));

create policy "owners delete gates"
on public.gates for delete
to authenticated
using (private.is_project_owner(gates.project_id));

create policy "anonymous readers see published sources"
on public.sources for select
to anon
using (
  exists (
    select 1 from public.projects as project
     where project.id = sources.project_id
       and project.visibility = 'public'
  )
);

create policy "authenticated readers see published or owned sources"
on public.sources for select
to authenticated
using (
  exists (
    select 1 from public.projects as project
     where project.id = sources.project_id
       and project.visibility = 'public'
  )
  or private.is_project_owner(sources.project_id)
);

create policy "owners insert sources"
on public.sources for insert
to authenticated
with check (private.is_project_owner(sources.project_id));

create policy "owners update sources"
on public.sources for update
to authenticated
using (private.is_project_owner(sources.project_id))
with check (private.is_project_owner(sources.project_id));

create policy "owners delete sources"
on public.sources for delete
to authenticated
using (private.is_project_owner(sources.project_id));

create policy "anonymous readers see published week source links"
on public.week_sources for select
to anon
using (
  exists (
    select 1 from public.projects as project
     where project.id = week_sources.project_id
       and project.visibility = 'public'
  )
);

create policy "authenticated readers see published or owned week source links"
on public.week_sources for select
to authenticated
using (
  exists (
    select 1 from public.projects as project
     where project.id = week_sources.project_id
       and project.visibility = 'public'
  )
  or private.is_project_owner(week_sources.project_id)
);

create policy "owners insert week source links"
on public.week_sources for insert
to authenticated
with check (private.is_project_owner(week_sources.project_id));

create policy "owners update week source links"
on public.week_sources for update
to authenticated
using (private.is_project_owner(week_sources.project_id))
with check (private.is_project_owner(week_sources.project_id));

create policy "owners delete week source links"
on public.week_sources for delete
to authenticated
using (private.is_project_owner(week_sources.project_id));

create policy "owners read the activity log"
on public.activity_log for select
to authenticated
using (private.is_project_owner(activity_log.project_id));
