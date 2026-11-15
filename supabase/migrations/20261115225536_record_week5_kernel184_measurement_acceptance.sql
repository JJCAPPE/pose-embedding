-- Record accepted kernel-184 prefix timing; complete capacity and admission remain pending.
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
      "version": 71,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 15: Independent review accepted CPU job 8639284 on the qualified kernel-553.184.2 profile. The one complete admission-prefix pass took 1,289.522811 seconds and reached exactly the intended pending-capacity rejection; the 1,447-second scheduler job retained successful command, source/input/runtime/resource/seal checks. No capacity or authorization was produced. This is parser-warmed prefix timing, not complete campaign throughput. Complete measured CPU/GPU/storage/researcher capacity and genuine admission remain pending. Historical evidence retains its original provenance under ADR0012. Week 5 remains open; selection, final training and novel opening remain gated. No actual researcher hours are claimed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 67,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 15: Following accepted CPU 8621649 and GPU 8622248 qualification, single-prefix measurement 8639284 passed independent review. Its full scientific prefix reached the exact pending-capacity rejection in 1,289.522811 seconds, with complete command/source/input/runtime/resource/seal evidence and no capacity or authorization output. This parser-warmed engineering timing does not establish complete campaign throughput or finish admission.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-15-corrected-admission-prefix-measurement-accepted"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 42,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON COMPLETE CAPACITY AND ADMISSION, November 15: Single-prefix measurement 8639284 is independently accepted at 1,289.522811 seconds. Its result must feed the complete measured CPU/GPU/storage/researcher capacity model before genuine admission. No corrected total campaign forecast or capacity pass is claimed; the 873.911-hour forecast describes only the old call graph. Preserve the 200 GiB reserve, 25% margin and November 29/December 6/December 7-18 deadlines. Week 5 remains open.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-15-corrected-admission-prefix-measurement-accepted"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 48,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 15: CPU 8621649 and GPU 8622248 qualification and corrected single-prefix measurement 8639284 are independently accepted. The 1,289.522811-second parser-warmed prefix is not complete campaign throughput. Complete feasible capacity and genuine admission remain pending; no capacity or authorization output was produced by the measurement. This gate remains pending, Week 5 remains open, and selection, final training and novel opening remain gated. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-15-corrected-admission-prefix-measurement-accepted"
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
