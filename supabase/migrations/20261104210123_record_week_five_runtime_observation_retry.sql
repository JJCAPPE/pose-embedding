-- Record verified startup failure and reviewed retention retry; no scientific gate advances.
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
      "version": 42,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 4: SCC access is restored. Independent review verified that job 8426211 failed its startup runtime-profile comparison on November 3 at 8:17:17 PM EST after 39 scheduler seconds, before initialization or geometry. The exact differing runtime field is unknown because the rejected observation was not retained. A reviewed external correction now saves it before the unchanged comparison. Successor job 8435003 was submitted and observed queued at 3:56 PM EST November 4; no new runtime or scientific result is accepted. Fresh storage checks pass, but full new-profile validation, regeneration, admission/recertification and measured schema-2 capacity remain required. Preserve f101f0e/r2, paired seeds and physical batches, fixed panel/fallback and all scientific settings. Historical libm diagnostics remain two and stopped. Week 5 stays open; selection runs, final training and novel opening remain closed. November 29 locks, December 6 compute and December 7-18 delivery remain fixed. Actual researcher time is unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 39,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 4: job 8426211's pre-scientific startup failure is independently verified; no initialization, geometry or new runtime was accepted. SCC access is restored. The external observation-retention correction passed 121 synthetic tests and independent review without changing the strict profile comparison, scientific source or numerical requirements. Successor 8435003 was observed queued at 3:56 PM EST. Independently review its retained startup profile and all required accounting, source/input, resource, seal and numerical evidence before dependent work. Fresh synthetic GPU verification, parity/five caches, three paired pilots/replay and all nine corruption paths/projections/retrieval remain required. Preserve prior evidence, paired seeds/batches, fixed panel/fallback and every tolerance."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 22,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, November 4: fresh quota headroom of 3,820,630,000,000 bytes and filesystem free space of 4,209,739,038,720 bytes exceed the unchanged 467,248,364,800-byte storage requirement. The retained failed attempt was reconciled without deducting completed outputs or deleting evidence. This establishes observed storage headroom, not campaign capacity. Job 8426211 failed before scientific work; successor 8435003 acceptance and new-profile timing remain pending. Full admission/recertification and CPU/GPU/researcher capacity must include queue/setup and at least 25% slack. Preserve the 200 GiB reserve, November 29 locks, December 6 compute and December 7-18 delivery. The admission targets were missed; actual researcher time remains unreported."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 23,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 4: restored SCC access allowed independent acceptance of job 8426211's startup failure record only. No new-profile scientific prerequisite or measured capacity is accepted. The reviewed external correction retains rejected runtime observations while preserving every comparison and tolerance. Successor 8435003 was observed queued at 3:56 PM EST; submission is not acceptance. Fresh storage headroom passes; complete regeneration, full admission/recertification and schema-2 capacity remain required before selection authorization. Historical libm diagnostics remain two and stopped. Failure-verification SHA-256: adf934852624191d76bc5d241f4e145178da544bc7840c01515fba7b50b4c353. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#current-checkpoint-november-4-2026"
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
