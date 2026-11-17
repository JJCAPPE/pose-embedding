-- Record locally verified report splitting; allocated qualification and capacity remain pending.
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
      "version": 75,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 17: The authorized fixed report split is implemented and locally tested. Construction and independent verification each process 108 cells, then 72; all 180 cells and the complete report/bootstrap checks remain required. SCC qualification and complete capacity are pending. The forecast must include continuation reads, retained attempt growth and queue, detection and review time. Ordinary 48-hour L40S access is available without a reservation. Confirmed planning availability remains 4/1/8 hours before locks, for compute review and for delivery; actual time is unreported. Week 5 stays open; selection runs, final training and novel opening remain closed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 71,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 17: The fixed 108/72 report split is implemented and locally tested. Split and unsplit report files match; independent validation recomputes all 180 cells and rejects forged metrics in either part. Historical CPU/GPU qualification and component measurement 8640396 remain accepted with their original provenance. Qualification of the changed source on SCC is pending; local tests do not establish throughput or scientific acceptance.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-17-fixed-report-split-implemented-qualification-pending"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 46,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON QUALIFICATION AND COMPLETE CAPACITY, November 17: The report split is implemented. Before genuine admission, qualify the changed source and reconcile continuation reads, retained attempt growth, actual command grouping, storage and every queue/detection/review handoff. Ordinary 48-hour L40S access is available; no reservation or special access is assumed. Preserve the 200 GiB reserve, 25% margin, confirmed 4/1/8-hour planning budgets and fixed deadlines. Week 5 remains open.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-17-fixed-report-split-implemented-qualification-pending"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 52,
      "state": "pending"
    },
    "values": {
      "evidence": "PENDING, November 17: The report split is implemented and locally tested, with all 180 cells and complete independent report/bootstrap verification retained. SCC qualification and the full CPU/GPU/storage/calendar/researcher assessment remain required before genuine admission. No capacity pass, closure or later-stage authorization is claimed. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-17-fixed-report-split-implemented-qualification-pending"
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
