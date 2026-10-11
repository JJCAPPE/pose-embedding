-- Record the allocated controller diagnostic and fresh cache submission; scientific gates remain pending.
-- Full row/version checks preserve concurrent progress and closed-week history.
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
      "actual_minutes": 0,
      "advisor_prompt": "Do all October 18 validity, seal, storage, runtime and researcher-availability criteria pass without changing the declared study?",
      "closed_at": null,
      "deliverable": "A reviewed completion release, full fixture-to-report rehearsal, fresh bound admission evidence, nine verified development conditions and immutable go/no-go report.",
      "end_date": "2026-10-18",
      "id": "week-05",
      "number": 5,
      "objective": "Complete one successor release, revalidate its caches/pilots and meet every scientific/resource prerequisite before selection.",
      "phase": "Preselection go/no-go",
      "planned_minutes": 300,
      "project_id": "pose-embed",
      "reflection": "Done: Completed task 03 and independently verified the fixed geometry panel with exact fresh-process repeats. Preserved failed cache attempt 8028119 and diagnosed its CUDA-device availability error: the persistent parent monitor held a context on an exclusive-process L40S, blocking the parity child. No parity or cache output was created. Next: Verify the external controller correction in an allocated synthetic check, then restart identical scientific commands in a new immutable cache attempt before independent validation. Open issues: Task 02 is temporarily blocked; full-query geometry telemetry, pilots, corruption paths, timing and the full capacity decision remain unfinished. All three scientific gates stay pending. The frozen release and scientific recipe are unchanged. Availability remains up to 5 hours weekly normally, 10 if necessary; budget no guaranteed Thanksgiving hours. Actual researcher time remains unreported. No selection, final training or novel-test opening is authorized.",
      "reopen_reason": "",
      "risks": [
        "Frozen final-training/extraction guards require a new release and fresh evidence; preserve original locks and Week 4 closure.",
        "Inherited five-hour tracker estimates are not a measured forecast: re-estimate implementation, revalidation, corruptions, reporting and resource planning before October 18.",
        "Current quota and remaining peak bytes must pass; dated capacity readings and prior GPU access are not reservations."
      ],
      "start_date": "2026-10-12",
      "state": "active",
      "title": "Complete the execution path and preselection evidence",
      "version": 9
    },
    "values": {
      "reflection": "Done: Completed task 03 and verified the fixed geometry panel. Preserved failed cache attempt 8028119 and confirmed its exclusive-GPU context conflict with allocated diagnostic 8028141: the held-context probe was rejected, then two sequential probes succeeded with the parent CUDA-uninitialized. All 58 diagnostic evidence hashes, both seals and 12 resource samples passed independent verification. Next: Verify fresh-cache job 8028152 using the reviewed external controller, then complete independent cache/pilot validation, corruption paths, full-query telemetry and timing. Open issues: Task 02 is back in progress; no cache result is claimed and all three scientific gates remain pending. The full measured capacity forecast is still required. Normal availability is 5 hours weekly, with up to 10 if necessary; budget no guaranteed Thanksgiving hours. The researcher explicitly requested that actual time remain unreported. No selection, final training or novel-test opening is authorized."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "Cache attempt 8028119 failed before parity or cache creation: command 002 exited 2 after 45.0216 seconds with CUDA-capable devices busy or unavailable. Saved GPU reports confirm exclusive-process mode and a persistent parent Python CUDA context, which blocked the parity child. The failed attempt and frozen release 731938a are preserved. An external controller correction will use a short-lived GPU preflight child and keep the parent CUDA-uninitialized; it must pass an allocated synthetic reproduction/remedy check before any identical fresh cache retry. Revalidation is blocked pending that check; no successful cache result or retry is claimed.",
      "details": "After the completion-release freeze, regenerate parity, all five clean caches and all three full pilots under successor bindings; independently validate/account for them while retaining original evidence. Then complete all nine 18,929-query corrupted development paths, reused across three pilot heads. Time maximum severity per family through all CPU/I/O/GPU stages. Corrupted scores cannot select settings.",
      "estimate_minutes": 90,
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md",
      "expected_output": "Fresh successor admission receipts, nine complete corruption paths, 27 head projections and measured stage-level runtime/memory/bytes.",
      "id": "w05-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "blocked",
      "title": "Revalidate the release and development paths",
      "version": 6,
      "week_id": "week-05"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "Allocated diagnostic 8028141 passed independent verification at 23:23:22.796524 UTC: all 58 evidence hashes, both seals and 12 resource samples passed; the held-context GPU probe was rejected and two sequential probes succeeded with the parent CUDA-uninitialized. The reviewed external controller preserves frozen release 731938a and identical scientific commands. Fresh-cache job 8028152 was submitted at 23:23:23 UTC; its allocation and cache outcome remain unverified at this checkpoint. Failed attempt 8028119 is retained. Task 02 is in progress; full cache/pilot/corruption validation and timing remain required."
    }
  }
]
$edits$::jsonb;

  edit jsonb;
  current_row jsonb;
  expected_row jsonb;
  assignments text;
  columns_sql text;
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
    if edit->>'table' not in ('weeks', 'tasks', 'gates', 'sources', 'week_sources')
       or edit->'values' ? 'version' then
      raise exception 'Unexpected amendment scope';
    end if;
    if edit->>'table' = 'week_sources' then
      select to_jsonb(t) into current_row from public.week_sources t
        where project_id = 'pose-embed' and week_id = edit->>'week_id'
          and source_id = edit->>'source_id' for update;
    else
      execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
        into current_row using edit->>'id';
    end if;
    if edit->>'operation' = 'insert' then
      expected_row := edit->'values' || jsonb_build_object('version', 1);
      if current_row is not null then
        if current_row @> expected_row then continue; end if;
        raise exception using errcode = '40001', message = edit->>'id' || ' already exists with different content';
      end if;
      select string_agg(format('%I', key), ', ' order by key),
             string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, assignments from jsonb_object_keys(expected_row) key;
      execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
        edit->>'table', columns_sql, assignments, edit->>'table') using expected_row;
      continue;
    end if;
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
