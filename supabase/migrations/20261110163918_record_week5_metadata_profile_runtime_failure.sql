-- Record verified pre-profiling runtime failure; no research gate or time changes.
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
      "version": 57,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 10: Diagnostic 8549858 stopped before profiling because libc/libm contents on the allocated SCC host differ from the accepted runtime. No SCC job remains active, and no improved timing result was produced. Earlier accepted evidence is preserved. The existing automation stays active for authorized local optimization; SCC execution needs a runtime resolution. Week 5 remains open; full admission, independent recertification, feasible capacity and selection authorization are still required. Later stages remain closed; actual researcher time is unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 54,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS LOCALLY, November 10: Independent review accepted the startup failure record for 8549858, which exited one after five seconds before profiling or parser comparison. Only libc/libm content hashes differ from the accepted runtime; no replacement profile is authorized. The next local candidate reduces repeated development-episode reconstruction with complete dependency, mutation and equivalence checks. Accepted measurement 8539455 remains the timing baseline. Full admission and independent recertification remain pending; no unchanged SCC retry is planned."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 30,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON MEASURED CAPACITY AND SCC RUNTIME, November 10: Profiling 8549858 stopped before its comparison because libc/libm contents differ from the accepted baseline. Local optimization remains authorized, but no improved complete forecast is accepted: the prior necessary bound is 2225.815 hours with 25% slack versus 168 available. Preserve full first checks, transitive content rehash, fresh dynamic guards and independent recertification. SCC work needs the accepted environment restored or a documented researcher-authorized resolution. November 29 locks, December 6 compute, December 7–18 delivery, the 200 GiB reserve and 25% margin remain binding.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-metadata-profiling-stopped-at-runtime-validation"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 35,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 10: Diagnostic 8549858 produced no profiling result after its startup guard detected changed libc/libm contents. Authorized local engineering can continue; no replacement SCC runtime baseline or scientific acceptance follows. Measurement 8539455 still forecasts 2225.815 hours with slack versus 168 available, before other work. Require newly measured complete costs, full admission and independent recertification. All deadlines and safeguards remain unchanged. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-10-metadata-profiling-stopped-at-runtime-validation"
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
