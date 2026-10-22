-- Record geometry completion at receipt write time (recorded_at was review start) and active timing allocation; scientific gates remain pending.
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
      "reflection": "Done: Tasks 01 and 03 are complete. The fixed geometry panel, exact fresh-process repeats and fixtures are now joined by all nine 18,929-row damage summaries and fallback denominators. Corruption job 8035983 passed execution/metadata review of 927 evidence bindings, 135 commands, 67 GPU preflights, 358 resource samples and both seals. Nine encodings, 27 query projections, three clean galleries and 27 engineering results are retained. All five clean caches and all three fixed pilots previously passed independent validation. Next: Verify resident timing job 8038355, submitted October 12 at 18:32:58.249374 UTC; then complete allocated full admission hashing/numerical replay and the measured capacity decision. Open issues: No timing outcome or full campaign admission is claimed. Task 02 remains in progress and all scientific gates remain pending. Preserve failed attempts, complete validation costs and compatible CPU queue constraints. Normal availability is 5 hours weekly, with up to 10 if necessary; budget no guaranteed Thanksgiving hours. The researcher explicitly requested that actual time remain unreported. No selection, final training or novel-test opening is authorized.",
      "reopen_reason": "",
      "risks": [
        "Frozen final-training/extraction guards require a new release and fresh evidence; preserve original locks and Week 4 closure.",
        "Inherited five-hour tracker estimates are not a measured forecast: re-estimate implementation, revalidation, corruptions, reporting and resource planning before October 18.",
        "Current quota and remaining peak bytes must pass; dated capacity readings and prior GPU access are not reservations."
      ],
      "start_date": "2026-10-12",
      "state": "active",
      "title": "Complete the execution path and preselection evidence",
      "version": 22
    },
    "values": {
      "reflection": "Done: Tasks 01 and 03 are complete. The fixed geometry panel, exact fresh-process repeats and fixtures are now joined by all nine 18,929-row damage summaries and fallback denominators. Corruption job 8035983 passed execution/metadata review of 927 evidence bindings, 135 commands, 67 GPU preflights, 358 resource samples and both seals. Nine encodings, 27 query projections, three clean galleries and 27 engineering results are retained. All five clean caches and all three fixed pilots previously passed independent validation. Next: Verify resident timing job 8038355, which started October 12 at 18:35:49 UTC on its assigned L40S with passing initial resource checks; then complete allocated full admission hashing/numerical replay and the measured capacity decision. Open issues: No timing outcome or full campaign admission is claimed. Task 02 remains in progress and all scientific gates remain pending. Preserve failed attempts, complete validation costs and compatible CPU queue constraints. Normal availability is 5 hours weekly, with up to 10 if necessary; budget no guaranteed Thanksgiving hours. The researcher explicitly requested that actual time remain unreported. No selection, final training or novel-test opening is authorized."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "Corruption job 8035983 completed October 12 at 18:28:39.920098 UTC with successful accounting and 7,190 wall seconds. Independent execution/metadata review verified 927 evidence bindings, 135 commands, 67 GPU preflights, 358 RAM/storage samples and both seals. Retained outputs are nine 18,929-row encodings, 27 query projections, three clean gallery projections and 27 engineering results: 39 archives totaling 9,833,359,944 bytes. All nine full-query geometry summaries were recomputed; task 01 is complete. Full scientific archive hashing and numerical admission replay remain pending in an allocation; no tensor replay was performed on the login node. Independent cache/pilot validation remains accepted. Failed attempt 8028119 and independent-validator 8035576 remain preserved; a separate preserved post-failure seal check passed after the latter. Timing job 8038355 was submitted at 18:32:58.249374 UTC using the verified corruption receipt. No timing outcome or campaign admission is claimed. Task 02 remains in progress; source, checks, tolerances, seeds, physical batches and duration are unchanged.",
      "details": "After the completion-release freeze, regenerate parity, all five clean caches and all three full pilots under successor bindings; independently validate/account for them while retaining original evidence. Then complete all nine 18,929-query corrupted development paths, reused across three pilot heads. Time maximum severity per family through all CPU/I/O/GPU stages. Corrupted scores cannot select settings.",
      "estimate_minutes": 90,
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md",
      "expected_output": "Fresh successor admission receipts, nine complete corruption paths, 27 head projections and measured stage-level runtime/memory/bytes.",
      "id": "w05-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "in_progress",
      "title": "Revalidate the release and development paths",
      "version": 19,
      "week_id": "week-05"
    },
    "values": {
      "completion_note": "Corruption job 8035983 completed October 12 at 18:28:39.920098 UTC with successful accounting and 7,190 wall seconds. Independent execution/metadata review verified 927 evidence bindings, 135 commands, 67 GPU preflights, 358 RAM/storage samples and both seals. Retained outputs are nine 18,929-row encodings, 27 query projections, three clean gallery projections and 27 engineering results: 39 archives totaling 9,833,359,944 bytes. All nine full-query geometry summaries were recomputed; task 01 is complete. Full scientific archive hashing and numerical admission replay remain pending in an allocation; no tensor replay was performed on the login node. Independent cache/pilot validation remains accepted. Failed attempt 8028119 and independent-validator 8035576 remain preserved; a separate preserved post-failure seal check passed after the latter. Timing job 8038355 was submitted at 18:32:58.249374 UTC using the verified corruption receipt and started at 18:35:49 UTC on ece-long@scc-j01. Its assigned L40S and eleven initial resource/nvidia-smi checks passed; the outcome is pending. No timing outcome or campaign admission is claimed. Task 02 remains in progress; source, checks, tolerances, seeds, physical batches and duration are unchanged."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-01",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": "2026-10-12T18:30:49.548448+00:00",
      "completion_note": "Geometry job 8028081 previously passed the fixed 40-base/43-total panel, exact identity/nesting/missingness checks, two fresh-process repeats, and fixture coverage for absent invalid-own-scale/all-missing cases. Corruption completion review at October 12 18:30:49.548448 UTC independently recomputed all nine complete 18,929-row geometry summaries from ordered allocated telemetry. Every condition has 18,929 finite rows, zero undefined and zero zero-damage rows, with 38,605,963 originally observed joint-frame/person locations. Each jitter condition used fallback 0 of 18,929 queries; the original training-only value 0.6601371765136719 and evidence binding remain unchanged. All 927 evidence bindings, 135 commands, 67 GPU preflights, 358 resource samples and both seals passed. Task 01 is complete; full scientific tensor/hash/numerical admission replay and all scientific gates remain pending. See the execution record for exact receipt and per-condition damage summaries.",
      "details": "Freeze 40 hash-selected base queries plus up to eight deterministic geometry sentinels before corrupted scores. Cover absent categories with fixtures, repeat all conditions in two fresh processes, and require exact identity/nesting/missingness checks. Bind the existing training-only fallback 0.6601371765136719 and original evidence; do not estimate a new value. Record full-query damage/fallback summaries under plan Section 5.",
      "estimate_minutes": 90,
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md",
      "expected_output": "Immutable panel IDs/hashes, invariant/repeatability receipts and full-query damage denominators for all nine conditions.",
      "id": "w05-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "done",
      "title": "Audit the fixed geometry panel and fallback",
      "version": 7,
      "week_id": "week-05"
    },
    "values": {
      "completion_note": "Geometry job 8028081 previously passed the fixed 40-base/43-total panel, exact identity/nesting/missingness checks, two fresh-process repeats, and fixture coverage for absent invalid-own-scale/all-missing cases. The passed corruption completion receipt was written October 12 at 18:31:21.614571 UTC; its review independently recomputed all nine complete 18,929-row geometry summaries from ordered allocated telemetry. Every condition has 18,929 finite rows, zero undefined and zero zero-damage rows, with 38,605,963 originally observed joint-frame/person locations. Each jitter condition used fallback 0 of 18,929 queries; the original training-only value 0.6601371765136719 and evidence binding remain unchanged. All 927 evidence bindings, 135 commands, 67 GPU preflights, 358 resource samples and both seals passed. Task 01 is complete; full scientific tensor/hash/numerical admission replay and all scientific gates remain pending. See the execution record for exact receipt and per-condition damage summaries.",
      "completed_at": "2026-10-12T18:31:21.614571+00:00"
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
