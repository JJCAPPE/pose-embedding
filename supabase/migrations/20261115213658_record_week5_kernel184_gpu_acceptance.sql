-- Record accepted kernel-184 CPU/GPU qualification; measured capacity and admission remain pending.
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
      "version": 70,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 15: Independent review accepted GPU parity job 8622248 on the authorized kernel-553.184.2 profile, following accepted CPU qualification 8621649. The fixed 48-sample, all-12-layer comparison passes unchanged tolerances and complete runtime/source/input/resource/seal checks. This is bounded qualification only. The next prerequisite is the existing single corrected admission-prefix measurement; independently accepted timing must feed complete capacity and admission checks. Historical evidence retains its original provenance under ADR0012. Week 5 remains open; selection, final training and novel opening remain gated. No new runtime forecast, capacity pass or researcher hours are claimed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 66,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 15: CPU 8621649 and parity-only GPU 8622248 passed independent qualification on the authorized kernel-553.184.2 path. The GPU check covers the fixed 48 auxiliary samples and all 12 layers at frozen tolerances, with complete runtime/source/input/resource/seal evidence. Historical artifacts keep their original provenance. Corrected-prefix timing and full admission remain pending; this bounded qualification does not complete the task.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-15-kernel-184-gpu-parity-accepted"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 41,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON MEASURED CAPACITY AND ADMISSION, November 15: Bounded CPU/GPU qualification for kernel 553.184.2 is independently accepted. The next prerequisite is the existing single corrected admission-prefix measurement, followed by independent timing acceptance and the complete capacity model before genuine admission. The 873.911-hour forecast describes only the old call graph. Preserve the 200 GiB reserve, 25% margin and November 29/December 6/December 7-18 deadlines. No capacity pass or Week 5 closure is claimed.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-15-kernel-184-gpu-parity-accepted"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 47,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 15: CPU 8621649 and bounded GPU parity 8622248 are independently accepted for the authorized kernel-553.184.2 path. Corrected-prefix timing, complete feasible capacity and genuine admission remain pending. Qualification alone does not pass this gate or close Week 5. Selection, final training and novel opening remain gated. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-15-kernel-184-gpu-parity-accepted"
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
