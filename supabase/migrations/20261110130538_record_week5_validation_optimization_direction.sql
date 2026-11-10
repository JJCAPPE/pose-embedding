-- Record researcher-authorized validation optimization; no research gate changes.
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
      "version": 56,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 10: The researcher authorized result-blind engineering to reduce redundant validation after accepted measurement 8539455 failed the calendar bound. A small parser optimization preserves all checks and passes local tests; complete SCC capacity improvement is not yet established. Earlier accepted baselines, caches, paired pilots, development and timing remain preserved. Week 5 stays open; full admission, independent recertification, feasible capacity and selection authorization remain required. Later stages stay closed and actual researcher time remains unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 53,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 10: Accepted measurement 8539455 remains the baseline: first/reused/fresh prefixes 3263.363/3087.310/3223.896 seconds, with check/hit counts 42/24, 0/66, 42/24. The researcher authorized reducing redundant deterministic work. The first parser change passes local correctness tests; synthetic component speedups are not SCC or campaign-capacity evidence. Bounded metadata profiling will identify remaining cost. Full admission and independent recertification remain pending; frozen scientific source, accepted evidence and all safeguards are preserved."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 29,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON MEASURED CAPACITY, November 10: Researcher direction now authorizes result-blind validation optimization and bounded measurement. The prior measured necessary forecast remains 2225.815 hours with 25% slack versus 168 available; no improved complete forecast is accepted yet. Preserve complete first checks, full transitive content rehash on reuse, fresh dynamic guards and independent command recertification. Use a reviewed immutable correction before scientific use; never relabel old artifacts. November 29 locks, December 6 compute, December 7\u201318 delivery, the 200 GiB reserve and 25% margin remain binding.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-reduce-redundant-validation"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 34,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 10: The researcher authorized reducing redundant validation to address accepted measurement 8539455. Its necessary bound remains 1.25 × (392C+1662R) = 2225.815 hours versus 168 available, before remaining evaluation/reporting and queue/setup. Local parser optimization and component profiling do not establish capacity. Require newly measured complete costs, full admission and independent recertification; all deadlines and scientific safeguards remain unchanged. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-reduce-redundant-validation"
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
