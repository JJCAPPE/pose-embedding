-- Record the exact kernel blocker and paused automation; no scientific gate advances.
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
      "version": 43,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 4, 5:41 PM EST review: job 8435003 failed before scientific work after 41 scheduler seconds. The retained complete profile differs from the authorized profile only in runtime.platform: SCC supplied kernel 553.182.1 instead of ADR0009's 553.177.1. All other fields match exactly. Independent failure review verified 22 retained files, 763 metadata bindings and 616 frozen source files; no initialization, geometry or new runtime is accepted. The observation-retention correction worked. Further allocations require a researcher decision; the existing automation is PAUSED with saved-state verification. A narrow result-blind amendment for the exact observed profile is proposed, not adopted. All affected validation/regeneration, admission/recertification, measured schema-2 capacity and selection authorization remain required. Week 5 stays open; selection runs, final training and novel opening remain closed. November 29 locks, December 6 compute and December 7-18 delivery remain fixed. Actual researcher time is unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 40,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS; allocations held, November 4: independent review verified job 8435003's pre-scientific startup failure. The retained profile has exactly one difference: kernel 553.182.1 instead of the authorized 553.177.1. All other complete profile fields match. The retention correction worked; no initialization, geometry or new runtime is accepted. A researcher decision is required before any retry; the existing automation is paused. The proposed exact-profile amendment is not authorized. Fresh CPU acceptance, synthetic GPU verification, parity/five caches, three paired pilots/replay and all development corruption/projection/retrieval evidence remain required. Preserve frozen source/r2 locks, seeds, physical batches, panel/fallback and every tolerance."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 23,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, November 4: job 8435003's retained profile isolates a newer kernel (553.182.1 versus authorized 553.177.1); researcher authorization is required before affected validation can resume. The earlier 20:53 UTC storage observation passed the unchanged 467,248,364,800-byte requirement, but no new capacity observation or campaign feasibility is claimed. No scientific outputs were produced or deducted. Full admission/recertification and measured CPU/GPU/storage/researcher capacity remain pending, including queue/setup and at least 25% slack. Preserve the 200 GiB reserve, November 29 locks, December 6 compute and December 7-18 delivery. Admission targets were missed; actual researcher time is unreported."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 24,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 4: job 8435003's startup failure is independently verified. Only runtime.platform differs: observed kernel 553.182.1 versus ADR0009's 553.177.1; all other complete profile fields match. No new runtime or scientific prerequisite is accepted. A narrow result-blind amendment is proposed, not adopted; allocations are held and the existing automation is paused pending researcher direction. Complete affected regeneration, full admission/recertification and measured schema-2 capacity remain required before selection authorization. Historical libm diagnostics remain two and stopped; this retention attempt narrowed the current cause. Failure-verification SHA-256: f8d0bc151b4fb042b2f821ea7db0d0b79a268da0e1fcd4aaf35f46b936a17d7f. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#current-checkpoint-november-4-2026"
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
