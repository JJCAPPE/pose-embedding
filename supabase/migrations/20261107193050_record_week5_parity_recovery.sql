-- Record verified development failure and reviewed parity recovery; Week 5 stays open.
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
      "version": 52,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 7: Development job 8501664 stopped before corrupted extraction because its retained parity report named a different host and GPU. Independent review verified the failure record and retained all partial outputs. A reviewed external correction regenerates parity on the assigned GPU before the unchanged frozen controller; exact environment checks remain enforced. CPU/GPU prerequisites, five caches and three paired pilots with numerical replay remain accepted. Development evidence, timing, full admission/recertification, measured capacity and selection authorization remain required; Week 5 stays open and actual researcher time remains unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 49,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 7: Independent review verified development job 8501664's host/GPU parity mismatch: eleven command outcomes, five GPU preflights, 23 resource records, four seals and exact before/after CPU runtime. Three gallery projections are retained, with zero corrupted encodings, query projections or retrieval results. The reviewed correction runs fresh parity on the allocated GPU, then the original 135-command controller, preserving original gallery provenance and frozen scientific checks. The source-bound forecast is 203,073,741,824 bytes; the 200 GiB reserve and 25% margin remain intact. No development acceptance is claimed. Selection runs, final training and novel opening stay closed."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 30,
      "state": "pending"
    },
    "values": {
      "evidence": "PENDING, November 7: CPU baseline 8457156, synthetic GPU prerequisite 8466503, all five clean caches and three paired pilots with independent numerical replay 8499390 remain accepted under ADR0010. Failure review of development job 8501664 established a parity-environment mismatch before corrupted extraction; the reviewed allocation-local parity correction does not establish scientific acceptance. Development corruption/projection/retrieval evidence, resident timing, full admission and independent recertification, measured schema-2 CPU/GPU/storage/researcher capacity and selection authorization remain required. Week 5 stays open. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-7-allocation-local-parity-recovery"
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
