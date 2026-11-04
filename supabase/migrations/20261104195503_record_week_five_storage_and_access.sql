-- Reconcile restored storage and unavailable SCC access; no scientific gate advances.
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
      "version": 41,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 4: Week 5 remains incomplete. The November 3 storage check found 3,821,470,000,000 bytes of quota headroom and 4,210,645,008,384 filesystem bytes, exceeding the unchanged 467,248,364,800-byte requirement. The reviewed ADR0009 CPU baseline/geometry job 8426211 was submitted and last observed queued at 8:05 PM EST November 3. SCC access was unavailable at 19:43 UTC November 4, so its outcome is unverified; do not resubmit or treat submission as acceptance. Next: restore access, reconcile the existing job and independently review accounting, complete runtime/source/input bindings, initialization/geometry, resources and seals. Fresh synthetic GPU verification, parity/five caches, paired pilots/replay, nine corruption paths/projections/retrieval, timing, full admission/recertification and measured schema-2 capacity remain required. Preserve f101f0e/r2, fixed panel/fallback, physical pairing and all scientific settings. Tasks 01/03 retain their historical evidence; the two historical libm diagnostics remain stopped. November 29 locks, December 6 compute and December 7-18 delivery remain fixed. Actual researcher time is unreported. Selection runs, final training, novel opening and closure remain closed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 38,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 4: the restored-storage check passed the unchanged reserve/margin requirement. ADR0009 CPU baseline/geometry job 8426211 was submitted November 3 and last observed queued at 8:05 PM EST. SCC access was unavailable November 4 at 19:43 UTC; completion and new-profile acceptance are unverified. Restore access and independently review the existing job before any dependent work. Fresh synthetic GPU verification, parity/all five caches including both 95,001-row repeats, three complete paired pilots with numerical replay, all nine development corruption paths/projections/retrieval and independent acceptance remain required. Preserve f101f0e/r2 source and locks, seeds, physical pairing, fixed panel/fallback, settings and tolerances. Prior runtime/cache evidence retains its original bindings; no scientific gate is newly passed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 21,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, November 4: November 3 quota headroom of 3,821,470,000,000 bytes and filesystem free space of 4,210,645,008,384 bytes passed the unchanged 467,248,364,800-byte storage requirement. All 19 forecast source bindings matched; no completed output was deducted and no retained evidence deleted. This resolves that observed storage shortfall, not campaign capacity. Job 8426211's outcome is unverified while SCC access is unavailable. Measure new-profile whole-job/resident timing, full admission/recertification, CPU/GPU windows and researcher work, including queue/setup and at least 25% slack. Preserve the 200 GiB reserve, November 29 locks, December 6 compute and December 7-18 delivery. The October 18 and October 28-November 1 admission targets were missed. Selection and closure remain gated; actual time is unreported."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 22,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 4: the observed storage shortfall is resolved by the November 3 preflight, but full measured capacity and selection authorization remain pending. ADR0009 job 8426211 was last observed queued; its outcome and new-profile acceptance are unverified while SCC access is unavailable. Independently accept the complete new-profile inventory, full admission/recertification and schema-2 CPU/GPU/storage/researcher capacity. Preserve scientific settings, fixed panel/fallback, historical evidence, the stopped libm count of two, storage reserve/margin and November 29/December 6/December 7-18 safeguards. Storage receipt SHA-256: 10ff01e58f7aac9446bc094fbe55c24f370b304011bf1c5f784fc4bf7be64de1. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#current-checkpoint-november-4-2026"
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
