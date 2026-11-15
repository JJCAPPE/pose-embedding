-- Record accepted kernel-only CPU qualification; GPU coverage, capacity and later stages remain pending.
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
      "version": 69,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 14: Independent review accepted CPU job 8621649 on the authorized kernel-only 553.184.2 profile. Nine fresh initializations (three per seed 7/17/29) and both original 43-panel geometry processes with all 430 tensor comparisons match accepted CPU 8561360 exactly. Accounting, complete runtime/source/input bindings, resources and unopened seals passed. GPU 8580442 used kernel 553.182.1, so fresh fixed 48-sample/all-12-layer parity and independent acceptance are the next prerequisite. ADR0012 preserves historical evidence without another adoption campaign or full recertification. Corrected-prefix timing, complete capacity and admission remain pending. Week 5 stays open; selection, final training and novel opening remain closed. No new timing forecast or actual researcher hours are inferred."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 65,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 14: CPU 8621649 passed independent kernel-only qualification under ADR0013. All nine initializations, both original 43-panel/all-430-comparison geometry processes, historical output equality, full runtime/source/input bindings, resources and seals passed. GPU 8580442 retains its kernel-553.182.1 provenance; the next prerequisite is fresh fixed 48-sample/all-12-layer parity for 553.184.2 followed by independent acceptance. Historical evidence remains preserved under ADR0012; corrected-prefix measurement and full admission remain pending.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-kernel-only-cpu-qualification-accepted"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 40,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON GPU QUALIFICATION AND MEASURED CAPACITY, November 14: CPU 8621649 is independently accepted on the authorized 553.184.2 profile. Fresh bounded GPU parity is required because accepted GPU 8580442 used the older kernel. Only accepted qualification permits the existing single corrected admission-prefix measurement; its independently accepted timing must feed the complete capacity model before genuine admission. The 873.911-hour estimate describes only the old call graph. Preserve the 200 GiB reserve, 25% margin and November 29/December 6/December 7-18 deadlines.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-kernel-only-cpu-qualification-accepted"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 46,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 14: CPU job 8621649 passed independent qualification for the exact kernel-only 553.184.2 profile, preserving historical initialization/geometry equality and all scientific checks. Fresh fixed 48-sample/all-12-layer GPU parity and independent acceptance remain required; accepted GPU 8580442 belongs to the older kernel profile. Corrected-prefix timing, complete feasible capacity and genuine admission remain pending. ADR0012 preserves historical evidence without another adoption campaign or full recertification. Selection runs, final training, novel opening and Week 5 closure remain unauthorized. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-kernel-only-cpu-qualification-accepted"
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
