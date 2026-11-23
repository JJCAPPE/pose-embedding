-- Record the November 23 Week 5 qualification review and conditional capacity blocker.
do $migration$
declare
  edits constant jsonb :=
$edits$
[
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "week-05",
      "version": 76,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 23: Job 8724028 finished. The synthetic report tests passed for 108 cells followed by 72. Independent review of the retained evidence is underway. The updated conditional forecast requires 49h 28m 54s and 48h 47m 46s for the two GPU jobs with the required margin. Both exceed the 48-hour queue limit. With the stated queue and review allowances, the schedule misses the compute deadline by 6h 45m 16s. Week 5 remains open. The pre-lock schedule needs updated researcher availability."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 72,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 23: CPU job 8724028 finished its fixed 108/72 synthetic report tests. The results cover all 180 cells. Independent qualification review of the retained evidence is underway.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-23-report-qualification-and-capacity-review"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 47,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON CAPACITY, November 23: Using the expanded inventory and the required 25% margin, the proposed GPU jobs need 49h 28m 54s and 48h 47m 46s. Both exceed the 48-hour L40S wall limit. The proposed schedule misses December 6 by 6h 45m 16s under its queue and review assumptions. Reconcile compatible allocation windows and remaining researcher hours before November 29.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-23-report-qualification-and-capacity-review"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 53,
      "state": "pending"
    },
    "values": {
      "evidence": "PENDING, November 23: Independent review of job 8724028 is underway. The proposed two GPU jobs exceed the ordinary 48-hour maximum, and the calendar misses the compute deadline under the stated queue and review assumptions. Capacity and genuine admission remain pending. Selection runs, final training and novel opening remain gated. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-23-report-qualification-and-capacity-review"
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
