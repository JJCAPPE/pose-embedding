-- Record independently accepted CPU evidence and the queued GPU prerequisite; no task or gate advances.
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
      "version": 46,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 5: CPU baseline 8457156 is independently accepted under the exact ADR0010 profile. All nine initializations, both complete fixed-panel geometry repeats, allocated validation, resources and seals passed. Synthetic GPU job 8466503 was queued at 10:50 PM EST. Week 5 remains open pending the remaining scientific inventory and measured admission."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 43,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 5: Independent CPU acceptance verified 43 fixed panel IDs, the original fallback, 430 tensor hashes and 387 damage rows per repeat, and all nine condition summaries. The required synthetic GPU prerequisite is queued; fresh parity/caches, paired pilots/replay and complete development corruption, projection and retrieval evidence remain pending."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 26,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, November 5: CPU acceptance does not establish campaign capacity. The refreshed source-bound forecast retains 202 GB with zero deduction for completed geometry; the 200 GiB reserve and 25% margin remain. Fresh submission guards passed. Resident timing, full admission, independent recertification and measured CPU/GPU/storage/researcher capacity are still required before selection authorization. November 29 locks and December 6 compute remain binding."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 27,
      "state": "pending"
    },
    "values": {
      "evidence": "PENDING, November 5: CPU baseline 8457156 is independently accepted; synthetic GPU job 8466503 is queued. Complete affected regeneration, independent recertification and measured capacity remain prerequisites to selection authorization. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#current-checkpoint-november-5-2026"
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
