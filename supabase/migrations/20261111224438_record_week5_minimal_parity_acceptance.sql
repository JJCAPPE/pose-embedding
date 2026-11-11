-- Record independently accepted bounded GPU parity; capacity and admission remain pending.
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
      "version": 65,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 11: Bounded GPU parity job 8580442 is independently accepted under ADR0012. The exact accepted runtime, fixed 48-sample auxiliary panel, all 12 comparison layers, resource records, source/input bindings and unopened seals passed review; every layer recorded zero maximum absolute error within unchanged tolerances. The job ran parity only and launched no development corruptions. Accepted historical evidence retains its original provenance. The next authorized prerequisite is one corrected admission-prefix measurement using the existing controller/assembler, retaining the expected pending-capacity rejection. Complete measured capacity and admission remain pending; the old 873.911-hour forecast applies only to the old call graph. Week 5 remains open and later stages stay closed. The legacy automation stays paused and eligible jobs use the single completion watcher."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 61,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 11: GPU parity 8580442 is independently accepted alongside CPU 8561360. Review checked 749 unique launch/runtime bindings before and after, 43 exported metadata files, two successful commands, five resource records and four seal observations. The fixed 48-sample panel and all 12 layers passed unchanged checks with zero recorded maximum absolute error. No development corruptions ran and no new cache acceptance was granted. The next prerequisite is one corrected admission-prefix measurement. Initial admission and complete capacity remain pending; no stage closure is claimed.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-11-bounded-gpu-parity-accepted"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 36,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON MEASURED CAPACITY, November 11: The remaining bounded GPU parity qualification is accepted. One corrected admission-prefix measurement is next, with the expected pending-capacity rejection preserved. The complete CPU/GPU/storage/calendar/researcher forecast and actual admission remain pending. The old 873.911-hour estimate describes the old call graph; no replacement runtime total or capacity pass is claimed. Preserve the 200 GiB reserve, 25% margin and fixed final-lock, compute and delivery deadlines.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-11-bounded-gpu-parity-accepted"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 42,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 11: Bounded GPU parity 8580442 is independently accepted under ADR0012, with exact runtime, fixed panel, all 12 layers, resources, bindings and unopened seals verified. Corrected admission-prefix timing and feasible complete capacity remain pending. Keep one full issuer check, initial opening safeguards and one independent final 180-cell/report verification. No selection runs, final training, novel opening or Week 5 closure are authorized. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-11-bounded-gpu-parity-accepted"
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
