-- Record bounded CPU compatibility; no artifact adoption, gate passage or time changes.
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
      "version": 60,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 10: Researcher-authorized CPU qualification 8561360 passed independent review. Nine fresh initializations and both complete geometry verification records match accepted baseline 8457156 exactly; accounting, resources, seals and source/runtime bindings passed. This qualifies the bounded CPU comparison, not general runtime or artifact adoption. The combined parser and development-reconstruction candidate passed 124 focused engineering tests and review; SCC timing gains remain unmeasured. Full admission, fresh independent recertification, candidate GPU/parity and artifact replay, feasible complete capacity and selection authorization remain required. Week 5 stays open; later stages stay closed and actual researcher time remains unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 56,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 10: CPU qualification 8561360 independently passed with exact retained initialization and geometry agreement. Original producer artifacts and labels remain unchanged. The separately bound parser/development validator candidate and finite metadata inventory passed 124 focused tests and review. Its bounded SCC comparison is the next prerequisite; no optimized cost, candidate scientific adoption, full admission or independent recertification is accepted.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-conditional-cpu-compatibility-accepted"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 32,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON COMPLETE MEASURED CAPACITY, November 10: The conditional CPU check passed, clearing the prerequisite for bounded metadata comparison. The necessary accepted forecast remains 2225.815 hours versus 168 available; a 205-second qualification job does not revise it. Require measured full first/reuse/fresh command costs and complete CPU/GPU/storage/researcher capacity. Preserve the 200 GiB reserve, 25% margin, November 29 locks, December 6 compute and December 7\u201318 delivery.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-conditional-cpu-compatibility-accepted"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 37,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 10: Conditional CPU initialization and geometry compatibility passed independent review. Candidate GPU/parity, retained-artifact replay, full admission, separate fresh recertification and feasible schema-2 capacity remain unaccepted. Component timing cannot establish full capacity. All numerical checks, resources, deadlines and confirmed researcher-availability requirements remain. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-conditional-cpu-compatibility-accepted"
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
