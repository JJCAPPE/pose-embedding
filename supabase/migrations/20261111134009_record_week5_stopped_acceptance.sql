-- Record the returned prompt and stopped command; final acceptance stays unverified.
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
      "version": 63,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 11: Whole-prefix measurement 8565319 completed and passed local independent engineering review of the exact qualified CPU runtime and required proof-reuse counters. Final guarded receipt publication is unverified. First/reused/fresh-proof passes took 1276.968/1190.539/1372.930 seconds. All timed passes used a warm parser in one process; separate fresh-command measurement remains required. The unchanged required-check calculation gives 873.911 hours including 25% margin versus 168 available, down from the previous 2225.815-hour bound but still infeasible before other work. The SCC session became unresponsive during final acceptance. A later pane capture showed the prompt had returned and the acceptance command was stopped. The existing automation remains PAUSED pending researcher resume direction; reconcile the stopped process and possible receipts before retrying. No downstream GPU job was submitted. Next, after acceptance, is conditional synthetic GPU runtime qualification; parity, retained-artifact replay/adoption, full admission, independent recertification, feasible complete capacity and selection authorization remain required. Week 5 stays open; later stages stay closed and actual researcher time remains unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 59,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 11: Whole-prefix 8565319 passed local independent review of exact runtime/source bindings, accounting, three commands, resource/seal checks and intended proof-reuse counters. Original artifacts and producer labels remain unchanged. Final guarded receipt publication remains unverified. The SCC prompt later returned with the acceptance command stopped. The same automation remains PAUSED pending researcher resume direction; reconcile that process and possible receipts before retrying. GPU qualification preparation remains unexecuted; parity and artifact-specific replay remain required. No artifact adoption, full admission or independent recertification is accepted."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 40,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 11: Conditional CPU qualification and component comparison are accepted. Whole-prefix measurement completed and passed local independent review; its final guarded receipt is unverified. The SCC prompt returned with the acceptance command stopped. The automation remains PAUSED pending researcher resume direction and reconciliation of that process and possible receipts. Required checks still exceed the fixed window: 873.911 hours with margin versus 168 available. GPU/parity, retained-artifact replay/adoption, full admission, fresh independent recertification and feasible schema-2 capacity remain unaccepted. All numerical checks, resources, deadlines and confirmed researcher availability remain. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-11-whole-prefix-review-and-scc-access-blocker"
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
