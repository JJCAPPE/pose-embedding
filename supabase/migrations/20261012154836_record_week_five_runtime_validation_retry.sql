-- Record verified compatible-runtime preflight and ongoing unchanged pilot validation; scientific gates remain pending.
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
      "reflection": "Done: Completed task 03, verified the fixed geometry panel and independently validated all five successor caches. All three pilots completed their fixed runs with matching execution/pairing metadata. Independent pilot-validator 8035576 failed to reproduce the locked initialization. Synthetic diagnostic 8035737 then verified that the failing CPU produces a different initialization hash in three native and three baseline repeats with identical RNG state. All 27 evidence files, five resource records, both seals and successful 17-second accounting were verified. Next: Before retrying the unchanged full validator, require an allocated AVX2-capable CPU, actual CPU flags and the exact native locked initialization hash through the reviewed runtime wrapper. Open issues: Task 02 remains blocked until retry submission; compatible full validation is pending, and corruption/timing work is held. The narrower eligible CPU pool must enter the capacity forecast. All scientific gates remain pending. Normal availability is 5 hours weekly, with up to 10 if necessary; budget no guaranteed Thanksgiving hours. The researcher explicitly requested that actual time remain unreported. No selection, final training or novel-test opening is authorized.",
      "reopen_reason": "",
      "risks": [
        "Frozen final-training/extraction guards require a new release and fresh evidence; preserve original locks and Week 4 closure.",
        "Inherited five-hour tracker estimates are not a measured forecast: re-estimate implementation, revalidation, corruptions, reporting and resource planning before October 18.",
        "Current quota and remaining peak bytes must pass; dated capacity readings and prior GPU access are not reservations."
      ],
      "start_date": "2026-10-12",
      "state": "active",
      "title": "Complete the execution path and preselection evidence",
      "version": 19
    },
    "values": {
      "reflection": "Done: Completed task 03, verified the fixed geometry panel and independently validated all five successor caches. All three pilots completed their fixed runs with matching execution/pairing metadata. Preserved failed independent validator 8035576 and the synthetic diagnostic showing a different initialization on the failing CPU. Retry 8035829 now runs on an allocated CPU with actual AVX2/FMA flags; three native full-size initializations reproduced the exact locked hash. The preflight command, three resource records and both seals passed independent verification. Next: Verify the unchanged full independent three-pilot validator and its accounting, resources and seals before corruption or timing work. Open issues: Full validation is running and has not passed; task 02 is in progress and all scientific gates remain pending. The narrower eligible CPU pool must enter the capacity forecast. Normal availability is 5 hours weekly, with up to 10 if necessary; budget no guaranteed Thanksgiving hours. The researcher explicitly requested that actual time remain unreported. No selection, final training or novel-test opening is authorized."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "Independent pilot-validator 8035576 failed October 12 because the locked initialization hash could not be reproduced; its original operation has no seal-after receipt, and a separate preserved post-failure seal check passed. Synthetic-only diagnostic 8035737 subsequently passed on the same scc-pi4 Intel E5-2650 v2 CPU, which lacks AVX2/FMA: three native DEFAULT and three explicit baseline DEFAULT repeats produced d09429fb578c782281dc032258ba707213494ec78f2f704aba28097fdcd40d69, differing from locked 035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284 despite identical RNG state. Independent verification bound all 27 evidence files, five resource records, both seals and successful 17-second accounting. No dataset tensors or saved heads were used. The runtime difference is confirmed; CPU-dispatch rounding is a supported explanation, and compatible full validation remains pending. Before retry, the reviewed wrapper must verify actual AVX2 CPU flags and exact native locked initialization without changing frozen source, checks, tolerances, seeds, batches or duration. Failed attempt 8028119 and the new validator attempt remain preserved. Task 02 remains blocked; corruption and timing work are held. The compatible CPU queue restriction must be included in the forecast; no retry or reservation is claimed.",
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
      "version": 16,
      "week_id": "week-05"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "Independent pilot-validator 8035576 failed to reproduce locked initialization; its original operation has no seal-after receipt, and a separate preserved post-failure seal check passed. Synthetic diagnostic 8035737 verified the failing CPU runtime difference. Reviewed retry 8035829 was submitted October 12 at 15:44:10.970322 UTC and started at 15:46:06 UTC on w@scc-wg4 with four CPU slots, 32 GiB, 12 hours and no GPU. Actual AVX2/FMA flags and three native full-size repetitions of locked 035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284 passed. Independent preflight verification bound the command, three resource records and both seals. The unchanged full validator is running; no full independent validation pass or scientific admission is claimed. Task 02 returns to in progress, with corruption/timing held until full validation passes. Failed attempt 8028119 and the new validator attempt remain preserved. Scientific source, checks, tolerances, seeds, physical batches and duration are unchanged. Include the narrower compatible CPU queue pool in capacity planning; inspect existing job and launch intent rather than resubmitting."
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
