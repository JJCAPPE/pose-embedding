-- Record the authorized runtime-baseline amendment; scientific gates stay pending.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "week-05",
      "version": 39,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "October 19: the researcher adopted ADR0008 and authorized resuming Week 5 allocations after recording the runtime-baseline amendment and passing fresh preflights. Freeze one actual runtime; require exact within-profile geometry and initialization repeatability and cross-method pairing. Historical runtime-derived numerical equality is superseded prospectively; original panel IDs, fallback, all scientific settings, prior artifacts and seals remain required. Existing f101f0e execution-r2 scientific source and protocol/design locks remain unchanged. Accepted setup receipts remain evidence for their bound inputs; no new scientific gate has passed. Next: review the narrow external baseline checks, verify identity/authorization/seal/resources/no duplicate job, and run the allocated baseline/geometry prerequisite. Fresh parity/five caches, three complete pilots, nine corruption paths and independent replay/full admission/capacity remain incomplete. The two prior non-progress diagnostics are retained; the approach changes without erasing their count. October 18 remains missed; later deadlines are unchanged. Selection, final training and novel opening remain closed. Actual researcher time is unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 36,
      "state": "blocked"
    },
    "values": {
      "completion_note": "IN PROGRESS, October 19: researcher-authorized ADR0008 permits a prospective runtime baseline with exact current-run repeatability and pairing, preserving scientific settings, original identities/fallback and every historical attempt. No new runtime or scientific artifact is accepted yet. Review external checks and pass all fresh preflights before baseline/geometry allocation; then complete fresh parity/five caches, three full paired pilots, all nine development corruption paths/projections/results and independent replay. Existing r2 scientific source and locks remain unchanged. The historical two-attempt diagnostic stop is retained; the libm investigation is not resumed.",
      "state": "in_progress"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 19,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, October 19: ADR0008 authorizes runtime-baseline regeneration after preflights but grants no capacity pass. October 18 admission was missed. Re-estimate all fresh scientific work, full admission, independent recertification, retained/remaining storage, CPU/GPU windows and researcher work with queue/setup and at least 25% slack. Preserve the 200 GiB reserve plus 1.25 times remaining peak bytes, November 29 final locks, December 6 compute and protected December 7–18 delivery. Prior measured no-go remains historical evidence; selection and closure require accepted successor evidence. Actual time remains unreported."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 20,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, October 19: adopted ADR0008 authorizes a prospective runtime baseline and fresh regeneration after identity, authorization, seal, resource and duplicate-job preflights. This grants no scientific/capacity pass or selection authorization. The original panel/fallback and scientific scope remain fixed; exact within-profile repeats, pairing, independent validation and all retained evidence are required. The two historical non-progress diagnostics remain recorded. Complete the fresh scientific inventory and measured schema-2 CPU/GPU/storage/availability assessment, including all validation, recertification, queue/setup and at least 25% slack. The October 18 gate was missed; later deadlines remain unchanged. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/decisions/0008-runtime-baseline.md"
    }
  }
]
$edits$::jsonb;

  edit jsonb;
  current_row jsonb;
  expected_row jsonb;
  assignments text;
  changed_rows integer;
  expected_version integer;
  parent_id text;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; import research-plan.v3.json';
    return;
  end if;
  if not exists (select 1 from public.weeks where id = 'week-04' and project_id = 'pose-embed' and state = 'closed') then
    raise exception using errcode = '40001', message = 'Week 4 must be closed before starting Week 5';
  end if;
  for parent_id in
    select distinct value->>'week_id' from jsonb_array_elements(edits)
    where value->>'week_id' is not null order by 1
  loop
    if parent_id < 'week-05' then raise exception 'Historical week change forbidden'; end if;
    select to_jsonb(w) into current_row from public.weeks w
      where id = parent_id and project_id = 'pose-embed' for update;
    if current_row is null or current_row->>'state' = 'closed'
       or current_row->>'closed_at' is not null then
      raise exception using errcode = '40001',
        message = parent_id || ' is missing or closed; an audited reopen is required';
    end if;
  end loop;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if edit->>'table' not in ('weeks', 'tasks', 'gates')
       or edit->>'operation' <> 'update' or edit->'values' ? 'version' then
      raise exception 'Unexpected amendment scope';
    end if;
    execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
      into current_row using edit->>'id';
    expected_version := (edit->'before'->>'version')::integer;
    expected_row := edit->'before' || edit->'values'
      || jsonb_build_object('version', expected_version + 1);
    if current_row @> expected_row then continue; end if;
    if current_row is null or not (current_row @> (edit->'before')) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed; refusing to overwrite live progress';
    end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = ''pose-embed'' and t.version = $3 returning to_jsonb(t)',
      edit->>'table', assignments, edit->>'table')
      into current_row using edit->'values', edit->>'id', expected_version;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 or not (current_row @> expected_row) then
      raise exception using errcode = '40001', message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
