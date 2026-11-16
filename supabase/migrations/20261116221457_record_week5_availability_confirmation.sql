-- Record the conditional report forecast and observed qualified CPU access gap.
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
      "version": 74,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 16: The researcher confirmed planning budgets of 4 hours before the November 29 locks, 1 hour for compute review and 8 hours for December 7-18 delivery; the corresponding allowances including the required 25% margin are 5, 1.25 and 10 hours. Actual time remains unreported. CPU job 8640396 remains independently accepted for all 23 retained-input components. Source review identified a possible fixed two-part construction and two-part independent verification path; implementation, qualification and complete capacity remain pending. The current conservative conditional forecast still exceeds the qualified public queue limit; it is not a measured report duration or accepted capacity. The official RCS access-request route has been identified; no request was sent and no new job was submitted. Week 5 stays open; genuine admission, selection, final training and novel opening remain gated."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 70,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 16: Component job 8640396 remains independently accepted: all 23 components, 218 scheduler seconds and complete command/source/input/runtime/resource/seal checks. Source review identified a possible fixed two-part construction and two-part independent verification path; implementation, qualification and complete capacity remain pending. Researcher planning availability is confirmed; actual time remains unreported. No new job, complete capacity pass or genuine admission is claimed.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-16-availability-confirmed-cpu-report-path-under-review"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 45,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON QUALIFIED CPU ACCESS AND COMPLETE CAPACITY, November 16: The researcher confirmed planning budgets of 4 hours before the November 29 locks, 1 hour for compute review and 8 hours for December 7-18 delivery; the corresponding allowances including the required 25% margin are 5, 1.25 and 10 hours. Actual time remains unreported. Source review identified a possible fixed two-part construction and two-part independent verification path; implementation, qualification and complete capacity remain pending. The current conservative conditional 22.773-hour report forecast including margin exceeds the observed 12-hour qualified public queue limit; compatible 24-hour queues require access not established here. This is a forecast/access gap, not measured report duration or scientific impossibility. The official RCS access-request route is available as a fallback; no request was sent. Preserve the 200 GiB reserve, 25% margin and November 29/December 6/December 7-18 deadlines. Week 5 remains open.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-16-availability-confirmed-cpu-report-path-under-review"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 51,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 16: CPU/GPU qualification, prefix measurement 8639284 and all 23 components from job 8640396 remain independently accepted. Researcher planning availability is confirmed at 4/1/8 hours for pre-lock work, compute review and delivery, with 5/1.25/10-hour allowances including the required 25% margin; actual time remains unreported. Source review identified a possible fixed two-part construction and two-part independent verification path; implementation, qualification and complete capacity remain pending. Qualified CPU access remains unresolved for the current conservative forecast. No complete capacity pass, genuine admission or later-stage authorization is claimed. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-16-availability-confirmed-cpu-report-path-under-review"
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
