-- Record the independently reviewed measurement startup failure and exact environment recovery.
do $migration$
declare
  edits constant jsonb := $edits$[
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "week-05",
      "version": 66,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 14: Independent review located job 8581145's four-second failure at the startup runtime check, before the admission measurement began. CUBLAS_WORKSPACE_CONFIG was absent instead of the accepted :4096:8; all other recorded profile fields match CPU baseline 8561360. Replacement CPU job 8616892 was submitted once with that existing value and observed queued with four slots at 12:50:09 UTC. The scheduler environment is verified; actual startup qualification and measurement outcome remain pending. The full runtime comparison, frozen source and failed attempt are preserved. Accepted CPU/GPU qualification and historical evidence remain intact. Corrected-path timing, complete capacity and admission are pending. Week 5 remains open; selection, final training and novel opening stay closed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 62,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 14: CPU 8561360 and bounded GPU parity 8580442 remain accepted. Measurement job 8581145 failed before the admission controller started because the accepted CUBLAS_WORKSPACE_CONFIG setting was missing. Independent review found no other startup-profile difference. Replacement job 8616892 was submitted with :4096:8 and observed queued with four CPU slots. Its scheduler environment includes the required value and all three roots. Actual startup qualification and outcome remain pending; the complete runtime check is unchanged. No admission measurement or capacity result is accepted.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-admission-measurement-startup-failure"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 37,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON MEASURED CAPACITY, November 14: Job 8581145 stopped at the startup environment check and produced no admission timing. Replacement job 8616892 was submitted with the exact accepted environment setting and is awaiting execution; no measurement result is accepted and no check is waived. Complete CPU/GPU/storage/calendar/researcher capacity and actual admission remain pending. The 873.911-hour estimate describes only the old call graph. Preserve the 200 GiB reserve, 25% margin and fixed deadlines.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-admission-measurement-startup-failure"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 43,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 14: Accepted CPU/GPU qualification remains intact. Independent review traced measurement 8581145's startup failure to one missing accepted environment setting; replacement job 8616892 was submitted with the exact accepted value and unchanged runtime checks. Actual startup qualification and the measurement outcome are pending. Corrected admission-prefix timing and feasible complete capacity remain pending. No selection runs, final training, novel opening or Week 5 closure are authorized. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-admission-measurement-startup-failure"
    }
  }
]$edits$::jsonb;

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
