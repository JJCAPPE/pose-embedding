-- Record approved minimum validation and recovered measurement; no gate passage.
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
      "version": 64,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 11: The researcher authorized minimum validation under ADR0012. The corrected consumers verify issued records and direct input bindings without repeating historical admission, selection numerical checks or all nine final-head audits. Full checks remain when issuing acceptance and before initial opening; the final independent check recomputes all 180 retrieval cells and report analyses. Historical evidence retains its original provenance, without a new whole-history adoption campaign or second complete Week 5 recertification. Measurement 8565319 now has its verified metadata acceptance receipt; its 873.911-hour forecast applies only to the old call graph. The corrected SCC path still needs bounded GPU parity and measured capacity. The complete scientific study is unchanged; Week 5 stays open and later stages stay closed. The legacy automation remains paused and eligible jobs use the single completion watcher."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 60,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 11: ADR0012 authorizes the minimum validation scope. Historical accepted caches/pilots and development execution retain original producer/runtime evidence. Current consumer checks retain direct hashes, exact roles, complete selection attempts and lock chronology without recursive historical replay. The existing parity helper now supports a bounded GPU-only qualification without launching development corruptions. Measurement 8565319 metadata acceptance is complete. Current GPU parity, corrected-path qualification, initial admission and capacity remain pending; no new scientific result or stage closure is claimed.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-11-minimum-validation-scope-authorized"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 35,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON MEASURED CAPACITY, November 11: The approved correction removes the 2,054 historical admission invocations that produced the old 873.911-hour forecast. That number is retained for the old implementation and is not a forecast for the corrected path. SCC qualification and a measured complete CPU/GPU/storage/researcher forecast remain required. No replacement runtime total is claimed. Preserve the 200 GiB reserve, 25% margin and fixed final-lock, compute and delivery deadlines.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-11-minimum-validation-scope-authorized"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 41,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 11: ADR0012 is approved and the minimum-scope implementation is independently reviewed. Keep one complete issuer check, initial opening safeguards and one final independent 180-cell/report verification; remove mandatory whole-history re-adoption and second Week 5 recertification. Historical measurement 8565319 has a verified metadata receipt. Candidate GPU parity, corrected-path timing and feasible complete capacity remain pending. No selection runs, final training, novel opening or Week 5 closure are authorized. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-11-minimum-validation-scope-authorized"
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
