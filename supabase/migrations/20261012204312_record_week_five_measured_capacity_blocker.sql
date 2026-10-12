-- Record verified measured-profile capacity blocker; required gates remain unresolved.
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
      "reflection": "Done: Tasks 01 and 03 are complete. All five caches and three paired pilots passed independent validation; nine development corruption paths and full-query geometry summaries passed execution/metadata review. Resident timing job 8038355 passed independent completion review: 95,001 resident rows, 76,013 optimization rows from 80 actions, 59,380 updates per arm and 60 paired batch plans. All 138 metadata bindings, five commands, two GPU preflights, 29 resource records and both seals passed. Next: Verify component-measurement job 8038699, submitted October 12 at 19:01:02.227712 UTC and observed queued at 19:01:56.931301 UTC, to isolate the repeated pilot-validation cost; then finish allocated full admission replay and measured capacity. Open issues: No component result, full admission or capacity decision is claimed. Task 02 remains in progress and all scientific gates remain pending. Include complete validation costs, indivisible reports and compatible CPU queue constraints. Normal availability is 5 hours weekly, with up to 10 if necessary; budget no guaranteed Thanksgiving hours. The researcher explicitly requested that actual time remain unreported. No selection, final training or novel-test opening is authorized.",
      "reopen_reason": "",
      "risks": [
        "Frozen final-training/extraction guards require a new release and fresh evidence; preserve original locks and Week 4 closure.",
        "Inherited five-hour tracker estimates are not a measured forecast: re-estimate implementation, revalidation, corruptions, reporting and resource planning before October 18.",
        "Current quota and remaining peak bytes must pass; dated capacity readings and prior GPU access are not reservations."
      ],
      "start_date": "2026-10-12",
      "state": "active",
      "title": "Complete the execution path and preselection evidence",
      "version": 24
    },
    "values": {
      "reflection": "Done: Tasks 01 and 03 remain complete; five caches and three paired pilots passed independent validation, and nine corruption paths/full-query geometry and resident timing passed completion review. Read-only job 8038699 passed all three unchanged pilot-validator calls. Independent review verified 1,276 metadata bindings, 17 resource samples, both seals, two monitored commands, native initialization and call order; its passed receipt was written October 12 at 19:32:11.651357 UTC. The measured component sum P is 778.274100575014 seconds, above the 305.8407079646018-second necessary condition for this runtime profile. Next: Resolve the measured capacity blocker through a documented result-blind amendment or evidence for a sufficiently faster compatible runtime before further admission work. Open issues: At the measured profile, 452 repeated P calls with 25% slack forecast 122.145796 hours, exceeding the shared 48-hour GPU-opening limit before other validation/report work. This is not a universal hardware lower bound. Task 04 is blocked; task 02 remains in progress with full A held, gates 01/02 remain pending and gate 03 is unresolved with no-go evidence. No full A measurement, admission, capacity approval or weekly closure is claimed. Normal availability is 5 hours weekly, with up to 10 if necessary; budget no guaranteed Thanksgiving hours. The researcher explicitly requested that actual time remain unreported. No selection, final training or novel-test opening is authorized."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "Resident timing job 8038355 completed October 12 at 18:54:55.877214 UTC with successful accounting and 1,147 scheduler seconds. Independent completion review wrote its passed receipt at 18:59:21.217675 UTC after checking 138 metadata bindings, five commands, two GPU preflights, 29 resource records, both seals and all 60 paired batch plans. Each arm held 95,001 resident rows, optimized 76,013 rows from 80 actions and completed 59,380 updates; no head was saved. Internal timing was 1,122.070329 seconds, including training of 346.070844 seconds Contrastive, 406.250132 Contextual and 319.758312 SupCon. Peak host RSS was 5,076,500,480 bytes; peak allocated GPU memory was 3,947,458,048 bytes. Independent cache/pilot validation and nine corruption paths remain accepted for Week 5 engineering; full allocated scientific admission hashing/numerical replay remains pending. Failed attempt 8028119 and independent-validator 8035576 remain preserved; a separate preserved post-failure seal check passed after the latter. Read-only component-measurement job 8038699 was submitted at 19:01:02.227712 UTC and observed queued at 19:01:56.931301 UTC. Its outcome is pending; it measures only the three unchanged pilot-validator calls, not full admission or a universal hardware bound. Task 02 remains in progress; source, checks, tolerances, seeds, physical batches and duration are unchanged.",
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
      "version": 21,
      "week_id": "week-05"
    },
    "values": {
      "completion_note": "Resident timing job 8038355 completed October 12 at 18:54:55.877214 UTC with successful accounting and 1,147 scheduler seconds. Independent completion review wrote its passed receipt at 18:59:21.217675 UTC after checking 138 metadata bindings, five commands, two GPU preflights, 29 resource records, both seals and all 60 paired batch plans. Each arm held 95,001 resident rows, optimized 76,013 rows from 80 actions and completed 59,380 updates; no head was saved. Internal timing was 1,122.070329 seconds, including training of 346.070844 seconds Contrastive, 406.250132 Contextual and 319.758312 SupCon. Peak host RSS was 5,076,500,480 bytes; peak allocated GPU memory was 3,947,458,048 bytes. Independent cache/pilot validation and nine corruption paths remain accepted for Week 5 engineering; full allocated scientific admission hashing/numerical replay remains pending. Failed attempt 8028119 and independent-validator 8035576 remain preserved; a separate preserved post-failure seal check passed after the latter. Read-only component-measurement job 8038699 subsequently passed all three unchanged pilot-validator calls; independent review wrote its passed receipt October 12 at 19:32:11.651357 UTC after verifying 1,276 metadata bindings, 17 resource samples, two commands, both seals and native runtime/call order. P is 778.274100575014 seconds, above this measured profile's 305.8407079646018-second necessary condition. Full A is held pending resolution of the capacity blocker; this component is not full admission or a universal hardware lower bound. Task 02 remains in progress; source, checks, tolerances, seeds, physical batches and duration are unchanged."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Require completion/revalidation/corruption/report receipts and resolved seals. Combine successor and full-size timing with current storage, an allocation calendar and researcher-confirmed available hours. Re-estimate separate implementation/review, revalidation, corruption, reporting and planning packages; inherited minutes are not capacity. Require reserve plus 1.25 times remaining peak bytes and 25% work slack plus queue/setup. Append selection authorization against the admitted successor digest only if all pass.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Measured dependency, capacity and availability ledger plus immutable selection authorization or explicit blocker; no date-based waiver.",
      "id": "w05-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Record the October 18 go/no-go",
      "version": 4,
      "week_id": "week-05"
    },
    "values": {
      "state": "blocked",
      "completion_note": "Measured-profile no-go recorded from read-only job 8038699: all three unchanged pilot-validator calls passed, totaling P=778.274100575014 seconds (Contextual 266.80653271399206; Contrastive 256.6426796570304; SupCon 254.82488820399158). Independent completion review passed 1,276 metadata bindings, 17 resource samples, both seals, two commands, native locked initialization and persisted call order; successful accounting records 836 seconds. The passed receipt was written October 12 at 19:32:11.651357 UTC: study-v3/operations/week5-p-component-verification/20261012T193150Z/verification.json, SHA-256 cd21652427c8918473b97ec7a58a31db4ebd3e94b5582f6c65f8912f9e898c9b. At this measured runtime profile, 452P with 25% slack forecasts 122.145796 hours, exceeding the campaign-wide maximum-job check against a 48-hour GPU-opening allocation before omitted validation/report costs. P must be below 305.8407079646018 seconds even to satisfy that necessary condition. This is not a universal hardware lower bound or full A measurement. Task 04 is blocked pending a documented result-blind amendment or verified faster compatible runtime; full admission replay is held. No capacity approval, selection authorization or weekly closure is claimed. Preserve release 731938a and every attempt; do not change epochs, seeds, methods, physical batches or safeguards.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "criterion": "The measured dependency/schedule/storage/availability ledger passes, including revalidation and all remaining work with slack, before immutable successor selection authorization; otherwise no sweep starts.",
      "decided_at": null,
      "evidence": "",
      "id": "w05-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 5,
      "waiver_reason": "",
      "week_id": "week-05"
    },
    "values": {
      "evidence": "UNRESOLVED — measured-profile no-go. Job 8038699 passed the three unchanged pilot validators: P=778.274100575014 seconds; necessary condition P<305.8407079646018 seconds. Under this measured profile, 452P with 25% slack forecasts 122.145796 hours, exceeding the shared 48-hour GPU-opening allocation limit before other costs. Passed independent receipt written 2026-10-12T19:32:11.651357Z: study-v3/operations/week5-p-component-verification/20261012T193150Z/verification.json; SHA-256 cd21652427c8918473b97ec7a58a31db4ebd3e94b5582f6c65f8912f9e898c9b. This is not a universal hardware lower bound. Full A and the complete capacity ledger are not approved; resolve through a result-blind amendment or verified faster compatible runtime. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md"
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
