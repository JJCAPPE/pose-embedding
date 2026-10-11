-- Record verified geometry and the fresh cache submission; no scientific gate passes.
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
      "reflection": "Done: Verified release 731938a on SCC, the 41-check full command rehearsal, successor preparation with eight byte-identical manifests, and supplementary job 8028071 with 84 passing checks and independently verified development/novel metadata tables. The real dataset seal remained intact; task 03 is complete. Next: Complete geometry job 8028081, fresh caches and pilots, all nine development corruption paths and measured timing, then verify the full capacity forecast. Open issues: The remaining three tasks and all three scientific gates are unfinished. Repeated validation and whole-report costs must fit the dated calendar; feasibility is not yet established. Availability remains up to 5 hours weekly normally, 10 if necessary; budget no guaranteed Thanksgiving hours. Actual researcher time remains unreported. No selection, final training or novel-test opening is authorized.",
      "reopen_reason": "",
      "risks": [
        "Frozen final-training/extraction guards require a new release and fresh evidence; preserve original locks and Week 4 closure.",
        "Inherited five-hour tracker estimates are not a measured forecast: re-estimate implementation, revalidation, corruptions, reporting and resource planning before October 18.",
        "Current quota and remaining peak bytes must pass; dated capacity readings and prior GPU access are not reservations."
      ],
      "start_date": "2026-10-12",
      "state": "active",
      "title": "Complete the execution path and preselection evidence",
      "version": 7
    },
    "values": {
      "reflection": "Done: Completed task 03 through the verified completion release, 41-check command rehearsal, 84 supplementary checks and actual metadata tables. Geometry job 8028081 passed: 40 base queries, 43 selected rows, nine conditions, 430 tensors and exact repeats in two fresh processes. Dataset seals remained intact. Next: Verify fresh-cache job 8028119, then run the paired pilots, all nine development corruption paths and measured timing before the capacity decision. Open issues: Geometry task 01 still needs full-query damage telemetry; task 02 is in progress and all three scientific gates remain pending. The dated calendar must include repeated validation and complete report costs. Availability remains up to 5 hours weekly normally, 10 if necessary; budget no guaranteed Thanksgiving hours. Actual researcher time remains unreported. The continuing Week 5 work does not authorize selection, final training or novel-test opening."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-01",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "Geometry job 8028081 was queued at 22:44:39 UTC using the unchanged frozen CLI with its required locks/geometry destination. The queued job is not a passing result. Panel invariants, repeats and all nine full-query damage summaries remain to be verified.",
      "details": "Freeze 40 hash-selected base queries plus up to eight deterministic geometry sentinels before corrupted scores. Cover absent categories with fixtures, repeat all conditions in two fresh processes, and require exact identity/nesting/missingness checks. Bind the existing training-only fallback 0.6601371765136719 and original evidence; do not estimate a new value. Record full-query damage/fallback summaries under plan Section 5.",
      "estimate_minutes": 90,
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md",
      "expected_output": "Immutable panel IDs/hashes, invariant/repeatability receipts and full-query damage denominators for all nine conditions.",
      "id": "w05-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "in_progress",
      "title": "Audit the fixed geometry panel and fallback",
      "version": 5,
      "week_id": "week-05"
    },
    "values": {
      "completion_note": "Geometry job 8028081 passed independent verification at 22:57:18 UTC: 40 base queries, 43 total selected rows, nine conditions, 430 tensors and exact repeats across two fresh processes. The absent invalid-own-scale and all-missing cases have executed fixture coverage. The original training fallback was preserved; both dataset seals and all 14 resource samples passed. This task remains in progress until all nine full-query damage summaries are verified. See the Week 5 execution record."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "After the completion-release freeze, regenerate parity, all five clean caches and all three full pilots under successor bindings; independently validate/account for them while retaining original evidence. Then complete all nine 18,929-query corrupted development paths, reused across three pilot heads. Time maximum severity per family through all CPU/I/O/GPU stages. Corrupted scores cannot select settings.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Fresh successor admission receipts, nine complete corruption paths, 27 head projections and measured stage-level runtime/memory/bytes.",
      "id": "w05-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Revalidate the release and development paths",
      "version": 4,
      "week_id": "week-05"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "Fresh five-cache L40S job 8028119 was submitted at 22:57:19 UTC against frozen release 731938a and the verified successor bindings. No cache outcome is claimed. Fresh parity/repeat extraction, independent cache and complete-pilot validation, all nine development conditions, 27 head projections and capacity measurements remain required.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md"
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
