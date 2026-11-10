-- Record verified local optimization; no scientific gate, runtime adoption or time changes.
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
      "version": 59,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 10: Command-local development-episode reconstruction reuse passed focused mutation/isolation tests and independent source review. A 740-row synthetic local comparison reduced 87 validations from 0.649315 to 0.181573 seconds with identical reports; this is not SCC capacity evidence. No SCC job is active after the accepted runtime startup failure. The researcher approved ADR0011: conditionally qualify the exact runtime candidate and a separately bound validator while retaining original frozen artifact provenance. Allocated compatibility and independent acceptance remain required. Full admission, independent recertification, measured complete capacity and selection authorization remain required. Week 5 is open and later stages closed; actual researcher time remains unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 55,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 10: Local development-episode reconstruction reuse is implemented and independently reviewed. It preserves full first checks, complete input/source rehash, fresh roles and independent-command validation. Synthetic reports match exactly; no scientific release has adopted the change. Current libc/libm mismatch still blocks SCC measurement. Researcher-approved ADR0011 permits conditional runtime qualification and separate producer/validator provenance; allocated compatibility and independent acceptance are still required. Full admission and independent recertification remain pending.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-development-episode-reconstruction-reuse-verified-locally"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 31,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON SCC RUNTIME AND COMPLETE MEASURED CAPACITY, November 10: A local 740-row synthetic comparison reduced 87 validations from 0.649315 to 0.181573 seconds, but cannot revise the accepted necessary 2225.815-hour forecast versus 168 available. Retain first checks, fresh content and authority checks, independent recertification, the 200 GiB reserve and 25% margin. ADR0011 authorizes qualification, not automatic scientific acceptance. November 29 locks, December 6 compute and December 7\u201318 delivery remain binding.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-development-episode-reconstruction-reuse-verified-locally"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 36,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 10: Local parser and development-reconstruction optimizations have software evidence only. No allocated improved full cost or complete schema-2 capacity is accepted. ADR0011 conditionally authorizes runtime qualification and separate producer/validator provenance; all required allocated checks must pass before adoption. Preserve full admission, fresh independent recertification, all resources/deadlines and actual researcher availability requirements. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-development-episode-reconstruction-reuse-verified-locally"
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
